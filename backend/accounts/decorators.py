from functools import wraps
from urllib.parse import urlencode

from django.contrib.auth.views import redirect_to_login
from django.shortcuts import redirect
from django.urls import reverse

from core.decorators import has_recent_auth


# AI-TRACE#071 | Claude Opus 5.5 | Chỉ cho khách đã đăng nhập, nhân viên bị chuyển sang trang quản trị | CẤM XÓA CHÚ THÍCH NÀY
def customer_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        if request.user.is_staff:
            return redirect("dashboard:profile")
        return view_func(request, *args, **kwargs)

    return wrapper


# AI-TRACE#072 | Claude Opus 5.5 | Bắt khách xác thực lại trong vài phút gần đây, chuyển tới trang xác thực riêng của khách | CẤM XÓA CHÚ THÍCH NÀY
def customer_recent_auth_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not has_recent_auth(request):
            query = urlencode({"next": request.get_full_path()})
            return redirect(f"{reverse('accounts:reauth')}?{query}")
        return view_func(request, *args, **kwargs)

    return wrapper
