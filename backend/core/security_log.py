import logging

from axes.signals import user_locked_out
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.db import DatabaseError
from django.dispatch import receiver

from .models import SecurityEvent

logger = logging.getLogger("security")

LEVELS = {"info": logging.INFO, "warning": logging.WARNING, "critical": logging.CRITICAL}


def _client_info(request):
    if request is None:
        return "unknown", None, None, None
    meta = request.META
    user_agent = (meta.get("HTTP_USER_AGENT") or "")[:255] or None
    return meta.get("REMOTE_ADDR") or "unknown", user_agent, request.method, request.path[:255]


def log_event(event_type, request=None, *, severity="info", user=None, username=None, ip_address=None, detail=None):
    ip, user_agent, method, path = _client_info(request)
    ip = ip_address or ip
    user_id = user.pk if user is not None and user.is_authenticated else None
    username = (username or "")[:150] or None

    logger.log(
        LEVELS.get(severity, logging.INFO),
        "event=%s ip=%s user_id=%s username=%r path=%r",
        event_type, ip, user_id, username, path,
    )
    try:
        SecurityEvent.objects.create(
            event_type=event_type,
            severity=severity,
            user_id=user_id,
            username_attempted=username,
            ip_address=ip,
            user_agent=user_agent,
            method=method,
            path=path,
            detail=detail,
        )
    except DatabaseError:
        logger.exception("Không ghi được core_securityevent cho sự kiện %s", event_type)


@receiver(user_logged_in, dispatch_uid="security_log_login_success")
def on_login_success(sender, request, user, **kwargs):
    log_event("login_success", request, user=user, username=user.get_username())


@receiver(user_login_failed, dispatch_uid="security_log_login_failed")
def on_login_failed(sender, credentials, request=None, **kwargs):
    log_event("login_failed", request, severity="warning", username=credentials.get("username"))


@receiver(user_logged_out, dispatch_uid="security_log_logout")
def on_logout(sender, request, user=None, **kwargs):
    log_event("logout", request, user=user, username=user.get_username() if user else None)


@receiver(user_locked_out, dispatch_uid="security_log_account_locked")
def on_account_locked(sender, request, username=None, ip_address=None, **kwargs):
    log_event("account_locked", request, severity="critical", username=username, ip_address=ip_address)