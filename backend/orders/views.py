from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.http import require_GET

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
