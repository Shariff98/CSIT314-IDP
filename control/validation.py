"""Small input checks shared by the controllers. Each raises ValueError with a message
the boundary can show to the user."""
import re
from datetime import date, datetime

EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE = re.compile(r"^\+?[0-9 ()-]{6,20}$")
IMAGE_TYPES = {"jpg", "jpeg", "png", "gif", "webp"}
MAX_IMAGE_BYTES = 5 * 1024 * 1024


def clean(value):
    return (value or "").strip()


def require(**values):
    """require(title=..., description=...) -> raises 'Missing: title, description'."""
    missing = [name.replace("_", " ") for name, value in values.items() if not clean(str(value or ""))]
    if missing:
        raise ValueError("Missing: " + ", ".join(missing))


def check_email(email):
    if not EMAIL.match(clean(email)):
        raise ValueError("Email address is not valid")
    return clean(email).lower()


def check_phone(phone, required=False):
    phone = clean(phone)
    if not phone and not required:
        return ""
    if not PHONE.match(phone):
        raise ValueError("Phone number is not valid")
    return phone


def to_int(value, label, minimum=None, maximum=None, allow_blank=False):
    if allow_blank and clean(str(value if value is not None else "")) == "":
        return None
    try:
        number = int(str(value).strip())
    except (TypeError, ValueError):
        raise ValueError(f"{label} must be a whole number")
    if minimum is not None and number < minimum:
        raise ValueError(f"{label} must be at least {minimum}" if minimum != 1 else f"{label} must be greater than 0")
    if maximum is not None and number > maximum:
        raise ValueError(f"{label} must be at most {maximum}")
    return number


def to_date(value, label, allow_blank=True):
    """Accepts 'YYYY-MM-DD' (what an HTML date input sends) or a date object."""
    if isinstance(value, date):
        return value.isoformat()
    if allow_blank and not clean(value):
        return None
    try:
        return datetime.strptime(clean(value), "%Y-%m-%d").date().isoformat()
    except ValueError:
        raise ValueError(f"{label} must be a date (YYYY-MM-DD)")


def clean_list(text):
    """' modern ,Minimalist,, ' -> 'Modern, Minimalist' (no blanks, no duplicates)."""
    seen, items = set(), []
    for part in (text or "").split(","):
        item = part.strip()
        if item and item.lower() not in seen:
            seen.add(item.lower())
            items.append(item[:1].upper() + item[1:])
    return ", ".join(items)


def image_extension(filename, data):
    extension = clean(filename).rsplit(".", 1)[-1].lower() if "." in clean(filename) else ""
    if extension not in IMAGE_TYPES:
        raise ValueError("Only JPG, PNG, GIF or WEBP images can be uploaded")
    if not data:
        raise ValueError("The file is empty")
    if len(data) > MAX_IMAGE_BYTES:
        raise ValueError("Images must be 5 MB or smaller")
    return extension
