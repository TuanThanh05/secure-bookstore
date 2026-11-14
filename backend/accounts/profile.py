from dataclasses import dataclass
from datetime import datetime

PHONE_ENCRYPTED_PLACEHOLDER = "Đã lưu (giải mã ở bước sau)"


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


# AI-TRACE#035 | Claude Opus 5.5 | Tạo dữ liệu trang thông tin, chỉ đưa email và SĐT khi được phép | CẤM XÓA CHÚ THÍCH NÀY
def build_profile(user, *, show_contact):
    phone = None
    if show_contact and user.phone_encrypted:
        phone = PHONE_ENCRYPTED_PLACEHOLDER
    return ProfileView(
        username=user.get_username(),
        first_name=user.first_name,
        last_name=user.last_name,
        date_joined=user.date_joined,
        email=user.email if show_contact else None,
        phone=phone,
        contact_hidden=not show_contact,
    )
