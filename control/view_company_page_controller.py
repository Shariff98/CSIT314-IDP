"""Control: ViewCompanyPageController (US-53 View interior designer company page,
also used by US-15 Preview public company page)."""
from entity.company import Company
from entity.idp import IDP
from entity.user_account import UserAccount


class ViewCompanyPageController:
    def view(self, designer_id):
        """Returns what a customer sees: the company, its team and its published projects.
        Returns None when there is no company or the designer's account is suspended."""
        designer = UserAccount.find_by_id(designer_id)
        if designer is None or designer.role != "InteriorDesigner" or designer.is_suspended():
            return None
        company = Company.find_by_designer(designer_id)
        if company is None:
            return None
        return {"designer": designer, "company": company, "team": company.team_members(),
                "projects": IDP.filter(designer_id=designer_id)}
