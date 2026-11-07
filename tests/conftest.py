import pytest

from app import create_app
from entity.idp import IDP
from entity.user_account import UserAccount

# The smallest valid PNG file (1x1 pixel), used to test uploads.
PNG = (b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
       b"\x00\x00\x00\rIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82")


@pytest.fixture
def fake_llm():
    """Stands in for the LLM service, so the chatbot tests need no API key or internet."""
    from tests.chatbot_helpers import FakeLLMGateway
    return FakeLLMGateway()


@pytest.fixture
def app(tmp_path, fake_llm):
    """Every test gets a fresh, empty database file and upload folder."""
    return create_app(db_path=str(tmp_path / "test.db"), upload_dir=str(tmp_path / "uploads"), llm_gateway=fake_llm)


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def designer(app):
    return UserAccount.create("Dana Designer", "dana@example.com", "pass123", "InteriorDesigner")


@pytest.fixture
def other_designer(app):
    return UserAccount.create("Olly Other", "olly@example.com", "pass123", "InteriorDesigner")


@pytest.fixture
def customer(app):
    return UserAccount.create("Chris Customer", "chris@example.com", "pass123", "Customer")


@pytest.fixture
def admin(app):
    return UserAccount.create("Ada Admin", "ada@example.com", "pass123", "UserAdmin")


@pytest.fixture
def manager(app):
    return UserAccount.create("Pat Manager", "pat@example.com", "pass123", "PlatformManager")


@pytest.fixture
def make_idp(designer):
    """make_idp(title=..., **fields) creates a project straight through the entity."""
    def _make(title="Cosy Bedroom", designer_id=None, **fields):
        values = dict(description="Warm tones", category="Bedroom", budget=8000)
        values.update(fields)
        return IDP.create(designer_id or designer.id, title, **values)
    return _make


def login(client, email, password="pass123"):
    return client.post("/login", data={"email": email, "password": password})
