"""JSON favourites contract. All records live in pytest's temporary database."""
import pytest

from entity.favourite import Favourite
from entity.user_account import UserAccount
from entity.user_profile import UserProfile
from tests.conftest import login


def test_save_duplicate_list_remove_and_repeated_remove(client, customer, make_idp):
    project = make_idp()
    login(client, customer.email)
    url = f"/api/favourites/projects/{project.id}"
    assert client.post(url).json == {"data": {"project_id": project.id, "saved": True, "result": "saved"}}
    assert client.post(url).json["data"]["result"] == "already_saved"
    assert project.shortlist_count() == 1
    data = client.get("/api/favourites/projects").json["data"]
    assert data["total"] == 1
    assert data["items"][0]["id"] == project.id
    assert data["items"][0]["photos"] == []
    assert client.get(f"/api/idps/{project.id}").json["data"]["is_saved"] is True
    assert client.delete(url).json == {"data": {"project_id": project.id, "saved": False, "result": "removed"}}
    assert client.delete(url).json["data"]["result"] == "not_saved"
    assert project.shortlist_count() == 0
    assert client.get("/api/favourites/projects").json == {"data": {"items": [], "total": 0}}
    assert client.get(f"/api/idps/{project.id}").json["data"]["is_saved"] is False


@pytest.mark.parametrize("method,path", [("post", "/api/favourites/projects/1"),
                                         ("delete", "/api/favourites/projects/1"),
                                         ("get", "/api/favourites/projects")])
@pytest.mark.parametrize("identity", [None, "designer", "admin", "manager"])
def test_permissions(client, request, identity, method, path):
    if identity:
        account = request.getfixturevalue(identity)
        login(client, account.email)
    response = getattr(client, method)(path)
    assert response.status_code == (403 if identity else 401)
    assert set(response.json) == {"error"}
    assert set(response.json["error"]) == {"code", "message"}


@pytest.mark.parametrize("method,path", [("post", "/api/favourites/projects/1"),
                                         ("delete", "/api/favourites/projects/1"),
                                         ("get", "/api/favourites/projects")])
@pytest.mark.parametrize("inactive", ["account", "profile", "missing"])
def test_inactive_sessions(client, customer, method, path, inactive):
    login(client, customer.email)
    if inactive == "account":
        customer.suspend()
    elif inactive == "profile":
        UserProfile.find_by_name("Customer").suspend()
    else:
        with client.session_transaction() as session:
            session["user_id"] = 999999
    assert getattr(client, method)(path).status_code == 401
    with client.session_transaction() as session:
        assert "user_id" not in session


def test_current_account_role_overrides_stale_session_role(client, designer):
    login(client, designer.email)
    with client.session_transaction() as session:
        session["role"] = "Customer"
    assert client.get("/api/favourites/projects").status_code == 403


def test_missing_and_unpublished_projects(client, customer, make_idp):
    draft = make_idp(published=False)
    project = make_idp()
    login(client, customer.email)
    assert client.post("/api/favourites/projects/999999").status_code == 404
    assert client.post(f"/api/favourites/projects/{draft.id}").status_code == 404
    client.post(f"/api/favourites/projects/{project.id}")
    project.update(published=0)
    assert client.get("/api/favourites/projects").json["data"]["total"] == 0
    assert client.get("/api/favourites/projects?q=Cosy").json["data"]["total"] == 0
    assert client.post(f"/api/favourites/projects/{project.id}").status_code == 404
    assert client.delete(f"/api/favourites/projects/{project.id}").json["data"]["result"] == "removed"


def test_customer_isolation_filters_and_session_identity(client, customer, make_idp):
    other = UserAccount.create("Other", "other@example.com", "password123", "Customer")
    private = make_idp("Private")
    Favourite.add(other.id, private.id)
    login(client, customer.email)
    url = f"/api/favourites/projects/{private.id}"
    assert client.get(f"/api/favourites/projects?customer_id={other.id}").json["data"]["total"] == 0
    assert client.delete(url, json={"customer_id": other.id}).json["data"]["result"] == "not_saved"
    assert Favourite.exists(other.id, private.id)
    assert client.post(url, json={"customer_id": other.id}).json["data"]["saved"] is True
    assert Favourite.exists(customer.id, private.id)
    kitchen = make_idp("Blue kitchen", category="Kitchen")
    client.post(f"/api/favourites/projects/{kitchen.id}")
    data = client.get("/api/favourites/projects?q=blue&category=Kitchen").json["data"]
    assert [item["id"] for item in data["items"]] == [kitchen.id]
    assert client.get("/api/favourites/projects?q=missing").json["data"]["total"] == 0


def test_existing_html_routes_work(client, customer, make_idp):
    project = make_idp()
    login(client, customer.email)
    assert client.post(f"/idp/{project.id}/save").status_code == 302
    assert client.get("/favourites").status_code == 200
    assert client.post(f"/idp/{project.id}/unsave").status_code == 302
