from django import forms
from django.contrib.auth import authenticate

from accounts.forms import ProfileUpdateForm
from catalog.review_services import CONTROL_CHARS


class ReauthForm(forms.Form):
    error_messages = {"invalid": "Tên đăng nhập hoặc mật khẩu không đúng."}

    username = forms.CharField(label="Tên đăng nhập", max_length=150)
    password = forms.CharField(label="Mật khẩu", strip=False, widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}))

    def __init__(self, request, *args, **kwargs):
        self.request = request
        self.user_mismatch = False
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs["autocomplete"] = "username"

    def clean(self):
        cleaned = super().clean()
        username = cleaned.get("username")
        password = cleaned.get("password")
        if username and password:
            user = authenticate(self.request, username=username, password=password)
            if user is None or user.pk != self.request.user.pk:
                self.user_mismatch = user is not None
                raise forms.ValidationError(self.error_messages["invalid"], code="invalid")
        return cleaned


# AI-TRACE#094 | Claude Opus 5.5 | Form sửa họ, tên, SĐT của nhân viên; ô SĐT luôn trống, để trống là giữ số cũ | CẤM XÓA CHÚ THÍCH NÀY
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
    "tam-khoa": "temp_locked",
    "chua-xac-nhan": "unverified",
}


# AI-TRACE#304 | Claude Opus 5.5 | Bộ lọc danh sách tài khoản khách: trạng thái (giá trị cố định) và username (bỏ ký tự điều khiển, tối đa 150 ký tự) | CẤM XÓA CHÚ THÍCH NÀY
class AccountFilterForm(forms.Form):
    trang_thai = forms.ChoiceField(label="Trạng thái", required=False, choices=[
        ("", "Tất cả"), ("hoat-dong", "Hoạt động"), ("da-khoa", "Đã khóa"),
        ("tam-khoa", "Tạm khóa"), ("chua-xac-nhan", "Chưa xác nhận email")])
    ten = forms.CharField(label="Username", required=False, max_length=150)

    def clean_ten(self):
        return " ".join(CONTROL_CHARS.sub("", self.cleaned_data["ten"]).split())

    @property
    def status(self):
        return ACCOUNT_STATUS_FILTERS.get(self.cleaned_data.get("trang_thai", "")) if self.is_valid() else None


# AI-TRACE#305 | Claude Opus 5.5 | Form khóa/mở khóa: lý do 5–255 ký tự và nhập lại tài khoản + mật khẩu admin, kiểm tra riêng cho đúng lần gửi này (không dùng lại xác thực cũ) | CẤM XÓA CHÚ THÍCH NÀY
class AccountActionForm(ReauthForm):
    reason = forms.CharField(label="Lý do", min_length=5, max_length=255,
                             widget=forms.Textarea(attrs={"rows": 3}),
                             help_text="Ghi vào nhật ký hệ thống cùng tài khoản thực hiện.")
    field_order = ["reason", "username", "password"]

    def clean_reason(self):
        text = " ".join(CONTROL_CHARS.sub("", self.cleaned_data["reason"]).split())
        if len(text) < 5:
            raise forms.ValidationError("Lý do cần ít nhất 5 ký tự.", code="min_length")
        return text
