import datetime
import secrets
from types import SimpleNamespace
from unittest import mock

from django.db import OperationalError
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from accounts.models import User
from dashboard import overview_services
from dashboard.overview_services import (BackupStatus, LowStockBook, Overview, OverviewError, get_overview,
                                         period_starts)

PASSWORD = secrets.token_urlsafe(12) + "-Aa9"


def overview(**changes):
    data = dict(paid=3, confirmed=2, packed=1, shipped=4, new_today=7, cancelled_today=1, revenue_today=267000,
                revenue_week=1250000, revenue_month=5400000, low_stock=2, out_of_stock=1,
                lowest_books=(LowStockBook(id=20, title="Đắc Nhân Tâm", stock=0),
                              LowStockBook(id=23, title="Nhà Giả Kim", stock=4)),
                warning_24h=5, critical_24h=0, login_failed_today=3, low_threshold=10,
                backup=BackupStatus(last_success=datetime.datetime.now(datetime.UTC), last_size=45000,
                                    last_failure=None, last_verify=datetime.datetime.now(datetime.UTC),
                                    last_verify_ok=True))
    data.update(changes)
    return Overview(**data)


# AI-TRACE#402 | Claude Opus 5.5 | Test service tổng quan: mốc ngày/7 ngày/tháng theo giờ Việt Nam đổi về UTC, gọi đúng 3 thủ tục qua kết nối staff với ngưỡng sắp hết từ settings, đọc nhiều bộ kết quả, đổi lỗi SIGNAL | CẤM XÓA CHÚ THÍCH NÀY
@override_settings(TIME_ZONE="Asia/Ho_Chi_Minh", LOW_STOCK_THRESHOLD=10)
class OverviewServiceTests(SimpleTestCase):
    def test_period_starts_use_vietnam_day(self):
        now = datetime.datetime(2026, 11, 1, 1, 30, tzinfo=datetime.UTC)
        today, week, month = period_starts(now)
        self.assertEqual(today, datetime.datetime(2026, 10, 31, 17, 0))
        self.assertEqual(week, datetime.datetime(2026, 10, 25, 17, 0))
        self.assertEqual(month, datetime.datetime(2026, 10, 31, 17, 0))
        late = datetime.datetime(2026, 11, 16, 18, 0, tzinfo=datetime.UTC)
        self.assertEqual(period_starts(late)[0], datetime.datetime(2026, 11, 16, 17, 0))

    def test_reads_three_procedures(self):
        cursor = mock.MagicMock()
        cursor.fetchall.side_effect = [
            [(3, 2, 1, 4, 7, 1, 267000, 1250000, 5400000)],
            [(2, 1)], [(20, "Đắc Nhân Tâm", 0)],
            [(5, 0, 3)],
            [("backup_created", datetime.datetime(2026, 11, 16, 6), '{"size": 45000}'),
             ("backup_failed", datetime.datetime(2026, 11, 16, 7), "{}")],
        ]
        cursor.nextset.side_effect = [None, True, None, None, None]
        cursor.description = ("x",)
        conn = mock.MagicMock()
        conn.cursor.return_value.__enter__.return_value = cursor
        with mock.patch.object(overview_services, "connections", {"staff": conn}):
            result = get_overview(SimpleNamespace(pk=2), datetime.datetime(2026, 11, 16, 7, tzinfo=datetime.UTC))
        names = [c.args[0] for c in cursor.callproc.call_args_list]
        self.assertEqual(names, ["sp_staff_dashboard_orders", "sp_staff_dashboard_stock",
                                 "sp_staff_dashboard_security", "sp_staff_dashboard_backup"])
        self.assertEqual(result.backup.last_size, 45000)
        self.assertTrue(result.backup.failing)
        self.assertIsNone(result.backup.last_verify_ok)
        self.assertEqual(cursor.callproc.call_args_list[1].args[1], [2, 10])
        self.assertEqual((result.todo, result.revenue_week, result.out_of_stock, result.login_failed_today),
                         (10, 1250000, 1, 3))
        self.assertEqual(result.lowest_books[0].title, "Đắc Nhân Tâm")

    def test_signal_and_permission_errors(self):
        cursor = mock.MagicMock()
        conn = mock.MagicMock()
        conn.cursor.return_value.__enter__.return_value = cursor
        with mock.patch.object(overview_services, "connections", {"staff": conn}):
            cursor.callproc.side_effect = OperationalError(1644, "NOT_STAFF")
            with self.assertRaises(OverviewError):
                get_overview(SimpleNamespace(pk=2))
            cursor.callproc.side_effect = OperationalError(1370, "execute command denied")
            with self.assertRaises(OperationalError):
                get_overview(SimpleNamespace(pk=2))


# AI-TRACE#403 | Claude Opus 5.5 | Test trang Tổng quan: chỉ nhân viên, hiện các nhóm số liệu và link lọc sẵn, thẻ nghiêm trọng tô đỏ khi có sự kiện, không lưu cache, lỗi nghiệp vụ hiện thông báo | CẤM XÓA CHÚ THÍCH NÀY
class OverviewViewTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(username="quan_tri", email="qt@example.test", password=PASSWORD,
                                              is_staff=True)
        self.customer = User.objects.create_user(username="an_nguyen", email="an@example.test", password=PASSWORD,
                                                 email_verified=True)
        self.url = reverse("dashboard:index")
        patcher = mock.patch("dashboard.views.get_overview", return_value=overview())
        self.get_overview = patcher.start()
        self.addCleanup(patcher.stop)

    def test_shows_numbers_and_links(self):
        self.client.force_login(self.staff)
        response = self.client.get(self.url)
        for text in ("Cần xử lý", "1.250.000", "Đắc Nhân Tâm", "Đăng nhập sai hôm nay",
                     reverse("dashboard:orders") + "?trang_thai=packed", reverse("dashboard:book_edit", args=[23]),
                     reverse("dashboard:logs") + "?muc_do=critical"):
            self.assertContains(response, text)
        self.assertNotContains(response, "dash-stat--alert")
        self.assertIn("no-cache", response["Cache-Control"])
        self.assertEqual(self.get_overview.call_args.args[0].pk, self.staff.pk)

    def test_critical_card_highlighted(self):
        self.get_overview.return_value = overview(critical_24h=2)
        self.client.force_login(self.staff)
        self.assertContains(self.client.get(self.url), "dash-stat--alert")

    def test_backup_status_states(self):
        self.client.force_login(self.staff)
        self.assertContains(self.client.get(self.url), "Đạt")
        self.get_overview.return_value = overview(backup=BackupStatus(None, None, None, None, None))
        response = self.client.get(self.url)
        self.assertContains(response, "Chưa có")
        self.assertContains(response, "Chưa có bản sao lưu trong 7 ngày qua")
        self.assertContains(response, "dash-stat--alert")
        now = datetime.datetime.now(datetime.UTC)
        failing = BackupStatus(now - datetime.timedelta(hours=2), 1, now, now, False)
        self.assertTrue(failing.failing and failing.needs_attention)
        self.get_overview.return_value = overview(backup=failing)
        response = self.client.get(self.url)
        self.assertContains(response, "Lần sao lưu gần nhất bị lỗi")
        self.assertContains(response, "Không đạt")

    def test_error_shows_message(self):
        self.get_overview.side_effect = OverviewError("NOT_STAFF")
        self.client.force_login(self.staff)
        response = self.client.get(self.url)
        self.assertContains(response, "Không đọc được số liệu tổng quan")

    def test_access_control(self):
        self.assertTrue(self.client.get(self.url)["Location"].startswith(reverse("accounts:login")))
        self.client.force_login(self.customer)
        self.assertEqual(self.client.get(self.url).status_code, 403)
        self.client.force_login(self.staff)
        self.assertEqual(self.client.post(self.url).status_code, 405)
        self.get_overview.assert_not_called()
