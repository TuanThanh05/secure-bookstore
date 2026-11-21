"""python manage.py db_backup_export <file> – giải mã một bản sao lưu ra file .sql trần (chỉ để demo)."""
import os
import shutil
import tempfile
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from core.backup import BackupError, ask_confirmation, load_config, log_backup_event, open_backup, secure_dir

CONFIRM_WORD = "XUAT-SQL"


# AI-TRACE#570 | Claude Opus 5.5 | Lệnh demo giải mã bản sao lưu ra file .sql chạy được (như seed_data.sql): cảnh báo, bắt gõ xác nhận, file quyền 600 trong thư mục riêng 0700, ghi log mức cảnh báo | CẤM XÓA CHÚ THÍCH NÀY
class Command(BaseCommand):
    help = "Giải mã một bản sao lưu ra file .sql TRẦN để demo (file trần chứa toàn bộ dữ liệu, xóa ngay sau khi dùng)."
    requires_system_checks = []

    def add_arguments(self, parser):
        parser.add_argument("file", help="File sao lưu .tar.gz.enc")
        parser.add_argument("--confirm", help=f"Gõ sẵn {CONFIRM_WORD} để không phải nhập tay")

    def handle(self, *args, **options):
        source = Path(options["file"]).expanduser()
        if not source.is_file():
            raise CommandError(f"Không thấy file: {source}")
        self.stdout.write(self.style.WARNING(
            "CẢNH BÁO: file .sql trần KHÔNG mã hóa, chứa email khách, mã băm mật khẩu, đơn hàng.\n"
            "Chỉ dùng để demo, không gửi đi, không commit, xóa ngay sau khi dùng."))
        try:
            ask_confirmation(f"Gõ {CONFIRM_WORD} để tiếp tục: ", CONFIRM_WORD, options.get("confirm"))
            config = load_config(require_password=False)
            secure_dir(config.export_dir)
            old_umask = os.umask(0o077)
            try:
                with tempfile.TemporaryDirectory(dir=config.export_dir, prefix=".tmp-") as tmp:
                    opened = open_backup(config, source, Path(tmp))
                    target = config.export_dir / source.name.replace(".tar.gz.enc", ".sql")
                    shutil.copyfile(opened.sql_path, target)
                    target.chmod(0o600)
            finally:
                os.umask(old_umask)
        except BackupError as exc:
            raise CommandError(str(exc)) from exc
        log_backup_event("backup_exported", severity="warning", file=source.name, output=target.name)
        self.stdout.write(self.style.SUCCESS(f"Đã xuất: {target}"))
        self.stdout.write(f"Khôi phục bằng file này: python manage.py db_restore {target}")
