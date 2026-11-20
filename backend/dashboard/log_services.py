import json
from dataclasses import dataclass, field
from datetime import UTC, datetime

from django.db import OperationalError, connections

SIGNAL_ERROR_CODE = 1644
STAFF_DB = "staff"
PAGE_SIZE = 50
MAX_OFFSET = 100000

EVENT_LABELS = dict([
    ("login_success", "Đăng nhập thành công"),
    ("login_failed", "Đăng nhập sai"),
    ("account_locked", "Khóa tạm do sai nhiều lần"),
    ("logout", "Đăng xuất"),
    ("password_changed", "Đổi mật khẩu"),
    ("password_reset_requested", "Yêu cầu quên mật khẩu"),
    ("otp_failed", "Sai mã xác thực 2 bước"),
    ("access_denied", "Không đủ quyền"),
    ("idor_attempt", "Nghi truy cập dữ liệu người khác"),
    ("db_permission_denied", "MySQL từ chối quyền"),
    ("payment_signature_invalid", "Thanh toán sai chữ ký"),
    ("payment_replay", "Thanh toán dùng lại giao dịch"),
    ("payment_amount_mismatch", "Thanh toán sai số tiền"),
    ("upload_rejected", "Upload bị từ chối"),
    ("rate_limited", "Vượt giới hạn tần suất"),
    ("csrf_failed", "Lỗi CSRF"),
    ("invalid_input", "Đầu vào bất thường"),
    ("register_success", "Đăng ký"),
    ("register_existing_email", "Đăng ký trùng email"),
    ("register_link_invalid", "Link đăng ký không hợp lệ"),
    ("captcha_failed", "CAPTCHA không đạt"),
    ("email_sent", "Đã gửi email"),
    ("email_send_failed", "Gửi email lỗi"),
    ("sensitive_data_viewed", "Xem dữ liệu nhạy cảm"),
    ("profile_updated", "Sửa hồ sơ"),
    ("two_factor_enabled", "Bật xác thực 2 bước"),
    ("two_factor_disabled", "Tắt xác thực 2 bước"),
    ("two_factor_recovery_used", "Dùng mã dự phòng"),
])
SEVERITY_LABELS = {"info": "Thông tin", "warning": "Cảnh báo", "critical": "Nghiêm trọng"}
TABLE_LABELS = {
    "accounts_user": "Tài khoản",
    "catalog_book": "Sách",
    "catalog_category": "Thể loại",
    "orders_order": "Đơn hàng",
}
ACTION_LABELS = {"INSERT": "Thêm", "UPDATE": "Sửa", "DELETE": "Xóa"}
SOURCE_LABELS = {"customer": "Khách", "system": "Hệ thống", "payment": "Thanh toán", "staff": "Quản trị",
                 "other": "Khác"}

LOG_ERROR_MESSAGES = {
    "INVALID_INPUT": "Bộ lọc không hợp lệ.",
    "NOT_STAFF": "Tài khoản không có quyền xem nhật ký.",
}


# AI-TRACE#330 | Claude Opus 5.5 | Lỗi khi đọc nhật ký hệ thống, mang mã lỗi và câu tiếng Việt | CẤM XÓA CHÚ THÍCH NÀY
class LogError(Exception):
    def __init__(self, code):
        self.code = code
        self.message = LOG_ERROR_MESSAGES[code]
        super().__init__(self.message)


def _aware(value):
    if value is None or value.tzinfo is not None:
        return value
    return value.replace(tzinfo=UTC)


def _json(value):
    if value is None or isinstance(value, dict):
        return value or {}
    try:
        data = json.loads(value)
    except (TypeError, ValueError):
        return {"raw": str(value)[:500]}
    return data if isinstance(data, dict) else {"value": data}


def _text(value):
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)[:300]
    return "—" if value is None else str(value)[:300]


# AI-TRACE#331 | Claude Opus 5.5 | Một dòng nhật ký bảo mật cho template: nhãn tiếng Việt, mức độ, người dùng, IP, đường dẫn, chi tiết dạng cặp khóa–giá trị | CẤM XÓA CHÚ THÍCH NÀY
@dataclass(frozen=True)
class SecurityEventRow:
    id: int
    created_at: datetime
    event_type: str
    severity: str
    user_id: int | None
    username: str | None
    username_attempted: str | None
    ip_address: str
    method: str | None
    path: str | None
    user_agent: str | None
    detail: dict = field(default_factory=dict)

    @property
    def label(self):
        return EVENT_LABELS.get(self.event_type, self.event_type)

    @property
    def severity_label(self):
        return SEVERITY_LABELS.get(self.severity, self.severity)

    @property
    def who(self):
        return self.username or self.username_attempted or ""

    @property
    def detail_items(self):
        return [(key, _text(value)) for key, value in self.detail.items()]


# AI-TRACE#332 | Claude Opus 5.5 | Một dòng nhật ký thay đổi dữ liệu: bảng, hành động, danh sách thay đổi cũ → mới, nguồn (khách/hệ thống/quản trị), người thực hiện | CẤM XÓA CHÚ THÍCH NÀY
@dataclass(frozen=True)
class AuditRow:
    id: int
    created_at: datetime
    table_name: str
    record_id: int
    action: str
    old_value: dict
    new_value: dict
    db_user: str
    app_user_id: int | None
    username: str | None

    @property
    def table_label(self):
        return TABLE_LABELS.get(self.table_name, self.table_name)

    @property
    def action_label(self):
        return ACTION_LABELS.get(self.action, self.action)

    @property
    def source_label(self):
        source = self.new_value.get("source")
        if source:
            return SOURCE_LABELS.get(source, source)
        return "Quản trị" if self.db_user.startswith("app_staff@") else ""

    @property
    def changes(self):
        keys = [k for k in dict.fromkeys([*self.old_value, *self.new_value]) if k not in ("source", "code")]
        return [(key, _text(self.old_value.get(key)) if key in self.old_value else "",
                 _text(self.new_value.get(key))) for key in keys]

    @property
    def record_label(self):
        code = self.new_value.get("code") or self.old_value.get("code")
        return f"#{self.record_id} · {str(code)[:8]}" if code else f"#{self.record_id}"


def _page_args(page):
    page = max(1, int(page or 1))
    offset = min((page - 1) * PAGE_SIZE, MAX_OFFSET)
    return page, offset


# AI-TRACE#333 | Claude Opus 5.5 | Gọi thủ tục đọc nhật ký qua kết nối staff: bộ kết quả 1 là tổng số dòng, bộ 2 là trang dữ liệu; đổi lỗi SIGNAL thành LogError | CẤM XÓA CHÚ THÍCH NÀY
def _read(procedure, params):
    try:
        with connections[STAFF_DB].cursor() as cursor:
            cursor.callproc(procedure, params)
            total = int(cursor.fetchone()[0])
            cursor.nextset()
            rows = cursor.fetchall()
            while cursor.nextset():
                pass
    except OperationalError as exc:
        args = exc.args
        if len(args) >= 2 and args[0] == SIGNAL_ERROR_CODE and args[1] in LOG_ERROR_MESSAGES:
            raise LogError(args[1]) from exc
        raise
    return total, rows


def _naive_utc(value):
    return value.astimezone(UTC).replace(tzinfo=None) if value is not None else None


# AI-TRACE#334 | Claude Opus 5.5 | Đọc một trang nhật ký bảo mật qua sp_staff_security_events, thời gian lọc đổi về UTC | CẤM XÓA CHÚ THÍCH NÀY
def list_security_events(actor, *, event_type=None, severity=None, start=None, end=None, keyword=None, page=1):
    page, offset = _page_args(page)
    total, rows = _read("sp_staff_security_events", [
        actor.pk, event_type or None, severity or None, _naive_utc(start), _naive_utc(end),
        (keyword or "").strip() or None, offset, PAGE_SIZE])
    events = [SecurityEventRow(id=int(r[0]), created_at=_aware(r[1]), event_type=r[2], severity=r[3],
                               user_id=r[4], username=r[5], username_attempted=r[6], ip_address=r[7],
                               method=r[8], path=r[9], user_agent=r[10], detail=_json(r[11])) for r in rows]
    return events, total, page


# AI-TRACE#335 | Claude Opus 5.5 | Đọc một trang nhật ký thay đổi dữ liệu qua sp_staff_audit_log | CẤM XÓA CHÚ THÍCH NÀY
def list_audit_log(actor, *, table=None, action=None, start=None, end=None, record_id=None, page=1):
    page, offset = _page_args(page)
    total, rows = _read("sp_staff_audit_log", [
        actor.pk, table or None, action or None, _naive_utc(start), _naive_utc(end), record_id or None,
        offset, PAGE_SIZE])
    entries = [AuditRow(id=int(r[0]), created_at=_aware(r[1]), table_name=r[2], record_id=int(r[3]), action=r[4],
                        old_value=_json(r[5]), new_value=_json(r[6]), db_user=r[7] or "", app_user_id=r[8],
                        username=r[9]) for r in rows]
    return entries, total, page
