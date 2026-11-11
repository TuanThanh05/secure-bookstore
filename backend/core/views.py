"""View dùng chung: trang lỗi tùy chỉnh và trang lỗi CSRF.

Các handler này chỉ có tác dụng khi DEBUG = False (môi trường prod).
Khi DEBUG = True, Django hiện trang lỗi chi tiết để lập trình viên gỡ lỗi.
Bước sau: ghi sự kiện bảo mật (403, CSRF) vào core_securityevent và security.log.
"""
from django.shortcuts import render
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
    # Không dùng render(request, ...): lỗi 500 có thể do CSDL, context processor
    # đụng tới user/session có thể gây lỗi tiếp. Render template không cần request.
    template = loader.get_template("errors/500.html")
    return HttpResponseServerError(template.render())


def csrf_failure(request, reason=""):
    # Không hiện "reason" cho người dùng (chỉ dùng để ghi log ở bước sau)
    return render(request, "errors/403_csrf.html", status=403)
