import secrets
from types import SimpleNamespace
from unittest import mock

from django.core.cache import cache
from django.db import OperationalError
from django.test import Client, SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from accounts.models import User
from orders import cart_services
from orders.cart_services import CART_ERROR_MESSAGES, CartError, add_to_cart

PASSWORD = secrets.token_urlsafe(12) + "-Aa9"


def customer(pk=3):
    return SimpleNamespace(pk=pk, is_authenticated=True, is_staff=False, get_username=lambda: "an_nguyen")


def request_for(user):
    return SimpleNamespace(user=user, META={"REMOTE_ADDR": "127.0.0.1"}, method="POST", path="/orders/cart/them/")


@override_settings(CART_ADD_RATE_LIMIT=20, CART_ADD_RATE_WINDOW=60)
class AddToCartServiceTests(SimpleTestCase):
    def setUp(self):
        cache.clear()
        self.cursor = mock.MagicMock()
        self.cursor.nextset.return_value = None
        self.cursor.fetchone.return_value = (3,)
        self.conn = mock.MagicMock(in_atomic_block=False)
        self.conn.cursor.return_value.__enter__.return_value = self.cursor
        for target, value in ((cart_services, "connection"),):
            patcher = mock.patch.object(target, value, self.conn)
            patcher.start()
            self.addCleanup(patcher.stop)
        log_patcher = mock.patch.object(cart_services, "log_event")
        self.log_event = log_patcher.start()
        self.addCleanup(log_patcher.stop)

    def test_calls_procedure_with_session_user(self):
        self.assertEqual(add_to_cart(request_for(customer(3)), "7", "2"), 3)
        self.cursor.callproc.assert_called_once_with("sp_cart_add", [3, 7, 2, None])
        self.cursor.execute.assert_called_once_with("SELECT @_sp_cart_add_3")

    def test_quantity_must_be_one_to_five(self):
        for bad in (0, 6, 10, -1, "2.5", True, None):
            with self.subTest(bad=bad), self.assertRaises(CartError) as ctx:
                add_to_cart(request_for(customer()), 7, bad)
            self.assertEqual(ctx.exception.code, "INVALID_INPUT")
        self.cursor.callproc.assert_not_called()

    def test_bad_book_id_never_reaches_database(self):
        for bad in ("7 OR 1=1", 0, "abc"):
            with self.subTest(bad=bad), self.assertRaises(CartError) as ctx:
                add_to_cart(request_for(customer()), bad, 1)
            self.assertEqual(ctx.exception.code, "BOOK_NOT_FOUND")
        self.cursor.callproc.assert_not_called()

    def test_staff_and_anonymous_refused(self):
        for user in (SimpleNamespace(pk=2, is_authenticated=True, is_staff=True),
                     SimpleNamespace(pk=None, is_authenticated=False, is_staff=False)):
            with self.subTest(user=user), self.assertRaises(CartError):
                add_to_cart(request_for(user), 7, 1)
        self.cursor.callproc.assert_not_called()

    @override_settings(CART_ADD_RATE_LIMIT=3)
    def test_rate_limited_and_logged(self):
        for _ in range(3):
            add_to_cart(request_for(customer()), 7, 1)
        with self.assertRaises(CartError) as ctx:
            add_to_cart(request_for(customer()), 7, 1)
        self.assertEqual(ctx.exception.code, "RATE_LIMITED")
        self.assertEqual(self.cursor.callproc.call_count, 3)
        self.assertEqual(self.log_event.call_args.args[0], "rate_limited")

    def test_signal_codes_become_cart_errors(self):
        for code in ("NOT_CUSTOMER", "BOOK_NOT_FOUND", "OUT_OF_STOCK", "CART_LIMIT", "CART_FULL", "INVALID_INPUT"):
            with self.subTest(code=code):
                cache.clear()
                self.cursor.callproc.side_effect = OperationalError(1644, code)
                with self.assertRaises(CartError) as ctx:
                    add_to_cart(request_for(customer()), 7, 1)
                self.assertEqual(ctx.exception.message, CART_ERROR_MESSAGES[code])

    def test_permission_error_not_swallowed(self):
        self.cursor.callproc.side_effect = OperationalError(1370, "execute command denied")
        with self.assertRaises(OperationalError):
            add_to_cart(request_for(customer()), 7, 1)

    def test_refuses_inside_atomic_block(self):
        self.conn.in_atomic_block = True
        with self.assertRaises(RuntimeError):
            add_to_cart(request_for(customer()), 7, 1)


class CartAddViewTests(TestCase):
    def setUp(self):
        cache.clear()
        self.url = reverse("orders:cart_add")
        self.detail = reverse("catalog:book_detail", args=[7])
        self.customer = User.objects.create_user(username="an_nguyen", email="an@example.test", password=PASSWORD, email_verified=True)
        self.staff = User.objects.create_user(username="quan_tri", email="qt@example.test", password=PASSWORD, is_staff=True)
        patcher = mock.patch("orders.views.add_to_cart", return_value=2)
        self.add = patcher.start()
        self.addCleanup(patcher.stop)

    def post(self, **data):
        payload = {"book_id": "7", "quantity": "2", "next": self.detail}
        payload.update(data)
        return self.client.post(self.url, payload)

    def test_success_stays_on_current_page(self):
        self.client.force_login(self.customer)
        response = self.post()
        self.assertEqual(response["Location"], self.detail)
        request, book_id, quantity = self.add.call_args.args
        self.assertEqual((request.user.pk, book_id, quantity), (self.customer.pk, 7, 2))

    def test_open_redirect_is_blocked(self):
        self.client.force_login(self.customer)
        for evil in ("https://evil.example/x", "//evil.example", "javascript:alert(1)", "http://127.0.0.1@evil.example/"):
            with self.subTest(evil=evil):
                self.assertEqual(self.post(next=evil)["Location"], self.detail)

    def test_anonymous_goes_to_login_and_back(self):
        response = self.post()
        self.assertEqual(response["Location"], f"{reverse('accounts:login')}?next={self.detail}")
        self.add.assert_not_called()

    def test_staff_refused(self):
        self.client.force_login(self.staff)
        self.post()
        self.add.assert_not_called()

    def test_invalid_quantity_never_calls_service(self):
        self.client.force_login(self.customer)
        for bad in ("0", "6", "abc", ""):
            with self.subTest(bad=bad):
                self.post(quantity=bad)
        self.add.assert_not_called()

    def test_price_field_is_ignored(self):
        self.client.force_login(self.customer)
        self.post(price="1", unit_price="1")
        self.assertEqual(len(self.add.call_args.args), 3)

    def test_missing_book_goes_home_with_message(self):
        self.add.side_effect = CartError("BOOK_NOT_FOUND")
        self.client.force_login(self.customer)
        self.assertEqual(self.post(next="")["Location"], reverse("catalog:home"))

    def test_post_only_and_csrf(self):
        self.client.force_login(self.customer)
        self.assertEqual(self.client.get(self.url).status_code, 405)
        strict = Client(enforce_csrf_checks=True)
        strict.force_login(self.customer)
        self.assertEqual(strict.post(self.url, {"book_id": "7", "quantity": "1"}).status_code, 403)
        self.add.assert_not_called()
