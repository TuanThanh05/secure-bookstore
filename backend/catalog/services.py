"""Logic nghiệp vụ của app catalog.

ĐỌC dữ liệu: qua view MySQL (v_public_books, v_public_categories) bằng model
managed = False. GHI dữ liệu: gọi stored procedure, ví dụ:

    from django.db import connection   # kết nối "default" = app_customer
    with connection.cursor() as cur:
        cur.callproc("sp_ten_thu_tuc", [tham_so_1, tham_so_2])   # tham số truyền riêng, KHÔNG nối chuỗi

TẠM THỜI (trước khi có view v_public_books): list_categories() và
list_public_books() trả dữ liệu giả, CÙNG TÊN THUỘC TÍNH với model sau này,
để template không phải sửa khi chuyển sang dữ liệu thật.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Category:
    id: int
    name: str


@dataclass(frozen=True)
class BookCard:
    """Dữ liệu một thẻ sách (khớp cột của view v_public_books sẽ viết)."""

    id: int
    title: str
    author: str
    category_id: int
    price: int                 # VND, số nguyên
    rating: float | None       # trung bình sao 0–5, None khi chưa có đánh giá
    review_count: int
    in_stock: bool
    cover_url: str = ""        # URL ảnh trong MEDIA; rỗng → template hiện ảnh giữ chỗ


_CATEGORIES = (
    Category(1, "Văn học"),
    Category(2, "Triết học"),
    Category(3, "Khoa học"),
    Category(4, "Kinh tế"),
    Category(5, "Nghệ thuật"),
)

_BOOKS = (
    BookCard(1, "Nhà Giả Kim", "Paulo Coelho", 1, 290000, 4.8, 310, True),
    BookCard(2, "Suy Tưởng", "Marcus Aurelius", 2, 340000, 4.9, 114, True),
    BookCard(3, "Tư Duy Nhanh Và Chậm", "Daniel Kahneman", 3, 310000, 4.4, 215, True),
    BookCard(4, "Lược Sử Loài Người", "Yuval Noah Harari", 3, 450000, 4.7, 180, True),
    BookCard(5, "Nhà Lãnh Đạo Không Chức Danh", "Robin Sharma", 4, 220000, 4.1, 92, True),
    BookCard(6, "Kiến Trúc Hiện Đại Và Bản Sắc Á Đông", "Kenzo Tanaka", 5, 420000, 4.6, 37, False),
    BookCard(7, "Thơ Và Cuộc Đời", "Rilke & Baudelaire", 1, 195000, 4.0, 29, True),
    BookCard(8, "Kinh Tế Học Hài Hước", "Steven D. Levitt", 4, 185000, None, 0, True),
)


def list_categories():
    """Các thể loại hiển thị trên bộ lọc."""
    return list(_CATEGORIES)


def list_public_books(category_id=None, q=""):
    """Sách đang bán, lọc theo thể loại và từ khóa (tên sách hoặc tác giả).

    Đầu vào đã được view kiểm tra (category_id là số nguyên hợp lệ hoặc None,
    q đã làm sạch). Khi có MySQL: thay bằng truy vấn ORM trên view
    v_public_books, ví dụ .filter(title__icontains=q) – ORM tự truyền tham số,
    không nối chuỗi SQL.
    """
    books = _BOOKS
    if category_id is not None:
        books = [b for b in books if b.category_id == category_id]
    if q:
        needle = q.casefold()
        books = [b for b in books if needle in b.title.casefold() or needle in b.author.casefold()]
    return list(books)
