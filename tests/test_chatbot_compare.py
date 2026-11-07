"""Compare in chat: "compare #12 and #15", or "Compare these" after a search."""
import pytest

from control.recommend_idps_controller import RecommendIDPsController
from tests.chatbot_helpers import FakeLLMGateway, make_idp


def offline(fail=True):
    return RecommendIDPsController(FakeLLMGateway(fail=fail))


@pytest.fixture
def three(app):
    a = make_idp(9_000, styles="Modern")
    b = make_idp(10_200, styles="Classic")
    c = make_idp(12_000, styles="Modern", views=50)
    return a, b, c


def test_compare_by_ids(three):
    a, b, c = three
    result = offline().recommend(f"compare #{a.id} and #{c.id}")
    assert [r["id"] for r in result["comparison"]] == [a.id, c.id]
    assert f"#{a.id} {a.title}: cheapest at $9,000" in result["reply"]
    assert f"#{c.id} {c.title}: most popular (0 saves, 50 views)" in result["reply"]


def test_compare_these_uses_the_last_results(three):
    first = offline().recommend("kitchen around $10k")
    result = offline().recommend("Compare these", context=first["prefs"])
    assert {r["id"] for r in result["comparison"]} == {p["id"] for p in first["projects"]}
    closest = next(r for r in result["comparison"] if r["budget"] == 10_200)
    assert closest["vs_budget"] == 200 and f"#{closest['id']} {closest['title']}: closest to your $10,000" in result["reply"]


def test_best_match_line_only_when_matches_differ(three):
    first = offline().recommend("modern kitchen around $10k")
    reply = offline().recommend("compare them side by side", context=first["prefs"])["reply"]
    assert "best match for what you asked" in reply


def test_one_project_winning_everything_gets_one_line(app):
    a = make_idp(9_000, views=40)
    b = make_idp(12_000)
    reply = offline().recommend(f"compare #{a.id} and #{b.id}")["reply"]
    assert reply.splitlines()[1:] == [f"- #{a.id} {a.title}: cheapest at $9,000, most popular (0 saves, 40 views)"]


def test_compare_never_shows_unpublished_projects(three):
    a, b, _ = three
    hidden = make_idp(10_000, published=False)
    result = offline().recommend(f"compare #{a.id}, #{b.id} and #{hidden.id}")
    assert hidden.id not in {r["id"] for r in result["comparison"]}


def test_compare_with_nothing_to_compare_explains_how(app):
    result = offline().recommend("compare")
    assert "comparison" not in result and "compare #12 and #15" in result["reply"]


def test_compare_does_not_need_the_llm(three):
    llm = FakeLLMGateway()
    a, b, _ = three
    RecommendIDPsController(llm).recommend(f"compare #{a.id} and #{b.id}")
    assert not any(kind == "reply" for kind, _ in llm.calls)


def test_compare_keeps_the_memory(three):
    first = offline().recommend("modern kitchen around $10k")
    result = offline().recommend("compare these", context=first["prefs"])
    assert result["prefs"]["budget"] == 10_000 and result["prefs"]["seen_ids"] == first["prefs"]["seen_ids"]


def test_compare_over_the_api(client, three):
    a, b, _ = three
    body = client.post("/api/chat", json={"message": f"compare #{a.id} and #{b.id}"}).get_json()
    assert [r["id"] for r in body["comparison"]] == [a.id, b.id]
    assert set(body["comparison"][0]) >= {"title", "budget", "designer", "styles", "views", "saves", "url"}
