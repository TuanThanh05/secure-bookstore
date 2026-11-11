"""URL của app dashboard. Dùng trong template: {% url 'dashboard:<tên>' %}"""
from django.urls import path  # noqa: F401  (dùng khi thêm URL)

from . import views  # noqa: F401

app_name = "dashboard"

urlpatterns = [
    # Ví dụ: path("", views.index, name="index"),
]
