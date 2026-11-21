from django.conf import settings
from django.core.cache import cache
from django.db import OperationalError, connection

from core.client_ip import client_ip
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


class PaymentError(Exception):
    def __init__(self, code):
        self.code = code
        self.message = PAYMENT_ERROR_MESSAGES[code]
        super().__init__(self.message)


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


def _signal_code(exc):
    args = exc.args
    if len(args) >= 2 and args[0] == SIGNAL_ERROR_CODE and args[1] in PAYMENT_ERROR_MESSAGES:
        return args[1]
    return None


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
            cursor.callproc("sp_payment_simulate", [user.pk, code, client_ip(request), None])
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
