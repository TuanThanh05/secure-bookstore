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


# AI-TRACE#480 | Claude Opus 5.5 | Ngữ cảnh mã hóa chuỗi bí mật gắn với user_id: chép bản mã sang dòng khác thì không giải mã được | CẤM XÓA CHÚ THÍCH NÀY
def _context(user_id):
    return f"accounts_totpdevice.secret:{user_id}"


def _secret(device):
    return decrypt_field(device.secret_encrypted, _context(device.user_id))


# AI-TRACE#481 | Claude Opus 5.5 | Nhân viên luôn phải qua bước 2; khách chỉ khi đã bật và xác nhận thiết bị | CẤM XÓA CHÚ THÍCH NÀY
def requires_two_factor(user):
    return bool(user.is_staff or user.is_superuser) or has_two_factor(user)


def has_two_factor(user):
    return TotpDevice.objects.filter(user_id=user.pk, confirmed_at__isnull=False).exists()


def confirmed_device(user):
    return TotpDevice.objects.filter(user_id=user.pk, confirmed_at__isnull=False).first()


# AI-TRACE#482 | Claude Opus 5.5 | Bắt đầu cài 2 bước: tạo chuỗi bí mật 160 bit mới (mã hóa), xóa lượt cài dở trước đó | CẤM XÓA CHÚ THÍCH NÀY
def start_setup(user):
    with transaction.atomic(using=settings.AUTH_DB_ALIAS):
        TotpDevice.objects.filter(user_id=user.pk, confirmed_at__isnull=True).delete()
        if TotpDevice.objects.filter(user_id=user.pk).exists():
            return None
        secret = pyotp.random_base32(32)
        return TotpDevice.objects.create(user_id=user.pk, secret_encrypted=encrypt_field(secret, _context(user.pk)))


# AI-TRACE#483 | Claude Opus 5.5 | Lấy lượt cài đang dở (chưa xác nhận, chưa quá hạn) của đúng người dùng | CẤM XÓA CHÚ THÍCH NÀY
def pending_setup(user):
    oldest = timezone.now() - timedelta(seconds=settings.TWO_FACTOR_SETUP_MAX_AGE)
    return TotpDevice.objects.filter(user_id=user.pk, confirmed_at__isnull=True, created_at__gte=oldest).first()


def setup_secret(device):
    return _secret(device)


def provisioning_uri(user, secret):
    return pyotp.TOTP(secret).provisioning_uri(name=user.get_username(), issuer_name=settings.TWO_FACTOR_ISSUER)


# AI-TRACE#484 | Claude Opus 5.5 | Vẽ mã QR thành SVG (phục vụ như ảnh từ URL riêng, không nhúng vào HTML) | CẤM XÓA CHÚ THÍCH NÀY
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


# AI-TRACE#485 | Claude Opus 5.5 | Kiểm mã 6 số: lệch ±30 giây, so sánh hằng thời gian, mỗi bước thời gian chỉ dùng một lần (UPDATE có điều kiện nên 2 request cùng lúc chỉ một cái qua) | CẤM XÓA CHÚ THÍCH NÀY
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


# AI-TRACE#486 | Claude Opus 5.5 | Xác nhận lượt cài: mã đúng thì bật 2 bước và tạo mã dự phòng (khách), trả mã dự phòng dạng chữ một lần | CẤM XÓA CHÚ THÍCH NÀY
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


# AI-TRACE#487 | Claude Opus 5.5 | Tạo 5 mã dự phòng mới (50 bit mỗi mã), chỉ lưu mã băm, xóa bộ cũ | CẤM XÓA CHÚ THÍCH NÀY
def replace_recovery_codes(user):
    codes = [_new_recovery_code() for _ in range(settings.RECOVERY_CODE_COUNT)]
    with transaction.atomic(using=settings.AUTH_DB_ALIAS):
        RecoveryCode.objects.filter(user_id=user.pk).delete()
        RecoveryCode.objects.bulk_create(
            RecoveryCode(user_id=user.pk, code_hash=make_password(_normalize_recovery(code))) for code in codes
        )
    return codes


# AI-TRACE#488 | Claude Opus 5.5 | Dùng một mã dự phòng: đúng thì đánh dấu đã dùng (UPDATE có điều kiện), trả số mã còn lại | CẤM XÓA CHÚ THÍCH NÀY
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


# AI-TRACE#489 | Claude Opus 5.5 | Tắt 2 bước của khách: xóa thiết bị và mọi mã dự phòng | CẤM XÓA CHÚ THÍCH NÀY
def disable(user):
    with transaction.atomic(using=settings.AUTH_DB_ALIAS):
        RecoveryCode.objects.filter(user_id=user.pk).delete()
        TotpDevice.objects.filter(user_id=user.pk).delete()


def _failure_key(user):
    return f"accounts:2fa-failures:{user.pk}"


# AI-TRACE#490 | Claude Opus 5.5 | Đếm số lần nhập sai bước 2 của mỗi tài khoản trong 1 giờ (chặn dò mã qua nhiều lượt đăng nhập) | CẤM XÓA CHÚ THÍCH NÀY
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
