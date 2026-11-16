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
    ("default", "app_customer gọi sp_place_order (tham số sai, không ghi gì)", "CALL sp_place_order(0, NULL, NULL, NULL, NULL, @c, @n)", SIGNAL),
    ("default", "app_customer gọi sp_order_get (id sai, không đọc gì)", "CALL sp_order_get(0, NULL)", SIGNAL),
    ("default", "app_customer đọc orders_order", "SELECT id FROM orders_order LIMIT 1", 1142),
    ("default", "app_customer UPDATE thẳng orders_order", "UPDATE orders_order SET total = total WHERE 1 = 0", 1142),
    ("default", "app_customer INSERT thẳng orders_orderitem", "INSERT INTO orders_orderitem (order_id, book_id, book_title, unit_price, quantity) SELECT 1, 1, 'x', 1, 1 FROM DUAL WHERE 1 = 0", 1142),
    ("staff", "app_staff gọi sp_place_order", "CALL sp_place_order(0, NULL, NULL, NULL, NULL, @c, @n)", 1370),
    ("staff", "app_staff gọi sp_order_get", "CALL sp_order_get(0, NULL)", 1370),
    ("default", "app_customer gọi sp_order_cancel (id sai, không ghi gì)", "CALL sp_order_cancel(0, NULL)", SIGNAL),
    ("default", "app_customer gọi sp_cancel_expired_orders (chỉ Event được gọi)", "CALL sp_cancel_expired_orders(@n)", 1370),
    ("default", "app_customer gọi sp_order_expire_one (chỉ Event được gọi)", "CALL sp_order_expire_one(0, @d)", 1370),
    ("staff", "app_staff gọi sp_order_cancel", "CALL sp_order_cancel(0, NULL)", 1370),
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
    ("default", "app_customer gọi sp_payment_simulate (id sai, không ghi gì)", "CALL sp_payment_simulate(0, NULL, NULL, @t)", SIGNAL),
    ("staff", "app_staff gọi sp_payment_simulate", "CALL sp_payment_simulate(0, NULL, NULL, @t)", 1370),
    ("default", "app_customer đọc payments_payment", "SELECT id FROM payments_payment LIMIT 1", 1142),
    ("default", "app_customer INSERT thẳng payments_payment", "INSERT INTO payments_payment (order_id, provider, amount, status) SELECT 1, 'simulated', 1, 'failed' FROM DUAL WHERE 1 = 0", 1142),
    ("staff", "app_staff đọc payments_payment", "SELECT id FROM payments_payment LIMIT 1", 1142),
    ("default", "app_customer gọi sp_staff_security_events", "CALL sp_staff_security_events(0, NULL, NULL, NULL, NULL, NULL, 0, 50)", 1370),
    ("default", "app_customer đọc core_securityevent", "SELECT id FROM core_securityevent LIMIT 1", 1142),
    ("default", "app_customer gọi sp_purge_old_logs", "CALL sp_purge_old_logs(@n)", 1370),
    ("default", "app_customer đọc accounts_passwordhistory", "SELECT id FROM accounts_passwordhistory LIMIT 1", ALLOWED),
    ("default", "app_customer DELETE accounts_passwordhistory", "DELETE FROM accounts_passwordhistory WHERE 1 = 0", 1142),
    ("staff", "app_staff đổi email trong accounts_user", "UPDATE accounts_user SET email = email WHERE 1 = 0", 1143),
    ("default", "app_customer đọc core_auditlog", "SELECT id FROM core_auditlog LIMIT 1", 1142),
)


# AI-TRACE#116 | Claude Opus 5.5 | Lệnh kiểm tra phân quyền trên CSDL thật: chạy từng câu bằng app_customer/app_staff, so với kết quả mong đợi | CẤM XÓA CHÚ THÍCH NÀY
class Command(BaseCommand):
    help = "Kiểm tra phân quyền MySQL thật của app_customer và app_staff (chạy sau db_apply, không dùng settings.migrate)."

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
        users = {alias: connections[alias].settings_dict.get("USER") for alias in ("default", "staff")}
        if users["default"] == users["staff"]:
            raise CommandError("default và staff đang dùng cùng một tài khoản MySQL. Không chạy lệnh này với settings.migrate.")

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
