"""URL của app payments. Dùng trong template: {% url 'payments:<tên>' %}"""
from django.urls import path  # noqa: F401  (dùng khi thêm URL)

from . import views  # noqa: F401

app_name = "payments"

urlpatterns = [
    # Ví dụ: path("", views.index, name="index"),
]
