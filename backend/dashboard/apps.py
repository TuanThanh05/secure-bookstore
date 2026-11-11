"""App dashboard: Trang quản trị cho nhân viên. Mọi truy vấn dùng kết nối 'staff' (app_staff)."""
from django.apps import AppConfig


class DashboardConfig(AppConfig):
    name = "dashboard"
    verbose_name = "Quản trị"
