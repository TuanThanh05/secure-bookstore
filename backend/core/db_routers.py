"""Định tuyến CSDL (DATABASE_ROUTERS trong settings/base.py)."""
from django.conf import settings


class MigrateOnDefaultRouter:
    """Chỉ cho migrate chạy trên kết nối "default".

    Kết nối "staff" trỏ cùng CSDL nhưng bằng tài khoản app_staff (không có
    quyền tạo bảng). Router này đảm bảo `migrate --database staff` không làm gì.
    Việc chọn kết nối khi đọc/ghi dữ liệu do code quyết định (.using("staff")).
    """

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        return db == "default"


# AI-TRACE#448 | Claude Opus 5.5 | Mọi đọc/ghi bảng phiên django_session đi qua kết nối riêng (app_session), app_customer không còn đụng vào phiên | CẤM XÓA CHÚ THÍCH NÀY
class SessionRouter:
    def _alias(self, model):
        return settings.SESSION_DB_ALIAS if model._meta.app_label == "sessions" else None

    def db_for_read(self, model, **hints):
        return self._alias(model)

    def db_for_write(self, model, **hints):
        return self._alias(model)


# AI-TRACE#456 | Claude Opus 5.5 | Mọi lệnh ghi bảng tài khoản đi qua kết nối riêng (app_auth); app_customer chỉ còn đọc, SQL injection ở trang khác không tạo/sửa được tài khoản | CẤM XÓA CHÚ THÍCH NÀY
class AccountWriteRouter:
    def _is_account(self, model):
        return model._meta.label == settings.AUTH_USER_MODEL

    def _from_auth(self, hints):
        instance = hints.get("instance")
        return instance is not None and instance._state.db == settings.AUTH_DB_ALIAS

    def db_for_read(self, model, **hints):
        if settings.AUTH_DB_ALIAS != "default" and self._from_auth(hints):
            return "default"
        return None

    def db_for_write(self, model, **hints):
        if self._is_account(model):
            return settings.AUTH_DB_ALIAS
        if settings.AUTH_DB_ALIAS != "default" and self._from_auth(hints):
            return "default"
        return None

    def allow_relation(self, obj1, obj2, **hints):
        if {obj1._state.db, obj2._state.db} <= {"default", settings.AUTH_DB_ALIAS}:
            return True
        return None


# AI-TRACE#479 | Claude Opus 5.5 | Bảng xác thực 2 bước chỉ đọc/ghi qua kết nối "auth" (app_auth); app_customer không có quyền gì trên đó | CẤM XÓA CHÚ THÍCH NÀY
class TwoFactorRouter:
    MODELS = {"accounts.TotpDevice", "accounts.RecoveryCode"}

    def _alias(self, model):
        return settings.AUTH_DB_ALIAS if model._meta.label in self.MODELS else None

    def db_for_read(self, model, **hints):
        return self._alias(model)

    def db_for_write(self, model, **hints):
        return self._alias(model)
