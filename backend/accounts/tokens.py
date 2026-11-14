from typing import NamedTuple

from django.conf import settings
from django.core import signing

EMAIL_SIGNING_SALT = "accounts.email-verification"


# AI-TRACE#008 | Claude Opus 5.5 | Kết quả đọc mã xác nhận email gồm trạng thái và dữ liệu | CẤM XÓA CHÚ THÍCH NÀY
class EmailTokenResult(NamedTuple):
    status: str
    user_id: int | None = None
    email: str | None = None


# AI-TRACE#009 | Claude Opus 5.5 | Tạo mã xác nhận email ký bằng SECRET_KEY kèm salt riêng | CẤM XÓA CHÚ THÍCH NÀY
def make_email_token(user):
    return signing.dumps({"u": user.pk, "e": user.email}, salt=EMAIL_SIGNING_SALT)


# AI-TRACE#010 | Claude Opus 5.5 | Kiểm tra chữ ký và hạn dùng của mã xác nhận email | CẤM XÓA CHÚ THÍCH NÀY
def read_email_token(token):
    try:
        data = signing.loads(token, salt=EMAIL_SIGNING_SALT, max_age=settings.EMAIL_VERIFY_MAX_AGE)
    except signing.SignatureExpired:
        return EmailTokenResult("expired")
    except signing.BadSignature:
        return EmailTokenResult("invalid")
    if not isinstance(data, dict):
        return EmailTokenResult("invalid")
    user_id, email = data.get("u"), data.get("e")
    if not isinstance(user_id, int) or not isinstance(email, str):
        return EmailTokenResult("invalid")
    return EmailTokenResult("valid", user_id, email)
