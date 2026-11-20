from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import DatabaseError, connections

ALLOWED = "được phép"
SIGNAL = 1644

CHECKS = (
    ("staff", "app_staff gọi sp_category_list", "CALL sp_category_list()", ALLOWED),
    ("default", "app_customer gọi sp_category_list", "CALL sp_category_list()", 1370),
    ("staff", "app_staff gọi sp_category_create (đầu vào sai, không ghi gì)", "CALL sp_category_create(0, '', 'x', @o)", SIGNAL),
    ("default", "app_customer gọi sp_category_create", "CALL sp_category_create(0, '', 'x', @o)", 1370),
    ("default", "app_customer gọi sp_category_delete", "CALL sp_category_delete(0, 0)", 1370),
    ("staff", "app_staff INSERT thẳng catalog_category", "INSERT INTO catalog_category (name, slug) SELECT 'x', 'x' FROM DUAL WHERE 1 = 0", 1142),
    ("staff", "app_staff DELETE thẳng catalog_category", "DELETE FROM catalog_category WHERE 1 = 0", 1142),
    ("default", "app_customer đọc catalog_category", "SELECT id FROM catalog_category LIMIT 1", 1142),
    ("staff", "app_staff đọc v_staff_books (có giá nhập, tồn kho)", "SELECT id, cost_price, stock FROM v_staff_books LIMIT 1", ALLOWED),
    ("default", "app_customer đọc v_staff_books", "SELECT id FROM v_staff_books LIMIT 1", 1142),
    ("staff", "app_staff gọi sp_book_restock (số lượng sai, không ghi gì)", "CALL sp_book_restock(0, 0, 0, @o)", SIGNAL),
    ("default", "app_customer gọi sp_book_restock", "CALL sp_book_restock(0, 0, 0, @o)", 1370),
    ("default", "app_customer gọi sp_book_delete", "CALL sp_book_delete(0, 0)", 1370),
    ("staff", "app_staff UPDATE thẳng catalog_book", "UPDATE catalog_book SET stock = stock WHERE 1 = 0", 1142),
    ("default", "app_customer đọc catalog_book", "SELECT id FROM catalog_book LIMIT 1", 1142),
    ("default", "app_customer gọi sp_public_category_list", "CALL sp_public_category_list()", ALLOWED),
    ("default", "app_customer gọi sp_public_book_list", "CALL sp_public_book_list(NULL, NULL)", ALLOWED),
    ("default", "app_customer gọi sp_public_book_list (thể loại sai)", "CALL sp_public_book_list(-1, NULL)", SIGNAL),
    ("default", "app_customer đọc catalog_review", "SELECT id FROM catalog_review LIMIT 1", 1142),
    ("default", "app_customer gọi sp_review_save (đầu vào sai, không ghi gì)", "CALL sp_review_save(0, 0, 0, '', @o)", SIGNAL),
    ("default", "app_customer gọi sp_review_get_mine", "CALL sp_review_get_mine(1, 1)", ALLOWED),
    ("default", "app_customer gọi sp_review_can_write", "CALL sp_review_can_write(1, 1)", ALLOWED),
    ("staff", "app_staff gọi sp_review_can_write", "CALL sp_review_can_write(1, 1)", 1370),
    ("default", "app_customer INSERT thẳng catalog_review", "INSERT INTO catalog_review (user_id, book_id, rating, content) SELECT 1, 1, 5, 'x' FROM DUAL WHERE 1 = 0", 1142),
    ("staff", "app_staff gọi sp_review_save", "CALL sp_review_save(0, 0, 0, '', @o)", 1370),
    ("default", "app_customer gọi sp_public_book_get", "CALL sp_public_book_get(1)", ALLOWED),
    ("default", "app_customer gọi sp_review_list", "CALL sp_review_list(1)", ALLOWED),
    ("default", "app_customer gọi sp_cart_add (số lượng sai, không ghi gì)", "CALL sp_cart_add(0, 0, 0, @o)", SIGNAL),
    ("default", "app_customer đọc orders_cartitem", "SELECT id FROM orders_cartitem LIMIT 1", 1142),
    ("default", "app_customer INSERT thẳng orders_cartitem", "INSERT INTO orders_cartitem (cart_id, book_id, quantity) SELECT 1, 1, 1 FROM DUAL WHERE 1 = 0", 1142),
    ("staff", "app_staff gọi sp_cart_add", "CALL sp_cart_add(0, 0, 0, @o)", 1370),
    ("default", "app_customer gọi sp_cart_list (id sai, không đọc gì)", "CALL sp_cart_list(0)", SIGNAL),
    ("default", "app_customer gọi sp_cart_set_quantity (số lượng sai, không ghi gì)", "CALL sp_cart_set_quantity(0, 0, 0)", SIGNAL),
    ("default", "app_customer gọi sp_cart_remove (id sai, không ghi gì)", "CALL sp_cart_remove(0, 0)", SIGNAL),
    ("default", "app_customer DELETE thẳng orders_cartitem", "DELETE FROM orders_cartitem WHERE 1 = 0", 1142),
    ("staff", "app_staff gọi sp_cart_list", "CALL sp_cart_list(0)", 1370),
    ("staff", "app_staff gọi sp_cart_remove", "CALL sp_cart_remove(0, 0)", 1370),
    ("default", "app_customer gọi sp_place_order (tham số sai, không ghi gì)", "CALL sp_place_order(0, NULL, NULL, NULL, NULL, 5, 20, @c, @n)", SIGNAL),
    ("default", "app_customer gọi sp_order_get (id sai, không đọc gì)", "CALL sp_order_get(0, NULL)", SIGNAL),
    ("default", "app_customer đọc orders_order", "SELECT id FROM orders_order LIMIT 1", 1142),
    ("default", "app_customer UPDATE thẳng orders_order", "UPDATE orders_order SET total = total WHERE 1 = 0", 1142),
    ("default", "app_customer INSERT thẳng orders_orderitem", "INSERT INTO orders_orderitem (order_id, book_id, book_title, unit_price, quantity) SELECT 1, 1, 'x', 1, 1 FROM DUAL WHERE 1 = 0", 1142),
    ("staff", "app_staff gọi sp_place_order", "CALL sp_place_order(0, NULL, NULL, NULL, NULL, 5, 20, @c, @n)", 1370),
    ("staff", "app_staff gọi sp_order_get", "CALL sp_order_get(0, NULL)", 1370),
    ("default", "app_customer gọi sp_order_cancel (id sai, không ghi gì)", "CALL sp_order_cancel(0, NULL, @l)", SIGNAL),
    ("default", "app_customer gọi sp_cancel_expired_orders (chỉ Event được gọi)", "CALL sp_cancel_expired_orders(@n)", 1370),
    ("default", "app_customer gọi sp_order_expire_one (chỉ Event được gọi)", "CALL sp_order_expire_one(0, @d)", 1370),
    ("staff", "app_staff gọi sp_order_cancel", "CALL sp_order_cancel(0, NULL, @l)", 1370),
    ("staff", "app_staff gọi sp_cancel_expired_orders", "CALL sp_cancel_expired_orders(@n)", 1370),
    ("staff", "app_staff gọi sp_staff_account_list (id sai, không đọc gì)", "CALL sp_staff_account_list(0, NULL, NULL, 5, 15)", SIGNAL),
    ("staff", "app_staff gọi sp_staff_account_lock (lý do sai, không ghi gì)", "CALL sp_staff_account_lock(0, 0, '')", SIGNAL),
    ("staff", "app_staff UPDATE thẳng is_active", "UPDATE accounts_user SET is_active = is_active WHERE 1 = 0", 1143),
    ("default", "app_customer gọi sp_staff_account_list", "CALL sp_staff_account_list(0, NULL, NULL, 5, 15)", 1370),
    ("default", "app_customer gọi sp_staff_account_get", "CALL sp_staff_account_get(0, 0, 5, 15)", 1370),
    ("default", "app_customer gọi sp_staff_account_lock", "CALL sp_staff_account_lock(0, 0, '')", 1370),
    ("default", "app_customer gọi sp_staff_account_unlock", "CALL sp_staff_account_unlock(0, 0, '')", 1370),
    ("staff", "app_staff gọi sp_staff_security_events (id sai, không đọc gì)", "CALL sp_staff_security_events(0, NULL, NULL, NULL, NULL, NULL, 0, 50)", SIGNAL),
    ("staff", "app_staff gọi sp_staff_audit_log (id sai, không đọc gì)", "CALL sp_staff_audit_log(0, NULL, NULL, NULL, NULL, NULL, 0, 50)", SIGNAL),
    ("staff", "app_staff đọc thẳng core_securityevent", "SELECT id FROM core_securityevent LIMIT 1", 1142),
    ("staff", "app_staff xóa core_auditlog", "DELETE FROM core_auditlog WHERE 1 = 0", 1142),
    ("staff", "app_staff gọi sp_purge_old_logs (chỉ Event được gọi)", "CALL sp_purge_old_logs(@n)", 1370),
    ("default", f"app_customer gọi sp_payment_simulate khi PAYMENT_SIMULATION={settings.PAYMENT_SIMULATION} (id sai, không ghi gì)",
     "CALL sp_payment_simulate(0, NULL, NULL, @t)", SIGNAL if settings.PAYMENT_SIMULATION else 1370),
    ("staff", "app_staff gọi sp_payment_simulate", "CALL sp_payment_simulate(0, NULL, NULL, @t)", 1370),
    ("default", "app_customer đọc payments_payment", "SELECT id FROM payments_payment LIMIT 1", 1142),
    ("default", "app_customer INSERT thẳng payments_payment", "INSERT INTO payments_payment (order_id, provider, amount, status) SELECT 1, 'simulated', 1, 'failed' FROM DUAL WHERE 1 = 0", 1142),
    ("staff", "app_staff đọc payments_payment", "SELECT id FROM payments_payment LIMIT 1", 1142),
    ("default", "app_customer gọi sp_order_list_mine (id sai, không đọc gì)", "CALL sp_order_list_mine(0, 'active', 0, 10)", SIGNAL),
    ("staff", "app_staff gọi sp_order_list_mine", "CALL sp_order_list_mine(0, 'active', 0, 10)", 1370),
    ("staff", "app_staff gọi sp_staff_order_list (id sai, không đọc gì)", "CALL sp_staff_order_list(0, NULL, 0, 10)", SIGNAL),
    ("staff", "app_staff gọi sp_staff_order_get (id sai, không đọc gì)", "CALL sp_staff_order_get(0, NULL)", SIGNAL),
    ("staff", "app_staff gọi sp_staff_order_confirm (id sai, không ghi gì)", "CALL sp_staff_order_confirm(0, NULL)", SIGNAL),
    ("staff", "app_staff gọi sp_staff_order_advance (thủ tục nội bộ)", "CALL sp_staff_order_advance(0, NULL, 'paid', 'confirmed')", 1370),
    ("staff", "app_staff UPDATE thẳng orders_order", "UPDATE orders_order SET status = status WHERE 1 = 0", 1142),
    ("default", "app_customer gọi sp_staff_order_list", "CALL sp_staff_order_list(0, NULL, 0, 10)", 1370),
    ("default", "app_customer gọi sp_staff_order_deliver", "CALL sp_staff_order_deliver(0, NULL)", 1370),
    ("staff", "app_staff gọi sp_staff_dashboard_orders (id sai, không đọc gì)", "CALL sp_staff_dashboard_orders(0, UTC_TIMESTAMP(), UTC_TIMESTAMP(), UTC_TIMESTAMP())", SIGNAL),
    ("staff", "app_staff gọi sp_staff_dashboard_stock (id sai, không đọc gì)", "CALL sp_staff_dashboard_stock(0, 10)", SIGNAL),
    ("staff", "app_staff gọi sp_staff_dashboard_security (id sai, không đọc gì)", "CALL sp_staff_dashboard_security(0, UTC_TIMESTAMP())", SIGNAL),
    ("default", "app_customer gọi sp_staff_dashboard_orders", "CALL sp_staff_dashboard_orders(0, UTC_TIMESTAMP(), UTC_TIMESTAMP(), UTC_TIMESTAMP())", 1370),
    ("default", "app_customer gọi sp_staff_dashboard_security", "CALL sp_staff_dashboard_security(0, UTC_TIMESTAMP())", 1370),
    ("default", "app_customer gọi sp_staff_security_events", "CALL sp_staff_security_events(0, NULL, NULL, NULL, NULL, NULL, 0, 50)", 1370),
    ("default", "app_customer đọc core_securityevent", "SELECT id FROM core_securityevent LIMIT 1", 1142),
    ("default", "app_customer gọi sp_purge_old_logs", "CALL sp_purge_old_logs(@n)", 1370),
    ("default", "app_customer đọc accounts_passwordhistory", "SELECT id FROM accounts_passwordhistory LIMIT 1", ALLOWED),
    ("default", "app_customer DELETE accounts_passwordhistory", "DELETE FROM accounts_passwordhistory WHERE 1 = 0", 1142),
    ("staff", "app_staff đổi email trong accounts_user", "UPDATE accounts_user SET email = email WHERE 1 = 0", 1143),
    ("default", "app_customer đọc core_auditlog", "SELECT id FROM core_auditlog LIMIT 1", 1142),
    ("default", "app_customer đọc django_session (lấy cookie admin)", "SELECT session_key FROM django_session LIMIT 1", 1142),
    ("default", "app_customer sửa django_session", "UPDATE django_session SET expire_date = expire_date WHERE 1 = 0", 1142),
    ("default", "app_customer xóa django_session", "DELETE FROM django_session WHERE 1 = 0", 1142),
    ("staff", "app_staff đọc django_session", "SELECT session_key FROM django_session LIMIT 1", 1142),
    ("session", "app_session đọc django_session", "SELECT session_key FROM django_session LIMIT 1", ALLOWED),
    ("session", "app_session thêm/sửa/xóa django_session (không đổi gì)", "UPDATE django_session SET expire_date = expire_date WHERE 1 = 0", ALLOWED),
    ("session", "app_session đọc accounts_user", "SELECT id FROM accounts_user LIMIT 1", 1142),
    ("session", "app_session đọc core_securityevent", "SELECT id FROM core_securityevent LIMIT 1", 1142),
    ("session", "app_session gọi sp_category_list", "CALL sp_category_list()", 1370),
    ("default", "app_customer đọc accounts_user (đăng nhập)", "SELECT id, password FROM accounts_user LIMIT 1", ALLOWED),
    ("default", "app_customer tạo tài khoản", "INSERT INTO accounts_user (username) SELECT username FROM accounts_user WHERE 1 = 0", 1142),
    ("default", "app_customer tự mở khóa (is_active)", "UPDATE accounts_user SET is_active = is_active WHERE 1 = 0", 1142),
    ("default", "app_customer đổi mật khẩu", "UPDATE accounts_user SET password = password WHERE 1 = 0", 1142),
    ("auth", "app_auth đọc accounts_user", "SELECT id, password FROM accounts_user LIMIT 1", ALLOWED),
    ("auth", "app_auth tạo tài khoản (không ghi dòng nào)", "INSERT INTO accounts_user (username) SELECT username FROM accounts_user WHERE 1 = 0", ALLOWED),
    ("auth", "app_auth đổi mật khẩu (không đổi dòng nào)", "UPDATE accounts_user SET password = password WHERE 1 = 0", ALLOWED),
    ("auth", "app_auth xóa tài khoản", "DELETE FROM accounts_user WHERE 1 = 0", 1142),
    ("auth", "app_auth đọc catalog_book", "SELECT id FROM catalog_book LIMIT 1", 1142),
    ("auth", "app_auth đọc django_session", "SELECT session_key FROM django_session LIMIT 1", 1142),
    ("auth", "app_auth sửa accounts_passwordhistory", "DELETE FROM accounts_passwordhistory WHERE 1 = 0", 1142),
    ("auth", "app_auth gọi sp_category_list", "CALL sp_category_list()", 1370),
    ("default", "app_customer đọc chuỗi bí mật 2 bước", "SELECT secret_encrypted FROM accounts_totpdevice LIMIT 1", 1142),
    ("default", "app_customer đọc mã dự phòng", "SELECT code_hash FROM accounts_recoverycode LIMIT 1", 1142),
    ("default", "app_customer xóa thiết bị 2 bước", "DELETE FROM accounts_totpdevice WHERE 1 = 0", 1142),
    ("staff", "app_staff đọc chuỗi bí mật 2 bước", "SELECT secret_encrypted FROM accounts_totpdevice LIMIT 1", 1142),
    ("session", "app_session đọc chuỗi bí mật 2 bước", "SELECT secret_encrypted FROM accounts_totpdevice LIMIT 1", 1142),
    ("auth", "app_auth đọc thiết bị 2 bước", "SELECT id, secret_encrypted FROM accounts_totpdevice LIMIT 1", ALLOWED),
    ("auth", "app_auth ghi bước thời gian (không đổi dòng nào)", "UPDATE accounts_totpdevice SET last_used_step = last_used_step WHERE 1 = 0", ALLOWED),
    ("auth", "app_auth đọc mã dự phòng", "SELECT id FROM accounts_recoverycode LIMIT 1", ALLOWED),
    ("default", "app_customer đọc bảng khóa đăng nhập axes", "SELECT id FROM axes_accessattempt LIMIT 1", 1142),
    ("default", "app_customer xóa trạng thái khóa đăng nhập (axes)", "DELETE FROM axes_accessattempt WHERE 1 = 0", 1142),
    ("default", "app_customer xóa hạn khóa axes", "DELETE FROM axes_accessattemptexpiration WHERE 1 = 0", 1142),
    ("default", "app_customer ghi axes_accesslog", "UPDATE axes_accesslog SET logout_time = logout_time WHERE 1 = 0", 1142),
    ("staff", "app_staff xóa trạng thái khóa đăng nhập (axes)", "DELETE FROM axes_accessattempt WHERE 1 = 0", 1142),
    ("session", "app_session đọc bảng khóa đăng nhập axes", "SELECT id FROM axes_accessattempt LIMIT 1", 1142),
    ("auth", "app_auth đọc bảng khóa đăng nhập axes", "SELECT id FROM axes_accessattempt LIMIT 1", ALLOWED),
    ("auth", "app_auth xóa trạng thái khóa (không xóa dòng nào)", "DELETE FROM axes_accessattempt WHERE 1 = 0", ALLOWED),
    ("auth", "app_auth xóa hạn khóa (không xóa dòng nào)", "DELETE FROM axes_accessattemptexpiration WHERE 1 = 0", ALLOWED),
    ("auth", "app_auth ghi axes_accesslog (không đổi dòng nào)", "UPDATE axes_accesslog SET logout_time = logout_time WHERE 1 = 0", ALLOWED),
    ("auth", "app_auth xóa axes_accesslog", "DELETE FROM axes_accesslog WHERE 1 = 0", 1142),
    ("auth", "app_auth gọi sp_payment_simulate", "CALL sp_payment_simulate(0, NULL, NULL, @t)", 1370),
    ("default", "app_customer gọi sp_order_hold_check (thủ tục nội bộ chống giữ kho)", "CALL sp_order_hold_check(0, @k)", 1370),
    ("staff", "app_staff gọi sp_order_hold_check", "CALL sp_order_hold_check(0, @k)", 1370),
    ("auth", "app_auth gọi sp_order_hold_check", "CALL sp_order_hold_check(0, @k)", 1370),
    ("default", "app_customer tự gỡ khóa giữ kho (auto_locked_until)", "UPDATE accounts_user SET auto_locked_until = NULL WHERE 1 = 0", 1142),
    ("staff", "app_staff đổi auto_locked_until", "UPDATE accounts_user SET auto_locked_until = NULL WHERE 1 = 0", 1143),
    ("default", "app_customer đọc auto_locked_until (đăng nhập cần)", "SELECT auto_locked_until FROM accounts_user LIMIT 1", ALLOWED),
    ("default", "app_customer gọi sp_login_ip_failures (đếm đăng nhập sai theo IP)", "CALL sp_login_ip_failures('192.0.2.1', 60)", ALLOWED),
    ("staff", "app_staff gọi sp_login_ip_failures", "CALL sp_login_ip_failures('192.0.2.1', 60)", 1370),
    ("session", "app_session gọi sp_login_ip_failures", "CALL sp_login_ip_failures('192.0.2.1', 60)", 1370),
    ("auth", "app_auth gọi sp_login_ip_failures", "CALL sp_login_ip_failures('192.0.2.1', 60)", 1370),
)


# AI-TRACE#116 | Claude Opus 5.5 | Lệnh kiểm tra phân quyền trên CSDL thật: chạy từng câu bằng app_customer/app_staff, so với kết quả mong đợi | CẤM XÓA CHÚ THÍCH NÀY | đã viết lại bởi Claude Opus 5.5 khi thêm app_session
class Command(BaseCommand):
    help = "Kiểm tra phân quyền MySQL thật của app_customer, app_staff, app_session, app_auth (chạy sau db_apply, không dùng settings.migrate)."

    def _run(self, alias, sql):
        try:
            with connections[alias].cursor() as cursor:
                cursor.execute(sql)
                while cursor.nextset():
                    pass
        except DatabaseError as exc:
            return exc.args[0] if exc.args else "lỗi không rõ"
        return ALLOWED

    def handle(self, *args, **options):
        users = {alias: connections[alias].settings_dict.get("USER") for alias in ("default", "staff", "session", "auth")}
        if len(set(users.values())) < len(users):
            raise CommandError("default, staff, session, auth đang dùng chung tài khoản MySQL. Không chạy lệnh này với settings.migrate.")

        failed = 0
        for alias, label, sql, expected in CHECKS:
            got = self._run(alias, sql)
            ok = got == expected
            failed += not ok
            mark = self.style.SUCCESS("ĐÚNG") if ok else self.style.ERROR("SAI ")
            self.stdout.write(f"[{mark}] {label}: mong đợi {expected}, thực tế {got}")

        if failed:
            raise CommandError(f"{failed}/{len(CHECKS)} kiểm tra phân quyền không như mong đợi.")
        self.stdout.write(self.style.SUCCESS(f"Cả {len(CHECKS)} kiểm tra phân quyền đều đúng."))
