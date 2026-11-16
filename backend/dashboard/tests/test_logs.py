import datetime
import secrets
import time
from types import SimpleNamespace
from unittest import mock

from django.db import OperationalError
from django.test import Client, RequestFactory, SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from accounts.models import User
from core.decorators import REAUTH_SESSION_KEY
from core.middleware import DbPermissionDeniedMiddleware
from core.models import SecurityEvent
from dashboard import log_services
from dashboard.forms import AuditLogFilterForm, SecurityLogFilterForm
from dashboard.log_services import AuditRow, LogError, SecurityEventRow, list_audit_log, list_security_events

PASSWORD = secrets.token_urlsafe(12) + "-Aa9"
NOW = datetime.datetime(2026, 11, 16, 2, 0, tzinfo=datetime.UTC)


def event(**overrides):
    values = {"id": 1, "created_at": NOW, "event_type": "login_failed", "severity": "warning", "user_id": None,
              "username": None, "username_attempted": "khach", "ip_address": "10.0.0.1", "method": "POST",
              "path": "/account/login/", "user_agent": "UA", "detail": {"reason": "x"}}
    values.update(overrides)
    return SecurityEventRow(**values)


def audit(**overrides):
    values = {"id": 1, "created_at": NOW, "table_name": "orders_order", "record_id": 24, "action": "UPDATE",
              "old_value": {"status": "pending"}, "new_value": {"status": "cancelled", "code": "0bae69e2aa", "source": "system"},
              "db_user": "event_scheduler@localhost", "app_user_id": None, "username": None}
    values.update(overrides)
    return AuditRow(**values)


# AI-TRACE#344 | Claude Opus 5.5 | Test dữ liệu nhật ký: nhãn tiếng Việt, danh sách thay đổi cũ → mới, nguồn, đọc JSON lỗi không làm hỏng trang | CẤM XÓA CHÚ THÍCH NÀY
class LogRowTests(SimpleTestCase):
    def test_security_row(self):
        row = event()
        self.assertEqual(row.label, "Đăng nhập sai")
        self.assertEqual(row.severity_label, "Cảnh báo")
        self.assertEqual(row.who, "khach")
        self.assertEqual(row.detail_items, [("reason", "x")])
        self.assertEqual(event(event_type="la_lung").label, "la_lung")

    def test_audit_row(self):
        row = audit()
        self.assertEqual(row.table_label, "Đơn hàng")
        self.assertEqual(row.source_label, "Hệ thống")
        self.assertEqual(row.changes, [("status", "pending", "cancelled")])
        self.assertEqual(row.record_label, "#24 · 0bae69e2")
        staff_row = audit(table_name="accounts_user", new_value={"is_active": 0, "reason": "Spam"},
                          old_value={"is_active": 1}, db_user="app_staff@localhost")
        self.assertEqual(staff_row.source_label, "Quản trị")
        self.assertIn(("reason", "", "Spam"), staff_row.changes)

    def test_bad_json_is_kept_as_raw(self):
        self.assertEqual(log_services._json("{khong hop le"), {"raw": "{khong hop le"})
        self.assertEqual(log_services._json(None), {})
        self.assertEqual(log_services._json("[1, 2]"), {"value": [1, 2]})


# AI-TRACE#345 | Claude Opus 5.5 | Test service đọc nhật ký bằng cursor giả: tham số đúng thứ tự, thời gian đổi về UTC, phân trang có trần, đổi lỗi SIGNAL, lỗi quyền để nguyên | CẤM XÓA CHÚ THÍCH NÀY
class LogServiceTests(SimpleTestCase):
    def setUp(self):
        self.actor = SimpleNamespace(pk=2)
        self.cursor = mock.MagicMock()
        self.cursor.fetchone.return_value = (120,)
        self.cursor.nextset.side_effect = [True, None]
        self.cursor.fetchall.return_value = [(5, datetime.datetime(2026, 11, 16, 1, 0), "csrf_failed", "warning", 4,
                                              "binh", None, "10.0.0.2", "POST", "/orders/cart/go/", "UA",
                                              '{"reason": "CSRF cookie not set."}')]
        conn = mock.MagicMock()
        conn.cursor.return_value.__enter__.return_value = self.cursor
        patcher = mock.patch.object(log_services, "connections", {"staff": conn})
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_security_events_params_and_rows(self):
        start = datetime.datetime(2026, 11, 16, 0, 0, tzinfo=datetime.timezone(datetime.timedelta(hours=7)))
        rows, total, page = list_security_events(self.actor, event_type="csrf_failed", severity="warning",
                                                 start=start, end=None, keyword="  binh ", page=3)
        self.cursor.callproc.assert_called_once_with("sp_staff_security_events", [
            2, "csrf_failed", "warning", datetime.datetime(2026, 11, 15, 17, 0), None, "binh", 100, 50])
        self.assertEqual((total, page), (120, 3))
        self.assertEqual(rows[0].detail, {"reason": "CSRF cookie not set."})
        self.assertEqual(rows[0].created_at.tzinfo, datetime.UTC)

    def test_offset_is_capped(self):
        list_security_events(self.actor, page=999999)
        self.assertEqual(self.cursor.callproc.call_args.args[1][6], 100000)

    def test_audit_params(self):
        self.cursor.fetchall.return_value = []
        list_audit_log(self.actor, table="orders_order", action="UPDATE", record_id=24)
        self.cursor.callproc.assert_called_once_with("sp_staff_audit_log", [2, "orders_order", "UPDATE", None, None, 24, 0, 50])

    def test_errors(self):
        self.cursor.callproc.side_effect = OperationalError(1644, "INVALID_INPUT")
        with self.assertRaises(LogError):
            list_security_events(self.actor)
        self.cursor.callproc.side_effect = OperationalError(1370, "execute command denied")
        with self.assertRaises(OperationalError):
            list_audit_log(self.actor)


# AI-TRACE#346 | Claude Opus 5.5 | Test bộ lọc nhật ký: loại/mức độ chỉ nhận giá trị cố định, ngày theo giờ Việt Nam đổi thành khoảng có múi giờ, chặn khoảng ngược và quá 400 ngày | CẤM XÓA CHÚ THÍCH NÀY
@override_settings(TIME_ZONE="Asia/Ho_Chi_Minh")
class LogFilterFormTests(SimpleTestCase):
    def test_choices_are_fixed(self):
        self.assertFalse(SecurityLogFilterForm({"loai": "x' OR '1"}).is_valid())
        self.assertFalse(SecurityLogFilterForm({"muc_do": "debug"}).is_valid())
        self.assertFalse(AuditLogFilterForm({"bang": "auth_user"}).is_valid())
        self.assertFalse(AuditLogFilterForm({"ma": "0"}).is_valid())

    def test_date_range(self):
        form = SecurityLogFilterForm({"tu": "2026-11-15", "den": "2026-11-16"})
        self.assertTrue(form.is_valid())
        start, end = form.range()
        self.assertEqual(start.astimezone(datetime.UTC), datetime.datetime(2026, 11, 14, 17, 0, tzinfo=datetime.UTC))
        self.assertEqual(end.astimezone(datetime.UTC), datetime.datetime(2026, 11, 16, 17, 0, tzinfo=datetime.UTC))
        self.assertFalse(SecurityLogFilterForm({"tu": "2026-11-20", "den": "2026-11-01"}).is_valid())
        self.assertFalse(SecurityLogFilterForm({"tu": "2025-01-01", "den": "2026-11-16"}).is_valid())

    def test_keyword_cleaned(self):
        form = SecurityLogFilterForm({"tim": " 10.0.\u202e0.1 "})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["tim"], "10.0.0.1")


# AI-TRACE#347 | Claude Opus 5.5 | Test trang nhật ký: chỉ admin, bắt buộc xác thực lại, mỗi lần xem ghi log, lọc chuyển đúng xuống service, bộ lọc sai không gọi CSDL | CẤM XÓA CHÚ THÍCH NÀY
class LogViewTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(username="quan_tri", email="qt@example.test", password=PASSWORD, is_staff=True)
        self.customer = User.objects.create_user(username="khach", email="k@example.test", password=PASSWORD, email_verified=True)
        self.client.force_login(self.staff)
        for name, value in (("list_security_events", ([event()], 1, 1)), ("list_audit_log", ([audit()], 1, 1))):
            patcher = mock.patch(f"dashboard.log_views.{name}", return_value=value)
            setattr(self, name, patcher.start())
            self.addCleanup(patcher.stop)

    def reauth(self):
        session = self.client.session
        session[REAUTH_SESSION_KEY] = {"user_id": self.staff.pk, "at": int(time.time())}
        session.save()

    def test_requires_reauth(self):
        for name in ("dashboard:logs", "dashboard:logs_audit"):
            with self.subTest(name=name):
                self.assertTrue(self.client.get(reverse(name))["Location"].startswith(reverse("dashboard:reauth")))
        self.list_security_events.assert_not_called()

    def test_security_tab(self):
        self.reauth()
        response = self.client.get(reverse("dashboard:logs"), {"loai": "login_failed", "muc_do": "warning", "tim": "khach"})
        self.assertContains(response, "Đăng nhập sai")
        self.assertIn("no-cache", response["Cache-Control"])
        kwargs = self.list_security_events.call_args.kwargs
        self.assertEqual((kwargs["event_type"], kwargs["severity"], kwargs["keyword"]), ("login_failed", "warning", "khach"))
        viewed = SecurityEvent.objects.filter(event_type="sensitive_data_viewed").latest("id")
        self.assertEqual(viewed.detail["fields"], ["security_log"])

    def test_audit_tab(self):
        self.reauth()
        response = self.client.get(reverse("dashboard:logs_audit"), {"bang": "orders_order", "ma": "24"})
        self.assertContains(response, "Hệ thống")
        self.assertContains(response, "cancelled")
        self.assertEqual(self.list_audit_log.call_args.kwargs["record_id"], 24)

    def test_invalid_filter_does_not_query(self):
        self.reauth()
        self.client.get(reverse("dashboard:logs"), {"loai": "hack"})
        self.list_security_events.assert_not_called()

    def test_customer_and_anonymous_blocked(self):
        customer = Client()
        customer.force_login(self.customer)
        self.assertEqual(customer.get(reverse("dashboard:logs")).status_code, 403)
        self.assertTrue(Client().get(reverse("dashboard:logs"))["Location"].startswith(reverse("accounts:login")))


# AI-TRACE#348 | Claude Opus 5.5 | Test 4 log bổ sung: CSRF, MySQL từ chối quyền (middleware), nghi IDOR khi mở đơn người khác, mã đơn rác không ghi | CẤM XÓA CHÚ THÍCH NÀY
class NewSecurityEventTests(TestCase):
    def setUp(self):
        self.customer = User.objects.create_user(username="khach", email="k@example.test", password=PASSWORD, email_verified=True)

    def test_csrf_failure_logged(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.customer)
        self.assertEqual(client.post(reverse("orders:cart_remove"), {"book_id": "1"}).status_code, 403)
        logged = SecurityEvent.objects.get(event_type="csrf_failed")
        self.assertEqual(logged.user_id, self.customer.pk)
        self.assertIn("reason", logged.detail)

    def test_db_permission_denied_logged(self):
        request = RequestFactory().get("/orders/cart/")
        request.user = self.customer
        middleware = DbPermissionDeniedMiddleware(lambda r: None)
        self.assertIsNone(middleware.process_exception(request, OperationalError(1370, "execute command denied")))
        self.assertIsNone(middleware.process_exception(request, OperationalError(1644, "CART_LIMIT")))
        self.assertIsNone(middleware.process_exception(request, ValueError("x")))
        logged = SecurityEvent.objects.get(event_type="db_permission_denied")
        self.assertEqual((logged.severity, logged.detail["mysql_code"]), ("critical", 1370))

    def test_idor_attempt_logged_only_for_valid_codes(self):
        from orders.services import OrderError
        self.client.force_login(self.customer)
        with mock.patch("orders.views.get_order", side_effect=OrderError("ORDER_NOT_FOUND")):
            self.assertEqual(self.client.get(reverse("orders:order_detail", args=["a" * 32])).status_code, 404)
            self.assertEqual(self.client.get(reverse("orders:order_detail", args=["abc"])).status_code, 404)
        logged = SecurityEvent.objects.filter(event_type="idor_attempt")
        self.assertEqual(logged.count(), 1)
        self.assertEqual(logged.first().detail["code_prefix"], "a" * 8)
