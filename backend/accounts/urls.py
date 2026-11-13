from django.contrib.auth import views as auth_views
from django.urls import path

from .forms import LoginForm
from . import views

app_name = "accounts"

urlpatterns = [
    path("register/", views.register, name="register"),
    path("login/", auth_views.LoginView.as_view(
            template_name="account/login.html",
            authentication_form=LoginForm,
            redirect_authenticated_user=True,),name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
]

