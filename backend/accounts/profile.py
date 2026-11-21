from dataclasses import dataclass
from datetime import datetime

from core.crypto import DecryptionError, decrypt_field, encrypt_field

PHONE_UNREADABLE = "Không đọc được (dữ liệu hỏng hoặc sai khóa)"


@dataclass(frozen=True)
class ProfileView:
    username: str
    first_name: str
    last_name: str
    date_joined: datetime
    email: str | None
    phone: str | None
    contact_hidden: bool


def phone_context(user):
    return f"accounts_user.phone_encrypted:{user.pk}"


def encrypt_phone(user, phone):
    if not phone:
        return None
    return encrypt_field(phone, phone_context(user))


def decrypt_phone(user):
    if not user.phone_encrypted:
        return None
    try:
        return decrypt_field(user.phone_encrypted, phone_context(user))
    except DecryptionError:
        return PHONE_UNREADABLE


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
