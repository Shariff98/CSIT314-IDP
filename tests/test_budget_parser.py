import pytest

from control import budget_parser

CATEGORIES = ["Bathroom", "Bedroom", "Kitchen", "Living Room", "Office"]
STYLES = ["Modern", "Scandinavian", "Japandi"]


@pytest.mark.parametrize("text, expected", [
    ("kitchen around $10k", 10_000),
    ("budget is 10,000", 10_000),
    ("10000 dollars please", 10_000),
    ("$12.5k for the bedroom", 12_500),
    ("about 1.2m for the whole house", 1_200_000),
    ("$800 for paint", 800),
    ("3 bedrooms, budget 15000", 15_000),   # "3" is not a budget
    ("ten thousand", None),                 # words are not parsed, which is fine
    ("no idea yet", None),
    ("bathroom -5000", -5_000),             # negative is returned so the controller can reject it
])
def test_parse_budget(text, expected):
    assert budget_parser.parse_budget(text) == expected


def test_parse_finds_category_styles_and_strict():
    prefs = budget_parser.parse("Scandinavian kitchen in my condo, no more than $9,000", CATEGORIES, STYLES)
    assert prefs == {"budget": 9_000, "budget_min": None, "category": "Kitchen", "styles": ["Scandinavian"],
                     "exclude_styles": [], "property_type": "Condo", "location": None, "strict_max": True}


def test_parse_synonyms():
    assert budget_parser.parse("redo my toilet for 5k", CATEGORIES)["category"] == "Bathroom"
    assert budget_parser.parse("lounge makeover 20k", CATEGORIES)["category"] == "Living Room"
    assert budget_parser.parse("kitchen around 10k", CATEGORIES)["strict_max"] is False
