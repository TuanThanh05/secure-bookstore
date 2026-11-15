from django.urls import path

from . import views

app_name = "catalog"

urlpatterns = [
    path("", views.home, name="home"),
    path("gioi-thieu/", views.about, name="about"),
    path("sach/<int:book_id>/", views.book_detail, name="book_detail"),
    path("sach/<int:book_id>/danh-gia/", views.review_submit, name="review_submit"),
]
