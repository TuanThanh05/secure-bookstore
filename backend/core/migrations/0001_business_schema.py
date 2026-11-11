"""Tạo các bảng nghiệp vụ (catalog_*, orders_*, payments_*, core_*).

Không sinh bằng makemigrations: migration này đọc SQL từ database/schema/
(nơi duy nhất định nghĩa lược đồ nghiệp vụ) rồi chạy bằng tài khoản migrate.
Phụ thuộc accounts/0001 vì các bảng có khóa ngoại tới accounts_user.

Trigger, view, thủ tục KHÔNG tạo ở đây mà ở database/objects/ (root chạy
bằng database/apply.sh), vì tài khoản migrate cố ý không có quyền đó.
"""
from pathlib import Path

import sqlparse
from django.db import migrations

# backend/core/migrations/ → lên 3 cấp là thư mục gốc repo
SCHEMA_DIR = Path(__file__).resolve().parents[3] / "database" / "schema"

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
]


def _statements(filename):
    """Tách file SQL thành từng câu lệnh (bỏ chú thích, bỏ câu rỗng)."""
    text = (SCHEMA_DIR / filename).read_text(encoding="utf-8")
    cleaned = sqlparse.format(text, strip_comments=True)
    return [s.strip() for s in sqlparse.split(cleaned) if s.strip()]


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(
            sql=_statements("01_tables.sql"),
            reverse_sql=[f"DROP TABLE IF EXISTS {t}" for t in BUSINESS_TABLES],
        ),
    ]
