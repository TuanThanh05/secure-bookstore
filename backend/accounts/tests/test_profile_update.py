import base64
import secrets
import time
from unittest import mock

from django.test import Client, TestCase, override_settings
from django.urls import reverse

from accounts.models import User
from accounts.profile import decrypt_phone, encrypt_phone
from core.models import SecurityEvent

PASSWORD = secrets.token_urlsafe(12) + "-Aa9"
TEST_KEY = base64.b64encode(secrets.token_bytes(32)).decode()


# AI-TRACE#083 | Claude Opus 5.5 | Test xác thực lại của khách và cập nhật họ, tên, SĐT mã hóa | CẤM XÓA CHÚ THÍCH NÀY
@override_settings(FIELD_ENCRYPTION_KEY=TEST_KEY)
class ProfileUpdateTests(TestCase):
    def setUp(self):
        self.update_url = reverse("accounts:profile_update")
        self.reauth_url = reverse("accounts:reauth")
        self.user = User.objects.create_user(username="an_nguyen", email="an@example.test", password=PASSWORD,
                                             email_verified=True, first_name="An", last_name="Nguyễn")
        self.client.force_login(self.user)

    def reauth(self, username="an_nguyen", password=PASSWORD, client=None):
        return (client or self.client).post(self.reauth_url, {"username": username, "password": password, "next": self.update_url})

    def update(self, **data):
        payload = {"last_name": "Trần", "first_name": "Bình", "phone": "0912 345 678"}
        payload.update(data)
        return self.client.post(self.update_url, payload)

    def fresh(self):
        return User.objects.get(pk=self.user.pk)

    def test_profile_has_update_button(self):
        self.assertContains(self.client.get(reverse("accounts:profile")), self.update_url)

    def test_update_requires_reauth(self):
        response = self.client.get(self.update_url)
        self.assertRedirects(response, f"{self.reauth_url}?next={self.update_url}", fetch_redirect_response=False)

    def test_reauth_page_has_forgot_password_link(self):
        response = self.client.get(self.reauth_url, {"next": self.update_url})
        self.assertContains(response, reverse("accounts:password_reset"))
        self.assertContains(response, "Xác thực")

    def test_reauth_then_update_saves_encrypted_phone(self):
        self.assertRedirects(self.reauth(), self.update_url, fetch_redirect_response=False)
        response = self.update()
        self.assertRedirects(response, reverse("accounts:profile"))
        user = self.fresh()
        self.assertEqual((user.last_name, user.first_name), ("Trần", "Bình"))
        self.assertTrue(user.phone_encrypted.startswith("v1."))
        self.assertNotIn("0912345678", user.phone_encrypted)
        self.assertEqual(decrypt_phone(user), "0912345678")
        event = SecurityEvent.objects.get(event_type="profile_updated")
        self.assertEqual(sorted(event.detail["fields"]), ["first_name", "last_name", "phone_encrypted"])
        self.assertNotIn("0912345678", str(event.detail))
        self.assertContains(self.client.get(reverse("accounts:profile")), "0912345678")

    def test_reauth_by_email_works(self):
        self.assertRedirects(self.reauth(username="AN@example.test"), self.update_url, fetch_redirect_response=False)

    def test_international_prefix_is_normalized(self):
        self.reauth()
        self.update(phone="+84 912.345.678")
        self.assertEqual(decrypt_phone(self.fresh()), "0912345678")

    def test_empty_phone_clears_column(self):
        self.user.phone_encrypted = encrypt_phone(self.user, "0912345678")
        self.user.save()
        self.reauth()
        self.update(phone="")
        self.assertIsNone(self.fresh().phone_encrypted)

    def test_invalid_input_rejected(self):
        self.reauth()
        cases = [
            {"phone": "12345"}, {"phone": "0112345678"}, {"phone": "09123456789"}, {"phone": "<script>"},
            {"first_name": "Bình1"}, {"last_name": "<b>Trần</b>"}, {"first_name": "a" * 51},
        ]
        for data in cases:
            with self.subTest(data=data):
                response = self.update(**data)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(self.fresh().first_name, "An")

    def test_extra_fields_are_ignored(self):
        self.reauth()
        self.update(username="hacker", email="hacker@example.test", is_staff="1", email_verified="0")
        user = self.fresh()
        self.assertEqual((user.username, user.email, user.is_staff, user.email_verified),
                         ("an_nguyen", "an@example.test", False, True))

    def test_no_change_does_not_write_or_log(self):
        self.reauth()
        self.update(last_name="Nguyễn", first_name="An", phone="")
        self.assertFalse(SecurityEvent.objects.filter(event_type="profile_updated").exists())

    def test_wrong_password_does_not_unlock(self):
        response = self.reauth(password=PASSWORD + "-sai")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.get(self.update_url).status_code, 302)

    def test_other_users_credentials_do_not_unlock(self):
        User.objects.create_user(username="binh", email="binh@example.test", password=PASSWORD, email_verified=True)
        self.reauth(username="binh")
        self.assertEqual(self.client.get(self.update_url).status_code, 302)
        self.assertTrue(SecurityEvent.objects.filter(event_type="access_denied", detail__step_up="user_mismatch").exists())

    def test_reauth_expires(self):
        self.reauth()
        with mock.patch("core.decorators.time.time", return_value=time.time() + 121):
            self.assertEqual(self.client.get(self.update_url).status_code, 302)

    def test_post_after_expiry_is_not_saved(self):
        self.reauth()
        with mock.patch("core.decorators.time.time", return_value=time.time() + 121):
            response = self.update()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.fresh().first_name, "An")

    def test_next_cannot_leave_site(self):
        response = self.client.post(self.reauth_url, {"username": "an_nguyen", "password": PASSWORD,
                                                      "next": "https://evil.example/"})
        self.assertRedirects(response, reverse("accounts:profile"))

    def test_staff_cannot_use_customer_pages(self):
        staff = User.objects.create_user(username="quan_tri", email="admin@example.test", password=PASSWORD, is_staff=True)
        client = Client()
        client.force_login(staff)
        self.assertRedirects(client.get(self.reauth_url), reverse("dashboard:profile"))
        self.assertRedirects(client.get(self.update_url), reverse("dashboard:profile"))

    def test_pages_are_not_cached_and_need_csrf(self):
        self.reauth()
        self.assertIn("no-store", self.client.get(self.update_url)["Cache-Control"])
        self.assertIn("no-store", self.client.get(self.reauth_url)["Cache-Control"])
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.user)
        self.assertEqual(self.reauth(client=csrf_client).status_code, 403)

    def test_unreadable_phone_does_not_break_profile(self):
        self.user.phone_encrypted = "v1.khong-giai-ma-duoc"
        self.user.save()
        response = self.client.get(reverse("accounts:profile"))
        self.assertContains(response, "Không đọc được")
