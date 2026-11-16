from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET

from core.decorators import recent_auth_required, staff_required
from core.security_log import log_event

from .forms import AuditLogFilterForm, SecurityLogFilterForm
from .log_services import PAGE_SIZE, LogError, list_audit_log, list_security_events


# AI-TRACE#339 | Claude Opus 5.5 | Dữ liệu phân trang cho trang nhật ký: dùng Paginator trên tổng số dòng thủ tục trả về, giữ bộ lọc trong link trang | CẤM XÓA CHÚ THÍCH NÀY
def _pager(request, total, page):
    paginator = Paginator(range(total), PAGE_SIZE)
    query = request.GET.copy()
    query.pop("trang", None)
    return paginator.get_page(page), query.urlencode()


def _page_number(request):
    try:
        return max(1, int(request.GET.get("trang", 1)))
    except (TypeError, ValueError):
        return 1


def _log_view(request, tab, filters):
    log_event("sensitive_data_viewed", request, user=request.user, username=request.user.get_username(),
              detail={"fields": [tab], "owner": "system", "filters": filters})


# AI-TRACE#340 | Claude Opus 5.5 | Tab nhật ký bảo mật: cần xác thực lại, lọc loại/mức độ/ngày/username-IP, mỗi lần xem ghi log | CẤM XÓA CHÚ THÍCH NÀY
@staff_required
@recent_auth_required
@never_cache
@require_GET
def logs(request):
    form = SecurityLogFilterForm(request.GET or None)
    rows, total, page = [], 0, _page_number(request)
    filters = {}
    if form.is_bound and not form.is_valid():
        messages.error(request, "Bộ lọc không hợp lệ.")
    else:
        data = form.cleaned_data if form.is_bound else {}
        start, end = form.range() if form.is_bound else (None, None)
        filters = {"loai": data.get("loai") or None, "muc_do": data.get("muc_do") or None,
                   "tu": str(data.get("tu") or "") or None, "den": str(data.get("den") or "") or None,
                   "tim": data.get("tim") or None}
        try:
            rows, total, page = list_security_events(
                request.user, event_type=data.get("loai"), severity=data.get("muc_do"), start=start, end=end,
                keyword=data.get("tim"), page=page)
        except LogError as exc:
            messages.error(request, exc.message)
    _log_view(request, "security_log", filters)
    pager, querystring = _pager(request, total, page)
    return render(request, "dashboard/logs.html", {
        "tab": "security", "form": form, "events": rows, "total": total, "pager": pager,
        "querystring": querystring, "filtered": any(filters.values()),
    })


# AI-TRACE#341 | Claude Opus 5.5 | Tab nhật ký thay đổi dữ liệu: cần xác thực lại, lọc bảng/hành động/ngày/id bản ghi, mỗi lần xem ghi log | CẤM XÓA CHÚ THÍCH NÀY
@staff_required
@recent_auth_required
@never_cache
@require_GET
def logs_audit(request):
    form = AuditLogFilterForm(request.GET or None)
    rows, total, page = [], 0, _page_number(request)
    filters = {}
    if form.is_bound and not form.is_valid():
        messages.error(request, "Bộ lọc không hợp lệ.")
    else:
        data = form.cleaned_data if form.is_bound else {}
        start, end = form.range() if form.is_bound else (None, None)
        filters = {"bang": data.get("bang") or None, "hanh_dong": data.get("hanh_dong") or None,
                   "tu": str(data.get("tu") or "") or None, "den": str(data.get("den") or "") or None,
                   "ma": data.get("ma")}
        try:
            rows, total, page = list_audit_log(
                request.user, table=data.get("bang"), action=data.get("hanh_dong"), start=start, end=end,
                record_id=data.get("ma"), page=page)
        except LogError as exc:
            messages.error(request, exc.message)
    _log_view(request, "audit_log", filters)
    pager, querystring = _pager(request, total, page)
    return render(request, "dashboard/logs.html", {
        "tab": "audit", "form": form, "entries": rows, "total": total, "pager": pager,
        "querystring": querystring, "filtered": any(v for v in filters.values()),
    })
