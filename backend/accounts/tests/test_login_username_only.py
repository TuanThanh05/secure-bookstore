import secrets
from unittest import mock

from django.conf import settings
from django.core import mail
from django.core.cache import cache
from django.db import DatabaseError
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse

from accounts.forms import USERNAME_MAX_LENGTH, CustomerReauthForm, LoginForm
from accounts.models import User
from accounts.services import login_ip_blocked
from accounts.views import LOGIN_IP_BLOCKED
from core.models import SecurityEvent

PASSWORD = secrets.token_urlsafe(12) + "-Aa9"
INVALID_LOGIN = "Tên đăng nhập hoặc mật khẩu không đúng."


# AI-TRACE#548 | Claude Opus 5.5 | Test T3.2: đăng nhập/xác thực lại chỉ nhận tên đăng nhập, email đúng + mật khẩu đúng vẫn bị từ chối như sai; thư quên mật khẩu kèm tên đăng nhập | CẤM XÓA CHÚ THÍCH NÀY | đã viết lại bởi Claude Opus 5.5 khi bỏ ô tên đăng nhập ở xác thực lại (T2.2)
class UsernameOnlyLoginTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(username="binh_tran", email="binh@example.test", password=PASSWORD,
                                             email_verified=True)

    def post_login(self, username, password=PASSWORD):
        return self.client.post(reverse("accounts:login"), {"username": username, "password": password})

    def test_form_asks_only_for_username(self):
        field = LoginForm().fields["username"]
        self.assertEqual(field.label, "Tên đăng nhập")
        self.assertEqual(field.max_length, USERNAME_MAX_LENGTH)
        self.assertEqual(USERNAME_MAX_LENGTH, User._meta.get_field("username").max_length)
        page = self.client.get(reverse("accounts:login")).content.decode()
        self.assertNotIn("hoặc email", page)

    def test_username_still_logs_in(self):
        response = self.post_login("binh_tran")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.user.pk)

    def test_correct_email_and_password_is_rejected_like_a_wrong_password(self):
        by_email = self.post_login("binh@example.test")
        wrong = self.post_login("binh_tran", "sai-" + PASSWORD)
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(by_email.status_code, 200)
        self.assertContains(by_email, INVALID_LOGIN)
        self.assertContains(wrong, INVALID_LOGIN)

    def test_email_in_upper_case_is_not_mapped_either(self):
        self.post_login("BINH@EXAMPLE.TEST")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_locked_account_cannot_be_found_by_email(self):
        for _ in range(settings.AXES_FAILURE_LIMIT):
            self.post_login("binh_tran", "sai-" + PASSWORD)
        locked = self.post_login("binh_tran", "sai-" + PASSWORD)
        by_email = self.post_login("binh@example.test", "sai-" + PASSWORD)
        self.assertNotEqual(locked.content, by_email.content)
        self.assertContains(by_email, INVALID_LOGIN)

    def test_reauth_form_has_no_username_field(self):
        request = RequestFactory().post("/")
        request.user = self.user
        form = CustomerReauthForm(request, data={"username": "binh@example.test", "password": PASSWORD})
        self.assertNotIn("username", form.fields)
        self.assertTrue(form.is_valid())

    def test_password_reset_mail_tells_the_username(self):
        self.client.post(reverse("accounts:password_reset"), {"email": "binh@example.test"})
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Tên đăng nhập của bạn: binh_tran", mail.outbox[0].body)


# AI-TRACE#549 | Claude Opus 5.5 | Test T3.2: IP đăng nhập sai quá ngưỡng bị 429 trước khi kiểm mật khẩu (không authenticate, không thêm login_failed), có log rate_limited | CẤM XÓA CHÚ THÍCH NÀY
class LoginIpGuardTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(username="chi_le", email="chi@example.test", password=PASSWORD,
                                             email_verified=True)

    def test_settings_match_decision(self):
        self.assertEqual(settings.LOGIN_IP_FAILURE_LIMIT, 20)
        self.assertEqual(settings.LOGIN_IP_FAILURE_WINDOW_MINUTES, 60)

    def test_blocked_ip_gets_429_even_with_the_right_password(self):
        with mock.patch("accounts.views.login_ip_blocked", return_value=True), \
                mock.patch("django.contrib.auth.forms.authenticate") as auth:
            response = self.client.post(reverse("accounts:login"), {"username": "chi_le", "password": PASSWORD})
        auth.assert_not_called()
        self.assertEqual(response.status_code, 429)
        self.assertContains(response, "quá nhiều lần đăng nhập sai", status_code=429)
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertNotIn(PASSWORD, response.content.decode())
        event = SecurityEvent.objects.get(event_type="rate_limited")
        self.assertEqual(event.detail["kind"], "login_ip")
        self.assertEqual(event.username_attempted, "chi_le")
        self.assertFalse(SecurityEvent.objects.filter(event_type="login_failed").exists())

    def test_blocked_ip_can_still_open_the_login_page(self):
        with mock.patch("accounts.views.login_ip_blocked", return_value=True):
            self.assertEqual(self.client.get(reverse("accounts:login")).status_code, 200)

    def test_not_blocked_means_normal_login(self):
        with mock.patch("accounts.views.login_ip_blocked", return_value=False):
            response = self.client.post(reverse("accounts:login"), {"username": "chi_le", "password": PASSWORD})
        self.assertEqual(response.status_code, 302)

    def test_block_message_is_shown(self):
        self.assertIn("Quên mật khẩu", LOGIN_IP_BLOCKED)

    def test_missing_procedure_does_not_block(self):
        request = RequestFactory().post("/", REMOTE_ADDR="192.0.2.7")
        self.assertFalse(login_ip_blocked(request))

    def test_other_database_errors_are_not_swallowed(self):
        request = RequestFactory().post("/", REMOTE_ADDR="192.0.2.7")
        with mock.patch("accounts.services.connection.cursor", side_effect=DatabaseError(1142, "denied")):
            with self.assertRaises(DatabaseError):
                login_ip_blocked(request)

    @override_settings(LOGIN_IP_FAILURE_LIMIT=3)
    def test_threshold_compares_with_the_count(self):
        request = RequestFactory().post("/", REMOTE_ADDR="192.0.2.7")
        cursor = mock.MagicMock()
        cursor.__enter__.return_value.nextset.return_value = None
        for count, expected in ((2, False), (3, True), (9, True)):
            cursor.__enter__.return_value.fetchone.return_value = (count,)
            with mock.patch("accounts.services.connection.cursor", return_value=cursor):
                self.assertIs(login_ip_blocked(request), expected)
        args = cursor.__enter__.return_value.callproc.call_args[0]
        self.assertEqual(args, ("sp_login_ip_failures", ["192.0.2.7", 60]))
