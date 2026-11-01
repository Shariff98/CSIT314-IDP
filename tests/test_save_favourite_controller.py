from control.create_idp_controller import CreateIDPController
from control.save_favourite_controller import SaveFavouriteController


def make_idp(designer):
    return CreateIDPController().create_idp(designer.id, "Cosy Bedroom", "Warm tones", "Bedroom", 8000)


def test_save_adds_to_favourites_and_shortlist_count(designer, customer):
    idp = make_idp(designer)
    assert SaveFavouriteController().save(customer.id, idp.id) == "saved"
    assert [i.id for i in SaveFavouriteController().list_favourites(customer.id)] == [idp.id]
    assert idp.shortlist_count() == 1


def test_saving_twice_does_not_duplicate(designer, customer):
    idp = make_idp(designer)
    controller = SaveFavouriteController()
    controller.save(customer.id, idp.id)
    assert controller.save(customer.id, idp.id) == "already_saved"
    assert idp.shortlist_count() == 1


def test_save_unknown_idp_returns_not_found(customer):
    assert SaveFavouriteController().save(customer.id, 999) == "not_found"


def test_cannot_save_a_draft(designer, customer):
    draft = CreateIDPController().create_idp(designer.id, "Draft", "Hidden", "Bedroom", 100, publish=False)
    assert SaveFavouriteController().save(customer.id, draft.id) == "not_found"


def test_is_saved(designer, customer):
    idp = make_idp(designer)
    controller = SaveFavouriteController()
    assert not controller.is_saved(customer.id, idp.id)
    controller.save(customer.id, idp.id)
    assert controller.is_saved(customer.id, idp.id)
