"""python manage.py db_restore <file> – khôi phục CSDL từ bản sao lưu (ghi đè, cần root)."""
import os
import tempfile
from pathlib import Path

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

from core.backup import (BackupError, ask_confirmation, create_backup, execute_sql_file, load_config,
                         log_backup_event, open_backup, restore_covers, restore_logs)
from core.dbadmin import admin_secret, connect_admin, db_settings


class Command(BaseCommand):
    help = "Khôi phục CSDL từ file sao lưu (.tar.gz.enc) hoặc file .sql trần. GHI ĐÈ dữ liệu hiện tại."
    requires_system_checks = []

    def add_arguments(self, parser):
        parser.add_argument("file", help="File .tar.gz.enc (do db_backup tạo) hoặc .sql (do db_backup_export tạo)")
        parser.add_argument("--root-user", default="root", help="Tài khoản quản trị MySQL (mặc định: root)")
        parser.add_argument("--confirm", help="Gõ sẵn tên CSDL để không phải nhập tay")
        parser.add_argument("--skip-media", action="store_true", help="Không chép lại ảnh bìa")

    def handle(self, *args, **options):
        source = Path(options["file"]).expanduser()
        if not source.is_file():
            raise CommandError(f"Không thấy file: {source}")
        plain = source.suffix == ".sql"
        db_name = db_settings()["NAME"]
        self.stdout.write(self.style.WARNING(
            f"KHÔI PHỤC sẽ GHI ĐÈ toàn bộ bảng, thủ tục, trigger, Event của CSDL `{db_name}` "
            "bằng nội dung file sao lưu. Trước đó hệ thống tự sao lưu bản hiện tại."))
        try:
            ask_confirmation(f"Gõ lại tên CSDL ({db_name}) để tiếp tục: ", db_name, options.get("confirm"))
            config = load_config()
            root_password = admin_secret("MYSQL_ROOT_PASSWORD", f"Mật khẩu MySQL của {options['root_user']}: ")
            safety = create_backup(config)
            log_backup_event("backup_created", file=safety.path.name, size=safety.size, reason="before_restore")
            self.stdout.write(f"Đã sao lưu bản hiện tại trước khi khôi phục: {safety.path}")
            with tempfile.TemporaryDirectory(dir=config.backup_dir, prefix=".tmp-") as tmp:
                if plain:
                    sql_path, covers, logs = source, (), ()
                else:
                    opened = open_backup(config, source, Path(tmp))
                    sql_path, covers, logs = opened.sql_path, opened.covers, opened.logs
                conn = connect_admin(options["root_user"], root_password, database=db_name)
                try:
                    statements = execute_sql_file(conn, sql_path)
                finally:
                    conn.close()
                restored = 0 if options["skip_media"] else restore_covers(covers)
                logs_folder = restore_logs(config, logs, source.name)
        except BackupError as exc:
            raise CommandError(f"Khôi phục thất bại: {exc}") from exc

        os.environ["MYSQL_ROOT_PASSWORD"] = root_password
        self.stdout.write("Cấp lại quyền cho thủ tục vừa tạo lại (db_apply)...")
        call_command("db_apply", root_user=options["root_user"], stdout=self.stdout)
        log_backup_event("restore_performed", severity="warning", file=source.name, database=db_name,
                         statements=statements, covers=restored, logs=len(logs), safety_backup=safety.path.name)
        self.stdout.write(self.style.SUCCESS(
            f"Đã khôi phục `{db_name}` từ {source.name}: {statements} câu lệnh SQL, {restored} ảnh bìa."))
        if logs_folder:
            self.stdout.write(f"Log bảo mật trong bản sao lưu đã chép ra {logs_folder} (logs/security.log đang chạy giữ nguyên).")
        self.stdout.write("Mọi phiên đăng nhập đã bị xóa: khách và admin phải đăng nhập lại.")
        self.stdout.write("Nên chạy tiếp: python manage.py db_check_grants")
