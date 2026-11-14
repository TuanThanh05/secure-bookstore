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
    path("quen-mat-khau/", views.CustomerPasswordResetView.as_view(), name="password_reset"),
    path("quen-mat-khau/da-gui/", views.password_reset_done, name="password_reset_done"),
    path("dat-lai-mat-khau/<uidb64>/<token>/", views.CustomerPasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("login/", auth_views.LoginView.as_view(
            template_name="account/login.html",
            authentication_form=LoginForm,
            redirect_authenticated_user=True,),name="login"),
    path("logout/", views.SecureLogoutView.as_view(), name="logout"),
    path("profile/", views.profile, name="profile"),
]

