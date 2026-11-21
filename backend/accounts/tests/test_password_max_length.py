import secrets
from unittest import mock

from django.conf import settings
from django.contrib.auth.password_validation import password_validators_help_texts, validate_password
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.test import RequestFactory, SimpleTestCase, TestCase
from django.urls import reverse

from accounts.forms import (
    CustomerPasswordChangeForm,
    CustomerReauthForm,
    CustomerSetPasswordForm,
    LoginForm,
    SignupCompleteForm,
)
from accounts.models import User
from accounts.validators import MaximumLengthValidator
from accounts.views import CustomerPasswordResetConfirmView
from dashboard.forms import ReauthForm

LIMIT = settings.PASSWORD_MAX_LENGTH


def secret_of(length):
    base = f"{secrets.token_urlsafe(LIMIT)}Aa9-"
    return (base * 3)[:length]


# AI-TRACE#467 | Claude Opus 5.5 | Test giới hạn 64 ký tự: validator, mọi form có ô mật khẩu, quá dài thì không gọi authenticate hay validator (không băm) | CẤM XÓA CHÚ THÍCH NÀY | đã viết lại bởi Claude Opus 5.5 khi bỏ ô tên đăng nhập ở xác thực lại (T2.2)
class MaximumLengthValidatorTests(SimpleTestCase):
    def test_limit_is_64(self):
        self.assertEqual(LIMIT, 64)

    def test_boundary(self):
        validator = MaximumLengthValidator(max_length=LIMIT)
        validator.validate(secret_of(LIMIT))
        with self.assertRaises(ValidationError) as caught:
            validator.validate(secret_of(LIMIT + 1))
        self.assertEqual(caught.exception.code, "password_too_long")

    def test_registered_in_settings(self):
        with self.assertRaises(ValidationError):
            validate_password(secret_of(LIMIT + 1))
        self.assertIn(f"Mật khẩu dài tối đa {LIMIT} ký tự.", password_validators_help_texts())


class PasswordFieldCapTests(TestCase):
    def setUp(self):
        cache.clear()
        self.secret = secret_of(LIMIT)
        self.user = User.objects.create_user(username="an_nguyen", email="an@example.test",
                                             password=self.secret, email_verified=True)
        self.request = RequestFactory().post("/")
        self.too_long = secret_of(LIMIT + 1)

    def assert_capped(self, form, *names):
        self.assertFalse(form.is_valid())
        for name in names:
            self.assertIn(name, form.errors)
            self.assertEqual(form.fields[name].widget.attrs["maxlength"], LIMIT)

    @mock.patch("django.contrib.auth.password_validation.validate_password")
    def test_signup_too_long_skips_validators(self, validate):
        form = SignupCompleteForm(data={"username": "binh_tran", "password1": self.too_long,
                                        "password2": self.too_long}, email="binh@example.test")
        self.assert_capped(form, "password1", "password2")
        validate.assert_not_called()
        self.assertFalse(User.objects.filter(username="binh_tran").exists())

    @mock.patch("django.contrib.auth.forms.authenticate")
    def test_login_too_long_skips_authenticate(self, auth):
        form = LoginForm(self.request, data={"username": "an_nguyen", "password": self.too_long})
        self.assert_capped(form, "password")
        auth.assert_not_called()

    def test_login_with_64_characters_works(self):
        response = self.client.post(reverse("accounts:login"), {"username": "an_nguyen", "password": self.secret})
        self.assertEqual(response.status_code, 302)
        self.assertIn("_auth_user_id", self.client.session)

    @mock.patch("django.contrib.auth.password_validation.validate_password")
    def test_change_password_too_long(self, validate):
        form = CustomerPasswordChangeForm(self.user, data={"old_password": self.too_long,
                                                           "new_password1": self.too_long,
                                                           "new_password2": self.too_long})
        with mock.patch.object(User, "check_password") as check:
            self.assert_capped(form, "old_password", "new_password1", "new_password2")
            check.assert_not_called()
        validate.assert_not_called()

    @mock.patch("django.contrib.auth.password_validation.validate_password")
    def test_reset_password_too_long(self, validate):
        form = CustomerSetPasswordForm(self.user, data={"new_password1": self.too_long,
                                                        "new_password2": self.too_long})
        self.assert_capped(form, "new_password1", "new_password2")
        validate.assert_not_called()

    @mock.patch("accounts.forms.authenticate")
    def test_customer_reauth_too_long(self, auth):
        form = CustomerReauthForm(self.request, data={"password": self.too_long})
        self.assert_capped(form, "password")
        auth.assert_not_called()

    @mock.patch("accounts.forms.authenticate")
    def test_staff_reauth_too_long(self, auth):
        form = ReauthForm(self.request, data={"password": self.too_long})
        self.assert_capped(form, "password")
        auth.assert_not_called()

    def test_reset_view_uses_capped_form(self):
        self.assertIs(CustomerPasswordResetConfirmView.form_class, CustomerSetPasswordForm)
