"""Smarter understanding: budget ranges, style synonyms and exclusions, plurals, and small talk."""
import pytest

from control import budget_parser
from control.recommend_idps_controller import RecommendIDPsController, budget_window
from tests.chatbot_helpers import FakeLLMGateway, make_idp

CATEGORIES = ["Bathroom", "Bedroom", "Kitchen", "Living Room", "Office", "Study", "Kids Room"]
STYLES = ["Classic", "Industrial", "Japandi", "Luxury", "Minimalist", "Modern", "Rustic", "Scandinavian"]


# ---------- parser ----------
@pytest.mark.parametrize("text, expected", [
    ("between $8k and $12k", (8_000, 12_000)),
    ("8-12k please", (8_000, 12_000)),
    ("from 8,000 to 12,000", (8_000, 12_000)),
    ("$9,500 – $11,000", (9_500, 11_000)),
    ("2 to 3 bedrooms", None),           # not money
    ("12k to 8k", None),                 # backwards
    ("around $10k", None),
])
def test_parse_range(text, expected):
    assert budget_parser.parse_range(text) == expected


def test_range_becomes_budget_and_floor():
    prefs = budget_parser.parse("kitchen between $8k and $12k", CATEGORIES, STYLES)
    assert (prefs["budget_min"], prefs["budget"], prefs["strict_max"]) == (8_000, 12_000, True)


@pytest.mark.parametrize("text, style", [
    ("a scandi bedroom", "Scandinavian"), ("nordic vibes", "Scandinavian"), ("japanese study", "Japandi"),
    ("farmhouse kitchen", "Rustic"), ("something high-end", "Luxury"), ("traditional living room", "Classic"),
])
def test_style_synonyms(text, style):
    assert budget_parser.parse(text, CATEGORIES, STYLES)["styles"] == [style]


@pytest.mark.parametrize("text", ["modern but not industrial", "modern, no industrial please",
                                  "modern without the loft look", "I hate industrial, modern is nice"])
def test_style_exclusions(text):
    prefs = budget_parser.parse(text, CATEGORIES, STYLES)
    assert prefs["styles"] == ["Modern"] and prefs["exclude_styles"] == ["Industrial"]


def test_plural_rooms_and_exact_category_names():
    assert budget_parser.parse("two bathrooms 15k", CATEGORIES)["category"] == "Bathroom"
    assert budget_parser.parse("a study nook 6k", CATEGORIES)["category"] == "Study"
    assert budget_parser.parse("a study nook 6k", ["Office"])["category"] == "Office"   # synonym when no Study
    assert budget_parser.parse("kids room 9000", CATEGORIES)["category"] == "Kids Room"


@pytest.mark.parametrize("text, intent", [
    ("hi", "greeting"), ("Hello there!", "greeting"), ("thanks!", "thanks"), ("what can you do?", "help"),
    ("kitchen 10k", None), ("this is the third one", None),
])
def test_detect_intent(text, intent):
    assert budget_parser.detect_intent(text) == intent


# ---------- controller ----------
def offline():
    return RecommendIDPsController(FakeLLMGateway(fail=True))


def test_range_only_returns_projects_inside_it(app):
    for budget in (7_000, 8_500, 9_500, 11_000, 11_900, 12_500, 15_000):
        make_idp(budget)
    result = offline().recommend("kitchen between $8k and $12k")
    assert result["projects"] and all(8_000 <= p["budget"] <= 12_000 for p in result["projects"])


def test_widened_range_lowers_only_the_floor():
    assert budget_window(12_000, True, widened=False, budget_min=8_000) == (8_000, 12_000)
    assert budget_window(12_000, True, widened=True, budget_min=8_000) == (7_200, 12_000)


def test_excluded_styles_are_never_shown_even_after_relaxing(app):
    for budget in (9_500, 10_000, 10_500, 11_000):
        make_idp(budget, styles="Industrial")
    keep = [make_idp(b, styles=s) for b, s in ((9_800, "Modern"), (10_200, "Classic"), (12_000, "Rustic"))]
    result = offline().recommend("kitchen around 10k, not industrial")
    assert {p["id"] for p in result["projects"]} == {i.id for i in keep}


def test_exclusions_add_up_across_messages(app):
    make_idp(10_000, styles="Industrial,Rustic")
    first = offline().recommend("kitchen 10k, not industrial")
    second = offline().recommend("and no rustic", context=first["prefs"])
    assert second["prefs"]["exclude_styles"] == ["Industrial", "Rustic"]


def test_asking_for_an_excluded_style_cancels_the_exclusion(app):
    make_idp(10_000, styles="Industrial")
    first = offline().recommend("kitchen 10k, not industrial")
    second = offline().recommend("actually industrial is fine", context=first["prefs"])
    assert second["prefs"]["styles"] == ["Industrial"] and second["prefs"]["exclude_styles"] == []


@pytest.mark.parametrize("message, start", [("hi", "Hi!"), ("thanks", "You're welcome"),
                                            ("what can you do?", "I match you"), ("blah blah", "I match you")])
def test_small_talk_gets_a_proper_answer(app, message, start):
    result = offline().recommend(message)
    assert result["reply"].startswith(start) and result["projects"] == []


def test_greeting_with_a_request_still_searches(app):
    for budget in (9_500, 10_000, 11_000):
        make_idp(budget)
    assert len(offline().recommend("hi! modern kitchen around 10k")["projects"]) == 3


def test_llm_range_and_exclusions_are_validated(app):
    llm = FakeLLMGateway(prefs={"budget": 12_000, "budget_min": 15_000, "styles": ["Modern", "Industrial"],
                                "exclude_styles": ["Industrial", "Made Up"]})
    make_idp(10_000, styles="Modern,Industrial")
    prefs = RecommendIDPsController(llm).recommend("modern 12k not industrial")["prefs"]
    assert prefs["budget_min"] is None                  # floor above the top is dropped
    assert prefs["styles"] == ["Modern"] and prefs["exclude_styles"] == ["Industrial"]


def test_range_picks_spread_across_the_range_with_range_labels(app):
    for budget in (8_200, 9_000, 11_000, 11_500, 14_000, 14_800):
        make_idp(budget)
    result = offline().recommend("kitchen between $8k and $15k")
    assert [p["label"] for p in result["projects"]] == [
        "Lower end of your range", "Middle of your range", "Top of your range"]
    assert result["reply"].startswith("Here are 3 projects for $8,000 to $15,000")
