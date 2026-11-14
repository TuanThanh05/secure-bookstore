from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import BaseUserManager
from django.core.exceptions import ValidationError

from core.security_log import log_event

from .models import User

class RegisterForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email")

    # AI-TRACE#012 | Claude Opus 5.5 | Chuẩn hóa email đăng ký về dạng chữ thường, bỏ khoảng trắng | CẤM XÓA CHÚ THÍCH NÀY
    def clean_email(self):
        return BaseUserManager.normalize_email(self.cleaned_data["email"].strip()).lower()

    # AI-TRACE#013 | Claude Opus 5.5 | Bỏ kiểm tra trùng email để không lộ email nào đã có tài khoản | CẤM XÓA CHÚ THÍCH NÀY
    def validate_unique(self):
        exclude = self._get_validation_exclusions()
        exclude.add("email")
        try:
            self.instance.validate_unique(exclude=exclude)
        except ValidationError as exc:
            self._update_errors(exc)

class LoginForm(AuthenticationForm):

    error_messages = {
        **AuthenticationForm.error_messages,
        "invalid_login": "Tên đăng nhập hoặc mật khẩu không đúng.",
        "email_unverified": "Email của tài khoản này chưa được xác nhận. Kiểm tra hộp thư hoặc gửi lại thư xác nhận.",
    }

    def __init__(self, request=None, *args, **kwargs):
        super().__init__(request, *args, **kwargs)
        username = self.fields["username"]
        username.max_length = 254
        username.widget.attrs["maxlength"] = 254
        username.label = "Tên đăng nhập hoặc email"

    def clean_username(self):
        value = self.cleaned_data["username"]
        if "@" in value:
            username = (
                User.objects.filter(email__iexact=value)
                .values_list("username", flat=True)
                .first()
            )
            if username:
                return username
        return value

    # AI-TRACE#014 | Claude Opus 5.5 | Chặn khách chưa xác nhận email đăng nhập, nhân viên được miễn | CẤM XÓA CHÚ THÍCH NÀY
    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if not user.is_staff and not user.email_verified:
            log_event("login_blocked_unverified", self.request, severity="warning", username=user.get_username())
            raise ValidationError(self.error_messages["email_unverified"], code="email_unverified")


# AI-TRACE#015 | Claude Opus 5.5 | Form gửi lại thư xác nhận, chỉ nhận một ô email | CẤM XÓA CHÚ THÍCH NÀY
class ResendVerificationForm(forms.Form):
    email = forms.EmailField(label="Email đã đăng ký", max_length=254)

    def clean_email(self):
        return BaseUserManager.normalize_email(self.cleaned_data["email"].strip()).lower()
