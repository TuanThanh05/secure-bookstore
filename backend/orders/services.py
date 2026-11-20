import datetime
import re
import secrets
from dataclasses import dataclass
from typing import NamedTuple

from django.conf import settings
from django.core.cache import cache
from django.db import OperationalError, connection

from core.crypto import DecryptionError, decrypt_field, encrypt_field
from core.security_log import log_event

SIGNAL_ERROR_CODE = 1644

SHIPPING_FEE = 30000
IDEMPOTENCY_KEY_RE = re.compile(r"^[0-9a-f]{32}$")
ORDER_CODE_RE = IDEMPOTENCY_KEY_RE

ORDER_ERROR_MESSAGES = {
    "INVALID_INPUT": "Thông tin giao hàng không hợp lệ.",
    "NOT_CUSTOMER": "Chỉ khách đã đăng nhập và xác nhận email mới đặt hàng được.",
    "PENDING_EXISTS": "Bạn đang có một đơn chờ thanh toán. Hãy thanh toán hoặc đợi đơn đó hết hạn trước khi đặt đơn mới.",
    "CART_EMPTY": "Giỏ hàng đang trống.",
    "BOOK_INACTIVE": "Một số sách đã ngừng bán. Hãy gỡ chúng khỏi giỏ trước khi đặt hàng.",
    "OUT_OF_STOCK": "Một số sách vừa hết hàng hoặc không đủ số lượng, vui lòng kiểm tra lại giỏ.",
    "ORDER_NOT_FOUND": "Không tìm thấy đơn hàng.",
    "ORDER_NOT_CANCELLABLE": "Đơn hàng này không còn hủy được (đã thanh toán hoặc đã hủy).",
    "RATE_LIMITED": "Bạn thao tác quá nhanh. Hãy thử lại sau ít phút.",
    "ORDER_TOO_LARGE": f"Mỗi đơn tối đa {settings.ORDER_MAX_ITEMS} cuốn. Hãy bớt sách trong giỏ rồi đặt lại.",
    "ACCOUNT_LOCKED": "Tài khoản đang bị tạm khóa vì đã hủy hoặc bỏ nhiều đơn chưa thanh toán.",
}

ORDER_GROUPS = {
    "active": "Đang xử lý",
    "history": "Lịch sử",
}
ORDER_LIST_PAGE_SIZE = 10
ORDER_LIST_MAX_OFFSET = 100000

ORDER_STATUS_LABELS = {
    "pending": "Chờ thanh toán",
    "paid": "Đã thanh toán",
    "confirmed": "Đã tiếp nhận",
    "packed": "Đã đóng gói",
    "shipped": "Đang giao",
    "delivered": "Đã giao",
    "cancelled": "Đã hủy",
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


# AI-TRACE#266 | Claude Opus 5.5 | Ngữ cảnh mã hóa SĐT/địa chỉ giao hàng gắn với người đặt và mã chống trùng của đơn, bản mã chép sang đơn khác sẽ không giải mã được | CẤM XÓA CHÚ THÍCH NÀY
def shipping_context(field, user_pk, idempotency_key):
    return f"orders_order.{field}:{user_pk}:{idempotency_key}"


# AI-TRACE#267 | Claude Opus 5.5 | Giới hạn số lần đặt hàng của mỗi khách theo ORDER_PLACE_RATE_* | CẤM XÓA CHÚ THÍCH NÀY
def _allow_place_order(user):
    key = f"order-place-rate:{user.pk}"
    window = settings.ORDER_PLACE_RATE_WINDOW
    if cache.add(key, 1, window):
        return True
    try:
        count = cache.incr(key)
    except ValueError:
        cache.set(key, 1, window)
        return True
    return count <= settings.ORDER_PLACE_RATE_LIMIT


# AI-TRACE#005 | Claude Opus 5.5 | Đặt đơn: user lấy từ phiên, mã hóa SĐT/địa chỉ, giới hạn tần suất rồi gọi sp_place_order và đổi lỗi SIGNAL thành OrderError | CẤM XÓA CHÚ THÍCH NÀY | đã viết lại bởi Claude Opus 5.5 khi truyền thời gian giữ kho và số cuốn tối đa
def place_order(request, idempotency_key, shipping_name, phone, address):
    user = request.user
    if not user.is_authenticated or user.is_staff:
        raise OrderError("NOT_CUSTOMER")
    if not isinstance(idempotency_key, str) or not IDEMPOTENCY_KEY_RE.match(idempotency_key):
        raise OrderError("INVALID_INPUT")
    if connection.in_atomic_block:
        raise RuntimeError("place_order không được gọi bên trong transaction.atomic")
    if not _allow_place_order(user):
        log_event("rate_limited", request, severity="warning", user=user, username=user.get_username(),
                  detail={"action": "place_order"})
        raise OrderError("RATE_LIMITED")
    phone_encrypted = encrypt_field(phone, shipping_context("shipping_phone_encrypted", user.pk, idempotency_key))
    address_encrypted = encrypt_field(address, shipping_context("shipping_address_encrypted", user.pk, idempotency_key))
    params = [user.pk, idempotency_key, shipping_name, phone_encrypted, address_encrypted,
              settings.ORDER_HOLD_MINUTES, settings.ORDER_MAX_ITEMS, None, None]
    try:
        with connection.cursor() as cursor:
            cursor.callproc("sp_place_order", params)
            while cursor.nextset():
                pass
            cursor.execute("SELECT @_sp_place_order_7, @_sp_place_order_8")
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


# AI-TRACE#268 | Claude Opus 5.5 | Một sách trong đơn: tên và giá chụp lúc đặt | CẤM XÓA CHÚ THÍCH NÀY
@dataclass(frozen=True)
class OrderLine:
    book_id: int
    title: str
    unit_price: int
    quantity: int

    @property
    def line_total(self):
        return self.unit_price * self.quantity


# AI-TRACE#269 | Claude Opus 5.5 | Đơn hàng cho template: trạng thái, tiền, thông tin giao hàng đã giải mã, hạn thanh toán; không chứa mã chống trùng | CẤM XÓA CHÚ THÍCH NÀY
@dataclass(frozen=True)
class Order:
    code: str
    status: str
    subtotal: int
    shipping_fee: int
    total: int
    shipping_name: str
    shipping_phone: str | None
    shipping_address: str | None
    created_at: datetime.datetime
    expires_at: datetime.datetime
    paid_at: datetime.datetime | None
    cancelled_at: datetime.datetime | None
    lines: tuple

    @property
    def status_label(self):
        return ORDER_STATUS_LABELS.get(self.status, self.status)

    @property
    def awaiting_payment(self):
        return self.status == "pending" and self.expires_at > datetime.datetime.now(datetime.UTC)

    @property
    def expired(self):
        return self.status == "pending" and not self.awaiting_payment

    @property
    def can_cancel(self):
        return self.status == "pending"


def _aware(value):
    if value is None or value.tzinfo is not None:
        return value
    return value.replace(tzinfo=datetime.UTC)


def _decrypt_shipping(value, field, user_pk, idempotency_key):
    try:
        return decrypt_field(value, shipping_context(field, user_pk, idempotency_key))
    except DecryptionError:
        return None


# AI-TRACE#270 | Claude Opus 5.5 | Đọc một đơn của chính khách bằng sp_order_get; mã đơn sai mẫu bị chặn trước khi xuống CSDL, đơn người khác báo không tìm thấy | CẤM XÓA CHÚ THÍCH NÀY
def get_order(request, code):
    user = request.user
    if not user.is_authenticated or user.is_staff:
        raise OrderError("NOT_CUSTOMER")
    if not isinstance(code, str) or not ORDER_CODE_RE.match(code):
        raise OrderError("ORDER_NOT_FOUND")
    try:
        with connection.cursor() as cursor:
            cursor.callproc("sp_order_get", [user.pk, code])
            header = cursor.fetchone()
            cursor.nextset()
            items = cursor.fetchall()
            while cursor.nextset():
                pass
    except OperationalError as exc:
        signal = _signal_code(exc)
        if signal is None:
            raise
        raise OrderError(signal) from exc
    if header is None:
        raise OrderError("ORDER_NOT_FOUND")
    (order_code, status, subtotal, shipping_fee, total, shipping_name, phone_enc, address_enc,
     idempotency_key, created_at, expires_at, paid_at, cancelled_at) = header
    return Order(
        code=order_code, status=status, subtotal=int(subtotal), shipping_fee=int(shipping_fee), total=int(total),
        shipping_name=shipping_name,
        shipping_phone=_decrypt_shipping(phone_enc, "shipping_phone_encrypted", user.pk, idempotency_key),
        shipping_address=_decrypt_shipping(address_enc, "shipping_address_encrypted", user.pk, idempotency_key),
        created_at=_aware(created_at), expires_at=_aware(expires_at),
        paid_at=_aware(paid_at), cancelled_at=_aware(cancelled_at),
        lines=tuple(OrderLine(book_id=int(r[0]), title=r[1], unit_price=int(r[2]), quantity=int(r[3])) for r in items),
    )


# AI-TRACE#286 | Claude Opus 5.5 | Giới hạn số lần bấm hủy đơn của mỗi khách theo ORDER_CANCEL_RATE_* | CẤM XÓA CHÚ THÍCH NÀY
def _allow_cancel_order(user):
    key = f"order-cancel-rate:{user.pk}"
    window = settings.ORDER_CANCEL_RATE_WINDOW
    if cache.add(key, 1, window):
        return True
    try:
        count = cache.incr(key)
    except ValueError:
        cache.set(key, 1, window)
        return True
    return count <= settings.ORDER_CANCEL_RATE_LIMIT


# AI-TRACE#287 | Claude Opus 5.5 | Khách hủy đơn chờ thanh toán của chính mình bằng sp_order_cancel; mã đơn sai mẫu không xuống CSDL, kho được cộng lại trong thủ tục | CẤM XÓA CHÚ THÍCH NÀY | đã viết lại bởi Claude Opus 5.5 khi trả về cờ tài khoản vừa bị khóa vì giữ kho
def cancel_order(request, code):
    user = request.user
    if not user.is_authenticated or user.is_staff:
        raise OrderError("NOT_CUSTOMER")
    if not isinstance(code, str) or not ORDER_CODE_RE.match(code):
        raise OrderError("ORDER_NOT_FOUND")
    if connection.in_atomic_block:
        raise RuntimeError("cancel_order không được gọi bên trong transaction.atomic")
    if not _allow_cancel_order(user):
        log_event("rate_limited", request, severity="warning", user=user, username=user.get_username(),
                  detail={"action": "cancel_order"})
        raise OrderError("RATE_LIMITED")
    try:
        with connection.cursor() as cursor:
            cursor.callproc("sp_order_cancel", [user.pk, code, None])
            while cursor.nextset():
                pass
            cursor.execute("SELECT @_sp_order_cancel_2")
            (locked,) = cursor.fetchone()
    except OperationalError as exc:
        signal = _signal_code(exc)
        if signal is None:
            raise
        raise OrderError(signal) from exc
    return bool(locked)


# AI-TRACE#365 | Claude Opus 5.5 | Một dòng trong danh sách đơn của khách: mã, trạng thái, tổng tiền, thời gian, số cuốn và tên cuốn đầu; không chứa thông tin giao hàng | CẤM XÓA CHÚ THÍCH NÀY
@dataclass(frozen=True)
class OrderSummary:
    code: str
    status: str
    total: int
    created_at: datetime.datetime
    expires_at: datetime.datetime
    paid_at: datetime.datetime | None
    cancelled_at: datetime.datetime | None
    item_count: int
    line_count: int
    first_title: str

    @property
    def expired(self):
        return self.status == "pending" and self.expires_at <= datetime.datetime.now(datetime.UTC)

    @property
    def status_key(self):
        return "expired" if self.expired else self.status

    @property
    def status_label(self):
        return "Quá hạn thanh toán" if self.expired else ORDER_STATUS_LABELS.get(self.status, self.status)

    @property
    def other_titles(self):
        return max(self.line_count - 1, 0)


# AI-TRACE#366 | Claude Opus 5.5 | Đọc một trang đơn của chính khách theo nhóm Đang xử lý/Lịch sử bằng sp_order_list_mine; nhóm sai bị chặn trước khi xuống CSDL, trả tổng số và danh sách | CẤM XÓA CHÚ THÍCH NÀY
def list_my_orders(request, group, page=1):
    user = request.user
    if not user.is_authenticated or user.is_staff:
        raise OrderError("NOT_CUSTOMER")
    if group not in ORDER_GROUPS:
        raise OrderError("INVALID_INPUT")
    if not isinstance(page, int) or page < 1:
        page = 1
    offset = min((page - 1) * ORDER_LIST_PAGE_SIZE, ORDER_LIST_MAX_OFFSET)
    try:
        with connection.cursor() as cursor:
            cursor.callproc("sp_order_list_mine", [user.pk, group, offset, ORDER_LIST_PAGE_SIZE])
            total = int(cursor.fetchone()[0])
            cursor.nextset()
            rows = cursor.fetchall()
            while cursor.nextset():
                pass
    except OperationalError as exc:
        signal = _signal_code(exc)
        if signal is None:
            raise
        raise OrderError(signal) from exc
    orders = [
        OrderSummary(code=r[0], status=r[1], total=int(r[2]), created_at=_aware(r[3]), expires_at=_aware(r[4]),
                     paid_at=_aware(r[5]), cancelled_at=_aware(r[6]), item_count=int(r[7]), line_count=int(r[8]),
                     first_title=r[9] or "")
        for r in rows
    ]
    return total, orders
