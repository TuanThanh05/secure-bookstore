from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import redirect_to_login
from django.core.paginator import Paginator
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.cache import never_cache
from django.http import Http404
from django.views.decorators.http import require_http_methods, require_POST, require_safe

from accounts.profile import decrypt_phone
from core.middleware import auto_lock_message
from core.session_store import end_user_sessions
from core.security_log import log_event

from .cart_services import (CART_MAX_PER_BOOK, CartError, add_to_cart, get_cart, remove_from_cart,
                            set_cart_quantity)
from .forms import CartAddForm, CartQuantityForm, CartRemoveForm, CheckoutForm
from .services import (ORDER_CODE_RE, ORDER_GROUPS, ORDER_LIST_MAX_OFFSET, ORDER_LIST_PAGE_SIZE, SHIPPING_FEE,
                       OrderError, cancel_order, get_order, list_my_orders, new_idempotency_key, place_order)


@login_required
@never_cache
@require_safe
def cart(request):
    if request.user.is_staff:
        messages.error(request, "Tài khoản quản trị không dùng giỏ hàng.")
        return redirect("dashboard:index")
    return render(request, "shop/cart.html", {
        "cart": get_cart(request),
        "cart_max": CART_MAX_PER_BOOK,
        "cart_update_url": reverse("orders:cart_update"),
        "cart_remove_url": reverse("orders:cart_remove"),
        "order_max_items": settings.ORDER_MAX_ITEMS,
        "order_hold_minutes": settings.ORDER_HOLD_MINUTES,
    })


def _cart_page_guard(request):
    cart_url = reverse("orders:cart")
    if not request.user.is_authenticated:
        return redirect_to_login(cart_url)
    if request.user.is_staff:
        messages.error(request, "Tài khoản quản trị không dùng giỏ hàng.")
        return redirect("dashboard:index")
    return None


@require_POST
def cart_update(request):
    blocked = _cart_page_guard(request)
    if blocked:
        return blocked
    form = CartQuantityForm(request.POST)
    if not form.is_valid():
        messages.error(request, CartError("INVALID_INPUT").message)
        return redirect("orders:cart")
    try:
        set_cart_quantity(request, form.cleaned_data["book_id"], form.cleaned_data["quantity"])
    except CartError as exc:
        messages.error(request, exc.message)
    else:
        messages.success(request, "Đã cập nhật số lượng.")
    return redirect("orders:cart")


@require_POST
def cart_remove(request):
    blocked = _cart_page_guard(request)
    if blocked:
        return blocked
    form = CartRemoveForm(request.POST)
    if not form.is_valid():
        messages.error(request, CartError("NOT_IN_CART").message)
        return redirect("orders:cart")
    try:
        remove_from_cart(request, form.cleaned_data["book_id"])
    except CartError as exc:
        messages.error(request, exc.message)
    else:
        messages.success(request, "Đã gỡ sách khỏi giỏ hàng.")
    return redirect("orders:cart")


def _page_number(request):
    try:
        return min(max(1, int(request.GET.get("trang", 1))), ORDER_LIST_MAX_OFFSET // ORDER_LIST_PAGE_SIZE + 1)
    except (TypeError, ValueError):
        return 1


@login_required
@never_cache
@require_safe
def order_list(request):
    if request.user.is_staff:
        messages.error(request, "Tài khoản quản trị không có đơn hàng.")
        return redirect("dashboard:index")
    status = request.GET.get("status", "active")
    if status not in ORDER_GROUPS:
        status = "active"
    page = _page_number(request)
    total, orders = list_my_orders(request, status, page)
    pager = Paginator(range(total), ORDER_LIST_PAGE_SIZE).get_page(page)
    return render(request, "account/orders.html", {
        "status": status, "tabs": ORDER_GROUPS, "orders": orders, "total": total, "pager": pager,
    })


def _safe_back_url(request, book_id, allow_detail=True):
    candidate = request.POST.get("next", "")
    if candidate and url_has_allowed_host_and_scheme(candidate, allowed_hosts={request.get_host()},
                                                     require_https=request.is_secure()):
        return candidate
    if allow_detail and isinstance(book_id, int) and book_id > 0:
        return reverse("catalog:book_detail", args=[book_id])
    return reverse("catalog:home")


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
        if request.POST.get("then") == "cart" and exc.code != "BOOK_NOT_FOUND":
            back_url = reverse("orders:cart")
    else:
        messages.success(request, f"Đã thêm vào giỏ. Trong giỏ đang có {in_cart} cuốn sách này.")
        if request.POST.get("then") == "cart":
            back_url = reverse("orders:cart")
    return redirect(back_url)


def _log_order_probe(request, code, exc):
    if exc.code == "ORDER_NOT_FOUND" and ORDER_CODE_RE.match(code or ""):
        log_event("idor_attempt", request, severity="warning", user=request.user,
                  username=request.user.get_username(), detail={"resource": "order", "code_prefix": code[:8]})


CHECKOUT_KEY_SESSION = "checkout_idempotency_key"
LAST_ORDER_SESSION = "last_order_code"


def _checkout_key(request):
    key = request.session.get(CHECKOUT_KEY_SESSION)
    if not key:
        key = new_idempotency_key()
        request.session[CHECKOUT_KEY_SESSION] = key
    return key


def _checkout_initial(user):
    return {"shipping_name": " ".join(part for part in (user.last_name, user.first_name) if part),
            "phone": decrypt_phone(user) or ""}


@login_required
@never_cache
@require_http_methods(["GET", "HEAD", "POST"])
def checkout(request):
    if request.user.is_staff:
        messages.error(request, "Tài khoản quản trị không đặt hàng.")
        return redirect("dashboard:index")
    cart_data = get_cart(request)
    if not cart_data.lines:
        messages.error(request, OrderError("CART_EMPTY").message)
        return redirect("orders:cart")
    if cart_data.has_unavailable:
        messages.error(request, "Hãy gỡ các sách ngừng bán hoặc hết hàng khỏi giỏ trước khi đặt hàng.")
        return redirect("orders:cart")
    if sum(line.quantity for line in cart_data.lines) > settings.ORDER_MAX_ITEMS:
        messages.error(request, OrderError("ORDER_TOO_LARGE").message)
        return redirect("orders:cart")
    key = _checkout_key(request)
    status = 200
    if request.method == "POST":
        form = CheckoutForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            try:
                result = place_order(request, key, data["shipping_name"], data["phone"], data["address"])
            except OrderError as exc:
                messages.error(request, exc.message)
                if exc.code in ("CART_EMPTY", "BOOK_INACTIVE", "OUT_OF_STOCK", "ORDER_TOO_LARGE"):
                    return redirect("orders:cart")
                if exc.code == "PENDING_EXISTS" and request.session.get(LAST_ORDER_SESSION):
                    return redirect("orders:order_detail", code=request.session[LAST_ORDER_SESSION])
                status = 400
            else:
                request.session.pop(CHECKOUT_KEY_SESSION, None)
                request.session[LAST_ORDER_SESSION] = result.order_code
                messages.success(request, f"Đã tạo đơn hàng. Hãy thanh toán trong {settings.ORDER_HOLD_MINUTES} phút, "
                                          "quá hạn đơn sẽ bị hủy.")
                return redirect("orders:order_detail", code=result.order_code)
        else:
            status = 400
    else:
        form = CheckoutForm(initial=_checkout_initial(request.user))
    return render(request, "shop/checkout.html", {
        "form": form,
        "cart": cart_data,
        "shipping_fee": SHIPPING_FEE,
        "total": cart_data.subtotal + SHIPPING_FEE,
        "order_hold_minutes": settings.ORDER_HOLD_MINUTES,
    }, status=status)


@login_required
@never_cache
@require_safe
def order_detail(request, code):
    if request.user.is_staff:
        messages.error(request, "Tài khoản quản trị không có đơn hàng.")
        return redirect("dashboard:index")
    try:
        order = get_order(request, code)
    except OrderError as exc:
        _log_order_probe(request, code, exc)
        raise Http404 from None
    return render(request, "shop/order_detail.html", {"order": order, "payment_simulation": settings.PAYMENT_SIMULATION})


@login_required
@require_POST
def order_cancel(request, code):
    if request.user.is_staff:
        messages.error(request, "Tài khoản quản trị không có đơn hàng.")
        return redirect("dashboard:index")
    try:
        account_locked = cancel_order(request, code)
    except OrderError as exc:
        if exc.code == "ORDER_NOT_FOUND":
            _log_order_probe(request, code, exc)
            raise Http404 from None
        messages.error(request, exc.message)
    else:
        if account_locked:
            return _logout_auto_locked(request)
        messages.success(request, "Đã hủy đơn hàng. Sách trong đơn đã được trả lại kho.")
    return redirect("orders:order_detail", code=code)


def _logout_auto_locked(request):
    user = request.user
    user.refresh_from_db(fields=["auto_locked_until"])
    log_event("order_hold_abuse", request, severity="warning", user=user, username=user.get_username(),
              detail={"via": "cancel", "locked_until": user.auto_locked_until.strftime("%Y-%m-%dT%H:%M:%SZ")})
    message = auto_lock_message(user)
    end_user_sessions(user.pk)
    logout(request)
    messages.error(request, message)
    return redirect("accounts:login")
