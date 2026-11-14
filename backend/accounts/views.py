from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET, require_http_methods
from django.contrib.auth.views import LogoutView

from core.security_log import log_event

from .forms import RegisterForm, ResendVerificationForm
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

class SecureLogoutView(LogoutView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        response["Clear-Site-Data"] = '"cache", "cookies", "storage"'
        return response


@login_required
@require_GET
def profile(request):
    return render(request, "account/profile.html")
