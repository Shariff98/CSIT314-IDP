"""Database connection shared by all entity classes (SQLite, no ORM).

Only entity classes import this module. Boundary and control classes never
touch SQL, which keeps the b-c-e layers separate.
"""
import sqlite3
from contextlib import contextmanager
from datetime import datetime

_db_path = "platform.db"

BUILT_IN_PROFILES = [
    ("UserAdmin", "Manages user accounts and user profiles."),
    ("InteriorDesigner", "Manages company information, portfolio and interest statistics."),
    ("Customer", "Searches, views and saves interior design projects."),
    ("PlatformManager", "Manages IDP categories and views platform reports."),
]

DEFAULT_CATEGORIES = [
    ("Living Room", "Lounges, family rooms and open-plan living areas."),
    ("Kitchen", "Kitchens and pantries."),
    ("Bedroom", "Master, guest and kids' bedrooms."),
    ("Bathroom", "Bathrooms, ensuites and powder rooms."),
    ("Office", "Home offices and commercial office fit-outs."),
]


def configure(path):
    """Point the entities at a database file (tests use a temporary one)."""
    global _db_path
    _db_path = path


def now():
    """Timestamp format used in every table: 'YYYY-MM-DD HH:MM:SS'."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@contextmanager
def get_connection():
    """Opens a connection, commits on success, rolls back on error, always closes."""
    conn = sqlite3.connect(_db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


SCHEMA = """
CREATE TABLE IF NOT EXISTS user_profile (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL DEFAULT '',
    status      TEXT NOT NULL DEFAULT 'Active'          -- Active | Suspended
);

CREATE TABLE IF NOT EXISTS user_account (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT NOT NULL,
    email         TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role          TEXT NOT NULL,                         -- name of a user_profile
    status        TEXT NOT NULL DEFAULT 'Active',        -- Active | Suspended
    created_at    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS company (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    designer_id      INTEGER NOT NULL UNIQUE REFERENCES user_account(id) ON DELETE CASCADE,
    name             TEXT NOT NULL,
    registration_no  TEXT NOT NULL,
    address          TEXT NOT NULL DEFAULT '',
    phone            TEXT NOT NULL DEFAULT '',
    email            TEXT NOT NULL DEFAULT '',
    description      TEXT NOT NULL DEFAULT '',
    specialisations  TEXT NOT NULL DEFAULT '',           -- comma separated
    service_areas    TEXT NOT NULL DEFAULT '',           -- comma separated
    certifications   TEXT NOT NULL DEFAULT '',
    awards           TEXT NOT NULL DEFAULT '',
    years_experience INTEGER NOT NULL DEFAULT 0,
    budget_min       INTEGER,
    budget_max       INTEGER,
    services         TEXT NOT NULL DEFAULT '',           -- comma separated
    logo_file        TEXT,
    cover_file       TEXT,
    updated_at       TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS team_member (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL REFERENCES company(id) ON DELETE CASCADE,
    name       TEXT NOT NULL,
    position   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS category (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL DEFAULT '',
    status      TEXT NOT NULL DEFAULT 'Active',          -- Active | Suspended
    created_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS idp (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    designer_id     INTEGER NOT NULL REFERENCES user_account(id) ON DELETE CASCADE,
    title           TEXT NOT NULL,
    description     TEXT NOT NULL,
    category        TEXT NOT NULL,                       -- name of a category
    budget          INTEGER NOT NULL,
    style_tags      TEXT NOT NULL DEFAULT '',            -- comma separated, e.g. 'Modern,Minimalist'
    property_type   TEXT NOT NULL DEFAULT '',            -- HDB | Condo | Landed | Commercial
    location        TEXT NOT NULL DEFAULT '',
    completion_date TEXT,
    status          TEXT NOT NULL DEFAULT 'Current',     -- Current | Past
    published       INTEGER NOT NULL DEFAULT 1,          -- 1 published, 0 draft
    views           INTEGER NOT NULL DEFAULT 0,
    created_at      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS idp_photo (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    idp_id      INTEGER NOT NULL REFERENCES idp(id) ON DELETE CASCADE,
    filename    TEXT NOT NULL,
    is_cover    INTEGER NOT NULL DEFAULT 0,
    uploaded_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS favourite (
    customer_id INTEGER NOT NULL REFERENCES user_account(id) ON DELETE CASCADE,
    idp_id      INTEGER NOT NULL REFERENCES idp(id) ON DELETE CASCADE,
    saved_at    TEXT NOT NULL,
    PRIMARY KEY (customer_id, idp_id)
);

CREATE TABLE IF NOT EXISTS view_event (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    idp_id      INTEGER NOT NULL REFERENCES idp(id) ON DELETE CASCADE,
    customer_id INTEGER REFERENCES user_account(id) ON DELETE SET NULL,
    session_key TEXT,
    viewed_at   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS notification (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    designer_id INTEGER NOT NULL REFERENCES user_account(id) ON DELETE CASCADE,
    idp_id      INTEGER NOT NULL REFERENCES idp(id) ON DELETE CASCADE,
    message     TEXT NOT NULL,
    is_read     INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS chat_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id     INTEGER REFERENCES user_account(id) ON DELETE SET NULL,
    message         TEXT NOT NULL,
    filters         TEXT NOT NULL DEFAULT '{}',          -- JSON of the extracted preferences
    recommended_ids TEXT NOT NULL DEFAULT '',            -- comma separated idp ids
    source          TEXT NOT NULL DEFAULT 'llm',         -- llm | fallback
    created_at      TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_view_event_idp ON view_event(idp_id, viewed_at);
CREATE INDEX IF NOT EXISTS ix_favourite_idp ON favourite(idp_id, saved_at);
CREATE INDEX IF NOT EXISTS ix_idp_designer ON idp(designer_id);
"""


def init_db():
    """Creates the tables and the built-in profiles and default categories."""
    with get_connection() as conn:
        conn.executescript(SCHEMA)
        conn.executemany("INSERT OR IGNORE INTO user_profile (name, description) VALUES (?, ?)",
                         BUILT_IN_PROFILES)
        conn.executemany("INSERT OR IGNORE INTO category (name, description, created_at) VALUES (?, ?, ?)",
                         [(n, d, now()) for n, d in DEFAULT_CATEGORIES])
