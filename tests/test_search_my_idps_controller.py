"""US-03 Search and filter my IDPs."""
import pytest

from control.search_my_idps_controller import SearchMyIDPsController


@pytest.fixture
def portfolio(make_idp, other_designer):
    return {
        "kitchen": make_idp("Modern Kitchen", category="Kitchen", created_at="2026-01-10 10:00:00"),
        "bedroom": make_idp("Calm Bedroom", status="Past", created_at="2026-03-05 10:00:00"),
        "draft": make_idp("Draft Office", category="Office", published=False, created_at="2026-03-20 10:00:00"),
        "not_mine": make_idp("Modern Kitchen Too", category="Kitchen", designer_id=other_designer.id),
    }


def titles(results):
    return sorted(i.title for i in results)


def test_search_by_keyword_only_returns_my_projects(designer, portfolio):
    assert titles(SearchMyIDPsController().search(designer.id, "kitchen")) == ["Modern Kitchen"]


def test_filter_by_status(designer, portfolio):
    controller = SearchMyIDPsController()
    assert titles(controller.search(designer.id, status="Past")) == ["Calm Bedroom"]
    assert titles(controller.search(designer.id, status="Draft")) == ["Draft Office"]


def test_filter_by_category(designer, portfolio):
    assert titles(SearchMyIDPsController().search(designer.id, category="Office")) == ["Draft Office"]


def test_filter_by_created_date_range(designer, portfolio):
    found = SearchMyIDPsController().search(designer.id, date_from="2026-03-01", date_to="2026-03-31")
    assert titles(found) == ["Calm Bedroom", "Draft Office"]


def test_filters_combine(designer, portfolio):
    assert SearchMyIDPsController().search(designer.id, "office", status="Past") == []


def test_rejects_from_date_after_to_date(designer):
    with pytest.raises(ValueError, match="From date"):
        SearchMyIDPsController().search(designer.id, date_from="2026-04-01", date_to="2026-03-01")


def test_rejects_unknown_status(designer):
    with pytest.raises(ValueError):
        SearchMyIDPsController().search(designer.id, status="Archived")
