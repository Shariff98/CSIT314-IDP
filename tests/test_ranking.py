"""Pure ranking functions: no database, no LLM."""
from types import SimpleNamespace

from control.recommend_idps_controller import (band_of, budget_fit, budget_window, pick_three,
                                               preference_match, score_candidates)


def idp(id, budget, designer=None, category="Kitchen", styles=("Modern",), saves=0, views=0):
    return SimpleNamespace(id=id, budget=budget, designer_id=designer or id, category=category,
                           styles=list(styles), property_type="HDB", location="Tampines", saves=saves, views=views)


def test_window_is_90_to_130_percent():
    assert budget_window(10_000) == (9_000, 13_000)


def test_strict_window_tops_out_at_budget():
    assert budget_window(10_000, strict_max=True) == (9_000, 10_000)


def test_widened_window_goes_to_150_percent():
    assert budget_window(10_000, widened=True) == (9_000, 15_000)


def test_budget_fit_peaks_at_budget_and_falls_faster_below():
    assert budget_fit(10_000, 10_000, 9_000, 13_000) == 1.0
    assert budget_fit(13_000, 10_000, 9_000, 13_000) == 0.0
    assert budget_fit(9_500, 10_000, 9_000, 13_000) < budget_fit(10_500, 10_000, 9_000, 13_000)


def test_preference_match_is_share_of_what_was_asked():
    prefs = {"category": "Kitchen", "styles": ["Modern", "Japandi"]}
    assert preference_match(idp(1, 10_000), prefs) == 2 / 3
    assert preference_match(idp(1, 10_000), {}) == 1.0


def test_exact_budget_and_matching_category_beats_stretch_with_no_match():
    prefs = {"budget": 10_000, "category": "Kitchen", "styles": ["Modern"]}
    exact = idp(1, 10_000)
    stretch = idp(2, 12_900, category="Bedroom", styles=("Classic",), saves=50, views=500)
    ranked = score_candidates([stretch, exact], prefs, 9_000, 13_000)
    assert ranked[0][0] is exact


def test_bands():
    assert band_of(10_000, 10_000) == "Best fit for your budget"
    assert band_of(11_000, 10_000) == "Small step up"
    assert band_of(12_900, 10_000) == "Worth stretching for"


def test_pick_three_takes_one_per_band_and_prefers_different_designers():
    scored = [(idp(1, 10_000, designer=7), 0.9), (idp(2, 10_200, designer=7), 0.85),
              (idp(3, 11_200, designer=7), 0.8), (idp(4, 11_000, designer=8), 0.6),
              (idp(5, 12_900, designer=9), 0.5)]
    picks = pick_three(scored, 10_000)
    assert [p[0].id for p in picks] == [1, 4, 5]
    assert [p[2] for p in picks] == ["Best fit for your budget", "Small step up", "Worth stretching for"]


def test_pick_three_fills_empty_bands_from_the_rest():
    scored = [(idp(1, 10_000), 0.9), (idp(2, 9_800), 0.8), (idp(3, 9_500), 0.7)]
    assert sorted(p[0].id for p in pick_three(scored, 10_000)) == [1, 2, 3]
