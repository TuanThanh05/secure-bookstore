from django.contrib import messages
from django.core.paginator import Paginator
from django.http import Http404
from django.shortcuts import redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_http_methods

from core.decorators import recent_auth_required, staff_required
from core.security_log import log_event

from .account_services import AccountError, get_account, list_accounts, lock_account, unlock_account
from .forms import AccountActionForm, AccountFilterForm

ACCOUNTS_PER_PAGE = 20


def _account_page(request, show_full):
    form = AccountFilterForm(request.GET or None)
    keyword = form.cleaned_data.get("ten") if form.is_valid() else ""
    status = form.status
    try:
        accounts = list_accounts(request.user, status, keyword)
    except AccountError as exc:
        messages.error(request, exc.message)
        accounts = []
    page = Paginator(accounts, ACCOUNTS_PER_PAGE).get_page(request.GET.get("trang"))
    query = request.GET.copy()
    query.pop("trang", None)
    return {
        "form": form,
        "page": page,
        "total": len(accounts),
        "filtered": bool(status or keyword),
        "querystring": query.urlencode(),
        "show_full": show_full,
    }, len(accounts), status, keyword


@staff_required
@never_cache
@require_GET
def accounts(request):
    context, *_ = _account_page(request, show_full=False)
    return render(request, "dashboard/accounts.html", context)


@staff_required
@recent_auth_required
@never_cache
@require_GET
def accounts_full(request):
    context, count, status, keyword = _account_page(request, show_full=True)
    log_event("sensitive_data_viewed", request, user=request.user, username=request.user.get_username(),
              detail={"fields": ["email", "phone"], "owner": "customers", "rows": count,
                      "status": status, "keyword": keyword or None})
    return render(request, "dashboard/accounts.html", context)


def _account_or_404(request, user_id):
    try:
        return get_account(request.user, user_id)
    except AccountError as exc:
        if exc.code == "ACCOUNT_NOT_FOUND":
            raise Http404 from None
        raise


def _account_action(request, user_id, action):
    account = _account_or_404(request, user_id)
    locking = action == "lock"
    if locking and account.is_locked:
        messages.info(request, f"Tài khoản {account.username} đã bị khóa từ trước.")
        return redirect("dashboard:accounts")
    if not locking and not account.is_locked:
        messages.info(request, f"Tài khoản {account.username} đang không bị khóa.")
        return redirect("dashboard:accounts")
    status = 200
    if request.method == "POST":
        form = AccountActionForm(request, data=request.POST)
        if form.is_valid():
            log_event("login_success", request, user=request.user, username=request.user.get_username(),
                      detail={"step_up": True, "action": f"account_{action}", "target_id": account.id})
            try:
                ended = (lock_account if locking else unlock_account)(request.user, account.id,
                                                                     form.cleaned_data["reason"])
            except AccountError as exc:
                messages.error(request, exc.message)
            else:
                if locking:
                    log_event("logout", request, severity="warning", user=request.user,
                              username=request.user.get_username(),
                              detail={"reason": "account_locked", "target_id": account.id, "sessions_ended": ended})
                    messages.success(request, f"Đã khóa tài khoản {account.username} và đăng xuất {ended} phiên đang mở.")
                else:
                    messages.success(request, f"Đã mở khóa tài khoản {account.username}.")
            return redirect("dashboard:accounts")
        status = 400
    else:
        form = AccountActionForm(request)
    return render(request, "dashboard/account_action.html",
                  {"account": account, "form": form, "locking": locking}, status=status)


@staff_required
@never_cache
@require_http_methods(["GET", "POST"])
def account_lock(request, user_id):
    return _account_action(request, user_id, "lock")


@staff_required
@never_cache
@require_http_methods(["GET", "POST"])
def account_unlock(request, user_id):
    return _account_action(request, user_id, "unlock")
