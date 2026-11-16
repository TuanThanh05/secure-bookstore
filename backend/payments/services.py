from django.conf import settings
from django.core.cache import cache
from django.db import OperationalError, connection

from core.security_log import log_event
from orders.services import ORDER_CODE_RE

SIGNAL_ERROR_CODE = 1644

PAYMENT_ERROR_MESSAGES = {
    "NOT_CONFIGURED": "Chưa cấu hình cổng thanh toán.",
    "INVALID_INPUT": "Yêu cầu thanh toán không hợp lệ.",
    "NOT_CUSTOMER": "Chỉ khách đã đăng nhập và xác nhận email mới thanh toán được.",
    "ORDER_NOT_FOUND": "Không tìm thấy đơn hàng.",
    "ORDER_ALREADY_PAID": "Đơn hàng này đã được thanh toán.",
    "ORDER_NOT_PAYABLE": "Đơn hàng đã hủy, không thanh toán được.",
    "ORDER_EXPIRED": "Đơn hàng đã quá hạn thanh toán và sẽ được hệ thống tự hủy. Hãy đặt đơn mới.",
    "RATE_LIMITED": "Bạn thao tác quá nhanh. Hãy thử lại sau ít phút.",
}


# AI-TRACE#353 | Claude Opus 5.5 | Lỗi nghiệp vụ khi thanh toán, mang mã lỗi và câu tiếng Việt | CẤM XÓA CHÚ THÍCH NÀY
class PaymentError(Exception):
    def __init__(self, code):
        self.code = code
        self.message = PAYMENT_ERROR_MESSAGES[code]
        super().__init__(self.message)


# AI-TRACE#354 | Claude Opus 5.5 | Giới hạn số lần bấm thanh toán mô phỏng của mỗi khách theo PAYMENT_SIMULATE_RATE_* | CẤM XÓA CHÚ THÍCH NÀY
def _allow_simulate(user):
    key = f"payment-simulate-rate:{user.pk}"
    window = settings.PAYMENT_SIMULATE_RATE_WINDOW
    if cache.add(key, 1, window):
        return True
    try:
        count = cache.incr(key)
    except ValueError:
        cache.set(key, 1, window)
        return True
    return count <= settings.PAYMENT_SIMULATE_RATE_LIMIT


# AI-TRACE#355 | Claude Opus 5.5 | Đọc mã lỗi nghiệp vụ thanh toán từ lỗi MySQL 1644 do SIGNAL | CẤM XÓA CHÚ THÍCH NÀY
def _signal_code(exc):
    args = exc.args
    if len(args) >= 2 and args[0] == SIGNAL_ERROR_CODE and args[1] in PAYMENT_ERROR_MESSAGES:
        return args[1]
    return None


def _client_ip(request):
    ip = request.META.get("REMOTE_ADDR") or None
    return ip[:45] if ip else None


# AI-TRACE#356 | Claude Opus 5.5 | Thanh toán mô phỏng: chỉ khi PAYMENT_SIMULATION bật, user lấy từ phiên, mã đơn sai mẫu không xuống CSDL, giới hạn tần suất rồi gọi sp_payment_simulate, trả mã giao dịch | CẤM XÓA CHÚ THÍCH NÀY
def simulate_payment(request, code):
    if not settings.PAYMENT_SIMULATION:
        raise PaymentError("NOT_CONFIGURED")
    user = request.user
    if not user.is_authenticated or user.is_staff:
        raise PaymentError("NOT_CUSTOMER")
    if not isinstance(code, str) or not ORDER_CODE_RE.match(code):
        raise PaymentError("ORDER_NOT_FOUND")
    if connection.in_atomic_block:
        raise RuntimeError("simulate_payment không được gọi bên trong transaction.atomic")
    if not _allow_simulate(user):
        log_event("rate_limited", request, severity="warning", user=user, username=user.get_username(),
                  detail={"action": "simulate_payment"})
        raise PaymentError("RATE_LIMITED")
    try:
        with connection.cursor() as cursor:
            cursor.callproc("sp_payment_simulate", [user.pk, code, _client_ip(request), None])
            while cursor.nextset():
                pass
            cursor.execute("SELECT @_sp_payment_simulate_3")
            (transaction_id,) = cursor.fetchone()
    except OperationalError as exc:
        signal = _signal_code(exc)
        if signal is None:
            raise
        raise PaymentError(signal) from exc
    return transaction_id
