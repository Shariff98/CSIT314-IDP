"""US-34 View IDP details as customer, and US-37 count repeat views once per session."""
from control.view_idp_controller import ViewIDPController


def test_view_returns_details_and_counts_one_view(make_idp, customer):
    idp = make_idp("Loft", property_type="Condo", location="Novena")
    seen = ViewIDPController().view(idp.id, customer.id, "session-1")
    assert (seen.title, seen.property_type, seen.location) == ("Loft", "Condo", "Novena")
    assert seen.views == 1


def test_detail_includes_designer_and_company(make_idp, designer):
    from control.create_company_profile_controller import CreateCompanyProfileController
    CreateCompanyProfileController().create_company(designer.id, "Dana Co", "DANA-123", "1 St", "", "d@co.sg", "")
    seen = ViewIDPController().view(make_idp().id)
    assert seen.designer().name == "Dana Designer"
    assert seen.company().name == "Dana Co"


def test_unknown_idp_returns_none(app):
    assert ViewIDPController().view(999) is None


def test_draft_is_hidden_from_customers_but_not_from_owner(make_idp, customer, designer):
    draft = make_idp("Draft", published=False)
    assert ViewIDPController().view(draft.id, customer.id) is None
    assert ViewIDPController().view(draft.id, designer.id) is not None


def test_same_session_counts_once(make_idp, customer):
    idp = make_idp()
    controller = ViewIDPController()
    for _ in range(3):
        controller.view(idp.id, customer.id, "session-1")
    controller.view(idp.id, customer.id, "session-2")
    assert controller.view(idp.id, None, "session-2").views == 2


def test_designer_viewing_own_project_is_not_counted(make_idp, designer):
    idp = make_idp()
    assert ViewIDPController().view(idp.id, designer.id, "s").views == 0
