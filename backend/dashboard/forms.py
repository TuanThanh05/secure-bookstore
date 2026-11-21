from datetime import datetime, time, timedelta

from django import forms
from django.utils import timezone

from accounts.forms import CurrentUserPasswordForm, ProfileUpdateForm
from catalog.review_services import CONTROL_CHARS

from .log_services import ACTION_LABELS, EVENT_LABELS, SEVERITY_LABELS, TABLE_LABELS
from .order_services import ORDER_FILTERS


class ReauthForm(CurrentUserPasswordForm):
    pass


class StaffProfileUpdateForm(ProfileUpdateForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        phone = self.fields["phone"]
        phone.label = "Số điện thoại mới"
        phone.help_text = "Để trống nếu không đổi. Số hiện tại không được hiển thị."
        phone.widget.attrs.update({"autocomplete": "off", "placeholder": "Để trống nếu không đổi"})


ACCOUNT_STATUS_FILTERS = {
    "hoat-dong": "active",
    "da-khoa": "locked",
    "khoa-tu-dong": "auto_locked",
    "tam-khoa": "temp_locked",
    "chua-xac-nhan": "unverified",
}


class AccountFilterForm(forms.Form):
    trang_thai = forms.ChoiceField(label="Trạng thái", required=False, choices=[
        ("", "Tất cả"), ("hoat-dong", "Hoạt động"), ("da-khoa", "Đã khóa"),
        ("khoa-tu-dong", "Khóa tự động (giữ kho)"), ("tam-khoa", "Tạm khóa"), ("chua-xac-nhan", "Chưa xác nhận email")])
    ten = forms.CharField(label="Username", required=False, max_length=150)

    def clean_ten(self):
        return " ".join(CONTROL_CHARS.sub("", self.cleaned_data["ten"]).split())

    @property
    def status(self):
        return ACCOUNT_STATUS_FILTERS.get(self.cleaned_data.get("trang_thai", "")) if self.is_valid() else None


class AccountActionForm(ReauthForm):
    reason = forms.CharField(label="Lý do", min_length=5, max_length=255,
                             widget=forms.Textarea(attrs={"rows": 3}),
                             help_text="Ghi vào nhật ký hệ thống cùng tài khoản thực hiện.")
    field_order = ["reason", "password"]

    def clean_reason(self):
        text = " ".join(CONTROL_CHARS.sub("", self.cleaned_data["reason"]).split())
        if len(text) < 5:
            raise forms.ValidationError("Lý do cần ít nhất 5 ký tự.", code="min_length")
        return text


LOG_MAX_DAYS = 400


class _LogDateRangeForm(forms.Form):
    tu = forms.DateField(label="Từ ngày", required=False, widget=forms.DateInput(attrs={"type": "date"}))
    den = forms.DateField(label="Đến ngày", required=False, widget=forms.DateInput(attrs={"type": "date"}))

    def clean(self):
        cleaned = super().clean()
        start, end = cleaned.get("tu"), cleaned.get("den")
        if start and end:
            if start > end:
                raise forms.ValidationError("Ngày bắt đầu phải trước ngày kết thúc.")
            if (end - start).days > LOG_MAX_DAYS:
                raise forms.ValidationError(f"Chỉ xem tối đa {LOG_MAX_DAYS} ngày một lần.")
        return cleaned

    def range(self):
        tz = timezone.get_current_timezone()
        start, end = self.cleaned_data.get("tu"), self.cleaned_data.get("den")
        begin = datetime.combine(start, time.min, tzinfo=tz) if start else None
        finish = datetime.combine(end + timedelta(days=1), time.min, tzinfo=tz) if end else None
        return begin, finish


class SecurityLogFilterForm(_LogDateRangeForm):
    loai = forms.ChoiceField(label="Loại sự kiện", required=False)
    muc_do = forms.ChoiceField(label="Mức độ", required=False)
    tim = forms.CharField(label="Username hoặc IP", required=False, max_length=150)
    field_order = ["loai", "muc_do", "tu", "den", "tim"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["loai"].choices = [("", "Tất cả"), *sorted(EVENT_LABELS.items(), key=lambda item: item[1])]
        self.fields["muc_do"].choices = [("", "Tất cả"), *SEVERITY_LABELS.items()]

    def clean_tim(self):
        return " ".join(CONTROL_CHARS.sub("", self.cleaned_data["tim"]).split())


class AuditLogFilterForm(_LogDateRangeForm):
    bang = forms.ChoiceField(label="Dữ liệu", required=False)
    hanh_dong = forms.ChoiceField(label="Hành động", required=False)
    ma = forms.IntegerField(label="Id bản ghi", required=False, min_value=1, max_value=2**63 - 1)
    field_order = ["bang", "hanh_dong", "tu", "den", "ma"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["bang"].choices = [("", "Tất cả"), *TABLE_LABELS.items()]
        self.fields["hanh_dong"].choices = [("", "Tất cả"), *ACTION_LABELS.items()]


class OrderFilterForm(forms.Form):
    trang_thai = forms.ChoiceField(label="Trạng thái", required=False,
                                   choices=[("", "Tất cả"), *ORDER_FILTERS.items()])

    @property
    def status(self):
        return (self.cleaned_data.get("trang_thai") or None) if self.is_valid() else None
