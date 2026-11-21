import getpass
import os

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import DatabaseError, connection

from accounts.emails import send_staff_password_changed_email
from accounts.models import User
from core.security_log import log_event
from core.session_store import end_user_sessions

MAX_TRIES = 3
WRONG_SETTINGS = "Lệnh này phải chạy với --settings=bookstore.settings.migrate (tài khoản web không được đổi mật khẩu nhân viên)."


class Command(BaseCommand):
    help = "Đổi mật khẩu tài khoản nhân viên/quản trị. Chạy trên máy chủ: --settings=bookstore.settings.migrate"

    def add_arguments(self, parser):
        parser.add_argument("username", help="Tên đăng nhập của nhân viên")

    def _check_connection(self):
        web_accounts = {os.environ.get("DB_CUSTOMER_USER", "app_customer"), os.environ.get("DB_STAFF_USER", "app_staff")}
        if connection.settings_dict.get("USER") in web_accounts:
            raise CommandError(WRONG_SETTINGS)

    def _ask_password(self, user):
        for _ in range(MAX_TRIES):
            first = getpass.getpass("Mật khẩu mới: ")
            second = getpass.getpass("Nhập lại mật khẩu mới: ")
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
        raise CommandError(f"Nhập sai {MAX_TRIES} lần. Mật khẩu chưa được đổi.")

    def handle(self, *args, **options):
        self._check_connection()
        user = User.objects.filter(username=options["username"], is_staff=True).first()
        if user is None:
            raise CommandError("Không có tài khoản nhân viên với tên đăng nhập này.")

        password = self._ask_password(user)
        user.set_password(password)
        try:
            user.save(update_fields=["password"])
        except DatabaseError as exc:
            raise CommandError(WRONG_SETTINGS) from exc

        ended = end_user_sessions(user.pk)
        log_event("password_changed", user=user, username=user.get_username(), ip_address="cli",
                  detail={"via": "cli", "sessions_ended": ended})
        sent = send_staff_password_changed_email(user)

        self.stdout.write(self.style.SUCCESS(f"Đã đổi mật khẩu cho {user.get_username()}."))
        self.stdout.write(f"Đã đăng xuất {ended} phiên đang mở.")
        self.stdout.write("Đã gửi thư báo tới email của tài khoản." if sent else "Chưa gửi được thư báo (xem security.log).")
