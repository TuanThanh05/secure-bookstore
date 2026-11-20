import time
from urllib.parse import quote, urlencode

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.cache import never_cache
from django.views.decorators.csp import csp_override
from django.views.decorators.http import require_GET, require_http_methods
from axes.utils import reset as axes_reset
from django.contrib.auth.views import LoginView, LogoutView, PasswordResetConfirmView, PasswordResetView
from django.urls import reverse_lazy

from core.captcha import captcha_site_key, verify_captcha
from core.decorators import has_recent_auth, mark_recent_auth
from core.security_log import log_event

from .decorators import customer_recent_auth_required, customer_required
from . import two_factor
from .emails import send_password_changed_email, send_two_factor_email
from .forms import (
    CustomerPasswordChangeForm,
    CustomerPasswordResetForm,
    CustomerReauthForm,
    CustomerSetPasswordForm,
    LoginForm,
    ProfileUpdateForm,
    SignupCompleteForm,
    SignupEmailForm,
    TwoFactorCodeForm,
    TwoFactorDisableForm,
)
from .models import User
from .profile import build_profile, decrypt_phone
from .services import (
    allow_signup_step,
    clear_password_change_failures,
    complete_signup,
    email_has_account,
    pending_signup_email,
    record_password_change_failure,
    remember_signup_email,
    start_signup,
    update_profile,
)
from .tokens import read_signup_token

SIGNUP_ERRORS = {
    "expired": "Link đăng ký đã hết hạn.",
    "invalid": "Link đăng ký không hợp lệ.",
    "used": "Link đăng ký không còn hiệu lực. Có thể email này đã được dùng để tạo tài khoản.",
    "session": "Phiên đăng ký đã hết hạn hoặc không tồn tại. Hãy mở lại link trong thư, hoặc đăng ký lại từ đầu.",
}
SIGNUP_RATE_MESSAGE = "Bạn thao tác quá nhiều lần. Vui lòng thử lại sau ít phút."
CAPTCHA_MESSAGES = {
    "unavailable": "Hệ thống xác minh đang gặp sự cố. Vui lòng thử lại sau ít phút.",
}
CAPTCHA_DEFAULT_MESSAGE = "Chưa xác minh được bạn không phải robot. Vui lòng làm lại bước xác minh rồi gửi lại."


def _signup_error(request, reason):
    return render(request, "account/signup_complete.html", {"error": SIGNUP_ERRORS[reason]}, status=400)


def _register_page(request, form, status=200):
    context = {"form": form, "turnstile_site_key": captcha_site_key(), "turnstile_action": settings.TURNSTILE_ACTION}
    return render(request, "account/register.html", context, status=status)


# AI-TRACE#422 | Claude Opus 5.5 | Đăng ký bước 1: chỉ nhận email, mọi trường hợp đều chuyển tới trang kiểm tra hộp thư | CẤM XÓA CHÚ THÍCH NÀY | đã viết lại bởi Claude Opus 5.5 khi thêm Cloudflare Turnstile
@csp_override(settings.SIGNUP_CSP)
@require_http_methods(["GET", "POST"])
def register(request):
    if request.user.is_authenticated:
        return redirect("catalog:home")

    if request.method == "POST":
        form = SignupEmailForm(request.POST)
        if form.is_valid():
            if not allow_signup_step(request, "start"):
                form.add_error(None, SIGNUP_RATE_MESSAGE)
                return _register_page(request, form, status=429)
            captcha = verify_captcha(request, settings.TURNSTILE_ACTION)
            if not captcha.ok:
                form.add_error(None, CAPTCHA_MESSAGES.get(captcha.reason, CAPTCHA_DEFAULT_MESSAGE))
                return _register_page(request, form, status=503 if captcha.reason == "unavailable" else 400)
            start_signup(request, form.cleaned_data["email"])
            return redirect("accounts:check_email")
    else:
        form = SignupEmailForm()

    return _register_page(request, form)


# AI-TRACE#024 | Claude Opus 5.5 | Trang báo kiểm tra hộp thư, giống nhau cho mọi trường hợp | CẤM XÓA CHÚ THÍCH NÀY
@require_GET
def check_email(request):
    return render(request, "account/check_email.html", {"link_minutes": settings.SIGNUP_LINK_MAX_AGE // 60})


# AI-TRACE#423 | Claude Opus 5.5 | Mở link đăng ký: kiểm tra mã, cất email vào phiên rồi chuyển sang địa chỉ không chứa mã | CẤM XÓA CHÚ THÍCH NÀY
@never_cache
@require_GET
def signup_confirm(request, token):
    if request.user.is_authenticated:
        return redirect("catalog:home")
    result = read_signup_token(token)
    status = result.status
    if status == "valid" and email_has_account(result.email):
        status = "used"
    if status != "valid":
        log_event("register_link_invalid", request, severity="warning", detail={"reason": status},
                  path=reverse("accounts:signup_confirm", args=["-"]))
        return _signup_error(request, status)
    remember_signup_email(request, result.email)
    return redirect("accounts:signup_complete")


# AI-TRACE#424 | Claude Opus 5.5 | Đăng ký bước 2: đặt tên đăng nhập, mật khẩu cho email trong phiên, xong thì về đăng nhập | CẤM XÓA CHÚ THÍCH NÀY
@never_cache
@require_http_methods(["GET", "POST"])
def signup_complete(request):
    if request.user.is_authenticated:
        return redirect("catalog:home")
    email = pending_signup_email(request)
    if email is None:
        log_event("register_link_invalid", request, severity="warning", detail={"reason": "session"})
        return _signup_error(request, "session")

    if request.method == "POST":
        form = SignupCompleteForm(request.POST, email=email)
        if not allow_signup_step(request, "complete"):
            form.add_error(None, SIGNUP_RATE_MESSAGE)
            return render(request, "account/signup_complete.html", {"form": form, "email": email}, status=429)
        if form.is_valid():
            outcome = complete_signup(request, form, email)
            if outcome == "created":
                messages.success(request, "Tạo tài khoản thành công. Mời bạn đăng nhập.")
                return redirect("accounts:login")
            if outcome == "email_taken":
                return _signup_error(request, "used")
            form.add_error("username", User._meta.get_field("username").error_messages["unique"])
        return render(request, "account/signup_complete.html", {"form": form, "email": email}, status=400)

    form = SignupCompleteForm(email=email)
    return render(request, "account/signup_complete.html", {"form": form, "email": email})


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


# AI-TRACE#052 | Claude Opus 5.5 | Đặt mật khẩu mới từ link: chặn nhân viên, xác nhận email, mở khóa axes, báo thư | CẤM XÓA CHÚ THÍCH NÀY | đã viết lại bởi Claude Opus 5.5 khi đổi sang đăng ký bằng email
class CustomerPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = "account/password_reset_confirm.html"
    form_class = CustomerSetPasswordForm
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


# AI-TRACE#036 | Claude Opus 5.5 | Trang thông tin của khách, nhân viên bị chuyển sang trang quản trị | CẤM XÓA CHÚ THÍCH NÀY | đã viết lại bởi Claude Opus 5.5 khi thêm xác thực 2 bước
@login_required
@never_cache
@require_GET
def profile(request):
    if request.user.is_staff:
        return redirect("dashboard:profile")
    enabled = two_factor.has_two_factor(request.user)
    return render(request, "account/profile.html", {
        "profile": build_profile(request.user, show_contact=True),
        "two_factor_enabled": enabled,
        "recovery_remaining": two_factor.recovery_remaining(request.user) if enabled else None,
    })


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


TWO_FACTOR_PENDING_KEY = "accounts:2fa-pending"
TWO_FACTOR_EXPIRED = "Phiên đăng nhập 2 bước đã hết hạn. Vui lòng đăng nhập lại."
TWO_FACTOR_BLOCKED = "Tài khoản đã nhập sai mã xác thực quá nhiều lần. Vui lòng thử lại sau 1 giờ."
TWO_FACTOR_WRONG = "Mã xác thực không đúng hoặc đã được dùng."
STAFF_WITHOUT_TWO_FACTOR = ("Tài khoản quản trị chưa cài xác thực 2 bước nên không đăng nhập được trên web. "
                            "Cài bằng lệnh trên máy chủ (xem docs/xac-thuc-2-buoc.md).")


# AI-TRACE#493 | Claude Opus 5.5 | Đăng nhập bước 1: đúng mật khẩu mà cần 2 bước thì CHƯA đăng nhập, chỉ ghi trạng thái chờ (đổi session ID) rồi chuyển sang bước 2 | CẤM XÓA CHÚ THÍCH NÀY
class SecureLoginView(LoginView):
    template_name = "account/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        user = form.get_user()
        if not two_factor.requires_two_factor(user):
            return super().form_valid(form)
        if (user.is_staff or user.is_superuser) and two_factor.confirmed_device(user) is None:
            log_event("access_denied", self.request, severity="warning", user=user, username=user.get_username(),
                      detail={"kind": "staff_without_two_factor"})
            form.add_error(None, STAFF_WITHOUT_TWO_FACTOR)
            return self.form_invalid(form)
        if two_factor.is_blocked(user):
            log_event("rate_limited", self.request, severity="warning", user=user, username=user.get_username(),
                      detail={"kind": "two_factor"})
            form.add_error(None, TWO_FACTOR_BLOCKED)
            return self.form_invalid(form)
        self.request.session.cycle_key()
        self.request.session[TWO_FACTOR_PENDING_KEY] = {
            "user_id": user.pk,
            "backend": user.backend,
            "at": int(time.time()),
            "tries": 0,
            "next": self.get_success_url(),
        }
        return redirect("accounts:login_two_factor")


def _pending_login(request):
    data = request.session.get(TWO_FACTOR_PENDING_KEY)
    if not isinstance(data, dict):
        return None, None
    age = int(time.time()) - int(data.get("at", 0))
    if not 0 <= age <= settings.TWO_FACTOR_PENDING_MAX_AGE:
        request.session.pop(TWO_FACTOR_PENDING_KEY, None)
        return None, None
    user = User.objects.filter(pk=data.get("user_id"), is_active=True).first()
    if user is None:
        request.session.pop(TWO_FACTOR_PENDING_KEY, None)
        return None, None
    return data, user


def _cancel_pending(request, message):
    request.session.pop(TWO_FACTOR_PENDING_KEY, None)
    messages.error(request, message)
    return redirect("accounts:login")


# AI-TRACE#494 | Claude Opus 5.5 | Đăng nhập bước 2: mã 6 số (hoặc mã dự phòng của khách) đúng mới login(); sai 5 lần hủy lượt, sai nhiều lần/giờ chặn tài khoản | CẤM XÓA CHÚ THÍCH NÀY
@never_cache
@require_http_methods(["GET", "POST"])
def login_two_factor(request):
    if request.user.is_authenticated:
        return redirect("catalog:home")
    pending, user = _pending_login(request)
    if pending is None:
        return _cancel_pending(request, TWO_FACTOR_EXPIRED)
    allow_recovery = not (user.is_staff or user.is_superuser)
    if request.method == "POST":
        form = TwoFactorCodeForm(request.POST, allow_recovery=allow_recovery)
        if two_factor.is_blocked(user):
            return _cancel_pending(request, TWO_FACTOR_BLOCKED)
        if form.is_valid():
            code = form.cleaned_data["code"]
            method, remaining = None, None
            if allow_recovery and two_factor.looks_like_recovery_code(code):
                remaining = two_factor.use_recovery_code(user, code)
                method = "recovery" if remaining is not None else None
            else:
                device = two_factor.confirmed_device(user)
                method = "totp" if device is not None and two_factor.verify_code(device, code) else None
            if method:
                next_url = pending.get("next") or settings.LOGIN_REDIRECT_URL
                request.session.pop(TWO_FACTOR_PENDING_KEY, None)
                two_factor.clear_failures(user)
                login(request, user, backend=pending.get("backend"))
                if method == "recovery":
                    log_event("two_factor_recovery_used", request, severity="warning", user=user,
                              username=user.get_username(), detail={"remaining": remaining})
                    send_two_factor_email(request, user, "recovery_used", remaining=remaining)
                    messages.warning(request, f"Bạn vừa dùng một mã dự phòng. Còn lại {remaining} mã.")
                return redirect(next_url)
            failures = two_factor.record_failure(user)
            pending["tries"] = int(pending.get("tries", 0)) + 1
            request.session[TWO_FACTOR_PENDING_KEY] = pending
            log_event("otp_failed", request, severity="warning", user=user, username=user.get_username(),
                      detail={"tries": pending["tries"], "failures_hour": failures})
            if pending["tries"] >= settings.TWO_FACTOR_MAX_ATTEMPTS or two_factor.is_blocked(user):
                return _cancel_pending(request, "Bạn đã nhập sai mã quá nhiều lần. Vui lòng đăng nhập lại.")
            form.add_error("code", TWO_FACTOR_WRONG)
    else:
        form = TwoFactorCodeForm(allow_recovery=allow_recovery)
    return render(request, "account/login_two_factor.html", {
        "form": form,
        "allow_recovery": allow_recovery,
        "minutes": settings.TWO_FACTOR_PENDING_MAX_AGE // 60,
    })


# AI-TRACE#495 | Claude Opus 5.5 | Cài 2 bước cho khách: trang QR cần xác thực lại; mã đúng thì bật, hiện 5 mã dự phòng đúng một lần, gửi thư báo | CẤM XÓA CHÚ THÍCH NÀY
@customer_required
@never_cache
@require_http_methods(["GET", "POST"])
def two_factor_setup(request):
    user = request.user
    if two_factor.has_two_factor(user):
        messages.info(request, "Xác thực 2 bước đang bật.")
        return redirect("accounts:profile")
    if request.method == "GET":
        if not has_recent_auth(request):
            query = urlencode({"next": request.get_full_path()})
            return redirect(f"{reverse('accounts:reauth')}?{query}")
        device = two_factor.pending_setup(user) or two_factor.start_setup(user)
        form = TwoFactorCodeForm()
    else:
        device = two_factor.pending_setup(user)
        if device is None:
            messages.error(request, "Lượt cài đã hết hạn. Hãy bắt đầu lại.")
            return redirect("accounts:two_factor_setup")
        form = TwoFactorCodeForm(request.POST)
        if form.is_valid():
            codes = two_factor.confirm_setup(user, device, form.cleaned_data["code"])
            if codes is not None:
                log_event("two_factor_enabled", request, user=user, username=user.get_username(), detail={"via": "web"})
                send_two_factor_email(request, user, "enabled")
                return render(request, "account/two_factor_codes.html", {
                    "codes": codes,
                    "download_data": quote(_recovery_file_text(user, codes)),
                })
            log_event("otp_failed", request, severity="warning", user=user, username=user.get_username(),
                      detail={"kind": "setup"})
            form.add_error("code", TWO_FACTOR_WRONG)
    secret = two_factor.setup_secret(device)
    return render(request, "account/two_factor_setup.html", {
        "form": form,
        "secret": two_factor.group_secret(secret),
        "issuer": settings.TWO_FACTOR_ISSUER,
        "setup_minutes": settings.TWO_FACTOR_SETUP_MAX_AGE // 60,
    })


def _recovery_file_text(user, codes):
    lines = [
        f"Ma du phong xac thuc 2 buoc - {settings.TWO_FACTOR_ISSUER}",
        f"Tai khoan: {user.get_username()}",
        "Moi ma chi dung duoc mot lan. Cat file nay o noi an toan, khong gui cho ai.",
        "",
        *codes,
        "",
    ]
    return "\n".join(lines)


# AI-TRACE#496 | Claude Opus 5.5 | Ảnh QR của lượt cài đang dở: chỉ chủ tài khoản, không cache, hết lượt cài thì 404 | CẤM XÓA CHÚ THÍCH NÀY
@customer_required
@never_cache
@require_GET
def two_factor_qr(request):
    device = two_factor.pending_setup(request.user)
    if device is None:
        raise Http404
    uri = two_factor.provisioning_uri(request.user, two_factor.setup_secret(device))
    response = HttpResponse(two_factor.qr_svg(uri), content_type="image/svg+xml")
    response["Content-Security-Policy"] = "default-src 'none'"
    return response


# AI-TRACE#497 | Claude Opus 5.5 | Tắt 2 bước: cần mật khẩu và mã hiện tại (hoặc mã dự phòng), sai nhiều lần thì đăng xuất, gửi thư báo | CẤM XÓA CHÚ THÍCH NÀY
@customer_required
@never_cache
@require_http_methods(["GET", "POST"])
def two_factor_disable(request):
    user = request.user
    device = two_factor.confirmed_device(user)
    if device is None:
        messages.info(request, "Xác thực 2 bước đang tắt.")
        return redirect("accounts:profile")
    if request.method == "POST":
        form = TwoFactorDisableForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data["code"]
            password_ok = user.check_password(form.cleaned_data["password"])
            if two_factor.looks_like_recovery_code(code):
                code_ok = password_ok and two_factor.use_recovery_code(user, code) is not None
            else:
                code_ok = password_ok and two_factor.verify_code(device, code)
            if code_ok:
                two_factor.disable(user)
                two_factor.clear_failures(user)
                log_event("two_factor_disabled", request, severity="warning", user=user,
                          username=user.get_username(), detail={"via": "web"})
                send_two_factor_email(request, user, "disabled")
                messages.success(request, "Đã tắt xác thực 2 bước.")
                return redirect("accounts:profile")
            failures = two_factor.record_failure(user)
            log_event("otp_failed", request, severity="warning", user=user, username=user.get_username(),
                      detail={"kind": "disable", "failures_hour": failures})
            if two_factor.is_blocked(user):
                logout(request)
                messages.error(request, TWO_FACTOR_BLOCKED)
                return redirect("accounts:login")
            form.add_error(None, "Mật khẩu hoặc mã xác thực không đúng.")
    else:
        form = TwoFactorDisableForm()
    return render(request, "account/two_factor_disable.html", {"form": form})
