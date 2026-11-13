from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.contrib.auth.hashers import check_password
from django.db import models
from django.db.models import Q

USERNAME_REGEX = r"^[A-Za-z0-9._-]{3,50}$"

username_validator = RegexValidator(
    regex=USERNAME_REGEX,
    message="Tên đăng nhập dài 3-50 ký tự, chỉ gồm chữ, số và . _ -",
)


class User(AbstractUser):

    username = models.CharField(
        "tên đăng nhập",
        max_length=50,
        unique=True,
        validators=[username_validator],
        error_messages={"unique": "Tên đăng nhập này đã được sử dụng."},
    )

    email = models.EmailField(
        "email",
        unique=True,
        error_messages={"unique": "Email này đã được sử dụng."},
    )

    phone_encrypted = models.CharField("SĐT (đã mã hóa)", max_length=512, null=True, blank=True)
    email_verified = models.BooleanField("đã xác minh email", default=False)

    def check_password(self, raw_password):
        if self.is_staff:
            return check_password(raw_password, self.password)
        return super().check_password(raw_password)

    class Meta:
        db_table = "accounts_user"
        verbose_name = "người dùng"
        verbose_name_plural = "người dùng"
        constraints = [
            models.CheckConstraint(
                condition=Q(username__regex=USERNAME_REGEX),
                name="ck_user_username_format",
            ),
            models.CheckConstraint(
                condition=Q(is_superuser=False) | Q(is_staff=True),
                name="ck_user_superuser_is_staff",
            ),
        ]

    def __str__(self):
        return self.username
