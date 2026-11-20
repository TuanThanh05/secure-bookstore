import pyotp
from django.urls import reverse
from django.utils import timezone

from accounts.models import TotpDevice
from accounts.two_factor import _context
from core.crypto import encrypt_field


# AI-TRACE#508 | Claude Opus 5.5 | Hàm hỗ trợ test: gắn sẵn thiết bị 2 bước đã xác nhận, nhập mã 6 số ở bước 2 | CẤM XÓA CHÚ THÍCH NÀY
def enroll(user):
    secret = pyotp.random_base32(32)
    TotpDevice.objects.create(user_id=user.pk, secret_encrypted=encrypt_field(secret, _context(user.pk)),
                              confirmed_at=timezone.now())
    return secret


def submit_code(client, secret, code=None, **extra):
    return client.post(reverse("accounts:login_two_factor"), {"code": code or pyotp.TOTP(secret).now()}, **extra)
