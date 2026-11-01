"""Control: ManageTeamMemberController (US-13 Add team members to company page)."""
from control.update_company_info_controller import company_for
from control.validation import clean, require
from entity.team_member import TeamMember

MAX_MEMBERS = 30


class ManageTeamMemberController:
    def add(self, designer_id, name, position):
        require(name=name, position=position)
        company = company_for(designer_id)
        if len(company.team_members()) >= MAX_MEMBERS:
            raise ValueError(f"A company page can list at most {MAX_MEMBERS} team members")
        return TeamMember.add(company.id, clean(name), clean(position))

    def remove(self, designer_id, member_id):
        """Only removes members of the designer's own company."""
        return TeamMember.remove(company_for(designer_id).id, member_id)
