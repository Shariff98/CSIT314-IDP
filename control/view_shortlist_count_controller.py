"""Control: ViewShortlistCountController (US-46 View IDP shortlist count)."""
from entity.idp import IDP


class ViewShortlistCountController:
    def shortlist_counts(self, designer_id):
        """Each of the designer's projects with how many customers saved it to favourites.
        Only the designer's own projects are included, most shortlisted first."""
        rows = [{"idp": idp, "shortlists": idp.shortlist_count()} for idp in IDP.list_for_designer(designer_id)]
        rows.sort(key=lambda r: (-r["shortlists"], r["idp"].title))
        return {"rows": rows, "total": sum(r["shortlists"] for r in rows)}

    def shortlist_count(self, designer_id, idp_id):
        idp = IDP.find_by_id(idp_id)
        if idp is None or idp.designer_id != designer_id:
            return None
        return idp.shortlist_count()
