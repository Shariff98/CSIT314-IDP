"""JSON API used by the React designer pages: own project (US-27, 04, 05, 06, 26, 33, 55),
analytics (US-29, 46, 57, 48), company profile (US-02, 24, 32, 25, 12, 14, 13, 52)
and the public designer directory / company page (US-53)."""
import io

import pytest

from entity.company import Company
from entity.favourite import Favourite
from entity.user_account import UserAccount
from tests.conftest import PNG, login


@pytest.fixture
def project(make_idp):
    return make_idp("Warm kitchen", category="Kitchen", budget=12000, style_tags="Modern", published=False)


def photo(name="room.png"):
    return {"photo": (io.BytesIO(PNG), name)}


# ---------- own project ----------

def test_view_my_project_includes_drafts_and_shortlists(client, designer, project):
    login(client, designer.email)
    res = client.get(f"/api/designer/portfolio/{project.id}")
    assert res.status_code == 200
    data = res.json["data"]["project"]
    assert data["id"] == project.id and data["published"] is False and data["shortlists"] == 0


def test_someone_elses_project_is_not_found_for_every_action(client, other_designer, project):
    login(client, other_designer.email)
    base = f"/api/designer/portfolio/{project.id}"
    assert client.get(base).status_code == 404
    assert client.put(base, json={"title": "x"}).status_code == 404
    assert client.delete(base).status_code == 404
    assert client.put(f"{base}/tags", json={"category": "Kitchen", "style_tags": "Modern"}).status_code == 404
    assert client.put(f"{base}/status", json={"status": "Past"}).status_code == 404
    assert client.put(f"{base}/publish", json={"published": True}).status_code == 404
    assert client.post(f"{base}/photos", data=photo(), content_type="multipart/form-data").status_code == 404


def test_customers_and_visitors_cannot_use_the_designer_api(client, customer, project):
    assert client.get(f"/api/designer/portfolio/{project.id}").status_code == 401
    login(client, customer.email)
    res = client.get(f"/api/designer/portfolio/{project.id}")
    assert res.status_code == 403 and res.json["error"]["message"] == "An InteriorDesigner account is required."


def test_update_project(client, designer, project):
    login(client, designer.email)
    res = client.put(f"/api/designer/portfolio/{project.id}", json=dict(
        title="Bright kitchen", description="New tones", category="Kitchen", budget=15000,
        property_type="Condo", location="Bishan", completion_date="2026-03-01"))
    assert res.status_code == 200
    data = res.json["data"]["project"]
    assert (data["title"], data["budget"], data["location"]) == ("Bright kitchen", 15000, "Bishan")


@pytest.mark.parametrize("changes, message", [
    ({"budget": 0}, "Budget"), ({"budget": True}, "true/false"), ({"title": ["x"]}, "title must be text"),
    ({"category": "Nope"}, "active category"), ({"property_type": "Castle"}, "Property type"),
])
def test_update_rejects_bad_input(client, designer, project, changes, message):
    login(client, designer.email)
    body = dict(title="T", description="D", category="Kitchen", budget=1000, **{})
    body.update(changes)
    res = client.put(f"/api/designer/portfolio/{project.id}", json=body)
    assert res.status_code == 400 and message in res.json["error"]["message"]


def test_update_needs_a_json_object(client, designer, project):
    login(client, designer.email)
    res = client.put(f"/api/designer/portfolio/{project.id}", data="nope", content_type="text/plain")
    assert res.status_code == 400 and "JSON object" in res.json["error"]["message"]


def test_assign_tags_accepts_text_or_list(client, designer, project):
    login(client, designer.email)
    base = f"/api/designer/portfolio/{project.id}/tags"
    res = client.put(base, json={"category": "Bedroom", "style_tags": ["japandi", "Modern"]})
    assert res.json["data"]["project"]["style_tags"] == ["Japandi", "Modern"]
    assert res.json["data"]["project"]["category"] == "Bedroom"
    res = client.put(base, json={"category": "Bedroom", "style_tags": "a, b, c, d, e, f"})
    assert res.status_code == 400 and "at most 5" in res.json["error"]["message"]


def test_mark_status_past_sets_completion_date(client, designer, project):
    login(client, designer.email)
    res = client.put(f"/api/designer/portfolio/{project.id}/status", json={"status": "Past"})
    assert res.json["data"]["project"]["status"] == "Past"
    assert res.json["data"]["project"]["completion_date"]
    assert client.put(f"/api/designer/portfolio/{project.id}/status", json={"status": "Old"}).status_code == 400


def test_publish_and_unpublish_change_what_customers_see(client, designer, project):
    login(client, designer.email)
    base = f"/api/designer/portfolio/{project.id}/publish"
    res = client.put(base, json={"published": True})
    assert res.json["data"]["result"] == "published" and res.json["data"]["project"]["published"] is True
    assert client.get("/api/idps").json["data"]["total"] == 1
    assert client.put(base, json={"published": False}).json["data"]["result"] == "unpublished"
    assert client.get("/api/idps").json["data"]["total"] == 0
    assert client.put(base, json={"published": "yes"}).status_code == 400


def test_upload_photos_set_cover_and_delete(client, designer, project):
    login(client, designer.email)
    base = f"/api/designer/portfolio/{project.id}/photos"
    first = client.post(base, data=photo("a.png"), content_type="multipart/form-data")
    assert first.status_code == 201
    second = client.post(base, data=photo("b.png"), content_type="multipart/form-data").json["data"]["project"]
    photos = second["photos"]
    assert len(photos) == 2 and photos[0]["is_cover"] is True
    other = photos[1]["id"]
    covered = client.put(f"/api/designer/photos/{other}/cover").json["data"]["project"]["photos"]
    assert covered[0]["id"] == other and covered[0]["is_cover"] is True  # the cover is listed first
    left = client.delete(f"/api/designer/photos/{other}").json["data"]["project"]["photos"]
    assert len(left) == 1 and left[0]["is_cover"] is True                # the next photo becomes the cover


def test_upload_rejects_missing_or_non_image_files(client, designer, project):
    login(client, designer.email)
    base = f"/api/designer/portfolio/{project.id}/photos"
    assert client.post(base, data={}, content_type="multipart/form-data").status_code == 400
    bad = client.post(base, data={"photo": (io.BytesIO(b"not an image"), "notes.txt")}, content_type="multipart/form-data")
    assert bad.status_code == 400


def test_other_designers_photo_is_not_found(client, designer, other_designer, project):
    login(client, designer.email)
    photo_id = client.post(f"/api/designer/portfolio/{project.id}/photos", data=photo(),
                           content_type="multipart/form-data").json["data"]["project"]["photos"][0]["id"]
    login(client, other_designer.email)
    assert client.put(f"/api/designer/photos/{photo_id}/cover").status_code == 404
    assert client.delete(f"/api/designer/photos/{photo_id}").status_code == 404


def test_delete_project(client, designer, project):
    login(client, designer.email)
    res = client.delete(f"/api/designer/portfolio/{project.id}")
    assert res.json["data"] == {"project_id": project.id, "deleted": True}
    assert client.get(f"/api/designer/portfolio/{project.id}").status_code == 404


# ---------- analytics ----------

def test_analytics_dashboard_counts_views_and_shortlists(client, designer, customer, make_idp):
    kitchen, bath = make_idp("Kitchen"), make_idp("Bath")
    for idp, views in ((kitchen, 12), (bath, 3)):
        for n in range(views):
            idp.record_view(customer.id, f"session-{n}")
    Favourite.add(customer.id, kitchen.id)
    login(client, designer.email)
    data = client.get("/api/designer/analytics").json["data"]
    assert data["summary"]["projects"] == 2 and data["summary"]["views"] == 15
    assert data["summary"]["top_project"]["id"] == kitchen.id
    assert data["views"]["total"] == 15
    assert data["shortlists"]["total"] == 1 and data["shortlists"]["rows"][0]["id"] == kitchen.id
    assert data["unread_notifications"] == 0 and data["notifications"] == []


def test_analytics_only_shows_own_projects(client, other_designer, make_idp):
    make_idp("Not yours")
    login(client, other_designer.email)
    assert client.get("/api/designer/analytics").json["data"]["summary"]["projects"] == 0


# ---------- own company ----------

COMPANY = dict(name="Studio Dana", registration_no="20240001A", address="1 Road", phone="61234567",
               email="studio@example.com", description="Calm homes")


def test_company_is_null_until_created_then_can_be_updated(client, designer):
    login(client, designer.email)
    assert client.get("/api/designer/company").json["data"] == {"company": None, "team": []}
    assert client.put("/api/designer/company", json=COMPANY).status_code == 404
    created = client.post("/api/designer/company", json=COMPANY)
    assert created.status_code == 201 and created.json["data"]["company"]["name"] == "Studio Dana"
    assert client.post("/api/designer/company", json=COMPANY).status_code == 400   # only one per designer
    updated = client.put("/api/designer/company", json={**COMPANY, "name": "Studio D"})
    assert updated.json["data"]["company"]["name"] == "Studio D"


def test_company_sections_team_and_images(client, designer):
    login(client, designer.email)
    client.post("/api/designer/company", json=COMPANY)
    res = client.put("/api/designer/company/specialisations", json={"specialisations": ["Modern", "Japandi"],
                                                                    "service_areas": "North, East"})
    assert res.json["data"]["company"]["specialisations"] == ["Modern", "Japandi"]
    res = client.put("/api/designer/company/credentials", json={"certifications": "BCA", "awards": "",
                                                                "years_experience": 7})
    assert res.json["data"]["company"]["years_experience"] == 7
    res = client.put("/api/designer/company/services", json={"budget_min": 20000, "budget_max": 9000,
                                                             "services": "Carpentry"})
    assert res.status_code == 400
    res = client.put("/api/designer/company/services", json={"budget_min": 9000, "budget_max": 20000,
                                                             "services": ["Carpentry"]})
    assert res.json["data"]["company"]["budget_max"] == 20000
    team = client.post("/api/designer/company/team", json={"name": "Ann", "position": "Lead"}).json["data"]["team"]
    assert team[0]["name"] == "Ann"
    assert client.delete(f"/api/designer/company/team/{team[0]['id']}").json["data"]["team"] == []
    assert client.delete("/api/designer/company/team/999").status_code == 400
    logo = client.post("/api/designer/company/images", data={"kind": "logo", "image": (io.BytesIO(PNG), "l.png")},
                       content_type="multipart/form-data")
    assert logo.json["data"]["company"]["logo_url"].startswith("/uploads/")


def test_company_details_must_be_text(client, designer):
    login(client, designer.email)
    assert client.post("/api/designer/company", json={**COMPANY, "phone": 61234567}).status_code == 400


# ---------- public designer directory ----------

def make_company(designer, name, specialisations="Modern", areas="North", budget_min=20000):
    company = Company.create(designer.id, name, f"REG{designer.id:05d}X", "1 Road", "61234567",
                             f"{designer.id}@example.com", "Studio")
    company.save(specialisations=specialisations, service_areas=areas, budget_min=budget_min, budget_max=90000)
    return company


def test_designer_directory_lists_active_companies_with_filters(client, designer, other_designer, make_idp):
    make_company(designer, "Alpha Interiors", "Modern, Japandi", "North", 10000)
    make_company(other_designer, "Beta Studio", "Industrial", "East", 50000)
    make_idp("Shown")
    data = client.get("/api/designers").json["data"]
    assert [d["name"] for d in data["items"]] == ["Alpha Interiors", "Beta Studio"]   # most projects first
    assert data["items"][0]["project_count"] == 1
    assert "Japandi" in data["options"]["specialisations"] and data["options"]["service_areas"] == ["East", "North"]
    names = lambda query: [d["name"] for d in client.get(f"/api/designers?{query}").json["data"]["items"]]
    assert names("specialisation=Japandi") == ["Alpha Interiors"]
    assert names("service_area=East") == ["Beta Studio"]
    assert names("max_budget=20000") == ["Alpha Interiors"]
    assert names("q=beta") == ["Beta Studio"]
    assert client.get("/api/designers?max_budget=abc").status_code == 400


def test_suspended_designers_are_hidden(client, designer):
    make_company(designer, "Alpha Interiors")
    UserAccount.find_by_id(designer.id).suspend()
    assert client.get("/api/designers").json["data"]["total"] == 0
    assert client.get(f"/api/designers/{designer.id}").status_code == 404


def test_company_page_shows_team_and_published_projects_only(client, designer, make_idp):
    make_company(designer, "Alpha Interiors")
    make_idp("Published one")
    make_idp("Secret draft", published=False)
    data = client.get(f"/api/designers/{designer.id}").json["data"]
    assert data["company"]["name"] == "Alpha Interiors" and data["designer"]["id"] == designer.id
    assert [p["title"] for p in data["projects"]] == ["Published one"]


def test_unknown_api_paths_answer_in_json(client):
    res = client.get("/api/nothing-here")
    assert res.status_code == 404 and res.json["error"]["code"] == "not_found"
    assert client.delete("/api/idps").json["error"]["code"] == "method_not_allowed"


def test_designer_api_rejects_missing_role_profile(client, designer):
    from entity.db import get_connection
    login(client, designer.email)
    with get_connection() as connection:
        connection.execute("DELETE FROM user_profile WHERE name = ?", ("InteriorDesigner",))
    assert client.get("/api/designer/portfolio").status_code == 401
