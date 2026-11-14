from django.contrib.auth import views as auth_views
from django.urls import path

from .forms import LoginForm
from . import views

app_name = "accounts"

urlpatterns = [
    path("register/", views.register, name="register"),
    path("kiem-tra-email/", views.check_email, name="check_email"),
    path("xac-nhan-email/<str:token>/", views.verify_email, name="verify_email"),
    path("gui-lai-xac-nhan/", views.resend_verification_view, name="resend_verification"),
    path("login/", auth_views.LoginView.as_view(
            template_name="account/login.html",
            authentication_form=LoginForm,
            redirect_authenticated_user=True,),name="login"),
    path("logout/", views.SecureLogoutView.as_view(), name="logout"),
    path("profile/", views.profile, name="profile"),
]

