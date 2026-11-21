import datetime
import secrets
from types import SimpleNamespace
from unittest import mock

from django.core.cache import cache
from django.db import OperationalError
from django.test import Client, SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from accounts.models import User
from orders.services import Order, OrderLine
from payments import services
from payments.services import PaymentError, simulate_payment

PASSWORD = secrets.token_urlsafe(12) + "-Aa9"
CODE = "b" * 32
TXN = "SIM" + "0A" * 12


def order(status="pending", minutes_left=10):
    now = datetime.datetime.now(datetime.UTC)
    return Order(code=CODE, status=status, subtotal=158000, shipping_fee=30000, total=188000, shipping_name="Nguyễn An",
                 shipping_phone="0901234567", shipping_address="12 Nguyễn Huệ, Q.1, TP.HCM", created_at=now,
                 expires_at=now + datetime.timedelta(minutes=minutes_left), paid_at=now if status == "paid" else None,
                 cancelled_at=now if status == "cancelled" else None,
                 lines=(OrderLine(book_id=7, title="Nhà Giả Kim", unit_price=79000, quantity=2),))


@override_settings(PAYMENT_SIMULATION=True, PAYMENT_SIMULATE_RATE_LIMIT=100, PAYMENT_SIMULATE_RATE_WINDOW=600)
class SimulatePaymentServiceTests(SimpleTestCase):
    def setUp(self):
        cache.clear()
        self.user = SimpleNamespace(pk=42, is_authenticated=True, is_staff=False, get_username=lambda: "an_nguyen")
        self.request = SimpleNamespace(user=self.user, META={"REMOTE_ADDR": "127.0.0.1"}, method="POST", path="/")
        self.cursor = mock.MagicMock()
        self.cursor.nextset.return_value = None
        self.cursor.fetchone.return_value = (TXN,)
        self.conn = mock.MagicMock(in_atomic_block=False)
        self.conn.cursor.return_value.__enter__.return_value = self.cursor
        patcher = mock.patch.object(services, "connection", self.conn)
        patcher.start()
        self.addCleanup(patcher.stop)
        log_patcher = mock.patch.object(services, "log_event")
        self.log_event = log_patcher.start()
        self.addCleanup(log_patcher.stop)

    def test_calls_procedure_with_session_user_and_returns_transaction(self):
        self.assertEqual(simulate_payment(self.request, CODE), TXN)
        self.cursor.callproc.assert_called_once_with("sp_payment_simulate", [42, CODE, "127.0.0.1", None])
        self.cursor.execute.assert_called_once_with("SELECT @_sp_payment_simulate_3")

    @override_settings(PAYMENT_SIMULATION=False)
    def test_disabled_never_reaches_database(self):
        with self.assertRaises(PaymentError) as ctx:
            simulate_payment(self.request, CODE)
        self.assertEqual(ctx.exception.code, "NOT_CONFIGURED")
        self.cursor.callproc.assert_not_called()

    def test_bad_code_never_reaches_database(self):
        for bad in ("B" * 32, "abc", "b" * 31 + "'", None, 123):
            with self.subTest(bad=bad), self.assertRaises(PaymentError) as ctx:
                simulate_payment(self.request, bad)
            self.assertEqual(ctx.exception.code, "ORDER_NOT_FOUND")
        self.cursor.callproc.assert_not_called()

    def test_staff_and_anonymous_refused(self):
        for user in (SimpleNamespace(pk=2, is_authenticated=True, is_staff=True),
                     SimpleNamespace(pk=None, is_authenticated=False, is_staff=False)):
            with self.subTest(user=user), self.assertRaises(PaymentError):
                simulate_payment(SimpleNamespace(user=user, META={}), CODE)
        self.cursor.callproc.assert_not_called()

    def test_missing_ip_sent_as_null(self):
        self.request.META = {}
        simulate_payment(self.request, CODE)
        self.assertIsNone(self.cursor.callproc.call_args.args[1][2])

    def test_signal_codes_become_payment_errors(self):
        for code in ("ORDER_NOT_FOUND", "ORDER_ALREADY_PAID", "ORDER_NOT_PAYABLE", "ORDER_EXPIRED", "NOT_CUSTOMER",
                     "INVALID_INPUT"):
            with self.subTest(code=code):
                self.cursor.callproc.side_effect = OperationalError(1644, code)
                with self.assertRaises(PaymentError) as ctx:
                    simulate_payment(self.request, CODE)
                self.assertEqual(ctx.exception.code, code)

    def test_unknown_signal_and_permission_error_not_swallowed(self):
        for error in (OperationalError(1370, "execute command denied"), OperationalError(1644, "PAYMENT_LOCKED")):
            with self.subTest(error=error):
                self.cursor.callproc.side_effect = error
                with self.assertRaises(OperationalError):
                    simulate_payment(self.request, CODE)

    @override_settings(PAYMENT_SIMULATE_RATE_LIMIT=2)
    def test_rate_limited_and_logged(self):
        simulate_payment(self.request, CODE)
        simulate_payment(self.request, CODE)
        with self.assertRaises(PaymentError) as ctx:
            simulate_payment(self.request, CODE)
        self.assertEqual(ctx.exception.code, "RATE_LIMITED")
        self.assertEqual(self.cursor.callproc.call_count, 2)
        self.assertEqual(self.log_event.call_args.args[0], "rate_limited")

    def test_refuses_inside_atomic_block(self):
        self.conn.in_atomic_block = True
        with self.assertRaises(RuntimeError):
            simulate_payment(self.request, CODE)


@override_settings(PAYMENT_SIMULATION=True)
class SimulateViewTests(TestCase):
    def setUp(self):
        self.customer = User.objects.create_user(username="an_nguyen", email="an@example.test", password=PASSWORD,
                                                 email_verified=True)
        self.staff = User.objects.create_user(username="quan_tri", email="qt@example.test", password=PASSWORD,
                                              is_staff=True)
        self.url = reverse("payments:simulate", args=[CODE])
        self.detail = reverse("orders:order_detail", args=[CODE])
        patcher = mock.patch("payments.views.simulate_payment", return_value=TXN)
        self.simulate_payment = patcher.start()
        self.addCleanup(patcher.stop)
        patcher = mock.patch("orders.views.get_order", return_value=order())
        self.get_order = patcher.start()
        self.addCleanup(patcher.stop)

    def test_success_redirects_to_order_with_transaction(self):
        self.client.force_login(self.customer)
        response = self.client.post(self.url, follow=True)
        self.assertEqual(response.redirect_chain[-1][0], self.detail)
        self.assertContains(response, "Thanh toán thành công (mô phỏng)")
        self.assertContains(response, TXN)
        request, code = self.simulate_payment.call_args.args
        self.assertEqual((request.user.pk, code), (self.customer.pk, CODE))

    def test_other_users_order_is_404_and_logged(self):
        self.simulate_payment.side_effect = PaymentError("ORDER_NOT_FOUND")
        self.client.force_login(self.customer)
        with mock.patch("orders.views.log_event") as log_event:
            self.assertEqual(self.client.post(self.url).status_code, 404)
        self.assertEqual(log_event.call_args.args[0], "idor_attempt")

    def test_business_errors_show_message(self):
        self.client.force_login(self.customer)
        for code, text in (("ORDER_ALREADY_PAID", "đã được thanh toán"), ("ORDER_EXPIRED", "quá hạn thanh toán"),
                           ("ORDER_NOT_PAYABLE", "đã hủy"), ("NOT_CONFIGURED", "Chưa cấu hình")):
            with self.subTest(code=code):
                self.simulate_payment.side_effect = PaymentError(code)
                response = self.client.post(self.url, follow=True)
                self.assertEqual(response.redirect_chain[-1][0], self.detail)
                self.assertContains(response, text)

    def test_access_control(self):
        self.assertTrue(self.client.post(self.url)["Location"].startswith(reverse("accounts:login")))
        self.client.force_login(self.staff)
        self.assertEqual(self.client.post(self.url)["Location"], reverse("dashboard:index"))
        self.client.force_login(self.customer)
        self.assertEqual(self.client.get(self.url).status_code, 405)
        strict = Client(enforce_csrf_checks=True)
        strict.force_login(self.customer)
        self.assertEqual(strict.post(self.url).status_code, 403)
        self.simulate_payment.assert_not_called()

    def test_pay_box_only_for_pending_unexpired(self):
        self.client.force_login(self.customer)
        response = self.client.get(self.detail)
        self.assertContains(response, "Xác nhận thanh toán")
        self.assertContains(response, self.url)
        for kwargs in ({"status": "paid"}, {"status": "cancelled"}, {"minutes_left": -1}):
            with self.subTest(**kwargs):
                self.get_order.return_value = order(**kwargs)
                self.assertNotContains(self.client.get(self.detail), "Xác nhận thanh toán")

    @override_settings(PAYMENT_SIMULATION=False)
    def test_disabled_shows_not_configured(self):
        self.client.force_login(self.customer)
        response = self.client.get(self.detail)
        self.assertNotContains(response, "Xác nhận thanh toán")
        self.assertContains(response, "Chưa cấu hình cổng thanh toán")
