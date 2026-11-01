"""Feature 3: the designer's portfolio.
US-04 Update, US-05 Delete, US-06 Current or past, US-16 List, US-26 Category and tags,
US-27 View my IDP, US-33 Draft and publish, US-55 Photos and cover."""
import os
from datetime import date

import pytest

from control.assign_idp_tags_controller import AssignIDPTagsController
from control.delete_idp_controller import DeleteIDPController
from control.list_my_idps_controller import ListMyIDPsController
from control.mark_idp_status_controller import MarkIDPStatusController
from control.publish_idp_controller import PublishIDPController
from control.update_idp_controller import UpdateIDPController
from control.upload_idp_photo_controller import MAX_PHOTOS, UploadIDPPhotoController
from control.view_my_idp_controller import ViewMyIDPController
from entity import storage
from entity.category import Category
from entity.favourite import Favourite
from entity.idp import IDP
from tests.conftest import PNG


# ---------- US-16 View list of my IDPs ----------
def test_list_shows_all_my_projects_including_drafts(designer, other_designer, make_idp):
    make_idp("Published")
    make_idp("Draft", published=False)
    make_idp("Theirs", designer_id=other_designer.id)
    assert sorted(i.title for i in ListMyIDPsController().list_idps(designer.id)) == ["Draft", "Published"]


# ---------- US-27 View my IDP details ----------
def test_view_my_idp_does_not_count_a_view(designer, make_idp):
    idp = make_idp()
    assert ViewMyIDPController().view(designer.id, idp.id).views == 0


def test_cannot_view_another_designers_idp(other_designer, make_idp):
    assert ViewMyIDPController().view(other_designer.id, make_idp().id) is None


# ---------- US-04 Update IDP ----------
def test_update_idp(designer, make_idp):
    idp = make_idp()
    UpdateIDPController().update_idp(designer.id, idp.id, "New title", "New text", "Kitchen", "12000", "Condo",
                                     "Bishan", "2026-02-01")
    saved = IDP.find_by_id(idp.id)
    assert (saved.title, saved.category, saved.budget, saved.location) == ("New title", "Kitchen", 12000, "Bishan")


def test_update_validates_like_create(designer, make_idp):
    with pytest.raises(ValueError, match="Budget"):
        UpdateIDPController().update_idp(designer.id, make_idp().id, "T", "D", "Kitchen", "0")


def test_cannot_update_another_designers_idp(other_designer, make_idp):
    with pytest.raises(LookupError):
        UpdateIDPController().update_idp(other_designer.id, make_idp().id, "T", "D", "Kitchen", 1)


# ---------- US-05 Delete IDP ----------
def test_delete_removes_project_photos_and_favourites(designer, customer, make_idp):
    idp = make_idp()
    photo = UploadIDPPhotoController().upload(designer.id, idp.id, "a.png", PNG)
    Favourite.add(customer.id, idp.id)
    assert DeleteIDPController().delete(designer.id, idp.id) == "deleted"
    assert IDP.find_by_id(idp.id) is None
    assert Favourite.list_for_customer(customer.id) == []
    assert not os.path.exists(os.path.join(storage.upload_dir(), photo.filename))


def test_cannot_delete_another_designers_idp(other_designer, make_idp):
    idp = make_idp()
    assert DeleteIDPController().delete(other_designer.id, idp.id) == "not_found"
    assert IDP.find_by_id(idp.id) is not None


# ---------- US-06 Mark IDP as current or past ----------
def test_mark_past_sets_completion_date_when_missing(designer, make_idp):
    idp = MarkIDPStatusController().mark(designer.id, make_idp().id, "Past")
    assert idp.status == "Past"
    assert idp.completion_date == date.today().isoformat()


def test_mark_past_keeps_existing_completion_date(designer, make_idp):
    idp = MarkIDPStatusController().mark(designer.id, make_idp(completion_date="2025-12-01").id, "Past")
    assert idp.completion_date == "2025-12-01"


def test_mark_back_to_current(designer, make_idp):
    idp = make_idp(status="Past")
    assert MarkIDPStatusController().mark(designer.id, idp.id, "Current").status == "Current"


def test_mark_rejects_unknown_status(designer, make_idp):
    with pytest.raises(ValueError):
        MarkIDPStatusController().mark(designer.id, make_idp().id, "Archived")


# ---------- US-33 Save as draft, publish and unpublish ----------
def test_publish_and_unpublish(designer, make_idp):
    idp = make_idp(published=False)
    controller = PublishIDPController()
    assert controller.publish(designer.id, idp.id) == "published"
    assert controller.publish(designer.id, idp.id) == "already_published"
    assert controller.unpublish(designer.id, idp.id) == "unpublished"
    assert controller.unpublish(designer.id, idp.id) == "already_draft"
    assert not IDP.find_by_id(idp.id).is_published


def test_cannot_publish_into_suspended_category(designer, make_idp):
    idp = make_idp(category="Office", published=False)
    Category.find_by_name("Office").suspend()
    with pytest.raises(ValueError, match="active category"):
        PublishIDPController().publish(designer.id, idp.id)


# ---------- US-26 Assign category and style tags ----------
def test_assign_category_and_tags(designer, make_idp):
    idp = AssignIDPTagsController().assign(designer.id, make_idp().id, "Office", "industrial, Modern")
    assert idp.category == "Office"
    assert idp.style_tag_list == ["Industrial", "Modern"]


def test_assign_rejects_too_many_tags(designer, make_idp):
    with pytest.raises(ValueError, match="at most 5"):
        AssignIDPTagsController().assign(designer.id, make_idp().id, "Office", "a,b,c,d,e,f")


# ---------- US-55 Upload photos and set cover ----------
def test_first_photo_becomes_cover_then_cover_can_change(designer, make_idp):
    idp = make_idp()
    controller = UploadIDPPhotoController()
    first = controller.upload(designer.id, idp.id, "one.png", PNG)
    second = controller.upload(designer.id, idp.id, "two.jpg", PNG)
    assert idp.cover_photo().id == first.id
    controller.set_cover(designer.id, second.id)
    assert idp.cover_photo().id == second.id
    assert len(idp.photos()) == 2


def test_deleting_cover_promotes_next_photo(designer, make_idp):
    idp = make_idp()
    controller = UploadIDPPhotoController()
    first = controller.upload(designer.id, idp.id, "one.png", PNG)
    second = controller.upload(designer.id, idp.id, "two.png", PNG)
    controller.delete_photo(designer.id, first.id)
    assert idp.cover_photo().id == second.id


def test_photo_limit(designer, make_idp):
    idp = make_idp()
    controller = UploadIDPPhotoController()
    for i in range(MAX_PHOTOS):
        controller.upload(designer.id, idp.id, f"{i}.png", PNG)
    with pytest.raises(ValueError, match="at most"):
        controller.upload(designer.id, idp.id, "extra.png", PNG)


def test_cannot_upload_to_another_designers_idp(other_designer, make_idp):
    with pytest.raises(LookupError):
        UploadIDPPhotoController().upload(other_designer.id, make_idp().id, "a.png", PNG)
