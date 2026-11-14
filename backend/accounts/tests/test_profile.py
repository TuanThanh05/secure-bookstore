import secrets

from django.test import TestCase
from django.urls import reverse

from accounts.models import User

PASSWORD = secrets.token_urlsafe(12) + "-Aa9"


# AI-TRACE#045 | Claude Opus 5.5 | Test trang thông tin của khách: hiện email, chặn nhân viên, không lưu cache | CẤM XÓA CHÚ THÍCH NÀY
class CustomerProfileTests(TestCase):
    def setUp(self):
        self.url = reverse("accounts:profile")
        self.customer = User.objects.create_user(
            username="an_nguyen", email="an@example.test", password=PASSWORD,
            first_name="An", last_name="Nguyễn", email_verified=True,
        )

    def test_anonymous_is_sent_to_login(self):
        response = self.client.get(self.url)
        self.assertRedirects(response, f"{reverse('accounts:login')}?next={self.url}")

    def test_customer_sees_own_contact_and_names(self):
        self.client.force_login(self.customer)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        for text in ("an_nguyen", "an@example.test", "An", "Nguyễn", "Chưa cập nhật"):
            self.assertContains(response, text)

    def test_customer_page_is_not_cached(self):
        self.client.force_login(self.customer)
        response = self.client.get(self.url)
        self.assertIn("no-store", response["Cache-Control"])

    def test_staff_is_redirected_to_dashboard_profile(self):
        staff = User.objects.create_user(username="nhan_vien", email="staff@example.test", password=PASSWORD, is_staff=True)
        self.client.force_login(staff)
        response = self.client.get(self.url)
        self.assertRedirects(response, reverse("dashboard:profile"))

    def test_post_is_not_allowed(self):
        self.client.force_login(self.customer)
        self.assertEqual(self.client.post(self.url).status_code, 405)
