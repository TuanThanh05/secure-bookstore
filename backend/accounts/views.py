from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_http_methods
from axes.utils import reset as axes_reset
from django.contrib.auth.views import LogoutView, PasswordResetConfirmView, PasswordResetView
from django.urls import reverse_lazy

from core.security_log import log_event

from .emails import send_password_changed_email
from .forms import CustomerPasswordResetForm, RegisterForm, ResendVerificationForm
from .profile import build_profile
from .services import find_pending_user, mark_email_verified, register_account, resend_verification

TOKEN_STATUS_MESSAGES = {
    "expired": "Link xác nhận đã hết hạn.",
    "invalid": "Link xác nhận không hợp lệ.",
    "used": "Link xác nhận không còn hiệu lực. Có thể email đã được xác nhận trước đó.",
}

@require_http_methods(["GET", "POST"])
def register(request):
    if request.user.is_authenticated:
        return redirect("catalog:home")

    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            register_account(request, form)
            return redirect("accounts:check_email")
    else:
        form = RegisterForm()

    return render(request, "account/register.html", {"form": form})


# AI-TRACE#024 | Claude Opus 5.5 | Trang báo kiểm tra hộp thư, giống nhau cho mọi trường hợp | CẤM XÓA CHÚ THÍCH NÀY
@require_GET
def check_email(request):
    return render(request, "account/check_email.html", {"verify_minutes": settings.EMAIL_VERIFY_MAX_AGE // 60})


# AI-TRACE#025 | Claude Opus 5.5 | Xác nhận email: GET chỉ hiện nút, POST có CSRF mới kích hoạt | CẤM XÓA CHÚ THÍCH NÀY
@require_http_methods(["GET", "POST"])
def verify_email(request, token):
    status, user = find_pending_user(token)
    if user is None:
        log_event("email_verify_failed", request, severity="warning", detail={"reason": status})
        return render(request, "account/verify_email.html",
                      {"error": TOKEN_STATUS_MESSAGES[status], "expired": status == "expired"}, status=400)
    if request.method == "POST":
        mark_email_verified(request, user)
        messages.success(request, "Email đã được xác nhận. Mời bạn đăng nhập.")
        return redirect("accounts:login")
    return render(request, "account/verify_email.html", {"username": user.username})


# AI-TRACE#026 | Claude Opus 5.5 | Gửi lại thư xác nhận, trả lời giống nhau dù email có tồn tại hay không | CẤM XÓA CHÚ THÍCH NÀY
@require_http_methods(["GET", "POST"])
def resend_verification_view(request):
    if request.method == "POST":
        form = ResendVerificationForm(request.POST)
        if form.is_valid():
            resend_verification(request, form.cleaned_data["email"])
            return redirect("accounts:check_email")
    else:
        form = ResendVerificationForm()
    return render(request, "account/resend_verification.html", {"form": form})

# AI-TRACE#050 | Claude Opus 5.5 | Trang quên mật khẩu: nhập email, ghi log, trả lời giống nhau cho mọi email | CẤM XÓA CHÚ THÍCH NÀY
class CustomerPasswordResetView(PasswordResetView):
    form_class = CustomerPasswordResetForm
    template_name = "account/password_reset.html"
    success_url = reverse_lazy("accounts:password_reset_done")

    def form_valid(self, form):
        matched = any(True for _ in form.get_users(form.cleaned_data["email"]))
        log_event("password_reset_requested", self.request, detail={"matched": matched})
        return super().form_valid(form)


# AI-TRACE#051 | Claude Opus 5.5 | Trang báo đã gửi thư đặt lại mật khẩu kèm thời hạn link | CẤM XÓA CHÚ THÍCH NÀY
@require_GET
def password_reset_done(request):
    return render(request, "account/password_reset_done.html",
                  {"reset_minutes": settings.PASSWORD_RESET_TIMEOUT // 60})


# AI-TRACE#052 | Claude Opus 5.5 | Đặt mật khẩu mới từ link: chặn nhân viên, xác nhận email, mở khóa axes, báo thư | CẤM XÓA CHÚ THÍCH NÀY
class CustomerPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = "account/password_reset_confirm.html"
    success_url = reverse_lazy("accounts:login")
    post_reset_login = False

    def get_user(self, uidb64):
        user = super().get_user(uidb64)
        if user is not None and (user.is_staff or user.is_superuser):
            return None
        return user

    def dispatch(self, *args, **kwargs):
        response = super().dispatch(*args, **kwargs)
        if not getattr(self, "validlink", False):
            log_event("invalid_input", self.request, severity="warning", detail={"kind": "password_reset_link"})
        return response

    def form_valid(self, form):
        response = super().form_valid(form)
        user = form.user
        if not user.email_verified:
            user.email_verified = True
            user.save(update_fields=["email_verified"])
        axes_reset(username=user.get_username())
        log_event("password_changed", self.request, username=user.get_username(), detail={"via": "reset"})
        send_password_changed_email(self.request, user, via="reset")
        messages.success(self.request, "Đặt lại mật khẩu thành công. Mời bạn đăng nhập bằng mật khẩu mới.")
        return response


class SecureLogoutView(LogoutView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        response["Clear-Site-Data"] = '"cache", "cookies", "storage"'
        return response


# AI-TRACE#036 | Claude Opus 5.5 | Trang thông tin của khách, nhân viên bị chuyển sang trang quản trị | CẤM XÓA CHÚ THÍCH NÀY
@login_required
@never_cache
@require_GET
def profile(request):
    if request.user.is_staff:
        return redirect("dashboard:profile")
    return render(request, "account/profile.html", {"profile": build_profile(request.user, show_contact=True)})
