import hashlib
import smtplib

from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse

from core.security_log import log_event

from .tokens import make_email_token


# AI-TRACE#016 | Claude Opus 5.5 | Giới hạn mỗi địa chỉ email chỉ nhận một thư mỗi loại trong một khoảng thời gian | CẤM XÓA CHÚ THÍCH NÀY
def _allow_send(email, kind):
    digest = hashlib.sha256(email.lower().encode("utf-8")).hexdigest()
    return cache.add(f"accounts:email-sent:{kind}:{digest}", 1, timeout=settings.EMAIL_RESEND_INTERVAL)


# AI-TRACE#017 | Claude Opus 5.5 | Gửi một thư văn bản thuần, lỗi SMTP chỉ ghi log không lộ ra ngoài | CẤM XÓA CHÚ THÍCH NÀY
def _send(request, kind, user_or_none, email, subject, template, context):
    if not _allow_send(email, kind):
        log_event("rate_limited", request, username=getattr(user_or_none, "username", None), detail={"kind": kind})
        return False
    body = render_to_string(template, context)
    try:
        send_mail(subject, body, None, [email])
    except (smtplib.SMTPException, OSError):
        log_event("email_send_failed", request, severity="warning", username=getattr(user_or_none, "username", None), detail={"kind": kind})
        return False
    log_event("email_sent", request, username=getattr(user_or_none, "username", None), detail={"kind": kind})
    return True


# AI-TRACE#018 | Claude Opus 5.5 | Gửi thư chứa link xác nhận email có hạn dùng | CẤM XÓA CHÚ THÍCH NÀY
def send_verification_email(request, user):
    link = request.build_absolute_uri(reverse("accounts:verify_email", args=[make_email_token(user)]))
    context = {"username": user.username, "link": link, "minutes": settings.EMAIL_VERIFY_MAX_AGE // 60}
    return _send(request, "verify", user, user.email, "Xác nhận email – Secure Bookstore",
                 "account/email/verify_email.txt", context)


# AI-TRACE#019 | Claude Opus 5.5 | Báo cho chủ email biết có người dùng email này để đăng ký lại | CẤM XÓA CHÚ THÍCH NÀY
def send_existing_account_email(request, user):
    context = {
        "username": user.username,
        "login_link": request.build_absolute_uri(reverse("accounts:login")),
    }
    return _send(request, "existing_notice", user, user.email, "Có người vừa đăng ký bằng email của bạn – Secure Bookstore",
                 "account/email/existing_account.txt", context)


# AI-TRACE#047 | Claude Opus 5.5 | Gửi thư chứa link đặt lại mật khẩu có hạn dùng | CẤM XÓA CHÚ THÍCH NÀY
def send_password_reset_email(request, user, link):
    context = {"username": user.username, "link": link, "minutes": settings.PASSWORD_RESET_TIMEOUT // 60}
    return _send(request, "password_reset", user, user.email, "Đặt lại mật khẩu – Secure Bookstore",
                 "account/email/password_reset.txt", context)


# AI-TRACE#048 | Claude Opus 5.5 | Báo cho chủ tài khoản biết mật khẩu vừa được đổi | CẤM XÓA CHÚ THÍCH NÀY
def send_password_changed_email(request, user, via):
    context = {
        "username": user.username,
        "via": via,
        "reset_link": request.build_absolute_uri(reverse("accounts:password_reset")),
    }
    return _send(request, "password_changed", user, user.email, "Mật khẩu của bạn vừa được thay đổi – Secure Bookstore",
                 "account/email/password_changed.txt", context)
