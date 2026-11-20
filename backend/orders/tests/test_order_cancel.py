import datetime
import secrets
from types import SimpleNamespace
from unittest import mock

from django.core.cache import cache
from django.db import OperationalError
from django.test import Client, SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from accounts.models import User
from orders import services
from orders.services import Order, OrderError, OrderLine, cancel_order

PASSWORD = secrets.token_urlsafe(12) + "-Aa9"
CODE = "a" * 32


def order(status="pending", minutes_left=10):
    now = datetime.datetime.now(datetime.UTC)
    return Order(code=CODE, status=status, subtotal=158000, shipping_fee=30000, total=188000, shipping_name="Nguyễn An",
                 shipping_phone="0901234567", shipping_address="12 Nguyễn Huệ, Q.1, TP.HCM", created_at=now,
                 expires_at=now + datetime.timedelta(minutes=minutes_left), paid_at=now if status == "paid" else None,
                 cancelled_at=now if status == "cancelled" else None,
                 lines=(OrderLine(book_id=7, title="Nhà Giả Kim", unit_price=79000, quantity=2),))


# AI-TRACE#291 | Claude Opus 5.5 | Test service hủy đơn bằng cursor giả: mã đơn sai mẫu không xuống CSDL, chặn nhân viên/ẩn danh, giới hạn tần suất, đổi lỗi SIGNAL | CẤM XÓA CHÚ THÍCH NÀY | đã viết lại bởi Claude Opus 5.5 khi thủ tục hủy trả cờ khóa vì giữ kho
@override_settings(ORDER_CANCEL_RATE_LIMIT=100, ORDER_CANCEL_RATE_WINDOW=600)
class CancelOrderServiceTests(SimpleTestCase):
    def setUp(self):
        cache.clear()
        self.user = SimpleNamespace(pk=42, is_authenticated=True, is_staff=False, get_username=lambda: "an_nguyen")
        self.request = SimpleNamespace(user=self.user, META={"REMOTE_ADDR": "127.0.0.1"}, method="POST", path="/")
        self.cursor = mock.MagicMock()
        self.cursor.nextset.return_value = None
        self.cursor.fetchone.return_value = (0,)
        self.conn = mock.MagicMock(in_atomic_block=False)
        self.conn.cursor.return_value.__enter__.return_value = self.cursor
        patcher = mock.patch.object(services, "connection", self.conn)
        patcher.start()
        self.addCleanup(patcher.stop)
        log_patcher = mock.patch.object(services, "log_event")
        self.log_event = log_patcher.start()
        self.addCleanup(log_patcher.stop)

    def test_calls_procedure_with_session_user(self):
        self.assertFalse(cancel_order(self.request, CODE))
        self.cursor.callproc.assert_called_once_with("sp_order_cancel", [42, CODE, None])
        self.cursor.execute.assert_called_once_with("SELECT @_sp_order_cancel_2")

    def test_returns_true_when_account_just_locked(self):
        self.cursor.fetchone.return_value = (1,)
        self.assertTrue(cancel_order(self.request, CODE))

    def test_bad_code_never_reaches_database(self):
        for bad in ("A" * 32, "abc", "a" * 31 + "'", None, 123):
            with self.subTest(bad=bad), self.assertRaises(OrderError) as ctx:
                cancel_order(self.request, bad)
            self.assertEqual(ctx.exception.code, "ORDER_NOT_FOUND")
        self.cursor.callproc.assert_not_called()

    def test_staff_and_anonymous_refused(self):
        for user in (SimpleNamespace(pk=2, is_authenticated=True, is_staff=True),
                     SimpleNamespace(pk=None, is_authenticated=False, is_staff=False)):
            with self.subTest(user=user), self.assertRaises(OrderError):
                cancel_order(SimpleNamespace(user=user), CODE)
        self.cursor.callproc.assert_not_called()

    def test_signal_codes_become_order_errors(self):
        for code in ("ORDER_NOT_FOUND", "ORDER_NOT_CANCELLABLE", "NOT_CUSTOMER"):
            with self.subTest(code=code):
                self.cursor.callproc.side_effect = OperationalError(1644, code)
                with self.assertRaises(OrderError) as ctx:
                    cancel_order(self.request, CODE)
                self.assertEqual(ctx.exception.code, code)

    def test_permission_error_not_swallowed(self):
        self.cursor.callproc.side_effect = OperationalError(1370, "execute command denied")
        with self.assertRaises(OperationalError):
            cancel_order(self.request, CODE)

    @override_settings(ORDER_CANCEL_RATE_LIMIT=2)
    def test_rate_limited_and_logged(self):
        cancel_order(self.request, CODE)
        cancel_order(self.request, CODE)
        with self.assertRaises(OrderError) as ctx:
            cancel_order(self.request, CODE)
        self.assertEqual(ctx.exception.code, "RATE_LIMITED")
        self.assertEqual(self.cursor.callproc.call_count, 2)
        self.assertEqual(self.log_event.call_args.args[0], "rate_limited")

    def test_refuses_inside_atomic_block(self):
        self.conn.in_atomic_block = True
        with self.assertRaises(RuntimeError):
            cancel_order(self.request, CODE)

    def test_can_cancel_only_pending(self):
        self.assertTrue(order().can_cancel)
        self.assertTrue(order(minutes_left=-1).can_cancel)
        for status in ("paid", "shipped", "delivered", "cancelled"):
            self.assertFalse(order(status=status).can_cancel)


# AI-TRACE#292 | Claude Opus 5.5 | Test view hủy đơn: chỉ POST + CSRF, đơn người khác/mã sai trả 404, nhân viên/ẩn danh bị chặn, nút hủy hai bước chỉ hiện khi còn chờ thanh toán | CẤM XÓA CHÚ THÍCH NÀY
class OrderCancelViewTests(TestCase):
    def setUp(self):
        self.customer = User.objects.create_user(username="an_nguyen", email="an@example.test", password=PASSWORD, email_verified=True)
        self.staff = User.objects.create_user(username="quan_tri", email="qt@example.test", password=PASSWORD, is_staff=True)
        self.url = reverse("orders:order_cancel", args=[CODE])
        self.detail = reverse("orders:order_detail", args=[CODE])
        for name, value in (("cancel_order", None), ("get_order", order())):
            patcher = mock.patch(f"orders.views.{name}", return_value=value)
            setattr(self, name, patcher.start())
            self.addCleanup(patcher.stop)

    def test_success_redirects_to_order(self):
        self.client.force_login(self.customer)
        response = self.client.post(self.url, follow=True)
        self.assertEqual(response.redirect_chain[-1][0], self.detail)
        self.assertContains(response, "Đã hủy đơn hàng")
        request, code = self.cancel_order.call_args.args
        self.assertEqual((request.user.pk, code), (self.customer.pk, CODE))

    def test_other_users_order_is_404(self):
        self.cancel_order.side_effect = OrderError("ORDER_NOT_FOUND")
        self.client.force_login(self.customer)
        self.assertEqual(self.client.post(self.url).status_code, 404)

    def test_not_cancellable_shows_message(self):
        self.cancel_order.side_effect = OrderError("ORDER_NOT_CANCELLABLE")
        self.client.force_login(self.customer)
        self.assertContains(self.client.post(self.url, follow=True), "không còn hủy được")

    def test_access_control(self):
        self.assertTrue(self.client.post(self.url)["Location"].startswith(reverse("accounts:login")))
        self.client.force_login(self.staff)
        self.assertEqual(self.client.post(self.url)["Location"], reverse("dashboard:index"))
        self.client.force_login(self.customer)
        self.assertEqual(self.client.get(self.url).status_code, 405)
        strict = Client(enforce_csrf_checks=True)
        strict.force_login(self.customer)
        self.assertEqual(strict.post(self.url).status_code, 403)
        self.cancel_order.assert_not_called()

    def test_cancel_box_only_for_pending(self):
        self.client.force_login(self.customer)
        self.assertContains(self.client.get(self.detail), "Xác nhận hủy đơn")
        for status, text in (("paid", "Đã thanh toán"), ("cancelled", "Đã hủy")):
            with self.subTest(status=status):
                self.get_order.return_value = order(status=status)
                response = self.client.get(self.detail)
                self.assertNotContains(response, "Xác nhận hủy đơn")
                self.assertContains(response, text)
        self.get_order.return_value = order(minutes_left=-1)
        response = self.client.get(self.detail)
        self.assertContains(response, "Quá hạn thanh toán")
        self.assertContains(response, "Xác nhận hủy đơn")
