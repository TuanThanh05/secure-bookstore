import re
from types import SimpleNamespace
from unittest import mock

from django.core.cache import cache
from django.db import OperationalError
from django.conf import settings
from django.test import SimpleTestCase, override_settings

from core.crypto import decrypt_field
from orders import services
from orders.services import (ORDER_ERROR_MESSAGES, OrderError, PlaceOrderResult, new_idempotency_key, place_order,
                             shipping_context)

KEY = "0123456789abcdef0123456789abcdef"


# AI-TRACE#007 | Claude Opus 5.5 | Test place_order bằng cursor giả: user lấy từ phiên, SĐT/địa chỉ được mã hóa theo ngữ cảnh đơn, giới hạn tần suất, đổi lỗi SIGNAL | CẤM XÓA CHÚ THÍCH NÀY | đã viết lại bởi Claude Opus 5.5 khi truyền thời gian giữ kho và số cuốn tối đa
@override_settings(ORDER_PLACE_RATE_LIMIT=100, ORDER_PLACE_RATE_WINDOW=600)
class PlaceOrderTests(SimpleTestCase):
    def setUp(self):
        cache.clear()
        self.user = SimpleNamespace(pk=42, is_authenticated=True, is_staff=False, get_username=lambda: "an_nguyen")
        self.request = SimpleNamespace(user=self.user, META={"REMOTE_ADDR": "127.0.0.1"}, method="POST", path="/orders/dat-hang/")
        log_patcher = mock.patch.object(services, "log_event")
        self.log_event = log_patcher.start()
        self.addCleanup(log_patcher.stop)
        self.cursor = mock.MagicMock()
        self.cursor.nextset.return_value = None
        self.cursor.fetchone.return_value = ("a" * 32, 1)
        conn = mock.MagicMock()
        conn.in_atomic_block = False
        conn.cursor.return_value.__enter__.return_value = self.cursor
        patcher = mock.patch.object(services, "connection", conn)
        self.connection = patcher.start()
        self.addCleanup(patcher.stop)

    def call(self):
        return place_order(self.request, KEY, "Nguyễn An", "0901234567", "12 Nguyễn Huệ, Q.1")

    def test_new_order_returns_code_and_created_true(self):
        result = self.call()
        self.assertEqual(result, PlaceOrderResult("a" * 32, True))

    def test_passes_user_pk_and_encrypted_shipping(self):
        self.call()
        proc, params = self.cursor.callproc.call_args.args
        self.assertEqual(proc, "sp_place_order")
        self.assertEqual(params[:3], [42, KEY, "Nguyễn An"])
        self.assertEqual(params[5:], [settings.ORDER_HOLD_MINUTES, settings.ORDER_MAX_ITEMS, None, None])
        self.assertEqual(params[5:7], [5, 20])
        self.assertNotIn("0901234567", params[3])
        self.assertEqual(decrypt_field(params[3], shipping_context("shipping_phone_encrypted", 42, KEY)), "0901234567")
        self.assertEqual(decrypt_field(params[4], shipping_context("shipping_address_encrypted", 42, KEY)), "12 Nguyễn Huệ, Q.1")
        self.cursor.execute.assert_called_once_with("SELECT @_sp_place_order_7, @_sp_place_order_8")

    def test_ciphertext_bound_to_order_context(self):
        self.call()
        phone_enc = self.cursor.callproc.call_args.args[1][3]
        from core.crypto import DecryptionError
        for context in (shipping_context("shipping_phone_encrypted", 43, KEY),
                        shipping_context("shipping_phone_encrypted", 42, "f" * 32),
                        shipping_context("shipping_address_encrypted", 42, KEY)):
            with self.subTest(context=context), self.assertRaises(DecryptionError):
                decrypt_field(phone_enc, context)

    def test_staff_anonymous_and_bad_key_refused(self):
        for user in (SimpleNamespace(pk=2, is_authenticated=True, is_staff=True),
                     SimpleNamespace(pk=None, is_authenticated=False, is_staff=False)):
            with self.subTest(user=user), self.assertRaises(OrderError):
                place_order(SimpleNamespace(user=user), KEY, "A", "0901234567", "12 Nguyễn Huệ")
        for bad in ("A" * 32, "abc", None, KEY + "0"):
            with self.subTest(bad=bad), self.assertRaises(OrderError) as ctx:
                place_order(self.request, bad, "A", "0901234567", "12 Nguyễn Huệ")
            self.assertEqual(ctx.exception.code, "INVALID_INPUT")
        self.cursor.callproc.assert_not_called()

    @override_settings(ORDER_PLACE_RATE_LIMIT=2)
    def test_rate_limited_and_logged(self):
        self.call()
        self.call()
        with self.assertRaises(OrderError) as ctx:
            self.call()
        self.assertEqual(ctx.exception.code, "RATE_LIMITED")
        self.assertEqual(self.cursor.callproc.call_count, 2)
        self.assertEqual(self.log_event.call_args.args[0], "rate_limited")

    def test_repeated_request_returns_created_false(self):
        self.cursor.fetchone.return_value = ("b" * 32, 0)
        result = self.call()
        self.assertEqual(result.order_code, "b" * 32)
        self.assertIs(result.created, False)

    def test_each_signal_code_becomes_order_error(self):
        for code, message in ORDER_ERROR_MESSAGES.items():
            if code == "RATE_LIMITED":
                continue
            with self.subTest(code=code):
                self.cursor.callproc.side_effect = OperationalError(1644, code)
                with self.assertRaises(OrderError) as ctx:
                    self.call()
                self.assertEqual(ctx.exception.code, code)
                self.assertEqual(ctx.exception.message, message)

    def test_permission_error_is_not_swallowed(self):
        self.cursor.callproc.side_effect = OperationalError(1142, "command denied")
        with self.assertRaises(OperationalError):
            self.call()

    def test_unknown_signal_text_is_not_swallowed(self):
        self.cursor.callproc.side_effect = OperationalError(1644, "SOMETHING_ELSE")
        with self.assertRaises(OperationalError):
            self.call()

    def test_error_message_does_not_leak_sql_details(self):
        self.cursor.callproc.side_effect = OperationalError(1644, "OUT_OF_STOCK")
        with self.assertRaises(OrderError) as ctx:
            self.call()
        self.assertNotIn("sp_place_order", str(ctx.exception))
        self.assertNotIn("catalog_book", str(ctx.exception))

    def test_refuses_to_run_inside_atomic_block(self):
        self.connection.in_atomic_block = True
        with self.assertRaises(RuntimeError):
            self.call()
        self.cursor.callproc.assert_not_called()

    def test_idempotency_key_format_and_uniqueness(self):
        keys = {new_idempotency_key() for _ in range(100)}
        self.assertEqual(len(keys), 100)
        for key in keys:
            self.assertRegex(key, re.compile(r"^[0-9a-f]{32}$"))
