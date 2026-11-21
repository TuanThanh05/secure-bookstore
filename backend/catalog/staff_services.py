import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime

from django.db import OperationalError, connections

SIGNAL_ERROR_CODE = 1644
STAFF_DB = "staff"
NAME_MAX_LENGTH = 100
SLUG_MAX_LENGTH = 120

CATEGORY_ERROR_MESSAGES = {
    "INVALID_INPUT": "Tên thể loại không hợp lệ (1–100 ký tự, phải có chữ hoặc số).",
    "NOT_STAFF": "Tài khoản không có quyền quản lý thể loại.",
    "CATEGORY_EXISTS": "Đã có thể loại trùng tên này.",
    "CATEGORY_NOT_FOUND": "Không tìm thấy thể loại.",
    "CATEGORY_IN_USE": "Thể loại còn sách nên không xóa được. Hãy chuyển sách sang thể loại khác trước.",
}


@dataclass(frozen=True)
class StaffCategory:
    id: int
    name: str
    slug: str
    book_count: int
    active_book_count: int
    created_at: datetime

    @property
    def can_delete(self):
        return self.book_count == 0


class CategoryError(Exception):
    def __init__(self, code):
        self.code = code
        self.message = CATEGORY_ERROR_MESSAGES[code]
        super().__init__(self.message)


def clean_name(name):
    cleaned = " ".join((name or "").split())
    if not cleaned or len(cleaned) > NAME_MAX_LENGTH:
        raise CategoryError("INVALID_INPUT")
    return cleaned


def make_slug(name):
    text = name.replace("đ", "d").replace("Đ", "D")
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii").lower()
    slug = re.sub(r"[^a-z0-9]+", "-", text).strip("-")[:SLUG_MAX_LENGTH].strip("-")
    if not slug:
        raise CategoryError("INVALID_INPUT")
    return slug


def _call(procedure, params, out_index=None, messages=CATEGORY_ERROR_MESSAGES, error_class=CategoryError):
    connection = connections[STAFF_DB]
    if connection.in_atomic_block:
        raise RuntimeError(f"{procedure} không được gọi bên trong transaction.atomic")
    try:
        with connection.cursor() as cursor:
            cursor.callproc(procedure, params)
            while cursor.nextset():
                pass
            if out_index is None:
                return None
            cursor.execute(f"SELECT @_{procedure}_{out_index}")
            return cursor.fetchone()[0]
    except OperationalError as exc:
        args = exc.args
        if len(args) >= 2 and args[0] == SIGNAL_ERROR_CODE and args[1] in messages:
            raise error_class(args[1]) from exc
        raise


def _category_id(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        raise CategoryError("CATEGORY_NOT_FOUND") from None


def list_categories():
    connection = connections[STAFF_DB]
    if connection.in_atomic_block:
        raise RuntimeError("sp_category_list không được gọi bên trong transaction.atomic")
    with connection.cursor() as cursor:
        cursor.callproc("sp_category_list", [])
        rows = cursor.fetchall()
        while cursor.nextset():
            pass
    return [StaffCategory(row[0], row[1], row[2], int(row[3]), int(row[4]), row[5]) for row in rows]


def create_category(actor, name):
    cleaned = clean_name(name)
    return _call("sp_category_create", [actor.pk, cleaned, make_slug(cleaned), None], out_index=3)


def rename_category(actor, category_id, name):
    cleaned = clean_name(name)
    _call("sp_category_rename", [actor.pk, _category_id(category_id), cleaned, make_slug(cleaned)])


def delete_category(actor, category_id):
    _call("sp_category_delete", [actor.pk, _category_id(category_id)])
