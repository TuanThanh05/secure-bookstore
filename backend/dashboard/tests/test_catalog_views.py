import secrets
import time
from io import BytesIO
from unittest import mock

from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse
from PIL import Image

from accounts.models import User
from catalog.book_services import BookError
from catalog.covers import CoverError
from catalog.models import StaffBook
from catalog.staff_services import CategoryError, StaffCategory
from core.decorators import REAUTH_SESSION_KEY

PASSWORD = secrets.token_urlsafe(12) + "-Aa9"
VIEWS = "dashboard.catalog_views"
CATEGORIES = [StaffCategory(4, "Văn học", "van-hoc", 1, 1, None), StaffCategory(5, "Trống", "trong", 0, 0, None)]


def make_book(**overrides):
    values = {"id": 9, "title": "Nhà Giả Kim", "author": "Paulo Coelho", "isbn": "9780306406157", "category_id": 4,
              "description": "Hành trình", "cover_image": None, "price": 79000, "cost_price": 50000, "stock": 6,
              "is_active": True}
    values.update(overrides)
    return StaffBook(**values)


def book_post(**overrides):
    data = {"title": " Nhà  Giả Kim ", "author": "Paulo Coelho", "isbn": "978-0-306-40615-7", "category_id": "4",
            "description": "Hành trình", "price": "79000", "cost_price": "50000"}
    data.update(overrides)
    return data


def jpeg():
    buffer = BytesIO()
    Image.new("RGB", (60, 90), (120, 20, 30)).save(buffer, "JPEG")
    return SimpleUploadedFile("bia.jpg", buffer.getvalue(), content_type="image/jpeg")


# AI-TRACE#182 | Claude Opus 5.5 | Khung test trang kho sách: tài khoản admin, giả lập service, đánh dấu đã xác thực lại | CẤM XÓA CHÚ THÍCH NÀY
class CatalogViewTestBase(TestCase):
    def setUp(self):
        cache.clear()
        self.staff = User.objects.create_user(username="quan_tri", email="qt@example.test", password=PASSWORD, is_staff=True)
        self.client.force_login(self.staff)
        self.services = {}
        for name, value in {
            "list_categories": CATEGORIES, "list_books": [], "get_book": make_book(), "create_book": 21,
            "update_book": None, "restock_book": 16, "reduce_book_stock": 4, "set_book_active": None,
            "delete_book": None, "create_category": 6, "rename_category": None, "delete_category": None,
        }.items():
            patcher = mock.patch(f"{VIEWS}.{name}", return_value=value)
            self.services[name] = patcher.start()
            self.addCleanup(patcher.stop)

    def reauth(self):
        session = self.client.session
        session[REAUTH_SESSION_KEY] = {"user_id": self.staff.pk, "at": int(time.time())}
        session.save()

    def messages_of(self, response):
        return [str(m) for m in response.context["messages"]] if response.context else []


# AI-TRACE#183 | Claude Opus 5.5 | Test phân quyền trang kho sách: ẩn danh phải đăng nhập, khách bị 403, POST thiếu CSRF bị chặn, GET không đổi dữ liệu | CẤM XÓA CHÚ THÍCH NÀY
class CatalogAccessTests(CatalogViewTestBase):
    URLS = [
        ("GET", "dashboard:books", {}), ("GET", "dashboard:book_create", {}), ("GET", "dashboard:book_edit", {"book_id": 9}),
        ("POST", "dashboard:book_restock", {"book_id": 9}), ("POST", "dashboard:book_reduce", {"book_id": 9}),
        ("POST", "dashboard:book_toggle", {"book_id": 9}), ("GET", "dashboard:book_delete", {"book_id": 9}),
        ("GET", "dashboard:categories", {}), ("POST", "dashboard:category_rename", {"category_id": 4}),
        ("GET", "dashboard:category_delete", {"category_id": 5}),
    ]

    def call(self, client, method, name, kwargs):
        url = reverse(name, kwargs=kwargs)
        return client.get(url) if method == "GET" else client.post(url, {})

    def test_anonymous_is_sent_to_login(self):
        anonymous = Client()
        for method, name, kwargs in self.URLS:
            with self.subTest(name=name):
                response = self.call(anonymous, method, name, kwargs)
                self.assertEqual(response.status_code, 302)
                self.assertIn(reverse("accounts:login"), response["Location"])

    def test_customer_is_forbidden(self):
        customer = User.objects.create_user(username="khach", email="k@example.test", password=PASSWORD, email_verified=True)
        client = Client()
        client.force_login(customer)
        for method, name, kwargs in self.URLS:
            with self.subTest(name=name):
                self.assertEqual(self.call(client, method, name, kwargs).status_code, 403)
        self.services["restock_book"].assert_not_called()
        self.services["delete_book"].assert_not_called()

    def test_post_without_csrf_token_is_rejected(self):
        strict = Client(enforce_csrf_checks=True)
        strict.force_login(self.staff)
        response = strict.post(reverse("dashboard:book_restock", kwargs={"book_id": 9}), {"nhap-quantity": "5"})
        self.assertEqual(response.status_code, 403)
        self.services["restock_book"].assert_not_called()

    def test_state_changing_urls_refuse_get(self):
        for name in ("dashboard:book_restock", "dashboard:book_reduce", "dashboard:book_toggle"):
            with self.subTest(name=name):
                self.assertEqual(self.client.get(reverse(name, kwargs={"book_id": 9})).status_code, 405)
        self.assertEqual(self.client.get(reverse("dashboard:category_rename", kwargs={"category_id": 4})).status_code, 405)

    def test_pages_are_not_cached(self):
        response = self.client.get(reverse("dashboard:books"))
        self.assertIn("no-store", response["Cache-Control"])


# AI-TRACE#184 | Claude Opus 5.5 | Test trang danh sách sách: truyền bộ lọc, bỏ qua giá trị lạ, nhãn tồn kho, escape dữ liệu | CẤM XÓA CHÚ THÍCH NÀY
class BookListViewTests(CatalogViewTestBase):
    def test_filters_are_passed_to_service(self):
        self.client.get(reverse("dashboard:books"), {"ten": " giả kim ", "tac_gia": "coelho", "the_loai": "4", "trang_thai": "an"})
        self.services["list_books"].assert_called_once_with(category_id="4", author="coelho", title="giả kim", is_active=False)

    def test_unknown_status_and_bad_page_are_ignored(self):
        response = self.client.get(reverse("dashboard:books"), {"trang_thai": "drop", "trang": "abc"})
        self.assertEqual(response.status_code, 200)
        self.services["list_books"].assert_called_once_with(category_id=None, author=None, title=None, is_active=None)

    def test_table_shows_cost_price_badges_and_escapes_text(self):
        self.services["list_books"].return_value = [
            make_book(id=1, title="<script>alert(1)</script>", stock=0),
            make_book(id=2, title="Sắp hết", stock=10),
            make_book(id=3, title="Còn nhiều", stock=11, is_active=False),
        ]
        html = self.client.get(reverse("dashboard:books")).content.decode()
        self.assertNotIn("<script>alert(1)</script>", html)
        self.assertIn("&lt;script&gt;", html)
        self.assertIn("50.000 ₫", html)
        self.assertEqual(html.count("Hết hàng"), 1)
        self.assertEqual(html.count("dash-badge--warning"), 1)
        self.assertIn("Đang ẩn", html)
        self.assertIn("Văn học", html)

    def test_pagination_keeps_filters(self):
        self.services["list_books"].return_value = [make_book(id=i) for i in range(1, 26)]
        html = self.client.get(reverse("dashboard:books"), {"tac_gia": "coelho"}).content.decode()
        self.assertIn("?tac_gia=coelho&trang=2", html)


# AI-TRACE#185 | Claude Opus 5.5 | Test thêm và sửa sách: gửi dữ liệu sạch, ảnh, gắn lỗi service vào đúng ô, 404 khi không có sách | CẤM XÓA CHÚ THÍCH NÀY
class BookFormViewTests(CatalogViewTestBase):
    def test_create_calls_service_and_redirects_to_edit(self):
        response = self.client.post(reverse("dashboard:book_create"), {**book_post(stock="8"), "cover": jpeg()})
        self.assertRedirects(response, reverse("dashboard:book_edit", kwargs={"book_id": 21}), fetch_redirect_response=False)
        kwargs = self.services["create_book"].call_args.kwargs
        self.assertEqual((kwargs["title"], kwargs["isbn"], kwargs["category_id"], kwargs["price"], kwargs["stock"]),
                         ("Nhà Giả Kim", "9780306406157", 4, 79000, 8))
        self.assertEqual(kwargs["cover_file"].name, "bia.jpg")

    def test_invalid_isbn_never_reaches_service(self):
        response = self.client.post(reverse("dashboard:book_create"), book_post(isbn="9780306406158", stock="1"))
        self.assertContains(response, "chữ số kiểm tra")
        self.services["create_book"].assert_not_called()

    def test_service_errors_land_on_matching_field(self):
        cases = [(BookError("ISBN_EXISTS"), "isbn"), (CoverError("COVER_INVALID"), "cover"),
                 (BookError("CATEGORY_NOT_FOUND"), "category_id"), (BookError("NOT_STAFF"), "__all__")]
        for error, field in cases:
            with self.subTest(code=error.code):
                self.services["create_book"].side_effect = error
                response = self.client.post(reverse("dashboard:book_create"), book_post(stock="1"))
                self.assertEqual(response.status_code, 200)
                self.assertIn(error.message, response.context["form"].errors[field])

    def test_unknown_category_choice_is_rejected_by_form(self):
        response = self.client.post(reverse("dashboard:book_create"), book_post(category_id="999", stock="1"))
        self.assertTrue(response.context["form"].errors["category_id"])
        self.services["create_book"].assert_not_called()

    def test_stock_over_limit_is_rejected_by_form(self):
        response = self.client.post(reverse("dashboard:book_create"), book_post(stock="10001"))
        self.assertTrue(response.context["form"].errors["stock"])

    def test_edit_prefills_and_never_shows_stock_field_in_info_form(self):
        response = self.client.get(reverse("dashboard:book_edit", kwargs={"book_id": 9}))
        self.assertEqual(response.context["form"].initial["isbn"], "9780306406157")
        self.assertNotIn("stock", response.context["form"].fields)

    def test_edit_saves_and_can_remove_cover(self):
        self.services["get_book"].return_value = make_book(cover_image="covers/" + "a" * 32 + ".webp")
        response = self.client.post(reverse("dashboard:book_edit", kwargs={"book_id": 9}), book_post(remove_cover="on"))
        self.assertRedirects(response, reverse("dashboard:book_edit", kwargs={"book_id": 9}), fetch_redirect_response=False)
        self.assertTrue(self.services["update_book"].call_args.kwargs["remove_cover"])

    def test_new_cover_and_remove_cover_together_is_rejected(self):
        response = self.client.post(reverse("dashboard:book_edit", kwargs={"book_id": 9}), {**book_post(remove_cover="on"), "cover": jpeg()})
        self.assertIn("không làm cả hai", str(response.context["form"].errors))
        self.services["update_book"].assert_not_called()

    def test_missing_book_is_404(self):
        self.services["get_book"].side_effect = BookError("BOOK_NOT_FOUND")
        self.assertEqual(self.client.get(reverse("dashboard:book_edit", kwargs={"book_id": 404})).status_code, 404)


# AI-TRACE#186 | Claude Opus 5.5 | Test nhập kho, giảm kho, ẩn hiện: chỉ POST, kiểm tra số lượng, trạng thái rõ ràng, báo lỗi service | CẤM XÓA CHÚ THÍCH NÀY
class BookStockAndStatusTests(CatalogViewTestBase):
    def edit_url(self):
        return reverse("dashboard:book_edit", kwargs={"book_id": 9})

    def test_restock_and_reduce_call_service(self):
        response = self.client.post(reverse("dashboard:book_restock", kwargs={"book_id": 9}), {"nhap-quantity": "10"}, follow=True)
        self.services["restock_book"].assert_called_once_with(self.staff, 9, 10)
        self.assertIn("Đã nhập thêm 10 cuốn. Tồn kho hiện tại: 16.", self.messages_of(response))
        self.client.post(reverse("dashboard:book_reduce", kwargs={"book_id": 9}), {"giam-quantity": "2"})
        self.services["reduce_book_stock"].assert_called_once_with(self.staff, 9, 2)

    def test_bad_quantity_never_reaches_service(self):
        for value in ("0", "-3", "10001", "abc", ""):
            with self.subTest(value=value):
                self.client.post(reverse("dashboard:book_restock", kwargs={"book_id": 9}), {"nhap-quantity": value})
        self.services["restock_book"].assert_not_called()

    def test_service_error_is_shown(self):
        self.services["restock_book"].side_effect = BookError("STOCK_LIMIT")
        response = self.client.post(reverse("dashboard:book_restock", kwargs={"book_id": 9}), {"nhap-quantity": "5"}, follow=True)
        self.assertTrue(any("10.000" in m for m in self.messages_of(response)))

    def test_toggle_uses_explicit_target(self):
        self.client.post(reverse("dashboard:book_toggle", kwargs={"book_id": 9}), {"trang_thai": "an"})
        self.services["set_book_active"].assert_called_once_with(self.staff, 9, False)

    def test_toggle_rejects_unknown_target(self):
        self.client.post(reverse("dashboard:book_toggle", kwargs={"book_id": 9}), {"trang_thai": "1"})
        self.services["set_book_active"].assert_not_called()


# AI-TRACE#187 | Claude Opus 5.5 | Test xóa sách và xóa thể loại: bắt buộc xác thực lại, có trang xác nhận, chặn khi sách đang hiện hoặc thể loại còn sách | CẤM XÓA CHÚ THÍCH NÀY
class DeleteFlowTests(CatalogViewTestBase):
    def test_book_delete_requires_reauth(self):
        self.services["get_book"].return_value = make_book(is_active=False)
        for method in ("get", "post"):
            with self.subTest(method=method):
                response = getattr(self.client, method)(reverse("dashboard:book_delete", kwargs={"book_id": 9}))
                self.assertTrue(response["Location"].startswith(reverse("dashboard:reauth")))
        self.services["delete_book"].assert_not_called()

    def test_book_delete_confirm_then_delete(self):
        self.reauth()
        self.services["get_book"].return_value = make_book(is_active=False)
        response = self.client.get(reverse("dashboard:book_delete", kwargs={"book_id": 9}))
        self.assertContains(response, "Xóa vĩnh viễn")
        self.services["delete_book"].assert_not_called()
        response = self.client.post(reverse("dashboard:book_delete", kwargs={"book_id": 9}))
        self.assertRedirects(response, reverse("dashboard:books"), fetch_redirect_response=False)
        self.services["delete_book"].assert_called_once_with(self.staff, 9)

    def test_active_book_cannot_be_deleted(self):
        self.reauth()
        response = self.client.post(reverse("dashboard:book_delete", kwargs={"book_id": 9}))
        self.assertRedirects(response, reverse("dashboard:book_edit", kwargs={"book_id": 9}), fetch_redirect_response=False)
        self.services["delete_book"].assert_not_called()

    def test_sold_book_error_is_reported(self):
        self.reauth()
        self.services["get_book"].return_value = make_book(is_active=False)
        self.services["delete_book"].side_effect = BookError("BOOK_HAS_ORDERS")
        response = self.client.post(reverse("dashboard:book_delete", kwargs={"book_id": 9}), follow=True)
        self.assertIn(BookError("BOOK_HAS_ORDERS").message, self.messages_of(response))

    def test_category_delete_requires_reauth_and_empty_category(self):
        url_empty = reverse("dashboard:category_delete", kwargs={"category_id": 5})
        self.assertTrue(self.client.post(url_empty)["Location"].startswith(reverse("dashboard:reauth")))
        self.reauth()
        self.client.post(reverse("dashboard:category_delete", kwargs={"category_id": 4}))
        self.services["delete_category"].assert_not_called()
        self.assertContains(self.client.get(url_empty), "Xóa thể loại")
        self.client.post(url_empty)
        self.services["delete_category"].assert_called_once_with(self.staff, 5)

    def test_missing_category_is_404(self):
        self.reauth()
        self.assertEqual(self.client.get(reverse("dashboard:category_delete", kwargs={"category_id": 99})).status_code, 404)


# AI-TRACE#188 | Claude Opus 5.5 | Test trang thể loại: thêm, báo trùng tên đúng ô, đổi tên | CẤM XÓA CHÚ THÍCH NÀY
class CategoryViewTests(CatalogViewTestBase):
    def test_create_category(self):
        response = self.client.post(reverse("dashboard:categories"), {"name": "  Kinh   tế "})
        self.assertRedirects(response, reverse("dashboard:categories"), fetch_redirect_response=False)
        self.services["create_category"].assert_called_once_with(self.staff, "Kinh tế")

    def test_duplicate_name_error_on_field(self):
        self.services["create_category"].side_effect = CategoryError("CATEGORY_EXISTS")
        response = self.client.post(reverse("dashboard:categories"), {"name": "Văn học"})
        self.assertIn(CategoryError("CATEGORY_EXISTS").message, response.context["form"].errors["name"])

    def test_rename_category(self):
        self.client.post(reverse("dashboard:category_rename", kwargs={"category_id": 4}), {"name": "Văn học Việt Nam"})
        self.services["rename_category"].assert_called_once_with(self.staff, 4, "Văn học Việt Nam")

    def test_table_lists_categories_with_counts(self):
        html = self.client.get(reverse("dashboard:categories")).content.decode()
        self.assertIn('value="Văn học"', html)
        self.assertIn(reverse("dashboard:category_delete", kwargs={"category_id": 5}), html)
        self.assertNotIn(reverse("dashboard:category_delete", kwargs={"category_id": 4}), html)
