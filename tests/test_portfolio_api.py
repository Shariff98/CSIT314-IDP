"""Owner-only read-only portfolio JSON contract, using temporary test data."""
import pytest

from entity.idp import IDP
from entity.user_profile import UserProfile
from tests.conftest import login


def test_lists_only_own_drafts_and_published_without_views(client, designer, other_designer, make_idp):
    published = make_idp()
    draft = make_idp(published=False)
    make_idp(designer_id=other_designer.id)
    login(client, designer.email)
    data = client.get(f"/api/designer/portfolio?designer_id={other_designer.id}").json["data"]
    assert data["total"] == 2
    assert {item["id"] for item in data["items"]} == {published.id, draft.id}
    assert {item["published"] for item in data["items"]} == {True, False}
    assert all(item["designer_id"] == designer.id for item in data["items"])
    assert all(item["photos"] == [] and item["company"] is None for item in data["items"])
    assert IDP.find_by_id(published.id).views == IDP.find_by_id(draft.id).views == 0
    assert client.get("/my/idps").status_code == 200


@pytest.mark.parametrize("identity", [None, "customer", "admin", "manager"])
def test_permissions(client, request, identity):
    if identity:
        login(client, request.getfixturevalue(identity).email)
    response = client.get("/api/designer/portfolio")
    assert response.status_code == (403 if identity else 401)
    assert set(response.json) == {"error"}


@pytest.mark.parametrize("inactive", ["account", "profile", "missing"])
def test_inactive_sessions(client, designer, inactive):
    login(client, designer.email)
    if inactive == "account":
        designer.suspend()
    elif inactive == "profile":
        UserProfile.find_by_name("InteriorDesigner").suspend()
    else:
        with client.session_transaction() as session:
            session["user_id"] = 999999
    assert client.get("/api/designer/portfolio").status_code == 401
    with client.session_transaction() as session:
        assert "user_id" not in session


def test_database_role_overrides_stale_cookie(client, customer):
    login(client, customer.email)
    with client.session_transaction() as session:
        session["role"] = "InteriorDesigner"
    assert client.get("/api/designer/portfolio").status_code == 403


@pytest.mark.parametrize("query", ["q=blue", "status=Past", "status=Published", "category=Kitchen",
                                   "date_from=2026-01-01&date_to=2026-02-01",
                                   "q=blue&status=Past&category=Kitchen&date_from=2026-01-01&date_to=2026-02-01"])
def test_filters(client, designer, make_idp, query):
    wanted = make_idp("Blue kitchen", status="Past", category="Kitchen", created_at="2026-01-10 10:00:00")
    make_idp("Other", published=False, created_at="2026-03-01 10:00:00")
    login(client, designer.email)
    response = client.get("/api/designer/portfolio?" + query)
    assert response.status_code == 200
    assert [item["id"] for item in response.json["data"]["items"]] == [wanted.id]


def test_draft_filter_and_empty(client, designer, make_idp):
    draft = make_idp(published=False)
    make_idp()
    login(client, designer.email)
    assert [item["id"] for item in client.get("/api/designer/portfolio?status=Draft").json["data"]["items"]] == [draft.id]
    assert client.get("/api/designer/portfolio?q=missing").json == {"data": {"items": [], "total": 0}}


@pytest.mark.parametrize("query", ["status=Archived", "date_from=no", "date_to=2026-02-30",
                                   "date_from=2026-03-01&date_to=2026-01-01", "category=Unknown"])
def test_invalid_filters(client, designer, query):
    login(client, designer.email)
    response = client.get("/api/designer/portfolio?" + query)
    assert response.status_code == 400
    assert response.json["error"]["code"] == "invalid_request"


def test_empty_owner_portfolio(client, designer):
    login(client, designer.email)
    assert client.get("/api/designer/portfolio").json == {"data": {"items": [], "total": 0}}
