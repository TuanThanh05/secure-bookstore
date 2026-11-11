"""python manage.py db_apply – tạo trigger/view/thủ tục rồi cấp quyền.

Chạy bằng tài khoản quản trị (root), SAU khi `migrate` đã tạo bảng
(MySQL không cho cấp quyền hay tạo trigger trên bảng chưa có).
Chạy lại mỗi khi thêm/sửa file trong database/objects/ hoặc database/grants/.

Thứ tự: database/objects/*.sql rồi database/grants/*.sql, mỗi thư mục theo tên
file (vì vậy tên bắt đầu bằng số: 10_, 20_, 30_...). File được dùng DELIMITER.
Mỗi file object tự DROP ... IF EXISTS trước khi tạo, nên chạy lại không lỗi.

Vì sao root làm việc này mà không phải migrate: khi MySQL bật binlog, tạo
trigger/thủ tục cần quyền SUPER (hoặc nới lỏng log_bin_trust_function_creators).
Nhóm không cấp quyền đó cho tài khoản migrate.
"""
from pathlib import Path

import MySQLdb
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from core.dbadmin import admin_secret, connect_admin, db_settings, load_admin_env, split_sql

FOLDERS = ("objects", "grants")


class Command(BaseCommand):
    help = "Chạy database/objects/*.sql rồi database/grants/*.sql bằng tài khoản quản trị."
    requires_system_checks = []

    def add_arguments(self, parser):
        parser.add_argument("--root-user", default="root", help="Tài khoản quản trị MySQL (mặc định: root)")

    def handle(self, *args, **options):
        load_admin_env()
        db_name = db_settings()["NAME"]
        password = admin_secret("MYSQL_ROOT_PASSWORD", f"Mật khẩu MySQL của {options['root_user']}: ")

        base = Path(settings.REPO_DIR) / "database"
        files = [f for folder in FOLDERS for f in sorted((base / folder).glob("*.sql"))]
        if not files:
            raise CommandError(f"Không có file .sql nào trong {base}/objects hoặc {base}/grants.")

        conn = connect_admin(options["root_user"], password, database=db_name)
        try:
            with conn.cursor() as cur:
                for path in files:
                    statements = split_sql(path.read_text(encoding="utf-8"))
                    for number, sql in enumerate(statements, start=1):
                        try:
                            cur.execute(sql)  # không truyền tham số: MySQLdb không đụng tới dấu %
                        except MySQLdb.Error as exc:
                            raise CommandError(
                                f"{path.relative_to(base.parent)}, câu lệnh thứ {number}: {exc.args}"
                            ) from exc
                    self.stdout.write(f"  ✓ {path.relative_to(base.parent)} ({len(statements)} câu lệnh)")
        finally:
            conn.close()

        self.stdout.write(self.style.SUCCESS("Xong: đã tạo trigger/view/thủ tục và cấp quyền."))
