import json
import secrets
from unittest import mock

from django.core import mail
from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from accounts.models import User
from core.captcha import NO_CAPTCHA
from core.models import SecurityEvent

SITE_KEY = "0x4AAAA" + secrets.token_hex(8)
SECRET = "0x4AAAA" + secrets.token_hex(16)
TOKEN = "tok-" + secrets.token_urlsafe(40)
TURNSTILE = "https://challenges.cloudflare.com"


def cloudflare(payload):
    response = mock.MagicMock()
    response.read.return_value = json.dumps(payload).encode()
    response.__enter__.return_value = response
    return response


PASS = {"success": True, "hostname": "testserver", "action": "signup", "error-codes": []}


@override_settings(TURNSTILE_SITE_KEY=SITE_KEY, TURNSTILE_SECRET_KEY=SECRET)
class SignupCaptchaTests(TestCase):
    def setUp(self):
        cache.clear()
        self.url = reverse("accounts:register")

    def start(self, email="an@example.test", token=TOKEN, payload=PASS, side_effect=None, client=None):
        data = {"email": email}
        if token is not None:
            data["cf-turnstile-response"] = token
        with mock.patch("core.captcha.urllib.request.urlopen",
                        return_value=cloudflare(payload), side_effect=side_effect) as opened:
            response = (client or self.client).post(self.url, data)
        return response, opened

    def test_page_shows_widget_and_relaxes_csp_only_here(self):
        response = self.client.get(self.url)
        self.assertContains(response, 'class="cf-turnstile"')
        self.assertContains(response, f'data-sitekey="{SITE_KEY}"')
        self.assertContains(response, 'data-action="signup"')
        self.assertContains(response, f'<script src="{TURNSTILE}/turnstile/v0/api.js" async defer></script>', html=False)
        self.assertNotContains(response, SECRET)
        csp = response.headers["Content-Security-Policy"]
        self.assertIn(f"script-src 'self' {TURNSTILE}", csp)
        self.assertIn(f"frame-src {TURNSTILE}", csp)
        self.assertIn("frame-ancestors 'none'", csp)
        for other in (reverse("accounts:login"), reverse("accounts:check_email"), reverse("accounts:signup_complete")):
            with self.subTest(other=other):
                self.assertNotIn(TURNSTILE, self.client.get(other).headers["Content-Security-Policy"])

    def test_valid_captcha_continues_to_send_link(self):
        response, opened = self.start()
        self.assertRedirects(response, reverse("accounts:check_email"))
        opened.assert_called_once()
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(User.objects.count(), 0)

    def test_missing_token_blocks_mail(self):
        response, opened = self.start(token=None)
        self.assertContains(response, "Chưa xác minh được bạn không phải robot", status_code=400)
        opened.assert_not_called()
        self.assertEqual(len(mail.outbox), 0)
        self.assertTrue(SecurityEvent.objects.filter(event_type="captcha_failed", detail__reason="missing").exists())

    def test_invalid_or_reused_token_blocks_mail(self):
        for codes in (["invalid-input-response"], ["timeout-or-duplicate"]):
            with self.subTest(codes=codes):
                response, _ = self.start(payload={"success": False, "error-codes": codes})
                self.assertEqual(response.status_code, 400)
        self.assertEqual(len(mail.outbox), 0)

    def test_wrong_hostname_or_action_blocks_mail(self):
        for payload in ({**PASS, "hostname": "evil.example"}, {**PASS, "action": "login"}):
            with self.subTest(payload=payload):
                response, _ = self.start(payload=payload)
                self.assertEqual(response.status_code, 400)
        self.assertEqual(len(mail.outbox), 0)

    def test_cloudflare_down_blocks_mail(self):
        response, _ = self.start(side_effect=TimeoutError())
        self.assertContains(response, "Hệ thống xác minh đang gặp sự cố", status_code=503)
        self.assertEqual(len(mail.outbox), 0)
        self.assertTrue(SecurityEvent.objects.filter(event_type="captcha_failed", detail__reason="unavailable").exists())

    def test_ip_limit_is_checked_before_calling_cloudflare(self):
        for number in range(5):
            self.start(f"user{number}@example.test")
        response, opened = self.start("user5@example.test")
        self.assertEqual(response.status_code, 429)
        opened.assert_not_called()
        self.assertEqual(len(mail.outbox), 5)

    @override_settings(EMAIL_RESEND_INTERVAL=0)
    def test_valid_captcha_still_obeys_mailbox_limit(self):
        for number in range(6):
            response, _ = self.start(client=Client(REMOTE_ADDR=f"10.0.0.{number}"))
            self.assertRedirects(response, reverse("accounts:check_email"))
        self.assertEqual(len(mail.outbox), 5)
        self.assertTrue(SecurityEvent.objects.filter(event_type="rate_limited", detail__kind="signup_email").exists())

    def test_invalid_email_does_not_call_cloudflare(self):
        response, opened = self.start(email="khong-phai-email")
        self.assertEqual(response.status_code, 200)
        opened.assert_not_called()

    def test_csrf_is_still_required(self):
        client = Client(enforce_csrf_checks=True)
        response, opened = self.start(client=client)
        self.assertEqual(response.status_code, 403)
        opened.assert_not_called()


@override_settings(**NO_CAPTCHA)
class SignupWithoutCaptchaTests(TestCase):
    def test_page_has_no_widget_or_script_when_disabled(self):
        response = Client().get(reverse("accounts:register"))
        self.assertNotContains(response, "cf-turnstile")
        self.assertNotContains(response, "api.js")
