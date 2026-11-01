"""Entity: Notification. A message to a designer, e.g. an IDP reached 50 views."""
from entity.db import get_connection, now


class Notification:
    def __init__(self, id, designer_id, idp_id, message, is_read=0, created_at=None):
        self.id = id
        self.designer_id = designer_id
        self.idp_id = idp_id
        self.message = message
        self.is_read = is_read
        self.created_at = created_at

    @classmethod
    def create(cls, designer_id, idp_id, message):
        with get_connection() as conn:
            cur = conn.execute("INSERT INTO notification (designer_id, idp_id, message, created_at) VALUES (?, ?, ?, ?)",
                               (designer_id, idp_id, message, now()))
        return cls(cur.lastrowid, designer_id, idp_id, message, 0, now())

    @classmethod
    def exists(cls, idp_id, message):
        with get_connection() as conn:
            return conn.execute("SELECT 1 FROM notification WHERE idp_id = ? AND message = ?",
                                (idp_id, message)).fetchone() is not None

    @classmethod
    def list_for_designer(cls, designer_id, unread_only=False):
        sql = "SELECT * FROM notification WHERE designer_id = ?" + (" AND is_read = 0" if unread_only else "")
        with get_connection() as conn:
            rows = conn.execute(sql + " ORDER BY id DESC", (designer_id,)).fetchall()
        return [cls(**dict(r)) for r in rows]

    @classmethod
    def mark_all_read(cls, designer_id):
        with get_connection() as conn:
            conn.execute("UPDATE notification SET is_read = 1 WHERE designer_id = ?", (designer_id,))
