"""US-17 Filter IDPs by category, style, budget, property type and location (and US-18 sort)."""
import pytest

from control.filter_idp_controller import FilterIDPController


@pytest.fixture
def projects(make_idp):
    return [
        make_idp("Tampines Kitchen", category="Kitchen", budget=20000, style_tags="Modern, Minimalist",
                 property_type="HDB", location="Tampines"),
        make_idp("Bukit Timah Kitchen", category="Kitchen", budget=60000, style_tags="Classic",
                 property_type="Landed", location="Bukit Timah"),
        make_idp("Jurong Bedroom", category="Bedroom", budget=9000, style_tags="Modernist",
                 property_type="HDB", location="Jurong"),
        make_idp("Hidden Draft", category="Kitchen", budget=20000, published=False),
    ]


def titles(results):
    return sorted(i.title for i in results)


def test_filter_by_category(projects):
    assert titles(FilterIDPController().filter(category="Kitchen")) == ["Bukit Timah Kitchen", "Tampines Kitchen"]


def test_filter_by_style_matches_whole_tag(projects):
    # "Modern" must not match the "Modernist" tag
    assert titles(FilterIDPController().filter(style="Modern")) == ["Tampines Kitchen"]


def test_filter_by_budget_range(projects):
    assert titles(FilterIDPController().filter(min_budget="10000", max_budget="30000")) == ["Tampines Kitchen"]


def test_filter_by_property_type_and_location(projects):
    assert titles(FilterIDPController().filter(property_type="HDB", location="jurong")) == ["Jurong Bedroom"]


def test_filters_combine_with_keyword(projects):
    assert titles(FilterIDPController().filter(keyword="kitchen", property_type="Landed")) == ["Bukit Timah Kitchen"]


def test_blank_filters_return_all_published(projects):
    assert len(FilterIDPController().filter("", "", "", "", "", "", "")) == 3


def test_sort_by_budget(projects):
    budgets = [i.budget for i in FilterIDPController().filter(sort="budget_high")]
    assert budgets == sorted(budgets, reverse=True)


def test_rejects_min_budget_above_max(projects):
    with pytest.raises(ValueError, match="Minimum budget"):
        FilterIDPController().filter(min_budget=50000, max_budget=100)


def test_rejects_non_numeric_budget(projects):
    with pytest.raises(ValueError, match="whole number"):
        FilterIDPController().filter(max_budget="cheap")
