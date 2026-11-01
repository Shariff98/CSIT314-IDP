"""Entity: Favourite. A customer's saved (shortlisted) IDP."""
import sqlite3

from entity.db import get_connection, now
from entity.idp import IDP


class Favourite:
    def __init__(self, customer_id, idp_id, saved_at=None):
        self.customer_id = customer_id
        self.idp_id = idp_id
        self.saved_at = saved_at

    @classmethod
    def add(cls, customer_id, idp_id, saved_at=None):
        """Returns False if the customer already saved this IDP."""
        try:
            with get_connection() as conn:
                conn.execute("INSERT INTO favourite (customer_id, idp_id, saved_at) VALUES (?, ?, ?)",
                             (customer_id, idp_id, saved_at or now()))
            return True
        except sqlite3.IntegrityError:
            return False

    @classmethod
    def remove(cls, customer_id, idp_id):
        """Returns False if it was not in the customer's favourites."""
        with get_connection() as conn:
            cur = conn.execute("DELETE FROM favourite WHERE customer_id = ? AND idp_id = ?", (customer_id, idp_id))
        return cur.rowcount == 1

    @classmethod
    def exists(cls, customer_id, idp_id):
        with get_connection() as conn:
            row = conn.execute("SELECT 1 FROM favourite WHERE customer_id = ? AND idp_id = ?",
                               (customer_id, idp_id)).fetchone()
        return row is not None

    @classmethod
    def list_for_customer(cls, customer_id, keyword="", category=None):
        sql = ("SELECT i.* FROM idp i JOIN favourite f ON f.idp_id = i.id WHERE f.customer_id = ? "
               "AND (i.title LIKE ? OR i.description LIKE ? OR i.style_tags LIKE ?)")
        params = [customer_id] + [f"%{keyword or ''}%"] * 3
        if category:
            sql += " AND i.category = ?"
            params.append(category)
        with get_connection() as conn:
            rows = conn.execute(sql + " ORDER BY f.saved_at DESC, i.id DESC", params).fetchall()
        return [IDP(**dict(r)) for r in rows]
