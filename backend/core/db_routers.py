"""Định tuyến CSDL (DATABASE_ROUTERS trong settings/base.py)."""


class MigrateOnDefaultRouter:
    """Chỉ cho migrate chạy trên kết nối "default".

    Kết nối "staff" trỏ cùng CSDL nhưng bằng tài khoản app_staff (không có
    quyền tạo bảng). Router này đảm bảo `migrate --database staff` không làm gì.
    Việc chọn kết nối khi đọc/ghi dữ liệu do code quyết định (.using("staff")).
    """

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        return db == "default"
