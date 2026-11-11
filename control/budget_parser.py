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
# Everyday words for the style tags designers use. Only names that exist in the data are kept.
STYLE_WORDS = {
    "Scandinavian": ["scandi", "nordic"],
    "Minimalist": ["minimal", "minimalistic", "clean and simple"],
    "Japandi": ["japanese", "wabi sabi", "zen"],
    "Industrial": ["loft", "exposed brick", "raw concrete"],
    "Classic": ["traditional", "vintage", "timeless"],
    "Rustic": ["farmhouse", "cottage", "country"],
    "Luxury": ["luxurious", "high end", "high-end", "premium", "opulent"],
    "Tropical": ["bali", "balinese", "resort"],
    "Modern": ["sleek"],
    "Contemporary": ["current", "trendy"],
}
NEGATION = r"(?:not|no|without|except|avoid|anything but|nothing|don'?t want|do not want|hate|dislike)"
# "between $8k and $12k", "8-12k", "from 8,000 to 12,000"
RANGE = re.compile(
    r"(?:between|from)?\s*\$?\s?(?P<low>\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?)\s?(?P<low_suffix>k|m|thousand)?"
    r"\s*(?:-|–|to|and)\s*"
    r"\$?\s?(?P<high>\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?)\s?(?P<high_suffix>k|m|thousand|million)?\b",
    re.IGNORECASE,
)
INTENTS = {
    "greeting": re.compile(r"^\s*(hi|hello|hey|hiya|yo|good (morning|afternoon|evening))\b", re.IGNORECASE),
    "thanks": re.compile(r"\b(thanks|thank you|thx|cheers|appreciate it)\b", re.IGNORECASE),
    "help": re.compile(r"\b(help|what can you do|how does this work|how do you work|who are you)\b", re.IGNORECASE),
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


def _amount(number, suffix):
    value = float(number.replace(",", ""))
    suffix = (suffix or "").lower()
    if suffix in ("k", "thousand"):
        value *= 1_000
    elif suffix in ("m", "million"):
        value *= 1_000_000
    return int(round(value))


def parse_range(text):
    """Returns (low, high) for "between $8k and $12k" or "8-12k", else None.

    A suffix on the second number also applies to the first ("8-12k" is 8,000 to
    12,000). Both ends must be 1,000 or more and low must be below high, so
    "2 to 3 bedrooms" is not a range.
    """
    for match in RANGE.finditer(text or ""):
        high = _amount(match.group("high"), match.group("high_suffix"))
        low = _amount(match.group("low"), match.group("low_suffix") or match.group("high_suffix"))
        if 1_000 <= low < high:
            return low, high
    return None


def detect_intent(text):
    """"greeting", "thanks" or "help" for small talk, else None."""
    for name, pattern in INTENTS.items():
        if pattern.search(text or ""):
            return name
    return None


def _style_terms(style):
    return [style.lower()] + STYLE_WORDS.get(style, [])


def find_styles(text, styles):
    """(wanted, excluded) style names. "not industrial" or "no rustic please" goes in excluded."""
    lowered = (text or "").lower()
    wanted, excluded = [], []
    for style in styles:
        terms = "|".join(re.escape(t) for t in _style_terms(style))
        if re.search(rf"\b{NEGATION}\s+(?:(?:too|very|anything|the|a|any)\s+)?(?:{terms})\b", lowered):
            excluded.append(style)
        elif re.search(rf"\b(?:{terms})\b", lowered):
            wanted.append(style)
    return wanted, excluded


def _find(words_by_name, text):
    lowered = f" {text.lower()} "
    for name, words in words_by_name.items():
        if any(re.search(rf"\b{re.escape(w)}s?\b", lowered) for w in words):
            return name
    return None


def parse(text, categories=(), styles=()):
    """Plain-text version of the LLM's first step."""
    lowered = (text or "").lower()
    # An exact category name wins over a synonym, so "study" finds Study when it exists, not Office.
    category = next((c for c in sorted(categories, key=len, reverse=True)
                     if re.search(rf"\b{re.escape(c.lower())}s?\b", lowered)), None)
    if category is None:
        category = _find(CATEGORY_WORDS, text or "")
        if category not in categories:
            category = None
    wanted, excluded = find_styles(text, styles)
    budget_range = parse_range(text)
    return {
        "budget": budget_range[1] if budget_range else parse_budget(text),
        "budget_min": budget_range[0] if budget_range else None,
        "category": category,
        "styles": wanted,
        "exclude_styles": excluded,
        "property_type": _find(PROPERTY_WORDS, text or ""),
        "location": None,
        "strict_max": bool(budget_range) or bool(STRICT_WORDS.search(text or "")),
    }
