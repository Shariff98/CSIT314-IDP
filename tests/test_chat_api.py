"""Boundary tests for POST /api/chat and the LLM gateway."""
import json

import pytest

from app import create_app
from boundary.llm_gateway import LLMGateway
from control.recommend_idps_controller import LLMUnavailable
from tests.chatbot_helpers import FakeLLMGateway, make_idp


def test_chat_returns_reply_and_projects(client, fake_llm):
    for b in (9_800, 11_000, 12_500):
        make_idp(b)
    fake_llm.prefs = {"budget": 10_000, "category": "Kitchen"}
    res = client.post("/api/chat", json={"message": "kitchen 10k"})
    assert res.status_code == 200
    body = res.get_json()
    assert set(body) == {"reply", "projects", "relaxed", "source"} and len(body["projects"]) == 3


@pytest.mark.parametrize("payload", [{}, {"message": ""}, {"message": "   "}, {"message": 42}])
def test_empty_message_gives_400(client, payload):
    assert client.post("/api/chat", json=payload).status_code == 400


def test_message_over_500_characters_gives_400(client):
    assert client.post("/api/chat", json={"message": "x" * 501}).status_code == 400


def test_21st_message_in_an_hour_gives_429(tmp_path):
    client = create_app(db_path=str(tmp_path / "t.db"), llm_gateway=FakeLLMGateway(), chat_rate_limit=20).test_client()
    codes = [client.post("/api/chat", json={"message": "hi"}).status_code for _ in range(21)]
    assert codes[:20] == [200] * 20 and codes[20] == 429


def test_api_key_never_appears_in_response(tmp_path):
    secret = "gsk_TEST_SECRET_123"
    gateway = LLMGateway(base_url="http://127.0.0.1:9", api_key=secret, timeout=1)  # nothing listens here
    client = create_app(db_path=str(tmp_path / "t.db"), llm_gateway=gateway).test_client()
    for b in (9_800, 11_000, 12_500):
        make_idp(b)
    res = client.post("/api/chat", json={"message": "kitchen $10k"})
    assert res.status_code == 200 and res.get_json()["source"] == "fallback"
    assert secret not in res.get_data(as_text=True)


def test_gateway_without_key_raises_llm_unavailable():
    with pytest.raises(LLMUnavailable):
        LLMGateway(api_key="").extract_preferences("kitchen 10k", [], ["Kitchen"], [])


def test_gateway_parses_openai_style_json(monkeypatch):
    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def read(self):
            content = json.dumps({"budget": 10000, "category": "Kitchen"})
            return json.dumps({"choices": [{"message": {"content": content}}]}).encode()

    sent = {}

    def fake_urlopen(request, timeout):
        sent["body"] = json.loads(request.data)
        sent["auth"] = request.headers["Authorization"]
        return FakeResponse()

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    prefs = LLMGateway(api_key="k", model="m").extract_preferences("kitchen 10k", [], ["Kitchen"], ["Modern"])
    assert prefs == {"budget": 10000, "category": "Kitchen"}
    assert sent["body"]["response_format"] == {"type": "json_object"} and sent["auth"] == "Bearer k"


def test_demo_pages(client):
    idp = make_idp(10_000)
    assert client.get("/").status_code == 200
    assert client.get(f"/idp/{idp.id}").status_code == 200
    assert client.get("/idp/99999").status_code == 404
