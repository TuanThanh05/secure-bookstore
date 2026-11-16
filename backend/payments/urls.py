from django.urls import path

from . import views

app_name = "payments"

urlpatterns = [
    path("mo-phong/<str:code>/", views.simulate, name="simulate"),
]
