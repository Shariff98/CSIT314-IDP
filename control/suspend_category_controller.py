"""Control: SuspendCategoryController (US-60 Suspend or delete category and reassign IDPs)."""
from entity.category import Category


class SuspendCategoryController:
    def _target(self, category, reassign_to):
        """A category with projects needs another active category to move them into."""
        if category.idp_count() == 0:
            return None
        target = Category.find_by_name((reassign_to or "").strip())
        if target is None or not target.is_active() or target.id == category.id:
            raise ValueError(f"'{category.name}' has {category.idp_count()} projects: "
                             "choose another active category to move them to")
        return target

    def _load(self, category_id):
        category = Category.find_by_id(category_id)
        if category is None:
            raise LookupError("Category not found")
        return category

    def _check_not_last(self, category):
        if category.is_active() and len(Category.all_active()) == 1:
            raise ValueError("At least one category must stay active")

    def suspend(self, category_id, reassign_to=None):
        """Returns how many IDPs were moved. Suspended categories disappear from drop-downs."""
        category = self._load(category_id)
        if not category.is_active():
            raise ValueError("Category is already suspended")
        self._check_not_last(category)
        target = self._target(category, reassign_to)
        moved = category.reassign_idps(target.name) if target else 0
        category.suspend()
        return moved

    def reactivate(self, category_id):
        category = self._load(category_id)
        category.reactivate()
        return category

    def delete(self, category_id, reassign_to=None):
        """Returns how many IDPs were moved before the category was deleted."""
        category = self._load(category_id)
        self._check_not_last(category)
        target = self._target(category, reassign_to)
        moved = category.reassign_idps(target.name) if target else 0
        category.delete()
        return moved
