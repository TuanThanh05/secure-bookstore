import getpass

from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.core.validators import validate_email
from django.db import DatabaseError, transaction
from django.db.models import Q

from accounts.models import User
from core.security_log import log_event

from ._two_factor_cli import WRONG_SETTINGS, check_connection, enroll_in_terminal

MAX_TRIES = 3


# AI-TRACE#506 | Claude Opus 5.5 | Lệnh máy chủ tạo admin duy nhất: kiểm tra quy tắc mật khẩu, bắt buộc cài 2 bước ngay, lỗi ở bất kỳ bước nào thì không tạo gì | CẤM XÓA CHÚ THÍCH NÀY
class Command(BaseCommand):
    help = ("Tạo tài khoản quản trị DUY NHẤT kèm xác thực 2 bước (Google Authenticator). "
            "Chạy trên máy chủ: --settings=bookstore.settings.migrate")

    def add_arguments(self, parser):
        parser.add_argument("username", help="Tên đăng nhập của quản trị viên")
        parser.add_argument("email", help="Email thật của quản trị viên (nhận thư báo)")

    def _ask_password(self, user):
        for _ in range(MAX_TRIES):
            first = getpass.getpass("Mật khẩu: ")
            second = getpass.getpass("Nhập lại mật khẩu: ")
            if first != second:
                self.stderr.write("Hai lần nhập không khớp.")
                continue
            try:
                validate_password(first, user)
            except ValidationError as exc:
                for message in exc.messages:
                    self.stderr.write(message)
                continue
            return first
        raise CommandError(f"Nhập sai {MAX_TRIES} lần. Chưa tạo tài khoản.")

    def handle(self, *args, **options):
        check_connection()
        if User.objects.filter(Q(is_staff=True) | Q(is_superuser=True)).exists():
            raise CommandError("Đã có tài khoản quản trị. Hệ thống chỉ có một admin; "
                               "mất điện thoại thì dùng lệnh dat_lai_2fa_admin.")
        username, email = options["username"], options["email"].strip().lower()
        try:
            User._meta.get_field("username").run_validators(username)
            validate_email(email)
        except ValidationError as exc:
            raise CommandError(" ".join(exc.messages)) from exc
        if User.objects.filter(Q(username__iexact=username) | Q(email__iexact=email)).exists():
            raise CommandError("Tên đăng nhập hoặc email đã được dùng.")

        user = User(username=username, email=email, is_staff=True, is_superuser=True, email_verified=True)
        password = self._ask_password(user)
        try:
            with transaction.atomic(using=settings.AUTH_DB_ALIAS):
                user.set_password(password)
                user.save()
                enroll_in_terminal(self, user)
        except DatabaseError as exc:
            raise CommandError(WRONG_SETTINGS) from exc

        log_event("two_factor_enabled", user=user, username=user.get_username(), ip_address="cli",
                  detail={"via": "cli", "kind": "admin_created"})
        self.stdout.write(self.style.SUCCESS(f"Đã tạo quản trị viên {username} và bật xác thực 2 bước."))
