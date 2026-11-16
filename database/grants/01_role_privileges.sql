-- =====================================================================
-- Cấp quyền cho 2 vai trò r_customer, r_staff và cho bookstore_definer
-- (chương 6.2). Root chạy file này SAU khi `python manage.py migrate` đã
-- tạo bảng (MySQL không cho cấp quyền trên bảng chưa tồn tại), bằng:
--
--   python manage.py db_apply
--
-- Chạy lại nhiều lần không sao (GRANT trùng không báo lỗi).
-- Mỗi khi có bảng/view/thủ tục mới cần quyền: thêm vào file này rồi chạy lại.
--
-- Nguyên tắc:
--   - Bảng nghiệp vụ (catalog_*, orders_*, payments_*, core_auditlog):
--     KHÔNG cấp gì. Sau này chỉ cấp SELECT trên view và EXECUTE trên thủ tục.
--   - Bảng nội bộ của Django: cấp đúng mức Django cần để chạy.
--   - Không cấp DELETE trên accounts_user, không cấp gì trên bảng log ngoài INSERT.
-- =====================================================================

-- ---------------------------------------------------------------------
-- bookstore_definer: chủ sở hữu trigger/view/thủ tục (khóa đăng nhập)
-- Trigger chạy bằng quyền của definer: cần TRIGGER để chạy và SELECT để
-- đọc giá trị NEW./OLD. các cột.
-- ---------------------------------------------------------------------
GRANT SELECT, TRIGGER ON accounts_user TO 'bookstore_definer'@'localhost';

-- Trigger trg_pwhist_* (objects/11_...): thêm mã băm mới, đọc để tìm dòng
-- thứ 5, xóa các dòng cũ hơn. Chỉ definer có INSERT/DELETE trên bảng này.
GRANT SELECT, INSERT, DELETE ON accounts_passwordhistory TO 'bookstore_definer'@'localhost';

-- ---------------------------------------------------------------------
-- r_customer: kết nối "default" của Django (app_customer)
-- ---------------------------------------------------------------------

-- Django đọc khi khởi động và khi kiểm tra quyền
GRANT SELECT ON django_migrations              TO 'r_customer';
GRANT SELECT ON django_content_type            TO 'r_customer';
GRANT SELECT ON auth_permission                TO 'r_customer';
GRANT SELECT ON auth_group                     TO 'r_customer';
GRANT SELECT ON auth_group_permissions         TO 'r_customer';
-- Chỉ ĐỌC nhóm/quyền của user: khách không tự thêm mình vào nhóm nhân viên được
GRANT SELECT ON accounts_user_groups           TO 'r_customer';
GRANT SELECT ON accounts_user_user_permissions TO 'r_customer';

-- Đăng ký, đăng nhập, đổi mật khẩu. Trigger trg_user_guard_* chặn leo thang quyền.
GRANT SELECT, INSERT, UPDATE ON accounts_user  TO 'r_customer';

-- Lịch sử mật khẩu: chỉ ĐỌC để so sánh mật khẩu mới với 5 mã băm gần nhất.
-- Không cấp INSERT/UPDATE/DELETE: việc ghi do trigger làm, nên dù có lỗi
-- SQL injection, kẻ tấn công cũng không xóa được lịch sử để dùng lại mật khẩu cũ.
GRANT SELECT ON accounts_passwordhistory       TO 'r_customer';

-- Phiên đăng nhập (SESSION_ENGINE mặc định lưu trong CSDL)
GRANT SELECT, INSERT, UPDATE, DELETE ON django_session TO 'r_customer';

-- Nhật ký bảo mật: chỉ được ghi thêm, không đọc/sửa/xóa
GRANT INSERT ON core_securityevent             TO 'r_customer';
GRANT SELECT, INSERT, UPDATE, DELETE ON axes_accessattempt           TO 'r_customer';
GRANT SELECT, INSERT, UPDATE, DELETE ON axes_accessattemptexpiration TO 'r_customer';
GRANT SELECT, INSERT, UPDATE         ON axes_accesslog               TO 'r_customer';

-- ---------------------------------------------------------------------
-- r_staff: kết nối "staff" (app_staff), chỉ app dashboard dùng
-- Phần lớn quyền (thủ tục sp_category_*, sp_book_*...) thêm ở các bước sau.
-- ---------------------------------------------------------------------
GRANT INSERT ON core_securityevent             TO 'r_staff';

-- Nhân viên sửa họ, tên, SĐT của chính mình (dashboard:profile_update).
-- Quyền THEO CỘT: chỉ 3 cột được UPDATE, chỉ đọc được cột id (cho WHERE id = ...).
-- app_staff không đụng được password, email, is_staff, is_superuser.
-- Trigger trg_user_guard_update chặn thêm: app_staff chỉ sửa được dòng nhân viên.
GRANT SELECT (id), UPDATE (first_name, last_name, phone_encrypted) ON accounts_user TO 'r_staff';

-- ---------------------------------------------------------------------
-- sp_place_order (database/objects/30_sp_place_order.sql)
-- Definer đọc/ghi đúng các bảng thủ tục cần. Từ MySQL 8.0.22, câu khóa dòng
-- SELECT ... FOR UPDATE cần SELECT cộng thêm UPDATE hoặc DELETE trên bảng đó.
-- ---------------------------------------------------------------------
GRANT SELECT, UPDATE ON orders_cart      TO 'bookstore_definer'@'localhost';
GRANT SELECT, DELETE ON orders_cartitem  TO 'bookstore_definer'@'localhost';
GRANT SELECT, UPDATE ON catalog_book     TO 'bookstore_definer'@'localhost';   -- thêm INSERT, DELETE ở phần sách bên dưới
GRANT SELECT, INSERT ON orders_order     TO 'bookstore_definer'@'localhost';
GRANT INSERT         ON orders_orderitem TO 'bookstore_definer'@'localhost';

-- Thủ tục SQL SECURITY DEFINER: MySQL kiểm tra cả quyền EXECUTE của chính definer
GRANT EXECUTE ON PROCEDURE sp_place_order TO 'bookstore_definer'@'localhost';

-- Khách chỉ được gọi thủ tục, không có quyền nào trên các bảng trên
GRANT EXECUTE ON PROCEDURE sp_place_order TO 'r_customer';

-- Đặt hàng (2026-11-16): đọc đơn của chính khách + trigger khóa đơn
-- (database/objects/30_sp_place_order.sql, 32_trg_orders_guard.sql).
-- Definer: đọc chi tiết đơn cho sp_order_get; TRIGGER để chạy các trigger
-- khóa đơn (trigger chạy bằng quyền definer).
GRANT SELECT          ON orders_orderitem TO 'bookstore_definer'@'localhost';
GRANT TRIGGER         ON orders_order     TO 'bookstore_definer'@'localhost';
GRANT TRIGGER         ON orders_orderitem TO 'bookstore_definer'@'localhost';
GRANT EXECUTE ON PROCEDURE sp_order_get   TO 'bookstore_definer'@'localhost';
GRANT EXECUTE ON PROCEDURE sp_order_get   TO 'r_customer';

-- Hủy đơn và hủy đơn quá hạn (database/objects/33_order_cancel.sql).
-- Definer: đổi trạng thái đơn (trigger 32 vẫn chỉ cho pending → cancelled),
-- cộng lại kho (đã có UPDATE catalog_book), gọi thủ tục nội bộ; EVENT để
-- Event ev_cancel_expired_orders chạy bằng quyền definer.
-- r_customer: chỉ sp_order_cancel. sp_cancel_expired_orders, sp_order_expire_one
-- không cấp cho tài khoản ứng dụng nào (chỉ Event gọi).
GRANT UPDATE                                   ON orders_order TO 'bookstore_definer'@'localhost';
GRANT EVENT ON *                               TO 'bookstore_definer'@'localhost';
GRANT EXECUTE ON PROCEDURE sp_order_cancel          TO 'bookstore_definer'@'localhost';
GRANT EXECUTE ON PROCEDURE sp_order_expire_one      TO 'bookstore_definer'@'localhost';
GRANT EXECUTE ON PROCEDURE sp_cancel_expired_orders TO 'bookstore_definer'@'localhost';
GRANT EXECUTE ON PROCEDURE sp_order_cancel          TO 'r_customer';

-- ---------------------------------------------------------------------
-- Thể loại sách (database/objects/40_category.sql)
-- Definer: đọc/khóa/ghi catalog_category, đếm sách, ghi nhật ký.
-- r_staff: chỉ gọi bốn thủ tục; không có quyền nào trên bảng.
-- r_customer: không có gì ở đây.
-- ---------------------------------------------------------------------
GRANT SELECT, INSERT, UPDATE, DELETE ON catalog_category TO 'bookstore_definer'@'localhost';
GRANT INSERT ON core_auditlog                            TO 'bookstore_definer'@'localhost';

GRANT EXECUTE ON PROCEDURE sp_category_list   TO 'bookstore_definer'@'localhost';
GRANT EXECUTE ON PROCEDURE sp_category_create TO 'bookstore_definer'@'localhost';
GRANT EXECUTE ON PROCEDURE sp_category_rename TO 'bookstore_definer'@'localhost';
GRANT EXECUTE ON PROCEDURE sp_category_delete TO 'bookstore_definer'@'localhost';

GRANT EXECUTE ON PROCEDURE sp_category_list    TO 'r_staff';
GRANT EXECUTE ON PROCEDURE sp_category_create  TO 'r_staff';
GRANT EXECUTE ON PROCEDURE sp_category_rename  TO 'r_staff';
GRANT EXECUTE ON PROCEDURE sp_category_delete  TO 'r_staff';

-- ---------------------------------------------------------------------
-- Sách (database/objects/41_book.sql)
-- Definer: thêm/sửa/xóa catalog_book, đọc orders_orderitem để biết sách đã bán chưa.
-- r_staff: chỉ đọc view một bảng v_staff_books và gọi sáu thủ tục.
-- r_customer: không có gì ở đây (giá nhập, tồn kho chi tiết là của nhân viên).
-- ---------------------------------------------------------------------
GRANT INSERT, DELETE ON catalog_book     TO 'bookstore_definer'@'localhost';
GRANT SELECT ON orders_orderitem         TO 'bookstore_definer'@'localhost';

GRANT EXECUTE ON PROCEDURE sp_book_create       TO 'bookstore_definer'@'localhost';
GRANT EXECUTE ON PROCEDURE sp_book_update       TO 'bookstore_definer'@'localhost';
GRANT EXECUTE ON PROCEDURE sp_book_set_active   TO 'bookstore_definer'@'localhost';
GRANT EXECUTE ON PROCEDURE sp_book_restock      TO 'bookstore_definer'@'localhost';
GRANT EXECUTE ON PROCEDURE sp_book_reduce_stock TO 'bookstore_definer'@'localhost';
GRANT EXECUTE ON PROCEDURE sp_book_delete       TO 'bookstore_definer'@'localhost';

GRANT SELECT ON v_staff_books                   TO 'r_staff';
GRANT EXECUTE ON PROCEDURE sp_book_create       TO 'r_staff';
GRANT EXECUTE ON PROCEDURE sp_book_update       TO 'r_staff';
GRANT EXECUTE ON PROCEDURE sp_book_set_active   TO 'r_staff';
GRANT EXECUTE ON PROCEDURE sp_book_restock      TO 'r_staff';
GRANT EXECUTE ON PROCEDURE sp_book_reduce_stock TO 'r_staff';
GRANT EXECUTE ON PROCEDURE sp_book_delete       TO 'r_staff';

-- ---------------------------------------------------------------------
-- Danh mục sách cho khách (database/objects/20_public_catalog.sql)
-- Definer: đọc thêm catalog_review để tính điểm đánh giá.
-- r_customer: chỉ gọi hai thủ tục đọc; không có quyền nào trên catalog_*.
-- ---------------------------------------------------------------------
GRANT SELECT ON catalog_review                       TO 'bookstore_definer'@'localhost';

GRANT EXECUTE ON PROCEDURE sp_public_category_list   TO 'bookstore_definer'@'localhost';
GRANT EXECUTE ON PROCEDURE sp_public_book_list       TO 'bookstore_definer'@'localhost';

GRANT EXECUTE ON PROCEDURE sp_public_category_list   TO 'r_customer';
GRANT EXECUTE ON PROCEDURE sp_public_book_list       TO 'r_customer';

-- ---------------------------------------------------------------------
-- Đánh giá sách (database/objects/21_review.sql)
-- Definer: thêm/sửa catalog_review (đã có SELECT ở phần danh mục cho khách),
-- đọc accounts_user và catalog_book để kiểm tra (đã có).
-- r_customer: chỉ gọi hai thủ tục; không có quyền ghi nào trên catalog_review.
-- ---------------------------------------------------------------------
GRANT INSERT, UPDATE ON catalog_review               TO 'bookstore_definer'@'localhost';

GRANT EXECUTE ON PROCEDURE sp_review_save            TO 'bookstore_definer'@'localhost';
GRANT EXECUTE ON PROCEDURE sp_review_get_mine        TO 'bookstore_definer'@'localhost';

GRANT EXECUTE ON PROCEDURE sp_review_save            TO 'r_customer';
GRANT EXECUTE ON PROCEDURE sp_review_get_mine        TO 'r_customer';

-- ---------------------------------------------------------------------
-- Trang chi tiết sách (sp_public_book_get trong objects/20_..., sp_review_list
-- trong objects/21_...). Definer đã có SELECT trên các bảng cần đọc.
-- ---------------------------------------------------------------------
GRANT EXECUTE ON PROCEDURE sp_public_book_get        TO 'bookstore_definer'@'localhost';
GRANT EXECUTE ON PROCEDURE sp_review_list            TO 'bookstore_definer'@'localhost';

GRANT EXECUTE ON PROCEDURE sp_public_book_get        TO 'r_customer';
GRANT EXECUTE ON PROCEDURE sp_review_list            TO 'r_customer';

-- ---------------------------------------------------------------------
-- Thêm vào giỏ hàng (database/objects/31_cart.sql)
-- Definer: tạo giỏ, thêm/sửa dòng giỏ (đã có SELECT/UPDATE giỏ, SELECT/DELETE
-- dòng giỏ cho sp_place_order).
-- r_customer: chỉ gọi thủ tục; không có quyền nào trên orders_cart*.
-- ---------------------------------------------------------------------
GRANT INSERT ON orders_cart                          TO 'bookstore_definer'@'localhost';
GRANT INSERT, UPDATE ON orders_cartitem              TO 'bookstore_definer'@'localhost';

GRANT EXECUTE ON PROCEDURE sp_cart_add               TO 'bookstore_definer'@'localhost';
GRANT EXECUTE ON PROCEDURE sp_cart_add               TO 'r_customer';

-- Trang giỏ hàng: đọc, đổi số lượng, gỡ (database/objects/31_cart.sql)
-- bookstore_definer đã có SELECT, UPDATE trên orders_cart và SELECT, INSERT,
-- UPDATE, DELETE trên orders_cartitem (ở trên), không cần cấp thêm quyền bảng.
-- r_customer: chỉ gọi thủ tục.
GRANT EXECUTE ON PROCEDURE sp_cart_list              TO 'bookstore_definer'@'localhost';
GRANT EXECUTE ON PROCEDURE sp_cart_set_quantity      TO 'bookstore_definer'@'localhost';
GRANT EXECUTE ON PROCEDURE sp_cart_remove            TO 'bookstore_definer'@'localhost';
GRANT EXECUTE ON PROCEDURE sp_cart_list              TO 'r_customer';
GRANT EXECUTE ON PROCEDURE sp_cart_set_quantity      TO 'r_customer';
GRANT EXECUTE ON PROCEDURE sp_cart_remove            TO 'r_customer';

-- ---------------------------------------------------------------------
-- Quản lý tài khoản khách (database/objects/42_account.sql)
-- Definer: đổi is_active của khách (trigger chỉ cho đúng cột này), đọc bảng
-- axes để biết tài khoản "Tạm khóa", ghi core_auditlog (đã có INSERT).
-- r_staff: chỉ gọi bốn thủ tục; không có quyền UPDATE(is_active) trực tiếp.
-- ---------------------------------------------------------------------
GRANT UPDATE (is_active) ON accounts_user            TO 'bookstore_definer'@'localhost';
GRANT SELECT             ON axes_accessattempt       TO 'bookstore_definer'@'localhost';
GRANT EXECUTE ON PROCEDURE sp_staff_account_list     TO 'bookstore_definer'@'localhost';
GRANT EXECUTE ON PROCEDURE sp_staff_account_get      TO 'bookstore_definer'@'localhost';
GRANT EXECUTE ON PROCEDURE sp_staff_account_lock     TO 'bookstore_definer'@'localhost';
GRANT EXECUTE ON PROCEDURE sp_staff_account_unlock   TO 'bookstore_definer'@'localhost';
GRANT EXECUTE ON PROCEDURE sp_staff_account_list     TO 'r_staff';
GRANT EXECUTE ON PROCEDURE sp_staff_account_get      TO 'r_staff';
GRANT EXECUTE ON PROCEDURE sp_staff_account_lock     TO 'r_staff';
GRANT EXECUTE ON PROCEDURE sp_staff_account_unlock   TO 'r_staff';

-- ---------------------------------------------------------------------
-- Nhật ký hệ thống (database/objects/34_trg_orders_audit.sql, 43_logs.sql)
-- Definer: đọc 2 bảng log cho thủ tục đọc; xóa log cũ hơn 1 năm (chỉ trong
-- sp_purge_old_logs do Event gọi). Tài khoản ứng dụng vẫn chỉ có INSERT.
-- r_staff: chỉ gọi 2 thủ tục đọc. sp_purge_old_logs không cấp cho ai (chỉ Event).
-- ---------------------------------------------------------------------
GRANT SELECT, DELETE ON core_securityevent           TO 'bookstore_definer'@'localhost';
GRANT SELECT, DELETE ON core_auditlog                TO 'bookstore_definer'@'localhost';
GRANT EXECUTE ON PROCEDURE sp_staff_security_events  TO 'bookstore_definer'@'localhost';
GRANT EXECUTE ON PROCEDURE sp_staff_audit_log        TO 'bookstore_definer'@'localhost';
GRANT EXECUTE ON PROCEDURE sp_purge_old_logs         TO 'bookstore_definer'@'localhost';
GRANT EXECUTE ON PROCEDURE sp_staff_security_events  TO 'r_staff';
GRANT EXECUTE ON PROCEDURE sp_staff_audit_log        TO 'r_staff';

-- ---------------------------------------------------------------------
-- Thanh toán mô phỏng (database/objects/35_payment_simulate.sql)
-- Definer: ghi giao dịch vào payments_payment (trigger cấm sửa/xóa), đổi đơn
-- sang 'paid' (đã có UPDATE orders_order, trigger 32 chỉ cho pending → paid).
-- r_customer: chỉ gọi sp_payment_simulate; không có quyền nào trên
-- payments_payment. Django chỉ gọi khi PAYMENT_SIMULATION=True. Khi lắp cổng
-- thật thì bỏ thủ tục này và dòng EXECUTE dưới đây.
-- ---------------------------------------------------------------------
GRANT SELECT, INSERT ON payments_payment             TO 'bookstore_definer'@'localhost';
GRANT TRIGGER        ON payments_payment             TO 'bookstore_definer'@'localhost';
GRANT EXECUTE ON PROCEDURE sp_payment_simulate       TO 'bookstore_definer'@'localhost';
GRANT EXECUTE ON PROCEDURE sp_payment_simulate       TO 'r_customer';
