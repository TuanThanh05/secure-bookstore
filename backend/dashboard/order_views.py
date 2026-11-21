from django.contrib import messages
from django.core.paginator import Paginator
from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_POST

from core.decorators import recent_auth_required, staff_required
from core.security_log import log_event

from .forms import OrderFilterForm
from .order_services import (MAX_OFFSET, ORDER_ACTIONS, PAGE_SIZE, OrderAdminError, advance_order, get_order,
                             list_orders)


def _page_number(request):
    try:
        return min(max(1, int(request.GET.get("trang", 1))), MAX_OFFSET // PAGE_SIZE + 1)
    except (TypeError, ValueError):
        return 1


@staff_required
@never_cache
@require_GET
def orders(request):
    form = OrderFilterForm(request.GET or None)
    rows, total, page = [], 0, _page_number(request)
    if form.is_bound and not form.is_valid():
        messages.error(request, "Bộ lọc không hợp lệ.")
    else:
        try:
            total, rows = list_orders(request.user, form.status, page)
        except OrderAdminError as exc:
            messages.error(request, exc.message)
    query = request.GET.copy()
    query.pop("trang", None)
    return render(request, "dashboard/orders.html", {
        "form": form, "orders": rows, "total": total,
        "pager": Paginator(range(total), PAGE_SIZE).get_page(page),
        "querystring": query.urlencode(), "filtered": bool(form.is_bound and form.status),
        "back": request.get_full_path(),
    })


@staff_required
@recent_auth_required
@never_cache
@require_GET
def order_detail(request, code):
    try:
        order = get_order(request.user, code)
    except OrderAdminError as exc:
        if exc.code == "ORDER_NOT_FOUND":
            raise Http404 from None
        raise
    log_event("sensitive_data_viewed", request, user=request.user, username=request.user.get_username(),
              detail={"fields": ["shipping_name", "shipping_phone", "shipping_address"], "owner": "customer",
                      "order_code_prefix": order.code[:8]})
    return render(request, "dashboard/order_detail.html", {"order": order, "back": request.get_full_path()})


def _safe_back(request):
    candidate = request.POST.get("next", "")
    if (candidate.startswith(reverse("dashboard:orders"))
            and url_has_allowed_host_and_scheme(candidate, allowed_hosts={request.get_host()},
                                                require_https=request.is_secure())):
        return candidate
    return reverse("dashboard:orders")


@staff_required
@never_cache
@require_POST
def order_advance(request, code, action):
    if action not in ORDER_ACTIONS:
        raise Http404
    try:
        done = advance_order(request.user, code, action)
    except OrderAdminError as exc:
        if exc.code == "ORDER_NOT_FOUND":
            raise Http404 from None
        messages.error(request, exc.message)
    else:
        messages.success(request, f"{done} {code[:8]}….")
    return redirect(_safe_back(request))
