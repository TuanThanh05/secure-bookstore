import datetime
import secrets
from types import SimpleNamespace
from unittest import mock

from django.db import OperationalError
from django.test import Client, SimpleTestCase, TestCase
from django.urls import reverse

from accounts.models import User
from core.crypto import encrypt_field
from orders import services
from orders.cart_services import Cart, CartLine
from orders.forms import CheckoutForm
from orders.services import Order, OrderError, OrderLine, PlaceOrderResult, get_order, shipping_context

PASSWORD = secrets.token_urlsafe(12) + "-Aa9"
CODE = "a" * 32
KEY = "b" * 32


def cart_line(book_id=7, quantity=2, is_active=True, in_stock=True):
    return CartLine(book_id=book_id, title="Nhà Giả Kim", author="Paulo Coelho", cover_image=None, price=79000,
                    quantity=quantity, is_active=is_active, in_stock=in_stock)


def order(status="pending", minutes_left=10):
    now = datetime.datetime.now(datetime.UTC)
    return Order(code=CODE, status=status, subtotal=158000, shipping_fee=30000, total=188000, shipping_name="Nguyễn An",
                 shipping_phone="0901234567", shipping_address="12 Nguyễn Huệ, Q.1, TP.HCM",
                 created_at=now, expires_at=now + datetime.timedelta(minutes=minutes_left), paid_at=None, cancelled_at=None,
                 lines=(OrderLine(book_id=7, title="Nhà Giả Kim", unit_price=79000, quantity=2),))


# AI-TRACE#278 | Claude Opus 5.5 | Test form giao hàng: chuẩn hóa SĐT, chặn tên có thẻ HTML/ký tự lạ, địa chỉ quá ngắn, bỏ ký tự vô hình | CẤM XÓA CHÚ THÍCH NÀY
class CheckoutFormTests(SimpleTestCase):
    def form(self, **data):
        payload = {"shipping_name": "Nguyễn  Văn An", "phone": "+84 901 234 567", "address": "12 Nguyễn Huệ,\n Q.1, TP.HCM"}
        payload.update(data)
        return CheckoutForm(payload)

    def test_valid_data_is_normalised(self):
        form = self.form()
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data, {"shipping_name": "Nguyễn Văn An", "phone": "0901234567",
                                             "address": "12 Nguyễn Huệ, Q.1, TP.HCM"})

    def test_rejects_bad_values(self):
        for field, value in (("shipping_name", "<script>alert(1)</script>"), ("shipping_name", "An123"),
                             ("shipping_name", ""), ("phone", "0123456789"), ("phone", "09012345"),
                             ("address", "abc"), ("address", "1234567890123"), ("address", "x" * 256)):
            with self.subTest(field=field, value=value):
                self.assertIn(field, self.form(**{field: value}).errors)

    def test_invisible_characters_removed(self):
        form = self.form(address="12 Nguy\u202een Hu\u200bệ, Q.1, TP.HCM")
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["address"], "12 Nguyen Huệ, Q.1, TP.HCM")


# AI-TRACE#279 | Claude Opus 5.5 | Test get_order bằng cursor giả: mã đơn sai mẫu không xuống CSDL, giải mã đúng ngữ cảnh, đơn người khác báo không tìm thấy, hạn thanh toán | CẤM XÓA CHÚ THÍCH NÀY
class GetOrderServiceTests(SimpleTestCase):
    def setUp(self):
        self.user = SimpleNamespace(pk=42, is_authenticated=True, is_staff=False)
        self.request = SimpleNamespace(user=self.user)
        created = datetime.datetime(2026, 11, 16, 0, 0)
        self.cursor = mock.MagicMock()
        self.cursor.nextset.side_effect = [True, None]
        self.cursor.fetchone.return_value = (
            CODE, "pending", 158000, 30000, 188000, "Nguyễn An",
            encrypt_field("0901234567", shipping_context("shipping_phone_encrypted", 42, KEY)),
            encrypt_field("12 Nguyễn Huệ", shipping_context("shipping_address_encrypted", 42, KEY)),
            KEY, created, created + datetime.timedelta(minutes=15), None, None)
        self.cursor.fetchall.return_value = [(7, "Nhà Giả Kim", 79000, 2)]
        conn = mock.MagicMock(in_atomic_block=False)
        conn.cursor.return_value.__enter__.return_value = self.cursor
        patcher = mock.patch.object(services, "connection", conn)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_reads_and_decrypts(self):
        result = get_order(self.request, CODE)
        self.cursor.callproc.assert_called_once_with("sp_order_get", [42, CODE])
        self.assertEqual((result.shipping_phone, result.shipping_address), ("0901234567", "12 Nguyễn Huệ"))
        self.assertEqual(result.lines[0].line_total, 158000)
        self.assertEqual(result.expires_at.tzinfo, datetime.UTC)
        self.assertFalse(hasattr(result, "idempotency_key"))

    def test_wrong_context_does_not_crash(self):
        header = list(self.cursor.fetchone.return_value)
        header[8] = "c" * 32
        self.cursor.fetchone.return_value = tuple(header)
        result = get_order(self.request, CODE)
        self.assertIsNone(result.shipping_phone)

    def test_bad_code_never_reaches_database(self):
        for bad in ("A" * 32, "abc", "a" * 31 + "' OR 1=1 --", None):
            with self.subTest(bad=bad), self.assertRaises(OrderError) as ctx:
                get_order(self.request, bad)
            self.assertEqual(ctx.exception.code, "ORDER_NOT_FOUND")
        self.cursor.callproc.assert_not_called()

    def test_other_users_order_is_not_found(self):
        self.cursor.callproc.side_effect = OperationalError(1644, "ORDER_NOT_FOUND")
        with self.assertRaises(OrderError):
            get_order(self.request, CODE)

    def test_expiry_flags(self):
        self.assertTrue(order().awaiting_payment)
        self.assertTrue(order(minutes_left=-1).expired)
        self.assertFalse(order(status="paid").awaiting_payment)


# AI-TRACE#280 | Claude Opus 5.5 | Test view đặt hàng và xem đơn: giỏ phải sạch, mã chống trùng chỉ trong phiên, giá/user_id từ form bị bỏ qua, IDOR trả 404, CSRF, nhân viên bị từ chối | CẤM XÓA CHÚ THÍCH NÀY
class CheckoutViewTests(TestCase):
    def setUp(self):
        self.customer = User.objects.create_user(username="an_nguyen", email="an@example.test", password=PASSWORD,
                                                 email_verified=True, first_name="An", last_name="Nguyễn")
        self.staff = User.objects.create_user(username="quan_tri", email="qt@example.test", password=PASSWORD, is_staff=True)
        self.url = reverse("orders:checkout")
        self.data = {"shipping_name": "Nguyễn An", "phone": "0901234567", "address": "12 Nguyễn Huệ, Q.1, TP.HCM"}
        for name, value in (("get_cart", Cart(lines=(cart_line(),))), ("place_order", PlaceOrderResult(CODE, True)),
                            ("get_order", order())):
            patcher = mock.patch(f"orders.views.{name}", return_value=value)
            setattr(self, name, patcher.start())
            self.addCleanup(patcher.stop)

    def test_get_shows_summary_and_prefill(self):
        self.client.force_login(self.customer)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("no-cache", response["Cache-Control"])
        self.assertContains(response, "188.000")
        self.assertContains(response, 'value="Nguyễn An"')

    def test_empty_or_unavailable_cart_goes_back(self):
        self.client.force_login(self.customer)
        for cart_data in (Cart(lines=()), Cart(lines=(cart_line(), cart_line(8, in_stock=False)))):
            with self.subTest(cart=cart_data):
                self.get_cart.return_value = cart_data
                self.assertEqual(self.client.get(self.url)["Location"], reverse("orders:cart"))
        self.place_order.assert_not_called()

    def test_success_uses_session_key_and_ignores_client_values(self):
        self.client.force_login(self.customer)
        self.client.get(self.url)
        key = self.client.session["checkout_idempotency_key"]
        response = self.client.post(self.url, {**self.data, "total": "1", "user_id": "1", "idempotency_key": "c" * 32})
        self.assertEqual(response["Location"], reverse("orders:order_detail", args=[CODE]))
        request, sent_key, name, phone, address = self.place_order.call_args.args
        self.assertEqual((request.user.pk, sent_key, name, phone, address),
                         (self.customer.pk, key, "Nguyễn An", "0901234567", "12 Nguyễn Huệ, Q.1, TP.HCM"))
        self.assertNotIn("checkout_idempotency_key", self.client.session)
        self.assertEqual(self.client.session["last_order_code"], CODE)

    def test_double_submit_reuses_same_key(self):
        self.client.force_login(self.customer)
        self.client.get(self.url)
        self.place_order.side_effect = OrderError("RATE_LIMITED")
        self.client.post(self.url, self.data)
        self.client.post(self.url, self.data)
        keys = {call.args[1] for call in self.place_order.call_args_list}
        self.assertEqual(len(keys), 1)

    def test_invalid_form_returns_400_without_calling(self):
        self.client.force_login(self.customer)
        response = self.client.post(self.url, {**self.data, "phone": "123"})
        self.assertEqual(response.status_code, 400)
        self.place_order.assert_not_called()

    def test_errors(self):
        self.client.force_login(self.customer)
        for code, target in (("OUT_OF_STOCK", reverse("orders:cart")), ("BOOK_INACTIVE", reverse("orders:cart"))):
            with self.subTest(code=code):
                self.place_order.side_effect = OrderError(code)
                self.assertEqual(self.client.post(self.url, self.data)["Location"], target)
        self.place_order.side_effect = OrderError("PENDING_EXISTS")
        session = self.client.session
        session["last_order_code"] = CODE
        session.save()
        self.assertEqual(self.client.post(self.url, self.data)["Location"], reverse("orders:order_detail", args=[CODE]))

    def test_order_detail_and_idor(self):
        self.client.force_login(self.customer)
        response = self.client.get(reverse("orders:order_detail", args=[CODE]))
        self.assertContains(response, "Chờ thanh toán")
        self.assertContains(response, "12 Nguyễn Huệ")
        self.assertNotContains(response, KEY)
        self.assertIn("no-cache", response["Cache-Control"])
        self.get_order.side_effect = OrderError("ORDER_NOT_FOUND")
        self.assertEqual(self.client.get(reverse("orders:order_detail", args=["f" * 32])).status_code, 404)

    def test_access_control(self):
        detail = reverse("orders:order_detail", args=[CODE])
        self.assertTrue(self.client.get(self.url)["Location"].startswith(reverse("accounts:login")))
        self.assertTrue(self.client.get(detail)["Location"].startswith(reverse("accounts:login")))
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get(self.url)["Location"], reverse("dashboard:index"))
        self.assertEqual(self.client.get(detail)["Location"], reverse("dashboard:index"))
        self.assertEqual(self.client.post(detail).status_code, 405)
        strict = Client(enforce_csrf_checks=True)
        strict.force_login(self.customer)
        self.assertEqual(strict.post(self.url, self.data).status_code, 403)
        self.place_order.assert_not_called()


# AI-TRACE#281 | Claude Opus 5.5 | Test nút Đặt hàng ở trang chi tiết sách: thêm vào giỏ rồi chuyển sang giỏ | CẤM XÓA CHÚ THÍCH NÀY
class BuyNowButtonTests(TestCase):
    def setUp(self):
        self.customer = User.objects.create_user(username="an_nguyen", email="an@example.test", password=PASSWORD, email_verified=True)
        patcher = mock.patch("orders.views.add_to_cart", return_value=1)
        self.add = patcher.start()
        self.addCleanup(patcher.stop)

    def test_then_cart_redirects_to_cart(self):
        self.client.force_login(self.customer)
        response = self.client.post(reverse("orders:cart_add"), {"book_id": "7", "quantity": "1", "then": "cart",
                                                                 "next": reverse("catalog:book_detail", args=[7])})
        self.assertEqual(response["Location"], reverse("orders:cart"))
        self.add.assert_called_once()
