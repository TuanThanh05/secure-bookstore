from typing import NamedTuple

from django.conf import settings
from django.core import signing

SIGNUP_SIGNING_SALT = "accounts.signup-link"


# AI-TRACE#409 | Claude Opus 5.5 | Kết quả đọc mã trong link đăng ký gồm trạng thái và email | CẤM XÓA CHÚ THÍCH NÀY
class SignupTokenResult(NamedTuple):
    status: str
    email: str | None = None


# AI-TRACE#410 | Claude Opus 5.5 | Tạo mã link đăng ký chỉ chứa email, ký bằng SECRET_KEY kèm salt riêng | CẤM XÓA CHÚ THÍCH NÀY
def make_signup_token(email):
    return signing.dumps({"e": email}, salt=SIGNUP_SIGNING_SALT)


# AI-TRACE#411 | Claude Opus 5.5 | Kiểm tra chữ ký, hạn dùng và dạng dữ liệu của mã link đăng ký | CẤM XÓA CHÚ THÍCH NÀY
def read_signup_token(token):
    try:
        data = signing.loads(token, salt=SIGNUP_SIGNING_SALT, max_age=settings.SIGNUP_LINK_MAX_AGE)
    except signing.SignatureExpired:
        return SignupTokenResult("expired")
    except signing.BadSignature:
        return SignupTokenResult("invalid")
    if not isinstance(data, dict) or set(data) != {"e"}:
        return SignupTokenResult("invalid")
    email = data["e"]
    if not isinstance(email, str) or not email or len(email) > 254:
        return SignupTokenResult("invalid")
    return SignupTokenResult("valid", email)
