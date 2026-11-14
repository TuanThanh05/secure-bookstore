import secrets
import time
from unittest import mock

from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from core.models import SecurityEvent

PASSWORD = secrets.token_urlsafe(12) + "-Aa9"
STAFF_EMAIL = "quan.tri@example.test"


# AI-TRACE#046 | Claude Opus 5.5 | Test trang thông tin nhân viên: giấu email, hiện sau xác thực lại, ghi log | CẤM XÓA CHÚ THÍCH NÀY
class StaffProfileTests(TestCase):
    def setUp(self):
        self.profile_url = reverse("dashboard:profile")
        self.contact_url = reverse("dashboard:profile_contact")
        self.reauth_url = reverse("dashboard:reauth")
        self.staff = User.objects.create_user(
            username="quan_tri", email=STAFF_EMAIL, password=PASSWORD, is_staff=True,
            first_name="Tuấn", last_name="Trần",
        )

    def login(self):
        self.client.force_login(self.staff)

    def reauth(self, username="quan_tri", password=PASSWORD):
        return self.client.post(self.reauth_url, {"username": username, "password": password, "next": self.contact_url})

    def test_profile_never_sends_email_to_browser(self):
        self.login()
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, STAFF_EMAIL)
        self.assertNotContains(response, "quan.tri@")
        self.assertContains(response, "quan_tri")
        self.assertContains(response, "Trần")
        self.assertContains(response, self.contact_url)

    def test_profile_is_not_cached(self):
        self.login()
        self.assertIn("no-store", self.client.get(self.profile_url)["Cache-Control"])

    def test_customer_gets_403(self):
        customer = User.objects.create_user(username="khach", email="khach@example.test", password=PASSWORD, email_verified=True)
        self.client.force_login(customer)
        self.assertEqual(self.client.get(self.profile_url).status_code, 403)
        self.assertEqual(self.client.get(self.contact_url).status_code, 403)

    def test_contact_requires_reauth(self):
        self.login()
        response = self.client.get(self.contact_url)
        self.assertRedirects(response, f"{self.reauth_url}?next={self.contact_url}", fetch_redirect_response=False)
        self.assertFalse(SecurityEvent.objects.filter(event_type="sensitive_data_viewed").exists())

    def test_contact_shown_after_reauth_and_logged(self):
        self.login()
        response = self.reauth()
        self.assertRedirects(response, self.contact_url, fetch_redirect_response=False)
        response = self.client.get(self.contact_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, STAFF_EMAIL)
        self.assertIn("no-store", response["Cache-Control"])
        event = SecurityEvent.objects.get(event_type="sensitive_data_viewed")
        self.assertEqual(event.user_id, self.staff.pk)
        self.assertEqual(event.detail["fields"], ["email", "phone"])

    def test_plain_profile_stays_hidden_even_after_reauth(self):
        self.login()
        self.reauth()
        self.assertNotContains(self.client.get(self.profile_url), STAFF_EMAIL)

    def test_reauth_expires(self):
        self.login()
        self.reauth()
        later = time.time() + 121
        with mock.patch("core.decorators.time.time", return_value=later):
            response = self.client.get(self.contact_url)
        self.assertEqual(response.status_code, 302)

    def test_wrong_password_does_not_reveal(self):
        self.login()
        self.reauth(password=PASSWORD + "-sai")
        response = self.client.get(self.contact_url)
        self.assertEqual(response.status_code, 302)

    def test_reauth_as_other_staff_does_not_reveal(self):
        User.objects.create_user(username="nguoi_khac", email="khac@example.test", password=PASSWORD, is_staff=True)
        self.login()
        self.reauth(username="nguoi_khac")
        self.assertEqual(self.client.get(self.contact_url).status_code, 302)

    def test_reauth_page_shows_minutes_from_settings(self):
        self.login()
        response = self.client.get(self.reauth_url, {"next": self.contact_url})
        self.assertContains(response, "2 phút")
