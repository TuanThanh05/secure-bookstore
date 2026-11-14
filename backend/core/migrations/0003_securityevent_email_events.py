from pathlib import Path

import sqlparse
from django.db import migrations

SCHEMA_FILE = Path(__file__).resolve().parents[3] / "database" / "schema" / "02_securityevent_email_events.sql"


def _statements():
    cleaned = sqlparse.format(SCHEMA_FILE.read_text(encoding="utf-8"), strip_comments=True)
    return [s.strip() for s in sqlparse.split(cleaned) if s.strip()]


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0002_securityevent"),
    ]

    operations = [
        migrations.RunSQL(sql=_statements(), reverse_sql=migrations.RunSQL.noop),
    ]
