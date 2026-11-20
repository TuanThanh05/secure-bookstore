from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("register/", views.register, name="register"),
    path("kiem-tra-email/", views.check_email, name="check_email"),
    path("dang-ky/xac-nhan/<str:token>/", views.signup_confirm, name="signup_confirm"),
    path("dang-ky/hoan-tat/", views.signup_complete, name="signup_complete"),
    path("quen-mat-khau/", views.CustomerPasswordResetView.as_view(), name="password_reset"),
    path("quen-mat-khau/da-gui/", views.password_reset_done, name="password_reset_done"),
    path("dat-lai-mat-khau/<uidb64>/<token>/", views.CustomerPasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("login/", views.SecureLoginView.as_view(), name="login"),
    path("login/xac-thuc-2-buoc/", views.login_two_factor, name="login_two_factor"),
    path("logout/", views.SecureLogoutView.as_view(), name="logout"),
    path("profile/", views.profile, name="profile"),
    path("doi-mat-khau/", views.password_change, name="password_change"),
    path("xac-thuc-lai/", views.reauth, name="reauth"),
    path("cap-nhat/", views.profile_update, name="profile_update"),
    path("xac-thuc-2-buoc/bat/", views.two_factor_setup, name="two_factor_setup"),
    path("xac-thuc-2-buoc/ma-qr.svg", views.two_factor_qr, name="two_factor_qr"),
    path("xac-thuc-2-buoc/tat/", views.two_factor_disable, name="two_factor_disable"),
]

