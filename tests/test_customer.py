"""Feature 4: customer search, view and favourites.
US-07 Browse, US-08 Search favourites, US-18 Sort, US-44 View favourites, US-45 Same designer,
US-56 Remove from favourites."""
from control.browse_idp_controller import BrowseIDPController
from control.remove_favourite_controller import RemoveFavouriteController
from control.save_favourite_controller import SaveFavouriteController
from control.search_favourites_controller import SearchFavouritesController
from control.view_designer_projects_controller import ViewDesignerProjectsController
from control.view_favourites_controller import ViewFavouritesController
from entity.favourite import Favourite
from entity.user_account import UserAccount


# ---------- US-07 Browse published IDPs / US-18 Sort ----------
def test_browse_lists_published_newest_first(make_idp):
    make_idp("Old", created_at="2026-01-01 09:00:00")
    make_idp("New", created_at="2026-03-01 09:00:00")
    make_idp("Draft", published=False)
    assert [i.title for i in BrowseIDPController().browse()] == ["New", "Old"]


def test_browse_sorted_by_most_saved(make_idp):
    loved, ignored = make_idp("Loved"), make_idp("Ignored")
    for i in range(2):
        c = UserAccount.create(f"C{i}", f"c{i}@example.com", "pass123", "Customer")
        Favourite.add(c.id, loved.id)
    assert [i.title for i in BrowseIDPController().browse("saves")] == ["Loved", "Ignored"]


def test_browse_sorted_by_most_viewed(make_idp):
    quiet, busy = make_idp("Quiet"), make_idp("Busy")
    busy.record_view()
    assert BrowseIDPController().browse("views")[0].title == "Busy"


def test_unknown_sort_falls_back_to_newest(make_idp):
    make_idp("A", created_at="2026-01-01 09:00:00")
    make_idp("B", created_at="2026-02-01 09:00:00")
    assert BrowseIDPController().browse("random")[0].title == "B"


# ---------- US-44 View favourites list ----------
def test_favourites_list_newest_saved_first(customer, make_idp):
    first, second = make_idp("First"), make_idp("Second")
    Favourite.add(customer.id, first.id, saved_at="2026-01-01 10:00:00")
    Favourite.add(customer.id, second.id, saved_at="2026-01-02 10:00:00")
    assert [i.title for i in ViewFavouritesController().list_favourites(customer.id)] == ["Second", "First"]


def test_favourites_are_private_to_each_customer(customer, make_idp):
    other = UserAccount.create("Other", "other@example.com", "pass123", "Customer")
    SaveFavouriteController().save(other.id, make_idp().id)
    assert ViewFavouritesController().list_favourites(customer.id) == []


# ---------- US-08 Search and filter favourites ----------
def test_search_favourites_by_keyword_and_category(customer, make_idp):
    for idp in (make_idp("Blue Kitchen", category="Kitchen"), make_idp("Blue Bedroom"), make_idp("Red Kitchen",
                                                                                               category="Kitchen")):
        Favourite.add(customer.id, idp.id)
    make_idp("Blue Office", category="Office")               # not saved, so never found
    controller = SearchFavouritesController()
    assert sorted(i.title for i in controller.search(customer.id, "blue")) == ["Blue Bedroom", "Blue Kitchen"]
    assert [i.title for i in controller.search(customer.id, "blue", "Kitchen")] == ["Blue Kitchen"]
    assert controller.search(customer.id, "office") == []


# ---------- US-56 Remove from favourites ----------
def test_remove_favourite(customer, make_idp):
    idp = make_idp()
    SaveFavouriteController().save(customer.id, idp.id)
    assert RemoveFavouriteController().remove(customer.id, idp.id) == "removed"
    assert ViewFavouritesController().list_favourites(customer.id) == []
    assert idp.shortlist_count() == 0


def test_remove_something_not_saved(customer, make_idp):
    assert RemoveFavouriteController().remove(customer.id, make_idp().id) == "not_saved"


# ---------- US-45 Other projects by same designer ----------
def test_other_projects_by_same_designer(make_idp, other_designer):
    main = make_idp("Main")
    make_idp("Sibling")
    make_idp("Sibling Draft", published=False)
    make_idp("Stranger", designer_id=other_designer.id)
    assert [i.title for i in ViewDesignerProjectsController().other_projects(main.id)] == ["Sibling"]


def test_other_projects_for_unknown_idp(app):
    assert ViewDesignerProjectsController().other_projects(999) == []
