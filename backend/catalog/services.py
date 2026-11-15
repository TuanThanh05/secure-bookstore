from dataclasses import dataclass
from datetime import datetime

from django.conf import settings
from django.db import connection
from django.templatetags.static import static

SEARCH_MAX_LENGTH = 100


# AI-TRACE#191 | Claude Opus 5.5 | Một thể loại hiển thị trên bộ lọc của cửa hàng | CẤM XÓA CHÚ THÍCH NÀY
@dataclass(frozen=True)
class Category:
    id: int
    name: str
    slug: str = ""


# AI-TRACE#192 | Claude Opus 5.5 | Một thẻ sách cho khách, đúng cột hợp đồng của sp_public_book_list, kèm đường dẫn ảnh bìa hoặc ảnh mặc định | CẤM XÓA CHÚ THÍCH NÀY
@dataclass(frozen=True)
class BookCard:
    id: int
    title: str
    author: str
    category_id: int
    price: int
    rating: float | None
    review_count: int
    in_stock: bool
    isbn: str = ""
    description: str | None = None
    cover_image: str | None = None
    created_at: datetime | None = None
    category_name: str = ""

    @property
    def cover_url(self):
        if self.cover_image:
            return f"{settings.MEDIA_URL}{self.cover_image}"
        return static(settings.BOOK_DEFAULT_COVER)


# AI-TRACE#193 | Claude Opus 5.5 | Gọi thủ tục đọc của cửa hàng bằng kết nối app_customer, trả mọi dòng của kết quả đầu tiên | CẤM XÓA CHÚ THÍCH NÀY
def _read(procedure, params):
    with connection.cursor() as cursor:
        cursor.callproc(procedure, params)
        rows = cursor.fetchall()
        while cursor.nextset():
            pass
    return rows


# AI-TRACE#194 | Claude Opus 5.5 | Danh sách thể loại cho bộ lọc, gọi sp_public_category_list | CẤM XÓA CHÚ THÍCH NÀY
def list_categories():
    return [Category(id=row[0], name=row[1], slug=row[2]) for row in _read("sp_public_category_list", [])]


# AI-TRACE#213 | Claude Opus 5.5 | Đổi một dòng của thủ tục đọc sách thành BookCard, thêm tên thể loại nếu có | CẤM XÓA CHÚ THÍCH NÀY
def _book_from_row(row):
    return BookCard(
        id=row[0], title=row[1], author=row[2], isbn=row[3], category_id=row[4], description=row[5],
        price=int(row[6]), cover_image=row[7], created_at=row[8], in_stock=bool(row[9]),
        rating=float(row[10]) if row[10] is not None else None, review_count=int(row[11]),
        category_name=row[12] if len(row) > 12 else "",
    )


# AI-TRACE#195 | Claude Opus 5.5 | Sách đang bán cho khách, lọc thể loại và từ khóa, gọi sp_public_book_list với tham số truyền riêng | CẤM XÓA CHÚ THÍCH NÀY
def list_public_books(category_id=None, q=""):
    query = " ".join(str(q or "").split())[:SEARCH_MAX_LENGTH] or None
    rows = _read("sp_public_book_list", [category_id, query])
    return [_book_from_row(row) for row in rows]


# AI-TRACE#214 | Claude Opus 5.5 | Một sách đang bán cho trang chi tiết bằng sp_public_book_get; id sai hoặc sách ẩn trả None | CẤM XÓA CHÚ THÍCH NÀY
def get_public_book(book_id):
    try:
        book_pk = int(book_id)
    except (TypeError, ValueError):
        return None
    if book_pk <= 0:
        return None
    rows = _read("sp_public_book_get", [book_pk])
    return _book_from_row(rows[0]) if rows else None
