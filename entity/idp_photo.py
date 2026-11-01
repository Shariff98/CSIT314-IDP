"""Entity: IDPPhoto. One uploaded photo of an IDP; one photo per IDP can be the cover."""
from entity import storage
from entity.db import get_connection, now


class IDPPhoto:
    def __init__(self, id, idp_id, filename, is_cover=0, uploaded_at=None):
        self.id = id
        self.idp_id = idp_id
        self.filename = filename
        self.is_cover = is_cover
        self.uploaded_at = uploaded_at

    @classmethod
    def create(cls, idp_id, data, extension, is_cover=False):
        filename = storage.save(data, extension)
        with get_connection() as conn:
            cur = conn.execute("INSERT INTO idp_photo (idp_id, filename, is_cover, uploaded_at) VALUES (?, ?, ?, ?)",
                               (idp_id, filename, int(is_cover), now()))
        return cls.find_by_id(cur.lastrowid)

    @classmethod
    def find_by_id(cls, photo_id):
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM idp_photo WHERE id = ?", (photo_id,)).fetchone()
        return cls(**dict(row)) if row else None

    @classmethod
    def list_for_idp(cls, idp_id):
        with get_connection() as conn:
            rows = conn.execute("SELECT * FROM idp_photo WHERE idp_id = ? ORDER BY is_cover DESC, id",
                                (idp_id,)).fetchall()
        return [cls(**dict(r)) for r in rows]

    def set_as_cover(self):
        with get_connection() as conn:
            conn.execute("UPDATE idp_photo SET is_cover = (id = ?) WHERE idp_id = ?", (self.id, self.idp_id))
        self.is_cover = 1

    def delete(self):
        storage.delete(self.filename)
        with get_connection() as conn:
            conn.execute("DELETE FROM idp_photo WHERE id = ?", (self.id,))
