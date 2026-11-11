"""Cấu hình CHỈ dùng cho lệnh cần quyền tạo/sửa bảng.

Đổi tài khoản của cả 2 kết nối sang bookstore_migrate. Mật khẩu lấy từ biến
môi trường DB_MIGRATE_PASSWORD hoặc file database/.env.db (không nằm trong .env,
nên web lúc chạy không biết mật khẩu này).

    python manage.py migrate         --settings=bookstore.settings.migrate
    python manage.py createsuperuser --settings=bookstore.settings.migrate
    python manage.py test            --settings=bookstore.settings.migrate

Không bao giờ chạy runserver/gunicorn bằng file này.
"""
import os

import environ
from django.core.exceptions import ImproperlyConfigured

from .dev import *  # noqa: F401,F403
from .dev import DATABASES, REPO_DIR

_admin_env = REPO_DIR / "database" / ".env.db"
if _admin_env.exists():
    environ.Env.read_env(_admin_env, overwrite=False)

if not os.environ.get("DB_MIGRATE_PASSWORD"):
    raise ImproperlyConfigured(
        "Thiếu DB_MIGRATE_PASSWORD: điền vào database/.env.db (xem database/.env.db.example)."
    )

_migrate_account = {
    "USER": os.environ.get("DB_MIGRATE_USER", "bookstore_migrate"),
    "PASSWORD": os.environ["DB_MIGRATE_PASSWORD"],
    "CONN_MAX_AGE": 0,
}
DATABASES["default"] = {**DATABASES["default"], **_migrate_account}
# "staff" cũng dùng tài khoản migrate: khi chạy test, "staff" trỏ vào CSDL tạm
# test_bookstore (TEST MIRROR) mà app_staff không có quyền vào.
DATABASES["staff"] = {**DATABASES["staff"], **_migrate_account}
