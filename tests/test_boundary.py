"""End-to-end checks through the web pages (boundary layer) for all four roles."""
import pytest

from entity.category import Category
from entity.idp import IDP
from entity.user_account import UserAccount
from tests.conftest import PNG, login


def test_designer_creates_project_then_customer_saves_it(client, designer, customer):
    login(client, "dana@example.com")
    resp = client.post("/idp/new", data={"title": "Loft Office", "description": "Industrial",
                                         "category": "Office", "budget": "15000"})
    assert resp.status_code == 302

    client.get("/logout")
    login(client, "chris@example.com")
    assert b"Loft Office" in client.get("/?q=loft").data
    assert b"1 views" in client.get("/idp/1").data
    assert b"1 views" in client.get("/idp/1").data          # same session: still 1 view (US-37)
    client.post("/idp/1/save")
    assert b"Loft Office" in client.get("/favourites").data
    client.post("/idp/1/unsave")
    assert b"Loft Office" not in client.get("/favourites").data


def test_customer_cannot_open_create_page(client, customer):
    login(client, "chris@example.com")
    assert client.get("/idp/new").status_code == 302


@pytest.mark.parametrize("path", ["/admin/accounts", "/platform/", "/my/idps", "/analytics/", "/favourites"])
def test_pages_need_the_right_role(client, path):
    resp = client.get(path)
    assert resp.status_code == 302 and "/login" in resp.headers["Location"]


def test_login_sends_each_role_to_its_home_page(client, admin, manager, designer, customer):
    homes = {"ada@example.com": "/admin/accounts", "pat@example.com": "/platform/",
             "dana@example.com": "/my/idps", "chris@example.com": "/"}
    for email, home in homes.items():
        assert login(client, email).headers["Location"] == home
        client.get("/logout")


def test_wrong_password_shows_error(client, customer):
    resp = client.post("/login", data={"email": "chris@example.com", "password": "nope"})
    assert resp.status_code == 401 and b"Invalid email or password" in resp.data


def test_register_then_log_in(client):
    resp = client.post("/register", data={"name": "Nina", "email": "nina@example.com", "password": "longpassword",
                                          "confirm_password": "longpassword"})
    assert resp.status_code == 302
    assert login(client, "nina@example.com", "longpassword").status_code == 302


def test_admin_pages(client, admin, customer):
    login(client, "ada@example.com")
    for path in ["/admin/accounts", "/admin/accounts?q=chris&role=Customer&status=Active", "/admin/accounts/new",
                 f"/admin/accounts/{customer.id}/edit", "/admin/profiles", "/admin/profiles/new", "/admin/profiles/1/edit"]:
        assert client.get(path).status_code == 200, path
    resp = client.post("/admin/accounts/new", data={"name": "Neo", "email": "neo@example.com",
                                                    "password": "password1", "role": "InteriorDesigner"})
    assert resp.status_code == 302 and UserAccount.find_by_email("neo@example.com") is not None
    client.post(f"/admin/accounts/{customer.id}/suspend")
    assert UserAccount.find_by_id(customer.id).is_suspended()
    assert client.post("/admin/accounts/new", data={"name": "", "email": "x", "password": "",
                                                    "role": ""}).status_code == 400
    assert client.post("/admin/profiles/new", data={"name": "Moderator", "description": "Reviews"}).status_code == 302


def test_designer_pages(client, designer):
    login(client, "dana@example.com")
    assert client.get("/company").status_code == 302                      # no company yet -> create page
    resp = client.post("/company/new", data={"name": "Dana Co", "registration_no": "DANA-001", "address": "1 St",
                                             "phone": "", "email": "d@co.sg", "description": "Hi"})
    assert resp.status_code == 302
    client.post("/company/specialisations", data={"specialisations": "Modern", "service_areas": "East"})
    client.post("/company/team", data={"name": "Jo", "position": "Designer"})
    client.post("/company/images", data={"kind": "logo", "image": (__import__("io").BytesIO(PNG), "logo.png")},
                content_type="multipart/form-data")
    client.post("/idp/new", data={"title": "Draft Den", "description": "Cosy", "category": "Living Room",
                                  "budget": "5000", "action": "draft"})
    idp = IDP.list_for_designer(designer.id)[0]
    assert not idp.is_published
    client.post(f"/my/idps/{idp.id}/publish", data={"action": "publish"})
    client.post(f"/my/idps/{idp.id}/photos", data={"photo": (__import__("io").BytesIO(PNG), "a.png")},
                content_type="multipart/form-data")
    assert IDP.find_by_id(idp.id).is_published and len(idp.photos()) == 1
    for path in ["/company", "/company/edit", "/company/preview", f"/designers/{designer.id}", "/my/idps",
                 "/my/idps?q=den&status=Published", f"/my/idps/{idp.id}", f"/my/idps/{idp.id}/edit", "/analytics/",
                 "/analytics/views", "/analytics/shortlists", "/analytics/rank?by=shortlists",
                 "/analytics/trend?period=weekly", "/analytics/segment?category=Kitchen", "/analytics/compare",
                 "/analytics/notifications", "/idp/new"]:
        assert client.get(path).status_code == 200, path
    assert client.get("/analytics/export.csv").data.startswith(b"IDP ID,Title")
    assert b"Dana Co" in client.get("/company/preview").data
    client.post(f"/my/idps/{idp.id}/delete")
    assert IDP.find_by_id(idp.id) is None


def test_designer_cannot_touch_another_designers_project(client, designer, other_designer, make_idp):
    idp = make_idp(designer_id=other_designer.id)
    login(client, "dana@example.com")
    assert client.get(f"/my/idps/{idp.id}").status_code == 404
    assert client.post(f"/my/idps/{idp.id}/delete").status_code == 404


def test_platform_manager_pages(client, manager, make_idp):
    make_idp(category="Office")
    login(client, "pat@example.com")
    for path in ["/platform/", "/platform/demand", "/platform/categories", "/platform/categories/new",
                 "/platform/categories/1/edit", "/platform/reports/daily", "/platform/reports/weekly?date=2026-03-04",
                 "/platform/reports/monthly"]:
        assert client.get(path).status_code == 200, path
    assert client.get("/platform/reports/yearly").status_code == 404
    csv_resp = client.get("/platform/reports/weekly/export?format=csv&date=2026-03-04")
    assert csv_resp.mimetype == "text/csv"
    assert client.get("/platform/reports/daily/export?format=pdf").data.startswith(b"%PDF")
    client.post("/platform/categories/new", data={"name": "Gym", "description": "Home gyms"})
    office = Category.find_by_name("Office")
    client.post(f"/platform/categories/{office.id}/suspend", data={"reassign_to": "Kitchen"})
    assert Category.find_by_id(office.id).status == "Suspended"


def test_customer_browse_filters_and_company_page(client, customer, make_idp):
    make_idp("Tampines Kitchen", category="Kitchen", location="Tampines", property_type="HDB")
    login(client, "chris@example.com")
    assert b"Tampines Kitchen" in client.get("/?category=Kitchen&property_type=HDB&sort=views").data
    assert b"Tampines Kitchen" not in client.get("/?category=Bedroom").data
    assert b"Minimum budget" in client.get("/?min_budget=10&max_budget=1").data
    assert client.get("/idp/999").status_code == 404
    assert client.get("/favourites?q=kitchen").status_code == 200
