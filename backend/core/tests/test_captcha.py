import json
import secrets
import socket
import urllib.error
import urllib.parse
from unittest import mock

from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings

from core import captcha
from core.models import SecurityEvent

REAL_SITE_KEY = "0x4AAAA" + secrets.token_hex(8)
REAL_SECRET = "0x4AAAA" + secrets.token_hex(16)
DUMMY_PASS_SECRET = "1x" + "0" * 31 + "AA"
TOKEN = "tok-" + secrets.token_urlsafe(40)
ENABLED = override_settings(TURNSTILE_SITE_KEY=REAL_SITE_KEY, TURNSTILE_SECRET_KEY=REAL_SECRET,
                            ALLOWED_HOSTS=["shop.example.test", "testserver"])


def cloudflare(payload):
    response = mock.MagicMock()
    response.read.return_value = json.dumps(payload).encode()
    response.__enter__.return_value = response
    return response


def good(**extra):
    return {"success": True, "hostname": "shop.example.test", "action": "signup", "error-codes": [], **extra}


@ENABLED
class VerifyCaptchaTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def post(self, token=TOKEN, host="shop.example.test"):
        data = {captcha.RESPONSE_FIELD: token} if token is not None else {}
        return self.factory.post("/account/register/", data, HTTP_HOST=host, REMOTE_ADDR="203.0.113.7")

    def verify(self, payload=None, side_effect=None, **kwargs):
        with mock.patch("core.captcha.urllib.request.urlopen",
                        return_value=cloudflare(payload or good()), side_effect=side_effect) as opened:
            result = captcha.verify_captcha(self.post(**kwargs), "signup")
        return result, opened

    def last_event(self):
        return SecurityEvent.objects.filter(event_type="captcha_failed").latest("id")

    def test_valid_token_passes_and_sends_secret_token_ip_over_https(self):
        result, opened = self.verify()
        self.assertEqual(result, captcha.CaptchaResult(True, "verified"))
        request = opened.call_args.args[0]
        self.assertEqual(request.full_url, "https://challenges.cloudflare.com/turnstile/v0/siteverify")
        self.assertEqual(request.get_method(), "POST")
        body = urllib.parse.parse_qs(request.data.decode())
        self.assertEqual(body, {"secret": [REAL_SECRET], "response": [TOKEN], "remoteip": ["203.0.113.7"]})
        self.assertEqual(opened.call_args.kwargs["timeout"], 5)
        self.assertFalse(SecurityEvent.objects.filter(event_type="captcha_failed").exists())

    def test_missing_token_is_rejected_without_calling_cloudflare(self):
        result, opened = self.verify(token=None)
        self.assertEqual(result.reason, "missing")
        opened.assert_not_called()
        self.assertEqual(self.last_event().detail["reason"], "missing")

    def test_oversized_token_is_rejected_without_calling_cloudflare(self):
        result, opened = self.verify(token="x" * 2049)
        self.assertEqual(result.reason, "invalid")
        opened.assert_not_called()

    def test_forged_or_invalid_token_is_rejected(self):
        result, _ = self.verify({"success": False, "error-codes": ["invalid-input-response"]})
        self.assertEqual(result, captcha.CaptchaResult(False, "rejected", ("invalid-input-response",)))
        self.assertEqual(self.last_event().detail["codes"], ["invalid-input-response"])

    def test_expired_or_reused_token_is_rejected(self):
        result, _ = self.verify({"success": False, "error-codes": ["timeout-or-duplicate"]})
        self.assertFalse(result.ok)
        self.assertEqual(result.codes, ("timeout-or-duplicate",))

    def test_success_must_be_exactly_true(self):
        for value in ("true", 1, None):
            with self.subTest(value=value):
                result, _ = self.verify(good(success=value))
                self.assertEqual(result.reason, "rejected")

    def test_hostname_mismatch_is_rejected(self):
        result, _ = self.verify(good(hostname="evil.example"))
        self.assertEqual(result.reason, "hostname_mismatch")

    def test_hostname_is_compared_without_port(self):
        result, _ = self.verify(host="shop.example.test:8000")
        self.assertTrue(result.ok)

    def test_action_mismatch_is_rejected(self):
        for action in ("login", "", None):
            with self.subTest(action=action):
                result, _ = self.verify(good(action=action))
                self.assertEqual(result.reason, "action_mismatch")

    def test_cloudflare_timeout_or_outage_does_not_skip_captcha(self):
        for error in (TimeoutError(), socket.timeout(), urllib.error.URLError("down"), ConnectionResetError()):
            with self.subTest(error=type(error).__name__):
                result, _ = self.verify(side_effect=error)
                self.assertEqual(result, captcha.CaptchaResult(False, "unavailable"))
        self.assertEqual(self.last_event().detail["reason"], "unavailable")

    def test_garbage_response_counts_as_unavailable(self):
        broken = cloudflare({})
        broken.read.return_value = b"<html>bad gateway</html>"
        with mock.patch("core.captcha.urllib.request.urlopen", return_value=broken):
            self.assertEqual(captcha.verify_captcha(self.post(), "signup").reason, "unavailable")
        with mock.patch("core.captcha.urllib.request.urlopen", return_value=cloudflare(["not", "a", "dict"])):
            self.assertEqual(captcha.verify_captcha(self.post(), "signup").reason, "unavailable")

    def test_strange_error_codes_are_not_logged(self):
        codes = ["timeout-or-duplicate", "<script>", "x" * 80, 7]
        result, _ = self.verify({"success": False, "error-codes": codes})
        self.assertEqual(result.codes, ("timeout-or-duplicate",))

    def test_log_never_contains_token_or_secret(self):
        self.verify({"success": False, "error-codes": ["invalid-input-response"]})
        self.verify(token=None)
        stored = json.dumps(list(SecurityEvent.objects.values("detail", "path", "user_agent")), default=str)
        self.assertNotIn(TOKEN, stored)
        self.assertNotIn(REAL_SECRET, stored)

    @override_settings(TURNSTILE_SECRET_KEY=DUMMY_PASS_SECRET)
    def test_test_secret_skips_hostname_and_action_checks(self):
        result, _ = self.verify({"success": True, "hostname": "example.com", "action": ""})
        self.assertEqual(result, captcha.CaptchaResult(True, "test_key"))

    @override_settings(**captcha.NO_CAPTCHA)
    def test_disabled_captcha_passes_without_network(self):
        result, opened = self.verify(token=None)
        self.assertEqual(result, captcha.CaptchaResult(True, "disabled"))
        opened.assert_not_called()


class TurnstileCheckTests(SimpleTestCase):
    @override_settings(**captcha.NO_CAPTCHA)
    def test_warns_when_disabled(self):
        self.assertEqual([w.id for w in captcha.check_turnstile()], ["core.W001"])

    @override_settings(TURNSTILE_SITE_KEY="1x00000000000000000000AA", TURNSTILE_SECRET_KEY=DUMMY_PASS_SECRET)
    def test_warns_when_using_test_keys(self):
        self.assertEqual([w.id for w in captcha.check_turnstile()], ["core.W002"])

    @ENABLED
    def test_silent_with_real_keys(self):
        self.assertEqual(captcha.check_turnstile(), [])
        self.assertEqual(captcha.captcha_site_key(), REAL_SITE_KEY)

    def test_only_https_endpoint_is_used(self):
        self.assertTrue(captcha.SITEVERIFY_URL.startswith("https://challenges.cloudflare.com/"))
