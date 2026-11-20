import secrets
import time
from unittest import mock

import pyotp
from django.core import mail
from django.core.cache import cache
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts import two_factor
from accounts.models import RecoveryCode, TotpDevice, User
from accounts.tests.two_factor_helpers import enroll, submit_code
from core.crypto import DecryptionError, decrypt_field
from core.decorators import mark_recent_auth
from core.models import SecurityEvent

VIEWS_TIME = "accounts.views.time.time"


def new_secret(tag):
    return f"{secrets.token_urlsafe(12)}-{tag}-Aa9"


class Base(TestCase):
    def setUp(self):
        cache.clear()
        self.password = new_secret("kh")
        self.customer = User.objects.create_user(username="an_nguyen", email="an@example.test",
                                                 password=self.password, email_verified=True)
        self.staff = User.objects.create_user(username="quan_tri", email="qt@example.test",
                                              password=self.password, is_staff=True)

    def post_password(self, username, client=None, **data):
        client = client or self.client
        return client.post(reverse("accounts:login"), {"username": username, "password": self.password, **data})

    def events(self, event_type):
        return SecurityEvent.objects.filter(event_type=event_type)


# AI-TRACE#509 | Claude Opus 5.5 | Test service TOTP: mã đúng/sai, lệch giờ, không dùng lại mã, chuỗi bí mật mã hóa gắn user, mã dự phòng một lần | CẤM XÓA CHÚ THÍCH NÀY
class TwoFactorServiceTests(Base):
    def setUp(self):
        super().setUp()
        self.secret = enroll(self.customer)
        self.device = two_factor.confirmed_device(self.customer)

    def test_correct_code_once_only(self):
        code = pyotp.TOTP(self.secret).now()
        self.assertTrue(two_factor.verify_code(self.device, code))
        self.assertFalse(two_factor.verify_code(self.device, code))

    def test_clock_drift_one_step_allowed_three_rejected(self):
        totp = pyotp.TOTP(self.secret)
        self.assertFalse(two_factor.verify_code(self.device, totp.at(time.time() - 90)))
        self.assertTrue(two_factor.verify_code(self.device, totp.at(time.time() - 30)))

    def test_older_step_rejected_after_newer_used(self):
        totp = pyotp.TOTP(self.secret)
        self.assertTrue(two_factor.verify_code(self.device, totp.now()))
        self.assertFalse(two_factor.verify_code(self.device, totp.at(time.time() - 30)))

    def test_bad_format(self):
        for bad in ("", "12345", "1234567", "abcdef", "12 34 5x"):
            self.assertFalse(two_factor.verify_code(self.device, bad))

    def test_secret_stored_encrypted_and_bound_to_user(self):
        row = TotpDevice.objects.get(user_id=self.customer.pk)
        self.assertTrue(row.secret_encrypted.startswith("v1."))
        self.assertNotIn(self.secret, row.secret_encrypted)
        with self.assertRaises(DecryptionError):
            decrypt_field(row.secret_encrypted, two_factor._context(self.staff.pk))

    def test_recovery_codes_hashed_and_single_use(self):
        codes = two_factor.replace_recovery_codes(self.customer)
        self.assertEqual(len(codes), 5)
        stored = list(RecoveryCode.objects.filter(user_id=self.customer.pk).values_list("code_hash", flat=True))
        self.assertTrue(all(code.replace("-", "") not in "".join(stored) for code in codes))
        self.assertEqual(two_factor.use_recovery_code(self.customer, codes[0].lower()), 4)
        self.assertIsNone(two_factor.use_recovery_code(self.customer, codes[0]))
        self.assertIsNone(two_factor.use_recovery_code(self.customer, "AAAAA-AAAAA"))

    def test_requires_two_factor(self):
        self.assertTrue(two_factor.requires_two_factor(self.staff))
        self.assertTrue(two_factor.requires_two_factor(self.customer))
        two_factor.disable(self.customer)
        self.assertFalse(two_factor.requires_two_factor(self.customer))


# AI-TRACE#510 | Claude Opus 5.5 | Test đăng nhập 2 bước: đúng mật khẩu chưa đăng nhập, mã đúng mới vào, sai 5 lần hủy lượt, hết hạn, mã dự phòng, admin bắt buộc | CẤM XÓA CHÚ THÍCH NÀY
class TwoFactorLoginTests(Base):
    def test_customer_without_two_factor_logs_in_directly(self):
        response = self.post_password("an_nguyen")
        self.assertEqual(response.status_code, 302)
        self.assertIn("_auth_user_id", self.client.session)

    def test_password_alone_is_not_login(self):
        secret = enroll(self.customer)
        self.client.get(reverse("accounts:login"))
        before = self.client.session.session_key
        response = self.post_password("an_nguyen")
        self.assertRedirects(response, reverse("accounts:login_two_factor"), fetch_redirect_response=False)
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertNotEqual(self.client.session.session_key, before)
        self.assertEqual(self.client.get(reverse("accounts:profile")).status_code, 302)
        response = submit_code(self.client, secret)
        self.assertIn("_auth_user_id", self.client.session)
        self.assertEqual(response.status_code, 302)

    def test_next_is_kept(self):
        secret = enroll(self.customer)
        self.post_password("an_nguyen", next="/account/profile/")
        response = submit_code(self.client, secret)
        self.assertEqual(response["Location"], "/account/profile/")

    def test_wrong_code_five_times_cancels(self):
        enroll(self.customer)
        self.post_password("an_nguyen")
        for _ in range(4):
            response = submit_code(self.client, None, code="000000")
            self.assertEqual(response.status_code, 200)
        response = submit_code(self.client, None, code="000000")
        self.assertRedirects(response, reverse("accounts:login"), fetch_redirect_response=False)
        self.assertEqual(self.events("otp_failed").count(), 5)
        self.assertRedirects(self.client.get(reverse("accounts:login_two_factor")), reverse("accounts:login"),
                             fetch_redirect_response=False)

    def test_pending_expires(self):
        secret = enroll(self.customer)
        with mock.patch(VIEWS_TIME, return_value=time.time() - 400):
            self.post_password("an_nguyen")
        response = submit_code(self.client, secret)
        self.assertRedirects(response, reverse("accounts:login"), fetch_redirect_response=False)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_no_pending_redirects(self):
        self.assertRedirects(self.client.get(reverse("accounts:login_two_factor")), reverse("accounts:login"),
                             fetch_redirect_response=False)

    def test_recovery_code_login_logs_and_mails(self):
        enroll(self.customer)
        codes = two_factor.replace_recovery_codes(self.customer)
        self.post_password("an_nguyen")
        submit_code(self.client, None, code=codes[2])
        self.assertIn("_auth_user_id", self.client.session)
        self.assertEqual(self.events("two_factor_recovery_used").get().detail["remaining"], 4)
        self.assertTrue(any("mã dự phòng" in m.subject for m in mail.outbox))

    def test_hourly_limit_blocks_new_attempts(self):
        secret = enroll(self.customer)
        for _ in range(2):
            self.post_password("an_nguyen")
            for _ in range(5):
                submit_code(self.client, None, code="000000")
        response = self.post_password("an_nguyen")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "quá nhiều lần")
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertIsNotNone(secret)

    def test_staff_must_have_device(self):
        response = self.post_password("quan_tri")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "chưa cài xác thực 2 bước")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_staff_cannot_use_recovery_code(self):
        enroll(self.staff)
        self.post_password("quan_tri")
        submit_code(self.client, None, code="ABCDE-FGHJK")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_staff_login_with_code(self):
        secret = enroll(self.staff)
        self.post_password("quan_tri")
        submit_code(self.client, secret)
        self.assertEqual(self.client.session["_auth_user_id"], str(self.staff.pk))
        self.assertIn("staff_login_at", self.client.session)


# AI-TRACE#511 | Claude Opus 5.5 | Test bật/tắt 2 bước của khách: cần xác thực lại, QR không cache, mã sai không bật, mã dự phòng hiện một lần, thư báo | CẤM XÓA CHÚ THÍCH NÀY
class TwoFactorSetupTests(Base):
    def login_customer(self):
        self.client.force_login(self.customer)

    def reauth(self):
        session = self.client.session
        request = mock.Mock(session=session, user=self.customer)
        mark_recent_auth(request)
        session.save()
        self.client.cookies["bs_sid"] = session.session_key

    def test_setup_requires_recent_auth(self):
        self.login_customer()
        response = self.client.get(reverse("accounts:two_factor_setup"))
        self.assertTrue(response["Location"].startswith(reverse("accounts:reauth")))
        self.assertFalse(TotpDevice.objects.exists())

    def test_full_setup_flow(self):
        self.login_customer()
        self.reauth()
        response = self.client.get(reverse("accounts:two_factor_setup"))
        self.assertEqual(response.status_code, 200)
        qr = self.client.get(reverse("accounts:two_factor_qr"))
        self.assertEqual(qr["Content-Type"], "image/svg+xml")
        self.assertIn("no-store", qr["Cache-Control"])
        self.assertEqual(qr["Content-Security-Policy"], "default-src 'none'")
        device = TotpDevice.objects.get(user_id=self.customer.pk)
        self.assertIsNone(device.confirmed_at)

        response = self.client.post(reverse("accounts:two_factor_setup"), {"code": "000000"})
        self.assertContains(response, "không đúng")
        self.assertFalse(two_factor.has_two_factor(self.customer))

        code = pyotp.TOTP(two_factor.setup_secret(device)).now()
        response = self.client.post(reverse("accounts:two_factor_setup"), {"code": code})
        self.assertTrue(two_factor.has_two_factor(self.customer))
        codes = response.context["codes"]
        self.assertEqual(len(codes), 5)
        self.assertContains(response, 'download="key-secure-bookstore.txt"')
        self.assertIn(codes[0], response.context["download_data"])
        self.assertIn("no-store", response["Cache-Control"])
        self.assertEqual(self.events("two_factor_enabled").count(), 1)
        self.assertTrue(any("BẬT" in m.subject for m in mail.outbox))
        self.assertEqual(self.client.get(reverse("accounts:two_factor_qr")).status_code, 404)

    def test_qr_without_setup_is_404(self):
        self.login_customer()
        self.assertEqual(self.client.get(reverse("accounts:two_factor_qr")).status_code, 404)

    def test_staff_redirected(self):
        self.client.force_login(self.staff)
        self.assertRedirects(self.client.get(reverse("accounts:two_factor_setup")), reverse("dashboard:profile"),
                             fetch_redirect_response=False)

    def test_disable_needs_password_and_code(self):
        secret = enroll(self.customer)
        codes = two_factor.replace_recovery_codes(self.customer)
        self.login_customer()
        url = reverse("accounts:two_factor_disable")
        response = self.client.post(url, {"password": "sai-" + secrets.token_hex(4), "code": pyotp.TOTP(secret).now()})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(two_factor.has_two_factor(self.customer))
        self.client.post(url, {"password": self.password, "code": codes[1]})
        self.assertFalse(two_factor.has_two_factor(self.customer))
        self.assertFalse(RecoveryCode.objects.filter(user_id=self.customer.pk).exists())
        self.assertEqual(self.events("two_factor_disabled").count(), 1)
        self.assertTrue(any("TẮT" in m.subject for m in mail.outbox))

    def test_profile_shows_status(self):
        self.login_customer()
        self.assertContains(self.client.get(reverse("accounts:profile")), "Bật xác thực 2 bước")
        enroll(self.customer)
        two_factor.replace_recovery_codes(self.customer)
        self.assertContains(self.client.get(reverse("accounts:profile")), "Còn 5 mã dự phòng")


# AI-TRACE#512 | Claude Opus 5.5 | Test lệnh tao_admin/dat_lai_2fa_admin: bắt cài 2 bước ngay, chỉ một admin, sai mã thì không tạo gì | CẤM XÓA CHÚ THÍCH NÀY
@override_settings(AUTH_DB_ALIAS="default")
class AdminCommandTests(TestCase):
    def setUp(self):
        cache.clear()
        self.password = new_secret("qt")

    def answer_code(self, username, wrong=False):
        def ask(prompt):
            if wrong:
                return "000000"
            device = TotpDevice.objects.get(user__username=username)
            return pyotp.TOTP(two_factor.setup_secret(device)).now()
        return ask

    def run_tao_admin(self, wrong=False):
        with mock.patch("getpass.getpass", return_value=self.password), \
                mock.patch("builtins.input", side_effect=self.answer_code("quan_tri", wrong)):
            call_command("tao_admin", "quan_tri", "qt@example.test", stdout=mock.Mock(), stderr=mock.Mock())

    def test_creates_admin_with_confirmed_device(self):
        self.run_tao_admin()
        admin = User.objects.get(username="quan_tri")
        self.assertTrue(admin.is_staff and admin.is_superuser)
        self.assertTrue(two_factor.has_two_factor(admin))
        self.assertFalse(RecoveryCode.objects.filter(user_id=admin.pk).exists())

    def test_wrong_code_creates_nothing(self):
        with self.assertRaises(CommandError):
            self.run_tao_admin(wrong=True)
        self.assertFalse(User.objects.filter(username="quan_tri").exists())
        self.assertFalse(TotpDevice.objects.exists())

    def test_only_one_admin(self):
        User.objects.create_user(username="admin_cu", email="cu@example.test", password=self.password, is_staff=True)
        with self.assertRaises(CommandError):
            self.run_tao_admin()

    def test_reset_replaces_device(self):
        self.run_tao_admin()
        admin = User.objects.get(username="quan_tri")
        old = TotpDevice.objects.get(user_id=admin.pk).secret_encrypted
        with mock.patch("builtins.input", side_effect=self.answer_code("quan_tri")):
            call_command("dat_lai_2fa_admin", "quan_tri", "--confirm", stdout=mock.Mock(), stderr=mock.Mock())
        new = TotpDevice.objects.get(user_id=admin.pk)
        self.assertNotEqual(old, new.secret_encrypted)
        self.assertIsNotNone(new.confirmed_at)
