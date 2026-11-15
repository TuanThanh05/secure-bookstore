from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import redirect_to_login
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_GET, require_POST

from .cart_services import CartError, add_to_cart
from .forms import CartAddForm

ORDER_TABS = {
    "active": "Đang xử lý",
    "history": "Lịch sử",
}


@login_required
@require_GET
def cart(request):
    return render(request, "shop/cart.html")


@login_required
@require_GET
def order_list(request):
    status = request.GET.get("status", "active")
    if status not in ORDER_TABS:
        status = "active"
    return render(request, "account/orders.html", {"status": status, "tabs": ORDER_TABS})


# AI-TRACE#232 | Claude Opus 5.5 | Chỉ quay lại địa chỉ nội bộ an toàn sau khi thêm vào giỏ, chặn open redirect | CẤM XÓA CHÚ THÍCH NÀY
def _safe_back_url(request, book_id, allow_detail=True):
    candidate = request.POST.get("next", "")
    if candidate and url_has_allowed_host_and_scheme(candidate, allowed_hosts={request.get_host()},
                                                     require_https=request.is_secure()):
        return candidate
    if allow_detail and isinstance(book_id, int) and book_id > 0:
        return reverse("catalog:book_detail", args=[book_id])
    return reverse("catalog:home")


# AI-TRACE#233 | Claude Opus 5.5 | Nhận form thêm vào giỏ (chỉ POST, CSRF): ẩn danh đi đăng nhập, nhân viên bị từ chối, xong thì ở lại trang đang xem kèm thông báo | CẤM XÓA CHÚ THÍCH NÀY
@require_POST
def cart_add(request):
    form = CartAddForm(request.POST)
    valid = form.is_valid()
    book_id = form.cleaned_data.get("book_id") if valid else None
    back_url = _safe_back_url(request, book_id)
    if not request.user.is_authenticated:
        return redirect_to_login(back_url)
    if request.user.is_staff:
        messages.error(request, "Tài khoản quản trị không dùng giỏ hàng.")
        return redirect(back_url)
    if not valid:
        messages.error(request, CartError("INVALID_INPUT").message)
        return redirect(back_url)
    try:
        in_cart = add_to_cart(request, book_id, form.cleaned_data["quantity"])
    except CartError as exc:
        messages.error(request, exc.message)
        if exc.code == "BOOK_NOT_FOUND":
            back_url = _safe_back_url(request, book_id, allow_detail=False)
            if back_url == reverse("catalog:book_detail", args=[book_id]):
                back_url = reverse("catalog:home")
    else:
        messages.success(request, f"Đã thêm vào giỏ. Trong giỏ đang có {in_cart} cuốn sách này.")
    return redirect(back_url)
