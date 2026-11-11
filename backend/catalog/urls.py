"""URL của app catalog. Dùng trong template: {% url 'catalog:<tên>' %}"""
from django.urls import path  # noqa: F401  (dùng khi thêm URL)

from . import views  # noqa: F401

app_name = "catalog"

urlpatterns = [
    # Ví dụ: path("", views.index, name="index"),
]
