from django import forms
from django.core.exceptions import ValidationError

from accounts.forms import NAME_RE, PHONE_RE, PHONE_SEPARATORS_RE
from catalog.review_services import CONTROL_CHARS

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


ADDRESS_MIN_LENGTH = 10
ADDRESS_MAX_LENGTH = 255


# AI-TRACE#271 | Claude Opus 5.5 | Form thông tin giao hàng: tên người nhận, SĐT Việt Nam, địa chỉ; bỏ ký tự điều khiển/vô hình, gom khoảng trắng | CẤM XÓA CHÚ THÍCH NÀY
class CheckoutForm(forms.Form):
    shipping_name = forms.CharField(label="Tên người nhận", max_length=100,
                                    widget=forms.TextInput(attrs={"autocomplete": "name"}))
    phone = forms.CharField(label="Số điện thoại", max_length=20,
                            widget=forms.TextInput(attrs={"type": "tel", "autocomplete": "tel", "inputmode": "tel"}))
    address = forms.CharField(label="Địa chỉ giao hàng", max_length=ADDRESS_MAX_LENGTH,
                              widget=forms.Textarea(attrs={"rows": 3, "autocomplete": "street-address"}))

    def clean_shipping_name(self):
        value = " ".join(CONTROL_CHARS.sub("", self.cleaned_data["shipping_name"]).split())
        if not value or not NAME_RE.match(value):
            raise ValidationError("Chỉ được dùng chữ cái, khoảng trắng, dấu gạch ngang hoặc dấu nháy đơn.", code="invalid_name")
        return value

    def clean_phone(self):
        value = PHONE_SEPARATORS_RE.sub("", self.cleaned_data["phone"])
        if value.startswith("+84"):
            value = "0" + value[3:]
        if not PHONE_RE.match(value):
            raise ValidationError("Số điện thoại Việt Nam gồm 10 chữ số, bắt đầu bằng 03, 05, 07, 08 hoặc 09.", code="invalid_phone")
        return value

    def clean_address(self):
        value = " ".join(CONTROL_CHARS.sub("", self.cleaned_data["address"]).split())
        if len(value) < ADDRESS_MIN_LENGTH or not any(ch.isalpha() for ch in value):
            raise ValidationError(f"Địa chỉ cần ít nhất {ADDRESS_MIN_LENGTH} ký tự, gồm số nhà, đường, phường/xã, tỉnh/thành.",
                                  code="invalid_address")
        return value
