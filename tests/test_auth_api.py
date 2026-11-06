"""JSON authentication contract and interoperability with the HTML session."""
import pytest

from control.update_user_account_controller import UpdateUserAccountController
from entity.user_profile import UserProfile


def sign_in(client, account):
    return client.post("/api/auth/login", json={"email": account.email, "password": "pass123"})


@pytest.mark.parametrize("fixture", ["customer", "designer", "admin", "manager"])
def test_login_preserves_role_and_restores_session(client, request, fixture):
    account = request.getfixturevalue(fixture)
    with client.session_transaction() as session:
        session["old_value"] = "discard"
    response = sign_in(client, account)
    expected = {"id": account.id, "name": account.name, "email": account.email,
                "role": account.role, "status": "Active"}
    assert response.status_code == 200
    assert response.json == {"data": {"user": expected}}
    assert client.get("/api/auth/me").json == response.json
    with client.session_transaction() as session:
        assert session["role"] == account.role
        assert "old_value" not in session


def test_invalid_credentials(client, customer):
    response = client.post("/api/auth/login", json={"email": customer.email, "password": "wrong"})
    assert response.status_code == 401
    assert response.json["error"]["code"] == "invalid_credentials"
    assert client.get("/api/auth/me").status_code == 401


@pytest.mark.parametrize("payload", [None, [], {"email": 123, "password": []}, {},
                                     {"email": "x@example.com", "password": ""}])
def test_bad_login_payload_is_json_error(client, payload):
    response = client.post("/api/auth/login", json=payload)
    assert response.status_code == 400
    assert set(response.json) == {"error"}
    assert set(response.json["error"]) == {"code", "message"}


def test_malformed_json(client):
    response = client.post("/api/auth/login", data="{", content_type="application/json")
    assert response.status_code == 400
    assert response.json["error"]["code"] == "invalid_request"


def test_registration_requires_login_and_cannot_choose_role(client):
    payload = {"name": "New Customer", "email": "new@example.com", "password": "password123",
               "confirm_password": "password123", "role": "UserAdmin"}
    response = client.post("/api/customers/register", json=payload)
    assert response.status_code == 201
    user = response.json["data"]["user"]
    assert set(user) == {"id", "name", "email", "role", "status"}
    assert user["role"] == "Customer"
    assert response.json["data"]["login_required"] is True
    assert client.get("/api/auth/me").status_code == 401
    assert client.post("/api/auth/login", json={"email": payload["email"],
                                               "password": payload["password"]}).status_code == 200
    assert client.post("/api/customers/register", json=payload).status_code == 400


@pytest.mark.parametrize("changes", [{"password": "short", "confirm_password": "short"},
                                      {"confirm_password": "different"}, {"email": "invalid"},
                                      {"name": []}])
def test_registration_validation(client, changes):
    payload = dict(name="New", email="new@example.com", password="password123",
                   confirm_password="password123")
    payload.update(changes)
    response = client.post("/api/customers/register", json=payload)
    assert response.status_code == 400
    assert response.json["error"]["code"] == "invalid_request"


@pytest.mark.parametrize("suspend_profile", [False, True])
def test_suspension_invalidates_restoration_and_login(client, customer, suspend_profile):
    sign_in(client, customer)
    if suspend_profile:
        UserProfile.find_by_name("Customer").suspend()
    else:
        customer.suspend()
    assert client.get("/api/auth/me").status_code == 401
    assert sign_in(client, customer).status_code == 401
    with client.session_transaction() as session:
        assert "user_id" not in session


def test_me_refreshes_account_details(client, customer):
    sign_in(client, customer)
    UpdateUserAccountController().update_account(customer.id, "Updated", customer.email, "InteriorDesigner")
    user = client.get("/api/auth/me").json["data"]["user"]
    assert (user["name"], user["role"]) == ("Updated", "InteriorDesigner")


def test_html_login_restores_via_api_and_logout_clears_session(client, customer):
    assert client.post("/login", data={"email": customer.email, "password": "pass123"}).status_code == 302
    assert client.get("/api/auth/me").json["data"]["user"]["id"] == customer.id
    assert client.post("/api/auth/logout").json == {"data": {"logged_out": True}}
    assert client.get("/api/auth/me").status_code == 401
    assert client.post("/api/auth/logout").status_code == 200


def test_api_login_works_with_html_routes(client, admin):
    sign_in(client, admin)
    assert client.get("/admin/accounts").status_code == 200
    assert client.get("/logout").status_code == 302
    assert client.get("/api/auth/me").status_code == 401
