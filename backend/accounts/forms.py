import re

from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm, PasswordResetForm, UserCreationForm
from django.contrib.auth.models import BaseUserManager
from django.core.exceptions import ValidationError
from django.urls import reverse

from .emails import send_password_reset_email

from .models import User

WRONG_CURRENT_CREDENTIAL = "Mật khẩu hiện tại không đúng."

# AI-TRACE#412 | Claude Opus 5.5 | Bước 1 đăng ký: chỉ một ô email, chuẩn hóa về chữ thường | CẤM XÓA CHÚ THÍCH NÀY
class SignupEmailForm(forms.Form):
    email = forms.EmailField(label="Email", max_length=254,
                             widget=forms.EmailInput(attrs={"autocomplete": "email"}))

    def clean_email(self):
        return BaseUserManager.normalize_email(self.cleaned_data["email"].strip()).lower()


# AI-TRACE#413 | Claude Opus 5.5 | Bước 2 đăng ký: tên đăng nhập và mật khẩu, email lấy từ phiên chứ không từ form | CẤM XÓA CHÚ THÍCH NÀY
class SignupCompleteForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username",)

    def __init__(self, *args, email, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance.email = email
        self.instance.email_verified = True


class LoginForm(AuthenticationForm):

    error_messages = {
        **AuthenticationForm.error_messages,
        "invalid_login": "Tên đăng nhập hoặc mật khẩu không đúng.",
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


# AI-TRACE#049 | Claude Opus 5.5 | Form quên mật khẩu chỉ gửi cho khách, dùng thư và giới hạn của nhóm | CẤM XÓA CHÚ THÍCH NÀY
class CustomerPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(label="Email đã đăng ký", max_length=254)

    def get_users(self, email):
        return (user for user in super().get_users(email) if not user.is_staff and not user.is_superuser)

    def save(self, *args, request=None, **kwargs):
        self._request = request
        return super().save(*args, request=request, **kwargs)

    def send_mail(self, subject_template_name, email_template_name, context, from_email, to_email,
                  html_email_template_name=None):
        path = reverse("accounts:password_reset_confirm", args=[context["uid"], context["token"]])
        link = f"{context['protocol']}://{context['domain']}{path}"
        send_password_reset_email(self._request, context["user"], link)


# AI-TRACE#057 | Claude Opus 5.5 | Form đổi mật khẩu: mật khẩu hiện tại và hai ô mật khẩu mới | CẤM XÓA CHÚ THÍCH NÀY
class CustomerPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.error_messages = {**self.error_messages, "password_incorrect": WRONG_CURRENT_CREDENTIAL}
        self.fields["old_password"].label = "Mật khẩu hiện tại"
        self.fields["new_password1"].label = "Mật khẩu mới"
        self.fields["new_password2"].label = "Nhập lại mật khẩu mới"


NAME_RE = re.compile(r"^[^\W\d_]+(?:[ '\-][^\W\d_]+)*$")
PHONE_SEPARATORS_RE = re.compile(r"[\s.\-()]")
PHONE_RE = re.compile(r"^0[35789][0-9]{8}$")


# AI-TRACE#073 | Claude Opus 5.5 | Form xác thực lại của khách, nhận tên đăng nhập hoặc email và mật khẩu | CẤM XÓA CHÚ THÍCH NÀY
class CustomerReauthForm(forms.Form):
    error_messages = {"invalid": "Tên đăng nhập hoặc mật khẩu không đúng."}

    username = forms.CharField(label="Tên đăng nhập hoặc email", max_length=254)
    password = forms.CharField(label="Mật khẩu", strip=False,
                               widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}))

    def __init__(self, request, *args, **kwargs):
        self.request = request
        self.user_mismatch = False
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs["autocomplete"] = "username"

    def clean(self):
        cleaned = super().clean()
        username = cleaned.get("username")
        password = cleaned.get("password")
        if username and password:
            if "@" in username:
                username = (
                    User.objects.filter(email__iexact=username).values_list("username", flat=True).first()
                    or username
                )
            user = authenticate(self.request, username=username, password=password)
            if user is None or user.pk != self.request.user.pk:
                self.user_mismatch = user is not None
                raise ValidationError(self.error_messages["invalid"], code="invalid")
        return cleaned


# AI-TRACE#074 | Claude Opus 5.5 | Form cập nhật họ, tên, SĐT của khách; không có ô username hay email | CẤM XÓA CHÚ THÍCH NÀY
class ProfileUpdateForm(forms.Form):
    last_name = forms.CharField(label="Họ", max_length=50, required=False)
    first_name = forms.CharField(label="Tên", max_length=50, required=False)
    phone = forms.CharField(label="Số điện thoại", max_length=20, required=False,
                            widget=forms.TextInput(attrs={"type": "tel", "autocomplete": "tel", "inputmode": "tel"}))

    def _clean_name(self, field):
        value = " ".join(self.cleaned_data[field].split())
        if value and not NAME_RE.match(value):
            raise ValidationError("Chỉ được dùng chữ cái, khoảng trắng, dấu gạch ngang hoặc dấu nháy đơn.", code="invalid_name")
        return value

    def clean_last_name(self):
        return self._clean_name("last_name")

    def clean_first_name(self):
        return self._clean_name("first_name")

    def clean_phone(self):
        value = PHONE_SEPARATORS_RE.sub("", self.cleaned_data["phone"])
        if value.startswith("+84"):
            value = "0" + value[3:]
        if value and not PHONE_RE.match(value):
            raise ValidationError("Số điện thoại Việt Nam gồm 10 chữ số, bắt đầu bằng 03, 05, 07, 08 hoặc 09.", code="invalid_phone")
        return value
