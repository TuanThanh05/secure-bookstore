"""Hàm dùng chung cho 2 lệnh quản trị CSDL: db_setup và db_apply.

Hai lệnh này đăng nhập MySQL bằng root (hoặc tài khoản quản trị khác) để tạo
tài khoản, trigger, cấp quyền. Chúng chạy giống nhau trên Docker (Arch) lẫn
MySQL cài thường (Windows), vì chỉ cần kết nối TCP tới DB_HOST:DB_PORT.

Mật khẩu quản trị lấy theo thứ tự: biến môi trường → database/.env.db → hỏi
trực tiếp (không hiện ký tự). Không bao giờ in mật khẩu ra màn hình.
"""
import getpass
import os
import re
from pathlib import Path

import environ
import MySQLdb
from django.conf import settings
from django.core.management.base import CommandError

MIN_MYSQL_VERSION = (8, 4)
ADMIN_ENV_FILE = Path(settings.REPO_DIR) / "database" / ".env.db"
SAFE_DB_NAME = re.compile(r"^[A-Za-z0-9_]{1,64}$")


def load_admin_env():
    """Nạp database/.env.db vào biến môi trường của tiến trình này (không ghi đè)."""
    if ADMIN_ENV_FILE.exists():
        environ.Env.read_env(ADMIN_ENV_FILE, overwrite=False)


def admin_secret(name, prompt=None):
    """Lấy một mật khẩu quản trị. Thiếu mà có prompt thì hỏi, không thì báo lỗi."""
    value = os.environ.get(name, "")
    if value:
        return value
    if prompt:
        value = getpass.getpass(prompt)
        if value:
            return value
    raise CommandError(f"Thiếu {name}: điền vào {ADMIN_ENV_FILE} (xem database/.env.db.example).")


def db_settings():
    """Thông tin kết nối lấy từ DATABASES["default"] (đọc từ .env)."""
    default = settings.DATABASES.get("default") or {}
    if default.get("ENGINE") != "django.db.backends.mysql":
        raise CommandError("DATABASES['default'] chưa cấu hình MySQL (xem settings/base.py).")
    name = default["NAME"]
    if not SAFE_DB_NAME.match(name):
        raise CommandError("DB_NAME chỉ được gồm chữ, số và dấu gạch dưới.")
    return default


def connect_admin(root_user, password, database=None):
    """Kết nối MySQL bằng tài khoản quản trị, cùng chế độ TLS với Django."""
    default = db_settings()
    options = default.get("OPTIONS", {})
    kwargs = {
        "host": default["HOST"],
        "port": int(default["PORT"]),
        "user": root_user,
        "password": password,
        "charset": "utf8mb4",
    }
    if database:
        kwargs["database"] = database
    if options.get("ssl_mode"):
        kwargs["ssl_mode"] = options["ssl_mode"]
    try:
        conn = MySQLdb.connect(**kwargs)
    except MySQLdb.OperationalError as exc:
        code = exc.args[0] if exc.args else None
        hint = {
            2002: "Không kết nối được. MySQL đã bật chưa? (Docker: docker compose ps)",
            2003: "Không kết nối được. MySQL đã bật chưa? (Docker: docker compose ps)",
            1045: "Sai tài khoản/mật khẩu quản trị, hoặc tài khoản không được đăng nhập từ máy này.",
            1049: "Chưa có CSDL. Chạy python manage.py db_setup trước.",
        }.get(code, "")
        raise CommandError(f"Lỗi kết nối MySQL {exc.args}. {hint}") from exc
    check_version(conn)
    return conn


def check_version(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT VERSION()")
        version = cur.fetchone()[0]
    numbers = tuple(int(x) for x in re.findall(r"\d+", version)[:2])
    if numbers < MIN_MYSQL_VERSION:
        raise CommandError(
            f"MySQL {version} quá cũ: Django 6.1 cần MySQL 8.4 trở lên. "
            "Không dùng XAMPP (là MariaDB)."
        )


def split_sql(text):
    """Tách file SQL thành từng câu lệnh, hiểu lệnh DELIMITER như client mysql.

    Bỏ qua câu chỉ có chú thích. Dùng cho database/objects/ và database/grants/.
    """
    delimiter = ";"
    statements, buffer = [], []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.upper().startswith("DELIMITER "):
            delimiter = stripped.split(None, 1)[1]
            continue
        buffer.append(line)
        if stripped.endswith(delimiter):
            statement = "\n".join(buffer).rstrip()
            statement = statement[: len(statement) - len(delimiter)]
            buffer = []
            if _has_code(statement):
                statements.append(statement.strip())
    if _has_code("\n".join(buffer)):
        raise CommandError("File SQL kết thúc mà câu lệnh cuối chưa có dấu kết thúc.")
    return statements


def _has_code(sql):
    lines = (line.strip() for line in sql.splitlines())
    return any(line and not line.startswith("--") for line in lines)
