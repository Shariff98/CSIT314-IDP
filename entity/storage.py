"""File storage for uploaded images (IDP photos, company logo and cover).

Like db.py, this is persistence, so only entity classes use it."""
import os
import uuid

_upload_dir = "uploads"


def configure(path):
    global _upload_dir
    _upload_dir = path
    os.makedirs(_upload_dir, exist_ok=True)


def upload_dir():
    return _upload_dir


def save(data, extension):
    """Writes the bytes to a new, randomly named file and returns its name."""
    filename = f"{uuid.uuid4().hex}.{extension}"
    with open(os.path.join(_upload_dir, filename), "wb") as fh:
        fh.write(data)
    return filename


def delete(filename):
    path = os.path.join(_upload_dir, filename or "")
    if filename and os.path.isfile(path):
        os.remove(path)
