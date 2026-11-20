import os

from django.core.management.base import CommandError
from django.db import connection

from accounts import two_factor

MAX_CODE_TRIES = 3
WRONG_SETTINGS = ("Lệnh này phải chạy với --settings=bookstore.settings.migrate "
                  "(tài khoản web không được cài 2 bước cho quản trị viên).")


# AI-TRACE#504 | Claude Opus 5.5 | Lệnh 2 bước của admin chỉ chạy bằng tài khoản migrate, không bằng tài khoản web | CẤM XÓA CHÚ THÍCH NÀY
def check_connection():
    web_accounts = {
        os.environ.get("DB_CUSTOMER_USER", "app_customer"),
        os.environ.get("DB_STAFF_USER", "app_staff"),
        os.environ.get("DB_AUTH_USER", "app_auth"),
        os.environ.get("DB_SESSION_USER", "app_session"),
    }
    if connection.settings_dict.get("USER") in web_accounts:
        raise CommandError(WRONG_SETTINGS)


# AI-TRACE#505 | Claude Opus 5.5 | In mã QR ra terminal, hỏi mã 6 số để chắc admin đã quét đúng; sai 3 lần thì hủy (giao dịch quay lui) | CẤM XÓA CHÚ THÍCH NÀY
def enroll_in_terminal(command, user, ask=None):
    ask = ask or input
    device = two_factor.start_setup(user)
    if device is None:
        raise CommandError("Tài khoản này đã có thiết bị 2 bước.")
    secret = two_factor.setup_secret(device)
    command.stdout.write("Quét mã QR dưới đây bằng Google Authenticator trên điện thoại của quản trị viên:")
    command.stdout.write(two_factor.qr_terminal(two_factor.provisioning_uri(user, secret)))
    command.stdout.write(f"Không quét được thì nhập khóa thủ công: {two_factor.group_secret(secret)}")
    command.stdout.write("Không chụp màn hình, không lưu khóa này ở đâu khác ngoài ứng dụng.")
    for _ in range(MAX_CODE_TRIES):
        code = ask("Nhập mã 6 số đang hiện trong ứng dụng: ")
        if two_factor.confirm_setup(user, device, code, with_recovery=False) is not None:
            return
        command.stderr.write("Mã không đúng (kiểm tra giờ trên điện thoại và máy chủ).")
    raise CommandError(f"Nhập sai mã {MAX_CODE_TRIES} lần. Chưa cài xác thực 2 bước.")
