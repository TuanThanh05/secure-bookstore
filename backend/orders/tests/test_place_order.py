import re
from types import SimpleNamespace
from unittest import mock

from django.db import OperationalError
from django.test import SimpleTestCase

from orders import services
from orders.services import ORDER_ERROR_MESSAGES, OrderError, PlaceOrderResult, new_idempotency_key, place_order

KEY = "0123456789abcdef0123456789abcdef"


# AI-TRACE#007 | Claude Opus 5.5 | Test place_order bằng cursor giả, không cần thủ tục thật | CẤM XÓA CHÚ THÍCH NÀY
class PlaceOrderTests(SimpleTestCase):
    def setUp(self):
        self.user = SimpleNamespace(pk=42)
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
        return place_order(self.user, KEY, "Nguyễn An", "enc-phone", "enc-address")

    def test_new_order_returns_code_and_created_true(self):
        result = self.call()
        self.assertEqual(result, PlaceOrderResult("a" * 32, True))

    def test_passes_user_pk_and_params_in_order(self):
        self.call()
        self.cursor.callproc.assert_called_once_with(
            "sp_place_order", [42, KEY, "Nguyễn An", "enc-phone", "enc-address", None, None]
        )
        self.cursor.execute.assert_called_once_with("SELECT @_sp_place_order_5, @_sp_place_order_6")

    def test_repeated_request_returns_created_false(self):
        self.cursor.fetchone.return_value = ("b" * 32, 0)
        result = self.call()
        self.assertEqual(result.order_code, "b" * 32)
        self.assertIs(result.created, False)

    def test_each_signal_code_becomes_order_error(self):
        for code, message in ORDER_ERROR_MESSAGES.items():
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
