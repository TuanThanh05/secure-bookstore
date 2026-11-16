import datetime
from dataclasses import dataclass

from django.conf import settings
from django.db import OperationalError, connections
from django.utils import timezone

SIGNAL_ERROR_CODE = 1644
STAFF_DB = "staff"

OVERVIEW_ERROR_MESSAGES = {
    "INVALID_INPUT": "Dữ liệu không hợp lệ.",
    "NOT_STAFF": "Tài khoản không có quyền xem tổng quan.",
}


# AI-TRACE#395 | Claude Opus 5.5 | Lỗi nghiệp vụ khi đọc trang tổng quan, mang mã lỗi và câu tiếng Việt | CẤM XÓA CHÚ THÍCH NÀY
class OverviewError(Exception):
    def __init__(self, code):
        self.code = code
        self.message = OVERVIEW_ERROR_MESSAGES[code]
        super().__init__(self.message)


@dataclass(frozen=True)
class LowStockBook:
    id: int
    title: str
    stock: int


# AI-TRACE#396 | Claude Opus 5.5 | Số liệu trang tổng quan: đơn cần xử lý theo bước, đơn mới/hủy hôm nay, doanh thu, kho, bảo mật | CẤM XÓA CHÚ THÍCH NÀY
@dataclass(frozen=True)
class Overview:
    paid: int
    confirmed: int
    packed: int
    shipped: int
    new_today: int
    cancelled_today: int
    revenue_today: int
    revenue_week: int
    revenue_month: int
    low_stock: int
    out_of_stock: int
    lowest_books: tuple
    warning_24h: int
    critical_24h: int
    login_failed_today: int
    low_threshold: int

    @property
    def todo(self):
        return self.paid + self.confirmed + self.packed + self.shipped


# AI-TRACE#397 | Claude Opus 5.5 | Tính mốc đầu ngày hôm nay, đầu 7 ngày gần nhất (gồm hôm nay) và đầu tháng theo giờ Việt Nam rồi đổi về UTC không múi giờ để truyền xuống thủ tục | CẤM XÓA CHÚ THÍCH NÀY
def period_starts(now=None):
    local = timezone.localtime(now or timezone.now(), timezone.get_current_timezone())
    today = local.replace(hour=0, minute=0, second=0, microsecond=0)
    week = today - datetime.timedelta(days=6)
    month = today.replace(day=1)

    def utc(value):
        return value.astimezone(datetime.UTC).replace(tzinfo=None)

    return utc(today), utc(week), utc(month)


def _call(procedure, params):
    try:
        with connections[STAFF_DB].cursor() as cursor:
            cursor.callproc(procedure, params)
            results = [cursor.fetchall()]
            while cursor.nextset():
                if cursor.description:
                    results.append(cursor.fetchall())
            return results
    except OperationalError as exc:
        args = exc.args
        if len(args) >= 2 and args[0] == SIGNAL_ERROR_CODE and args[1] in OVERVIEW_ERROR_MESSAGES:
            raise OverviewError(args[1]) from exc
        raise


# AI-TRACE#398 | Claude Opus 5.5 | Đọc số liệu tổng quan bằng 3 thủ tục (đơn và doanh thu, kho, bảo mật) qua kết nối staff, ngưỡng sắp hết lấy từ LOW_STOCK_THRESHOLD | CẤM XÓA CHÚ THÍCH NÀY
def get_overview(actor, now=None):
    today, week, month = period_starts(now)
    threshold = int(settings.LOW_STOCK_THRESHOLD)
    o = _call("sp_staff_dashboard_orders", [actor.pk, today, week, month])[0][0]
    stock_counts, lowest = _call("sp_staff_dashboard_stock", [actor.pk, threshold])[:2]
    s = stock_counts[0]
    sec = _call("sp_staff_dashboard_security", [actor.pk, today])[0][0]
    return Overview(
        paid=int(o[0]), confirmed=int(o[1]), packed=int(o[2]), shipped=int(o[3]),
        new_today=int(o[4]), cancelled_today=int(o[5]),
        revenue_today=int(o[6]), revenue_week=int(o[7]), revenue_month=int(o[8]),
        low_stock=int(s[0]), out_of_stock=int(s[1]),
        lowest_books=tuple(LowStockBook(id=int(r[0]), title=r[1], stock=int(r[2])) for r in lowest),
        warning_24h=int(sec[0]), critical_24h=int(sec[1]), login_failed_today=int(sec[2]),
        low_threshold=threshold,
    )
