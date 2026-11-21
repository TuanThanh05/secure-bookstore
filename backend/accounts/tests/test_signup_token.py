from unittest import mock

from django.core import signing
from django.test import SimpleTestCase, override_settings

from accounts.tokens import SIGNUP_SIGNING_SALT, make_signup_token, read_signup_token


class SignupTokenTests(SimpleTestCase):
    def test_valid_token_returns_email(self):
        result = read_signup_token(make_signup_token("an@example.test"))
        self.assertEqual(result.status, "valid")
        self.assertEqual(result.email, "an@example.test")

    def test_token_expires_after_five_minutes(self):
        token = make_signup_token("an@example.test")
        with mock.patch("django.core.signing.time.time", return_value=signing.time.time() + 301):
            self.assertEqual(read_signup_token(token).status, "expired")

    @override_settings(SIGNUP_LINK_MAX_AGE=600)
    def test_max_age_comes_from_settings(self):
        token = make_signup_token("an@example.test")
        with mock.patch("django.core.signing.time.time", return_value=signing.time.time() + 301):
            self.assertEqual(read_signup_token(token).status, "valid")

    def test_tampered_token_is_invalid(self):
        token = make_signup_token("an@example.test")
        tampered = token[:-1] + ("A" if token[-1] != "A" else "B")
        self.assertEqual(read_signup_token(tampered).status, "invalid")

    def test_forged_payload_without_secret_is_invalid(self):
        forged = signing.dumps({"e": "nannhan@example.test"}, key="khong-phai-secret-key", salt=SIGNUP_SIGNING_SALT)
        self.assertEqual(read_signup_token(forged).status, "invalid")

    def test_token_signed_for_other_purpose_is_invalid(self):
        other = signing.dumps({"e": "an@example.test"}, salt="accounts.email-verification")
        self.assertEqual(read_signup_token(other).status, "invalid")

    def test_garbage_and_wrong_shape_are_invalid(self):
        self.assertEqual(read_signup_token("").status, "invalid")
        self.assertEqual(read_signup_token("abc:def:ghi").status, "invalid")
        for payload in (["e", "an@example.test"], {"e": 1}, {"e": ""}, {"e": "a" * 255},
                        {"e": "an@example.test", "u": 1}):
            with self.subTest(payload=payload):
                token = signing.dumps(payload, salt=SIGNUP_SIGNING_SALT)
                self.assertEqual(read_signup_token(token).status, "invalid")

    def test_token_is_url_safe(self):
        self.assertRegex(make_signup_token("an@example.test"), r"^[A-Za-z0-9_:\-]+$")
