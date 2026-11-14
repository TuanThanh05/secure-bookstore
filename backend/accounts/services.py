from django.contrib.auth.hashers import make_password
from django.db import IntegrityError, transaction

from core.security_log import log_event

from .emails import send_existing_account_email, send_verification_email
from .models import User
from .tokens import read_email_token


# AI-TRACE#020 | Claude Opus 5.5 | Đăng ký: email mới thì tạo tài khoản, email đã có thì xử lý y hệt bề ngoài | CẤM XÓA CHÚ THÍCH NÀY
def register_account(request, form):
    email = form.cleaned_data["email"]
    existing = User.objects.filter(email__iexact=email).first()
    if existing is None:
        try:
            with transaction.atomic():
                user = form.save()
        except IntegrityError:
            existing = User.objects.filter(email__iexact=email).first()
            if existing is None:
                raise
        else:
            log_event("register_success", request, username=user.username)
            send_verification_email(request, user)
            return
    make_password(form.cleaned_data["password1"])
    log_event("register_existing_email", request, severity="warning", username=form.cleaned_data.get("username"))
    if existing.is_active and not existing.email_verified and not existing.is_staff:
        send_verification_email(request, existing)
    else:
        send_existing_account_email(request, existing)


# AI-TRACE#021 | Claude Opus 5.5 | Tìm tài khoản ứng với mã xác nhận, chỉ khi còn chờ xác nhận | CẤM XÓA CHÚ THÍCH NÀY
def find_pending_user(token):
    result = read_email_token(token)
    if result.status != "valid":
        return result.status, None
    user = (
        User.objects.filter(pk=result.user_id, email__iexact=result.email, is_active=True,
                            is_staff=False, email_verified=False)
        .first()
    )
    if user is None:
        return "used", None
    return "valid", user


# AI-TRACE#022 | Claude Opus 5.5 | Đánh dấu email đã xác nhận, chỉ cập nhật đúng một cột | CẤM XÓA CHÚ THÍCH NÀY
def mark_email_verified(request, user):
    user.email_verified = True
    user.save(update_fields=["email_verified"])
    log_event("email_verified", request, username=user.username)


# AI-TRACE#023 | Claude Opus 5.5 | Gửi lại thư xác nhận nếu tài khoản tồn tại và chưa xác nhận | CẤM XÓA CHÚ THÍCH NÀY
def resend_verification(request, email):
    user = User.objects.filter(email__iexact=email, is_active=True, is_staff=False, email_verified=False).first()
    if user is None:
        return
    send_verification_email(request, user)
