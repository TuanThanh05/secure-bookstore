from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_http_methods
from axes.utils import reset as axes_reset
from django.contrib.auth.views import LogoutView, PasswordResetConfirmView, PasswordResetView
from django.urls import reverse_lazy

from core.decorators import mark_recent_auth
from core.security_log import log_event

from .decorators import customer_recent_auth_required, customer_required
from .emails import send_password_changed_email
from .forms import (
    CustomerPasswordChangeForm,
    CustomerPasswordResetForm,
    CustomerReauthForm,
    ProfileUpdateForm,
    RegisterForm,
    ResendVerificationForm,
)
from .profile import build_profile, decrypt_phone
from .services import (
    clear_password_change_failures,
    find_pending_user,
    mark_email_verified,
    record_password_change_failure,
    register_account,
    resend_verification,
    update_profile,
)

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


# AI-TRACE#060 | Claude Opus 5.5 | Đổi mật khẩu cho khách: giữ phiên hiện tại, đăng xuất thiết bị khác, sai nhiều lần thì đăng xuất | CẤM XÓA CHÚ THÍCH NÀY
@login_required
@never_cache
@require_http_methods(["GET", "POST"])
def password_change(request):
    if request.user.is_staff:
        return redirect("dashboard:profile")

    user = request.user
    if request.method == "POST":
        form = CustomerPasswordChangeForm(user, request.POST)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, user)
            clear_password_change_failures(user)
            log_event("password_changed", request, user=user, username=user.get_username(), detail={"via": "change"})
            send_password_changed_email(request, user, via="change")
            messages.success(request, "Đổi mật khẩu thành công. Các thiết bị khác đã bị đăng xuất.")
            return redirect("accounts:profile")
        if form.has_error("old_password", "password_incorrect"):
            failures = record_password_change_failure(user)
            log_event("login_failed", request, severity="warning", user=user, username=user.get_username(),
                      detail={"kind": "password_change_old_password", "failures": failures})
            if failures >= settings.PASSWORD_CHANGE_MAX_FAILURES:
                log_event("rate_limited", request, severity="warning", user=user, username=user.get_username(),
                          detail={"kind": "password_change"})
                logout(request)
                messages.error(request, "Bạn đã nhập sai mật khẩu hiện tại quá nhiều lần. Vui lòng đăng nhập lại.")
                return redirect("accounts:login")
    else:
        form = CustomerPasswordChangeForm(user)

    return render(request, "account/password_change.html", {"form": form})


def _safe_next(request, value, default):
    if value and url_has_allowed_host_and_scheme(value, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        return value
    return reverse(default)


# AI-TRACE#076 | Claude Opus 5.5 | Trang xác thực lại riêng cho khách, có link quên mật khẩu, next chỉ trỏ trong site | CẤM XÓA CHÚ THÍCH NÀY
@customer_required
@never_cache
@require_http_methods(["GET", "POST"])
def reauth(request):
    next_url = _safe_next(request, request.POST.get("next") or request.GET.get("next"), "accounts:profile")
    if request.method == "POST":
        form = CustomerReauthForm(request, data=request.POST)
        if form.is_valid():
            mark_recent_auth(request)
            log_event("login_success", request, user=request.user, username=request.user.get_username(),
                      detail={"step_up": True})
            return redirect(next_url)
        if form.user_mismatch:
            log_event("access_denied", request, severity="warning", user=request.user,
                      username=request.user.get_username(), detail={"step_up": "user_mismatch"})
    else:
        form = CustomerReauthForm(request)
    return render(request, "account/reauth.html",
                  {"form": form, "next": next_url, "reauth_minutes": settings.REAUTH_MAX_AGE // 60})


# AI-TRACE#077 | Claude Opus 5.5 | Cập nhật họ, tên, SĐT của khách sau khi xác thực lại | CẤM XÓA CHÚ THÍCH NÀY
@customer_required
@customer_recent_auth_required
@never_cache
@require_http_methods(["GET", "POST"])
def profile_update(request):
    user = request.user
    if request.method == "POST":
        form = ProfileUpdateForm(request.POST)
        if form.is_valid():
            changed = update_profile(request, user, form.cleaned_data)
            messages.success(request, "Đã cập nhật thông tin." if changed else "Không có thay đổi nào.")
            return redirect("accounts:profile")
    else:
        form = ProfileUpdateForm(initial={
            "last_name": user.last_name,
            "first_name": user.first_name,
            "phone": decrypt_phone(user) or "",
        })
    return render(request, "account/profile_update.html", {"form": form})
