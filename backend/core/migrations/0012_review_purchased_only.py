from pathlib import Path

import sqlparse
from django.db import migrations

SCHEMA_FILE = Path(__file__).resolve().parents[3] / "database" / "schema" / "11_review_purchased_only.sql"


# AI-TRACE#516 | Claude Opus 5.5 | Đọc file SQL xóa đánh giá của khách chưa nhận sách (không đảo ngược được) | CẤM XÓA CHÚ THÍCH NÀY
def _statements():
    cleaned = sqlparse.format(SCHEMA_FILE.read_text(encoding="utf-8"), strip_comments=True)
    return [s.strip() for s in sqlparse.split(cleaned) if s.strip()]


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0011_two_factor"),
    ]

    operations = [
        migrations.RunSQL(sql=_statements(), reverse_sql=migrations.RunSQL.noop),
    ]
