from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods
from django.contrib.auth.views import LogoutView

from .forms import RegisterForm

@require_http_methods(["GET", "POST"])
def register(request):
    if request.user.is_authenticated:
        return redirect("catalog:home")

    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Đăng ký thành công. Mời bạn đăng nhập.")
            return redirect("accounts:login")
    else:
        form = RegisterForm()

    return render(request, "account/register.html", {"form": form})

class SecureLogoutView(LogoutView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        response["Clear-Site-Data"] = '"cache", "cookies", "storage"'
        return response