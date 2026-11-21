import re
from dataclasses import dataclass
from datetime import datetime

from django.conf import settings
from django.core.cache import cache
from django.db import OperationalError, connection

from core.security_log import log_event

SIGNAL_ERROR_CODE = 1644
CONTENT_MAX_LENGTH = 2000
CONTROL_CHARS = re.compile("[\\x00-\\x08\\x0b\\x0c\\x0e-\\x1f\\x7f\\u200b-\\u200f\\u202a-\\u202e\\u2066-\\u2069]")

REVIEW_ERROR_MESSAGES = {
    "INVALID_INPUT": "Đánh giá không hợp lệ: chọn từ 1 đến 5 sao và viết nội dung từ 1 đến 2000 ký tự.",
    "NOT_CUSTOMER": "Chỉ khách đã đăng nhập và xác nhận email mới đánh giá được.",
    "BOOK_NOT_FOUND": "Không tìm thấy sách.",
    "NOT_PURCHASED": "Bạn cần mua và nhận cuốn sách này (đơn ở trạng thái Đã giao) để đánh giá.",
    "RATE_LIMITED": "Bạn gửi đánh giá quá nhiều. Hãy thử lại sau.",
}


class ReviewError(Exception):
    def __init__(self, code):
        self.code = code
        self.message = REVIEW_ERROR_MESSAGES[code]
        super().__init__(self.message)


@dataclass(frozen=True)
class MyReview:
    rating: int
    content: str
    is_visible: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True)
class PublicReview:
    display_name: str
    rating: int
    content: str
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @property
    def edited(self):
        return bool(self.created_at and self.updated_at and self.updated_at > self.created_at)


def clean_content(value):
    text = str(value or "").replace("\r\n", "\n").replace("\r", "\n")
    text = CONTROL_CHARS.sub("", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if not text or len(text) > CONTENT_MAX_LENGTH:
        raise ReviewError("INVALID_INPUT")
    return text


def _int_in_range(value, low, high, code):
    if isinstance(value, bool):
        raise ReviewError(code)
    try:
        number = int(str(value).strip())
    except (TypeError, ValueError):
        raise ReviewError(code) from None
    if number < low or number > high:
        raise ReviewError(code)
    return number


def _allow_review(user):
    key = f"review-rate:{user.pk}"
    window = settings.REVIEW_RATE_WINDOW
    if cache.add(key, 1, window):
        return True
    try:
        count = cache.incr(key)
    except ValueError:
        cache.set(key, 1, window)
        return True
    return count <= settings.REVIEW_RATE_LIMIT


def save_review(request, book_id, rating, content):
    user = request.user
    if not user.is_authenticated or user.is_staff:
        raise ReviewError("NOT_CUSTOMER")
    book_pk = _int_in_range(book_id, 1, 2**63 - 1, "BOOK_NOT_FOUND")
    stars = _int_in_range(rating, 1, 5, "INVALID_INPUT")
    text = clean_content(content)
    if connection.in_atomic_block:
        raise RuntimeError("sp_review_save không được gọi bên trong transaction.atomic")
    if not _allow_review(user):
        log_event("rate_limited", request, severity="warning", user=user, username=user.get_username(),
                  detail={"action": "review_save", "book_id": book_pk})
        raise ReviewError("RATE_LIMITED")
    try:
        with connection.cursor() as cursor:
            cursor.callproc("sp_review_save", [user.pk, book_pk, stars, text, None])
            while cursor.nextset():
                pass
            cursor.execute("SELECT @_sp_review_save_4")
            created = cursor.fetchone()[0]
    except OperationalError as exc:
        args = exc.args
        if len(args) >= 2 and args[0] == SIGNAL_ERROR_CODE and args[1] in REVIEW_ERROR_MESSAGES:
            raise ReviewError(args[1]) from exc
        raise
    return bool(created)


def get_my_review(user, book_id):
    if not user.is_authenticated or user.is_staff:
        return None
    try:
        book_pk = _int_in_range(book_id, 1, 2**63 - 1, "BOOK_NOT_FOUND")
    except ReviewError:
        return None
    with connection.cursor() as cursor:
        cursor.callproc("sp_review_get_mine", [user.pk, book_pk])
        row = cursor.fetchone()
        while cursor.nextset():
            pass
    if row is None:
        return None
    return MyReview(rating=int(row[0]), content=row[1], is_visible=bool(row[2]), created_at=row[3], updated_at=row[4])


def can_write_review(user, book_id):
    if not user.is_authenticated or user.is_staff:
        return False
    try:
        book_pk = _int_in_range(book_id, 1, 2**63 - 1, "BOOK_NOT_FOUND")
    except ReviewError:
        return False
    with connection.cursor() as cursor:
        cursor.callproc("sp_review_can_write", [user.pk, book_pk])
        row = cursor.fetchone()
        while cursor.nextset():
            pass
    return bool(row and row[0])


def list_reviews(book_id):
    try:
        book_pk = _int_in_range(book_id, 1, 2**63 - 1, "BOOK_NOT_FOUND")
    except ReviewError:
        return []
    with connection.cursor() as cursor:
        cursor.callproc("sp_review_list", [book_pk])
        rows = cursor.fetchall()
        while cursor.nextset():
            pass
    return [PublicReview(display_name=r[0], rating=int(r[1]), content=r[2], created_at=r[3], updated_at=r[4]) for r in rows]
