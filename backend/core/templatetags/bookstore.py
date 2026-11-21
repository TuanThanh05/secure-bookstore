"""Filter dùng trong template. Nạp bằng {% load bookstore %}."""
from django import template

register = template.Library()


@register.filter
def vnd(value):
    """420000 → "420.000 ₫". Giá trị không phải số → chuỗi rỗng."""
    try:
        amount = int(value)
    except (TypeError, ValueError):
        return ""
    return f"{amount:,}".replace(",", ".") + " ₫"


@register.filter
def stars(rating):
    try:
        value = float(rating)
    except (TypeError, ValueError):
        return []
    value = min(max(round(value * 2) / 2, 0), 5)
    full = int(value)
    half = 1 if value - full else 0
    return ["star"] * full + ["star-half"] * half + ["star-empty"] * (5 - full - half)


@register.filter
def tone(value, count=4):
    """Số nguyên → 0..count-1, dùng chọn màu ảnh bìa giữ chỗ cho đỡ đơn điệu."""
    try:
        return int(value) % int(count)
    except (TypeError, ValueError, ZeroDivisionError):
        return 0
