from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import User

class RegisterForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email")

class LoginForm(AuthenticationForm):

    error_messages = {
        **AuthenticationForm.error_messages,
        "invalid_login": "Tên đăng nhập hoặc mật khẩu không đúng.",
    }

    def __init__(self, request=None, *args, **kwargs):
        super().__init__(request, *args, **kwargs)
        username = self.fields["username"]
        username.max_length = 254
        username.widget.attrs["maxlength"] = 254
        username.label = "Tên đăng nhập hoặc email"

    def clean_username(self):
        value = self.cleaned_data["username"]
        if "@" in value:
            username = (
                User.objects.filter(email__iexact=value)
                .values_list("username", flat=True)
                .first()
            )
            if username:
                return username
        return value