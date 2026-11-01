"""Control: UploadCompanyImageController (US-52 Upload company logo and cover image)."""
from control.update_company_info_controller import company_for
from control.validation import image_extension

FIELDS = {"logo": "logo_file", "cover": "cover_file"}


class UploadCompanyImageController:
    def upload(self, designer_id, kind, filename, data):
        if kind not in FIELDS:
            raise ValueError("Choose logo or cover image")
        extension = image_extension(filename, data)
        company = company_for(designer_id)
        company.replace_image(FIELDS[kind], data, extension)
        return company
