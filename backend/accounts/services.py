import hashlib
import time

from django.conf import settings
from django.core.cache import cache
from django.db import DatabaseError, IntegrityError, connection, transaction

from core.client_ip import client_ip
from core.security_log import log_event

from .emails import send_existing_account_email, send_signup_link_email
from .models import User
from .profile import decrypt_phone, encrypt_phone

SIGNUP_SESSION_KEY = "accounts:signup"


def _count_within(key, limit, window):
    if cache.add(key, 1, window):
        return True
    try:
        count = cache.incr(key)
    except ValueError:
        cache.set(key, 1, window)
        return True
    return count <= limit


def allow_signup_step(request, step):
    ip = client_ip(request) or "unknown"
    allowed = _count_within(f"accounts:signup-rate:{step}:{ip}", settings.SIGNUP_RATE_LIMIT, settings.SIGNUP_RATE_WINDOW)
    if not allowed:
        log_event("rate_limited", request, severity="warning", detail={"kind": f"signup_{step}"})
    return allowed


def _allow_signup_mail(email):
    digest = hashlib.sha256(email.lower().encode("utf-8")).hexdigest()
    return _count_within(f"accounts:signup-mail:{digest}", settings.SIGNUP_EMAIL_LIMIT, settings.SIGNUP_EMAIL_WINDOW)


def start_signup(request, email):
    existing = User.objects.filter(email__iexact=email).first()
    if not _allow_signup_mail(email):
        log_event("rate_limited", request, severity="warning", detail={"kind": "signup_email"})
        return
    if existing is None:
        send_signup_link_email(request, email)
        return
    log_event("register_existing_email", request, severity="warning")
    send_existing_account_email(request, existing)


def email_has_account(email):
    return User.objects.filter(email__iexact=email).exists()


def remember_signup_email(request, email):
    request.session.cycle_key()
    request.session[SIGNUP_SESSION_KEY] = {"email": email, "at": int(time.time())}


def pending_signup_email(request):
    data = request.session.get(SIGNUP_SESSION_KEY)
    if isinstance(data, dict):
        email, started = data.get("email"), data.get("at")
        if isinstance(email, str) and isinstance(started, int):
            age = int(time.time()) - started
            if 0 <= age <= settings.SIGNUP_SESSION_MAX_AGE:
                return email
    clear_signup(request)
    return None


def clear_signup(request):
    request.session.pop(SIGNUP_SESSION_KEY, None)


def complete_signup(request, form, email):
    if email_has_account(email):
        clear_signup(request)
        return "email_taken"
    try:
        with transaction.atomic(using=settings.AUTH_DB_ALIAS):
            user = form.save()
    except IntegrityError:
        if email_has_account(email):
            clear_signup(request)
            return "email_taken"
        if User.objects.filter(username__iexact=form.cleaned_data["username"]).exists():
            return "username_taken"
        raise
    clear_signup(request)
    log_event("register_success", request, username=user.username)
    return "created"


def _password_change_key(user):
    return f"accounts:password-change-failures:{user.pk}"


def record_password_change_failure(user):
    key = _password_change_key(user)
    cache.add(key, 0, timeout=settings.PASSWORD_CHANGE_FAILURE_WINDOW)
    try:
        return cache.incr(key)
    except ValueError:
        cache.set(key, 1, timeout=settings.PASSWORD_CHANGE_FAILURE_WINDOW)
        return 1


def clear_password_change_failures(user):
    cache.delete(_password_change_key(user))


def update_profile(request, user, data):
    changed = []
    if data["last_name"] != user.last_name:
        user.last_name = data["last_name"]
        changed.append("last_name")
    if data["first_name"] != user.first_name:
        user.first_name = data["first_name"]
        changed.append("first_name")
    if data["phone"] != (decrypt_phone(user) or ""):
        user.phone_encrypted = encrypt_phone(user, data["phone"])
        changed.append("phone_encrypted")
    if changed:
        user.save(update_fields=changed)
        log_event("profile_updated", request, user=user, username=user.get_username(), detail={"fields": changed})
    return changed


SP_DOES_NOT_EXIST = 1305


def login_ip_blocked(request):
    ip = client_ip(request)
    if not ip:
        return False
    try:
        with connection.cursor() as cursor:
            cursor.callproc("sp_login_ip_failures", [ip[:45], settings.LOGIN_IP_FAILURE_WINDOW_MINUTES])
            (failures,) = cursor.fetchone()
            while cursor.nextset():
                pass
    except DatabaseError as exc:
        if exc.args and exc.args[0] == SP_DOES_NOT_EXIST:
            return False
        raise
    return failures >= settings.LOGIN_IP_FAILURE_LIMIT

