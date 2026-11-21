from django.contrib.auth.hashers import check_password, is_password_usable
from django.core.exceptions import ValidationError

from .models import PasswordHistory


class PasswordHistoryValidator:
    def __init__(self, history_count=5):
        self.history_count = history_count

    def _recent_hashes(self, user):
        hashes = list(
            PasswordHistory.objects.filter(user_id=user.pk)
            .order_by("-id")
            .values_list("password_hash", flat=True)[: self.history_count]
        )
        current = user.password
        if current and is_password_usable(current) and current not in hashes:
            hashes = [current] + hashes[: self.history_count - 1]
        return hashes

    def validate(self, password, user=None):
        if user is None or user.pk is None or not password:
            return
        for encoded in self._recent_hashes(user):
            if is_password_usable(encoded) and check_password(password, encoded):
                raise ValidationError(
                    "Mật khẩu này trùng với một trong %(count)d mật khẩu gần nhất của bạn. Hãy chọn mật khẩu khác.",
                    code="password_reused",
                    params={"count": self.history_count},
                )

    def get_help_text(self):
        return f"Mật khẩu không được trùng với {self.history_count} mật khẩu gần nhất (tính cả mật khẩu đang dùng)."


class MaximumLengthValidator:
    def __init__(self, max_length=64):
        self.max_length = max_length

    def validate(self, password, user=None):
        if password is not None and len(password) > self.max_length:
            raise ValidationError(
                "Mật khẩu dài tối đa %(max_length)d ký tự.",
                code="password_too_long",
                params={"max_length": self.max_length},
            )

    def get_help_text(self):
        return f"Mật khẩu dài tối đa {self.max_length} ký tự."
