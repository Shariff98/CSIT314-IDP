"""Explicit public JSON representations; never serialize whole entity objects."""
from flask import url_for


PROJECT_FIELDS = ("id", "designer_id", "title", "description", "category", "budget",
                  "property_type", "location", "completion_date", "status", "views", "created_at")
COMPANY_FIELDS = ("id", "designer_id", "name", "registration_no", "address", "phone", "email",
                  "description", "years_experience", "budget_min", "budget_max")


def company_json(company):
    if company is None:
        return None
    result = {field: getattr(company, field) for field in COMPANY_FIELDS}
    result.update(specialisations=company.specialisation_list, service_areas=company.service_area_list,
                  services=company.service_list, certifications=company.certifications,
                  awards=company.awards,
                  logo_url=url_for("idp.uploaded", filename=company.logo_file) if company.logo_file else None,
                  cover_url=url_for("idp.uploaded", filename=company.cover_file) if company.cover_file else None)
    return result


def project_json(project):
    result = {field: getattr(project, field) for field in PROJECT_FIELDS}
    result.update(style_tags=project.style_tag_list, published=project.is_published,
                  photos=[{"id": photo.id, "url": url_for("idp.uploaded", filename=photo.filename),
                           "is_cover": bool(photo.is_cover)} for photo in project.photos()],
                  company=company_json(project.company()))
    return result
