"""URL của app catalog. Dùng trong template: {% url 'catalog:<tên>' %}"""
from django.urls import path

from . import views

app_name = "catalog"

urlpatterns = [
    path("", views.home, name="home"),
    path("gioi-thieu/", views.about, name="about"),
]
