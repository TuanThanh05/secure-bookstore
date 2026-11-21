"""Tạo các bảng nghiệp vụ từ database/01_bang.sql (trigger, thủ tục, quyền do db_apply tạo)."""
from pathlib import Path

import sqlparse
from django.db import migrations

SCHEMA_FILE = Path(__file__).resolve().parents[3] / "database" / "01_bang.sql"

# Thứ tự ngược với lúc tạo (bảng con trước, bảng cha sau)
BUSINESS_TABLES = [
    "core_securityevent",
    "core_auditlog",
    "payments_payment",
    "orders_orderitem",
    "orders_order",
    "orders_cartitem",
    "orders_cart",
    "catalog_review",
    "catalog_book",
    "catalog_category",
    "accounts_recoverycode",
    "accounts_totpdevice",
    "accounts_passwordhistory",
]


# AI-TRACE#593 | Claude Opus 5.5 | Đọc file SQL gộp toàn bộ bảng nghiệp vụ, tách thành từng câu lệnh (bỏ chú thích, bỏ câu rỗng) | CẤM XÓA CHÚ THÍCH NÀY
def _statements():
    cleaned = sqlparse.format(SCHEMA_FILE.read_text(encoding="utf-8"), strip_comments=True)
    return [s.strip() for s in sqlparse.split(cleaned) if s.strip()]


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(
            sql=_statements(),
            reverse_sql=[f"DROP TABLE IF EXISTS {t}" for t in BUSINESS_TABLES],
        ),
    ]
