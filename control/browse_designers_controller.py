"""Control: BrowseDesignersController.

Lets a customer find a design company to open its company page (US-53). Only companies
whose designer account is active are listed, so suspended designers disappear at once.
"""
from control.ownership import STYLES
from control.validation import clean, to_int
from entity.company import Company
from entity.idp import IDP


class BrowseDesignersController:
    def browse(self, keyword="", specialisation=None, service_area=None, max_budget=None):
        """Returns [{"company", "projects", "preview"}]; preview is the cover photo of the company's
        most viewed published project (or None), so each card has a real picture."""
        budget = to_int(max_budget, "Budget", minimum=0, allow_blank=True) if max_budget is not None else None
        results = []
        for company, count in Company.search(clean(keyword), clean(specialisation) or None,
                                             clean(service_area) or None, budget):
            top = IDP.filter(designer_id=company.designer_id, sort="views", limit=1)
            results.append({"company": company, "projects": count,
                            "preview": top[0].cover_photo() if top else None})
        return results

    def options(self):
        """Values for the filter drop-downs, taken from the companies that are listed."""
        companies = [company for company, _ in Company.search()]
        specialisations = {s for c in companies for s in c.specialisation_list}
        areas = {a for c in companies for a in c.service_area_list}
        return {"specialisations": sorted(specialisations.union(STYLES)), "service_areas": sorted(areas)}
