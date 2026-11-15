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
