"""US-54 Create IDP."""
import pytest

from control.create_idp_controller import CreateIDPController


def test_create_idp_saves_project(designer):
    idp = CreateIDPController().create_idp(designer.id, "Modern Kitchen", "Open plan", "Kitchen", "25000")
    assert idp.id is not None
    assert idp.budget == 25000
    assert idp.views == 0


def test_create_idp_saves_all_details(designer):
    idp = CreateIDPController().create_idp(designer.id, " Condo Revamp ", "Full refit", "Living Room", 40000,
                                           "Condo", "Tampines", "2026-05-01", "modern, Japandi")
    assert (idp.title, idp.property_type, idp.location) == ("Condo Revamp", "Condo", "Tampines")
    assert idp.completion_date == "2026-05-01"
    assert idp.style_tag_list == ["Modern", "Japandi"]
    assert idp.is_published and idp.status == "Current"


def test_create_idp_as_draft_is_not_published(designer):
    idp = CreateIDPController().create_idp(designer.id, "Draft", "Not ready", "Kitchen", 100, publish=False)
    assert not idp.is_published


def test_create_idp_rejects_missing_title(designer):
    with pytest.raises(ValueError, match="title"):
        CreateIDPController().create_idp(designer.id, "  ", "Open plan", "Kitchen", 25000)


@pytest.mark.parametrize("budget", ["abc", 0, -5])
def test_create_idp_rejects_bad_budget(designer, budget):
    with pytest.raises(ValueError, match="Budget"):
        CreateIDPController().create_idp(designer.id, "Modern Kitchen", "Open plan", "Kitchen", budget)


def test_create_idp_rejects_unknown_category(designer):
    with pytest.raises(ValueError, match="category"):
        CreateIDPController().create_idp(designer.id, "Pool", "Outdoor", "Swimming Pool", 1000)


@pytest.mark.parametrize("field, value, message", [
    ("property_type", "Castle", "Property type"),
    ("completion_date", "31/12/2026", "Completion date"),
    ("style_tags", "a,b,c,d,e,f", "at most 5"),
])
def test_create_idp_rejects_bad_optional_fields(designer, field, value, message):
    with pytest.raises(ValueError, match=message):
        CreateIDPController().create_idp(designer.id, "Title", "Desc", "Kitchen", 100, **{field: value})
