from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import redirect
from django.views.decorators.http import require_POST

from orders.views import _log_order_probe

from .services import PaymentError, simulate_payment


@login_required
@require_POST
def simulate(request, code):
    if request.user.is_staff:
        messages.error(request, "Tài khoản quản trị không có đơn hàng.")
        return redirect("dashboard:index")
    try:
        transaction_id = simulate_payment(request, code)
    except PaymentError as exc:
        if exc.code == "ORDER_NOT_FOUND":
            _log_order_probe(request, code, exc)
            raise Http404 from None
        messages.error(request, exc.message)
    else:
        messages.success(request, f"Thanh toán thành công (mô phỏng). Mã giao dịch: {transaction_id}.")
    return redirect("orders:order_detail", code=code)
