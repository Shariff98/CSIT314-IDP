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
COMPARE_WORDS = re.compile(r"\b(compare|comparison|side by side|which is better|difference between)\b", re.IGNORECASE)
PRICE_STEPS = {"cheaper": 0.8, "pricier": 1.25}
MAX_SEEN = 60
START_CHIPS = ["Modern kitchen around $10k", "Bedroom between $8k and $12k", "What can you do?"]
RANGE_BANDS = ["Lower end of your range", "Middle of your range", "Top of your range"]
RELAX_NOTES = {
    "style": "I couldn't find enough in that style, so I included other styles.",
    "category": "I couldn't find enough in that category, so I included other rooms.",
    "budget_window": "I widened the price range a little to find enough options.",
}
MEMORY_FIELDS = ("budget", "category", "styles", "exclude_styles", "property_type", "location")
SMALL_TALK = {
    "greeting": "Hi! I find interior design projects that fit your budget. Tell me the room, a style you like "
                "and your budget, for example \"Scandinavian bedroom around $12k\".",
    "thanks": "You're welcome! Tell me if you'd like to try another room, style or budget.",
    "help": "I match you with published design projects. You can tell me:\n"
            "- a room and budget: \"kitchen around $10k\" or \"between $8k and $12k\"\n"
            "- styles you like or don't: \"Japandi, but not industrial\"\n"
            "- a hard limit: \"no more than $15,000\"\n"
            "I remember what you said, so \"what about bathrooms?\" works. Say \"start over\" to reset.",
}
FORGET_WORDS = {"styles": re.compile(r"\bany (?:style|look)\b", re.IGNORECASE),
                "category": re.compile(r"\bany (?:room|category|space)\b", re.IGNORECASE)}
RESET_WORDS = re.compile(r"\b(start over|start again|new search|reset|forget (?:it|that|everything))\b", re.IGNORECASE)


class LLMUnavailable(Exception):
    """Raised by the LLM gateway when the service is down, slow, over its limit or not configured."""


# ---------- pure ranking functions (unit tested directly) ----------
def budget_window(budget, strict_max=False, widened=False, budget_min=None):
    """The price window to search. A range ("$8k to $12k") keeps its top and only lowers its floor when widened."""
    if budget_min:
        return (round(budget_min * WINDOW_LOW) if widened else budget_min), budget
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
    budget = target_price(prefs)
    popularity = [c.saves * 2 + c.views for c in candidates]
    top = max(popularity, default=0) or 1
    scored = []
    for idp, pop in zip(candidates, popularity):
        score = (WEIGHTS["fit"] * budget_fit(idp.budget, budget, low, high)
                 + WEIGHTS["preference"] * preference_match(idp, prefs)
                 + WEIGHTS["popularity"] * pop / top)
        scored.append((idp, round(score, 4)))
    return sorted(scored, key=lambda pair: (-pair[1], pair[0].budget, pair[0].id))


def target_price(prefs):
    """The price that scores best: the budget, or the middle of a range."""
    if prefs.get("budget_min"):
        return round((prefs["budget_min"] + prefs["budget"]) / 2)
    return prefs["budget"]


def band_labels(strict_max=False, budget_min=None):
    if budget_min:
        return RANGE_BANDS
    return [label for label, _, _ in (STRICT_BANDS if strict_max else BANDS)]


def band_of(price, budget, strict_max=False, budget_min=None):
    if budget_min:  # thirds of the range
        third = (budget - budget_min) / 3
        return RANGE_BANDS[0 if price <= budget_min + third else 1 if price <= budget_min + 2 * third else 2]
    for label, start, end in (STRICT_BANDS if strict_max else BANDS):
        if (start is None or price > budget * start) and (end is None or price <= budget * end):
            return label
    return (STRICT_BANDS if strict_max else BANDS)[-1][0]


def pick_three(scored, budget, strict_max=False, budget_min=None):
    """Best project in each price band, preferring 3 different designers.

    Empty bands are filled from the rest by score. Returns [(idp, score, label)]
    ordered by price.
    """
    chosen, designers = [], set()

    def take(pool):
        pool = [p for p in pool if p not in chosen]
        if not pool:
            return
        fresh = [p for p in pool if p[0].designer_id not in designers]
        pick = (fresh or pool)[0]
        chosen.append(pick)
        designers.add(pick[0].designer_id)

    for label in band_labels(strict_max, budget_min):
        take([p for p in scored if band_of(p[0].budget, budget, strict_max, budget_min) == label])
    while len(chosen) < 3 and len(chosen) < len(scored):
        take(scored)
    chosen.sort(key=lambda p: p[0].budget)
    return [(idp, score, band_of(idp.budget, budget, strict_max, budget_min)) for idp, score in chosen]


def money(amount):
    return f"${amount:,.0f}"


# ---------- the controller ----------
class RecommendIDPsController:
    def __init__(self, llm_gateway):
        self.llm = llm_gateway

    def recommend(self, message, history=None, customer_id=None, context=None):
        """Returns {"reply", "projects", "relaxed", "source", "prefs"}. Raises ValueError for an empty message.

        context is the "prefs" the previous answer returned. Anything this message
        does not mention is carried over from it, so "what about bathrooms?" keeps
        the budget and "make it $12k" keeps the room, with or without the LLM.
        """
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
        if COMPARE_WORDS.search(message):
            previous = self._clean(context or {}, "", categories, styles)
            return self._compare(message, previous, source, customer_id)
        said_nothing_new = not any(prefs[f] for f in MEMORY_FIELDS)
        intent = budget_parser.detect_intent(message)
        if said_nothing_new and (intent or not context):
            return self._answer(SMALL_TALK[intent or "help"], [], [], source, message, prefs, customer_id)
        if context and not RESET_WORDS.search(message):
            previous = self._clean(context, "", categories, styles)
            for field, words in FORGET_WORDS.items():
                if words.search(message):
                    previous[field] = [] if field == "styles" else None
                    if field == "styles":
                        previous["exclude_styles"] = []
            followup = budget_parser.detect_followup(message)
            new_budget = prefs["budget"]
            prefs = self.merge(previous, prefs)
            if followup in PRICE_STEPS and new_budget is None and prefs["budget"]:
                prefs = self.step_budget(prefs, PRICE_STEPS[followup])
            prefs["seen_ids"] = previous["seen_ids"] if followup == "more" else []

        budget = prefs["budget"]
        if budget is None:
            return self._answer(self.ask_budget(prefs), [], [], source, message, prefs, customer_id)
        if not MIN_BUDGET <= budget <= MAX_BUDGET:
            return self._answer(f"That budget doesn't look right. Please give an amount between "
                                f"{money(MIN_BUDGET)} and {money(MAX_BUDGET)}.",
                                [], [], source, message, prefs, customer_id)

        candidates, relaxed, (low, high) = self._find_candidates(prefs)
        if not candidates and prefs["seen_ids"]:
            return self._answer("That's everything I have for this search. Try a different budget, room or style.",
                                [], relaxed, source, message, prefs, customer_id)
        if not candidates:
            return self._answer(f"I couldn't find any published projects near {money(budget)}. "
                                "Try a different budget or room.", [], relaxed, source, message, prefs, customer_id)

        picks = pick_three(score_candidates(candidates, prefs, low, high), budget, prefs["strict_max"],
                           prefs["budget_min"])
        projects = [self._card(idp, score, label) for idp, score, label in picks]

        reply = None
        if source == "llm":
            try:
                reply = self.llm.write_reply(message, projects, [RELAX_NOTES[r] for r in relaxed])
            except LLMUnavailable:
                reply = None
            reply = self.remove_unknown_ids(reply or "", {p["id"] for p in projects})
        if not reply:
            reply = self.template_reply(budget, projects, relaxed, prefs["budget_min"])
        return self._answer(reply, projects, relaxed, source, message, prefs, customer_id)

    # ---------- compare ----------
    def _compare(self, message, previous, source, customer_id):
        """Side-by-side facts for 2 to 4 published projects: "#12 vs #15", or the last ones shown.

        Pure database facts, no LLM, so nothing in the comparison can be made up.
        """
        ids = list(dict.fromkeys(int(n) for n in re.findall(r"#(\d+)", message)))
        if len(ids) < 2:
            ids = previous["seen_ids"][-3:]
        idps = IDP.find_published(ids[:4])
        prefs = {**previous, "seen_ids": previous["seen_ids"]}
        if len(idps) < 2:
            return self._answer("Tell me which projects to compare, like \"compare #12 and #15\", "
                                "or search first and tap Compare these.", [], [], source, message, prefs, customer_id)
        rows = [self.comparison_row(idp, previous) for idp in idps]
        reply = self.comparison_reply(rows, previous)
        result = self._answer(reply, [], [], source, message, prefs, customer_id)
        result["comparison"] = rows
        return result

    @staticmethod
    def comparison_row(idp, prefs):
        budget = prefs.get("budget")
        return {"id": idp.id, "title": idp.title, "budget": idp.budget, "category": idp.category,
                "styles": idp.styles, "property_type": idp.property_type or "", "location": idp.location or "",
                "designer": idp.designer_name or "", "views": idp.views, "saves": idp.saves,
                "vs_budget": idp.budget - budget if budget else None,
                "matches": round(preference_match(idp, prefs) * 100) if budget else None,
                "url": f"/idp/{idp.id}"}

    @staticmethod
    def comparison_reply(rows, prefs):
        """One line per project that wins something, e.g. "#12 Oak Kitchen: cheapest, closest to your $10,000"."""
        wins = {}

        def win(row, reason):
            wins.setdefault(row["id"], (row, []))[1].append(reason)

        win(min(rows, key=lambda r: (r["budget"], r["id"])), f"cheapest at {money(min(r['budget'] for r in rows))}")
        popular = max(rows, key=lambda r: (r["saves"] * 2 + r["views"], -r["id"]))
        win(popular, f"most popular ({popular['saves']} saves, {popular['views']} views)")
        if prefs.get("budget"):
            win(min(rows, key=lambda r: (abs(r["vs_budget"]), r["budget"])), f"closest to your {money(prefs['budget'])}")
            if len({r["matches"] for r in rows}) > 1:
                win(max(rows, key=lambda r: (r["matches"], -abs(r["vs_budget"]))), "best match for what you asked")
        lines = [f"Comparing {len(rows)} projects:"]
        lines += [f"- #{row['id']} {row['title']}: {', '.join(reasons)}" for row, reasons in wins.values()]
        return "\n".join(lines)

    # ---------- steps ----------
    @staticmethod
    def merge(previous, new):
        """New values win; anything the new message left empty comes from the previous turn.

        strict_max and budget_min belong to the budget: they only carry over when the budget does.
        Excluded styles add up across messages.
        """
        merged = {f: new[f] or previous[f] for f in MEMORY_FIELDS}
        source = new if new["budget"] is not None else previous
        merged["strict_max"], merged["budget_min"] = source["strict_max"], source["budget_min"]
        # Liking a style you excluded earlier (or the other way round) cancels the old choice.
        merged["styles"] = [s for s in merged["styles"] if s not in new["exclude_styles"]]
        excluded = list(dict.fromkeys(previous["exclude_styles"] + new["exclude_styles"]))  # "and no rustic" adds up
        merged["exclude_styles"] = [s for s in excluded if s not in new["styles"]]
        return merged

    @staticmethod
    def step_budget(prefs, factor):
        """"Cheaper" / "a bit more": move the budget (and a range's floor) by factor, to the nearest $100."""
        def step(amount):
            return int(round(amount * factor / 100) * 100) if amount else amount
        return {**prefs, "budget": step(prefs["budget"]), "budget_min": step(prefs["budget_min"])}

    @staticmethod
    def suggestions(prefs, projects):
        """Follow-up chips. Each one is plain text the parser understands, so typing it works the same."""
        if not projects:
            return [] if prefs.get("budget") or prefs.get("category") else START_CHIPS
        chips = ["Show more", "Cheaper", "A bit more"] + (["Compare these"] if len(projects) >= 2 else [])
        if prefs.get("styles"):
            chips.append("Any style")
        if prefs.get("category"):
            chips.append("Any room")
        return chips

    @staticmethod
    def ask_budget(prefs):
        wanted = " ".join(filter(None, [", ".join(prefs["styles"]), prefs["category"]]))
        if wanted:
            return f"Sounds good, a {wanted.lower()} project. What budget do you have in mind? For example: \"around $10,000\"."
        return "What budget do you have in mind? For example: \"kitchen, around $10,000\"."

    @staticmethod
    def _clean(prefs, message, categories, styles):
        """Never trust the LLM's JSON: check every field against real data."""
        prefs = prefs if isinstance(prefs, dict) else {}
        try:
            budget = int(round(float(prefs.get("budget"))))
        except (TypeError, ValueError):
            budget = budget_parser.parse_budget(message)
        category = prefs.get("category") if prefs.get("category") in categories else None
        by_lower = {s.lower(): s for s in styles}

        def known(key):
            names = prefs.get(key) if isinstance(prefs.get(key), list) else []
            return list(dict.fromkeys(by_lower[s.lower()] for s in names if isinstance(s, str) and s.lower() in by_lower))

        excluded = known("exclude_styles")
        seen = prefs.get("seen_ids") if isinstance(prefs.get("seen_ids"), list) else []
        seen = [n for n in seen if isinstance(n, int) and not isinstance(n, bool)][-MAX_SEEN:]
        try:
            budget_min = int(round(float(prefs.get("budget_min"))))
        except (TypeError, ValueError):
            budget_min = None
        if budget is None or budget_min is None or not 0 < budget_min < budget:
            budget_min = None
        return {
            "budget": budget,
            "budget_min": budget_min,
            "category": category,
            "styles": [s for s in known("styles") if s not in excluded],
            "exclude_styles": excluded,
            "property_type": prefs.get("property_type") if isinstance(prefs.get("property_type"), str) else None,
            "location": prefs.get("location") if isinstance(prefs.get("location"), str) else None,
            "strict_max": bool(prefs.get("strict_max")) or budget_min is not None,
            "seen_ids": seen,
        }

    @staticmethod
    def _find_candidates(prefs):
        """Search, relaxing filters in this order until 3 are found: style, category, price window."""
        category, styles, widened, relaxed = prefs["category"], prefs["styles"], False, []
        while True:
            low, high = budget_window(prefs["budget"], prefs["strict_max"], widened, prefs["budget_min"])
            found = [idp for idp in IDP.find_in_budget(low, high, category, styles)
                     if not set(idp.styles) & set(prefs["exclude_styles"]) and idp.id not in prefs["seen_ids"]]
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
    def template_reply(budget, projects, relaxed, budget_min=None):
        span = f"{money(budget_min)} to {money(budget)}" if budget_min else f"a budget of {money(budget)}"
        lines = [f"Here are {len(projects)} projects for {span}:"]
        lines += [f"- #{p['id']} {p['title']}, {money(p['budget'])} ({p['label']})" for p in projects]
        lines += [RELAX_NOTES[r] for r in relaxed]
        return "\n".join(lines)

    @staticmethod
    def _answer(reply, projects, relaxed, source, message, prefs, customer_id):
        ChatLog.record(message, prefs, [p["id"] for p in projects], source, customer_id)
        seen = (prefs.get("seen_ids", []) + [p["id"] for p in projects])[-MAX_SEEN:]
        prefs = {**prefs, "seen_ids": seen}
        return {"reply": reply, "projects": projects, "relaxed": relaxed, "source": source, "prefs": prefs,
                "suggestions": RecommendIDPsController.suggestions(prefs, projects)}
