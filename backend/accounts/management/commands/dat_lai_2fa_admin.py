from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import DatabaseError, transaction

from accounts.emails import send_two_factor_email
from accounts.models import RecoveryCode, TotpDevice, User
from core.security_log import log_event
from core.session_store import end_user_sessions

from ._two_factor_cli import WRONG_SETTINGS, check_connection, enroll_in_terminal

CONFIRM_WORD = "dat lai"


# AI-TRACE#507 | Claude Opus 5.5 | Lệnh máy chủ cài lại 2 bước cho admin mất điện thoại: gõ xác nhận, gỡ thiết bị cũ, quét QR mới, đăng xuất mọi phiên, ghi log | CẤM XÓA CHÚ THÍCH NÀY | đã viết lại bởi Claude Opus 5.5 khi dùng chung end_user_sessions
class Command(BaseCommand):
    help = ("Cài lại xác thực 2 bước cho quản trị viên (mất/đổi điện thoại). "
            "Chạy trên máy chủ: --settings=bookstore.settings.migrate")

    def add_arguments(self, parser):
        parser.add_argument("username", help="Tên đăng nhập của quản trị viên")
        parser.add_argument("--confirm", action="store_true", help="Bỏ bước gõ xác nhận")

    def handle(self, *args, **options):
        check_connection()
        user = User.objects.filter(username=options["username"], is_staff=True).first()
        if user is None:
            raise CommandError("Không có tài khoản quản trị với tên đăng nhập này.")
        if not options["confirm"]:
            typed = input(f'Thiết bị 2 bước cũ của {user.get_username()} sẽ bị gỡ. Gõ "{CONFIRM_WORD}" để tiếp tục: ')
            if typed.strip() != CONFIRM_WORD:
                raise CommandError("Đã hủy. Không thay đổi gì.")
        try:
            with transaction.atomic(using=settings.AUTH_DB_ALIAS):
                RecoveryCode.objects.filter(user_id=user.pk).delete()
                TotpDevice.objects.filter(user_id=user.pk).delete()
                enroll_in_terminal(self, user)
        except DatabaseError as exc:
            raise CommandError(WRONG_SETTINGS) from exc

        ended = end_user_sessions(user.pk)
        log_event("two_factor_enabled", user=user, username=user.get_username(), ip_address="cli",
                  severity="warning", detail={"via": "cli", "kind": "admin_reset", "sessions_ended": ended})
        sent = send_two_factor_email(None, user, "enabled")
        self.stdout.write(self.style.SUCCESS(f"Đã cài lại xác thực 2 bước cho {user.get_username()}."))
        self.stdout.write(f"Đã đăng xuất {ended} phiên đang mở.")
        self.stdout.write("Đã gửi thư báo tới email của tài khoản." if sent else "Chưa gửi được thư báo (xem security.log).")
