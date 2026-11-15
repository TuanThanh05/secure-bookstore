from unittest import mock

from django.test import SimpleTestCase
from django.urls import reverse

from catalog.services import BookCard, Category

CATEGORIES = [Category(1, "Văn học", "van-hoc"), Category(3, "Khoa học", "khoa-hoc")]
BOOKS = [
    BookCard(1, "Nhà Giả Kim", "Paulo Coelho", 1, 290000, 4.8, 310, True),
    BookCard(4, "Lược Sử Loài Người", "Yuval Noah Harari", 3, 450000, None, 0, False),
]


# AI-TRACE#196 | Claude Opus 5.5 | Test trang chủ: hiển thị sách thật qua service, lọc thể loại, tìm kiếm, đầu vào độc hại, không script inline | CẤM XÓA CHÚ THÍCH NÀY
class HomePageTests(SimpleTestCase):
    url = reverse("catalog:home")

    def setUp(self):
        categories = mock.patch("catalog.views.services.list_categories", return_value=CATEGORIES)
        books = mock.patch("catalog.views.services.list_public_books", return_value=BOOKS)
        categories.start()
        self.list_books = books.start()
        self.addCleanup(categories.stop)
        self.addCleanup(books.stop)

    def test_hien_thi(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Secure Bookstore")
        self.assertContains(response, "Nhà Giả Kim")
        self.assertContains(response, "Hết hàng")
        self.list_books.assert_called_once_with(category_id=None, q="")

    def test_loc_the_loai(self):
        response = self.client.get(self.url, {"category": "3"})
        self.assertEqual(response.context["current_category"], 3)
        self.list_books.assert_called_once_with(category_id=3, q="")

    def test_the_loai_khong_hop_le_bi_bo_qua(self):
        for value in ["abc", "999", "-1", "1 OR 1=1", "1'"]:
            with self.subTest(value=value):
                self.list_books.reset_mock()
                response = self.client.get(self.url, {"category": value})
                self.assertEqual(response.status_code, 200)
                self.assertIsNone(response.context["current_category"])
                self.list_books.assert_called_once_with(category_id=None, q="")

    def test_tim_kiem(self):
        self.client.get(self.url, {"q": "  harari "})
        self.list_books.assert_called_once_with(category_id=None, q="harari")

    def test_tu_khoa_bi_cat_con_100_ky_tu(self):
        response = self.client.get(self.url, {"q": "a" * 500})
        self.assertEqual(len(response.context["q"]), 100)

    def test_xss_trong_tu_khoa_bi_escape(self):
        payload = '<script>alert(1)</script>"><img src=x onerror=alert(1)>'
        body = self.client.get(self.url, {"q": payload}).content.decode()
        self.assertNotIn("<script>alert(1)</script>", body)
        self.assertNotIn("<img src=x", body)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", body)

    def test_xss_trong_ten_sach_bi_escape(self):
        self.list_books.return_value = [BookCard(9, "<script>alert(2)</script>", "<b>X</b>", 1, 1000, None, 0, True)]
        body = self.client.get(self.url).content.decode()
        self.assertNotIn("<script>alert(2)</script>", body)
        self.assertNotIn("<b>X</b>", body)

    def test_anh_bia_mac_dinh_khi_chua_co_anh(self):
        self.assertContains(self.client.get(self.url), "img/book-cover-default.webp")

    def test_khong_nhan_post(self):
        self.assertEqual(self.client.post(self.url).status_code, 405)

    def test_khong_co_script_hay_style_inline(self):
        body = self.client.get(self.url).content.decode()
        self.assertNotIn("<script>", body)
        self.assertNotIn(" style=", body)
        self.assertNotIn(" onclick=", body)
        self.assertNotIn("https://", body)


class AboutPageTests(SimpleTestCase):
    def test_hien_thi(self):
        response = self.client.get(reverse("catalog:about"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Nhóm 7")
