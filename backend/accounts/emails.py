import hashlib
import smtplib

from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone

from core.client_ip import client_ip
from core.security_log import log_event

from .tokens import make_signup_token


def _allow_send(email, kind):
    digest = hashlib.sha256(email.lower().encode("utf-8")).hexdigest()
    return cache.add(f"accounts:email-sent:{kind}:{digest}", 1, timeout=settings.EMAIL_RESEND_INTERVAL)


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


def send_signup_link_email(request, email):
    link = request.build_absolute_uri(reverse("accounts:signup_confirm", args=[make_signup_token(email)]))
    context = {"link": link, "minutes": settings.SIGNUP_LINK_MAX_AGE // 60}
    return _send(request, "signup", None, email, "Tiếp tục đăng ký tài khoản – Secure Bookstore",
                 "account/email/signup_link.txt", context)


def send_existing_account_email(request, user):
    context = {
        "username": user.username,
        "login_link": request.build_absolute_uri(reverse("accounts:login")),
        "reset_link": request.build_absolute_uri(reverse("accounts:password_reset")),
    }
    return _send(request, "existing_notice", user, user.email, "Có người vừa đăng ký bằng email của bạn – Secure Bookstore",
                 "account/email/existing_account.txt", context)


def send_password_reset_email(request, user, link):
    context = {"username": user.username, "link": link, "minutes": settings.PASSWORD_RESET_TIMEOUT // 60}
    return _send(request, "password_reset", user, user.email, "Đặt lại mật khẩu – Secure Bookstore",
                 "account/email/password_reset.txt", context)


def send_password_changed_email(request, user, via):
    context = {
        "username": user.username,
        "via": via,
        "reset_link": request.build_absolute_uri(reverse("accounts:password_reset")),
    }
    return _send(request, "password_changed", user, user.email, "Mật khẩu của bạn vừa được thay đổi – Secure Bookstore",
                 "account/email/password_changed.txt", context)


def send_staff_password_changed_email(user):
    context = {"username": user.username, "changed_at": timezone.localtime()}
    return _send(None, "staff_password_changed", user, user.email, "Mật khẩu tài khoản quản trị vừa được thay đổi – Secure Bookstore",
                 "account/email/staff_password_changed.txt", context)


TWO_FACTOR_EMAILS = {
    "enabled": ("Xác thực 2 bước vừa được BẬT – Secure Bookstore", "account/email/two_factor_enabled.txt"),
    "disabled": ("Xác thực 2 bước vừa bị TẮT – Secure Bookstore", "account/email/two_factor_disabled.txt"),
    "recovery_used": ("Một mã dự phòng vừa được dùng để đăng nhập – Secure Bookstore",
                      "account/email/two_factor_recovery_used.txt"),
}


def send_two_factor_email(request, user, kind, remaining=None):
    subject, template = TWO_FACTOR_EMAILS[kind]
    context = {
        "username": user.username,
        "remaining": remaining,
        "at": timezone.localtime(),
        "reset_link": request.build_absolute_uri(reverse("accounts:password_reset")) if request else None,
    }
    return _send(request, f"two_factor_{kind}", user, user.email, subject, template, context)


def send_new_login_email(request, user, at):
    context = {
        "username": user.username,
        "at": timezone.localtime(at),
        "ip": client_ip(request) or "không rõ",
        "is_staff": user.is_staff,
        "reset_link": None if user.is_staff else _absolute(request, reverse("accounts:password_reset")),
    }
    return _send(request, "new_login_elsewhere", user, user.email,
                 "Tài khoản vừa đăng nhập ở nơi khác – Secure Bookstore", "account/email/new_login_elsewhere.txt", context)


def _absolute(request, path):
    try:
        return request.build_absolute_uri(path)
    except KeyError:
        return path

