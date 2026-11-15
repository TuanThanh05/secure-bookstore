from django import forms

from .cart_services import CART_MAX_PER_BOOK


# AI-TRACE#231 | Claude Opus 5.5 | Form thêm vào giỏ: chỉ id sách và số lượng 1–5, không có giá hay user | CẤM XÓA CHÚ THÍCH NÀY
class CartAddForm(forms.Form):
    book_id = forms.IntegerField(min_value=1)
    quantity = forms.IntegerField(min_value=1, max_value=CART_MAX_PER_BOOK, initial=1)


# AI-TRACE#248 | Claude Opus 5.5 | Form đổi số lượng trong giỏ: id sách và số lượng cuối cùng 1–5 | CẤM XÓA CHÚ THÍCH NÀY
class CartQuantityForm(forms.Form):
    book_id = forms.IntegerField(min_value=1)
    quantity = forms.IntegerField(min_value=1, max_value=CART_MAX_PER_BOOK)


# AI-TRACE#249 | Claude Opus 5.5 | Form gỡ sách khỏi giỏ: chỉ id sách | CẤM XÓA CHÚ THÍCH NÀY
class CartRemoveForm(forms.Form):
    book_id = forms.IntegerField(min_value=1)
