"""Control: UploadIDPPhotoController (US-55 Upload IDP photos and set cover image)."""
from control.ownership import own_idp
from control.validation import image_extension
from entity.idp_photo import IDPPhoto

MAX_PHOTOS = 10


class UploadIDPPhotoController:
    def upload(self, designer_id, idp_id, filename, data):
        """Adds a photo. The first photo of a project becomes its cover automatically."""
        idp = own_idp(designer_id, idp_id)
        extension = image_extension(filename, data)
        photos = idp.photos()
        if len(photos) >= MAX_PHOTOS:
            raise ValueError(f"A project can have at most {MAX_PHOTOS} photos")
        return IDPPhoto.create(idp.id, data, extension, is_cover=not photos)

    def _own_photo(self, designer_id, photo_id):
        photo = IDPPhoto.find_by_id(photo_id)
        if photo is None:
            raise LookupError("Photo not found")
        own_idp(designer_id, photo.idp_id)
        return photo

    def set_cover(self, designer_id, photo_id):
        photo = self._own_photo(designer_id, photo_id)
        photo.set_as_cover()
        return photo

    def delete_photo(self, designer_id, photo_id):
        """If the cover is deleted, the next photo becomes the cover."""
        photo = self._own_photo(designer_id, photo_id)
        photo.delete()
        remaining = IDPPhoto.list_for_idp(photo.idp_id)
        if photo.is_cover and remaining:
            remaining[0].set_as_cover()
        return photo.idp_id
