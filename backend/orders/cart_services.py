from dataclasses import dataclass

from django.conf import settings
from django.core.cache import cache
from django.db import OperationalError, connection
from django.templatetags.static import static

from core.security_log import log_event

SIGNAL_ERROR_CODE = 1644
CART_MAX_PER_BOOK = 5

CART_ERROR_MESSAGES = {
    "INVALID_INPUT": f"Số lượng phải từ 1 đến {CART_MAX_PER_BOOK}.",
    "NOT_CUSTOMER": "Chỉ khách đã đăng nhập và xác nhận email mới thêm vào giỏ được.",
    "BOOK_NOT_FOUND": "Không tìm thấy sách.",
    "OUT_OF_STOCK": "Sách đã hết hàng.",
    "CART_LIMIT": f"Mỗi sách tối đa {CART_MAX_PER_BOOK} cuốn trong giỏ hàng.",
    "CART_FULL": "Giỏ hàng đã có 30 đầu sách. Hãy đặt hàng hoặc bớt sách trước.",
    "NOT_IN_CART": "Sách này không có trong giỏ hàng.",
    "BOOK_UNAVAILABLE": "Sách đã ngừng bán, chỉ có thể gỡ khỏi giỏ.",
    "RATE_LIMITED": "Bạn thao tác quá nhanh. Hãy thử lại sau ít phút.",
}


class CartError(Exception):
    def __init__(self, code):
        self.code = code
        self.message = CART_ERROR_MESSAGES[code]
        super().__init__(self.message)


def _int_in_range(value, low, high, code):
    if isinstance(value, bool):
        raise CartError(code)
    try:
        number = int(str(value).strip())
    except (TypeError, ValueError):
        raise CartError(code) from None
    if number < low or number > high:
        raise CartError(code)
    return number


def _allow_cart_action(user, action, limit, window):
    key = f"cart-{action}-rate:{user.pk}"
    if cache.add(key, 1, window):
        return True
    try:
        count = cache.incr(key)
    except ValueError:
        cache.set(key, 1, window)
        return True
    return count <= limit


def _guard_cart_write(request, proc, action, limit, window, book_pk):
    user = request.user
    if connection.in_atomic_block:
        raise RuntimeError(f"{proc} không được gọi bên trong transaction.atomic")
    if not _allow_cart_action(user, action, limit, window):
        log_event("rate_limited", request, severity="warning", user=user, username=user.get_username(),
                  detail={"action": f"cart_{action}", "book_id": book_pk})
        raise CartError("RATE_LIMITED")


def _call_cart_proc(proc, params, out_index=None):
    try:
        with connection.cursor() as cursor:
            cursor.callproc(proc, params)
            rows = cursor.fetchall() if cursor.description else []
            while cursor.nextset():
                pass
            if out_index is not None:
                cursor.execute(f"SELECT @_{proc}_{out_index}")
                return cursor.fetchone()[0]
            return rows
    except OperationalError as exc:
        args = exc.args
        if len(args) >= 2 and args[0] == SIGNAL_ERROR_CODE and args[1] in CART_ERROR_MESSAGES:
            raise CartError(args[1]) from exc
        raise


def _require_customer(request):
    user = request.user
    if not user.is_authenticated or user.is_staff:
        raise CartError("NOT_CUSTOMER")
    return user


def add_to_cart(request, book_id, quantity):
    user = _require_customer(request)
    book_pk = _int_in_range(book_id, 1, 2**63 - 1, "BOOK_NOT_FOUND")
    amount = _int_in_range(quantity, 1, CART_MAX_PER_BOOK, "INVALID_INPUT")
    _guard_cart_write(request, "sp_cart_add", "add", settings.CART_ADD_RATE_LIMIT, settings.CART_ADD_RATE_WINDOW, book_pk)
    new_quantity = _call_cart_proc("sp_cart_add", [user.pk, book_pk, amount, None], out_index=3)
    return int(new_quantity)


@dataclass(frozen=True)
class CartLine:
    book_id: int
    title: str
    author: str
    cover_image: str | None
    price: int
    quantity: int
    is_active: bool
    in_stock: bool

    @property
    def cover_url(self):
        if self.cover_image:
            return f"{settings.MEDIA_URL}{self.cover_image}"
        return static(settings.BOOK_DEFAULT_COVER)

    @property
    def available(self):
        return self.is_active and self.in_stock

    @property
    def status_label(self):
        if not self.is_active:
            return "Ngừng bán"
        if not self.in_stock:
            return "Hết hàng"
        return ""

    @property
    def line_total(self):
        return self.price * self.quantity

    @property
    def can_increase(self):
        return self.available and self.quantity < CART_MAX_PER_BOOK

    @property
    def can_decrease(self):
        return self.available and self.quantity > 1


@dataclass(frozen=True)
class Cart:
    lines: tuple

    @property
    def subtotal(self):
        return sum(line.line_total for line in self.lines if line.available)

    @property
    def item_count(self):
        return sum(line.quantity for line in self.lines if line.available)

    @property
    def has_unavailable(self):
        return any(not line.available for line in self.lines)


def get_cart(request):
    user = _require_customer(request)
    rows = _call_cart_proc("sp_cart_list", [user.pk])
    return Cart(lines=tuple(
        CartLine(book_id=int(r[0]), title=r[1], author=r[2], cover_image=r[3] or None, price=int(r[4]),
                 quantity=int(r[5]), is_active=bool(r[6]), in_stock=bool(r[7]))
        for r in rows
    ))


def set_cart_quantity(request, book_id, quantity):
    user = _require_customer(request)
    book_pk = _int_in_range(book_id, 1, 2**63 - 1, "NOT_IN_CART")
    amount = _int_in_range(quantity, 1, CART_MAX_PER_BOOK, "INVALID_INPUT")
    _guard_cart_write(request, "sp_cart_set_quantity", "update",
                      settings.CART_UPDATE_RATE_LIMIT, settings.CART_UPDATE_RATE_WINDOW, book_pk)
    _call_cart_proc("sp_cart_set_quantity", [user.pk, book_pk, amount])
    return amount


def remove_from_cart(request, book_id):
    user = _require_customer(request)
    book_pk = _int_in_range(book_id, 1, 2**63 - 1, "NOT_IN_CART")
    _guard_cart_write(request, "sp_cart_remove", "update",
                      settings.CART_UPDATE_RATE_LIMIT, settings.CART_UPDATE_RATE_WINDOW, book_pk)
    _call_cart_proc("sp_cart_remove", [user.pk, book_pk])
