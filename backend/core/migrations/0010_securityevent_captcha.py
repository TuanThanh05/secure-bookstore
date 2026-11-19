from pathlib import Path

import sqlparse
from django.db import migrations

SCHEMA_FILE = Path(__file__).resolve().parents[3] / "database" / "schema" / "09_securityevent_captcha.sql"

PREVIOUS_TYPES = (
    "login_success", "login_failed", "account_locked", "logout", "password_changed",
    "password_reset_requested", "otp_failed", "access_denied", "idor_attempt", "db_permission_denied",
    "payment_signature_invalid", "payment_replay", "payment_amount_mismatch", "upload_rejected",
    "rate_limited", "csrf_failed", "invalid_input", "register_success", "register_existing_email",
    "register_link_invalid", "email_sent", "email_send_failed", "sensitive_data_viewed", "profile_updated",
)

REVERSE_SQL = [
    "ALTER TABLE core_securityevent DROP CHECK ck_secevent_type",
    "DELETE FROM core_securityevent WHERE event_type = 'captcha_failed'",
    "ALTER TABLE core_securityevent ADD CONSTRAINT ck_secevent_type CHECK (event_type IN ("
    + ", ".join(f"'{name}'" for name in PREVIOUS_TYPES)
    + "))",
]


# AI-TRACE#441 | Claude Opus 5.5 | Đọc file SQL thêm loại sự kiện CAPTCHA không đạt | CẤM XÓA CHÚ THÍCH NÀY
def _statements():
    cleaned = sqlparse.format(SCHEMA_FILE.read_text(encoding="utf-8"), strip_comments=True)
    return [s.strip() for s in sqlparse.split(cleaned) if s.strip()]


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0009_securityevent_signup"),
    ]

    operations = [
        migrations.RunSQL(sql=_statements(), reverse_sql=REVERSE_SQL),
    ]
