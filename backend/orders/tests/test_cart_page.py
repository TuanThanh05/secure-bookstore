import secrets
from types import SimpleNamespace
from unittest import mock

from django.core.cache import cache
from django.db import OperationalError
from django.test import Client, SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from accounts.models import User
from orders import cart_services
from orders.cart_services import Cart, CartError, CartLine, get_cart, remove_from_cart, set_cart_quantity

PASSWORD = secrets.token_urlsafe(12) + "-Aa9"


def customer(pk=3):
    return SimpleNamespace(pk=pk, is_authenticated=True, is_staff=False, get_username=lambda: "an_nguyen")


def request_for(user):
    return SimpleNamespace(user=user, META={"REMOTE_ADDR": "127.0.0.1"}, method="POST", path="/orders/cart/")


def line(book_id=7, quantity=2, is_active=True, in_stock=True, price=79000):
    return CartLine(book_id=book_id, title="Nhà Giả Kim", author="Paulo Coelho", cover_image=None, price=price,
                    quantity=quantity, is_active=is_active, in_stock=in_stock)


class CartDataTests(SimpleTestCase):
    def test_subtotal_skips_unavailable_lines(self):
        cart = Cart(lines=(line(1, 2), line(2, 3, in_stock=False), line(3, 1, is_active=False), line(4, 1, price=1000)))
        self.assertEqual(cart.subtotal, 79000 * 2 + 1000)
        self.assertEqual(cart.item_count, 3)
        self.assertTrue(cart.has_unavailable)

    def test_buttons_follow_limits(self):
        self.assertFalse(line(quantity=1).can_decrease)
        self.assertTrue(line(quantity=1).can_increase)
        self.assertFalse(line(quantity=5).can_increase)
        for unavailable in (line(in_stock=False), line(is_active=False)):
            self.assertFalse(unavailable.can_increase)
            self.assertFalse(unavailable.can_decrease)

    def test_status_labels(self):
        self.assertEqual(line(is_active=False, in_stock=False).status_label, "Ngừng bán")
        self.assertEqual(line(in_stock=False).status_label, "Hết hàng")
        self.assertEqual(line().status_label, "")
        self.assertTrue(line().cover_url)


@override_settings(CART_UPDATE_RATE_LIMIT=60, CART_UPDATE_RATE_WINDOW=60)
class CartPageServiceTests(SimpleTestCase):
    def setUp(self):
        cache.clear()
        self.cursor = mock.MagicMock()
        self.cursor.nextset.return_value = None
        self.cursor.description = [("id",)]
        self.cursor.fetchall.return_value = [(7, "Nhà Giả Kim", "Paulo Coelho", "", 79000, 2, 1, 1)]
        self.conn = mock.MagicMock(in_atomic_block=False)
        self.conn.cursor.return_value.__enter__.return_value = self.cursor
        patcher = mock.patch.object(cart_services, "connection", self.conn)
        patcher.start()
        self.addCleanup(patcher.stop)
        log_patcher = mock.patch.object(cart_services, "log_event")
        self.log_event = log_patcher.start()
        self.addCleanup(log_patcher.stop)

    def test_get_cart_uses_session_user(self):
        cart = get_cart(request_for(customer(3)))
        self.cursor.callproc.assert_called_once_with("sp_cart_list", [3])
        self.assertEqual(cart.lines[0], line(7, 2))

    def test_set_quantity_sends_final_number(self):
        self.assertEqual(set_cart_quantity(request_for(customer(3)), "7", "4"), 4)
        self.cursor.callproc.assert_called_once_with("sp_cart_set_quantity", [3, 7, 4])

    def test_remove(self):
        remove_from_cart(request_for(customer(3)), 7)
        self.cursor.callproc.assert_called_once_with("sp_cart_remove", [3, 7])

    def test_bad_input_never_reaches_database(self):
        for book_id, quantity, code in (("7 OR 1=1", 1, "NOT_IN_CART"), (0, 1, "NOT_IN_CART"),
                                        (7, 0, "INVALID_INPUT"), (7, 6, "INVALID_INPUT"), (7, True, "INVALID_INPUT")):
            with self.subTest(book_id=book_id, quantity=quantity), self.assertRaises(CartError) as ctx:
                set_cart_quantity(request_for(customer()), book_id, quantity)
            self.assertEqual(ctx.exception.code, code)
        with self.assertRaises(CartError):
            remove_from_cart(request_for(customer()), "abc")
        self.cursor.callproc.assert_not_called()

    def test_staff_and_anonymous_refused(self):
        for user in (SimpleNamespace(pk=2, is_authenticated=True, is_staff=True),
                     SimpleNamespace(pk=None, is_authenticated=False, is_staff=False)):
            for call in (lambda: get_cart(request_for(user)), lambda: set_cart_quantity(request_for(user), 7, 1),
                         lambda: remove_from_cart(request_for(user), 7)):
                with self.subTest(user=user), self.assertRaises(CartError):
                    call()
        self.cursor.callproc.assert_not_called()

    @override_settings(CART_UPDATE_RATE_LIMIT=2)
    def test_update_and_remove_share_rate_limit(self):
        set_cart_quantity(request_for(customer()), 7, 2)
        remove_from_cart(request_for(customer()), 7)
        with self.assertRaises(CartError) as ctx:
            set_cart_quantity(request_for(customer()), 7, 3)
        self.assertEqual(ctx.exception.code, "RATE_LIMITED")
        self.assertEqual(self.log_event.call_args.args[0], "rate_limited")

    def test_signal_codes_become_cart_errors(self):
        for code in ("NOT_IN_CART", "BOOK_UNAVAILABLE", "OUT_OF_STOCK", "NOT_CUSTOMER"):
            with self.subTest(code=code):
                self.cursor.callproc.side_effect = OperationalError(1644, code)
                with self.assertRaises(CartError) as ctx:
                    set_cart_quantity(request_for(customer()), 7, 2)
                self.assertEqual(ctx.exception.code, code)

    def test_permission_error_not_swallowed(self):
        self.cursor.callproc.side_effect = OperationalError(1370, "execute command denied")
        with self.assertRaises(OperationalError):
            get_cart(request_for(customer()))

    def test_refuses_inside_atomic_block(self):
        self.conn.in_atomic_block = True
        with self.assertRaises(RuntimeError):
            remove_from_cart(request_for(customer()), 7)


class CartPageViewTests(TestCase):
    def setUp(self):
        self.customer = User.objects.create_user(username="an_nguyen", email="an@example.test", password=PASSWORD, email_verified=True)
        self.staff = User.objects.create_user(username="quan_tri", email="qt@example.test", password=PASSWORD, is_staff=True)
        self.cart_url = reverse("orders:cart")
        self.update_url = reverse("orders:cart_update")
        self.remove_url = reverse("orders:cart_remove")
        for name, value in (("get_cart", Cart(lines=())), ("set_cart_quantity", 2), ("remove_from_cart", None)):
            patcher = mock.patch(f"orders.views.{name}", return_value=value)
            setattr(self, name, patcher.start())
            self.addCleanup(patcher.stop)

    def test_page_lists_lines_and_locks_buttons(self):
        self.get_cart.return_value = Cart(lines=(line(7, 1), line(8, 5), line(9, 2, is_active=False)))
        self.client.force_login(self.customer)
        response = self.client.get(self.cart_url)
        html = response.content.decode()
        self.assertEqual(response.status_code, 200)
        self.assertIn("no-cache", response["Cache-Control"])
        self.assertIn("Ngừng bán", html)
        self.assertIn(reverse("catalog:book_detail", args=[7]), html)
        self.assertNotIn(reverse("catalog:book_detail", args=[9]), html)
        self.assertIn('aria-label="Giảm một cuốn Nhà Giả Kim" disabled', html)
        self.assertIn("474.000", html)

    def test_empty_cart(self):
        self.client.force_login(self.customer)
        self.assertContains(self.client.get(self.cart_url), "Giỏ hàng đang trống.")

    def test_update_and_remove_go_back_to_cart(self):
        self.client.force_login(self.customer)
        response = self.client.post(self.update_url, {"book_id": "7", "quantity": "3", "user_id": "1", "price": "1"})
        self.assertEqual(response["Location"], self.cart_url)
        request, book_id, quantity = self.set_cart_quantity.call_args.args
        self.assertEqual((request.user.pk, book_id, quantity), (self.customer.pk, 7, 3))
        self.assertEqual(self.client.post(self.remove_url, {"book_id": "7"})["Location"], self.cart_url)
        self.assertEqual(self.remove_from_cart.call_args.args[1], 7)

    def test_next_is_ignored(self):
        self.client.force_login(self.customer)
        response = self.client.post(self.remove_url, {"book_id": "7", "next": "https://evil.example/"})
        self.assertEqual(response["Location"], self.cart_url)

    def test_invalid_input_never_calls_service(self):
        self.client.force_login(self.customer)
        for bad in ("0", "6", "abc", ""):
            with self.subTest(bad=bad):
                self.client.post(self.update_url, {"book_id": "7", "quantity": bad})
        self.client.post(self.remove_url, {"book_id": "-1"})
        self.set_cart_quantity.assert_not_called()
        self.remove_from_cart.assert_not_called()

    def test_service_error_shown_as_message(self):
        self.set_cart_quantity.side_effect = CartError("BOOK_UNAVAILABLE")
        self.client.force_login(self.customer)
        response = self.client.post(self.update_url, {"book_id": "7", "quantity": "2"}, follow=True)
        self.assertContains(response, CartError("BOOK_UNAVAILABLE").message)

    def test_anonymous_goes_to_login(self):
        expected = f"{reverse('accounts:login')}?next={self.cart_url}"
        self.assertEqual(self.client.post(self.update_url, {"book_id": "7", "quantity": "2"})["Location"], expected)
        self.assertEqual(self.client.post(self.remove_url, {"book_id": "7"})["Location"], expected)
        self.set_cart_quantity.assert_not_called()
        self.remove_from_cart.assert_not_called()

    def test_staff_refused(self):
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get(self.cart_url)["Location"], reverse("dashboard:index"))
        self.client.post(self.update_url, {"book_id": "7", "quantity": "2"})
        self.client.post(self.remove_url, {"book_id": "7"})
        self.get_cart.assert_not_called()
        self.set_cart_quantity.assert_not_called()
        self.remove_from_cart.assert_not_called()

    def test_post_only_and_csrf(self):
        self.client.force_login(self.customer)
        self.assertEqual(self.client.get(self.update_url).status_code, 405)
        self.assertEqual(self.client.get(self.remove_url).status_code, 405)
        strict = Client(enforce_csrf_checks=True)
        strict.force_login(self.customer)
        self.assertEqual(strict.post(self.update_url, {"book_id": "7", "quantity": "2"}).status_code, 403)
        self.assertEqual(strict.post(self.remove_url, {"book_id": "7"}).status_code, 403)
        self.set_cart_quantity.assert_not_called()
        self.remove_from_cart.assert_not_called()
