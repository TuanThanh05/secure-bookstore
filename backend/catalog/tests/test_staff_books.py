from types import SimpleNamespace
from unittest import mock

from django.db import OperationalError
from django.test import SimpleTestCase, override_settings

from catalog import staff_services
from catalog.book_services import (
    BOOK_ERROR_MESSAGES,
    BookError,
    clean_book_fields,
    clean_isbn,
    create_book,
    delete_book,
    list_books,
    reduce_book_stock,
    restock_book,
    set_book_active,
    update_book,
)
from catalog.models import StaffBook

VALID = {
    "title": "  Nhà   Giả Kim ",
    "author": "Paulo Coelho",
    "isbn": "978-0-306-40615-7",
    "category_id": "4",
    "description": "  Hành trình  ",
    "price": "79000",
    "cost_price": 50000,
}


# AI-TRACE#143 | Claude Opus 5.5 | Test chuẩn hóa ISBN, kiểm tra chữ số kiểm tra và các giới hạn thông tin sách | CẤM XÓA CHÚ THÍCH NÀY
class BookFieldTests(SimpleTestCase):
    def test_valid_isbn_10_and_13_are_normalized(self):
        self.assertEqual(clean_isbn("978-0-306-40615-7"), "9780306406157")
        self.assertEqual(clean_isbn("0 306 40615 2"), "0306406152")
        self.assertEqual(clean_isbn("0-8044-2957-x"), "080442957X")

    def test_bad_isbn_is_rejected(self):
        for bad in ("9780306406158", "0306406153", "12345", "97803064061X7", "", None, "978030640615７"):
            with self.subTest(bad=bad), self.assertRaises(BookError) as ctx:
                clean_isbn(bad)
            self.assertEqual(ctx.exception.code, "INVALID_ISBN")

    def test_fields_are_cleaned(self):
        fields = clean_book_fields(**VALID)
        self.assertEqual(fields, {
            "title": "Nhà Giả Kim", "author": "Paulo Coelho", "isbn": "9780306406157", "category_id": 4,
            "description": "Hành trình", "price": 79000, "cost_price": 50000,
        })

    def test_blank_description_becomes_none(self):
        self.assertIsNone(clean_book_fields(**{**VALID, "description": "   "})["description"])

    def test_limits(self):
        bad_cases = [
            {"title": ""}, {"title": "a" * 256}, {"author": "  "}, {"description": "x" * 5001},
            {"price": 0}, {"price": 100_000_001}, {"price": "79k"}, {"price": True},
            {"cost_price": -1}, {"cost_price": 100_000_001},
        ]
        for change in bad_cases:
            with self.subTest(change=change), self.assertRaises(BookError) as ctx:
                clean_book_fields(**{**VALID, **change})
            self.assertEqual(ctx.exception.code, "INVALID_INPUT")

    def test_bad_category_id_is_not_found(self):
        for bad in ("abc", 0, -3, "1 OR 1=1"):
            with self.subTest(bad=bad), self.assertRaises(BookError) as ctx:
                clean_book_fields(**{**VALID, "category_id": bad})
            self.assertEqual(ctx.exception.code, "CATEGORY_NOT_FOUND")


# AI-TRACE#144 | Claude Opus 5.5 | Test gọi sáu thủ tục sách bằng cursor giả qua kết nối staff, đổi lỗi SIGNAL thành BookError | CẤM XÓA CHÚ THÍCH NÀY
class BookProcedureTests(SimpleTestCase):
    def setUp(self):
        self.actor = SimpleNamespace(pk=7)
        self.cursor = mock.MagicMock()
        self.cursor.nextset.return_value = None
        self.cursor.fetchone.return_value = (21,)
        self.conn = mock.MagicMock()
        self.conn.in_atomic_block = False
        self.conn.cursor.return_value.__enter__.return_value = self.cursor
        patcher = mock.patch.object(staff_services, "connections", {"staff": self.conn})
        patcher.start()
        self.addCleanup(patcher.stop)
        book_patcher = mock.patch("catalog.book_services.get_book", return_value=SimpleNamespace(cover_image=None))
        book_patcher.start()
        self.addCleanup(book_patcher.stop)

    def test_create_sends_clean_values_and_initial_stock(self):
        self.assertEqual(create_book(self.actor, stock="100", **VALID), 21)
        self.cursor.callproc.assert_called_once_with("sp_book_create", [
            7, "Nhà Giả Kim", "Paulo Coelho", "9780306406157", 4, "Hành trình", None, 79000, 50000, 100, None,
        ])
        self.cursor.execute.assert_called_once_with("SELECT @_sp_book_create_10")

    def test_create_rejects_stock_over_limit_without_database(self):
        for bad in (10_001, -1, "nhiều"):
            with self.subTest(bad=bad), self.assertRaises(BookError) as ctx:
                create_book(self.actor, stock=bad, **VALID)
            self.assertEqual(ctx.exception.code, "INVALID_QUANTITY")
        self.cursor.callproc.assert_not_called()

    def test_update_keeps_current_cover_by_default(self):
        current = SimpleNamespace(cover_image="covers/" + "a" * 32 + ".webp")
        with mock.patch("catalog.book_services.get_book", return_value=current):
            update_book(self.actor, "9", **VALID)
        self.cursor.callproc.assert_called_once_with("sp_book_update", [
            7, 9, "Nhà Giả Kim", "Paulo Coelho", "9780306406157", 4, "Hành trình", current.cover_image, 79000, 50000,
        ])

    def test_update_never_sends_stock(self):
        with mock.patch("catalog.book_services.get_book", return_value=SimpleNamespace(cover_image=None)):
            update_book(self.actor, 9, **VALID)
        self.assertEqual(len(self.cursor.callproc.call_args.args[1]), 10)

    def test_set_active_sends_zero_or_one(self):
        set_book_active(self.actor, 9, False)
        set_book_active(self.actor, 9, "yes")
        self.assertEqual([c.args for c in self.cursor.callproc.call_args_list],
                         [("sp_book_set_active", [7, 9, 0]), ("sp_book_set_active", [7, 9, 1])])

    def test_restock_and_reduce_return_new_stock(self):
        self.assertEqual(restock_book(self.actor, 9, "30"), 21)
        self.cursor.callproc.assert_called_with("sp_book_restock", [7, 9, 30, None])
        self.assertEqual(reduce_book_stock(self.actor, 9, 2), 21)
        self.cursor.callproc.assert_called_with("sp_book_reduce_stock", [7, 9, 2, None])
        self.cursor.execute.assert_called_with("SELECT @_sp_book_reduce_stock_3")

    def test_bad_quantity_never_reaches_database(self):
        for fn in (restock_book, reduce_book_stock):
            for bad in (0, -5, 10_001, "1e3", None):
                with self.subTest(fn=fn.__name__, bad=bad), self.assertRaises(BookError) as ctx:
                    fn(self.actor, 9, bad)
                self.assertEqual(ctx.exception.code, "INVALID_QUANTITY")
        self.cursor.callproc.assert_not_called()

    def test_non_numeric_book_id_is_not_found(self):
        with self.assertRaises(BookError) as ctx:
            delete_book(self.actor, "9; DROP TABLE catalog_book")
        self.assertEqual(ctx.exception.code, "BOOK_NOT_FOUND")
        self.cursor.callproc.assert_not_called()

    def test_each_signal_code_becomes_book_error(self):
        for code, message in BOOK_ERROR_MESSAGES.items():
            with self.subTest(code=code):
                self.cursor.callproc.side_effect = OperationalError(1644, code)
                with self.assertRaises(BookError) as ctx:
                    delete_book(self.actor, 9)
                self.assertEqual((ctx.exception.code, ctx.exception.message), (code, message))

    def test_permission_error_is_not_swallowed(self):
        self.cursor.callproc.side_effect = OperationalError(1370, "execute command denied")
        with self.assertRaises(OperationalError):
            restock_book(self.actor, 9, 1)

    def test_refuses_inside_atomic_block(self):
        self.conn.in_atomic_block = True
        with self.assertRaises(RuntimeError):
            delete_book(self.actor, 9)


# AI-TRACE#145 | Claude Opus 5.5 | Test model sách đọc qua kết nối staff, lọc theo thể loại/tác giả/tên và đường dẫn ảnh bìa | CẤM XÓA CHÚ THÍCH NÀY
class StaffBookReadTests(SimpleTestCase):
    def test_model_reads_view_through_staff_connection(self):
        self.assertEqual(StaffBook.objects.all().db, "staff")
        self.assertEqual(StaffBook._meta.db_table, "v_staff_books")
        self.assertFalse(StaffBook._meta.managed)

    def test_filters_build_parameterized_query(self):
        qs = list_books(category_id="4", author="  paulo  coelho ", title="giả", is_active=True)
        sql, params = qs.query.sql_with_params()
        self.assertIn("v_staff_books", sql)
        self.assertEqual(params[0], 4)
        self.assertIn("%paulo coelho%", params)
        self.assertIn("%giả%", params)
        self.assertNotIn("coelho", sql)

    def test_bad_category_filter_returns_nothing(self):
        self.assertTrue(list_books(category_id="1 OR 1=1").query.is_empty())

    @override_settings(MEDIA_URL="/media/", BOOK_DEFAULT_COVER="img/book-cover-default.webp")
    def test_cover_url_uses_upload_or_default(self):
        self.assertEqual(StaffBook(cover_image="covers/" + "b" * 32 + ".png").cover_url, "/media/covers/" + "b" * 32 + ".png")
        self.assertTrue(StaffBook(cover_image=None).cover_url.endswith("img/book-cover-default.webp"))

    def test_only_hidden_books_can_be_deleted(self):
        self.assertTrue(StaffBook(is_active=False).can_delete)
        self.assertFalse(StaffBook(is_active=True).can_delete)
