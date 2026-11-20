import secrets

from django.test import RequestFactory, TestCase, override_settings

from core.models import SecurityEvent
from core.security_log import PATH_MAX_LENGTH, log_event, redact_path

TOKEN = secrets.token_urlsafe(24)


# AI-TRACE#522 | Claude Opus 5.5 | Test che mã bí mật trong đường dẫn của nhật ký (file log và core_securityevent), kể cả khi view quên truyền path | CẤM XÓA CHÚ THÍCH NÀY
class RedactPathTests(TestCase):
    def test_reset_link_token_is_replaced(self):
        self.assertEqual(redact_path(f"/account/dat-lai-mat-khau/MQ/{TOKEN}/"), "/account/dat-lai-mat-khau/MQ/-/")

    def test_reset_set_password_step_is_kept(self):
        path = "/account/dat-lai-mat-khau/MQ/set-password/"
        self.assertEqual(redact_path(path), path)

    def test_signup_link_token_is_replaced(self):
        self.assertEqual(redact_path(f"/account/dang-ky/xac-nhan/{TOKEN}/"), "/account/dang-ky/xac-nhan/-/")

    def test_token_without_trailing_slash_is_replaced(self):
        self.assertEqual(redact_path(f"/account/dang-ky/xac-nhan/{TOKEN}"), "/account/dang-ky/xac-nhan/-")

    def test_other_paths_unchanged(self):
        for path in ("/", "/sach/12/", "/account/login/", "/orders/don/abc/", None, ""):
            self.assertEqual(redact_path(path), path)

    @override_settings(SECURITY_LOG_SECRET_PATHS=[r"^/bi-mat/(?P<secret>[^/]+)"])
    def test_patterns_come_from_settings(self):
        self.assertEqual(redact_path(f"/bi-mat/{TOKEN}/x/"), "/bi-mat/-/x/")


class LogEventRedactionTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_request_path_with_token_is_redacted_in_file_and_table(self):
        request = self.factory.get(f"/account/dat-lai-mat-khau/MQ/{TOKEN}/")
        with self.assertLogs("security", level="WARNING") as logs:
            log_event("invalid_input", request, severity="warning")
        event = SecurityEvent.objects.get()
        self.assertEqual(event.path, "/account/dat-lai-mat-khau/MQ/-/")
        self.assertNotIn(TOKEN, logs.output[0])

    def test_explicit_path_with_token_is_redacted(self):
        with self.assertLogs("security", level="INFO") as logs:
            log_event("register_link_invalid", None, path=f"/account/dang-ky/xac-nhan/{TOKEN}/")
        self.assertEqual(SecurityEvent.objects.get().path, "/account/dang-ky/xac-nhan/-/")
        self.assertNotIn(TOKEN, logs.output[0])

    def test_long_token_is_redacted_before_truncating(self):
        long_token = "a" * 400
        request = self.factory.get(f"/account/dang-ky/xac-nhan/{long_token}/")
        with self.assertLogs("security", level="INFO"):
            log_event("register_link_invalid", request)
        self.assertEqual(SecurityEvent.objects.get().path, "/account/dang-ky/xac-nhan/-/")

    def test_long_ordinary_path_is_truncated(self):
        request = self.factory.get("/sach/" + "b" * 400)
        with self.assertLogs("security", level="INFO"):
            log_event("access_denied", request)
        self.assertEqual(len(SecurityEvent.objects.get().path), PATH_MAX_LENGTH)
