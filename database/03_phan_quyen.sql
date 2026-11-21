GRANT SELECT, TRIGGER ON accounts_user TO 'bookstore_definer'@'localhost';

GRANT SELECT, INSERT, DELETE ON accounts_passwordhistory TO 'bookstore_definer'@'localhost';
-- Trigger 12 bảo vệ 2 bước của nhân viên (`database/01_bang.sql`)
GRANT SELECT, TRIGGER ON accounts_totpdevice   TO 'bookstore_definer'@'localhost';
GRANT SELECT, TRIGGER ON accounts_recoverycode TO 'bookstore_definer'@'localhost';


-- Django đọc khi khởi động và khi kiểm tra quyền
GRANT SELECT ON django_migrations              TO 'r_customer';
GRANT SELECT ON django_content_type            TO 'r_customer';
GRANT SELECT ON auth_permission                TO 'r_customer';
GRANT SELECT ON auth_group                     TO 'r_customer';
GRANT SELECT ON auth_group_permissions         TO 'r_customer';
-- Chỉ ĐỌC nhóm/quyền của user: khách không tự thêm mình vào nhóm nhân viên được
GRANT SELECT ON accounts_user_groups           TO 'r_customer';
GRANT SELECT ON accounts_user_user_permissions TO 'r_customer';

GRANT SELECT ON accounts_user                  TO 'r_customer';
REVOKE IF EXISTS INSERT, UPDATE ON accounts_user FROM 'r_customer';

GRANT SELECT ON accounts_passwordhistory       TO 'r_customer';

REVOKE IF EXISTS SELECT, INSERT, UPDATE, DELETE ON django_session FROM 'r_customer';

-- Nhật ký bảo mật: chỉ được ghi thêm, không đọc/sửa/xóa
GRANT INSERT ON core_securityevent             TO 'r_customer';
REVOKE IF EXISTS SELECT, INSERT, UPDATE, DELETE ON axes_accessattempt           FROM 'r_customer';
REVOKE IF EXISTS SELECT, INSERT, UPDATE, DELETE ON axes_accessattemptexpiration FROM 'r_customer';
REVOKE IF EXISTS SELECT, INSERT, UPDATE         ON axes_accesslog               FROM 'r_customer';

GRANT SELECT, INSERT, UPDATE, DELETE ON django_session TO 'r_session';

GRANT SELECT, INSERT, UPDATE ON accounts_user TO 'r_auth';
GRANT SELECT, INSERT, UPDATE, DELETE ON accounts_totpdevice   TO 'r_auth';
GRANT SELECT, INSERT, UPDATE, DELETE ON accounts_recoverycode TO 'r_auth';
GRANT SELECT, INSERT, UPDATE, DELETE ON axes_accessattempt           TO 'r_auth';
GRANT SELECT, INSERT, UPDATE, DELETE ON axes_accessattemptexpiration TO 'r_auth';
GRANT SELECT, INSERT, UPDATE         ON axes_accesslog               TO 'r_auth';

GRANT INSERT ON core_securityevent             TO 'r_staff';

GRANT SELECT (id), UPDATE (first_name, last_name, phone_encrypted) ON accounts_user TO 'r_staff';

GRANT SELECT, UPDATE ON orders_cart      TO 'bookstore_definer'@'localhost';
GRANT SELECT, DELETE ON orders_cartitem  TO 'bookstore_definer'@'localhost';
GRANT SELECT, UPDATE ON catalog_book     TO 'bookstore_definer'@'localhost';   -- thêm INSERT, DELETE ở phần sách bên dưới
GRANT SELECT, INSERT ON orders_order     TO 'bookstore_definer'@'localhost';
GRANT INSERT         ON orders_orderitem TO 'bookstore_definer'@'localhost';

-- Thủ tục SQL SECURITY DEFINER: MySQL kiểm tra cả quyền EXECUTE của chính definer
GRANT EXECUTE ON PROCEDURE sp_place_order TO 'bookstore_definer'@'localhost';

-- Khách chỉ được gọi thủ tục, không có quyền nào trên các bảng trên
GRANT EXECUTE ON PROCEDURE sp_place_order TO 'r_customer';

GRANT SELECT          ON orders_orderitem TO 'bookstore_definer'@'localhost';
GRANT TRIGGER         ON orders_order     TO 'bookstore_definer'@'localhost';
GRANT TRIGGER         ON orders_orderitem TO 'bookstore_definer'@'localhost';
GRANT EXECUTE ON PROCEDURE sp_order_get   TO 'bookstore_definer'@'localhost';
GRANT EXECUTE ON PROCEDURE sp_order_get   TO 'r_customer';

GRANT UPDATE                                   ON orders_order TO 'bookstore_definer'@'localhost';
GRANT EVENT ON *                               TO 'bookstore_definer'@'localhost';
GRANT EXECUTE ON PROCEDURE sp_order_cancel          TO 'bookstore_definer'@'localhost';
GRANT EXECUTE ON PROCEDURE sp_order_expire_one      TO 'bookstore_definer'@'localhost';
GRANT EXECUTE ON PROCEDURE sp_cancel_expired_orders TO 'bookstore_definer'@'localhost';
GRANT EXECUTE ON PROCEDURE sp_order_hold_check      TO 'bookstore_definer'@'localhost';
GRANT EXECUTE ON PROCEDURE sp_order_cancel          TO 'r_customer';

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

GRANT SELECT ON catalog_review                       TO 'bookstore_definer'@'localhost';

GRANT EXECUTE ON PROCEDURE sp_public_category_list   TO 'bookstore_definer'@'localhost';
GRANT EXECUTE ON PROCEDURE sp_public_book_list       TO 'bookstore_definer'@'localhost';

GRANT EXECUTE ON PROCEDURE sp_public_category_list   TO 'r_customer';
GRANT EXECUTE ON PROCEDURE sp_public_book_list       TO 'r_customer';

GRANT INSERT, UPDATE ON catalog_review               TO 'bookstore_definer'@'localhost';

GRANT EXECUTE ON PROCEDURE sp_review_save            TO 'bookstore_definer'@'localhost';
GRANT EXECUTE ON PROCEDURE sp_review_get_mine        TO 'bookstore_definer'@'localhost';
GRANT EXECUTE ON PROCEDURE sp_review_can_write       TO 'bookstore_definer'@'localhost';

GRANT EXECUTE ON PROCEDURE sp_review_save            TO 'r_customer';
GRANT EXECUTE ON PROCEDURE sp_review_get_mine        TO 'r_customer';
GRANT EXECUTE ON PROCEDURE sp_review_can_write       TO 'r_customer';

GRANT EXECUTE ON PROCEDURE sp_public_book_get        TO 'bookstore_definer'@'localhost';
GRANT EXECUTE ON PROCEDURE sp_review_list            TO 'bookstore_definer'@'localhost';

GRANT EXECUTE ON PROCEDURE sp_public_book_get        TO 'r_customer';
GRANT EXECUTE ON PROCEDURE sp_review_list            TO 'r_customer';

GRANT INSERT ON orders_cart                          TO 'bookstore_definer'@'localhost';
GRANT INSERT, UPDATE ON orders_cartitem              TO 'bookstore_definer'@'localhost';

GRANT EXECUTE ON PROCEDURE sp_cart_add               TO 'bookstore_definer'@'localhost';
GRANT EXECUTE ON PROCEDURE sp_cart_add               TO 'r_customer';

GRANT EXECUTE ON PROCEDURE sp_cart_list              TO 'bookstore_definer'@'localhost';
GRANT EXECUTE ON PROCEDURE sp_cart_set_quantity      TO 'bookstore_definer'@'localhost';
GRANT EXECUTE ON PROCEDURE sp_cart_remove            TO 'bookstore_definer'@'localhost';
GRANT EXECUTE ON PROCEDURE sp_cart_list              TO 'r_customer';
GRANT EXECUTE ON PROCEDURE sp_cart_set_quantity      TO 'r_customer';
GRANT EXECUTE ON PROCEDURE sp_cart_remove            TO 'r_customer';

GRANT UPDATE (is_active) ON accounts_user            TO 'bookstore_definer'@'localhost';
-- Chống giữ kho (33_order_cancel.sql, 42_account.sql): definer đặt/gỡ khóa tự động.
GRANT UPDATE (auto_locked_until) ON accounts_user    TO 'bookstore_definer'@'localhost';
GRANT SELECT             ON axes_accessattempt       TO 'bookstore_definer'@'localhost';
GRANT EXECUTE ON PROCEDURE sp_staff_account_list     TO 'bookstore_definer'@'localhost';
GRANT EXECUTE ON PROCEDURE sp_staff_account_get      TO 'bookstore_definer'@'localhost';
GRANT EXECUTE ON PROCEDURE sp_staff_account_lock     TO 'bookstore_definer'@'localhost';
GRANT EXECUTE ON PROCEDURE sp_staff_account_unlock   TO 'bookstore_definer'@'localhost';
GRANT EXECUTE ON PROCEDURE sp_staff_account_list     TO 'r_staff';
GRANT EXECUTE ON PROCEDURE sp_staff_account_get      TO 'r_staff';
GRANT EXECUTE ON PROCEDURE sp_staff_account_lock     TO 'r_staff';
GRANT EXECUTE ON PROCEDURE sp_staff_account_unlock   TO 'r_staff';

GRANT SELECT, INSERT, DELETE ON core_securityevent   TO 'bookstore_definer'@'localhost';
GRANT SELECT, DELETE ON core_auditlog                TO 'bookstore_definer'@'localhost';
GRANT EXECUTE ON PROCEDURE sp_staff_security_events  TO 'bookstore_definer'@'localhost';
GRANT EXECUTE ON PROCEDURE sp_staff_audit_log        TO 'bookstore_definer'@'localhost';
GRANT EXECUTE ON PROCEDURE sp_purge_old_logs         TO 'bookstore_definer'@'localhost';
GRANT EXECUTE ON PROCEDURE sp_staff_security_events  TO 'r_staff';
GRANT EXECUTE ON PROCEDURE sp_staff_audit_log        TO 'r_staff';

GRANT SELECT, INSERT ON payments_payment             TO 'bookstore_definer'@'localhost';
GRANT TRIGGER        ON payments_payment             TO 'bookstore_definer'@'localhost';
GRANT EXECUTE ON PROCEDURE sp_payment_simulate       TO 'bookstore_definer'@'localhost';

GRANT EXECUTE ON PROCEDURE sp_order_list_mine        TO 'bookstore_definer'@'localhost';
GRANT EXECUTE ON PROCEDURE sp_order_list_mine        TO 'r_customer';

GRANT EXECUTE ON PROCEDURE sp_staff_order_list       TO 'bookstore_definer'@'localhost';
GRANT EXECUTE ON PROCEDURE sp_staff_order_get        TO 'bookstore_definer'@'localhost';
GRANT EXECUTE ON PROCEDURE sp_staff_order_advance    TO 'bookstore_definer'@'localhost';
GRANT EXECUTE ON PROCEDURE sp_staff_order_confirm    TO 'bookstore_definer'@'localhost';
GRANT EXECUTE ON PROCEDURE sp_staff_order_pack       TO 'bookstore_definer'@'localhost';
GRANT EXECUTE ON PROCEDURE sp_staff_order_ship       TO 'bookstore_definer'@'localhost';
GRANT EXECUTE ON PROCEDURE sp_staff_order_deliver    TO 'bookstore_definer'@'localhost';
GRANT EXECUTE ON PROCEDURE sp_staff_order_list       TO 'r_staff';
GRANT EXECUTE ON PROCEDURE sp_staff_order_get        TO 'r_staff';
GRANT EXECUTE ON PROCEDURE sp_staff_order_confirm    TO 'r_staff';
GRANT EXECUTE ON PROCEDURE sp_staff_order_pack       TO 'r_staff';
GRANT EXECUTE ON PROCEDURE sp_staff_order_ship       TO 'r_staff';
GRANT EXECUTE ON PROCEDURE sp_staff_order_deliver    TO 'r_staff';

GRANT EXECUTE ON PROCEDURE sp_staff_dashboard_orders    TO 'bookstore_definer'@'localhost';
GRANT EXECUTE ON PROCEDURE sp_staff_dashboard_stock     TO 'bookstore_definer'@'localhost';
GRANT EXECUTE ON PROCEDURE sp_staff_dashboard_security  TO 'bookstore_definer'@'localhost';
GRANT EXECUTE ON PROCEDURE sp_staff_dashboard_orders    TO 'r_staff';
GRANT EXECUTE ON PROCEDURE sp_staff_dashboard_stock     TO 'r_staff';
GRANT EXECUTE ON PROCEDURE sp_staff_dashboard_security  TO 'r_staff';

GRANT EXECUTE ON PROCEDURE sp_login_ip_failures      TO 'bookstore_definer'@'localhost';
GRANT EXECUTE ON PROCEDURE sp_login_ip_failures      TO 'r_customer';
GRANT SELECT, SHOW VIEW, TRIGGER, EVENT ON *   TO 'bookstore_backup'@'localhost';
GRANT SHOW_ROUTINE ON *.*                      TO 'bookstore_backup'@'localhost';

-- Trạng thái sao lưu trên trang Tổng quan (phần 45 của `database/02_trigger_thu_tuc.sql`)
GRANT EXECUTE ON PROCEDURE sp_staff_dashboard_backup    TO 'bookstore_definer'@'localhost';
GRANT EXECUTE ON PROCEDURE sp_staff_dashboard_backup    TO 'r_staff';
