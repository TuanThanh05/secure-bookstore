"""URL của app accounts. Dùng trong template: {% url 'accounts:<tên>' %}"""
from django.urls import path  # noqa: F401  (dùng khi thêm URL)

from . import views  # noqa: F401

app_name = "accounts"

urlpatterns = [
    # Ví dụ: path("", views.index, name="index"),
]
