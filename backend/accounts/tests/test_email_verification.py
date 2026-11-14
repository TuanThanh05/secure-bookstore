import re
import secrets
from unittest import mock

from axes.models import AccessAttempt
from django.core import mail, signing
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from accounts.models import User
from accounts.tokens import make_email_token
from core.models import SecurityEvent

PASSWORD = secrets.token_urlsafe(12) + "-Aa9"
LINK_RE = re.compile(r"https?://[^\s]+/account/xac-nhan-email/([^/\s]+)/")


# AI-TRACE#031 | Claude Opus 5.5 | Test luồng xác nhận email: đăng ký, xác nhận, gửi lại, chặn đăng nhập | CẤM XÓA CHÚ THÍCH NÀY
class EmailVerificationTests(TestCase):
    def setUp(self):
        cache.clear()
        self.register_url = reverse("accounts:register")
        self.login_url = reverse("accounts:login")
        self.resend_url = reverse("accounts:resend_verification")

    def register(self, username="an_nguyen", email="an@example.test", follow=False):
        return self.client.post(self.register_url, {
            "username": username, "email": email, "password1": PASSWORD, "password2": PASSWORD,
        }, follow=follow)

    def make_user(self, username, email, verified=False, staff=False):
        return User.objects.create_user(username=username, email=email, password=PASSWORD,
                                        email_verified=verified, is_staff=staff)

    def link_token(self, message):
        found = LINK_RE.search(message.body)
        self.assertIsNotNone(found, message.body)
        return found.group(1)

    def test_register_creates_unverified_user_and_sends_link(self):
        response = self.register()
        self.assertRedirects(response, reverse("accounts:check_email"))
        user = User.objects.get(username="an_nguyen")
        self.assertFalse(user.email_verified)
        self.assertTrue(user.is_active)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["an@example.test"])
        self.link_token(mail.outbox[0])
        self.assertTrue(SecurityEvent.objects.filter(event_type="email_sent", detail__kind="verify").exists())

    def test_existing_email_looks_identical_to_new_email(self):
        self.make_user("chu_cu", "an@example.test", verified=True)
        first = self.register(username="nguoi_moi", email="AN@Example.test", follow=True)
        cache.clear()
        second = self.register(username="nguoi_khac", email="khac@example.test", follow=True)
        self.assertEqual(first.redirect_chain, [(reverse("accounts:check_email"), 302)])
        self.assertEqual(first.redirect_chain, second.redirect_chain)
        self.assertEqual(first.content, second.content)
        self.assertFalse(User.objects.filter(username="nguoi_moi").exists())

    def test_existing_verified_email_gets_notice_without_link(self):
        self.make_user("chu_cu", "an@example.test", verified=True)
        self.register(username="nguoi_moi")
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["an@example.test"])
        self.assertIsNone(LINK_RE.search(mail.outbox[0].body))
        self.assertIn("chu_cu", mail.outbox[0].body)

    def test_existing_email_path_still_hashes_password(self):
        self.make_user("chu_cu", "an@example.test", verified=True)
        with mock.patch("accounts.services.make_password") as hashed:
            self.register(username="nguoi_moi")
        hashed.assert_called_once_with(PASSWORD)

    def test_existing_unverified_email_gets_new_link(self):
        self.make_user("chua_xac_nhan", "an@example.test")
        self.register(username="nguoi_moi")
        self.assertEqual(len(mail.outbox), 1)
        self.link_token(mail.outbox[0])

    def test_taken_username_is_still_reported(self):
        self.make_user("an_nguyen", "cu@example.test", verified=True)
        response = self.register(username="an_nguyen", email="moi@example.test")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tên đăng nhập này đã được sử dụng.")
        self.assertEqual(len(mail.outbox), 0)

    def test_get_does_not_verify_and_post_does(self):
        self.register()
        token = self.link_token(mail.outbox[0])
        url = reverse("accounts:verify_email", args=[token])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "an_nguyen")
        self.assertFalse(User.objects.get(username="an_nguyen").email_verified)
        response = self.client.post(url)
        self.assertRedirects(response, self.login_url)
        self.assertTrue(User.objects.get(username="an_nguyen").email_verified)
        self.assertTrue(SecurityEvent.objects.filter(event_type="email_verified").exists())

    def test_link_cannot_be_used_twice(self):
        self.register()
        url = reverse("accounts:verify_email", args=[self.link_token(mail.outbox[0])])
        self.client.post(url)
        response = self.client.post(url)
        self.assertEqual(response.status_code, 400)
        self.assertContains(response, "không còn hiệu lực", status_code=400)

    def test_expired_link_offers_resend(self):
        self.register()
        url = reverse("accounts:verify_email", args=[self.link_token(mail.outbox[0])])
        with mock.patch("django.core.signing.time.time", return_value=signing.time.time() + 301):
            response = self.client.get(url)
        self.assertEqual(response.status_code, 400)
        self.assertContains(response, "đã hết hạn", status_code=400)
        self.assertContains(response, self.resend_url, status_code=400)
        self.assertFalse(User.objects.get(username="an_nguyen").email_verified)

    def test_tampered_link_is_rejected(self):
        self.register()
        token = self.link_token(mail.outbox[0])
        tampered = token[:-1] + ("A" if token[-1] != "A" else "B")
        response = self.client.post(reverse("accounts:verify_email", args=[tampered]))
        self.assertEqual(response.status_code, 400)
        self.assertFalse(User.objects.get(username="an_nguyen").email_verified)
        self.assertTrue(SecurityEvent.objects.filter(event_type="email_verify_failed").exists())

    def test_link_stops_working_after_email_change(self):
        user = self.make_user("an_nguyen", "an@example.test")
        token = make_email_token(user)
        user.email = "moi@example.test"
        user.save()
        response = self.client.post(reverse("accounts:verify_email", args=[token]))
        self.assertEqual(response.status_code, 400)
        self.assertFalse(User.objects.get(pk=user.pk).email_verified)

    def test_link_does_not_reactivate_locked_account(self):
        user = self.make_user("bi_khoa", "khoa@example.test", verified=True)
        user.is_active = False
        user.save()
        response = self.client.post(reverse("accounts:verify_email", args=[make_email_token(user)]))
        self.assertEqual(response.status_code, 400)
        self.assertFalse(User.objects.get(pk=user.pk).is_active)

    def test_verify_post_requires_csrf(self):
        self.register()
        url = reverse("accounts:verify_email", args=[self.link_token(mail.outbox[0])])
        response = Client(enforce_csrf_checks=True).post(url)
        self.assertEqual(response.status_code, 403)
        self.assertFalse(User.objects.get(username="an_nguyen").email_verified)

    def test_unverified_customer_cannot_log_in_and_is_not_counted_by_axes(self):
        self.make_user("an_nguyen", "an@example.test")
        response = self.client.post(self.login_url, {"username": "an_nguyen", "password": PASSWORD})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "chưa được xác nhận")
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(AccessAttempt.objects.count(), 0)
        self.assertTrue(SecurityEvent.objects.filter(event_type="login_blocked_unverified").exists())

    def test_wrong_password_on_unverified_account_shows_generic_error(self):
        self.make_user("an_nguyen", "an@example.test")
        response = self.client.post(self.login_url, {"username": "an_nguyen", "password": PASSWORD + "-sai"})
        self.assertContains(response, "Tên đăng nhập hoặc mật khẩu không đúng.")
        self.assertNotContains(response, "chưa được xác nhận")

    def test_verified_customer_and_unverified_staff_can_log_in(self):
        self.make_user("da_xac_nhan", "ok@example.test", verified=True)
        self.make_user("nhan_vien", "staff@example.test", staff=True)
        for username in ("da_xac_nhan", "nhan_vien"):
            with self.subTest(username=username):
                client = Client()
                response = client.post(self.login_url, {"username": username, "password": PASSWORD})
                self.assertEqual(response.status_code, 302)
                self.assertIn("_auth_user_id", client.session)

    def test_resend_gives_same_answer_for_every_email(self):
        self.make_user("chua_xac_nhan", "cho@example.test")
        self.make_user("da_xac_nhan", "ok@example.test", verified=True)
        responses = [
            self.client.post(self.resend_url, {"email": email}, follow=True)
            for email in ("cho@example.test", "ok@example.test", "khong-co@example.test")
        ]
        contents = {r.content for r in responses}
        self.assertEqual(len(contents), 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["cho@example.test"])

    def test_resend_is_rate_limited_per_address(self):
        self.make_user("chua_xac_nhan", "cho@example.test")
        self.client.post(self.resend_url, {"email": "cho@example.test"})
        self.client.post(self.resend_url, {"email": "CHO@example.test"})
        self.assertEqual(len(mail.outbox), 1)
        self.assertTrue(SecurityEvent.objects.filter(event_type="rate_limited").exists())

    def test_smtp_failure_is_logged_not_shown(self):
        with mock.patch("accounts.emails.send_mail", side_effect=OSError("smtp down")):
            response = self.register(follow=True)
        self.assertEqual(response.redirect_chain, [(reverse("accounts:check_email"), 302)])
        self.assertTrue(SecurityEvent.objects.filter(event_type="email_send_failed").exists())

    def test_forged_host_header_is_rejected(self):
        response = self.client.post(self.register_url, {
            "username": "an_nguyen", "email": "an@example.test", "password1": PASSWORD, "password2": PASSWORD,
        }, HTTP_HOST="evil.example")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(len(mail.outbox), 0)

    def test_get_to_register_does_not_send_mail(self):
        self.client.get(self.register_url)
        self.client.get(self.resend_url)
        self.assertEqual(len(mail.outbox), 0)
