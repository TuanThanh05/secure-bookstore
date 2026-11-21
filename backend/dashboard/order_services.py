import datetime
from dataclasses import dataclass

from django.db import OperationalError, connections

from core.crypto import DecryptionError, decrypt_field
from orders.services import ORDER_CODE_RE, ORDER_STATUS_LABELS, OrderLine, shipping_context

SIGNAL_ERROR_CODE = 1644
STAFF_DB = "staff"
PAGE_SIZE = 20
MAX_OFFSET = 100000

ORDER_FILTERS = dict([
    ("todo", "Cần xử lý"),
    ("pending", "Chờ thanh toán"),
    ("paid", "Đã thanh toán"),
    ("confirmed", "Đã tiếp nhận"),
    ("packed", "Đã đóng gói"),
    ("shipped", "Đang giao"),
    ("delivered", "Đã giao"),
    ("cancelled", "Đã hủy"),
])

ORDER_ACTIONS = {
    "confirm": {"url": "dashboard:order_confirm", "procedure": "sp_staff_order_confirm", "from": "paid", "label": "Tiếp nhận đơn",
                "done": "Đã tiếp nhận đơn"},
    "pack": {"url": "dashboard:order_pack", "procedure": "sp_staff_order_pack", "from": "confirmed", "label": "Đóng gói xong",
             "done": "Đã chuyển đơn sang Đã đóng gói"},
    "ship": {"url": "dashboard:order_ship", "procedure": "sp_staff_order_ship", "from": "packed", "label": "Bắt đầu giao",
             "done": "Đã chuyển đơn sang Đang giao"},
    "deliver": {"url": "dashboard:order_deliver", "procedure": "sp_staff_order_deliver", "from": "shipped", "label": "Giao thành công",
                "done": "Đã chuyển đơn sang Đã giao"},
}
NEXT_ACTION = {spec["from"]: name for name, spec in ORDER_ACTIONS.items()}

ORDER_ADMIN_ERROR_MESSAGES = {
    "INVALID_INPUT": "Dữ liệu không hợp lệ.",
    "NOT_STAFF": "Tài khoản không có quyền quản lý đơn hàng.",
    "ORDER_NOT_FOUND": "Không tìm thấy đơn hàng.",
    "ORDER_WRONG_STATUS": "Đơn hàng không còn ở bước này (có thể vừa được chuyển ở nơi khác). Hãy tải lại trang.",
}


class OrderAdminError(Exception):
    def __init__(self, code):
        self.code = code
        self.message = ORDER_ADMIN_ERROR_MESSAGES[code]
        super().__init__(self.message)


def _aware(value):
    if value is None or value.tzinfo is not None:
        return value
    return value.replace(tzinfo=datetime.UTC)


class _StatusMixin:
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
    def next_action(self):
        name = NEXT_ACTION.get(self.status)
        return ORDER_ACTIONS[name] if name else None


@dataclass(frozen=True)
class StaffOrderRow(_StatusMixin):
    code: str
    username: str
    status: str
    total: int
    created_at: datetime.datetime
    expires_at: datetime.datetime
    paid_at: datetime.datetime | None
    item_count: int


@dataclass(frozen=True)
class StaffOrderDetail(_StatusMixin):
    code: str
    username: str
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
    payment_provider: str | None
    transaction_id: str | None
    lines: tuple


def _signal(exc):
    args = exc.args
    if len(args) >= 2 and args[0] == SIGNAL_ERROR_CODE and args[1] in ORDER_ADMIN_ERROR_MESSAGES:
        return OrderAdminError(args[1])
    return None


def _check_code(code):
    if not isinstance(code, str) or not ORDER_CODE_RE.match(code):
        raise OrderAdminError("ORDER_NOT_FOUND")
    return code


def _decrypt(value, field, user_id, idempotency_key):
    try:
        return decrypt_field(value, shipping_context(field, user_id, idempotency_key))
    except DecryptionError:
        return None


def list_orders(actor, status=None, page=1):
    status = status or None
    if status is not None and status not in ORDER_FILTERS:
        raise OrderAdminError("INVALID_INPUT")
    if not isinstance(page, int) or page < 1:
        page = 1
    offset = min((page - 1) * PAGE_SIZE, MAX_OFFSET)
    try:
        with connections[STAFF_DB].cursor() as cursor:
            cursor.callproc("sp_staff_order_list", [actor.pk, status, offset, PAGE_SIZE])
            total = int(cursor.fetchone()[0])
            cursor.nextset()
            rows = cursor.fetchall()
            while cursor.nextset():
                pass
    except OperationalError as exc:
        error = _signal(exc)
        if error is None:
            raise
        raise error from exc
    return total, [
        StaffOrderRow(code=r[0], username=r[1], status=r[2], total=int(r[3]), created_at=_aware(r[4]),
                      expires_at=_aware(r[5]), paid_at=_aware(r[6]), item_count=int(r[7]))
        for r in rows
    ]


def get_order(actor, code):
    code = _check_code(code)
    try:
        with connections[STAFF_DB].cursor() as cursor:
            cursor.callproc("sp_staff_order_get", [actor.pk, code])
            header = cursor.fetchone()
            cursor.nextset()
            items = cursor.fetchall()
            while cursor.nextset():
                pass
    except OperationalError as exc:
        error = _signal(exc)
        if error is None:
            raise
        raise error from exc
    if header is None:
        raise OrderAdminError("ORDER_NOT_FOUND")
    (order_code, user_id, username, status, subtotal, shipping_fee, total, shipping_name, phone_enc, address_enc,
     idempotency_key, created_at, expires_at, paid_at, cancelled_at, provider, transaction_id) = header
    return StaffOrderDetail(
        code=order_code, username=username, status=status, subtotal=int(subtotal), shipping_fee=int(shipping_fee),
        total=int(total), shipping_name=shipping_name,
        shipping_phone=_decrypt(phone_enc, "shipping_phone_encrypted", user_id, idempotency_key),
        shipping_address=_decrypt(address_enc, "shipping_address_encrypted", user_id, idempotency_key),
        created_at=_aware(created_at), expires_at=_aware(expires_at), paid_at=_aware(paid_at),
        cancelled_at=_aware(cancelled_at), payment_provider=provider, transaction_id=transaction_id,
        lines=tuple(OrderLine(book_id=int(r[0]), title=r[1], unit_price=int(r[2]), quantity=int(r[3])) for r in items),
    )


def advance_order(actor, code, action):
    spec = ORDER_ACTIONS.get(action)
    if spec is None:
        raise OrderAdminError("INVALID_INPUT")
    code = _check_code(code)
    connection = connections[STAFF_DB]
    if connection.in_atomic_block:
        raise RuntimeError(f"{spec['procedure']} không được gọi bên trong transaction.atomic")
    try:
        with connection.cursor() as cursor:
            cursor.callproc(spec["procedure"], [actor.pk, code])
            while cursor.nextset():
                pass
    except OperationalError as exc:
        error = _signal(exc)
        if error is None:
            raise
        raise error from exc
    return spec["done"]
