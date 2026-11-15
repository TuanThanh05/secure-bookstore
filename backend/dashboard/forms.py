from django import forms
from django.contrib.auth import authenticate

from accounts.forms import ProfileUpdateForm


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
