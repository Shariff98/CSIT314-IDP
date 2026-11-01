"""Entity: TeamMember. A person listed on a designer's company page."""
from entity.db import get_connection


class TeamMember:
    def __init__(self, id, company_id, name, position):
        self.id = id
        self.company_id = company_id
        self.name = name
        self.position = position

    @classmethod
    def add(cls, company_id, name, position):
        with get_connection() as conn:
            cur = conn.execute("INSERT INTO team_member (company_id, name, position) VALUES (?, ?, ?)",
                               (company_id, name, position))
        return cls(cur.lastrowid, company_id, name, position)

    @classmethod
    def remove(cls, company_id, member_id):
        """Returns True if a member of this company was removed."""
        with get_connection() as conn:
            cur = conn.execute("DELETE FROM team_member WHERE id = ? AND company_id = ?", (member_id, company_id))
        return cur.rowcount == 1

    @classmethod
    def list_for_company(cls, company_id):
        with get_connection() as conn:
            rows = conn.execute("SELECT * FROM team_member WHERE company_id = ? ORDER BY id", (company_id,)).fetchall()
        return [cls(**dict(r)) for r in rows]
