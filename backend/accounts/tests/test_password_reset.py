import re
import secrets
import time
from unittest import mock

from axes.models import AccessAttempt
from django.core import mail
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from accounts.models import User
from core.models import SecurityEvent

PASSWORD = secrets.token_urlsafe(12) + "-Aa9"
NEW_PASSWORD = secrets.token_urlsafe(12) + "-Bb8"
WEAK = "1234" * 2
LINK_RE = re.compile(r"https?://[^\s]+(/account/dat-lai-mat-khau/[^/\s]+/[^/\s]+/)")


# AI-TRACE#056 | Claude Opus 5.5 | Test luồng quên mật khẩu: gửi link, đặt lại, link hết hạn, chặn nhân viên | CẤM XÓA CHÚ THÍCH NÀY
class PasswordResetTests(TestCase):
    def setUp(self):
        cache.clear()
        self.reset_url = reverse("accounts:password_reset")
        self.login_url = reverse("accounts:login")
        self.customer = User.objects.create_user(username="an_nguyen", email="an@example.test",
                                                 password=PASSWORD, email_verified=True)

    def request_reset(self, email="an@example.test", client=None):
        return (client or self.client).post(self.reset_url, {"email": email}, follow=True)

    def link_path(self):
        found = LINK_RE.search(mail.outbox[-1].body)
        self.assertIsNotNone(found, mail.outbox[-1].body)
        return found.group(1)

    def set_new_password(self, path, password=NEW_PASSWORD):
        response = self.client.get(path, follow=True)
        set_url = response.redirect_chain[-1][0] if response.redirect_chain else path
        return self.client.post(set_url, {"new_password1": password, "new_password2": password})

    def test_login_page_links_to_reset(self):
        self.assertContains(self.client.get(self.login_url), self.reset_url)

    def test_customer_gets_link_and_same_page_as_unknown_email(self):
        known = self.request_reset()
        cache.clear()
        unknown = self.request_reset("khong-co@example.test")
        self.assertEqual(known.redirect_chain, [(reverse("accounts:password_reset_done"), 302)])
        self.assertEqual(known.content, unknown.content)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["an@example.test"])
        self.assertIn("5 phút", mail.outbox[0].body)
        self.assertTrue(SecurityEvent.objects.filter(event_type="password_reset_requested", detail__matched=True).exists())
        self.assertTrue(SecurityEvent.objects.filter(event_type="password_reset_requested", detail__matched=False).exists())

    def test_staff_never_receives_reset_link(self):
        User.objects.create_user(username="quan_tri", email="admin@example.test", password=PASSWORD, is_staff=True)
        self.request_reset("admin@example.test")
        self.assertEqual(len(mail.outbox), 0)

    def test_reset_changes_password_and_token_is_hidden_from_url(self):
        self.request_reset()
        path = self.link_path()
        response = self.client.get(path)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response["Location"].endswith("/set-password/"))
        response = self.set_new_password(path)
        self.assertRedirects(response, self.login_url)
        user = User.objects.get(pk=self.customer.pk)
        self.assertTrue(user.check_password(NEW_PASSWORD))
        self.assertFalse(user.check_password(PASSWORD))
        self.assertTrue(SecurityEvent.objects.filter(event_type="password_changed", detail__via="reset").exists())

    def test_link_works_only_once(self):
        self.request_reset()
        path = self.link_path()
        self.set_new_password(path)
        response = self.client.get(path, follow=True)
        self.assertContains(response, "không hợp lệ")
        self.assertFalse(response.context["validlink"])

    def test_link_expires_after_five_minutes(self):
        self.request_reset()
        path = self.link_path()
        later = time.time() + 5 * 60 + 5
        with mock.patch("django.contrib.auth.tokens.PasswordResetTokenGenerator._now") as now:
            from datetime import datetime
            now.return_value = datetime.fromtimestamp(later)
            response = self.client.get(path, follow=True)
        self.assertFalse(response.context["validlink"])
        self.assertTrue(SecurityEvent.objects.filter(event_type="invalid_input", detail__kind="password_reset_link").exists())

    def test_tampered_link_is_rejected(self):
        self.request_reset()
        path = self.link_path()
        tampered = path[:-2] + ("a" if path[-2] != "a" else "b") + "/"
        response = self.client.get(tampered, follow=True)
        self.assertFalse(response.context["validlink"])

    def test_weak_password_is_rejected(self):
        self.request_reset()
        response = self.set_new_password(self.link_path(), WEAK)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(User.objects.get(pk=self.customer.pk).check_password(PASSWORD))

    def test_reset_confirms_email_and_unlocks_axes(self):
        self.customer.email_verified = False
        self.customer.save()
        for _ in range(5):
            Client().post(self.login_url, {"username": "an_nguyen", "password": PASSWORD + "-sai"})
        self.assertTrue(AccessAttempt.objects.filter(username="an_nguyen").exists())
        self.request_reset()
        self.set_new_password(self.link_path())
        self.assertTrue(User.objects.get(pk=self.customer.pk).email_verified)
        self.assertFalse(AccessAttempt.objects.filter(username="an_nguyen").exists())
        response = Client().post(self.login_url, {"username": "an_nguyen", "password": NEW_PASSWORD})
        self.assertEqual(response.status_code, 302)

    def test_reset_sends_notice_and_logs_out_other_sessions(self):
        other = Client()
        other.force_login(self.customer)
        self.assertEqual(other.get(reverse("accounts:profile")).status_code, 200)
        self.request_reset()
        self.set_new_password(self.link_path())
        self.assertEqual(mail.outbox[-1].to, ["an@example.test"])
        self.assertIn("vừa được đặt lại", mail.outbox[-1].body)
        self.assertEqual(other.get(reverse("accounts:profile")).status_code, 302)

    def test_reset_requests_are_rate_limited(self):
        self.request_reset()
        self.request_reset("AN@example.test")
        self.assertEqual(len(mail.outbox), 1)
        self.assertTrue(SecurityEvent.objects.filter(event_type="rate_limited", detail__kind="password_reset").exists())

    def test_reset_limit_is_separate_from_verification_limit(self):
        self.customer.email_verified = False
        self.customer.save()
        self.client.post(reverse("accounts:resend_verification"), {"email": "an@example.test"})
        self.request_reset()
        self.assertEqual(len(mail.outbox), 2)

    def test_staff_reset_link_is_rejected_even_if_token_valid(self):
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode
        staff = User.objects.create_user(username="quan_tri", email="admin@example.test", password=PASSWORD, is_staff=True)
        path = reverse("accounts:password_reset_confirm",
                       args=[urlsafe_base64_encode(force_bytes(staff.pk)), default_token_generator.make_token(staff)])
        response = self.client.get(path, follow=True)
        self.assertFalse(response.context["validlink"])
