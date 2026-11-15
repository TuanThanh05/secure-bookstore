from django.urls import path

from . import catalog_views, views

app_name = "dashboard"

urlpatterns = [
    path("", views.index, name="index"),
    path("kho-sach/", catalog_views.books, name="books"),
    path("kho-sach/them/", catalog_views.book_create, name="book_create"),
    path("kho-sach/<int:book_id>/", catalog_views.book_edit, name="book_edit"),
    path("kho-sach/<int:book_id>/nhap-kho/", catalog_views.book_restock, name="book_restock"),
    path("kho-sach/<int:book_id>/giam-kho/", catalog_views.book_reduce, name="book_reduce"),
    path("kho-sach/<int:book_id>/trang-thai/", catalog_views.book_toggle, name="book_toggle"),
    path("kho-sach/<int:book_id>/xoa/", catalog_views.book_delete, name="book_delete"),
    path("the-loai/", catalog_views.categories, name="categories"),
    path("the-loai/<int:category_id>/sua/", catalog_views.category_rename, name="category_rename"),
    path("the-loai/<int:category_id>/xoa/", catalog_views.category_delete, name="category_delete"),
    path("don-hang/", views.orders, name="orders"),
    path("tai-khoan/", views.accounts, name="accounts"),
    path("nhat-ky/", views.logs, name="logs"),
    path("thong-tin/", views.profile, name="profile"),
    path("thong-tin/lien-he/", views.profile_contact, name="profile_contact"),
    path("thong-tin/cap-nhat/", views.profile_update, name="profile_update"),
    path("xac-thuc-lai/", views.reauth, name="reauth"),
]

