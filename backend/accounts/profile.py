from dataclasses import dataclass
from datetime import datetime

from core.crypto import DecryptionError, decrypt_field, encrypt_field

PHONE_UNREADABLE = "Không đọc được (dữ liệu hỏng hoặc sai khóa)"


# AI-TRACE#034 | Claude Opus 5.5 | Dữ liệu trang thông tin tài khoản, email và SĐT có thể bị giấu | CẤM XÓA CHÚ THÍCH NÀY
@dataclass(frozen=True)
class ProfileView:
    username: str
    first_name: str
    last_name: str
    date_joined: datetime
    email: str | None
    phone: str | None
    contact_hidden: bool


# AI-TRACE#068 | Claude Opus 5.5 | Ngữ cảnh mã hóa SĐT gắn với id người dùng, chống tráo bản mã giữa các dòng | CẤM XÓA CHÚ THÍCH NÀY
def phone_context(user):
    return f"accounts_user.phone_encrypted:{user.pk}"


# AI-TRACE#069 | Claude Opus 5.5 | Mã hóa SĐT trước khi lưu, chuỗi rỗng thì lưu NULL | CẤM XÓA CHÚ THÍCH NÀY
def encrypt_phone(user, phone):
    if not phone:
        return None
    return encrypt_field(phone, phone_context(user))


# AI-TRACE#070 | Claude Opus 5.5 | Giải mã SĐT để hiển thị, lỗi giải mã thì trả câu báo thay vì làm hỏng trang | CẤM XÓA CHÚ THÍCH NÀY
def decrypt_phone(user):
    if not user.phone_encrypted:
        return None
    try:
        return decrypt_field(user.phone_encrypted, phone_context(user))
    except DecryptionError:
        return PHONE_UNREADABLE


# AI-TRACE#035 | Claude Opus 5.5 | Tạo dữ liệu trang thông tin, chỉ đưa email và SĐT khi được phép | CẤM XÓA CHÚ THÍCH NÀY
def build_profile(user, *, show_contact):
    return ProfileView(
        username=user.get_username(),
        first_name=user.first_name,
        last_name=user.last_name,
        date_joined=user.date_joined,
        email=user.email if show_contact else None,
        phone=decrypt_phone(user) if show_contact else None,
        contact_hidden=not show_contact,
    )
