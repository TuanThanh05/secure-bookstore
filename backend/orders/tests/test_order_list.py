import datetime
import secrets
from types import SimpleNamespace
from unittest import mock

from django.db import OperationalError
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from accounts.models import User
from orders import services
from orders.services import ORDER_LIST_PAGE_SIZE, OrderError, OrderSummary, list_my_orders

PASSWORD = secrets.token_urlsafe(12) + "-Aa9"
NOW = datetime.datetime(2026, 11, 16, 6, 0, tzinfo=datetime.UTC)


def row(code="c" * 32, status="paid", minutes_left=10, lines=2, title="Nhà Giả Kim"):
    naive = NOW.replace(tzinfo=None)
    return (code, status, 188000, naive, naive + datetime.timedelta(minutes=minutes_left),
            naive if status not in ("pending", "cancelled") else None,
            naive if status == "cancelled" else None, 3, lines, title)


def summary(**kwargs):
    r = row(**kwargs)
    aware = [v.replace(tzinfo=datetime.UTC) if isinstance(v, datetime.datetime) else v for v in r]
    return OrderSummary(code=aware[0], status=aware[1], total=aware[2], created_at=aware[3], expires_at=aware[4],
                        paid_at=aware[5], cancelled_at=aware[6], item_count=aware[7], line_count=aware[8],
                        first_title=aware[9])


# AI-TRACE#370 | Claude Opus 5.5 | Test service danh sách đơn của khách bằng cursor giả: nhóm sai không xuống CSDL, chặn nhân viên/ẩn danh, tính offset theo trang, đọc 2 bộ kết quả, đổi lỗi SIGNAL, nhãn quá hạn | CẤM XÓA CHÚ THÍCH NÀY
class ListMyOrdersServiceTests(SimpleTestCase):
    def setUp(self):
        self.request = SimpleNamespace(user=SimpleNamespace(pk=42, is_authenticated=True, is_staff=False))
        self.cursor = mock.MagicMock()
        self.cursor.fetchone.return_value = (12,)
        self.cursor.fetchall.return_value = [row(), row(code="d" * 32, status="delivered", lines=1)]
        self.cursor.nextset.side_effect = [True, None]
        conn = mock.MagicMock()
        conn.cursor.return_value.__enter__.return_value = self.cursor
        patcher = mock.patch.object(services, "connection", conn)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_calls_procedure_with_session_user_and_offset(self):
        total, orders = list_my_orders(self.request, "active", 2)
        self.cursor.callproc.assert_called_once_with("sp_order_list_mine", [42, "active", ORDER_LIST_PAGE_SIZE,
                                                                            ORDER_LIST_PAGE_SIZE])
        self.assertEqual(total, 12)
        self.assertEqual([o.code for o in orders], ["c" * 32, "d" * 32])
        self.assertEqual(orders[0].created_at.tzinfo, datetime.UTC)
        self.assertEqual((orders[0].other_titles, orders[1].other_titles), (1, 0))

    def test_bad_page_becomes_first(self):
        for page in (0, -3, "2", None):
            with self.subTest(page=page):
                self.cursor.callproc.reset_mock()
                self.cursor.nextset.side_effect = [True, None]
                list_my_orders(self.request, "history", page)
                self.assertEqual(self.cursor.callproc.call_args.args[1][2], 0)

    def test_bad_group_never_reaches_database(self):
        for group in ("all", "", None, "active' OR 1=1"):
            with self.subTest(group=group), self.assertRaises(OrderError) as ctx:
                list_my_orders(self.request, group)
            self.assertEqual(ctx.exception.code, "INVALID_INPUT")
        self.cursor.callproc.assert_not_called()

    def test_staff_and_anonymous_refused(self):
        for user in (SimpleNamespace(pk=2, is_authenticated=True, is_staff=True),
                     SimpleNamespace(pk=None, is_authenticated=False, is_staff=False)):
            with self.subTest(user=user), self.assertRaises(OrderError):
                list_my_orders(SimpleNamespace(user=user), "active")
        self.cursor.callproc.assert_not_called()

    def test_signal_and_permission_errors(self):
        self.cursor.callproc.side_effect = OperationalError(1644, "NOT_CUSTOMER")
        with self.assertRaises(OrderError):
            list_my_orders(self.request, "active")
        self.cursor.callproc.side_effect = OperationalError(1370, "execute command denied")
        with self.assertRaises(OperationalError):
            list_my_orders(self.request, "active")

    def test_status_labels(self):
        self.assertEqual(summary(status="pending", minutes_left=-1).status_label, "Quá hạn thanh toán")
        self.assertEqual(summary(status="pending", minutes_left=-1).status_key, "expired")
        for status, label in (("confirmed", "Đã tiếp nhận"), ("packed", "Đã đóng gói"), ("shipped", "Đang giao"),
                              ("delivered", "Đã giao"), ("cancelled", "Đã hủy")):
            self.assertEqual(summary(status=status).status_label, label)


# AI-TRACE#371 | Claude Opus 5.5 | Test trang Đơn hàng của tôi: hai tab, tab sai về Đang xử lý, trang sai về 1, link sang chi tiết, trạng thái rỗng, nhân viên/ẩn danh bị chặn, không lưu cache | CẤM XÓA CHÚ THÍCH NÀY
class OrderListViewTests(TestCase):
    def setUp(self):
        self.customer = User.objects.create_user(username="an_nguyen", email="an@example.test", password=PASSWORD,
                                                 email_verified=True)
        self.staff = User.objects.create_user(username="quan_tri", email="qt@example.test", password=PASSWORD,
                                              is_staff=True)
        self.url = reverse("orders:list")
        patcher = mock.patch("orders.views.list_my_orders",
                             return_value=(2, [summary(), summary(code="e" * 32, status="packed", lines=1)]))
        self.list_my_orders = patcher.start()
        self.addCleanup(patcher.stop)

    def test_lists_orders_with_links(self):
        self.client.force_login(self.customer)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("orders:order_detail", args=["c" * 32]))
        self.assertContains(response, "Nhà Giả Kim và 1 sách khác")
        self.assertContains(response, "Đã đóng gói")
        self.assertContains(response, "188.000")
        self.assertIn("no-cache", response["Cache-Control"])
        request, group, page = self.list_my_orders.call_args.args
        self.assertEqual((request.user.pk, group, page), (self.customer.pk, "active", 1))

    def test_tab_and_page_parameters(self):
        self.client.force_login(self.customer)
        for query, expected in (({"status": "history", "trang": "3"}, ("history", 3)),
                                ({"status": "xyz", "trang": "abc"}, ("active", 1)),
                                ({"trang": "-5"}, ("active", 1)),
                                ({"trang": "999999999"}, ("active", 10001))):
            with self.subTest(query=query):
                self.client.get(self.url, query)
                self.assertEqual(self.list_my_orders.call_args.args[1:], expected)

    def test_empty_states(self):
        self.client.force_login(self.customer)
        self.list_my_orders.return_value = (0, [])
        self.assertContains(self.client.get(self.url), "chưa có đơn nào đang xử lý")
        self.assertContains(self.client.get(self.url, {"status": "history"}), "chưa có đơn nào trong lịch sử")

    def test_access_control(self):
        self.assertTrue(self.client.get(self.url)["Location"].startswith(reverse("accounts:login")))
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get(self.url)["Location"], reverse("dashboard:index"))
        self.client.force_login(self.customer)
        self.assertEqual(self.client.post(self.url).status_code, 405)
        self.list_my_orders.assert_not_called()
