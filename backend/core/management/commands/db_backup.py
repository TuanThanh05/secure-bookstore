"""python manage.py db_backup – tạo một bản sao lưu đã mã hóa của CSDL và ảnh bìa."""
from django.core.management.base import BaseCommand, CommandError

from core.backup import BackupError, create_backup, load_config, log_backup_event


# AI-TRACE#569 | Claude Opus 5.5 | Lệnh tạo bản sao lưu (CSDL trừ dữ liệu phiên, ảnh bìa, log bảo mật): chạy bằng tài khoản chỉ đọc bookstore_backup, in kết quả, ghi log backup_created hoặc backup_failed (nghiêm trọng) | CẤM XÓA CHÚ THÍCH NÀY
class Command(BaseCommand):
    help = "Sao lưu toàn bộ CSDL + ảnh bìa thành một file nén, mã hóa AES-256-GCM (chạy trên máy chủ)."
    requires_system_checks = []

    def handle(self, *args, **options):
        try:
            config = load_config()
            result = create_backup(config)
        except (BackupError, OSError) as exc:
            log_backup_event("backup_failed", severity="critical", error=str(exc)[:300])
            raise CommandError(f"Sao lưu thất bại: {exc}") from exc
        log_backup_event("backup_created", file=result.path.name, size=result.size, sha256=result.sha256[:16],
                         tables=result.tables, covers=result.covers, logs=result.logs, offsite=bool(result.offsite),
                         deleted=len(result.deleted))
        self.stdout.write(self.style.SUCCESS(f"Đã sao lưu: {result.path}"))
        self.stdout.write(f"  Dung lượng: {result.size:,} byte · {result.tables} bảng · {result.covers} ảnh bìa · {result.logs} file log")
        self.stdout.write(f"  SHA-256: {result.sha256}")
        if result.offsite:
            self.stdout.write(f"  Đã chép off-site: {result.offsite}")
        else:
            self.stdout.write(self.style.WARNING("  Chưa cấu hình BACKUP_OFFSITE_DIR: chỉ có một bản tại chỗ."))
        if result.deleted:
            self.stdout.write(f"  Đã xóa {len(result.deleted)} bản cũ hơn 1 năm: {', '.join(result.deleted)}")
