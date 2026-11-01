"""Control: ViewCompanyInfoController (US-02 View company information)."""
from entity.company import Company


class ViewCompanyInfoController:
    def view(self, designer_id):
        """The designer's own company record, or None if they haven't created one yet."""
        return Company.find_by_designer(designer_id)
