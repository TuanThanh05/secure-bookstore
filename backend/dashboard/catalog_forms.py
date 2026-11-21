from django import forms
from django.core.exceptions import ValidationError

from catalog.book_services import (
    DESCRIPTION_MAX_LENGTH,
    PRICE_MAX,
    STOCK_MAX,
    TITLE_MAX_LENGTH,
    BookError,
    clean_isbn,
)
from catalog.covers import MAX_UPLOAD_BYTES
from catalog.staff_services import NAME_MAX_LENGTH

COVER_ACCEPT = "image/jpeg,image/png,image/webp"

ERROR_FIELDS = {
    "INVALID_ISBN": ("isbn",),
    "ISBN_EXISTS": ("isbn",),
    "CATEGORY_NOT_FOUND": ("category_id",),
    "INVALID_QUANTITY": ("stock", "quantity"),
    "STOCK_LIMIT": ("quantity", "stock"),
    "INSUFFICIENT_STOCK": ("quantity",),
    "COVER_TOO_LARGE": ("cover",),
    "COVER_INVALID": ("cover",),
    "COVER_DIMENSIONS": ("cover",),
    "CATEGORY_EXISTS": ("name",),
    "INVALID_INPUT": ("name",),
}


def attach_error(form, error):
    for field in ERROR_FIELDS.get(error.code, ()):
        if field in form.fields:
            form.add_error(field, error.message)
            return
    form.add_error(None, error.message)


class BookForm(forms.Form):
    title = forms.CharField(label="Tên sách", max_length=TITLE_MAX_LENGTH)
    author = forms.CharField(label="Tác giả", max_length=TITLE_MAX_LENGTH)
    isbn = forms.CharField(label="ISBN", max_length=20, help_text="ISBN-10 hoặc ISBN-13, có thể có dấu gạch.")
    category_id = forms.TypedChoiceField(label="Thể loại", coerce=int)
    description = forms.CharField(label="Mô tả", required=False, max_length=DESCRIPTION_MAX_LENGTH,
                                  widget=forms.Textarea(attrs={"rows": 6}))
    price = forms.IntegerField(label="Giá bán (đ)", min_value=1, max_value=PRICE_MAX)
    cost_price = forms.IntegerField(label="Giá nhập (đ)", min_value=0, max_value=PRICE_MAX)
    cover = forms.FileField(label="Ảnh bìa", required=False,
                            help_text="JPEG, PNG hoặc WebP, tối đa 2 MB. Ảnh được lưu lại thành WebP.",
                            widget=forms.FileInput(attrs={"accept": COVER_ACCEPT}))

    def __init__(self, categories, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category_id"].choices = [("", "Chọn thể loại")] + [(c.id, c.name) for c in categories]
        self.fields["isbn"].widget.attrs.update({"autocomplete": "off", "spellcheck": "false"})

    def clean_title(self):
        return " ".join(self.cleaned_data["title"].split())

    def clean_author(self):
        return " ".join(self.cleaned_data["author"].split())

    def clean_isbn(self):
        try:
            return clean_isbn(self.cleaned_data["isbn"])
        except BookError as exc:
            raise ValidationError(exc.message, code=exc.code) from None

    def clean_cover(self):
        cover = self.cleaned_data.get("cover")
        if cover and cover.size > MAX_UPLOAD_BYTES:
            raise ValidationError("Ảnh bìa tối đa 2 MB.", code="COVER_TOO_LARGE")
        return cover

    def book_fields(self):
        data = self.cleaned_data
        return {key: data[key] for key in ("title", "author", "isbn", "category_id", "description", "price", "cost_price")}


class BookCreateForm(BookForm):
    stock = forms.IntegerField(label="Tồn kho ban đầu", min_value=0, max_value=STOCK_MAX, initial=0)


class BookEditForm(BookForm):
    remove_cover = forms.BooleanField(label="Bỏ ảnh bìa (dùng ảnh mặc định)", required=False)

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("cover") and cleaned.get("remove_cover"):
            raise ValidationError("Chọn ảnh mới hoặc bỏ ảnh, không làm cả hai cùng lúc.", code="cover_conflict")
        return cleaned


class StockForm(forms.Form):
    quantity = forms.IntegerField(label="Số lượng", min_value=1, max_value=STOCK_MAX)


class CategoryForm(forms.Form):
    name = forms.CharField(label="Tên thể loại", max_length=NAME_MAX_LENGTH)

    def clean_name(self):
        return " ".join(self.cleaned_data["name"].split())
