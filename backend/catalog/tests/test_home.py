"""Test trang chủ: hiển thị, lọc, tìm kiếm và các đầu vào độc hại (không cần CSDL)."""
from django.test import SimpleTestCase
from django.urls import reverse


class HomePageTests(SimpleTestCase):
    url = reverse("catalog:home")

    def test_hien_thi(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Secure Bookstore")
        self.assertContains(response, "Nhóm 7")
        self.assertEqual(len(response.context["books"]), 8)

    def test_loc_the_loai(self):
        response = self.client.get(self.url, {"category": "3"})
        self.assertEqual(response.context["current_category"], 3)
        self.assertTrue(all(b.category_id == 3 for b in response.context["books"]))

    def test_the_loai_khong_hop_le_bi_bo_qua(self):
        for value in ["abc", "999", "-1", "1 OR 1=1", "1'"]:
            with self.subTest(value=value):
                response = self.client.get(self.url, {"category": value})
                self.assertEqual(response.status_code, 200)
                self.assertIsNone(response.context["current_category"])
                self.assertEqual(len(response.context["books"]), 8)

    def test_tim_kiem(self):
        response = self.client.get(self.url, {"q": "harari"})
        titles = [b.title for b in response.context["books"]]
        self.assertEqual(titles, ["Lược Sử Loài Người"])

    def test_tu_khoa_bi_cat_con_100_ky_tu(self):
        response = self.client.get(self.url, {"q": "a" * 500})
        self.assertEqual(len(response.context["q"]), 100)

    def test_xss_trong_tu_khoa_bi_escape(self):
        payload = '<script>alert(1)</script>"><img src=x onerror=alert(1)>'
        response = self.client.get(self.url, {"q": payload})
        body = response.content.decode()
        self.assertNotIn("<script>alert(1)</script>", body)
        self.assertNotIn("<img src=x", body)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", body)

    def test_khong_nhan_post(self):
        self.assertEqual(self.client.post(self.url).status_code, 405)

    def test_khong_co_script_hay_style_inline(self):
        body = self.client.get(self.url).content.decode()
        self.assertNotIn("<script>", body)
        self.assertNotIn(" style=", body)
        self.assertNotIn(" onclick=", body)
        self.assertNotIn("https://", body)   # không tài nguyên ngoài (CDN, Google Fonts)


class AboutPageTests(SimpleTestCase):
    def test_hien_thi(self):
        response = self.client.get(reverse("catalog:about"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Nhóm 7")
