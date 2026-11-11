"""Entity: IDP (Interior Design Project) in a designer's portfolio."""
from entity import storage
from entity.db import get_connection, now
from entity.view_event import ViewEvent

SAVES = "(SELECT COUNT(*) FROM favourite f WHERE f.idp_id = i.id)"
DESIGNER = "(SELECT c.name FROM company c WHERE c.designer_id = i.designer_id)"
STYLE_LIST = "(',' || REPLACE(i.style_tags, ', ', ',') || ',')"
SORTS = {
    "newest": "i.created_at DESC, i.id DESC",
    "oldest": "i.created_at ASC, i.id ASC",
    "views": "i.views DESC, i.id DESC",
    "saves": "saves DESC, i.id DESC",
    "budget_low": "i.budget ASC, i.id ASC",
    "budget_high": "i.budget DESC, i.id DESC",
}


class IDP:
    EDITABLE = ("title", "description", "category", "budget", "style_tags", "property_type",
                "location", "completion_date", "status", "published")

    def __init__(self, id, designer_id, title, description, category, budget, style_tags="",
                 property_type="", location="", completion_date=None, status="Current", published=1,
                 views=0, created_at=None, saves=0, designer_name=None):
        self.id = id
        self.designer_id = designer_id
        self.title = title
        self.description = description
        self.category = category
        self.budget = budget
        self.style_tags = style_tags
        self.property_type = property_type
        self.location = location
        self.completion_date = completion_date
        self.status = status
        self.published = published
        self.views = views
        self.created_at = created_at
        self.saves = saves                  # filled by queries that count favourites
        self.designer_name = designer_name  # company name, filled by find_in_budget()

    @staticmethod
    def _from_row(row):
        if not row:
            return None
        return IDP(**dict(row))

    # ---------- create / load ----------
    @classmethod
    def create(cls, designer_id, title, description, category, budget, style_tags="", property_type="",
               location="", completion_date=None, published=True, status="Current", created_at=None):
        with get_connection() as conn:
            cur = conn.execute(
                "INSERT INTO idp (designer_id, title, description, category, budget, style_tags, property_type, "
                "location, completion_date, published, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (designer_id, title, description, category, budget, style_tags, property_type, location,
                 completion_date, int(bool(published)), status, created_at or now()),
            )
        return cls.find_by_id(cur.lastrowid)

    @classmethod
    def find_by_id(cls, idp_id):
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM idp WHERE id = ?", (idp_id,)).fetchone()
        return cls._from_row(row)

    @classmethod
    def _query(cls, where, params, sort="newest", limit=None):
        sql = f"SELECT i.*, {SAVES} AS saves FROM idp i WHERE {' AND '.join(where) or '1'}"
        sql += f" ORDER BY {SORTS.get(sort, SORTS['newest'])}"
        if limit:
            sql += f" LIMIT {int(limit)}"
        with get_connection() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [cls._from_row(r) for r in rows]

    # ---------- customer side (published only) ----------
    @classmethod
    def search(cls, keyword, sort="newest"):
        """Keyword search over title, description, style tags and location."""
        return cls.filter(keyword=keyword, sort=sort)

    @classmethod
    def filter(cls, keyword="", category=None, style=None, min_budget=None, max_budget=None,
               property_type=None, location=None, sort="newest", designer_id=None, exclude_id=None, limit=None):
        where, params = ["i.published = 1"], []
        if keyword:
            like = f"%{keyword}%"
            where.append("(i.title LIKE ? OR i.description LIKE ? OR i.style_tags LIKE ? OR i.location LIKE ?)")
            params += [like, like, like, like]
        if category:
            where.append("i.category = ?")
            params.append(category)
        if style:
            where.append("(',' || REPLACE(i.style_tags, ', ', ',') || ',') LIKE ?")
            params.append(f"%,{style},%")
        if min_budget is not None:
            where.append("i.budget >= ?")
            params.append(min_budget)
        if max_budget is not None:
            where.append("i.budget <= ?")
            params.append(max_budget)
        if property_type:
            where.append("i.property_type = ?")
            params.append(property_type)
        if location:
            where.append("i.location LIKE ?")
            params.append(f"%{location}%")
        if designer_id is not None:
            where.append("i.designer_id = ?")
            params.append(designer_id)
        if exclude_id is not None:
            where.append("i.id != ?")
            params.append(exclude_id)
        return cls._query(where, params, sort, limit)

    # ---------- budget chatbot (Get budget-matched recommendations) ----------
    @classmethod
    def find_in_budget(cls, low, high, category=None, styles=None):
        """Published projects with low <= budget <= high, optionally filtered.

        category: exact category name. styles: list of style names; a project
        matches if it has at least one of them. Each result carries its save
        count and designer company name, for ranking and for the chat cards.
        """
        where = ["i.published = 1", "i.budget BETWEEN ? AND ?"]
        params = [int(low), int(high)]
        if category:
            where.append("i.category = ?")
            params.append(category)
        if styles:
            where.append("(" + " OR ".join(f"{STYLE_LIST} LIKE ?" for _ in styles) + ")")
            params.extend(f"%,{s},%" for s in styles)
        sql = (f"SELECT i.*, {SAVES} AS saves, {DESIGNER} AS designer_name FROM idp i "
               f"WHERE {' AND '.join(where)} ORDER BY i.budget, i.id")
        with get_connection() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [cls._from_row(r) for r in rows]

    @classmethod
    def find_published(cls, ids):
        """Published projects with these ids, in the order given, with saves and designer name (chat compare)."""
        ids = [int(i) for i in ids]
        if not ids:
            return []
        sql = (f"SELECT i.*, {SAVES} AS saves, {DESIGNER} AS designer_name FROM idp i "
               f"WHERE i.published = 1 AND i.id IN ({','.join('?' for _ in ids)})")
        with get_connection() as conn:
            by_id = {r["id"]: cls._from_row(r) for r in conn.execute(sql, ids).fetchall()}
        return [by_id[i] for i in ids if i in by_id]

    @staticmethod
    def known_styles():
        """Every style tag used by a published project, sorted."""
        with get_connection() as conn:
            rows = conn.execute("SELECT style_tags FROM idp WHERE published = 1").fetchall()
        return sorted({s.strip() for r in rows for s in (r["style_tags"] or "").split(",") if s.strip()})

    # ---------- designer side (own projects, drafts included) ----------
    @classmethod
    def list_for_designer(cls, designer_id, keyword="", status=None, category=None, date_from=None,
                          date_to=None, sort="newest"):
        where, params = ["i.designer_id = ?"], [designer_id]
        if keyword:
            where.append("(i.title LIKE ? OR i.description LIKE ? OR i.style_tags LIKE ?)")
            params += [f"%{keyword}%"] * 3
        if status in ("Current", "Past"):
            where.append("i.status = ?")
            params.append(status)
        elif status == "Draft":
            where.append("i.published = 0")
        elif status == "Published":
            where.append("i.published = 1")
        if category:
            where.append("i.category = ?")
            params.append(category)
        if date_from:
            where.append("date(i.created_at) >= date(?)")
            params.append(date_from)
        if date_to:
            where.append("date(i.created_at) <= date(?)")
            params.append(date_to)
        return cls._query(where, params, sort)

    @classmethod
    def interest_by_day(cls, designer_id, start, end, category=None, status=None, idp_ids=None):
        """Returns {'YYYY-MM-DD': [views, shortlists]} for the designer's IDPs between two dates."""
        where, params = ["i.designer_id = ?"], [designer_id]
        if category:
            where.append("i.category = ?")
            params.append(category)
        if status:
            where.append("i.status = ?")
            params.append(status)
        if idp_ids:
            where.append(f"i.id IN ({','.join('?' * len(idp_ids))})")
            params += list(idp_ids)
        scope = " AND ".join(where)
        result = {}
        with get_connection() as conn:
            for index, (table, column) in enumerate((("view_event", "viewed_at"), ("favourite", "saved_at"))):
                rows = conn.execute(
                    f"SELECT date(e.{column}) AS day, COUNT(*) AS n FROM {table} e JOIN idp i ON i.id = e.idp_id "
                    f"WHERE {scope} AND date(e.{column}) BETWEEN date(?) AND date(?) GROUP BY day",
                    (*params, start, end)).fetchall()
                for row in rows:
                    result.setdefault(row["day"], [0, 0])[index] = row["n"]
        return result

    # ---------- changes ----------
    def update(self, **changes):
        unknown = set(changes) - set(self.EDITABLE)
        if unknown:
            raise KeyError(f"Unknown IDP fields: {', '.join(sorted(unknown))}")
        for key, value in changes.items():
            setattr(self, key, value)
        columns = ", ".join(f"{key} = ?" for key in changes)
        with get_connection() as conn:
            conn.execute(f"UPDATE idp SET {columns} WHERE id = ?", (*changes.values(), self.id))

    def delete(self):
        """Deletes the project, its photo files, favourites and view history."""
        for photo in self.photos():
            storage.delete(photo.filename)
        with get_connection() as conn:
            conn.execute("DELETE FROM idp WHERE id = ?", (self.id,))

    def record_view(self, customer_id=None, session_key=None, viewed_at=None):
        ViewEvent.record(self.id, customer_id, session_key, viewed_at)
        self.views += 1

    def seen_in_session(self, session_key):
        return ViewEvent.seen_in_session(self.id, session_key)

    # ---------- interest statistics ----------
    def shortlist_count(self):
        with get_connection() as conn:
            return conn.execute("SELECT COUNT(*) FROM favourite WHERE idp_id = ?", (self.id,)).fetchone()[0]

    # ---------- related objects ----------
    def photos(self):
        from entity.idp_photo import IDPPhoto
        return IDPPhoto.list_for_idp(self.id)

    def cover_photo(self):
        photos = self.photos()
        return next((p for p in photos if p.is_cover), photos[0] if photos else None)

    def designer(self):
        from entity.user_account import UserAccount
        return UserAccount.find_by_id(self.designer_id)

    def company(self):
        from entity.company import Company
        return Company.find_by_designer(self.designer_id)

    @property
    def styles(self):
        return self.style_tag_list

    @property
    def style_tag_list(self):
        return [t.strip() for t in (self.style_tags or "").split(",") if t.strip()]

    @property
    def is_published(self):
        return bool(self.published)
