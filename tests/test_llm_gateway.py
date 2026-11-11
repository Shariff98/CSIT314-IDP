"""LLMGateway reliability: the live chatbot must really use Groq, and fail safely when it can't.

No network: a fake opener stands in for urllib.request.urlopen and records each request.
"""
import io
import json
import urllib.error

import pytest

from boundary.llm_gateway import USER_AGENT, LLMGateway, parse_json_object
from control.recommend_idps_controller import LLMUnavailable


def ok(content):
    body = json.dumps({"choices": [{"message": {"content": content}}]}).encode()

    class Response(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False
    return Response(body)


def http_error(status, body=b"", headers=None):
    return urllib.error.HTTPError("https://api.groq.com/openai/v1/chat/completions", status, "error",
                                  headers or {}, io.BytesIO(body))


class FakeOpener:
    """Returns (or raises) the queued results in order and keeps every request it was given."""

    def __init__(self, *results):
        self.results, self.requests = list(results), []

    def __call__(self, request, timeout):
        self.requests.append(request)
        result = self.results.pop(0)
        if isinstance(result, Exception):
            raise result
        return result

    def body(self, n=-1):
        return json.loads(self.requests[n].data)


def gateway(opener, **kwargs):
    kwargs.setdefault("api_key", "gsk_test")
    return LLMGateway(base_url="https://api.groq.com/openai/v1", model="llama-3.3-70b-versatile",
                      fallback_model="llama-3.1-8b-instant", opener=opener, sleep=lambda s: None, **kwargs)


def test_every_request_sends_a_real_user_agent_not_python_urllib():
    # Identify the application explicitly rather than relying on the urllib default.
    opener = FakeOpener(ok("Hi"))
    gateway(opener)._chat([{"role": "user", "content": "hi"}])
    request = opener.requests[0]
    assert request.get_header("User-agent") == USER_AGENT
    assert not request.get_header("User-agent").startswith("Python-urllib")
    assert request.get_header("Authorization") == "Bearer gsk_test"
    assert request.full_url == "https://api.groq.com/openai/v1/chat/completions"


def test_pasted_key_quotes_and_newlines_are_removed():
    assert LLMGateway(api_key='  "gsk_abc"\n').api_key == "gsk_abc"


def test_rate_limit_is_retried_then_succeeds():
    opener = FakeOpener(http_error(429, b'{"error": {"code": "rate_limit_exceeded"}}', {"retry-after": "1"}),
                        ok("Hello"))
    llm = gateway(opener)
    assert llm._chat([{"role": "user", "content": "hi"}]) == "Hello"
    assert len(opener.requests) == 2 and llm.last_call["ok"] is True


def test_timeouts_are_retried():
    opener = FakeOpener(TimeoutError("slow"), ok("Hello"))
    assert gateway(opener)._chat([{"role": "user", "content": "hi"}]) == "Hello"


def test_retired_model_switches_to_the_fallback_model():
    gone = http_error(400, b'{"error": {"code": "model_decommissioned", "message": "The model has been decommissioned"}}')
    opener = FakeOpener(gone, ok("Hi"))
    llm = gateway(opener)
    llm._chat([{"role": "user", "content": "hi"}])
    assert [opener.body(i)["model"] for i in range(2)] == ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]
    assert llm.last_call["model"] == "llama-3.1-8b-instant"


def test_json_mode_rejection_retries_without_json_mode():
    failed = http_error(400, b'{"error": {"code": "json_validate_failed", "message": "Failed to generate JSON"}}')
    opener = FakeOpener(failed, ok('Sure! {"budget": 10000, "category": "Kitchen"}'))
    prefs = gateway(opener).extract_preferences("kitchen $10k", [], ["Kitchen"], ["Modern"])
    assert prefs["budget"] == 10000
    assert "response_format" in opener.body(0) and "response_format" not in opener.body(1)


def test_bad_key_is_not_retried_and_the_error_never_contains_the_key():
    opener = FakeOpener(http_error(401, b'{"error": {"code": "invalid_api_key", "message": "Invalid API Key"}}'))
    llm = gateway(opener, api_key="gsk_secret_value")
    with pytest.raises(LLMUnavailable) as raised:
        llm._chat([{"role": "user", "content": "hi"}])
    assert len(opener.requests) == 1
    assert "gsk_secret_value" not in str(raised.value) and "401" in str(raised.value)
    assert llm.status()["last_call"]["ok"] is False
    assert "gsk_secret_value" not in json.dumps(llm.status())


def test_cloudflare_block_is_explained():
    opener = FakeOpener(http_error(403, b"error code: 1010"))
    with pytest.raises(LLMUnavailable, match="Cloudflare"):
        gateway(opener)._chat([{"role": "user", "content": "hi"}])


def test_gives_up_after_max_attempts():
    opener = FakeOpener(*[http_error(503)] * 5)
    with pytest.raises(LLMUnavailable):
        gateway(opener, max_attempts=3)._chat([{"role": "user", "content": "hi"}])
    assert len(opener.requests) == 3


def test_stops_retrying_when_the_time_budget_is_spent():
    times = iter([0, 25, 25, 25])
    opener = FakeOpener(http_error(503), ok("late"))
    llm = LLMGateway(api_key="k", opener=opener, sleep=lambda s: None, clock=lambda: next(times), time_budget=20)
    with pytest.raises(LLMUnavailable):
        llm._chat([{"role": "user", "content": "hi"}])
    assert len(opener.requests) == 1


def test_no_key_fails_without_any_request():
    opener = FakeOpener()
    with pytest.raises(LLMUnavailable, match="LLM_API_KEY is not set"):
        gateway(opener, api_key="")._chat([{"role": "user", "content": "hi"}])
    assert opener.requests == []


@pytest.mark.parametrize("text", ['{"budget": 5}', '```json\n{"budget": 5}\n```', 'Here you go: {"budget": 5} done'])
def test_json_is_read_from_plain_fenced_or_wrapped_text(text):
    assert parse_json_object(text) == {"budget": 5}


@pytest.mark.parametrize("text", ["no json here", "[1, 2]", "{broken"])
def test_non_objects_are_rejected(text):
    with pytest.raises(LLMUnavailable):
        parse_json_object(text)


def test_ping_and_status_report_the_real_state():
    llm = gateway(FakeOpener(ok("OK")))
    assert llm.status()["configured"] is True and llm.status()["last_call"] is None
    assert llm.ping() == {"ok": True, "reply": "OK"}
    assert llm.status()["last_call"]["ok"] is True and llm.status()["provider"] == "api.groq.com"
    assert gateway(FakeOpener(), api_key="").ping()["ok"] is False


def test_chat_status_endpoint(client):
    res = client.get("/api/chat/status")
    assert res.status_code == 200 and "configured" in res.json


def test_chat_status_check_uses_the_live_gateway(tmp_path):
    from app import create_app
    llm = gateway(FakeOpener(ok("OK")))
    app = create_app(db_path=str(tmp_path / "t.db"), upload_dir=str(tmp_path / "up"), llm_gateway=llm)
    data = app.test_client().get("/api/chat/status?check=1").json
    assert data["check"] == {"ok": True, "reply": "OK"} and data["last_call"]["ok"] is True
    assert data["model"] == "llama-3.3-70b-versatile" and "gsk_test" not in json.dumps(data)


def test_chat_uses_the_llm_end_to_end_when_it_answers(tmp_path):
    """A real LLMGateway (fake network) drives a full chat message: source is "llm", not "fallback"."""
    from app import create_app
    from tests.chatbot_helpers import make_idp
    opener = FakeOpener(ok('{"budget": 10000, "category": "Kitchen", "styles": []}'), ok("Here are some ideas."))
    app = create_app(db_path=str(tmp_path / "t.db"), upload_dir=str(tmp_path / "up"), llm_gateway=gateway(opener))
    with app.app_context():
        for budget in (9500, 10000, 10500):
            make_idp(budget, category="Kitchen")
    res = app.test_client().post("/api/chat", json={"message": "kitchen around $10k"})
    assert res.status_code == 200 and res.json["source"] == "llm" and len(res.json["projects"]) == 3


def test_provider_error_cannot_leak_credentials_or_prompts(caplog):
    secret = "gsk_do_not_log"
    body = json.dumps({"error": {"code": secret, "message": "private prompt " + secret}}).encode()
    llm = gateway(FakeOpener(http_error(400, body)), api_key=secret)
    with pytest.raises(LLMUnavailable):
        llm._chat([{"role": "user", "content": "private prompt"}])
    output = caplog.text + json.dumps(llm.status())
    assert secret not in output and "private prompt" not in output
    assert "HTTP 400" in output


def test_invalid_preference_json_records_failure():
    llm = gateway(FakeOpener(ok("not JSON")))
    with pytest.raises(LLMUnavailable):
        llm.extract_preferences("kitchen", [], ["Kitchen"], [])
    assert llm.status()["last_call"]["ok"] is False


@pytest.mark.parametrize("content", [None, [], "   "])
def test_invalid_content_falls_back_instead_of_crashing(content):
    llm = gateway(FakeOpener(ok(content)))
    with pytest.raises(LLMUnavailable):
        llm._chat([{"role": "user", "content": "hi"}])
    assert llm.status()["last_call"]["ok"] is False
