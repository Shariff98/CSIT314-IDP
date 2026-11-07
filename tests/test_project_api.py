"""Public project API behaviour, serialization, and shared HTML view sessions."""
import pytest

from control.save_favourite_controller import SaveFavouriteController
from entity.category import Category
from entity.company import Company
from entity.idp import IDP
from entity.idp_photo import IDPPhoto
from tests.conftest import PNG, login


def ids(response):
    assert response.status_code == 200
    return [item["id"] for item in response.json["data"]["items"]]


def test_browse_published_without_counting_views(client, make_idp):
    project = make_idp()
    make_idp(published=False)
    response = client.get("/api/idps")
    assert ids(response) == [project.id]
    assert response.json["data"]["total"] == 1
    assert response.json["data"]["per_page"] == 24
    assert IDP.find_by_id(project.id).views == 0


@pytest.mark.parametrize("query", ["q=timber", "category=Kitchen", "style=Japandi", "min_budget=9000",
                                  "max_budget=12000", "property_type=Condo", "location=Tamp",
                                  "q=timber&category=Kitchen&style=Japandi&min_budget=9000&max_budget=12000&property_type=Condo&location=Tamp"])
def test_search_and_filters(client, make_idp, query):
    wanted = make_idp(title="Timber kitchen", category="Kitchen", style_tags="Modern, Japandi",
                      budget=10000, property_type="Condo", location="Tampines")
    make_idp(title="Other", budget=1000 if query == "min_budget=9000" else 15000)
    assert ids(client.get("/api/idps?" + query)) == [wanted.id]


@pytest.mark.parametrize("sort", ["newest", "budget_high", "views", "saves"])
def test_sorting(client, make_idp, customer, sort):
    make_idp(budget=1000)
    top = make_idp(budget=9000)
    top.record_view()
    SaveFavouriteController().save(customer.id, top.id)
    assert ids(client.get("/api/idps?sort=" + sort))[0] == top.id
    assert ids(client.get("/api/idps?sort=budget_low"))[-1] == top.id


def test_pagination(client, make_idp):
    projects = [make_idp(title=str(index)) for index in range(26)]
    data = client.get("/api/idps").json["data"]
    assert (len(data["items"]), data["total"], data["pages"]) == (24, 26, 2)
    assert ids(client.get("/api/idps?page=2")) == [projects[1].id, projects[0].id]
    assert len(ids(client.get("/api/idps?per_page=100"))) == 26
    assert ids(client.get("/api/idps?page=99")) == []


@pytest.mark.parametrize("query", ["page=0", "page=abc", "per_page=101", "per_page=0", "per_page=1.5",
                                  "min_budget=-1", "max_budget=no", "min_budget=10&max_budget=5"])
def test_invalid_parameters(client, query):
    response = client.get("/api/idps?" + query)
    assert response.status_code == 400
    assert set(response.json) == {"error"}
    assert set(response.json["error"]) == {"code", "message"}
    assert response.json["error"]["code"] == "invalid_request"


def test_empty_results_and_unknown_sort(client, make_idp):
    project = make_idp()
    assert ids(client.get("/api/idps?sort=unknown")) == [project.id]
    data = client.get("/api/idps?q=missing").json["data"]
    assert data == dict(items=[], total=0, page=1, per_page=24, pages=1)


def test_options_exclude_drafts_and_inactive_categories(client, make_idp):
    make_idp(style_tags="Custom style", location="Tampines")
    make_idp(style_tags="Secret style", location="Secret", published=False)
    Category.create("Hidden", "").suspend()
    options = client.get("/api/idps/options").json["data"]
    assert "Hidden" not in options["categories"]
    assert options["locations"] == ["Tampines"]
    assert "Custom style" in options["styles"] and "Secret style" not in options["styles"]
    assert "Modern" in options["styles"]
    assert "Commercial" in options["property_types"]
    assert set(options["sort_options"]) == {"newest", "views", "saves", "budget_low", "budget_high"}


def test_serialization_photos_company_and_no_credentials(client, designer, make_idp):
    company = Company.create(designer.id, "Studio", "REG123", "Address", "61234567", "studio@example.com", "Design")
    project = make_idp(style_tags="Modern, Minimalist")
    IDPPhoto.create(project.id, PNG, "png")
    cover = IDPPhoto.create(project.id, PNG, "png", is_cover=True)
    data = client.get(f"/api/idps/{project.id}").json["data"]["project"]
    assert set(data) == {"id", "designer_id", "title", "description", "category", "budget", "property_type",
                         "location", "completion_date", "status", "views", "created_at", "style_tags",
                         "published", "photos", "company"}
    assert data["style_tags"] == ["Modern", "Minimalist"]
    assert data["published"] is True
    assert data["company"]["id"] == company.id
    assert data["company"]["name"] == "Studio"
    assert "password" not in str(data) and "password_hash" not in str(data)
    assert data["photos"][0] == {"id": cover.id, "url": "/uploads/" + cover.filename, "is_cover": True}
    assert client.get(data["photos"][0]["url"]).data == PNG
    listing = client.get("/api/idps").json["data"]["items"][0]
    assert listing == data


def test_details_related_projects_and_saved_state(client, customer, make_idp, other_designer):
    project = make_idp()
    other = make_idp()
    make_idp(published=False)
    make_idp(designer_id=other_designer.id)
    login(client, customer.email)
    SaveFavouriteController().save(customer.id, project.id)
    data = client.get(f"/api/idps/{project.id}").json["data"]
    assert data["is_saved"] is True
    assert [item["id"] for item in data["other_projects"]] == [other.id]
    assert data["project"]["company"] is None
    assert data["project"]["photos"] == []


def test_draft_visibility_and_missing_project(client, designer, customer, make_idp):
    draft = make_idp(published=False)
    for account in (None, customer):
        if account:
            login(client, account.email)
        response = client.get(f"/api/idps/{draft.id}")
        assert response.status_code == 404
        assert response.json == {"error": {"code": "not_found", "message": "Project not found."}}
    login(client, designer.email)
    assert client.get(f"/api/idps/{draft.id}").status_code == 200
    assert IDP.find_by_id(draft.id).views == 0
    assert client.get("/api/idps/99999").status_code == 404


def test_views_once_per_session_shared_with_html(client, app, make_idp, designer):
    project = make_idp()
    assert client.get(f"/api/idps/{project.id}").json["data"]["is_saved"] is False
    client.get(f"/api/idps/{project.id}")
    assert client.get(f"/idp/{project.id}").status_code == 200
    assert IDP.find_by_id(project.id).views == 1
    app.test_client().get(f"/api/idps/{project.id}")
    assert IDP.find_by_id(project.id).views == 2
    login(client, designer.email)
    client.get(f"/api/idps/{project.id}")
    assert IDP.find_by_id(project.id).views == 2
    assert client.get("/").status_code == 200
