import re

from django import forms
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordChangeForm,
    PasswordResetForm,
    SetPasswordForm,
    UserCreationForm,
)
from django.contrib.auth.models import BaseUserManager
from django.core.exceptions import ValidationError
from django.core.validators import MaxLengthValidator
from django.urls import reverse

from core.middleware import auto_lock_message

from .emails import send_password_reset_email

from .models import User

USERNAME_MAX_LENGTH = 50
WRONG_CURRENT_CREDENTIAL = "Mật khẩu hiện tại không đúng."
TOO_LONG_MESSAGE = "Mật khẩu dài tối đa %(limit_value)d ký tự."


def cap_password_fields(form, *names):
    limit = settings.PASSWORD_MAX_LENGTH
    for name in names:
        field = form.fields[name]
        field.max_length = limit
        field.validators.append(MaxLengthValidator(limit, message=TOO_LONG_MESSAGE))
        field.widget.attrs["maxlength"] = limit

class SignupEmailForm(forms.Form):
    email = forms.EmailField(label="Email", max_length=254,
                             widget=forms.EmailInput(attrs={"autocomplete": "email"}))

    def clean_email(self):
        return BaseUserManager.normalize_email(self.cleaned_data["email"].strip()).lower()


class SignupCompleteForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username",)

    def __init__(self, *args, email, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance.email = email
        self.instance.email_verified = True
        cap_password_fields(self, "password1", "password2")


class LoginForm(AuthenticationForm):

    error_messages = {
        **AuthenticationForm.error_messages,
        "invalid_login": "Tên đăng nhập hoặc mật khẩu không đúng.",
    }

    def __init__(self, request=None, *args, **kwargs):
        super().__init__(request, *args, **kwargs)
        username = self.fields["username"]
        username.max_length = USERNAME_MAX_LENGTH
        username.widget.attrs["maxlength"] = USERNAME_MAX_LENGTH
        username.label = "Tên đăng nhập"
        cap_password_fields(self, "password")

    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if user.is_auto_locked:
            raise ValidationError(auto_lock_message(user), code="auto_locked")


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


class CustomerPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.error_messages = {**self.error_messages, "password_incorrect": WRONG_CURRENT_CREDENTIAL}
        self.fields["old_password"].label = "Mật khẩu hiện tại"
        self.fields["new_password1"].label = "Mật khẩu mới"
        self.fields["new_password2"].label = "Nhập lại mật khẩu mới"
        cap_password_fields(self, "old_password", "new_password1", "new_password2")


class CustomerSetPasswordForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        cap_password_fields(self, "new_password1", "new_password2")


NAME_RE = re.compile(r"^[^\W\d_]+(?:[ '\-][^\W\d_]+)*$")
PHONE_SEPARATORS_RE = re.compile(r"[\s.\-()]")
PHONE_RE = re.compile(r"^0[35789][0-9]{8}$")


class CurrentUserPasswordForm(forms.Form):
    error_messages = {"invalid": "Mật khẩu không đúng."}

    password = forms.CharField(label="Mật khẩu", strip=False,
                               widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}))

    def __init__(self, request, *args, **kwargs):
        self.request = request
        super().__init__(*args, **kwargs)
        cap_password_fields(self, "password")

    @property
    def account_name(self):
        return self.request.user.get_username()

    def clean(self):
        cleaned = super().clean()
        password = cleaned.get("password")
        if password:
            user = authenticate(self.request, username=self.account_name, password=password)
            if user is None or user.pk != self.request.user.pk:
                raise ValidationError(self.error_messages["invalid"], code="invalid")
        return cleaned


class CustomerReauthForm(CurrentUserPasswordForm):
    pass


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


class TwoFactorCodeForm(forms.Form):
    code = forms.CharField(label="Mã xác thực", max_length=20, strip=True)

    def __init__(self, *args, allow_recovery=False, **kwargs):
        super().__init__(*args, **kwargs)
        field = self.fields["code"]
        field.widget.attrs.update({"autocomplete": "one-time-code", "autofocus": True, "maxlength": 20,
                                   "inputmode": "text" if allow_recovery else "numeric"})
        if allow_recovery:
            field.label = "Mã 6 số trong ứng dụng hoặc mã dự phòng"


class TwoFactorDisableForm(forms.Form):
    password = forms.CharField(label="Mật khẩu hiện tại", strip=False,
                               widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}))
    code = forms.CharField(label="Mã 6 số trong ứng dụng hoặc mã dự phòng", max_length=20, strip=True,
                           widget=forms.TextInput(attrs={"autocomplete": "one-time-code", "maxlength": 20}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        cap_password_fields(self, "password")
