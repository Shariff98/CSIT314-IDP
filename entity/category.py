"""Entity: Category. Groups IDPs (e.g. Kitchen, Office). Managed by Platform Management."""
from entity.db import get_connection, now


class Category:
    def __init__(self, id, name, description="", status="Active", created_at=None):
        self.id = id
        self.name = name
        self.description = description
        self.status = status
        self.created_at = created_at

    @staticmethod
    def _from_row(row):
        return Category(**dict(row)) if row else None

    @classmethod
    def create(cls, name, description, created_at=None):
        with get_connection() as conn:
            cur = conn.execute("INSERT INTO category (name, description, created_at) VALUES (?, ?, ?)",
                               (name, description, created_at or now()))
        return cls.find_by_id(cur.lastrowid)

    @classmethod
    def find_by_id(cls, category_id):
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM category WHERE id = ?", (category_id,)).fetchone()
        return cls._from_row(row)

    @classmethod
    def find_by_name(cls, name):
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM category WHERE name = ? COLLATE NOCASE", (name,)).fetchone()
        return cls._from_row(row)

    @classmethod
    def search(cls, keyword="", status=None):
        sql = "SELECT * FROM category WHERE (name LIKE ? OR description LIKE ?)"
        params = [f"%{keyword}%", f"%{keyword}%"]
        if status:
            sql += " AND status = ?"
            params.append(status)
        with get_connection() as conn:
            rows = conn.execute(sql + " ORDER BY name", params).fetchall()
        return [cls._from_row(r) for r in rows]

    @classmethod
    def all_active(cls):
        return cls.search(status="Active")

    def update(self, name, description):
        """Renaming a category also renames it on every IDP that uses it."""
        with get_connection() as conn:
            conn.execute("UPDATE idp SET category = ? WHERE category = ?", (name, self.name))
            conn.execute("UPDATE category SET name = ?, description = ? WHERE id = ?", (name, description, self.id))
        self.name, self.description = name, description

    def idp_count(self):
        with get_connection() as conn:
            return conn.execute("SELECT COUNT(*) FROM idp WHERE category = ?", (self.name,)).fetchone()[0]

    def reassign_idps(self, target_name):
        """Moves every IDP in this category to another category. Returns how many moved."""
        with get_connection() as conn:
            cur = conn.execute("UPDATE idp SET category = ? WHERE category = ?", (target_name, self.name))
        return cur.rowcount

    def is_active(self):
        return self.status == "Active"

    def _set_status(self, status):
        self.status = status
        with get_connection() as conn:
            conn.execute("UPDATE category SET status = ? WHERE id = ?", (status, self.id))

    def suspend(self):
        self._set_status("Suspended")

    def reactivate(self):
        self._set_status("Active")

    def delete(self):
        with get_connection() as conn:
            conn.execute("DELETE FROM category WHERE id = ?", (self.id,))
