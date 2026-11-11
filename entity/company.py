"""Entity: Company. An Interior Designer's company information (one per designer)."""
from entity import storage
from entity.db import get_connection, now
from entity.team_member import TeamMember


def _split(text):
    return [part.strip() for part in (text or "").split(",") if part.strip()]


class Company:
    FIELDS = ("name", "registration_no", "address", "phone", "email", "description",
              "specialisations", "service_areas", "certifications", "awards", "years_experience",
              "budget_min", "budget_max", "services", "logo_file", "cover_file")

    def __init__(self, id, designer_id, name, registration_no, address="", phone="", email="",
                 description="", specialisations="", service_areas="", certifications="", awards="",
                 years_experience=0, budget_min=None, budget_max=None, services="", logo_file=None,
                 cover_file=None, updated_at=None):
        self.id = id
        self.designer_id = designer_id
        self.name = name
        self.registration_no = registration_no
        self.address = address
        self.phone = phone
        self.email = email
        self.description = description
        self.specialisations = specialisations
        self.service_areas = service_areas
        self.certifications = certifications
        self.awards = awards
        self.years_experience = years_experience
        self.budget_min = budget_min
        self.budget_max = budget_max
        self.services = services
        self.logo_file = logo_file
        self.cover_file = cover_file
        self.updated_at = updated_at

    @staticmethod
    def _from_row(row):
        return Company(**dict(row)) if row else None

    @classmethod
    def create(cls, designer_id, name, registration_no, address, phone, email, description):
        with get_connection() as conn:
            cur = conn.execute(
                "INSERT INTO company (designer_id, name, registration_no, address, phone, email, description, "
                "updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (designer_id, name, registration_no, address, phone, email, description, now()),
            )
        return cls.find_by_id(cur.lastrowid)

    @classmethod
    def find_by_id(cls, company_id):
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM company WHERE id = ?", (company_id,)).fetchone()
        return cls._from_row(row)

    @classmethod
    def find_by_designer(cls, designer_id):
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM company WHERE designer_id = ?", (designer_id,)).fetchone()
        return cls._from_row(row)

    @classmethod
    def search(cls, keyword="", specialisation=None, service_area=None, max_budget=None):
        """Companies customers can browse: the designer's account is active.

        Returns [(company, published_project_count)], companies with the most projects first.
        max_budget keeps companies whose minimum budget is at or below it.
        """
        where = ["a.role = 'InteriorDesigner'", "a.status = 'Active'"]
        params = []
        if keyword:
            like = f"%{keyword}%"
            where.append("(c.name LIKE ? OR c.description LIKE ? OR c.specialisations LIKE ? OR c.services LIKE ?)")
            params += [like] * 4
        for column, value in (("specialisations", specialisation), ("service_areas", service_area)):
            if value:
                where.append(f"(',' || REPLACE(c.{column}, ', ', ',') || ',') LIKE ?")
                params.append(f"%,{value},%")
        if max_budget is not None:
            where.append("(c.budget_min IS NULL OR c.budget_min <= ?)")
            params.append(max_budget)
        sql = ("SELECT c.*, (SELECT COUNT(*) FROM idp i WHERE i.designer_id = c.designer_id AND i.published = 1) "
               "AS project_count FROM company c JOIN user_account a ON a.id = c.designer_id "
               f"WHERE {' AND '.join(where)} ORDER BY project_count DESC, c.name")
        with get_connection() as conn:
            rows = conn.execute(sql, params).fetchall()
        results = []
        for row in rows:
            values = dict(row)
            count = values.pop("project_count")
            results.append((Company(**values), count))
        return results

    @classmethod
    def registration_taken(cls, registration_no, except_id=None):
        with get_connection() as conn:
            row = conn.execute("SELECT id FROM company WHERE registration_no = ? AND id IS NOT ?",
                               (registration_no, except_id)).fetchone()
        return row is not None

    def save(self, **changes):
        """Updates the given columns, e.g. company.save(name="New name")."""
        unknown = set(changes) - set(self.FIELDS)
        if unknown:
            raise KeyError(f"Unknown company fields: {', '.join(sorted(unknown))}")
        for key, value in changes.items():
            setattr(self, key, value)
        self.updated_at = now()
        columns = ", ".join(f"{key} = ?" for key in changes)
        with get_connection() as conn:
            conn.execute(f"UPDATE company SET {columns}, updated_at = ? WHERE id = ?",
                         (*changes.values(), self.updated_at, self.id))

    def replace_image(self, field, data, extension):
        """Stores a new logo or cover image and deletes the old file."""
        old = getattr(self, field)
        self.save(**{field: storage.save(data, extension)})
        storage.delete(old)

    @property
    def specialisation_list(self):
        return _split(self.specialisations)

    @property
    def service_area_list(self):
        return _split(self.service_areas)

    @property
    def service_list(self):
        return _split(self.services)

    def team_members(self):
        return TeamMember.list_for_company(self.id)
