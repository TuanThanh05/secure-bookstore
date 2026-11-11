"""python manage.py db_setup – tạo CSDL, role và 4 tài khoản MySQL.

Chạy bằng tài khoản quản trị (root), MỘT LẦN khi dựng máy mới, và chạy lại mỗi
khi đổi mật khẩu trong .env / database/.env.db (lệnh sẽ đồng bộ mật khẩu).
Chạy lại nhiều lần không hỏng gì.

Việc nó làm:
  1. Tạo CSDL (utf8mb4) nếu chưa có.
  2. Cài component validate_password, đặt chính sách MEDIUM, tối thiểu 12 ký tự.
  3. Tạo role r_customer, r_staff (quyền cụ thể cấp sau, bằng db_apply).
  4. Tạo/cập nhật app_customer, app_staff, bookstore_migrate theo ĐỊA CHỈ MÀ
     MYSQL THẤY MÁY NÀY KẾT NỐI TỪ (Docker: 172.28.0.1, cài thường: 127.0.0.1
     hoặc localhost) và bookstore_definer (khóa đăng nhập).
"""
import secrets

import MySQLdb
from django.core.management.base import BaseCommand, CommandError

from core.dbadmin import admin_secret, connect_admin, db_settings, load_admin_env

COMPONENT = "file://component_validate_password"


class Command(BaseCommand):
    help = "Tạo CSDL, role và các tài khoản MySQL theo vai trò (cần quyền root)."
    requires_system_checks = []

    def add_arguments(self, parser):
        parser.add_argument("--root-user", default="root", help="Tài khoản quản trị MySQL (mặc định: root)")

    def handle(self, *args, **options):
        load_admin_env()
        default = db_settings()
        staff = self._staff_settings()
        db_name = default["NAME"]

        root_password = admin_secret("MYSQL_ROOT_PASSWORD", f"Mật khẩu MySQL của {options['root_user']}: ")
        migrate_password = admin_secret("DB_MIGRATE_PASSWORD")

        conn = connect_admin(options["root_user"], root_password)
        try:
            with conn.cursor() as cur:
                host = self._client_host(cur)
                self.stdout.write(f"MySQL thấy máy này kết nối từ: {host}")

                # 1. CSDL
                cur.execute(
                    f"CREATE DATABASE IF NOT EXISTS `{db_name}` "
                    "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
                )

                # 2. bookstore_definer trước: chủ sở hữu trigger/view/thủ tục, khóa đăng nhập.
                #    Mật khẩu ngẫu nhiên, không lưu ở đâu (không ai cần đăng nhập bằng nó).
                if not self._user_exists(cur, "bookstore_definer", "localhost"):
                    cur.execute(
                        "CREATE USER 'bookstore_definer'@'localhost' IDENTIFIED BY %s ACCOUNT LOCK",
                        (secrets.token_urlsafe(32) + "-Aa9",),
                    )

                # 3. Chính sách mật khẩu (chương 5, lỗ hổng 1)
                cur.execute("SELECT COUNT(*) FROM mysql.component WHERE component_urn = %s", (COMPONENT,))
                if cur.fetchone()[0] == 0:
                    cur.execute(f"INSTALL COMPONENT '{COMPONENT}'")
                cur.execute("SET PERSIST validate_password.policy = 'MEDIUM'")
                cur.execute("SET PERSIST validate_password.length = 12")

                # 4. Role
                cur.execute("CREATE ROLE IF NOT EXISTS 'r_customer', 'r_staff'")

                # 5. Tài khoản ứng dụng và tài khoản migrate
                self._upsert_user(cur, default["USER"], host, default["PASSWORD"], 50, "DB_CUSTOMER_PASSWORD")
                self._grant_role(cur, "r_customer", default["USER"], host)

                self._upsert_user(cur, staff["USER"], host, staff["PASSWORD"], 20, "DB_STAFF_PASSWORD")
                self._grant_role(cur, "r_staff", staff["USER"], host)

                self._upsert_user(cur, "bookstore_migrate", host, migrate_password, 5, "DB_MIGRATE_PASSWORD")
                # Chỉ tạo/sửa BẢNG. Không FILE, SUPER, PROCESS, GRANT OPTION, không tạo trigger/thủ tục.
                cur.execute(
                    "GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, DROP, ALTER, INDEX, REFERENCES "
                    f"ON `{self._grant_pattern(db_name)}`.* TO %s@%s",
                    ("bookstore_migrate", host),
                )
                # CSDL tạm test_<tên> do "manage.py test" tạo rồi xóa
                cur.execute(
                    f"GRANT ALL PRIVILEGES ON `{self._grant_pattern('test_' + db_name)}`.* TO %s@%s",
                    ("bookstore_migrate", host),
                )

                self._warn_other_hosts(cur, [default["USER"], staff["USER"], "bookstore_migrate"], host)
        finally:
            conn.close()

        self.stdout.write(self.style.SUCCESS(
            f"Xong: CSDL `{db_name}`, role r_customer/r_staff, tài khoản "
            f"{default['USER']}, {staff['USER']}, bookstore_migrate @ {host}, bookstore_definer (khóa)."
        ))
        self.stdout.write("Tiếp theo: python manage.py migrate --settings=bookstore.settings.migrate")

    # ------------------------------------------------------------------
    def _staff_settings(self):
        from django.conf import settings

        staff = settings.DATABASES.get("staff")
        if not staff:
            raise CommandError("Thiếu kết nối DATABASES['staff'] trong settings.")
        return staff

    def _client_host(self, cur):
        cur.execute("SELECT SUBSTRING_INDEX(USER(), '@', -1)")
        return cur.fetchone()[0]

    def _user_exists(self, cur, user, host):
        cur.execute("SELECT COUNT(*) FROM mysql.user WHERE user = %s AND host = %s", (user, host))
        return cur.fetchone()[0] > 0

    def _upsert_user(self, cur, user, host, password, max_conn, env_name):
        """Tạo tài khoản, hoặc đồng bộ lại mật khẩu nếu đã có.

        Tên, host, mật khẩu đi qua tham số của MySQLdb (được escape), không nối chuỗi.
        """
        verb = "ALTER" if self._user_exists(cur, user, host) else "CREATE"
        try:
            cur.execute(
                f"{verb} USER %s@%s IDENTIFIED BY %s WITH MAX_USER_CONNECTIONS {int(max_conn)}",
                (user, host, password),
            )
        except MySQLdb.OperationalError as exc:
            if exc.args and exc.args[0] == 1819:
                raise CommandError(
                    f"Mật khẩu {env_name} quá yếu: cần ≥ 12 ký tự, có chữ hoa, chữ thường, "
                    "số và ký tự đặc biệt."
                ) from exc
            raise

    def _grant_role(self, cur, role, user, host):
        cur.execute(f"GRANT '{role}' TO %s@%s", (user, host))
        cur.execute("SET DEFAULT ROLE ALL TO %s@%s", (user, host))

    def _grant_pattern(self, db_name):
        # Trong GRANT, "_" là ký tự đại diện (khớp 1 ký tự bất kỳ) → phải escape
        return db_name.replace("_", r"\_")

    def _warn_other_hosts(self, cur, users, host):
        cur.execute(
            "SELECT user, host FROM mysql.user WHERE user IN (%s, %s, %s) AND host <> %s",
            (*users, host),
        )
        for user, other in cur.fetchall():
            self.stdout.write(self.style.WARNING(
                f"Lưu ý: còn tài khoản cũ {user}@{other} (từ lần chạy khác). "
                f"Không dùng nữa thì xóa: DROP USER '{user}'@'{other}';"
            ))
