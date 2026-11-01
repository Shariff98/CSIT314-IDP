"""Entity: Report. Platform activity between two dates (daily, weekly or monthly).

Reports are calculated from the stored data each time, so they are never out of date."""
from entity.db import get_connection


class Report:
    def __init__(self, period, start, end, metrics, top_categories, top_idps):
        self.period = period
        self.start = start
        self.end = end
        self.metrics = metrics
        self.top_categories = top_categories
        self.top_idps = top_idps

    @classmethod
    def build(cls, period, start, end):
        """start and end are 'YYYY-MM-DD' strings and both days are included."""
        rng = (start, end)
        between = "date({}) BETWEEN date(?) AND date(?)"
        with get_connection() as conn:
            def count(sql, params=rng):
                return conn.execute(sql, params).fetchone()[0]

            metrics = {
                "New accounts": count("SELECT COUNT(*) FROM user_account WHERE " + between.format("created_at")),
                "New interior designers": count("SELECT COUNT(*) FROM user_account WHERE role = 'InteriorDesigner' "
                                                "AND " + between.format("created_at")),
                "New customers": count("SELECT COUNT(*) FROM user_account WHERE role = 'Customer' AND "
                                       + between.format("created_at")),
                "New IDPs": count("SELECT COUNT(*) FROM idp WHERE " + between.format("created_at")),
                "IDP views": count("SELECT COUNT(*) FROM view_event WHERE " + between.format("viewed_at")),
                "Shortlists (saved to favourites)": count("SELECT COUNT(*) FROM favourite WHERE "
                                                          + between.format("saved_at")),
                "New categories": count("SELECT COUNT(*) FROM category WHERE " + between.format("created_at")),
            }
            top_categories = [dict(r) for r in conn.execute(
                "SELECT i.category AS name, COUNT(*) AS views FROM view_event v JOIN idp i ON i.id = v.idp_id "
                "WHERE " + between.format("v.viewed_at") + " GROUP BY i.category ORDER BY views DESC, name LIMIT 5",
                rng).fetchall()]
            top_idps = [dict(r) for r in conn.execute(
                "SELECT i.id, i.title, i.category, COUNT(*) AS views FROM view_event v JOIN idp i ON i.id = v.idp_id "
                "WHERE " + between.format("v.viewed_at") + " GROUP BY i.id ORDER BY views DESC, i.id LIMIT 5",
                rng).fetchall()]
        return cls(period, start, end, metrics, top_categories, top_idps)

    def to_rows(self):
        """Flat rows for CSV export."""
        rows = [["Report", f"{self.period} report"], ["From", self.start], ["To", self.end], []]
        rows += [["Metric", "Value"]] + [[k, v] for k, v in self.metrics.items()] + [[]]
        rows += [["Top categories by views", "Views"]] + [[c["name"], c["views"]] for c in self.top_categories] + [[]]
        rows += [["Top IDPs by views", "Views"]] + [[p["title"], p["views"]] for p in self.top_idps]
        return rows

    # ---------- whole-platform figures (dashboard and demand) ----------
    @classmethod
    def platform_totals(cls):
        with get_connection() as conn:
            def count(sql):
                return conn.execute(sql).fetchone()[0]
            return {
                "Active interior designers": count("SELECT COUNT(*) FROM user_account "
                                                   "WHERE role = 'InteriorDesigner' AND status = 'Active'"),
                "Active customers": count("SELECT COUNT(*) FROM user_account WHERE role = 'Customer' "
                                          "AND status = 'Active'"),
                "Total IDPs": count("SELECT COUNT(*) FROM idp"),
                "Published IDPs": count("SELECT COUNT(*) FROM idp WHERE published = 1"),
                "Total favourites": count("SELECT COUNT(*) FROM favourite"),
                "Total views": count("SELECT COUNT(*) FROM view_event"),
                "Active categories": count("SELECT COUNT(*) FROM category WHERE status = 'Active'"),
            }

    @classmethod
    def top_categories_overall(cls, limit=5):
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT c.name, COUNT(DISTINCT i.id) AS idps, COALESCE(SUM(i.views), 0) AS views, "
                "(SELECT COUNT(*) FROM favourite f JOIN idp j ON j.id = f.idp_id WHERE j.category = c.name) AS saves "
                "FROM category c LEFT JOIN idp i ON i.category = c.name GROUP BY c.id "
                "ORDER BY views DESC, saves DESC, c.name LIMIT ?", (limit,)).fetchall()
        return [dict(r) for r in rows]

    @classmethod
    def top_idps_overall(cls, metric="views", limit=5):
        order = "saves DESC" if metric == "saves" else "i.views DESC"
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT i.id, i.title, i.category, i.views, "
                "(SELECT COUNT(*) FROM favourite f WHERE f.idp_id = i.id) AS saves FROM idp i "
                f"ORDER BY {order}, i.id LIMIT ?", (limit,)).fetchall()
        return [dict(r) for r in rows]
