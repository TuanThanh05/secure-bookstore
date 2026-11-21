from pathlib import Path

import MySQLdb
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from core.dbadmin import admin_secret, connect_admin, db_settings, load_admin_env, split_sql

SQL_FILES = ("02_trigger_thu_tuc.sql", "03_phan_quyen.sql")
PAYMENT_GRANT = "GRANT EXECUTE ON PROCEDURE sp_payment_simulate TO 'r_customer'"
PAYMENT_REVOKE = "REVOKE IF EXISTS EXECUTE ON PROCEDURE sp_payment_simulate FROM 'r_customer'"


def apply_payment_simulation(cursor, enabled):
    cursor.execute(PAYMENT_GRANT if enabled else PAYMENT_REVOKE)
    return "cấp" if enabled else "thu hồi"


class Command(BaseCommand):
    help = "Chạy database/02_trigger_thu_tuc.sql rồi database/03_phan_quyen.sql bằng tài khoản quản trị."
    requires_system_checks = []

    def add_arguments(self, parser):
        parser.add_argument("--root-user", default="root", help="Tài khoản quản trị MySQL (mặc định: root)")

    def handle(self, *args, **options):
        load_admin_env()
        db_name = db_settings()["NAME"]
        password = admin_secret("MYSQL_ROOT_PASSWORD", f"Mật khẩu MySQL của {options['root_user']}: ")

        base = Path(settings.REPO_DIR) / "database"
        files = [base / name for name in SQL_FILES]
        missing = [path.name for path in files if not path.is_file()]
        if missing:
            raise CommandError(f"Thiếu file trong {base}: {', '.join(missing)}.")

        conn = connect_admin(options["root_user"], password, database=db_name)
        try:
            with conn.cursor() as cur:
                for path in files:
                    statements = split_sql(path.read_text(encoding="utf-8"))
                    for number, sql in enumerate(statements, start=1):
                        try:
                            cur.execute(sql)  # không truyền tham số: MySQLdb không đụng tới dấu %
                        except MySQLdb.Error as exc:
                            raise CommandError(
                                f"{path.relative_to(base.parent)}, câu lệnh thứ {number}: {exc.args}"
                            ) from exc
                    self.stdout.write(f"  ✓ {path.relative_to(base.parent)} ({len(statements)} câu lệnh)")
                action = apply_payment_simulation(cur, settings.PAYMENT_SIMULATION)
                self.stdout.write(f"  ✓ PAYMENT_SIMULATION={settings.PAYMENT_SIMULATION}: {action} quyền gọi sp_payment_simulate của r_customer")
        finally:
            conn.close()

        self.stdout.write(self.style.SUCCESS("Xong: đã tạo trigger/view/thủ tục và cấp quyền."))
