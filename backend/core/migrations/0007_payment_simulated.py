from pathlib import Path

import sqlparse
from django.db import migrations

SCHEMA_FILE = Path(__file__).resolve().parents[3] / "database" / "schema" / "06_payment_simulated.sql"

REVERSE_SQL = [
    "ALTER TABLE payments_payment DROP INDEX uq_payment_success_order",
    "ALTER TABLE payments_payment DROP COLUMN success_order_id",
    "ALTER TABLE payments_payment DROP CHECK ck_payment_provider",
    "ALTER TABLE payments_payment DROP CHECK ck_payment_success_valid",
    "ALTER TABLE payments_payment ADD CONSTRAINT ck_payment_success_valid CHECK "
    "(status <> 'success' OR (signature_valid = 1 AND transaction_id IS NOT NULL))",
    "ALTER TABLE payments_payment ALTER COLUMN provider SET DEFAULT 'mockpay'",
]


# AI-TRACE#350 | Claude Opus 5.5 | Đọc file SQL cho phép giao dịch thanh toán mô phỏng và chặn một đơn thanh toán hai lần | CẤM XÓA CHÚ THÍCH NÀY
def _statements():
    cleaned = sqlparse.format(SCHEMA_FILE.read_text(encoding="utf-8"), strip_comments=True)
    return [s.strip() for s in sqlparse.split(cleaned) if s.strip()]


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0006_log_indexes"),
    ]

    operations = [
        migrations.RunSQL(sql=_statements(), reverse_sql=REVERSE_SQL),
    ]
