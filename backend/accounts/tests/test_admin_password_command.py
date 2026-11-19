import os
import secrets
from io import StringIO
from unittest import mock

from django.contrib.sessions.models import Session
from django.core import mail
from django.core.cache import cache
from django.core.management import CommandError, call_command
from django.db import connection
from django.test import Client, TestCase
from django.urls import reverse

from accounts.models import User
from core.models import SecurityEvent
from core.session_store import SessionStore

GETPASS = "accounts.management.commands.doi_mat_khau_admin.getpass.getpass"


def new_secret(tag):
    return f"{secrets.token_urlsafe(12)}-{tag}-Aa9"


# AI-TRACE#093 | Claude Opus 5.5 | Test lệnh đổi mật khẩu admin: chỉ nhân viên, quy tắc mật khẩu, đăng xuất phiên, log, thư báo, chặn kết nối web | CẤM XÓA CHÚ THÍCH NÀY
class AdminPasswordCommandTests(TestCase):
    def setUp(self):
        cache.clear()
        self.old = new_secret("cu")
        self.new = new_secret("moi")
        self.staff = User.objects.create_user(username="quan_tri", email="admin@example.test",
                                              password=self.old, is_staff=True)
        self.customer = User.objects.create_user(username="an_nguyen", email="an@example.test",
                                                 password=self.old, email_verified=True)

    def run_command(self, answers, username="quan_tri"):
        out, err = StringIO(), StringIO()
        with mock.patch(GETPASS, side_effect=answers) as asked:
            call_command("doi_mat_khau_admin", username, stdout=out, stderr=err)
        return out.getvalue(), err.getvalue(), asked

    def staff_password_is(self, raw):
        return User.objects.get(pk=self.staff.pk).check_password(raw)

    def test_changes_password_logs_and_notifies(self):
        out, _, _ = self.run_command([self.new, self.new])
        self.assertTrue(self.staff_password_is(self.new))
        self.assertIn("Đã đổi mật khẩu", out)
        event = SecurityEvent.objects.get(event_type="password_changed", detail__via="cli")
        self.assertEqual(event.user_id, self.staff.pk)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["admin@example.test"])
        self.assertNotIn("http", mail.outbox[0].body)

    def test_ends_every_session_of_that_staff_only(self):
        staff_client, customer_client = Client(), Client()
        staff_client.force_login(self.staff)
        customer_client.force_login(self.customer)
        out, _, _ = self.run_command([self.new, self.new])
        self.assertIn("Đã đăng xuất 1 phiên", out)
        remaining = [SessionStore.decode_row(s).get("_auth_user_id") for s in Session.objects.all()]
        self.assertNotIn(str(self.staff.pk), remaining)
        self.assertIn(str(self.customer.pk), remaining)
        response = staff_client.get(reverse("dashboard:profile"))
        self.assertEqual(response.status_code, 302)

    def test_customer_account_is_refused(self):
        with self.assertRaises(CommandError):
            self.run_command([self.new, self.new], username="an_nguyen")
        self.assertTrue(User.objects.get(pk=self.customer.pk).check_password(self.old))

    def test_unknown_account_is_refused(self):
        with self.assertRaises(CommandError):
            self.run_command([self.new, self.new], username="khong_co")

    def test_three_mismatches_change_nothing(self):
        answers = [self.new, new_secret("khac")] * 3
        with self.assertRaises(CommandError):
            self.run_command(answers)
        self.assertTrue(self.staff_password_is(self.old))
        self.assertEqual(len(mail.outbox), 0)

    def test_reusing_current_password_is_rejected(self):
        with self.assertRaises(CommandError):
            self.run_command([self.old, self.old] * 3)
        self.assertTrue(self.staff_password_is(self.old))

    def test_retry_after_mistake_succeeds(self):
        _, err, _ = self.run_command([self.new, new_secret("khac"), self.new, self.new])
        self.assertIn("không khớp", err)
        self.assertTrue(self.staff_password_is(self.new))

    def test_refuses_web_database_account_before_asking(self):
        with mock.patch.dict(os.environ, {"DB_CUSTOMER_USER": connection.settings_dict["USER"]}), \
                mock.patch(GETPASS) as asked, self.assertRaises(CommandError):
            call_command("doi_mat_khau_admin", "quan_tri", stdout=StringIO(), stderr=StringIO())
        asked.assert_not_called()
        self.assertTrue(self.staff_password_is(self.old))

    def test_dashboard_shows_no_change_password_link(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse("dashboard:profile"))
        self.assertContains(response, "Không thể đổi mật khẩu")
        self.assertNotContains(response, reverse("accounts:password_change"))
        self.assertNotContains(response, reverse("accounts:password_reset"))
