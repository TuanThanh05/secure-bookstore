import re
import secrets
from unittest import mock

from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from accounts.forms import CurrentUserPasswordForm, CustomerReauthForm
from accounts.models import User
from core.models import SecurityEvent
from dashboard.forms import AccountActionForm, ReauthForm

PASSWORD = secrets.token_urlsafe(12) + "-Aa9"
OTHER_PASSWORD = secrets.token_urlsafe(12) + "-Bb8"
NAMED_USERNAME_INPUT = re.compile(r'<input[^>]*name="username"')


def account(**overrides):
    data = {"id": 7, "username": "khach_t22", "masked_email": "k***@example.test", "status_label": "Hoạt động",
            "is_locked": False, "date_joined": None}
    data.update(overrides)
    return mock.Mock(**data)


class PasswordOnlyReauthTests(TestCase):
    def setUp(self):
        cache.clear()
        self.customer = User.objects.create_user(username="khach_t22", email="k22@example.test", password=PASSWORD,
                                                 email_verified=True)
        self.other = User.objects.create_user(username="nguoi_khac", email="nk@example.test",
                                              password=OTHER_PASSWORD, email_verified=True)
        self.staff = User.objects.create_user(username="qtv_t22", email="q22@example.test", password=PASSWORD,
                                              is_staff=True)

    def test_forms_have_only_password(self):
        self.assertEqual(list(CustomerReauthForm.base_fields), ["password"])
        self.assertEqual(list(ReauthForm.base_fields), ["password"])
        self.assertEqual(list(AccountActionForm(mock.Mock()).fields), ["reason", "password"])
        for form_class in (CustomerReauthForm, ReauthForm, AccountActionForm):
            self.assertTrue(issubclass(form_class, CurrentUserPasswordForm))

    def test_customer_page_shows_name_as_text_only(self):
        self.client.force_login(self.customer)
        page = self.client.get(reverse("accounts:reauth")).content.decode()
        self.assertIn("Xác nhận bằng tài khoản", page)
        self.assertIn("khach_t22", page)
        self.assertIsNone(NAMED_USERNAME_INPUT.search(page))

    def test_staff_page_shows_name_as_text_only(self):
        self.client.force_login(self.staff)
        page = self.client.get(reverse("dashboard:reauth")).content.decode()
        self.assertIn("Xác nhận bằng tài khoản", page)
        self.assertIn("qtv_t22", page)
        self.assertIsNone(NAMED_USERNAME_INPUT.search(page))

    def test_lock_page_shows_admin_name_as_text_only(self):
        self.client.force_login(self.staff)
        with mock.patch("dashboard.account_views.get_account", return_value=account()):
            page = self.client.get(reverse("dashboard:account_lock", args=[7])).content.decode()
        self.assertIn("Xác nhận bằng tài khoản", page)
        self.assertIn("qtv_t22", page)
        self.assertIsNone(NAMED_USERNAME_INPUT.search(page))

    def test_posted_username_is_ignored(self):
        self.client.force_login(self.customer)
        url = reverse("accounts:reauth")
        response = self.client.post(url, {"username": "nguoi_khac", "password": OTHER_PASSWORD})
        self.assertContains(response, "Mật khẩu không đúng.")
        self.assertEqual(list(SecurityEvent.objects.filter(event_type="login_failed")
                              .values_list("username_attempted", flat=True)), ["khach_t22"])
        response = self.client.post(url, {"username": "nguoi_khac", "password": PASSWORD})
        self.assertEqual(response.status_code, 302)

    def test_wrong_password_counts_against_own_account(self):
        self.client.force_login(self.staff)
        self.client.post(reverse("dashboard:reauth"), {"password": "sai-" + PASSWORD})
        event = SecurityEvent.objects.get(event_type="login_failed")
        self.assertEqual(event.username_attempted, "qtv_t22")
        self.assertFalse(SecurityEvent.objects.filter(event_type="access_denied").exists())

    def test_logged_in_user_cannot_lock_out_another_account(self):
        attacker = self.client
        attacker.force_login(self.customer)
        for attempt in range(5):
            attacker.post(reverse("accounts:reauth"), {"username": "nguoi_khac", "password": f"doan-{attempt}"})
        victim = self.client_class().post(reverse("accounts:login"),
                                          {"username": "nguoi_khac", "password": OTHER_PASSWORD})
        self.assertEqual(victim.status_code, 302)
