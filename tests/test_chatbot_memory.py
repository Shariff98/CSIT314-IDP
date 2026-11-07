"""Multi-turn memory: each answer returns its prefs, and the next message builds on them."""
import pytest

from control.recommend_idps_controller import RecommendIDPsController
from tests.chatbot_helpers import FakeLLMGateway, make_idp


@pytest.fixture
def projects(app):
    for budget in (9_500, 10_000, 11_500, 12_000, 13_500):
        make_idp(budget, category="Kitchen", styles="Modern")
        make_idp(budget, category="Bathroom", styles="Scandinavian")


def offline():
    """The fallback parser on its own, so these tests prove memory works without the LLM."""
    return RecommendIDPsController(FakeLLMGateway(fail=True))


def chat(controller, *messages):
    context, result = None, None
    for message in messages:
        result = controller.recommend(message, context=context)
        context = result["prefs"]
    return result


def test_response_includes_the_prefs_it_used(projects):
    prefs = offline().recommend("modern kitchen around $10k")["prefs"]
    assert prefs["budget"] == 10_000 and prefs["category"] == "Kitchen" and prefs["styles"] == ["Modern"]


def test_budget_given_in_a_later_message_keeps_the_room(projects):
    first = offline().recommend("I want a bathroom")
    assert first["projects"] == [] and "bathroom" in first["reply"] and "budget" in first["reply"]
    result = chat(offline(), "I want a bathroom", "around $12k")
    assert result["prefs"]["category"] == "Bathroom"
    assert {p["category"] for p in result["projects"]} == {"Bathroom"}


def test_changing_the_room_keeps_the_budget(projects):
    result = chat(offline(), "kitchen around $10,000", "what about a bathroom?")
    assert result["prefs"]["budget"] == 10_000 and result["prefs"]["category"] == "Bathroom"
    assert result["projects"] and all(p["category"] == "Bathroom" for p in result["projects"])


def test_new_budget_replaces_the_old_one(projects):
    result = chat(offline(), "kitchen around $10,000", "make it $13,000 instead")
    assert result["prefs"]["budget"] == 13_000 and result["prefs"]["category"] == "Kitchen"


def test_strict_max_carries_over_only_with_its_budget(projects):
    kept = chat(offline(), "kitchen no more than $12,000", "what about a bathroom?")
    assert kept["prefs"]["strict_max"] is True
    replaced = chat(offline(), "kitchen no more than $12,000", "around $13,000")
    assert replaced["prefs"]["strict_max"] is False


def test_start_over_forgets_everything(projects):
    result = chat(offline(), "modern kitchen around $10,000", "start over, I need a bathroom")
    assert result["prefs"]["budget"] is None and result["prefs"]["styles"] == []
    assert result["prefs"]["category"] == "Bathroom"


def test_any_style_clears_only_the_style(projects):
    result = chat(offline(), "modern kitchen around $10,000", "any style is fine")
    assert result["prefs"]["styles"] == [] and result["prefs"]["category"] == "Kitchen"


def test_context_from_the_client_is_checked_like_llm_output(projects):
    forged = {"budget": "lots", "category": "Spaceship", "styles": ["Modern", "<script>"], "strict_max": 1}
    prefs = offline().recommend("kitchen please", context=forged)["prefs"]
    assert prefs["budget"] is None and prefs["category"] == "Kitchen" and prefs["styles"] == ["Modern"]


def test_api_round_trip_uses_context(client, projects):
    first = client.post("/api/chat", json={"message": "bathroom"}).get_json()
    second = client.post("/api/chat", json={"message": "$12k", "context": first["prefs"]}).get_json()
    assert second["prefs"]["budget"] == 12_000
    assert second["projects"]


@pytest.mark.parametrize("context", ["not a dict", 5, ["x"], None])
def test_api_ignores_a_malformed_context(client, projects, context):
    res = client.post("/api/chat", json={"message": "kitchen $10k", "context": context})
    assert res.status_code == 200
