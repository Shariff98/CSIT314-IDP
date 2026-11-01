"""US-46 View IDP shortlist count."""
from control.remove_favourite_controller import RemoveFavouriteController
from control.save_favourite_controller import SaveFavouriteController
from control.view_shortlist_count_controller import ViewShortlistCountController
from entity.user_account import UserAccount


def customers(n):
    return [UserAccount.create(f"C{i}", f"c{i}@example.com", "pass123", "Customer") for i in range(n)]


def test_counts_each_customer_save(designer, make_idp):
    popular, quiet = make_idp("Popular"), make_idp("Quiet")
    for c in customers(3):
        SaveFavouriteController().save(c.id, popular.id)
    data = ViewShortlistCountController().shortlist_counts(designer.id)
    assert [(r["idp"].title, r["shortlists"]) for r in data["rows"]] == [("Popular", 3), ("Quiet", 0)]
    assert data["total"] == 3


def test_count_drops_when_customer_removes_favourite(designer, make_idp, customer):
    idp = make_idp()
    SaveFavouriteController().save(customer.id, idp.id)
    RemoveFavouriteController().remove(customer.id, idp.id)
    assert ViewShortlistCountController().shortlist_count(designer.id, idp.id) == 0


def test_only_my_projects_are_listed(designer, other_designer, make_idp):
    make_idp("Mine")
    make_idp("Theirs", designer_id=other_designer.id)
    rows = ViewShortlistCountController().shortlist_counts(designer.id)["rows"]
    assert [r["idp"].title for r in rows] == ["Mine"]


def test_cannot_read_another_designers_count(other_designer, make_idp):
    idp = make_idp()
    assert ViewShortlistCountController().shortlist_count(other_designer.id, idp.id) is None
