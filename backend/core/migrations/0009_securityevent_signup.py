from pathlib import Path

import sqlparse
from django.db import migrations

SCHEMA_FILE = Path(__file__).resolve().parents[3] / "database" / "schema" / "08_securityevent_signup.sql"

PREVIOUS_TYPES = (
    "login_success", "login_failed", "account_locked", "logout", "password_changed",
    "password_reset_requested", "otp_failed", "access_denied", "idor_attempt", "db_permission_denied",
    "payment_signature_invalid", "payment_replay", "payment_amount_mismatch", "upload_rejected",
    "rate_limited", "csrf_failed", "invalid_input", "register_success", "register_existing_email",
    "email_sent", "email_send_failed", "email_verified", "email_verify_failed", "login_blocked_unverified",
    "sensitive_data_viewed", "profile_updated",
)

REVERSE_SQL = [
    "ALTER TABLE core_securityevent DROP CHECK ck_secevent_type",
    "DELETE FROM core_securityevent WHERE event_type = 'register_link_invalid'",
    "ALTER TABLE core_securityevent ADD CONSTRAINT ck_secevent_type CHECK (event_type IN ("
    + ", ".join(f"'{name}'" for name in PREVIOUS_TYPES)
    + "))",
]


# AI-TRACE#429 | Claude Opus 5.5 | Đọc file SQL đổi danh sách loại sự kiện cho luồng đăng ký bắt đầu bằng email | CẤM XÓA CHÚ THÍCH NÀY
def _statements():
    cleaned = sqlparse.format(SCHEMA_FILE.read_text(encoding="utf-8"), strip_comments=True)
    return [s.strip() for s in sqlparse.split(cleaned) if s.strip()]


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0008_order_status_flow"),
    ]

    operations = [
        migrations.RunSQL(sql=_statements(), reverse_sql=REVERSE_SQL),
    ]
