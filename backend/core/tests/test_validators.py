"""Test hàm kiểm tra đầu vào và filter template (không cần CSDL)."""
from django.test import SimpleTestCase

from core.templatetags.bookstore import stars, tone, vnd
from core.validators import clean_search_query, parse_positive_int


class ParsePositiveIntTests(SimpleTestCase):
    def test_hop_le(self):
        self.assertEqual(parse_positive_int("12"), 12)

    def test_tu_choi_gia_tri_la(self):
        for value in ["", "0", "-1", "+1", " 1", "1.5", "abc", "1 OR 1=1", "١٢", "9" * 10, None]:
            with self.subTest(value=value):
                self.assertIsNone(parse_positive_int(value))


class CleanSearchQueryTests(SimpleTestCase):
    def test_cat_do_dai_va_khoang_trang(self):
        self.assertEqual(clean_search_query("  nhà   giả kim "), "nhà giả kim")
        self.assertEqual(len(clean_search_query("a" * 500)), 100)

    def test_khong_phai_chuoi(self):
        self.assertEqual(clean_search_query(None), "")


class FilterTests(SimpleTestCase):
    def test_vnd(self):
        self.assertEqual(vnd(420000), "420.000 ₫")
        self.assertEqual(vnd("abc"), "")

    def test_stars(self):
        self.assertEqual(stars(4.3), ["star"] * 4 + ["star-half"])
        self.assertEqual(stars(4.8), ["star"] * 5)
        self.assertEqual(stars(0), ["star-empty"] * 5)
        self.assertEqual(stars(9), ["star"] * 5)
        self.assertEqual(stars(None), [])

    def test_tone(self):
        self.assertEqual([tone(i) for i in range(1, 6)], [1, 2, 3, 0, 1])
        self.assertEqual(tone("x"), 0)
