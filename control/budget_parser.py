"""Fallback parser: pulls a budget, category and styles out of plain text with no LLM.

Used when the LLM service is down, over its limit, or has no API key (use case
alternate flow A3). It returns the same dictionary shape as
LLMGateway.extract_preferences(), so the controller treats both the same way.
"""
import re

# "$10k", "10,000", "10000 dollars", "$12.5k", "1.2m", "-5000"
MONEY = re.compile(
    r"(?P<neg>-)?\$?\s?(?P<num>\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?)\s?(?P<suffix>k|m|thousand|million)?\b",
    re.IGNORECASE,
)
STRICT_WORDS = re.compile(r"\b(max|maximum|no more than|not more than|at most|up to|under|below|cap|limit)\b",
                          re.IGNORECASE)
CATEGORY_WORDS = {
    "Kitchen": ["kitchen", "pantry"],
    "Bathroom": ["bathroom", "bath", "toilet", "ensuite", "washroom"],
    "Bedroom": ["bedroom", "bed room", "master room", "kids room"],
    "Living Room": ["living room", "living", "lounge", "family room"],
    "Office": ["office", "study", "workspace"],
}
PROPERTY_WORDS = {"HDB": ["hdb"], "Condo": ["condo", "condominium", "apartment"],
                  "Landed": ["landed", "house", "terrace", "bungalow"], "Commercial": ["commercial", "shop"]}


def parse_budget(text):
    """Returns the first money amount in the text as an int, or None.

    A bare number only counts if it is 1,000 or more, so "3 bedrooms" is not a
    budget. A negative amount is returned as negative so the controller can
    reject it and ask again (alternate flow A4).
    """
    for match in MONEY.finditer(text or ""):
        raw, suffix = match.group("num"), (match.group("suffix") or "").lower()
        has_dollar = "$" in match.group(0)
        value = float(raw.replace(",", ""))
        if suffix in ("k", "thousand"):
            value *= 1_000
        elif suffix in ("m", "million"):
            value *= 1_000_000
        elif not has_dollar and "," not in raw and value < 1_000:
            continue  # "3 bedrooms", "2 kids"
        value = int(round(value))
        return -value if match.group("neg") else value
    return None


def _find(words_by_name, text):
    lowered = f" {text.lower()} "
    for name, words in words_by_name.items():
        if any(re.search(rf"\b{re.escape(w)}\b", lowered) for w in words):
            return name
    return None


def parse(text, categories=(), styles=()):
    """Plain-text version of the LLM's first step."""
    lowered = (text or "").lower()
    category = _find(CATEGORY_WORDS, text or "")
    if category not in categories:
        category = next((c for c in categories if c.lower() in lowered), None)
    return {
        "budget": parse_budget(text),
        "category": category,
        "styles": [s for s in styles if re.search(rf"\b{re.escape(s.lower())}\b", lowered)],
        "property_type": _find(PROPERTY_WORDS, text or ""),
        "location": None,
        "strict_max": bool(STRICT_WORDS.search(text or "")),
    }
