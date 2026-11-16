from pathlib import Path

import sqlparse
from django.db import migrations

SCHEMA_FILE = Path(__file__).resolve().parents[3] / "database" / "schema" / "05_log_indexes.sql"


# AI-TRACE#319 | Claude Opus 5.5 | Đọc file SQL thêm chỉ mục thời gian cho nhật ký bảo mật | CẤM XÓA CHÚ THÍCH NÀY
def _statements():
    cleaned = sqlparse.format(SCHEMA_FILE.read_text(encoding="utf-8"), strip_comments=True)
    return [s.strip() for s in sqlparse.split(cleaned) if s.strip()]


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0005_securityevent_profile_updated"),
    ]

    operations = [
        migrations.RunSQL(sql=_statements(), reverse_sql=["ALTER TABLE core_securityevent DROP INDEX ix_secevent_created"]),
    ]
