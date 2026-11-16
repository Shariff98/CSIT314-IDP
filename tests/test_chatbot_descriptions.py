"""Rooms are kept, and extra needs ("lots of storage") are matched against project descriptions.

The AI only re-orders a shortlist that Python made, can move a score by at most AI_WEIGHT,
and its reasons are kept only when the quoted words are really in the description.
Still at most two LLM calls per message.
"""
import pytest

from control.recommend_idps_controller import AI_WEIGHT, RecommendIDPsController, apply_ranking
from tests.chatbot_helpers import FakeLLMGateway, FakeRankingGateway, make_idp

STORAGE = "A modern kitchen with a pull-out pantry with lots of storage and warm oak finishes."
PLAIN = "A modern kitchen renovation."
NEEDS = {"budget": 10_000, "category": "Kitchen", "needs": ["lots of storage"]}


@pytest.fixture
def kitchens(app):
    """Two near-identical best-fit kitchens: the plain one is exactly on budget, so Python prefers it."""
    plain = make_idp(10_000, description=PLAIN)
    storage = make_idp(10_200, description=STORAGE)
    others = [make_idp(b, description=PLAIN) for b in (11_000, 11_800, 12_900)]
    return plain, storage, others


def ask(gateway, message="kitchen around $10k with lots of storage", context=None):
    return RecommendIDPsController(gateway).recommend(message, context=context)


def test_needs_reorder_the_shortlist_with_still_only_two_calls(kitchens):
    plain, storage, _ = kitchens
    fake = FakeRankingGateway(prefs=NEEDS, ranking={
        "scores": {str(storage.id): 1, str(plain.id): 0},
        "reasons": {str(storage.id): {"reason": "Has the storage you asked for", "quote": "lots of storage"}}})
    result = ask(fake)
    ids = [p["id"] for p in result["projects"]]
    assert storage.id in ids and plain.id not in ids
    assert [c[0] for c in fake.calls] == ["extract", "rank"]          # no write_reply: two calls in total
    assert f"#{storage.id}" in result["reply"] and "Has the storage you asked for" in result["reply"]
    card = next(p for p in result["projects"] if p["id"] == storage.id)
    assert "Lots of storage" in card["reasons"]                       # the matching words become a chip


def test_ai_sees_descriptions_but_no_prices(kitchens):
    fake = FakeRankingGateway(prefs=NEEDS)
    ask(fake)
    assert fake.ranked and all("budget" not in p for p in fake.ranked)
    assert any(p["description"] == STORAGE for p in fake.ranked)


def test_ai_cannot_add_projects_or_fake_quotes(kitchens):
    plain, storage, _ = kitchens
    outside = make_idp(40_000, description=STORAGE)                    # outside the budget window
    fake = FakeRankingGateway(prefs=NEEDS, ranking={
        "scores": {str(outside.id): 1, "9999": 1},
        "reasons": {str(outside.id): {"reason": "Best", "quote": "lots of storage"},
                    "9999": {"reason": "Invented", "quote": "x"},
                    str(storage.id): {"reason": "Has a sauna", "quote": "a private sauna"},
                    str(plain.id): {"reason": "Only $1 today", "quote": "modern kitchen"}}})
    result = ask(fake)
    ids = {p["id"] for p in result["projects"]}
    assert outside.id not in ids and 9999 not in ids
    assert "#9999" not in result["reply"] and "#%d" % outside.id not in result["reply"]
    assert "sauna" not in result["reply"] and "$1 today" not in result["reply"]


def test_ai_score_moves_a_project_by_at_most_ai_weight(kitchens):
    plain, storage, _ = kitchens
    blended, _ = apply_ranking([(plain, 0.9), (storage, 0.2)], {"scores": {str(plain.id): -5, str(storage.id): 99}})
    scores = {idp.id: score for idp, score in blended}
    assert scores[plain.id] == pytest.approx(0.9 * (1 - AI_WEIGHT))            # clamped to 0
    assert scores[storage.id] == pytest.approx(0.2 * (1 - AI_WEIGHT) + AI_WEIGHT)  # clamped to 1
    blended, _ = apply_ranking([(plain, 0.5)], "not even a dict")
    assert blended[0][1] == pytest.approx(0.5)                                  # missing score is neutral


def test_ranking_outage_still_answers_from_the_database(kitchens):
    fake = FakeRankingGateway(prefs=NEEDS, fail_rank=True)
    result = ask(fake)
    assert len(result["projects"]) == 3 and result["source"] == "llm"
    assert result["reply"].startswith("Here are 3 projects for a budget of $10,000")
    assert [c[0] for c in fake.calls] == ["extract", "rank"]


def test_switch_turns_ranking_off(kitchens, monkeypatch):
    monkeypatch.setenv("CHAT_RERANK", "0")
    fake = FakeRankingGateway(prefs=NEEDS)
    ask(fake)
    assert [c[0] for c in fake.calls] == ["extract", "reply"]


def test_no_needs_works_exactly_as_before(kitchens):
    fake = FakeRankingGateway(prefs={"budget": 10_000, "category": "Kitchen"})
    ask(fake, "kitchen around $10k")
    assert [c[0] for c in fake.calls] == ["extract", "reply"]


def test_needs_are_cleaned_and_remembered(kitchens):
    make_idp(10_000, category="Bathroom"), make_idp(11_000, category="Bathroom"), make_idp(12_000, category="Bathroom")
    messy = {**NEEDS, "needs": ["  lots of   storage ", "LOTS OF STORAGE", 42, "x" * 80, "a", "b", "c", "d"]}
    first = ask(FakeLLMGateway(prefs=messy))
    assert first["prefs"]["needs"] == ["lots of storage", "x" * 40, "a", "b", "c"]
    second = ask(FakeLLMGateway(prefs={"category": "Bathroom"}), "what about bathrooms?", context=first["prefs"])
    assert second["prefs"]["needs"] == first["prefs"]["needs"]
    assert {p["category"] for p in second["projects"]} == {"Bathroom"}


def test_strict_budget_tops_up_with_cheaper_projects_in_the_same_room(app):
    make_idp(10_000), make_idp(6_000), make_idp(6_500), make_idp(10_400), make_idp(9_000, category="Office")
    result = ask(FakeLLMGateway(prefs={"budget": 10_000, "category": "Kitchen", "strict_max": True}),
                 "kitchen no more than $10k")
    assert {p["category"] for p in result["projects"]} == {"Kitchen"}
    assert all(p["budget"] <= 10_000 for p in result["projects"])


@pytest.mark.parametrize("budget_min", [None, 8_000])
def test_sparse_room_never_exceeds_a_hard_ceiling(app, budget_min):
    within = make_idp(9_500)
    make_idp(10_400)
    make_idp(10_800)
    make_idp(9_000, category="Office")
    prefs = {"budget": 10_000, "budget_min": budget_min, "category": "Kitchen", "strict_max": True}
    result = ask(FakeLLMGateway(prefs=prefs))
    assert [project["id"] for project in result["projects"]] == [within.id]


def test_room_with_no_projects_offers_any_room(app):
    make_idp(10_000, category="Bedroom"), make_idp(10_500, category="Bedroom"), make_idp(11_000, category="Office")
    result = ask(FakeLLMGateway(prefs={"budget": 10_000, "category": "Kitchen"}), "kitchen around $10k")
    assert result["projects"] == [] and "any room" in result["reply"]
    assert result["suggestions"] == ["Any room"]
    again = ask(FakeLLMGateway(prefs={}), "any room", context=result["prefs"])
    assert again["prefs"]["category"] is None and len(again["projects"]) == 3
