"""Entity: one chatbot request and what it recommended (postcondition of the use case)."""
import json

from entity.db import get_connection, now


class ChatLog:
    @staticmethod
    def record(message, filters, recommended_ids, source, customer_id=None):
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO chat_log (customer_id, message, filters, recommended_ids, source, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (customer_id, message, json.dumps(filters), ",".join(str(i) for i in recommended_ids), source, now()),
            )

    @staticmethod
    def all():
        with get_connection() as conn:
            return [dict(r) for r in conn.execute("SELECT * FROM chat_log ORDER BY id").fetchall()]
