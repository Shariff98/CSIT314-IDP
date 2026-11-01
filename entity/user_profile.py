"""Entity: UserProfile. A role in the system (e.g. Customer) that accounts belong to."""
from entity.db import get_connection


class UserProfile:
    def __init__(self, id, name, description="", status="Active"):
        self.id = id
        self.name = name
        self.description = description
        self.status = status

    @staticmethod
    def _from_row(row):
        return UserProfile(**dict(row)) if row else None

    @classmethod
    def create(cls, name, description):
        with get_connection() as conn:
            cur = conn.execute("INSERT INTO user_profile (name, description) VALUES (?, ?)", (name, description))
        return cls.find_by_id(cur.lastrowid)

    @classmethod
    def find_by_id(cls, profile_id):
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM user_profile WHERE id = ?", (profile_id,)).fetchone()
        return cls._from_row(row)

    @classmethod
    def find_by_name(cls, name):
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM user_profile WHERE name = ? COLLATE NOCASE", (name,)).fetchone()
        return cls._from_row(row)

    @classmethod
    def search(cls, keyword="", status=None):
        sql = "SELECT * FROM user_profile WHERE (name LIKE ? OR description LIKE ?)"
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
        """Renaming a profile also moves every account that uses it."""
        with get_connection() as conn:
            conn.execute("UPDATE user_account SET role = ? WHERE role = ?", (name, self.name))
            conn.execute("UPDATE user_profile SET name = ?, description = ? WHERE id = ?",
                         (name, description, self.id))
        self.name, self.description = name, description

    def is_suspended(self):
        return self.status == "Suspended"

    def _set_status(self, status):
        self.status = status
        with get_connection() as conn:
            conn.execute("UPDATE user_profile SET status = ? WHERE id = ?", (status, self.id))

    def suspend(self):
        self._set_status("Suspended")

    def reactivate(self):
        self._set_status("Active")

    def account_count(self):
        with get_connection() as conn:
            return conn.execute("SELECT COUNT(*) FROM user_account WHERE role = ?", (self.name,)).fetchone()[0]
