import secrets
from typing import NamedTuple

from django.db import OperationalError, connection

SIGNAL_ERROR_CODE = 1644

ORDER_ERROR_MESSAGES = {
    "INVALID_INPUT": "Thông tin giao hàng không hợp lệ.",
    "CART_EMPTY": "Giỏ hàng đang trống.",
    "BOOK_INACTIVE": "Một số sách đã ngừng bán.",
    "OUT_OF_STOCK": "Một số sách vừa hết hàng, vui lòng kiểm tra lại giỏ.",
}


# AI-TRACE#002 | Claude Opus 5.5 | Lỗi nghiệp vụ khi đặt đơn, mang mã lỗi và câu tiếng Việt | CẤM XÓA CHÚ THÍCH NÀY
class OrderError(Exception):
    def __init__(self, code):
        self.code = code
        self.message = ORDER_ERROR_MESSAGES[code]
        super().__init__(self.message)


# AI-TRACE#003 | Claude Opus 5.5 | Kết quả đặt đơn gồm mã đơn và cờ đơn mới | CẤM XÓA CHÚ THÍCH NÀY
class PlaceOrderResult(NamedTuple):
    order_code: str
    created: bool


# AI-TRACE#004 | Claude Opus 5.5 | Sinh mã yêu cầu chống bấm đặt hàng hai lần | CẤM XÓA CHÚ THÍCH NÀY
def new_idempotency_key():
    return secrets.token_hex(16)


# AI-TRACE#005 | Claude Opus 5.5 | Gọi thủ tục sp_place_order và đổi lỗi SIGNAL thành OrderError | CẤM XÓA CHÚ THÍCH NÀY
def place_order(user, idempotency_key, shipping_name, phone_encrypted, address_encrypted):
    if connection.in_atomic_block:
        raise RuntimeError("place_order không được gọi bên trong transaction.atomic")
    params = [user.pk, idempotency_key, shipping_name, phone_encrypted, address_encrypted, None, None]
    try:
        with connection.cursor() as cursor:
            cursor.callproc("sp_place_order", params)
            while cursor.nextset():
                pass
            cursor.execute("SELECT @_sp_place_order_5, @_sp_place_order_6")
            order_code, created = cursor.fetchone()
    except OperationalError as exc:
        code = _signal_code(exc)
        if code is None:
            raise
        raise OrderError(code) from exc
    return PlaceOrderResult(order_code, bool(created))


# AI-TRACE#006 | Claude Opus 5.5 | Đọc mã lỗi nghiệp vụ từ lỗi MySQL 1644 do SIGNAL | CẤM XÓA CHÚ THÍCH NÀY
def _signal_code(exc):
    args = exc.args
    if len(args) >= 2 and args[0] == SIGNAL_ERROR_CODE and args[1] in ORDER_ERROR_MESSAGES:
        return args[1]
    return None
