"""Chat cards: "why this matches" reasons, and the real cover photo when there is one."""
from control.recommend_idps_controller import RecommendIDPsController, match_reasons
from entity.idp_photo import IDPPhoto
from tests.chatbot_helpers import FakeLLMGateway, make_idp
from tests.conftest import PNG


def offline():
    return RecommendIDPsController(FakeLLMGateway(fail=True))


def prefs(**kw):
    return {"budget": 10_000, "budget_min": None, "category": None, "styles": [], "property_type": None,
            "location": None, **kw}


def test_reasons_say_how_far_from_budget_and_what_matched(app):
    idp = make_idp(9_200, styles="Modern,Industrial", property_type="HDB")
    assert match_reasons(idp, prefs(category="Kitchen", styles=["Modern"], property_type="HDB")) == [
        "$800 under budget", "Modern", "Kitchen", "HDB"]
    assert match_reasons(idp, prefs(budget=9_200)) == ["On budget"]
    assert match_reasons(idp, prefs(budget=8_000)) == ["$1,200 over budget"]


def test_reasons_for_a_range(app):
    idp = make_idp(9_000)
    assert match_reasons(idp, prefs(budget=12_000, budget_min=8_000)) == ["Within your range"]
    assert match_reasons(idp, prefs(budget=12_000, budget_min=9_500)) == ["Just outside your range"]


def test_cards_carry_reasons(app):
    for budget in (9_500, 10_000, 11_000):
        make_idp(budget)
    cards = offline().recommend("modern kitchen around $10k")["projects"]
    assert all(card["reasons"] and "Modern" in card["reasons"] and "Kitchen" in card["reasons"] for card in cards)


def test_card_uses_the_cover_photo_when_there_is_one(app):
    with_photo = make_idp(10_000)
    IDPPhoto.create(with_photo.id, PNG, "png", is_cover=True)
    make_idp(9_500), make_idp(11_000)
    cards = {c["id"]: c for c in offline().recommend("kitchen around $10k")["projects"]}
    assert cards[with_photo.id]["image"].startswith("/uploads/") and cards[with_photo.id]["image"].endswith(".png")
    assert all(c["image"] == "/project-kitchen.svg" for i, c in cards.items() if i != with_photo.id)


def test_rooms_without_their_own_picture_get_the_generic_one(app):
    for budget in (9_500, 10_000, 11_000):
        make_idp(budget, category="Bathroom")
    cards = offline().recommend("bathroom around $10k")["projects"]
    assert {c["image"] for c in cards} == {"/project-detail.svg"}
