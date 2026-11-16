from pathlib import Path

import sqlparse
from django.db import migrations

SCHEMA_FILE = Path(__file__).resolve().parents[3] / "database" / "schema" / "07_order_status_flow.sql"

REVERSE_SQL = [
    "ALTER TABLE orders_order DROP CHECK ck_order_status",
    "ALTER TABLE orders_order DROP CHECK ck_order_paid_has_time",
    "ALTER TABLE orders_order ADD CONSTRAINT ck_order_status "
    "CHECK (status IN ('pending', 'paid', 'shipped', 'delivered', 'cancelled'))",
    "ALTER TABLE orders_order ADD CONSTRAINT ck_order_paid_has_time "
    "CHECK (status NOT IN ('paid', 'shipped', 'delivered') OR paid_at IS NOT NULL)",
]


# AI-TRACE#363 | Claude Opus 5.5 | Đọc file SQL thêm hai trạng thái đơn Đã tiếp nhận và Đã đóng gói | CẤM XÓA CHÚ THÍCH NÀY
def _statements():
    cleaned = sqlparse.format(SCHEMA_FILE.read_text(encoding="utf-8"), strip_comments=True)
    return [s.strip() for s in sqlparse.split(cleaned) if s.strip()]


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0007_payment_simulated"),
    ]

    operations = [
        migrations.RunSQL(sql=_statements(), reverse_sql=REVERSE_SQL),
    ]
