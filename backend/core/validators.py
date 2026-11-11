"""Hàm kiểm tra đầu vào dùng chung (mọi giá trị từ request đều là dữ liệu KHÔNG tin cậy)."""


def parse_positive_int(value, max_digits=9):
    """Chuỗi chỉ gồm chữ số (tối đa max_digits ký tự) → số nguyên dương; còn lại → None.

    Dùng cho tham số trên URL như ?category=, ?page=. Không dùng int() trần vì
    int(" 12 "), int("+12"), int("١٢") (chữ số Ả Rập) đều "thành công".
    """
    if not isinstance(value, str) or not value or len(value) > max_digits:
        return None
    if not (value.isascii() and value.isdigit()):
        return None
    number = int(value)
    return number if number > 0 else None


def clean_search_query(value, max_length=100):
    """Từ khóa tìm kiếm: bỏ khoảng trắng thừa, cắt còn tối đa max_length ký tự."""
    if not isinstance(value, str):
        return ""
    return " ".join(value.split())[:max_length]
