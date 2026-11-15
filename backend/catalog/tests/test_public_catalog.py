from datetime import datetime
from decimal import Decimal
from unittest import mock

from django.test import SimpleTestCase, override_settings

from catalog import services
from catalog.services import BookCard, get_public_book, list_categories, list_public_books

ROW = (7, "Nhà Giả Kim", "Paulo Coelho", "9780306406157", 4, "Hành trình", 79000, None,
       datetime(2026, 11, 15, 9, 0), 1, Decimal("4.5"), 2)


# AI-TRACE#197 | Claude Opus 5.5 | Test service danh mục cho khách: gọi đúng thủ tục bằng kết nối app_customer, tham số truyền riêng, đổi dòng thành BookCard | CẤM XÓA CHÚ THÍCH NÀY
class PublicCatalogServiceTests(SimpleTestCase):
    def setUp(self):
        self.cursor = mock.MagicMock()
        self.cursor.nextset.return_value = None
        self.cursor.fetchall.return_value = [ROW]
        conn = mock.MagicMock()
        conn.cursor.return_value.__enter__.return_value = self.cursor
        patcher = mock.patch.object(services, "connection", conn)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_categories_call_procedure(self):
        self.cursor.fetchall.return_value = [(1, "Văn học", "van-hoc")]
        categories = list_categories()
        self.cursor.callproc.assert_called_once_with("sp_public_category_list", [])
        self.assertEqual((categories[0].id, categories[0].name, categories[0].slug), (1, "Văn học", "van-hoc"))

    def test_books_call_procedure_with_separate_parameters(self):
        list_public_books(category_id=4, q="  giả   kim ")
        self.cursor.callproc.assert_called_once_with("sp_public_book_list", [4, "giả kim"])

    def test_empty_query_and_no_category_send_null(self):
        list_public_books()
        self.cursor.callproc.assert_called_once_with("sp_public_book_list", [None, None])

    def test_query_is_cut_to_100_characters(self):
        list_public_books(q="a" * 300)
        self.assertEqual(len(self.cursor.callproc.call_args.args[1][1]), 100)

    def test_sql_injection_payload_is_only_a_parameter(self):
        payload = "%' UNION SELECT password FROM accounts_user -- "
        list_public_books(q=payload)
        procedure, params = self.cursor.callproc.call_args.args
        self.assertEqual(procedure, "sp_public_book_list")
        self.assertEqual(params[1], payload.strip())
        self.cursor.execute.assert_not_called()

    def test_row_becomes_book_card_without_secret_columns(self):
        book = list_public_books()[0]
        self.assertIsInstance(book, BookCard)
        self.assertEqual((book.id, book.title, book.price, book.in_stock, book.rating, book.review_count),
                         (7, "Nhà Giả Kim", 79000, True, 4.5, 2))
        self.assertFalse(hasattr(book, "cost_price"))
        self.assertFalse(hasattr(book, "stock"))
        self.assertFalse(hasattr(book, "is_active"))

    def test_out_of_stock_and_no_rating(self):
        self.cursor.fetchall.return_value = [ROW[:9] + (0, None, 0)]
        book = list_public_books()[0]
        self.assertFalse(book.in_stock)
        self.assertIsNone(book.rating)

    @override_settings(MEDIA_URL="/media/", BOOK_DEFAULT_COVER="img/book-cover-default.webp")
    def test_cover_url_uses_upload_or_default(self):
        self.assertTrue(list_public_books()[0].cover_url.endswith("img/book-cover-default.webp"))
        self.cursor.fetchall.return_value = [ROW[:7] + ("covers/" + "c" * 32 + ".webp",) + ROW[8:]]
        self.assertEqual(list_public_books()[0].cover_url, "/media/covers/" + "c" * 32 + ".webp")


# AI-TRACE#224 | Claude Opus 5.5 | Test lấy một sách cho trang chi tiết: id sai không xuống CSDL, sách ẩn trả None, có tên thể loại | CẤM XÓA CHÚ THÍCH NÀY
class PublicBookDetailServiceTests(SimpleTestCase):
    setUp = PublicCatalogServiceTests.setUp

    def test_get_book_returns_card_with_category_name(self):
        self.cursor.fetchall.return_value = [ROW + ("Văn học",)]
        book = get_public_book("7")
        self.cursor.callproc.assert_called_once_with("sp_public_book_get", [7])
        self.assertEqual((book.id, book.category_name), (7, "Văn học"))

    def test_hidden_or_missing_book_is_none(self):
        self.cursor.fetchall.return_value = []
        self.assertIsNone(get_public_book(7))

    def test_bad_id_never_reaches_database(self):
        for bad in ("abc", "7 OR 1=1", 0, -1, None):
            with self.subTest(bad=bad):
                self.assertIsNone(get_public_book(bad))
        self.cursor.callproc.assert_not_called()
