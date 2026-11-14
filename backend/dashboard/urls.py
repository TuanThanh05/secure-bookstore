from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.index, name="index"),
    path("kho-sach/", views.books, name="books"),
    path("don-hang/", views.orders, name="orders"),
    path("tai-khoan/", views.accounts, name="accounts"),
    path("nhat-ky/", views.logs, name="logs"),
    path("thong-tin/", views.profile, name="profile"),
    path("xac-thuc-lai/", views.reauth, name="reauth"),
]

