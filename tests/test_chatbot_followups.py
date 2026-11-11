"""Follow-ups after a search: Show more, Cheaper, A bit more, and the chips that offer them."""
import pytest

from control import budget_parser
from control.recommend_idps_controller import START_CHIPS, RecommendIDPsController
from tests.chatbot_helpers import FakeLLMGateway, make_idp


@pytest.fixture
def kitchens(app):
    return [make_idp(b) for b in (7_600, 8_000, 9_000, 9_600, 10_000, 10_400, 11_000, 11_800, 12_500, 12_900, 14_000)]


def offline():
    return RecommendIDPsController(FakeLLMGateway(fail=True))


def chat(*messages):
    context, result = None, None
    for message in messages:
        result = offline().recommend(message, context=context)
        context = result["prefs"]
    return result


@pytest.mark.parametrize("text, followup", [
    ("Show more", "more"), ("any other options?", "more"), ("something else please", "more"),
    ("Cheaper", "cheaper"), ("that's too expensive", "cheaper"),
    ("A bit more", "pricier"), ("I can stretch a little", "pricier"),
    ("kitchen 10k", None), ("more modern please", None),
])
def test_detect_followup(text, followup):
    assert budget_parser.detect_followup(text) == followup


def test_show_more_never_repeats_a_project(kitchens):
    first = chat("kitchen around $10k")
    second = chat("kitchen around $10k", "Show more")
    first_ids = {p["id"] for p in first["projects"]}
    second_ids = {p["id"] for p in second["projects"]}
    assert len(second_ids) == 3 and not first_ids & second_ids
    assert set(second["prefs"]["seen_ids"]) == first_ids | second_ids


def test_show_more_says_when_it_runs_out(app):
    for b in (9_500, 10_000, 10_500):
        make_idp(b)
    result = chat("kitchen around $10k", "Show more")
    assert result["projects"] == [] and result["reply"].startswith("That's everything")


def test_a_new_search_forgets_what_was_shown(kitchens):
    result = chat("kitchen around $10k", "Show more", "around $12k")
    assert len(result["prefs"]["seen_ids"]) == 3


def test_cheaper_lowers_the_budget_by_a_fifth(kitchens):
    result = chat("kitchen around $10k", "Cheaper")
    assert result["prefs"]["budget"] == 8_000 and result["prefs"]["category"] == "Kitchen"


def test_a_bit_more_raises_the_budget_and_range(kitchens):
    result = chat("kitchen between $8k and $10k", "A bit more")
    assert (result["prefs"]["budget_min"], result["prefs"]["budget"]) == (10_000, 12_500)


def test_cheaper_with_a_new_amount_uses_the_amount(kitchens):
    assert chat("kitchen around $10k", "cheaper, say $9k")["prefs"]["budget"] == 9_000


def test_chips_after_results(kitchens):
    assert chat("modern kitchen around $10k")["suggestions"] == [
        "Show more", "Cheaper", "A bit more", "Compare these", "Any style", "Any room"]
    assert chat("around $10k")["suggestions"] == ["Show more", "Cheaper", "A bit more", "Compare these"]


def test_every_chip_is_understood(kitchens):
    for chip in chat("modern kitchen around $10k")["suggestions"]:
        result = chat("modern kitchen around $10k", chip)
        assert result["projects"] or result.get("comparison") or result["reply"].startswith("That's everything"), chip


def test_start_chips_when_nothing_is_known(app):
    assert offline().recommend("hello")["suggestions"] == START_CHIPS


@pytest.mark.parametrize("seen", [["1", 2], [True, 3], "nope", list(range(100))])
def test_seen_ids_from_the_client_are_cleaned(kitchens, seen):
    prefs = offline().recommend("show more", context={"budget": 10_000, "seen_ids": seen})["prefs"]
    assert all(isinstance(n, int) and not isinstance(n, bool) for n in prefs["seen_ids"])
    assert len(prefs["seen_ids"]) <= 60
