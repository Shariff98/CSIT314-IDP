"""Shared rule for the designer's portfolio use cases: a designer may only change their own IDPs."""
from entity.category import Category
from entity.idp import IDP

PROPERTY_TYPES = ["HDB", "Condo", "Landed", "Commercial"]
STYLES = ["Modern", "Minimalist", "Scandinavian", "Industrial", "Japandi", "Classic", "Tropical",
          "Contemporary", "Luxury", "Rustic"]
MAX_TAGS = 5


def own_idp(designer_id, idp_id):
    """Returns the IDP if it belongs to this designer. Someone else's IDP is reported as
    'not found' so a designer cannot discover other designers' drafts."""
    idp = IDP.find_by_id(idp_id)
    if idp is None or idp.designer_id != designer_id:
        raise LookupError("Project not found")
    return idp


def check_category(name):
    category = Category.find_by_name((name or "").strip())
    if category is None or not category.is_active():
        raise ValueError("Choose an active category")
    return category.name


def check_property_type(value):
    value = (value or "").strip()
    if value and value not in PROPERTY_TYPES:
        raise ValueError("Property type must be one of: " + ", ".join(PROPERTY_TYPES))
    return value


def check_tags(text):
    from control.validation import clean_list
    tags = clean_list(text)
    tag_list = [t for t in tags.split(", ") if t]
    if len(tag_list) > MAX_TAGS:
        raise ValueError(f"Use at most {MAX_TAGS} style tags")
    if any(len(t) > 30 for t in tag_list):
        raise ValueError("Each style tag must be 30 characters or fewer")
    return tags
