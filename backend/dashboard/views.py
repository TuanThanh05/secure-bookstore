from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_GET, require_http_methods

from core.decorators import mark_recent_auth, recent_auth_required, staff_required
from core.security_log import log_event

from .forms import ReauthForm


@staff_required
@require_GET
def index(request):
    return render(request, "dashboard/index.html")


@staff_required
@require_GET
def books(request):
    return render(request, "dashboard/books.html")


@staff_required
@require_GET
def orders(request):
    return render(request, "dashboard/orders.html")


@staff_required
@recent_auth_required
@require_GET
def accounts(request):
    return render(request, "dashboard/accounts.html")


@staff_required
@require_GET
def logs(request):
    return render(request, "dashboard/logs.html")


@staff_required
@require_GET
def profile(request):
    return render(request, "dashboard/profile.html")


def _safe_next(request, value):
    if value and url_has_allowed_host_and_scheme(value, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        return value
    return reverse("dashboard:accounts")


@staff_required
@require_http_methods(["GET", "POST"])
def reauth(request):
    next_url = _safe_next(request, request.POST.get("next") or request.GET.get("next"))
    if request.method == "POST":
        form = ReauthForm(request, data=request.POST)
        if form.is_valid():
            mark_recent_auth(request)
            log_event("login_success", request, user=request.user, username=request.user.get_username(), detail={"step_up": True})
            return redirect(next_url)
        if form.user_mismatch:
            log_event("access_denied", request, severity="warning", user=request.user, username=request.user.get_username(), detail={"step_up": "user_mismatch"})
    else:
        form = ReauthForm(request)
    return render(request, "dashboard/reauth.html", {"form": form, "next": next_url})
