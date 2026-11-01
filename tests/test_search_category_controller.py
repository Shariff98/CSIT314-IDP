"""US-59 View and search IDP categories."""
from control.search_category_controller import SearchCategoryController
from entity.category import Category


def test_lists_default_categories_with_idp_counts(make_idp):
    make_idp(category="Kitchen")
    make_idp(category="Kitchen")
    rows = {r["category"].name: r["idps"] for r in SearchCategoryController().search()}
    assert rows["Kitchen"] == 2
    assert rows["Office"] == 0
    assert len(rows) == 5


def test_search_matches_name_or_description(app):
    Category.create("Walk-in Wardrobe", "Dressing rooms")
    controller = SearchCategoryController()
    assert [r["category"].name for r in controller.search("wardrobe")] == ["Walk-in Wardrobe"]
    assert [r["category"].name for r in controller.search("dressing")] == ["Walk-in Wardrobe"]


def test_filter_by_status(app):
    Category.find_by_name("Office").suspend()
    controller = SearchCategoryController()
    assert [r["category"].name for r in controller.search(status="Suspended")] == ["Office"]
    assert "Office" not in controller.active_names()


def test_results_are_sorted_by_name(app):
    names = [r["category"].name for r in SearchCategoryController().search()]
    assert names == sorted(names)


def test_no_match(app):
    assert SearchCategoryController().search("spaceship") == []
