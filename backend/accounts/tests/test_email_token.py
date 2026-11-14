from types import SimpleNamespace
from unittest import mock

from django.core import signing
from django.test import SimpleTestCase, override_settings

from accounts.tokens import EMAIL_SIGNING_SALT, make_email_token, read_email_token

USER = SimpleNamespace(pk=7, email="an@example.test")


# AI-TRACE#011 | Claude Opus 5.5 | Test tạo và kiểm tra mã xác nhận email: hợp lệ, hết hạn, bị sửa | CẤM XÓA CHÚ THÍCH NÀY
class EmailTokenTests(SimpleTestCase):
    def test_valid_token_returns_user_and_email(self):
        result = read_email_token(make_email_token(USER))
        self.assertEqual(result.status, "valid")
        self.assertEqual(result.user_id, 7)
        self.assertEqual(result.email, "an@example.test")

    def test_token_expires_after_max_age(self):
        token = make_email_token(USER)
        with mock.patch("django.core.signing.time.time", return_value=signing.time.time() + 301):
            self.assertEqual(read_email_token(token).status, "expired")

    @override_settings(EMAIL_VERIFY_MAX_AGE=600)
    def test_max_age_comes_from_settings(self):
        token = make_email_token(USER)
        with mock.patch("django.core.signing.time.time", return_value=signing.time.time() + 301):
            self.assertEqual(read_email_token(token).status, "valid")

    def test_tampered_token_is_invalid(self):
        token = make_email_token(USER)
        tampered = token[:-1] + ("A" if token[-1] != "A" else "B")
        self.assertEqual(read_email_token(tampered).status, "invalid")

    def test_forged_payload_without_secret_is_invalid(self):
        forged = signing.dumps({"u": 1, "e": "admin@example.test"}, key="khong-phai-secret-key", salt=EMAIL_SIGNING_SALT)
        self.assertEqual(read_email_token(forged).status, "invalid")

    def test_token_signed_for_other_purpose_is_invalid(self):
        other = signing.dumps({"u": 7, "e": "an@example.test"}, salt="accounts.password-reset")
        self.assertEqual(read_email_token(other).status, "invalid")

    def test_garbage_and_wrong_shape_are_invalid(self):
        self.assertEqual(read_email_token("").status, "invalid")
        self.assertEqual(read_email_token("abc:def:ghi").status, "invalid")
        wrong = signing.dumps(["u", 7], salt=EMAIL_SIGNING_SALT)
        self.assertEqual(read_email_token(wrong).status, "invalid")
        bad_types = signing.dumps({"u": "7", "e": 1}, salt=EMAIL_SIGNING_SALT)
        self.assertEqual(read_email_token(bad_types).status, "invalid")

    def test_token_is_url_safe(self):
        token = make_email_token(USER)
        self.assertRegex(token, r"^[A-Za-z0-9_:\-]+$")
