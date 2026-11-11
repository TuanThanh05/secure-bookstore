"""App accounts: Đăng ký, đăng nhập, khóa tài khoản, 2FA, quên mật khẩu, hồ sơ. Chứa Custom User."""
from django.apps import AppConfig


class AccountsConfig(AppConfig):
    name = "accounts"
    verbose_name = "Tài khoản"
