import re

from .covers import delete_cover, save_cover
from .models import StaffBook
from .staff_services import _call

TITLE_MAX_LENGTH = 255
DESCRIPTION_MAX_LENGTH = 5000
PRICE_MAX = 100_000_000
STOCK_MAX = 10_000

BOOK_ERROR_MESSAGES = {
    "INVALID_INPUT": "Thông tin sách không hợp lệ.",
    "INVALID_ISBN": "ISBN không hợp lệ (sai độ dài hoặc sai chữ số kiểm tra).",
    "NOT_STAFF": "Tài khoản không có quyền quản lý sách.",
    "ISBN_EXISTS": "Đã có sách khác dùng ISBN này.",
    "CATEGORY_NOT_FOUND": "Thể loại không tồn tại.",
    "BOOK_NOT_FOUND": "Không tìm thấy sách.",
    "INVALID_QUANTITY": f"Số lượng phải từ 1 đến {STOCK_MAX:,}.".replace(",", "."),
    "STOCK_LIMIT": f"Tồn kho của mỗi đầu sách tối đa {STOCK_MAX:,} cuốn.".replace(",", "."),
    "INSUFFICIENT_STOCK": "Số lượng giảm lớn hơn số sách đang có trong kho.",
    "BOOK_ACTIVE": "Sách đang hiện. Hãy ẩn sách trước khi xóa.",
    "BOOK_HAS_ORDERS": "Sách đã có trong đơn hàng nên không xóa được, chỉ có thể ẩn.",
}


class BookError(Exception):
    def __init__(self, code):
        self.code = code
        self.message = BOOK_ERROR_MESSAGES[code]
        super().__init__(self.message)


def clean_isbn(value):
    isbn = re.sub(r"[\s-]", "", str(value or "")).upper()
    if re.fullmatch(r"[0-9]{9}[0-9X]", isbn):
        total = sum((10 - i) * (10 if ch == "X" else int(ch)) for i, ch in enumerate(isbn))
        if total % 11 == 0:
            return isbn
    elif re.fullmatch(r"[0-9]{13}", isbn):
        total = sum(int(ch) * (1 if i % 2 == 0 else 3) for i, ch in enumerate(isbn))
        if total % 10 == 0:
            return isbn
    raise BookError("INVALID_ISBN")


def _int_in_range(value, low, high, code="INVALID_INPUT"):
    if isinstance(value, bool):
        raise BookError(code)
    try:
        number = int(str(value).strip())
    except (TypeError, ValueError):
        raise BookError(code) from None
    if number < low or number > high:
        raise BookError(code)
    return number


def clean_book_fields(title, author, isbn, category_id, description, price, cost_price):
    title = " ".join(str(title or "").split())
    author = " ".join(str(author or "").split())
    if not title or len(title) > TITLE_MAX_LENGTH or not author or len(author) > TITLE_MAX_LENGTH:
        raise BookError("INVALID_INPUT")
    description = (description or "").strip() or None
    if description is not None and len(description) > DESCRIPTION_MAX_LENGTH:
        raise BookError("INVALID_INPUT")
    try:
        category = _int_in_range(category_id, 1, 2**63 - 1)
    except BookError:
        raise BookError("CATEGORY_NOT_FOUND") from None
    return {
        "title": title,
        "author": author,
        "isbn": clean_isbn(isbn),
        "category_id": category,
        "description": description,
        "price": _int_in_range(price, 1, PRICE_MAX),
        "cost_price": _int_in_range(cost_price, 0, PRICE_MAX),
    }


def _book_id(value):
    try:
        return _int_in_range(value, 1, 2**63 - 1)
    except BookError:
        raise BookError("BOOK_NOT_FOUND") from None


def _call_book(procedure, params, out_index=None):
    return _call(procedure, params, out_index, messages=BOOK_ERROR_MESSAGES, error_class=BookError)


def list_books(category_id=None, author=None, title=None, is_active=None):
    books = StaffBook.objects.all()
    if category_id not in (None, ""):
        try:
            books = books.filter(category_id=_int_in_range(category_id, 1, 2**63 - 1))
        except BookError:
            return books.none()
    if author:
        books = books.filter(author__icontains=" ".join(str(author).split()))
    if title:
        books = books.filter(title__icontains=" ".join(str(title).split()))
    if is_active is not None:
        books = books.filter(is_active=bool(is_active))
    return books


def get_book(book_id):
    book = StaffBook.objects.filter(pk=_book_id(book_id)).first()
    if book is None:
        raise BookError("BOOK_NOT_FOUND")
    return book


def create_book(actor, *, title, author, isbn, category_id, description, price, cost_price, stock, cover_file=None):
    fields = clean_book_fields(title, author, isbn, category_id, description, price, cost_price)
    initial_stock = _int_in_range(stock, 0, STOCK_MAX, code="INVALID_QUANTITY")
    cover_image = save_cover(cover_file) if cover_file else None
    params = [actor.pk, fields["title"], fields["author"], fields["isbn"], fields["category_id"],
              fields["description"], cover_image, fields["price"], fields["cost_price"], initial_stock, None]
    try:
        return _call_book("sp_book_create", params, out_index=10)
    except BaseException:
        delete_cover(cover_image)
        raise


def update_book(actor, book_id, *, title, author, isbn, category_id, description, price, cost_price,
                cover_file=None, remove_cover=False):
    book_pk = _book_id(book_id)
    fields = clean_book_fields(title, author, isbn, category_id, description, price, cost_price)
    old_cover = get_book(book_pk).cover_image
    if cover_file:
        cover_image = save_cover(cover_file)
    elif remove_cover:
        cover_image = None
    else:
        cover_image = old_cover
    params = [actor.pk, book_pk, fields["title"], fields["author"], fields["isbn"], fields["category_id"],
              fields["description"], cover_image, fields["price"], fields["cost_price"]]
    try:
        _call_book("sp_book_update", params)
    except BaseException:
        if cover_image != old_cover:
            delete_cover(cover_image)
        raise
    if old_cover and old_cover != cover_image:
        delete_cover(old_cover)


def set_book_active(actor, book_id, is_active):
    _call_book("sp_book_set_active", [actor.pk, _book_id(book_id), 1 if is_active else 0])


def restock_book(actor, book_id, quantity):
    amount = _int_in_range(quantity, 1, STOCK_MAX, code="INVALID_QUANTITY")
    return _call_book("sp_book_restock", [actor.pk, _book_id(book_id), amount, None], out_index=3)


def reduce_book_stock(actor, book_id, quantity):
    amount = _int_in_range(quantity, 1, STOCK_MAX, code="INVALID_QUANTITY")
    return _call_book("sp_book_reduce_stock", [actor.pk, _book_id(book_id), amount, None], out_index=3)


def delete_book(actor, book_id):
    book_pk = _book_id(book_id)
    cover_image = get_book(book_pk).cover_image
    _call_book("sp_book_delete", [actor.pk, book_pk])
    delete_cover(cover_image)
