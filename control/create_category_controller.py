"""Control: CreateCategoryController (US-49 Create IDP category)."""
from control.validation import clean, require
from entity.category import Category

MAX_NAME = 40


class CreateCategoryController:
    def create_category(self, name, description):
        require(name=name)
        name = " ".join(clean(name).split())
        if len(name) > MAX_NAME:
            raise ValueError(f"Category name must be {MAX_NAME} characters or fewer")
        if Category.find_by_name(name) is not None:
            raise ValueError("A category with this name already exists")
        return Category.create(name, clean(description))
