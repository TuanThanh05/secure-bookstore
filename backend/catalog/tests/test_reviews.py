from types import SimpleNamespace
from unittest import mock

from django.core.cache import cache
from django.db import OperationalError
from django.test import SimpleTestCase, override_settings

from catalog import review_services
from catalog.forms import ReviewForm
from catalog.review_services import (
    REVIEW_ERROR_MESSAGES,
    MyReview,
    ReviewError,
    clean_content,
    get_my_review,
    mask_username,
    save_review,
)


def customer(pk=3):
    return SimpleNamespace(pk=pk, is_authenticated=True, is_staff=False, get_username=lambda: "an_nguyen")


def request_for(user):
    return SimpleNamespace(user=user, META={"REMOTE_ADDR": "127.0.0.1"}, method="POST", path="/sach/7/danh-gia/")


# AI-TRACE#209 | Claude Opus 5.5 | Test chuẩn hóa nội dung đánh giá, che username và form đánh giá | CẤM XÓA CHÚ THÍCH NÀY
class ReviewInputTests(SimpleTestCase):
    def test_content_is_cleaned(self):
        self.assertEqual(clean_content("  Hay\r\n\r\n\r\n\r\nlắm \u202e\x00 "), "Hay\n\nlắm")

    def test_html_is_kept_as_text_for_escaping_later(self):
        self.assertEqual(clean_content("<script>alert(1)</script>"), "<script>alert(1)</script>")

    def test_bad_content_is_rejected(self):
        for bad in ("", "   \n\t ", None, "x" * 2001, "\u200b\u200b"):
            with self.subTest(bad=bad), self.assertRaises(ReviewError):
                clean_content(bad)

    def test_mask_username_keeps_first_and_last(self):
        self.assertEqual(mask_username("an_nguyen"), "a*******n")
        self.assertEqual(mask_username("abc"), "a*c")
        self.assertEqual(mask_username("ab"), "a*")
        self.assertEqual(mask_username("a"), "*")
        self.assertEqual(mask_username(""), "*")

    def test_form_accepts_only_one_to_five_stars(self):
        self.assertTrue(ReviewForm({"rating": "5", "content": "Hay"}).is_valid())
        for bad in ("0", "6", "-1", "5 OR 1=1", ""):
            with self.subTest(bad=bad):
                self.assertFalse(ReviewForm({"rating": bad, "content": "Hay"}).is_valid())

    def test_form_has_no_user_or_book_field(self):
        self.assertEqual(set(ReviewForm().fields), {"rating", "content"})
        form = ReviewForm({"rating": "4", "content": "Hay", "user_id": "1", "book_id": "2"})
        self.assertTrue(form.is_valid())
        self.assertEqual(set(form.cleaned_data), {"rating", "content"})


# AI-TRACE#210 | Claude Opus 5.5 | Test gửi đánh giá bằng cursor giả: user lấy từ phiên, chặn nhân viên, giới hạn tần suất, đổi lỗi SIGNAL | CẤM XÓA CHÚ THÍCH NÀY
@override_settings(REVIEW_RATE_LIMIT=5, REVIEW_RATE_WINDOW=3600)
class SaveReviewTests(SimpleTestCase):
    def setUp(self):
        cache.clear()
        self.cursor = mock.MagicMock()
        self.cursor.nextset.return_value = None
        self.cursor.fetchone.return_value = (1,)
        self.conn = mock.MagicMock(in_atomic_block=False)
        self.conn.cursor.return_value.__enter__.return_value = self.cursor
        patcher = mock.patch.object(review_services, "connection", self.conn)
        patcher.start()
        self.addCleanup(patcher.stop)
        log_patcher = mock.patch.object(review_services, "log_event")
        self.log_event = log_patcher.start()
        self.addCleanup(log_patcher.stop)

    def test_user_id_comes_from_session_not_input(self):
        self.assertTrue(save_review(request_for(customer(3)), "7", "5", "  Hay "))
        self.cursor.callproc.assert_called_once_with("sp_review_save", [3, 7, 5, "Hay", None])
        self.cursor.execute.assert_called_once_with("SELECT @_sp_review_save_4")

    def test_update_returns_false(self):
        self.cursor.fetchone.return_value = (0,)
        self.assertFalse(save_review(request_for(customer()), 7, 3, "Sửa lại"))

    def test_staff_and_anonymous_are_refused_before_database(self):
        staff = SimpleNamespace(pk=2, is_authenticated=True, is_staff=True)
        anonymous = SimpleNamespace(pk=None, is_authenticated=False, is_staff=False)
        for user in (staff, anonymous):
            with self.subTest(user=user), self.assertRaises(ReviewError) as ctx:
                save_review(request_for(user), 7, 5, "Hay")
            self.assertEqual(ctx.exception.code, "NOT_CUSTOMER")
        self.cursor.callproc.assert_not_called()

    def test_bad_rating_and_book_never_reach_database(self):
        for book_id, rating, code in [(7, 0, "INVALID_INPUT"), (7, 6, "INVALID_INPUT"), (7, "5'", "INVALID_INPUT"),
                                      (7, True, "INVALID_INPUT"), ("7 OR 1=1", 5, "BOOK_NOT_FOUND"), (0, 5, "BOOK_NOT_FOUND")]:
            with self.subTest(book_id=book_id, rating=rating), self.assertRaises(ReviewError) as ctx:
                save_review(request_for(customer()), book_id, rating, "Hay")
            self.assertEqual(ctx.exception.code, code)
        self.cursor.callproc.assert_not_called()

    def test_sixth_review_in_window_is_rate_limited_and_logged(self):
        for _ in range(5):
            save_review(request_for(customer()), 7, 5, "Hay")
        with self.assertRaises(ReviewError) as ctx:
            save_review(request_for(customer()), 7, 5, "Hay")
        self.assertEqual(ctx.exception.code, "RATE_LIMITED")
        self.assertEqual(self.cursor.callproc.call_count, 5)
        self.assertEqual(self.log_event.call_args.args[0], "rate_limited")

    def test_rate_limit_is_per_user(self):
        for _ in range(5):
            save_review(request_for(customer(3)), 7, 5, "Hay")
        self.assertTrue(save_review(request_for(customer(4)), 7, 5, "Hay"))

    def test_each_signal_code_becomes_review_error(self):
        for code in ("INVALID_INPUT", "NOT_CUSTOMER", "BOOK_NOT_FOUND"):
            with self.subTest(code=code):
                cache.clear()
                self.cursor.callproc.side_effect = OperationalError(1644, code)
                with self.assertRaises(ReviewError) as ctx:
                    save_review(request_for(customer()), 7, 5, "Hay")
                self.assertEqual(ctx.exception.message, REVIEW_ERROR_MESSAGES[code])

    def test_permission_error_is_not_swallowed(self):
        self.cursor.callproc.side_effect = OperationalError(1370, "execute command denied")
        with self.assertRaises(OperationalError):
            save_review(request_for(customer()), 7, 5, "Hay")

    def test_refuses_inside_atomic_block(self):
        self.conn.in_atomic_block = True
        with self.assertRaises(RuntimeError):
            save_review(request_for(customer()), 7, 5, "Hay")

    def test_get_my_review(self):
        self.cursor.fetchone.return_value = (4, "Hay", 0, None, None)
        self.assertEqual(get_my_review(customer(3), "7"), MyReview(4, "Hay", False, None, None))
        self.cursor.callproc.assert_called_once_with("sp_review_get_mine", [3, 7])

    def test_get_my_review_none_cases(self):
        self.cursor.fetchone.return_value = None
        self.assertIsNone(get_my_review(customer(), 7))
        self.assertIsNone(get_my_review(customer(), "abc"))
        self.assertIsNone(get_my_review(SimpleNamespace(is_authenticated=False, is_staff=False), 7))
