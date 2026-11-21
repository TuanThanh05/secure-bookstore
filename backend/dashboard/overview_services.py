import datetime
import json
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


class OverviewError(Exception):
    def __init__(self, code):
        self.code = code
        self.message = OVERVIEW_ERROR_MESSAGES[code]
        super().__init__(self.message)


@dataclass(frozen=True)
class BackupStatus:
    last_success: datetime.datetime | None
    last_size: int | None
    last_failure: datetime.datetime | None
    last_verify: datetime.datetime | None
    last_verify_ok: bool | None

    @property
    def failing(self):
        return self.last_failure is not None and (self.last_success is None or self.last_failure > self.last_success)

    @property
    def stale(self):
        return self.last_success is None or self.last_success < datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=7)


def _backup_status(rows):
    data = {}
    for event_type, created_at, detail in rows:
        if isinstance(detail, (bytes, str)):
            try:
                detail = json.loads(detail)
            except ValueError:
                detail = {}
        data[event_type] = (_aware(created_at), detail if isinstance(detail, dict) else {})
    success = data.get("backup_created", (None, {}))
    verify = data.get("restore_verified", (None, {}))
    size = success[1].get("size")
    return BackupStatus(
        last_success=success[0], last_size=int(size) if isinstance(size, int) else None,
        last_failure=data.get("backup_failed", (None, {}))[0],
        last_verify=verify[0], last_verify_ok=verify[1].get("ok") if verify[0] else None,
    )


def _aware(value):
    if value is None or value.tzinfo is not None:
        return value
    return value.replace(tzinfo=datetime.UTC)


@dataclass(frozen=True)
class LowStockBook:
    id: int
    title: str
    stock: int


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
    backup: BackupStatus

    @property
    def todo(self):
        return self.paid + self.confirmed + self.packed + self.shipped


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


def get_overview(actor, now=None):
    today, week, month = period_starts(now)
    threshold = int(settings.LOW_STOCK_THRESHOLD)
    o = _call("sp_staff_dashboard_orders", [actor.pk, today, week, month])[0][0]
    stock_counts, lowest = _call("sp_staff_dashboard_stock", [actor.pk, threshold])[:2]
    s = stock_counts[0]
    sec = _call("sp_staff_dashboard_security", [actor.pk, today])[0][0]
    backup = _backup_status(_call("sp_staff_dashboard_backup", [actor.pk])[0])
    return Overview(
        paid=int(o[0]), confirmed=int(o[1]), packed=int(o[2]), shipped=int(o[3]),
        new_today=int(o[4]), cancelled_today=int(o[5]),
        revenue_today=int(o[6]), revenue_week=int(o[7]), revenue_month=int(o[8]),
        low_stock=int(s[0]), out_of_stock=int(s[1]),
        lowest_books=tuple(LowStockBook(id=int(r[0]), title=r[1], stock=int(r[2])) for r in lowest),
        warning_24h=int(sec[0]), critical_24h=int(sec[1]), login_failed_today=int(sec[2]),
        low_threshold=threshold, backup=backup,
    )
