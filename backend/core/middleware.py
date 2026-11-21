import datetime
import time

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import SESSION_KEY, logout
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth.signals import user_logged_in
from django.db import DatabaseError
from django.dispatch import receiver
from django.shortcuts import redirect
from django.utils import timezone

from core.security_log import log_event
from core.session_store import REPLACED_SESSION_KEY, STAFF_LOGIN_AT_KEY, replace_other_sessions

STAFF_TIMEOUT_MESSAGE = "Phiên làm việc quản trị đã quá 1 giờ. Vui lòng đăng nhập lại."

DB_PERMISSION_ERRORS = {
    1044: "DB_ACCESS_DENIED",
    1142: "TABLE_ACCESS_DENIED",
    1143: "COLUMN_ACCESS_DENIED",
    1227: "SPECIFIC_ACCESS_DENIED",
    1370: "PROCEDURE_ACCESS_DENIED",
}


# AI-TRACE#329 | Claude Opus 5.5 | Middleware ghi db_permission_denied (mức critical) khi MySQL từ chối câu lệnh vì thiếu quyền – dấu hiệu tấn công hoặc lỗi phân quyền; lỗi vẫn đi tiếp thành trang 500 | CẤM XÓA CHÚ THÍCH NÀY
class DbPermissionDeniedMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        if not isinstance(exception, DatabaseError) or not exception.args:
            return None
        code = exception.args[0]
        if code not in DB_PERMISSION_ERRORS:
            return None
        user = getattr(request, "user", None)
        authenticated = user is not None and user.is_authenticated
        log_event("db_permission_denied", request, severity="critical", user=user,
                  username=user.get_username() if authenticated else None,
                  detail={"mysql_code": code, "error": DB_PERMISSION_ERRORS[code]})
        return None


# AI-TRACE#449 | Claude Opus 5.5 | Ghi giờ đăng nhập của nhân viên vào phiên (phần đã ký, không sửa được từ bảng) để giới hạn thời gian tuyệt đối | CẤM XÓA CHÚ THÍCH NÀY
@receiver(user_logged_in, dispatch_uid="staff_session_login_at")
def remember_staff_login(sender, request, user, **kwargs):
    if user.is_staff and request is not None and hasattr(request, "session"):
        request.session[STAFF_LOGIN_AT_KEY] = int(time.time())


# AI-TRACE#450 | Claude Opus 5.5 | Phiên nhân viên quá 1 giờ kể từ lúc đăng nhập thì đăng xuất dù vẫn thao tác; thiếu giờ đăng nhập cũng coi là hết hạn | CẤM XÓA CHÚ THÍCH NÀY
class StaffSessionLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        if user is not None and user.is_authenticated and user.is_staff and self._expired(request):
            request.logout_reason = "absolute_timeout"
            logout(request)
            messages.warning(request, STAFF_TIMEOUT_MESSAGE)
            return redirect("accounts:login")
        return self.get_response(request)

    def _expired(self, request):
        started = request.session.get(STAFF_LOGIN_AT_KEY)
        if not isinstance(started, int):
            return True
        age = int(time.time()) - started
        return not 0 <= age < settings.STAFF_SESSION_MAX_AGE


# AI-TRACE#524 | Claude Opus 5.5 | Phiên còn ghi người dùng nhưng tài khoản đã bị khóa (hoặc không còn) thì hủy hẳn phiên, không để phiên được gia hạn rồi sống lại khi mở khóa | CẤM XÓA CHÚ THÍCH NÀY | đã viết lại bởi Claude Opus 5.5 khi thêm khóa tự động vì giữ kho
class InactiveAccountSessionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        session = getattr(request, "session", None)
        if session is not None and SESSION_KEY in session:
            user = request.user
            if not user.is_authenticated:
                log_event("logout", request, severity="warning",
                          detail={"reason": "account_inactive", "user_id": str(session.get(SESSION_KEY))[:20]})
                session.flush()
            elif getattr(user, "is_auto_locked", False):
                log_event("logout", request, severity="warning", user=user, username=user.get_username(),
                          detail={"reason": "account_auto_locked"})
                session.flush()
                request.user = AnonymousUser()
                messages.error(request, auto_lock_message(user))
        return self.get_response(request)


# AI-TRACE#539 | Claude Opus 5.5 | Câu báo tài khoản bị khóa tự động vì giữ kho, kèm giờ mở (giờ Việt Nam) | CẤM XÓA CHÚ THÍCH NÀY
def auto_lock_message(user):
    until = timezone.localtime(user.auto_locked_until).strftime("%H:%M ngày %d/%m/%Y")
    return (f"Tài khoản bị tạm khóa đến {until} vì đã hủy hoặc bỏ 3 đơn chưa thanh toán trong 24 giờ. "
            "Nếu bị khóa nhầm, hãy liên hệ cửa hàng.")


# AI-TRACE#585 | Claude Opus 5.5 | Đăng nhập xong (sau bước 2 nếu có) thì đẩy mọi phiên khác của tài khoản ra: ghi log đăng xuất lý do new_login_elsewhere và gửi thư báo chủ tài khoản | CẤM XÓA CHÚ THÍCH NÀY
@receiver(user_logged_in, dispatch_uid="single_session_per_user")
def end_other_sessions(sender, request, user, **kwargs):
    if request is None or not hasattr(request, "session"):
        return
    now = timezone.now()
    replaced = replace_other_sessions(user.pk, request.session.session_key, {"at": now.isoformat()})
    if not replaced:
        return
    log_event("logout", request, severity="warning", user=user, username=user.get_username(),
              detail={"reason": "new_login_elsewhere", "ended": replaced})
    from accounts.emails import send_new_login_email

    send_new_login_email(request, user, now)


# AI-TRACE#586 | Claude Opus 5.5 | Phiên bị đẩy ra vì tài khoản đăng nhập ở nơi khác: hủy hẳn phiên và báo cho người đang dùng (chỉ giờ đăng nhập mới, không lộ IP) | CẤM XÓA CHÚ THÍCH NÀY
class ReplacedSessionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        session = getattr(request, "session", None)
        if session is not None and REPLACED_SESSION_KEY in session:
            notice = session.get(REPLACED_SESSION_KEY)
            session.flush()
            request.user = AnonymousUser()
            messages.warning(request, replaced_session_message(notice))
        return self.get_response(request)


def replaced_session_message(notice):
    when = ""
    try:
        at = datetime.datetime.fromisoformat(notice["at"])
        when = " lúc " + timezone.localtime(at).strftime("%H:%M ngày %d/%m/%Y")
    except (KeyError, TypeError, ValueError):
        pass
    return (f"Tài khoản của bạn vừa đăng nhập ở nơi khác{when} nên phiên này đã kết thúc. "
            "Nếu không phải bạn, hãy đổi mật khẩu ngay.")

