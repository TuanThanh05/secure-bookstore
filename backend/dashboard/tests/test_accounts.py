import datetime
import secrets
import time
from types import SimpleNamespace
from unittest import mock

from django.core.cache import cache
from django.db import OperationalError
from django.test import Client, SimpleTestCase, TestCase
from django.urls import reverse

from accounts.models import User
from accounts.profile import phone_context
from core.crypto import encrypt_field
from core.decorators import REAUTH_SESSION_KEY
from core.models import SecurityEvent
from dashboard import account_services
from dashboard.account_services import (AccountError, StaffAccount, get_account, list_accounts, lock_account,
                                        mask_email, mask_phone, unlock_account)

PASSWORD = secrets.token_urlsafe(12) + "-Aa9"
WRONG_PASSWORD = secrets.token_urlsafe(12)
VIEWS = "dashboard.account_views"
NOW = datetime.datetime(2026, 11, 16, 2, 0, tzinfo=datetime.UTC)


def account(id=7, username="an_nguyen", status="active", phone="0901234567"):
    return StaffAccount(id=id, username=username, email="an.nguyen@example.test", phone=phone, status=status,
                        date_joined=NOW, last_login=None)


# AI-TRACE#313 | Claude Opus 5.5 | Test che email/SĐT và nhãn trạng thái tài khoản | CẤM XÓA CHÚ THÍCH NÀY
class MaskingTests(SimpleTestCase):
    def test_mask_email(self):
        self.assertEqual(mask_email("an.nguyen@example.test"), "a***n@example.test")
        self.assertEqual(mask_email("ab@x.vn"), "a***@x.vn")
        self.assertEqual(mask_email("khong-hop-le"), "***")
        self.assertEqual(mask_email(""), "***")

    def test_mask_phone(self):
        self.assertEqual(mask_phone("0901234567"), "090****567")
        self.assertEqual(mask_phone(None), "")
        self.assertEqual(mask_phone("123"), "***")

    def test_status_labels(self):
        self.assertEqual(account(status="temp_locked").status_label, "Tạm khóa")
        self.assertEqual(account(status="locked").status_label, "Đã khóa")
        self.assertTrue(account(status="locked").is_locked)
        self.assertEqual(account().masked_phone, "090****567")


# AI-TRACE#314 | Claude Opus 5.5 | Test service tài khoản bằng cursor giả: tham số đúng thứ tự, ngưỡng axes từ settings, giải mã SĐT đúng ngữ cảnh, chặn đầu vào sai, đổi lỗi SIGNAL | CẤM XÓA CHÚ THÍCH NÀY | đã viết lại bởi Claude Opus 5.5 khi khóa tài khoản đăng xuất mọi phiên
class AccountServiceTests(SimpleTestCase):
    def setUp(self):
        self.actor = SimpleNamespace(pk=2)
        self.cursor = mock.MagicMock()
        self.cursor.nextset.return_value = None
        self.cursor.description = [("id",)]
        phone = encrypt_field("0901234567", phone_context(SimpleNamespace(pk=7)))
        self.cursor.fetchall.return_value = [(7, "an_nguyen", "an@example.test", phone, "temp_locked",
                                              datetime.datetime(2026, 11, 1), None)]
        conn = mock.MagicMock(in_atomic_block=False)
        conn.cursor.return_value.__enter__.return_value = self.cursor
        self.conn = conn
        patcher = mock.patch.object(account_services, "connections", {"staff": conn})
        patcher.start()
        sessions = mock.patch.object(account_services, "end_user_sessions", return_value=3)
        self.end_user_sessions = sessions.start()
        self.addCleanup(sessions.stop)
        self.addCleanup(patcher.stop)

    def test_list_passes_filters_and_axes_limits(self):
        accounts = list_accounts(self.actor, "temp_locked", "  an  ")
        self.cursor.callproc.assert_called_once_with("sp_staff_account_list", [2, "temp_locked", "an", 5, 15])
        self.assertEqual(accounts[0].phone, "0901234567")
        self.assertEqual(accounts[0].date_joined.tzinfo, datetime.UTC)

    def test_phone_from_other_user_context_not_shown(self):
        row = list(self.cursor.fetchall.return_value[0])
        row[3] = encrypt_field("0909999999", phone_context(SimpleNamespace(pk=8)))
        self.cursor.fetchall.return_value = [tuple(row)]
        self.assertIsNone(list_accounts(self.actor)[0].phone)

    def test_bad_filters_never_reach_database(self):
        for status, keyword in (("admin", None), ("active", "x" * 151)):
            with self.subTest(status=status), self.assertRaises(AccountError):
                list_accounts(self.actor, status, keyword)
        for bad_id in ("7 OR 1=1", 0, True, None):
            with self.subTest(bad_id=bad_id), self.assertRaises(AccountError):
                get_account(self.actor, bad_id)
        for reason in ("abc", "   x   ", "x" * 256):
            with self.subTest(reason=reason), self.assertRaises(AccountError):
                lock_account(self.actor, 7, reason)
        self.cursor.callproc.assert_not_called()

    def test_lock_and_unlock_call_procedures(self):
        self.assertEqual(lock_account(self.actor, "7", "  Spam   đánh giá "), 3)
        self.cursor.callproc.assert_called_with("sp_staff_account_lock", [2, 7, "Spam đánh giá"])
        self.end_user_sessions.assert_called_once_with(7)
        unlock_account(self.actor, 7, "Đã xác minh")
        self.cursor.callproc.assert_called_with("sp_staff_account_unlock", [2, 7, "Đã xác minh"])

    def test_signal_codes_become_account_errors(self):
        for code in ("NOT_STAFF", "ACCOUNT_NOT_FOUND", "ALREADY_LOCKED", "NOT_LOCKED"):
            with self.subTest(code=code):
                self.cursor.callproc.side_effect = OperationalError(1644, code)
                with self.assertRaises(AccountError) as ctx:
                    lock_account(self.actor, 7, "Spam đánh giá")
                self.assertEqual(ctx.exception.code, code)
        self.end_user_sessions.assert_not_called()

    def test_permission_error_not_swallowed(self):
        self.cursor.callproc.side_effect = OperationalError(1370, "execute command denied")
        with self.assertRaises(OperationalError):
            list_accounts(self.actor)

    def test_write_refuses_inside_atomic_block(self):
        self.conn.in_atomic_block = True
        with self.assertRaises(RuntimeError):
            lock_account(self.actor, 7, "Spam đánh giá")


# AI-TRACE#315 | Claude Opus 5.5 | Test trang quản lý tài khoản: chỉ admin, email/SĐT che mặc định, bản đầy đủ cần xác thực lại và ghi log, khóa/mở khóa luôn đòi nhập mật khẩu dù vừa xác thực, CSRF | CẤM XÓA CHÚ THÍCH NÀY | đã viết lại bởi Claude Opus 5.5 khi khóa tài khoản đăng xuất mọi phiên
class AccountViewTests(TestCase):
    def setUp(self):
        cache.clear()
        self.staff = User.objects.create_user(username="quan_tri", email="qt@example.test", password=PASSWORD, is_staff=True)
        self.customer = User.objects.create_user(username="khach", email="k@example.test", password=PASSWORD, email_verified=True)
        self.client.force_login(self.staff)
        self.list_url = reverse("dashboard:accounts")
        self.full_url = reverse("dashboard:accounts_full")
        self.lock_url = reverse("dashboard:account_lock", args=[7])
        self.unlock_url = reverse("dashboard:account_unlock", args=[7])
        patches = {"list_accounts": [account(), account(8, "binh", "locked", None)], "get_account": account(),
                   "lock_account": 2, "unlock_account": None}
        for name, value in patches.items():
            patcher = mock.patch(f"{VIEWS}.{name}", return_value=value)
            setattr(self, name, patcher.start())
            self.addCleanup(patcher.stop)

    def mark_reauth(self):
        session = self.client.session
        session[REAUTH_SESSION_KEY] = {"user_id": self.staff.pk, "at": int(time.time())}
        session.save()

    def action_data(self, **overrides):
        data = {"reason": "Spam đánh giá", "username": "quan_tri", "password": PASSWORD}
        data.update(overrides)
        return data

    def test_list_masks_contact_and_filters(self):
        response = self.client.get(self.list_url, {"trang_thai": "da-khoa", "ten": "an"})
        html = response.content.decode()
        self.assertEqual(response.status_code, 200)
        self.assertIn("no-cache", response["Cache-Control"])
        self.assertIn("a***n@example.test", html)
        self.assertIn("090****567", html)
        self.assertNotIn("an.nguyen@example.test", html)
        self.assertNotIn("0901234567", html)
        self.assertIn(self.unlock_url.replace("/7/", "/8/"), html)
        self.list_accounts.assert_called_once_with(self.staff, "locked", "an")

    def test_bad_status_filter_is_ignored(self):
        self.client.get(self.list_url, {"trang_thai": "admin"})
        self.list_accounts.assert_called_once_with(self.staff, None, "")

    def test_full_contact_needs_reauth_and_is_logged(self):
        response = self.client.get(self.full_url)
        self.assertTrue(response["Location"].startswith(reverse("dashboard:reauth")))
        self.mark_reauth()
        response = self.client.get(self.full_url)
        self.assertContains(response, "an.nguyen@example.test")
        self.assertContains(response, "0901234567")
        event = SecurityEvent.objects.filter(event_type="sensitive_data_viewed").latest("id")
        self.assertEqual(event.detail["owner"], "customers")

    def test_lock_requires_password_even_after_recent_reauth(self):
        self.mark_reauth()
        response = self.client.post(self.lock_url, self.action_data(password=WRONG_PASSWORD))
        self.assertEqual(response.status_code, 400)
        response = self.client.post(self.lock_url, {"reason": "Spam đánh giá"})
        self.assertEqual(response.status_code, 400)
        self.lock_account.assert_not_called()

    def test_lock_success(self):
        response = self.client.post(self.lock_url, self.action_data(), follow=True)
        self.assertEqual(response.redirect_chain[-1][0], self.list_url)
        self.assertContains(response, "Đã khóa tài khoản an_nguyen và đăng xuất 2 phiên đang mở.")
        self.assertTrue(SecurityEvent.objects.filter(event_type="logout", detail__reason="account_locked",
                                                     detail__target_id=7, detail__sessions_ended=2).exists())
        actor, user_id, reason = self.lock_account.call_args.args
        self.assertEqual((actor.pk, user_id, reason), (self.staff.pk, 7, "Spam đánh giá"))
        self.assertNotIn(REAUTH_SESSION_KEY, self.client.session)

    def test_unlock_success(self):
        self.get_account.return_value = account(status="locked")
        self.client.post(self.unlock_url, self.action_data(reason="Đã xác minh lại"))
        self.unlock_account.assert_called_once()

    def test_other_users_credentials_rejected_and_logged(self):
        response = self.client.post(self.lock_url, self.action_data(username="khach"))
        self.assertEqual(response.status_code, 400)
        self.assertTrue(SecurityEvent.objects.filter(event_type="access_denied").exists())
        self.lock_account.assert_not_called()

    def test_short_reason_rejected(self):
        self.assertEqual(self.client.post(self.lock_url, self.action_data(reason="abc")).status_code, 400)
        self.lock_account.assert_not_called()

    def test_wrong_state_redirects(self):
        self.get_account.return_value = account(status="locked")
        self.assertEqual(self.client.get(self.lock_url)["Location"], self.list_url)
        self.get_account.return_value = account()
        self.assertEqual(self.client.get(self.unlock_url)["Location"], self.list_url)

    def test_missing_or_staff_account_is_404(self):
        self.get_account.side_effect = AccountError("ACCOUNT_NOT_FOUND")
        self.assertEqual(self.client.get(self.lock_url).status_code, 404)

    def test_access_control_and_csrf(self):
        customer = Client()
        customer.force_login(self.customer)
        self.assertEqual(customer.get(self.list_url).status_code, 403)
        self.assertEqual(customer.post(self.lock_url, self.action_data()).status_code, 403)
        self.assertTrue(Client().get(self.list_url)["Location"].startswith(reverse("accounts:login")))
        strict = Client(enforce_csrf_checks=True)
        strict.force_login(self.staff)
        self.assertEqual(strict.post(self.lock_url, self.action_data()).status_code, 403)
        self.lock_account.assert_not_called()
