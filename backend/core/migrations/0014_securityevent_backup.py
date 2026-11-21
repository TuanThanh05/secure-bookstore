from pathlib import Path

import sqlparse
from django.db import migrations

SCHEMA_FILE = Path(__file__).resolve().parents[3] / "database" / "schema" / "13_securityevent_backup.sql"

PREVIOUS_TYPES = (
    "login_success", "login_failed", "account_locked", "logout", "password_changed",
    "password_reset_requested", "otp_failed", "access_denied", "idor_attempt", "db_permission_denied",
    "payment_signature_invalid", "payment_replay", "payment_amount_mismatch", "upload_rejected",
    "rate_limited", "csrf_failed", "invalid_input", "register_success", "register_existing_email",
    "register_link_invalid", "email_sent", "email_send_failed", "sensitive_data_viewed", "profile_updated", "captcha_failed",
    "two_factor_enabled", "two_factor_disabled", "two_factor_recovery_used", "order_hold_abuse",
)

REVERSE_SQL = [
    "ALTER TABLE core_securityevent DROP CHECK ck_secevent_type",
    "DELETE FROM core_securityevent WHERE event_type IN "
    "('backup_created', 'backup_failed', 'backup_exported', 'restore_performed', 'restore_verified')",
    "ALTER TABLE core_securityevent ADD CONSTRAINT ck_secevent_type CHECK (event_type IN ("
    + ", ".join(f"'{name}'" for name in PREVIOUS_TYPES)
    + "))",
]


# AI-TRACE#556 | Claude Opus 5.5 | Đọc file SQL thêm các loại sự kiện sao lưu và khôi phục CSDL | CẤM XÓA CHÚ THÍCH NÀY
def _statements():
    cleaned = sqlparse.format(SCHEMA_FILE.read_text(encoding="utf-8"), strip_comments=True)
    return [s.strip() for s in sqlparse.split(cleaned) if s.strip()]


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0013_securityevent_order_hold"),
    ]

    operations = [
        migrations.RunSQL(sql=_statements(), reverse_sql=REVERSE_SQL),
    ]
