"""URL của app core. Dùng trong template: {% url 'core:<tên>' %}"""
from django.urls import path  # noqa: F401  (dùng khi thêm URL)

from . import views  # noqa: F401

app_name = "core"

urlpatterns = [
    # Ví dụ: path("", views.index, name="index"),
]
