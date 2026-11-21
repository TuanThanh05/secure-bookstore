from django import forms
from django.core.exceptions import ValidationError

from accounts.forms import NAME_RE, PHONE_RE, PHONE_SEPARATORS_RE
from catalog.review_services import CONTROL_CHARS

from .cart_services import CART_MAX_PER_BOOK


class CartAddForm(forms.Form):
    book_id = forms.IntegerField(min_value=1)
    quantity = forms.IntegerField(min_value=1, max_value=CART_MAX_PER_BOOK, initial=1)


class CartQuantityForm(forms.Form):
    book_id = forms.IntegerField(min_value=1)
    quantity = forms.IntegerField(min_value=1, max_value=CART_MAX_PER_BOOK)


class CartRemoveForm(forms.Form):
    book_id = forms.IntegerField(min_value=1)


ADDRESS_MIN_LENGTH = 10
ADDRESS_MAX_LENGTH = 255


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
