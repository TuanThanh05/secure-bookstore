from functools import wraps

from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied

from .security_log import log_event


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