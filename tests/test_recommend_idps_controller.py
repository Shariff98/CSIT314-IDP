"""The use case end to end through the controller, with a fake LLM and a real (temporary) database."""
import pytest

from control.recommend_idps_controller import RecommendIDPsController
from entity.chat_log import ChatLog
from tests.chatbot_helpers import FakeLLMGateway, make_idp


@pytest.fixture
def kitchens(app):
    """Kitchen projects spread across all three bands, by different designers."""
    return [make_idp(b) for b in (8_000, 9_800, 10_000, 11_000, 11_800, 12_900, 14_000, 20_000)]


def recommend(prefs=None, message="modern kitchen around $10k", **fake):
    return RecommendIDPsController(FakeLLMGateway(prefs=prefs, **fake)).recommend(message)


def test_budget_10000_returns_three_in_window_one_per_band(kitchens):
    result = recommend({"budget": 10_000, "category": "Kitchen", "styles": ["Modern"]})
    budgets = [p["budget"] for p in result["projects"]]
    assert len(budgets) == 3 and all(9_000 <= b <= 13_000 for b in budgets)
    assert [p["label"] for p in result["projects"]] == [
        "Best fit for your budget", "Small step up", "Worth stretching for"]
    assert result["source"] == "llm" and result["relaxed"] == []


def test_cards_come_from_the_database(kitchens):
    card = recommend({"budget": 10_000, "category": "Kitchen"})["projects"][0]
    assert set(card) >= {"id", "title", "budget", "category", "designer", "url", "label"}
    assert card["designer"].startswith("Company ") and card["url"] == f"/idp/{card['id']}"


def test_unpublished_projects_are_never_returned(app):
    hidden = [make_idp(b, published=False) for b in (10_000, 10_100, 11_000)]
    shown = [make_idp(b) for b in (9_500, 11_200, 12_500)]
    ids = {p["id"] for p in recommend({"budget": 10_000, "category": "Kitchen"})["projects"]}
    assert ids == {i.id for i in shown} and not ids & {i.id for i in hidden}


def test_strict_max_keeps_every_result_at_or_below_budget(kitchens):
    make_idp(9_300), make_idp(9_600)
    result = recommend({"budget": 10_000, "category": "Kitchen", "strict_max": True})
    assert result["projects"] and all(p["budget"] <= 10_000 for p in result["projects"])


def test_relaxes_style_then_category_and_says_so(app):
    make_idp(10_000, styles="Japandi")
    make_idp(10_500, category="Bedroom", styles="Classic")
    make_idp(11_500, category="Office", styles="Classic")
    result = recommend({"budget": 10_000, "category": "Kitchen", "styles": ["Japandi"]})
    assert result["relaxed"] == ["style", "category"]
    assert len(result["projects"]) == 3


def test_widens_window_when_still_short(app):
    make_idp(10_000), make_idp(14_000), make_idp(14_800)
    result = recommend({"budget": 10_000, "category": "Kitchen"})
    assert result["relaxed"] == ["category", "budget_window"]
    assert max(p["budget"] for p in result["projects"]) == 14_800


def test_reply_line_with_unknown_project_id_is_removed(kitchens):
    result = recommend({"budget": 10_000}, reply="Try #9999, it is only $1!\nGreat picks below.")
    assert "#9999" not in result["reply"] and "Great picks below." in result["reply"]


def test_llm_outage_uses_fallback_parser(kitchens):
    result = recommend(message="kitchen around $10k", fail=True)
    assert result["source"] == "fallback" and len(result["projects"]) == 3
    assert result["reply"].startswith("Here are 3 projects for a budget of $10,000")


def test_reply_failure_still_returns_projects(kitchens):
    result = recommend({"budget": 10_000, "category": "Kitchen"}, fail_reply=True)
    assert len(result["projects"]) == 3 and result["reply"].startswith("Here are 3")


def test_no_budget_asks_a_question(kitchens):
    result = recommend({"budget": None, "category": "Kitchen"}, message="I want a new kitchen")
    assert result["projects"] == [] and "What budget" in result["reply"]


def test_invalid_budget_asks_again(kitchens):
    result = recommend({"budget": -5_000}, message="kitchen -5000")
    assert result["projects"] == [] and "doesn't look right" in result["reply"]


def test_llm_json_is_validated(kitchens):
    """A made-up category or style from the LLM is ignored rather than trusted."""
    result = recommend({"budget": "10000", "category": "Spaceship", "styles": ["Alien", 5]})
    assert len(result["projects"]) == 3 and result["relaxed"] == []


def test_each_request_is_logged(kitchens):
    result = recommend({"budget": 10_000, "category": "Kitchen"})
    log = ChatLog.all()[-1]
    assert log["recommended_ids"] == ",".join(str(p["id"]) for p in result["projects"])
    assert log["source"] == "llm"


def test_empty_message_is_rejected(app):
    with pytest.raises(ValueError):
        RecommendIDPsController(FakeLLMGateway()).recommend("   ")
