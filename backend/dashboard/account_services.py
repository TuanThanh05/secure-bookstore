from dataclasses import dataclass
from datetime import UTC, datetime
from types import SimpleNamespace

from django.conf import settings
from django.db import OperationalError, connections

from accounts.profile import phone_context
from core.crypto import DecryptionError, decrypt_field

SIGNAL_ERROR_CODE = 1644
STAFF_DB = "staff"
REASON_MIN_LENGTH = 5
REASON_MAX_LENGTH = 255
KEYWORD_MAX_LENGTH = 150

ACCOUNT_STATUSES = ("active", "locked", "temp_locked", "unverified")
ACCOUNT_STATUS_LABELS = {
    "active": "Hoạt động",
    "locked": "Đã khóa",
    "temp_locked": "Tạm khóa",
    "unverified": "Chưa xác nhận email",
}

ACCOUNT_ERROR_MESSAGES = {
    "INVALID_INPUT": "Dữ liệu không hợp lệ.",
    "NOT_STAFF": "Tài khoản không có quyền quản lý tài khoản.",
    "ACCOUNT_NOT_FOUND": "Không tìm thấy tài khoản khách hàng.",
    "ALREADY_LOCKED": "Tài khoản này đã bị khóa từ trước.",
    "NOT_LOCKED": "Tài khoản này đang không bị khóa.",
}


# AI-TRACE#297 | Claude Opus 5.5 | Lỗi nghiệp vụ khi quản lý tài khoản khách, mang mã lỗi và câu tiếng Việt | CẤM XÓA CHÚ THÍCH NÀY
class AccountError(Exception):
    def __init__(self, code):
        self.code = code
        self.message = ACCOUNT_ERROR_MESSAGES[code]
        super().__init__(self.message)


# AI-TRACE#298 | Claude Opus 5.5 | Che bớt email (giữ ký tự đầu, cuối của phần trước @ và tên miền) và SĐT (giữ 3 số đầu, 3 số cuối) | CẤM XÓA CHÚ THÍCH NÀY
def mask_email(email):
    local, sep, domain = (email or "").partition("@")
    if not sep or not local:
        return "***"
    if len(local) <= 2:
        return f"{local[0]}***@{domain}"
    return f"{local[0]}***{local[-1]}@{domain}"


def mask_phone(phone):
    if not phone:
        return ""
    if len(phone) <= 6:
        return "***"
    return f"{phone[:3]}****{phone[-3:]}"


# AI-TRACE#299 | Claude Opus 5.5 | Một tài khoản khách cho trang admin: trạng thái, email/SĐT bản đầy đủ và bản che, ngày tạo, lần đăng nhập cuối | CẤM XÓA CHÚ THÍCH NÀY
@dataclass(frozen=True)
class StaffAccount:
    id: int
    username: str
    email: str
    phone: str | None
    status: str
    date_joined: datetime
    last_login: datetime | None

    @property
    def status_label(self):
        return ACCOUNT_STATUS_LABELS.get(self.status, self.status)

    @property
    def is_locked(self):
        return self.status == "locked"

    @property
    def masked_email(self):
        return mask_email(self.email)

    @property
    def masked_phone(self):
        return mask_phone(self.phone)


def _aware(value):
    if value is None or value.tzinfo is not None:
        return value
    return value.replace(tzinfo=UTC)


def _decrypt_phone(user_id, value):
    if not value:
        return None
    try:
        return decrypt_field(value, phone_context(SimpleNamespace(pk=user_id)))
    except DecryptionError:
        return None


def _row_to_account(row):
    user_id, username, email, phone_encrypted, status, date_joined, last_login = row
    return StaffAccount(id=int(user_id), username=username, email=email or "",
                        phone=_decrypt_phone(int(user_id), phone_encrypted), status=status,
                        date_joined=_aware(date_joined), last_login=_aware(last_login))


def _axes_limits():
    return int(settings.AXES_FAILURE_LIMIT), max(1, int(settings.AXES_COOLOFF_TIME.total_seconds() // 60))


def _positive_id(value):
    if isinstance(value, bool):
        raise AccountError("ACCOUNT_NOT_FOUND")
    try:
        number = int(value)
    except (TypeError, ValueError):
        raise AccountError("ACCOUNT_NOT_FOUND") from None
    if number < 1 or number > 2**63 - 1:
        raise AccountError("ACCOUNT_NOT_FOUND")
    return number


# AI-TRACE#300 | Claude Opus 5.5 | Gọi thủ tục quản lý tài khoản qua kết nối staff, đổi lỗi SIGNAL thành AccountError, lỗi khác (thiếu quyền...) để nguyên | CẤM XÓA CHÚ THÍCH NÀY
def _call(procedure, params, fetch=False):
    connection = connections[STAFF_DB]
    if not fetch and connection.in_atomic_block:
        raise RuntimeError(f"{procedure} không được gọi bên trong transaction.atomic")
    try:
        with connection.cursor() as cursor:
            cursor.callproc(procedure, params)
            rows = cursor.fetchall() if fetch and cursor.description else []
            while cursor.nextset():
                pass
            return rows
    except OperationalError as exc:
        args = exc.args
        if len(args) >= 2 and args[0] == SIGNAL_ERROR_CODE and args[1] in ACCOUNT_ERROR_MESSAGES:
            raise AccountError(args[1]) from exc
        raise


# AI-TRACE#301 | Claude Opus 5.5 | Danh sách tài khoản khách qua sp_staff_account_list, lọc trạng thái và username (kiểm tra trước khi xuống CSDL) | CẤM XÓA CHÚ THÍCH NÀY
def list_accounts(actor, status=None, keyword=None):
    if status not in (None, *ACCOUNT_STATUSES):
        raise AccountError("INVALID_INPUT")
    keyword = (keyword or "").strip() or None
    if keyword is not None and len(keyword) > KEYWORD_MAX_LENGTH:
        raise AccountError("INVALID_INPUT")
    limit, cooloff = _axes_limits()
    rows = _call("sp_staff_account_list", [actor.pk, status, keyword, limit, cooloff], fetch=True)
    return [_row_to_account(row) for row in rows]


# AI-TRACE#302 | Claude Opus 5.5 | Một tài khoản khách qua sp_staff_account_get cho trang xác nhận khóa/mở khóa | CẤM XÓA CHÚ THÍCH NÀY
def get_account(actor, user_id):
    limit, cooloff = _axes_limits()
    rows = _call("sp_staff_account_get", [actor.pk, _positive_id(user_id), limit, cooloff], fetch=True)
    if not rows:
        raise AccountError("ACCOUNT_NOT_FOUND")
    return _row_to_account(rows[0])


def _clean_reason(reason):
    text = " ".join(str(reason or "").split())
    if not REASON_MIN_LENGTH <= len(text) <= REASON_MAX_LENGTH:
        raise AccountError("INVALID_INPUT")
    return text


# AI-TRACE#303 | Claude Opus 5.5 | Khóa và mở khóa tài khoản khách qua sp_staff_account_lock/unlock, kèm lý do ghi vào nhật ký | CẤM XÓA CHÚ THÍCH NÀY
def lock_account(actor, user_id, reason):
    _call("sp_staff_account_lock", [actor.pk, _positive_id(user_id), _clean_reason(reason)])


def unlock_account(actor, user_id, reason):
    _call("sp_staff_account_unlock", [actor.pk, _positive_id(user_id), _clean_reason(reason)])
