"""Entity: UserAccount. Holds account data and knows how to load and save itself."""
from werkzeug.security import generate_password_hash, check_password_hash

from entity.db import get_connection, now


class UserAccount:
    def __init__(self, id, name, email, password_hash, role, status="Active", created_at=None):
        self.id = id
        self.name = name
        self.email = email
        self.password_hash = password_hash
        self.role = role
        self.status = status
        self.created_at = created_at

    @staticmethod
    def _from_row(row):
        return UserAccount(**dict(row)) if row else None

    @classmethod
    def create(cls, name, email, password, role, created_at=None):
        with get_connection() as conn:
            cur = conn.execute(
                "INSERT INTO user_account (name, email, password_hash, role, created_at) VALUES (?, ?, ?, ?, ?)",
                (name, email.lower(), generate_password_hash(password), role, created_at or now()),
            )
        return cls.find_by_id(cur.lastrowid)

    @classmethod
    def find_by_id(cls, account_id):
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM user_account WHERE id = ?", (account_id,)).fetchone()
        return cls._from_row(row)

    @classmethod
    def find_by_email(cls, email):
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM user_account WHERE email = ?", ((email or "").lower(),)).fetchone()
        return cls._from_row(row)

    @classmethod
    def search(cls, keyword="", role=None, status=None):
        """Matches the keyword against name or email, optionally narrowed by role and status."""
        sql = "SELECT * FROM user_account WHERE (name LIKE ? OR email LIKE ?)"
        params = [f"%{keyword}%", f"%{keyword}%"]
        if role:
            sql += " AND role = ?"
            params.append(role)
        if status:
            sql += " AND status = ?"
            params.append(status)
        with get_connection() as conn:
            rows = conn.execute(sql + " ORDER BY name, id", params).fetchall()
        return [cls._from_row(r) for r in rows]

    def update(self, name, email, role):
        with get_connection() as conn:
            conn.execute("UPDATE user_account SET name = ?, email = ?, role = ? WHERE id = ?",
                         (name, email.lower(), role, self.id))
        self.name, self.email, self.role = name, email.lower(), role

    def check_password(self, password):
        return check_password_hash(self.password_hash, password or "")

    def is_suspended(self):
        return self.status == "Suspended"

    def _set_status(self, status):
        self.status = status
        with get_connection() as conn:
            conn.execute("UPDATE user_account SET status = ? WHERE id = ?", (status, self.id))

    def suspend(self):
        self._set_status("Suspended")

    def reactivate(self):
        self._set_status("Active")
