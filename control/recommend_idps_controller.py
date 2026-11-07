"""Control: Get budget-matched recommendations (the chatbot use case).

Four steps per message:
  1. Understand  - LLMGateway.extract_preferences() turns the text into JSON.
  2. Search/rank - this class finds published projects in the budget window and
                   scores them. Pure Python, no LLM, fully tested.
  3. Explain     - LLMGateway.write_reply() writes a short friendly reply.
  4. Check       - any project id in the reply that we did not choose is removed.

The LLM never touches the database and never decides which projects are shown,
so it cannot invent a project or a price. If the LLM fails, budget_parser does
step 1 and a template does step 3 (alternate flow A3).
"""
import re

from control import budget_parser
from entity.category import Category
from entity.chat_log import ChatLog
from entity.idp import IDP

MIN_BUDGET, MAX_BUDGET = 1_000, 1_000_000
WINDOW_LOW, WINDOW_HIGH, WIDENED_HIGH = 0.90, 1.30, 1.50
STRICT_WIDENED_LOW = 0.70
WEIGHTS = {"fit": 0.50, "preference": 0.35, "popularity": 0.15}

BANDS = [  # (label, from, to) as fractions of the budget
    ("Best fit for your budget", None, 1.05),
    ("Small step up", 1.05, 1.15),
    ("Worth stretching for", 1.15, None),
]
STRICT_BANDS = [
    ("Best fit for your budget", 0.97, None),
    ("Saves you a little", 0.93, 0.97),
    ("Saves you more", None, 0.93),
]
RELAX_NOTES = {
    "style": "I couldn't find enough in that style, so I included other styles.",
    "category": "I couldn't find enough in that category, so I included other rooms.",
    "budget_window": "I widened the price range a little to find enough options.",
}


class LLMUnavailable(Exception):
    """Raised by the LLM gateway when the service is down, slow, over its limit or not configured."""


# ---------- pure ranking functions (unit tested directly) ----------
def budget_window(budget, strict_max=False, widened=False):
    if strict_max:
        return round(budget * (STRICT_WIDENED_LOW if widened else WINDOW_LOW)), budget
    return round(budget * WINDOW_LOW), round(budget * (WIDENED_HIGH if widened else WINDOW_HIGH))


def budget_fit(price, budget, low, high):
    """1.0 at exactly the budget, falling in a straight line to 0 at each window edge.

    The window is narrower below the budget (90%) than above (130%), so the
    score falls faster for cheaper projects, which usually means smaller scope.
    """
    if price == budget:
        return 1.0
    edge = low if price < budget else high
    if edge == budget:
        return 0.0
    return max(0.0, 1 - abs(price - budget) / abs(edge - budget))


def preference_match(idp, prefs):
    """Share of the things the customer asked for that this project has."""
    wanted, matched = 0, 0
    if prefs.get("category"):
        wanted += 1
        matched += idp.category == prefs["category"]
    for style in prefs.get("styles") or []:
        wanted += 1
        matched += style.lower() in (s.lower() for s in idp.styles)
    for field in ("property_type", "location"):
        if prefs.get(field):
            wanted += 1
            matched += (getattr(idp, field) or "").lower() == prefs[field].lower()
    return matched / wanted if wanted else 1.0


def score_candidates(candidates, prefs, low, high):
    """Returns [(idp, score)] sorted best first. Ties go to the cheaper, then older project."""
    budget = prefs["budget"]
    popularity = [c.saves * 2 + c.views for c in candidates]
    top = max(popularity, default=0) or 1
    scored = []
    for idp, pop in zip(candidates, popularity):
        score = (WEIGHTS["fit"] * budget_fit(idp.budget, budget, low, high)
                 + WEIGHTS["preference"] * preference_match(idp, prefs)
                 + WEIGHTS["popularity"] * pop / top)
        scored.append((idp, round(score, 4)))
    return sorted(scored, key=lambda pair: (-pair[1], pair[0].budget, pair[0].id))


def band_of(price, budget, strict_max=False):
    for label, start, end in (STRICT_BANDS if strict_max else BANDS):
        if (start is None or price > budget * start) and (end is None or price <= budget * end):
            return label
    return (STRICT_BANDS if strict_max else BANDS)[-1][0]


def pick_three(scored, budget, strict_max=False):
    """Best project in each price band, preferring 3 different designers.

    Empty bands are filled from the rest by score. Returns [(idp, score, label)]
    ordered by price.
    """
    bands = STRICT_BANDS if strict_max else BANDS
    chosen, designers = [], set()

    def take(pool):
        pool = [p for p in pool if p not in chosen]
        if not pool:
            return
        fresh = [p for p in pool if p[0].designer_id not in designers]
        pick = (fresh or pool)[0]
        chosen.append(pick)
        designers.add(pick[0].designer_id)

    for label, _, _ in bands:
        take([p for p in scored if band_of(p[0].budget, budget, strict_max) == label])
    while len(chosen) < 3 and len(chosen) < len(scored):
        take(scored)
    chosen.sort(key=lambda p: p[0].budget)
    return [(idp, score, band_of(idp.budget, budget, strict_max)) for idp, score in chosen]


def money(amount):
    return f"${amount:,.0f}"


# ---------- the controller ----------
class RecommendIDPsController:
    def __init__(self, llm_gateway):
        self.llm = llm_gateway

    def recommend(self, message, history=None, customer_id=None):
        """Returns {"reply", "projects", "relaxed", "source"}. Raises ValueError for an empty message."""
        message = (message or "").strip()
        if not message:
            raise ValueError("Please type a message.")
        categories, styles = [c.name for c in Category.all_active()], IDP.known_styles()

        source = "llm"
        try:
            prefs = self.llm.extract_preferences(message, history or [], categories, styles)
        except LLMUnavailable:
            prefs, source = budget_parser.parse(message, categories, styles), "fallback"
        prefs = self._clean(prefs, message, categories, styles)

        budget = prefs["budget"]
        if budget is None:
            return self._answer("What budget do you have in mind? For example: \"kitchen, around $10,000\".",
                                [], [], source, message, prefs, customer_id)
        if not MIN_BUDGET <= budget <= MAX_BUDGET:
            return self._answer(f"That budget doesn't look right. Please give an amount between "
                                f"{money(MIN_BUDGET)} and {money(MAX_BUDGET)}.",
                                [], [], source, message, prefs, customer_id)

        candidates, relaxed, (low, high) = self._find_candidates(prefs)
        if not candidates:
            return self._answer(f"I couldn't find any published projects near {money(budget)}. "
                                "Try a different budget or room.", [], relaxed, source, message, prefs, customer_id)

        picks = pick_three(score_candidates(candidates, prefs, low, high), budget, prefs["strict_max"])
        projects = [self._card(idp, score, label) for idp, score, label in picks]

        reply = None
        if source == "llm":
            try:
                reply = self.llm.write_reply(message, projects, [RELAX_NOTES[r] for r in relaxed])
            except LLMUnavailable:
                reply = None
            reply = self.remove_unknown_ids(reply or "", {p["id"] for p in projects})
        if not reply:
            reply = self.template_reply(budget, projects, relaxed)
        return self._answer(reply, projects, relaxed, source, message, prefs, customer_id)

    # ---------- steps ----------
    @staticmethod
    def _clean(prefs, message, categories, styles):
        """Never trust the LLM's JSON: check every field against real data."""
        prefs = prefs if isinstance(prefs, dict) else {}
        try:
            budget = int(round(float(prefs.get("budget"))))
        except (TypeError, ValueError):
            budget = budget_parser.parse_budget(message)
        category = prefs.get("category") if prefs.get("category") in categories else None
        wanted = prefs.get("styles") if isinstance(prefs.get("styles"), list) else []
        by_lower = {s.lower(): s for s in styles}
        return {
            "budget": budget,
            "category": category,
            "styles": [by_lower[s.lower()] for s in wanted if isinstance(s, str) and s.lower() in by_lower],
            "property_type": prefs.get("property_type") if isinstance(prefs.get("property_type"), str) else None,
            "location": prefs.get("location") if isinstance(prefs.get("location"), str) else None,
            "strict_max": bool(prefs.get("strict_max")),
        }

    @staticmethod
    def _find_candidates(prefs):
        """Search, relaxing filters in this order until 3 are found: style, category, price window."""
        category, styles, widened, relaxed = prefs["category"], prefs["styles"], False, []
        while True:
            low, high = budget_window(prefs["budget"], prefs["strict_max"], widened)
            found = IDP.find_in_budget(low, high, category, styles)
            if len(found) >= 3:
                return found, relaxed, (low, high)
            if styles:
                styles = []
                relaxed.append("style")
            elif category:
                category = None
                relaxed.append("category")
            elif not widened:
                widened = True
                relaxed.append("budget_window")
            else:
                return found, relaxed, (low, high)

    @staticmethod
    def _card(idp, score, label):
        """What the React card shows. Built only from database data, never from LLM text."""
        slug = idp.category.lower().split()[0]
        return {"id": idp.id, "title": idp.title, "budget": idp.budget, "category": idp.category,
                "styles": idp.styles, "property_type": idp.property_type, "location": idp.location,
                "designer": idp.designer_name or "", "label": label, "score": score,
                "url": f"/idp/{idp.id}", "image": f"/project-{slug}.svg"}

    @staticmethod
    def remove_unknown_ids(reply, allowed_ids):
        """Drops every line that mentions a project id (#123) we did not choose."""
        kept = [line for line in reply.splitlines()
                if all(int(n) in allowed_ids for n in re.findall(r"#(\d+)", line))]
        return "\n".join(kept).strip()

    @staticmethod
    def template_reply(budget, projects, relaxed):
        lines = [f"Here are {len(projects)} projects for a budget of {money(budget)}:"]
        lines += [f"- #{p['id']} {p['title']}, {money(p['budget'])} ({p['label']})" for p in projects]
        lines += [RELAX_NOTES[r] for r in relaxed]
        return "\n".join(lines)

    @staticmethod
    def _answer(reply, projects, relaxed, source, message, prefs, customer_id):
        ChatLog.record(message, prefs, [p["id"] for p in projects], source, customer_id)
        return {"reply": reply, "projects": projects, "relaxed": relaxed, "source": source}
