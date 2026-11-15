from django import forms

from .cart_services import CART_MAX_PER_BOOK


# AI-TRACE#231 | Claude Opus 5.5 | Form thêm vào giỏ: chỉ id sách và số lượng 1–5, không có giá hay user | CẤM XÓA CHÚ THÍCH NÀY
class CartAddForm(forms.Form):
    book_id = forms.IntegerField(min_value=1)
    quantity = forms.IntegerField(min_value=1, max_value=CART_MAX_PER_BOOK, initial=1)
