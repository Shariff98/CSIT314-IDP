"""Entity: ViewEvent. One customer view of an IDP, with a timestamp for reports and trends."""
from entity.db import get_connection, now


class ViewEvent:
    @classmethod
    def record(cls, idp_id, customer_id=None, session_key=None, viewed_at=None):
        with get_connection() as conn:
            conn.execute("INSERT INTO view_event (idp_id, customer_id, session_key, viewed_at) VALUES (?, ?, ?, ?)",
                         (idp_id, customer_id, session_key, viewed_at or now()))
            conn.execute("UPDATE idp SET views = views + 1 WHERE id = ?", (idp_id,))

    @classmethod
    def seen_in_session(cls, idp_id, session_key):
        with get_connection() as conn:
            row = conn.execute("SELECT 1 FROM view_event WHERE idp_id = ? AND session_key = ?",
                               (idp_id, session_key)).fetchone()
        return row is not None
