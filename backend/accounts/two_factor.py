"""Xác thực 2 bước bằng ứng dụng (TOTP, RFC 6238). Xem docs/xac-thuc-2-buoc.md."""
import hmac
import io
import secrets
import time
from datetime import timedelta

import pyotp
import segno
from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.core.cache import cache
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from core.crypto import decrypt_field, encrypt_field

from .models import RecoveryCode, TotpDevice

STEP_SECONDS = 30
CODE_DIGITS = 6
RECOVERY_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
RECOVERY_LENGTH = 10


def _context(user_id):
    return f"accounts_totpdevice.secret:{user_id}"


def _secret(device):
    return decrypt_field(device.secret_encrypted, _context(device.user_id))


def requires_two_factor(user):
    return bool(user.is_staff or user.is_superuser) or has_two_factor(user)


def has_two_factor(user):
    return TotpDevice.objects.filter(user_id=user.pk, confirmed_at__isnull=False).exists()


def confirmed_device(user):
    return TotpDevice.objects.filter(user_id=user.pk, confirmed_at__isnull=False).first()


def start_setup(user):
    with transaction.atomic(using=settings.AUTH_DB_ALIAS):
        TotpDevice.objects.filter(user_id=user.pk, confirmed_at__isnull=True).delete()
        if TotpDevice.objects.filter(user_id=user.pk).exists():
            return None
        secret = pyotp.random_base32(32)
        return TotpDevice.objects.create(user_id=user.pk, secret_encrypted=encrypt_field(secret, _context(user.pk)))


def pending_setup(user):
    oldest = timezone.now() - timedelta(seconds=settings.TWO_FACTOR_SETUP_MAX_AGE)
    return TotpDevice.objects.filter(user_id=user.pk, confirmed_at__isnull=True, created_at__gte=oldest).first()


def setup_secret(device):
    return _secret(device)


def provisioning_uri(user, secret):
    return pyotp.TOTP(secret).provisioning_uri(name=user.get_username(), issuer_name=settings.TWO_FACTOR_ISSUER)


def qr_svg(uri):
    buffer = io.BytesIO()
    segno.make(uri, error="m").save(buffer, kind="svg", scale=5, border=4, xmldecl=False)
    return buffer.getvalue()


def qr_terminal(uri):
    buffer = io.StringIO()
    segno.make(uri, error="m").terminal(out=buffer, compact=True)
    return buffer.getvalue()


def group_secret(secret):
    return " ".join(secret[i:i + 4] for i in range(0, len(secret), 4))


def _clean_code(code):
    return "".join((code or "").split())


def verify_code(device, code):
    code = _clean_code(code)
    if len(code) != CODE_DIGITS or not code.isdigit():
        return False
    totp = pyotp.TOTP(_secret(device))
    now_step = int(time.time()) // STEP_SECONDS
    window = settings.TWO_FACTOR_VALID_WINDOW
    for step in range(now_step - window, now_step + window + 1):
        if step < 0 or not hmac.compare_digest(totp.generate_otp(step), code):
            continue
        updated = (
            TotpDevice.objects.filter(pk=device.pk)
            .filter(Q(last_used_step__isnull=True) | Q(last_used_step__lt=step))
            .update(last_used_step=step)
        )
        return updated == 1
    return False


def confirm_setup(user, device, code, *, with_recovery=True):
    if not verify_code(device, code):
        return None
    with transaction.atomic(using=settings.AUTH_DB_ALIAS):
        TotpDevice.objects.filter(pk=device.pk, confirmed_at__isnull=True).update(confirmed_at=timezone.now())
        return replace_recovery_codes(user) if with_recovery else []


def _new_recovery_code():
    raw = "".join(secrets.choice(RECOVERY_ALPHABET) for _ in range(RECOVERY_LENGTH))
    return f"{raw[:5]}-{raw[5:]}"


def _normalize_recovery(code):
    return "".join(ch for ch in (code or "").upper() if ch.isalnum())


def replace_recovery_codes(user):
    codes = [_new_recovery_code() for _ in range(settings.RECOVERY_CODE_COUNT)]
    with transaction.atomic(using=settings.AUTH_DB_ALIAS):
        RecoveryCode.objects.filter(user_id=user.pk).delete()
        RecoveryCode.objects.bulk_create(
            RecoveryCode(user_id=user.pk, code_hash=make_password(_normalize_recovery(code))) for code in codes
        )
    return codes


def use_recovery_code(user, code):
    normalized = _normalize_recovery(code)
    if len(normalized) != RECOVERY_LENGTH or any(ch not in RECOVERY_ALPHABET for ch in normalized):
        return None
    for row in RecoveryCode.objects.filter(user_id=user.pk, used_at__isnull=True):
        if check_password(normalized, row.code_hash):
            if RecoveryCode.objects.filter(pk=row.pk, used_at__isnull=True).update(used_at=timezone.now()) != 1:
                return None
            return RecoveryCode.objects.filter(user_id=user.pk, used_at__isnull=True).count()
    return None


def recovery_remaining(user):
    return RecoveryCode.objects.filter(user_id=user.pk, used_at__isnull=True).count()


def looks_like_recovery_code(code):
    return len(_normalize_recovery(code)) == RECOVERY_LENGTH and not _clean_code(code).isdigit()


def disable(user):
    with transaction.atomic(using=settings.AUTH_DB_ALIAS):
        RecoveryCode.objects.filter(user_id=user.pk).delete()
        TotpDevice.objects.filter(user_id=user.pk).delete()


def _failure_key(user):
    return f"accounts:2fa-failures:{user.pk}"


def record_failure(user):
    key = _failure_key(user)
    cache.add(key, 0, timeout=settings.TWO_FACTOR_USER_FAILURE_WINDOW)
    try:
        return cache.incr(key)
    except ValueError:
        cache.set(key, 1, timeout=settings.TWO_FACTOR_USER_FAILURE_WINDOW)
        return 1


def is_blocked(user):
    return (cache.get(_failure_key(user)) or 0) >= settings.TWO_FACTOR_USER_MAX_FAILURES


def clear_failures(user):
    cache.delete(_failure_key(user))
