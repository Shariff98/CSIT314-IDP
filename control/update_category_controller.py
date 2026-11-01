"""Control: UpdateCategoryController (US-38 Update IDP category)."""
from control.create_category_controller import MAX_NAME
from control.validation import clean, require
from entity.category import Category


class UpdateCategoryController:
    def update_category(self, category_id, name, description):
        """Renaming moves all its IDPs to the new name, so no project loses its category."""
        category = Category.find_by_id(category_id)
        if category is None:
            raise LookupError("Category not found")
        require(name=name)
        name = " ".join(clean(name).split())
        if len(name) > MAX_NAME:
            raise ValueError(f"Category name must be {MAX_NAME} characters or fewer")
        other = Category.find_by_name(name)
        if other is not None and other.id != category.id:
            raise ValueError("A category with this name already exists")
        category.update(name, clean(description))
        return category
