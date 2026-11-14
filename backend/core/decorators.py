import time
from functools import wraps
from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.urls import reverse

from .security_log import log_event

REAUTH_SESSION_KEY = "reauth"


def staff_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        if not user.is_staff:
            log_event("access_denied", request, severity="warning", user=user, username=user.get_username())
            raise PermissionDenied
        return view_func(request, *args, **kwargs)

    return wrapper


def mark_recent_auth(request):
    request.session.cycle_key()
    request.session[REAUTH_SESSION_KEY] = {"user_id": request.user.pk, "at": int(time.time())}


def has_recent_auth(request):
    data = request.session.get(REAUTH_SESSION_KEY)
    if not isinstance(data, dict) or data.get("user_id") != request.user.pk:
        return False
    age = int(time.time()) - int(data.get("at", 0))
    return 0 <= age <= settings.REAUTH_MAX_AGE


def recent_auth_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not has_recent_auth(request):
            query = urlencode({"next": request.get_full_path()})
            return redirect(f"{reverse('dashboard:reauth')}?{query}")
        return view_func(request, *args, **kwargs)

    return wrapper
