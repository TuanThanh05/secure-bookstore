from django.conf import settings
from django.core.cache import cache
from django.db import OperationalError, connection

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
    "RATE_LIMITED": "Bạn thao tác quá nhanh. Hãy thử lại sau ít phút.",
}


# AI-TRACE#227 | Claude Opus 5.5 | Lỗi nghiệp vụ khi thêm vào giỏ, mang mã lỗi và câu tiếng Việt | CẤM XÓA CHÚ THÍCH NÀY
class CartError(Exception):
    def __init__(self, code):
        self.code = code
        self.message = CART_ERROR_MESSAGES[code]
        super().__init__(self.message)


# AI-TRACE#228 | Claude Opus 5.5 | Đổi id sách và số lượng nhận từ request thành số nguyên trong khoảng cho phép | CẤM XÓA CHÚ THÍCH NÀY
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


# AI-TRACE#229 | Claude Opus 5.5 | Giới hạn mỗi khách thêm vào giỏ tối đa CART_ADD_RATE_LIMIT lần trong CART_ADD_RATE_WINDOW giây | CẤM XÓA CHÚ THÍCH NÀY
def _allow_cart_add(user):
    key = f"cart-add-rate:{user.pk}"
    window = settings.CART_ADD_RATE_WINDOW
    if cache.add(key, 1, window):
        return True
    try:
        count = cache.incr(key)
    except ValueError:
        cache.set(key, 1, window)
        return True
    return count <= settings.CART_ADD_RATE_LIMIT


# AI-TRACE#230 | Claude Opus 5.5 | Thêm sách vào giỏ bằng sp_cart_add; user lấy từ phiên đăng nhập, có giới hạn tần suất; trả số cuốn của sách đó trong giỏ sau khi thêm | CẤM XÓA CHÚ THÍCH NÀY
def add_to_cart(request, book_id, quantity):
    user = request.user
    if not user.is_authenticated or user.is_staff:
        raise CartError("NOT_CUSTOMER")
    book_pk = _int_in_range(book_id, 1, 2**63 - 1, "BOOK_NOT_FOUND")
    amount = _int_in_range(quantity, 1, CART_MAX_PER_BOOK, "INVALID_INPUT")
    if connection.in_atomic_block:
        raise RuntimeError("sp_cart_add không được gọi bên trong transaction.atomic")
    if not _allow_cart_add(user):
        log_event("rate_limited", request, severity="warning", user=user, username=user.get_username(),
                  detail={"action": "cart_add", "book_id": book_pk})
        raise CartError("RATE_LIMITED")
    try:
        with connection.cursor() as cursor:
            cursor.callproc("sp_cart_add", [user.pk, book_pk, amount, None])
            while cursor.nextset():
                pass
            cursor.execute("SELECT @_sp_cart_add_3")
            new_quantity = cursor.fetchone()[0]
    except OperationalError as exc:
        args = exc.args
        if len(args) >= 2 and args[0] == SIGNAL_ERROR_CODE and args[1] in CART_ERROR_MESSAGES:
            raise CartError(args[1]) from exc
        raise
    return int(new_quantity)
