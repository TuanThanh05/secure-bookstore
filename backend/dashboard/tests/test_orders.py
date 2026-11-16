import datetime
import secrets
import time
from types import SimpleNamespace
from unittest import mock

from django.db import OperationalError
from django.test import Client, SimpleTestCase, TestCase
from django.urls import reverse

from accounts.models import User
from core.decorators import REAUTH_SESSION_KEY
from dashboard import order_services
from dashboard.order_services import (PAGE_SIZE, OrderAdminError, StaffOrderDetail, StaffOrderRow, advance_order,
                                      get_order, list_orders)
from orders.services import OrderLine

PASSWORD = secrets.token_urlsafe(12) + "-Aa9"
CODE = "a" * 32
NOW = datetime.datetime(2026, 11, 16, 7, 0)


def row(status="paid"):
    return StaffOrderRow(code=CODE, username="an_nguyen", status=status, total=188000,
                         created_at=NOW.replace(tzinfo=datetime.UTC),
                         expires_at=datetime.datetime.now(datetime.UTC) + datetime.timedelta(minutes=5),
                         paid_at=None, item_count=2)


def detail(status="paid"):
    return StaffOrderDetail(code=CODE, username="an_nguyen", status=status, subtotal=158000, shipping_fee=30000,
                            total=188000, shipping_name="Nguyễn An", shipping_phone="0901234567",
                            shipping_address="12 Nguyễn Huệ, Q.1", created_at=NOW.replace(tzinfo=datetime.UTC),
                            expires_at=datetime.datetime.now(datetime.UTC), paid_at=NOW.replace(tzinfo=datetime.UTC),
                            cancelled_at=None, payment_provider="simulated", transaction_id="SIM" + "0" * 24,
                            lines=(OrderLine(book_id=7, title="Nhà Giả Kim", unit_price=79000, quantity=2),))


# AI-TRACE#390 | Claude Opus 5.5 | Test service quản lý đơn bằng cursor giả: bộ lọc/mã đơn/tên bước sai không xuống CSDL, gọi đúng thủ tục từng bước qua kết nối staff, giải mã thông tin giao hàng, đổi lỗi SIGNAL, nút bước tiếp theo theo trạng thái | CẤM XÓA CHÚ THÍCH NÀY
class OrderAdminServiceTests(SimpleTestCase):
    def setUp(self):
        self.actor = SimpleNamespace(pk=2)
        self.cursor = mock.MagicMock()
        self.cursor.nextset.side_effect = [True, None]
        self.conn = mock.MagicMock(in_atomic_block=False)
        self.conn.cursor.return_value.__enter__.return_value = self.cursor
        patcher = mock.patch.object(order_services, "connections", {"staff": self.conn})
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_list_calls_procedure_with_offset(self):
        self.cursor.fetchone.return_value = (41,)
        self.cursor.fetchall.return_value = [(CODE, "an_nguyen", "packed", 188000, NOW, NOW, NOW, 3)]
        total, rows = list_orders(self.actor, "todo", 3)
        self.cursor.callproc.assert_called_once_with("sp_staff_order_list", [2, "todo", 2 * PAGE_SIZE, PAGE_SIZE])
        self.assertEqual(total, 41)
        self.assertEqual((rows[0].status_label, rows[0].next_action["label"]), ("Đã đóng gói", "Bắt đầu giao"))

    def test_list_bad_filter_never_reaches_database(self):
        for status in ("all", "lost", "paid' OR 1=1"):
            with self.subTest(status=status), self.assertRaises(OrderAdminError):
                list_orders(self.actor, status)
        self.cursor.callproc.assert_not_called()
        self.cursor.fetchone.return_value = (0,)
        self.cursor.fetchall.return_value = []
        list_orders(self.actor, "", "x")
        self.assertEqual(self.cursor.callproc.call_args.args[1][1:3], [None, 0])

    def test_get_decrypts_shipping_with_owner_context(self):
        self.cursor.fetchone.return_value = (CODE, 3, "an_nguyen", "paid", 158000, 30000, 188000, "Nguyễn An", "enc-p",
                                             "enc-a", "k" * 32, NOW, NOW, NOW, None, "simulated", "SIMX")
        self.cursor.fetchall.return_value = [(7, "Nhà Giả Kim", 79000, 2)]
        with mock.patch.object(order_services, "decrypt_field", side_effect=lambda v, ctx: f"{v}|{ctx}") as dec:
            order = get_order(self.actor, CODE)
        self.cursor.callproc.assert_called_once_with("sp_staff_order_get", [2, CODE])
        self.assertEqual(order.shipping_phone, "enc-p|orders_order.shipping_phone_encrypted:3:" + "k" * 32)
        self.assertEqual(dec.call_count, 2)
        self.assertEqual((order.transaction_id, order.lines[0].line_total), ("SIMX", 158000))

    def test_get_unreadable_shipping_becomes_none(self):
        self.cursor.fetchone.return_value = (CODE, 3, "an_nguyen", "paid", 158000, 30000, 188000, "Nguyễn An", "bad",
                                             "bad", "k" * 32, NOW, NOW, NOW, None, None, None)
        self.cursor.fetchall.return_value = []
        order = get_order(self.actor, CODE)
        self.assertIsNone(order.shipping_phone)
        self.assertIsNone(order.shipping_address)

    def test_bad_code_never_reaches_database(self):
        for bad in ("A" * 32, "abc", None, 5):
            with self.subTest(bad=bad):
                with self.assertRaises(OrderAdminError):
                    get_order(self.actor, bad)
                with self.assertRaises(OrderAdminError):
                    advance_order(self.actor, bad, "confirm")
        self.cursor.callproc.assert_not_called()

    def test_each_action_calls_its_own_procedure(self):
        for action, procedure in (("confirm", "sp_staff_order_confirm"), ("pack", "sp_staff_order_pack"),
                                  ("ship", "sp_staff_order_ship"), ("deliver", "sp_staff_order_deliver")):
            with self.subTest(action=action):
                self.cursor.nextset.side_effect = [None]
                advance_order(self.actor, CODE, action)
                self.assertEqual(self.cursor.callproc.call_args.args, (procedure, [2, CODE]))

    def test_unknown_action_and_atomic_refused(self):
        with self.assertRaises(OrderAdminError):
            advance_order(self.actor, CODE, "cancel")
        self.conn.in_atomic_block = True
        with self.assertRaises(RuntimeError):
            advance_order(self.actor, CODE, "confirm")
        self.cursor.callproc.assert_not_called()

    def test_signal_and_permission_errors(self):
        for code in ("ORDER_WRONG_STATUS", "ORDER_NOT_FOUND", "NOT_STAFF"):
            with self.subTest(code=code):
                self.cursor.callproc.side_effect = OperationalError(1644, code)
                with self.assertRaises(OrderAdminError) as ctx:
                    advance_order(self.actor, CODE, "confirm")
                self.assertEqual(ctx.exception.code, code)
        self.cursor.callproc.side_effect = OperationalError(1370, "execute command denied")
        with self.assertRaises(OperationalError):
            advance_order(self.actor, CODE, "confirm")

    def test_next_action_follows_flow(self):
        expected = {"pending": None, "paid": "Tiếp nhận đơn", "confirmed": "Đóng gói xong", "packed": "Bắt đầu giao",
                    "shipped": "Giao thành công", "delivered": None, "cancelled": None}
        for status, label in expected.items():
            action = row(status).next_action
            self.assertEqual(action["label"] if action else None, label)


# AI-TRACE#391 | Claude Opus 5.5 | Test view quản lý đơn: chỉ nhân viên, danh sách không có thông tin giao hàng, chi tiết cần xác thực lại và ghi log, nút chuyển bước chỉ POST + CSRF, sai bước báo lỗi, mã không có trả 404, chỉ quay lại trang trong mục đơn hàng | CẤM XÓA CHÚ THÍCH NÀY
class OrderAdminViewTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(username="quan_tri", email="qt@example.test", password=PASSWORD,
                                              is_staff=True)
        self.customer = User.objects.create_user(username="an_nguyen", email="an@example.test", password=PASSWORD,
                                                 email_verified=True)
        self.list_url = reverse("dashboard:orders")
        self.detail_url = reverse("dashboard:order_detail", args=[CODE])
        self.confirm_url = reverse("dashboard:order_confirm", args=[CODE])
        for name, value in (("list_orders", (1, [row()])), ("get_order", detail()),
                            ("advance_order", "Đã tiếp nhận đơn")):
            patcher = mock.patch(f"dashboard.order_views.{name}", return_value=value)
            setattr(self, name, patcher.start())
            self.addCleanup(patcher.stop)

    def _reauth(self, client=None):
        client = client or self.client
        session = client.session
        session[REAUTH_SESSION_KEY] = {"user_id": self.staff.pk, "at": int(time.time())}
        session.save()

    def test_list_shows_orders_and_next_step(self):
        self.client.force_login(self.staff)
        response = self.client.get(self.list_url, {"trang_thai": "todo", "trang": "2"})
        self.assertContains(response, "an_nguyen")
        self.assertContains(response, "Tiếp nhận đơn")
        self.assertContains(response, self.confirm_url)
        self.assertNotContains(response, "0901234567")
        self.assertEqual(self.list_orders.call_args.args[1:], ("todo", 2))
        self.assertIn("no-cache", response["Cache-Control"])

    def test_list_bad_filter_does_not_query(self):
        self.client.force_login(self.staff)
        self.assertContains(self.client.get(self.list_url, {"trang_thai": "xyz"}), "Bộ lọc không hợp lệ")
        self.list_orders.assert_not_called()

    def test_detail_requires_reauth_and_logs(self):
        self.client.force_login(self.staff)
        response = self.client.get(self.detail_url)
        self.assertTrue(response["Location"].startswith(reverse("dashboard:reauth")))
        self.get_order.assert_not_called()
        self._reauth()
        with mock.patch("dashboard.order_views.log_event") as log_event:
            response = self.client.get(self.detail_url)
        self.assertContains(response, "12 Nguyễn Huệ, Q.1")
        self.assertContains(response, "Nhà Giả Kim")
        self.assertEqual(log_event.call_args.args[0], "sensitive_data_viewed")
        self.assertEqual(log_event.call_args.kwargs["detail"]["order_code_prefix"], CODE[:8])

    def test_detail_not_found_is_404(self):
        self.get_order.side_effect = OrderAdminError("ORDER_NOT_FOUND")
        self.client.force_login(self.staff)
        self._reauth()
        self.assertEqual(self.client.get(self.detail_url).status_code, 404)

    def test_advance_success_and_safe_redirect(self):
        self.client.force_login(self.staff)
        back = self.list_url + "?trang_thai=paid"
        response = self.client.post(self.confirm_url, {"next": back})
        self.assertEqual(response["Location"], back)
        self.assertEqual(self.advance_order.call_args.args[1:], (CODE, "confirm"))
        for bad in ("https://evil.example/", "/orders/", "//evil.example/dashboard/don-hang/"):
            with self.subTest(bad=bad):
                self.assertEqual(self.client.post(self.confirm_url, {"next": bad})["Location"], self.list_url)

    def test_each_step_url_maps_to_action(self):
        self.client.force_login(self.staff)
        for name, action in (("order_pack", "pack"), ("order_ship", "ship"), ("order_deliver", "deliver")):
            with self.subTest(name=name):
                self.client.post(reverse(f"dashboard:{name}", args=[CODE]))
                self.assertEqual(self.advance_order.call_args.args[2], action)

    def test_advance_wrong_status_and_not_found(self):
        self.client.force_login(self.staff)
        self.advance_order.side_effect = OrderAdminError("ORDER_WRONG_STATUS")
        self.assertContains(self.client.post(self.confirm_url, follow=True), "không còn ở bước này")
        self.advance_order.side_effect = OrderAdminError("ORDER_NOT_FOUND")
        self.assertEqual(self.client.post(self.confirm_url).status_code, 404)

    def test_access_control(self):
        for url in (self.list_url, self.detail_url):
            self.assertTrue(self.client.get(url)["Location"].startswith(reverse("accounts:login")))
        self.client.force_login(self.customer)
        self.assertEqual(self.client.get(self.list_url).status_code, 403)
        self.assertEqual(self.client.post(self.confirm_url).status_code, 403)
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get(self.confirm_url).status_code, 405)
        strict = Client(enforce_csrf_checks=True)
        strict.force_login(self.staff)
        self.assertEqual(strict.post(self.confirm_url).status_code, 403)
        self.advance_order.assert_not_called()
        self.get_order.assert_not_called()
