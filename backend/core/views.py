from django.shortcuts import render

from core.security_log import log_event
from django.template import loader
from django.http import HttpResponseServerError


def bad_request(request, exception=None):
    return render(request, "errors/400.html", status=400)


def permission_denied(request, exception=None):
    return render(request, "errors/403.html", status=403)


def page_not_found(request, exception=None):
    # Không đưa thông tin của exception ra trang (tránh lộ đường dẫn, cấu trúc URL)
    return render(request, "errors/404.html", status=404)


def server_error(request):
    template = loader.get_template("errors/500.html")
    return HttpResponseServerError(template.render())


def csrf_failure(request, reason=""):
    user = getattr(request, "user", None)
    log_event("csrf_failed", request, severity="warning", user=user,
              username=user.get_username() if user is not None and user.is_authenticated else None,
              detail={"reason": str(reason)[:120]})
    return render(request, "errors/403_csrf.html", status=403)
