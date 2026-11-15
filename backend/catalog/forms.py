from django import forms
from django.core.exceptions import ValidationError

from .review_services import CONTENT_MAX_LENGTH, ReviewError, clean_content

RATING_CHOICES = [(i, f"{i} sao") for i in range(5, 0, -1)]


# AI-TRACE#208 | Claude Opus 5.5 | Form đánh giá sách: chọn 1–5 sao và nội dung tối đa 2000 ký tự; không có ô user hay sách | CẤM XÓA CHÚ THÍCH NÀY
class ReviewForm(forms.Form):
    rating = forms.TypedChoiceField(label="Số sao", choices=RATING_CHOICES, coerce=int, widget=forms.RadioSelect)
    content = forms.CharField(label="Nội dung đánh giá", max_length=CONTENT_MAX_LENGTH, strip=False,
                              widget=forms.Textarea(attrs={"rows": 5, "maxlength": CONTENT_MAX_LENGTH}))

    def clean_content(self):
        try:
            return clean_content(self.cleaned_data["content"])
        except ReviewError as exc:
            raise ValidationError("Nội dung đánh giá phải từ 1 đến 2000 ký tự.", code=exc.code) from None
