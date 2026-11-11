"""URL của app orders. Dùng trong template: {% url 'orders:<tên>' %}"""
from django.urls import path  # noqa: F401  (dùng khi thêm URL)

from . import views  # noqa: F401

app_name = "orders"

urlpatterns = [
    # Ví dụ: path("", views.index, name="index"),
]
