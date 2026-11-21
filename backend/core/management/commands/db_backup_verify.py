"""python manage.py db_backup_verify [file] – thử khôi phục bản sao lưu vào CSDL tạm rồi đối chiếu."""
import tempfile
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from core.backup import (BACKUP_USER, BackupError, compare_counts, execute_sql_file, latest_backup, load_config,
                         log_backup_event, open_backup, table_counts)
from core.dbadmin import SAFE_DB_NAME, admin_secret, connect_admin, db_settings

WRITE_PRIVILEGES = ("ALL PRIVILEGES", "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "FILE",
                    "SUPER", "GRANT OPTION", "LOCK TABLES", "PROCESS")


class Command(BaseCommand):
    help = "Thử khôi phục một bản sao lưu vào CSDL tạm, đối chiếu số dòng với lúc sao lưu, rồi xóa CSDL tạm."
    requires_system_checks = []

    def add_arguments(self, parser):
        parser.add_argument("file", nargs="?", help="File .tar.gz.enc (mặc định: bản mới nhất trong BACKUP_DIR)")
        parser.add_argument("--root-user", default="root", help="Tài khoản quản trị MySQL (mặc định: root)")

    def handle(self, *args, **options):
        db_name = db_settings()["NAME"]
        check_db = f"{db_name}_restore_check"
        if not SAFE_DB_NAME.match(check_db):
            raise CommandError("Tên CSDL tạm không hợp lệ.")
        try:
            config = load_config(require_password=False)
            source = Path(options["file"]).expanduser() if options["file"] else latest_backup(config.backup_dir)
            if source is None or not source.is_file():
                raise BackupError("Không có bản sao lưu nào để kiểm tra. Chạy python manage.py db_backup trước.")
            root_password = admin_secret("MYSQL_ROOT_PASSWORD", f"Mật khẩu MySQL của {options['root_user']}: ")
            with tempfile.TemporaryDirectory(dir=config.backup_dir, prefix=".tmp-") as tmp:
                opened = open_backup(config, source, Path(tmp))
                conn = connect_admin(options["root_user"], root_password)
                try:
                    actual, readonly, statements = self._restore_and_count(conn, check_db, opened.sql_path)
                finally:
                    with conn.cursor() as cur:
                        cur.execute(f"DROP DATABASE IF EXISTS `{check_db}`")
                    conn.close()
        except BackupError as exc:
            log_backup_event("restore_verified", severity="critical", ok=False, error=str(exc)[:300])
            raise CommandError(f"Kiểm tra khôi phục thất bại: {exc}") from exc

        expected = opened.manifest.get("counts", {})
        diffs = compare_counts(expected, actual)
        self._report(source, opened.manifest, expected, actual, diffs, readonly, statements)
        ok = not diffs and readonly
        log_backup_event("restore_verified", severity="info" if ok else "critical", ok=ok, file=source.name,
                         tables=sum(1 for k in actual if not k.startswith("#")),
                         mismatches=[k for k, *_ in diffs][:10], backup_user_readonly=readonly)
        if not ok:
            raise CommandError("Kiểm tra khôi phục KHÔNG đạt (xem bảng trên).")

    def _restore_and_count(self, conn, check_db, sql_path):
        with conn.cursor() as cur:
            cur.execute(f"DROP DATABASE IF EXISTS `{check_db}`")
            cur.execute(f"CREATE DATABASE `{check_db}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            cur.execute(f"USE `{check_db}`")
        statements = execute_sql_file(conn, sql_path)
        with conn.cursor() as cur:
            cur.execute("SELECT event_name FROM information_schema.events WHERE event_schema = %s", (check_db,))
            for (event,) in cur.fetchall():
                cur.execute(f"ALTER EVENT `{check_db}`.`{event}` DISABLE")
            cur.execute("SHOW GRANTS FOR %s@'localhost'", (BACKUP_USER,))
            grants = " ".join(row[0].upper() for row in cur.fetchall())
        readonly = not any(f"{word} ON" in grants or f"{word}," in grants for word in WRITE_PRIVILEGES)
        return table_counts(conn, check_db), readonly, statements

    def _report(self, source, manifest, expected, actual, diffs, readonly, statements):
        self.stdout.write(f"Bản sao lưu: {source.name} (tạo lúc {manifest.get('created_at')})")
        self.stdout.write(f"Đã chạy {statements} câu lệnh SQL vào CSDL tạm.")
        self.stdout.write(f"{'Bảng / đối tượng':<34}{'Lúc sao lưu':>12}{'Khôi phục':>12}")
        for key in sorted(set(expected) | set(actual)):
            mark = "" if expected.get(key) == actual.get(key) else "  <-- LỆCH"
            self.stdout.write(f"{key:<34}{str(expected.get(key, '-')):>12}{str(actual.get(key, '-')):>12}{mark}")
        state = self.style.SUCCESS("chỉ đọc") if readonly else self.style.ERROR("CÓ QUYỀN GHI")
        self.stdout.write(f"Tài khoản {BACKUP_USER}: {state}")
        if not diffs and readonly:
            self.stdout.write(self.style.SUCCESS("Kiểm tra khôi phục ĐẠT: dữ liệu khôi phục khớp lúc sao lưu."))
