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
