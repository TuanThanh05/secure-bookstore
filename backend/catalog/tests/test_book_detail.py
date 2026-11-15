import secrets
from datetime import datetime
from unittest import mock

from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from accounts.models import User
from catalog.review_services import MyReview, PublicReview, ReviewError
from catalog.services import BookCard

PASSWORD = secrets.token_urlsafe(12) + "-Aa9"
VIEWS = "catalog.views"
BOOK = BookCard(7, "Nhà Giả Kim", "Paulo Coelho", 4, 79000, 4.5, 2, True, isbn="9780306406157",
                description="Dòng 1\nDòng 2", category_name="Văn học")
REVIEWS = [PublicReview("a*******n", 4, "Hay <script>alert(1)</script>", datetime(2026, 11, 15, 9), datetime(2026, 11, 15, 10)),
           PublicReview("k******e", 5, "Tuyệt", datetime(2026, 11, 14), datetime(2026, 11, 14))]


# AI-TRACE#223 | Claude Opus 5.5 | Test trang chi tiết sách và gửi đánh giá: 404 sách ẩn, form theo loại người xem, CSRF, chỉ POST, escape nội dung | CẤM XÓA CHÚ THÍCH NÀY
class BookDetailViewTests(TestCase):
    def setUp(self):
        cache.clear()
        self.detail = reverse("catalog:book_detail", args=[7])
        self.submit = reverse("catalog:review_submit", args=[7])
        self.customer = User.objects.create_user(username="an_nguyen", email="an@example.test", password=PASSWORD, email_verified=True)
        self.staff = User.objects.create_user(username="quan_tri", email="qt@example.test", password=PASSWORD, is_staff=True)
        self.mocks = {}
        for name, value in {"services.get_public_book": BOOK, "list_reviews": REVIEWS, "get_my_review": None, "save_review": True}.items():
            patcher = mock.patch(f"{VIEWS}.{name}", return_value=value)
            self.mocks[name] = patcher.start()
            self.addCleanup(patcher.stop)

    def test_anonymous_sees_book_reviews_and_login_link(self):
        response = self.client.get(self.detail)
        html = response.content.decode()
        self.assertEqual(response.status_code, 200)
        self.assertIn("Nhà Giả Kim", html)
        self.assertIn("Dòng 1<br>Dòng 2", html)
        self.assertIn("a*******n", html)
        self.assertIn("đã sửa", html)
        self.assertIn(f"{reverse('accounts:login')}?next={self.detail}", html)
        self.assertNotIn("<form method=\"post\" action=\"" + self.submit, html)
        self.assertIn('type="button" disabled', html)

    def test_review_content_is_escaped(self):
        html = self.client.get(self.detail).content.decode()
        self.assertNotIn("<script>alert(1)</script>", html)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", html)

    def test_hidden_or_missing_book_is_404(self):
        self.mocks["services.get_public_book"].return_value = None
        self.assertEqual(self.client.get(self.detail).status_code, 404)
        self.client.force_login(self.customer)
        self.assertEqual(self.client.post(self.submit, {"rating": "5", "content": "Hay"}).status_code, 404)
        self.mocks["save_review"].assert_not_called()

    def test_customer_sees_form_and_existing_review_is_prefilled(self):
        self.mocks["get_my_review"].return_value = MyReview(3, "Bình thường", False)
        self.client.force_login(self.customer)
        html = self.client.get(self.detail).content.decode()
        self.assertIn("Sửa đánh giá", html)
        self.assertIn("Bình thường</textarea>", html)
        self.assertIn("đang bị quản trị viên ẩn", html)

    def test_staff_gets_no_form_and_cannot_post(self):
        self.client.force_login(self.staff)
        self.assertNotIn(self.submit, self.client.get(self.detail).content.decode())
        self.client.post(self.submit, {"rating": "5", "content": "Hay"})
        self.mocks["save_review"].assert_not_called()

    def test_anonymous_post_goes_to_login_with_detail_as_next(self):
        response = self.client.post(self.submit, {"rating": "5", "content": "Hay"})
        self.assertEqual(response["Location"], f"{reverse('accounts:login')}?next={self.detail}")
        self.mocks["save_review"].assert_not_called()

    def test_submit_saves_and_redirects(self):
        self.client.force_login(self.customer)
        response = self.client.post(self.submit, {"rating": "4", "content": "  Hay  ", "user_id": str(self.staff.pk)})
        self.assertEqual(response["Location"], f"{self.detail}#danh-gia")
        request, book_id, rating, content = self.mocks["save_review"].call_args.args
        self.assertEqual((request.user.pk, book_id, rating, content), (self.customer.pk, 7, 4, "Hay"))

    def test_invalid_form_reopens_with_errors(self):
        self.client.force_login(self.customer)
        response = self.client.post(self.submit, {"rating": "9", "content": ""})
        self.assertEqual(response.status_code, 400)
        self.assertContains(response, 'class="review-form" open', status_code=400)
        self.mocks["save_review"].assert_not_called()

    def test_service_error_is_shown(self):
        self.mocks["save_review"].side_effect = ReviewError("RATE_LIMITED")
        self.client.force_login(self.customer)
        response = self.client.post(self.submit, {"rating": "5", "content": "Hay"})
        self.assertContains(response, ReviewError("RATE_LIMITED").message, status_code=400)

    def test_submit_requires_post_and_csrf(self):
        self.client.force_login(self.customer)
        self.assertEqual(self.client.get(self.submit).status_code, 405)
        strict = Client(enforce_csrf_checks=True)
        strict.force_login(self.customer)
        self.assertEqual(strict.post(self.submit, {"rating": "5", "content": "Hay"}).status_code, 403)
        self.mocks["save_review"].assert_not_called()

    def test_no_inline_script_or_style(self):
        html = self.client.get(self.detail).content.decode()
        self.assertNotIn("<script>", html.replace("&lt;script&gt;", ""))
        self.assertNotIn(" style=", html)
        self.assertNotIn(" onclick=", html)
