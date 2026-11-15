import secrets
import time
from unittest import mock

from django.conf import settings
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from accounts.profile import decrypt_phone, encrypt_phone
from core.models import SecurityEvent

PASSWORD = secrets.token_urlsafe(12) + "-Aa9"
STAFF_EMAIL = "quan.tri@example.test"
OLD_PHONE = "0987654321"


# AI-TRACE#100 | Claude Opus 5.5 | Test nhân viên cập nhật họ, tên, SĐT: xác thực lại, không lộ SĐT cũ, để trống giữ số, chặn mass assignment | CẤM XÓA CHÚ THÍCH NÀY
class StaffProfileUpdateTests(TestCase):
    def setUp(self):
        cache.clear()
        self.saved_using = []
        original_save = User.save

        def save_on_default(instance, *args, **kwargs):
            self.saved_using.append(kwargs.get("using"))
            kwargs["using"] = "default"
            return original_save(instance, *args, **kwargs)

        patcher = mock.patch.object(User, "save", save_on_default)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.url = reverse("dashboard:profile_update")
        self.staff = User.objects.create_user(username="quan_tri", email=STAFF_EMAIL, password=PASSWORD,
                                              is_staff=True, first_name="Tuấn", last_name="Trần")
        self.staff.phone_encrypted = encrypt_phone(self.staff, OLD_PHONE)
        self.staff.save(update_fields=["phone_encrypted"])

    def reauth(self):
        self.client.force_login(self.staff)
        self.client.post(reverse("dashboard:reauth"), {"username": "quan_tri", "password": PASSWORD, "next": self.url})

    def fresh(self):
        return User.objects.get(pk=self.staff.pk)

    def post(self, **data):
        payload = {"last_name": "Trần", "first_name": "Tuấn", "phone": ""}
        payload.update(data)
        return self.client.post(self.url, payload)

    def test_profile_page_has_update_button(self):
        self.client.force_login(self.staff)
        self.assertContains(self.client.get(reverse("dashboard:profile")), self.url)

    def test_requires_staff(self):
        customer = User.objects.create_user(username="khach", email="khach@example.test", password=PASSWORD, email_verified=True)
        self.client.force_login(customer)
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_requires_recent_reauth(self):
        self.client.force_login(self.staff)
        response = self.client.get(self.url)
        self.assertRedirects(response, f"{reverse('dashboard:reauth')}?next={self.url.replace('/', '%2F')}",
                             fetch_redirect_response=False)

    def test_form_never_shows_current_phone_or_email(self):
        self.reauth()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, OLD_PHONE)
        self.assertNotContains(response, STAFF_EMAIL)
        self.assertContains(response, "Để trống nếu không đổi")
        self.assertContains(response, "Trần")
        self.assertIn("no-store", response["Cache-Control"])

    def test_update_names_and_phone(self):
        self.reauth()
        response = self.post(last_name="Nguyễn", first_name="Văn An", phone="091 234 5678")
        self.assertRedirects(response, reverse("dashboard:profile"))
        user = self.fresh()
        self.assertEqual((user.last_name, user.first_name), ("Nguyễn", "Văn An"))
        self.assertEqual(decrypt_phone(user), "0912345678")
        self.assertTrue(user.phone_encrypted.startswith("v1."))
        event = SecurityEvent.objects.get(event_type="profile_updated", user_id=self.staff.pk)
        self.assertEqual(sorted(event.detail["fields"]), ["first_name", "last_name", "phone_encrypted"])
        self.assertNotIn("0912345678", str(event.detail))
        self.assertEqual(self.saved_using[-1], "staff")

    def test_blank_phone_keeps_old_number(self):
        self.reauth()
        self.post(first_name="Minh")
        user = self.fresh()
        self.assertEqual(user.first_name, "Minh")
        self.assertEqual(decrypt_phone(user), OLD_PHONE)

    def test_no_change_writes_no_log(self):
        self.reauth()
        self.post()
        self.assertFalse(SecurityEvent.objects.filter(event_type="profile_updated").exists())

    def test_invalid_phone_is_rejected(self):
        self.reauth()
        response = self.post(phone="12345")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "10 chữ số")
        self.assertEqual(decrypt_phone(self.fresh()), OLD_PHONE)

    def test_extra_fields_are_ignored(self):
        self.reauth()
        self.post(email="hacker@example.test", username="khac", is_superuser="on", first_name="Minh")
        user = self.fresh()
        self.assertEqual((user.email, user.username, user.is_superuser), (STAFF_EMAIL, "quan_tri", False))

    def test_expired_reauth_blocks_post(self):
        self.reauth()
        later = time.time() + settings.REAUTH_MAX_AGE + 5
        with mock.patch("core.decorators.time.time", return_value=later):
            response = self.post(first_name="Minh")
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response["Location"].startswith(reverse("dashboard:reauth")))
        self.assertEqual(self.fresh().first_name, "Tuấn")
