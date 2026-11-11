"""App core: Dùng chung: validator mật khẩu, mã hóa AES, ghi log bảo mật, middleware, mixin phân quyền."""
from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = "core"
    verbose_name = "Lõi dùng chung"
