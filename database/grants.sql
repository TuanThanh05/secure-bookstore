USE BOOKSTORE_GROUP5_DB;

-- khu vực vai trò cơ sở dữ liệu
CREATE ROLE IF NOT EXISTS
    'db_public_reader',
    'db_auth_service',
    'db_customer_service',
    'db_payment_service',
    'db_staff_service',
    'db_manager_service',
    'db_security_service',
    'db_operations_service',
    'db_super_service',
    'db_backup',
    'db_migrator';

-- khu vực quyền đọc công khai
GRANT SELECT ON BOOKSTORE_GROUP5_DB.v_public_books TO 'db_public_reader';
GRANT SELECT ON BOOKSTORE_GROUP5_DB.v_public_book_authors TO 'db_public_reader';
GRANT SELECT ON BOOKSTORE_GROUP5_DB.v_public_book_images TO 'db_public_reader';
GRANT SELECT ON BOOKSTORE_GROUP5_DB.v_public_reviews TO 'db_public_reader';

GRANT SELECT ON BOOKSTORE_GROUP5_DB.v_public_books TO 'db_customer_service', 'db_staff_service', 'db_manager_service', 'db_security_service', 'db_operations_service', 'db_super_service';
GRANT SELECT ON BOOKSTORE_GROUP5_DB.v_public_book_authors TO 'db_customer_service', 'db_staff_service', 'db_manager_service', 'db_security_service', 'db_operations_service', 'db_super_service';
GRANT SELECT ON BOOKSTORE_GROUP5_DB.v_public_book_images TO 'db_customer_service', 'db_staff_service', 'db_manager_service', 'db_security_service', 'db_operations_service', 'db_super_service';
GRANT SELECT ON BOOKSTORE_GROUP5_DB.v_public_reviews TO 'db_customer_service', 'db_staff_service', 'db_manager_service', 'db_security_service', 'db_operations_service', 'db_super_service';

-- khu vực quyền dịch vụ xác thực
GRANT SELECT ON BOOKSTORE_GROUP5_DB.v_auth_users TO 'db_auth_service';
GRANT SELECT ON BOOKSTORE_GROUP5_DB.v_auth_sessions TO 'db_auth_service';
GRANT SELECT ON BOOKSTORE_GROUP5_DB.v_auth_password_history TO 'db_auth_service';
GRANT SELECT ON BOOKSTORE_GROUP5_DB.v_auth_external_identities TO 'db_auth_service';
GRANT SELECT, INSERT, UPDATE ON BOOKSTORE_GROUP5_DB.email_verification_tokens TO 'db_auth_service';
GRANT SELECT, INSERT, UPDATE ON BOOKSTORE_GROUP5_DB.password_reset_tokens TO 'db_auth_service';
GRANT EXECUTE ON PROCEDURE BOOKSTORE_GROUP5_DB.sp_auth_register_local TO 'db_auth_service';
GRANT EXECUTE ON PROCEDURE BOOKSTORE_GROUP5_DB.sp_auth_register_google TO 'db_auth_service';
GRANT EXECUTE ON PROCEDURE BOOKSTORE_GROUP5_DB.sp_auth_set_password TO 'db_auth_service';
GRANT EXECUTE ON PROCEDURE BOOKSTORE_GROUP5_DB.sp_auth_verify_email TO 'db_auth_service';
GRANT EXECUTE ON PROCEDURE BOOKSTORE_GROUP5_DB.sp_auth_create_session TO 'db_auth_service';
GRANT EXECUTE ON PROCEDURE BOOKSTORE_GROUP5_DB.sp_auth_record_login_attempt TO 'db_auth_service';

-- khu vực quyền dịch vụ khách hàng
GRANT EXECUTE ON PROCEDURE BOOKSTORE_GROUP5_DB.sp_user_get_profile TO 'db_customer_service';
GRANT EXECUTE ON PROCEDURE BOOKSTORE_GROUP5_DB.sp_user_update_profile TO 'db_customer_service';
GRANT EXECUTE ON PROCEDURE BOOKSTORE_GROUP5_DB.sp_customer_get_cart TO 'db_customer_service';
GRANT EXECUTE ON PROCEDURE BOOKSTORE_GROUP5_DB.sp_customer_get_orders TO 'db_customer_service';
GRANT EXECUTE ON PROCEDURE BOOKSTORE_GROUP5_DB.sp_customer_get_order_detail TO 'db_customer_service';
GRANT EXECUTE ON PROCEDURE BOOKSTORE_GROUP5_DB.sp_customer_get_purchased_books TO 'db_customer_service';
GRANT EXECUTE ON PROCEDURE BOOKSTORE_GROUP5_DB.sp_customer_get_sessions TO 'db_customer_service';
GRANT EXECUTE ON PROCEDURE BOOKSTORE_GROUP5_DB.sp_customer_get_reviews TO 'db_customer_service';
GRANT EXECUTE ON PROCEDURE BOOKSTORE_GROUP5_DB.sp_customer_revoke_own_session TO 'db_customer_service';
GRANT EXECUTE ON PROCEDURE BOOKSTORE_GROUP5_DB.sp_customer_add_cart_item TO 'db_customer_service';
GRANT EXECUTE ON PROCEDURE BOOKSTORE_GROUP5_DB.sp_customer_set_cart_item TO 'db_customer_service';
GRANT EXECUTE ON PROCEDURE BOOKSTORE_GROUP5_DB.sp_customer_remove_cart_item TO 'db_customer_service';
GRANT EXECUTE ON PROCEDURE BOOKSTORE_GROUP5_DB.sp_customer_create_order TO 'db_customer_service';
GRANT EXECUTE ON PROCEDURE BOOKSTORE_GROUP5_DB.sp_customer_cancel_order TO 'db_customer_service';
GRANT EXECUTE ON PROCEDURE BOOKSTORE_GROUP5_DB.sp_customer_upsert_review TO 'db_customer_service';

-- khu vực quyền dịch vụ thanh toán
GRANT EXECUTE ON PROCEDURE BOOKSTORE_GROUP5_DB.sp_payment_record_momo_result TO 'db_payment_service';

-- khu vực quyền dịch vụ nhân viên
GRANT SELECT ON BOOKSTORE_GROUP5_DB.v_staff_orders TO 'db_staff_service';
GRANT SELECT ON BOOKSTORE_GROUP5_DB.v_staff_order_items TO 'db_staff_service';
GRANT SELECT ON BOOKSTORE_GROUP5_DB.v_staff_payment_status TO 'db_staff_service';
GRANT EXECUTE ON PROCEDURE BOOKSTORE_GROUP5_DB.sp_user_get_profile TO 'db_staff_service';
GRANT EXECUTE ON PROCEDURE BOOKSTORE_GROUP5_DB.sp_user_update_profile TO 'db_staff_service';
GRANT EXECUTE ON PROCEDURE BOOKSTORE_GROUP5_DB.sp_staff_change_order_status TO 'db_staff_service';

-- khu vực quyền dịch vụ quản lý cửa hàng
GRANT SELECT ON BOOKSTORE_GROUP5_DB.v_manager_inventory TO 'db_manager_service';
GRANT SELECT ON BOOKSTORE_GROUP5_DB.v_manager_inventory_transactions TO 'db_manager_service';
GRANT SELECT ON BOOKSTORE_GROUP5_DB.v_manager_orders TO 'db_manager_service';
GRANT SELECT ON BOOKSTORE_GROUP5_DB.v_manager_payments TO 'db_manager_service';
GRANT SELECT ON BOOKSTORE_GROUP5_DB.v_manager_staff_basic TO 'db_manager_service';
GRANT SELECT ON BOOKSTORE_GROUP5_DB.v_manager_reviews TO 'db_manager_service';
GRANT EXECUTE ON PROCEDURE BOOKSTORE_GROUP5_DB.sp_user_get_profile TO 'db_manager_service';
GRANT EXECUTE ON PROCEDURE BOOKSTORE_GROUP5_DB.sp_user_update_profile TO 'db_manager_service';
GRANT EXECUTE ON PROCEDURE BOOKSTORE_GROUP5_DB.sp_staff_change_order_status TO 'db_manager_service';
GRANT EXECUTE ON PROCEDURE BOOKSTORE_GROUP5_DB.sp_manager_create_author TO 'db_manager_service';
GRANT EXECUTE ON PROCEDURE BOOKSTORE_GROUP5_DB.sp_manager_update_author TO 'db_manager_service';
GRANT EXECUTE ON PROCEDURE BOOKSTORE_GROUP5_DB.sp_manager_create_category TO 'db_manager_service';
GRANT EXECUTE ON PROCEDURE BOOKSTORE_GROUP5_DB.sp_manager_update_category TO 'db_manager_service';
GRANT EXECUTE ON PROCEDURE BOOKSTORE_GROUP5_DB.sp_manager_create_publisher TO 'db_manager_service';
GRANT EXECUTE ON PROCEDURE BOOKSTORE_GROUP5_DB.sp_manager_update_publisher TO 'db_manager_service';
GRANT EXECUTE ON PROCEDURE BOOKSTORE_GROUP5_DB.sp_manager_create_supplier TO 'db_manager_service';
GRANT EXECUTE ON PROCEDURE BOOKSTORE_GROUP5_DB.sp_manager_update_supplier TO 'db_manager_service';
GRANT EXECUTE ON PROCEDURE BOOKSTORE_GROUP5_DB.sp_manager_create_book TO 'db_manager_service';
GRANT EXECUTE ON PROCEDURE BOOKSTORE_GROUP5_DB.sp_manager_update_book TO 'db_manager_service';
GRANT EXECUTE ON PROCEDURE BOOKSTORE_GROUP5_DB.sp_manager_add_book_author TO 'db_manager_service';
GRANT EXECUTE ON PROCEDURE BOOKSTORE_GROUP5_DB.sp_manager_set_primary_author TO 'db_manager_service';
GRANT EXECUTE ON PROCEDURE BOOKSTORE_GROUP5_DB.sp_manager_remove_book_author TO 'db_manager_service';
GRANT EXECUTE ON PROCEDURE BOOKSTORE_GROUP5_DB.sp_manager_add_book_image TO 'db_manager_service';
GRANT EXECUTE ON PROCEDURE BOOKSTORE_GROUP5_DB.sp_manager_update_book_image TO 'db_manager_service';
GRANT EXECUTE ON PROCEDURE BOOKSTORE_GROUP5_DB.sp_manager_remove_book_image TO 'db_manager_service';
GRANT EXECUTE ON PROCEDURE BOOKSTORE_GROUP5_DB.sp_manager_import_inventory TO 'db_manager_service';
GRANT EXECUTE ON PROCEDURE BOOKSTORE_GROUP5_DB.sp_manager_adjust_inventory TO 'db_manager_service';
GRANT EXECUTE ON PROCEDURE BOOKSTORE_GROUP5_DB.sp_manager_create_staff_account TO 'db_manager_service';
GRANT EXECUTE ON PROCEDURE BOOKSTORE_GROUP5_DB.sp_manager_set_review_status TO 'db_manager_service';
GRANT EXECUTE ON PROCEDURE BOOKSTORE_GROUP5_DB.sp_manager_cancel_order TO 'db_manager_service';

-- khu vực quyền dịch vụ quản trị an ninh
GRANT SELECT ON BOOKSTORE_GROUP5_DB.v_security_users TO 'db_security_service';
GRANT SELECT ON BOOKSTORE_GROUP5_DB.v_security_sessions TO 'db_security_service';
GRANT SELECT ON BOOKSTORE_GROUP5_DB.v_security_login_attempts TO 'db_security_service';
GRANT SELECT ON BOOKSTORE_GROUP5_DB.v_security_events TO 'db_security_service';
GRANT SELECT ON BOOKSTORE_GROUP5_DB.v_security_audit_logs TO 'db_security_service';
GRANT SELECT ON BOOKSTORE_GROUP5_DB.v_security_password_history_meta TO 'db_security_service';
GRANT EXECUTE ON PROCEDURE BOOKSTORE_GROUP5_DB.sp_user_get_profile TO 'db_security_service';
GRANT EXECUTE ON PROCEDURE BOOKSTORE_GROUP5_DB.sp_user_update_profile TO 'db_security_service';
GRANT EXECUTE ON PROCEDURE BOOKSTORE_GROUP5_DB.sp_security_lock_user TO 'db_security_service';
GRANT EXECUTE ON PROCEDURE BOOKSTORE_GROUP5_DB.sp_security_unlock_user TO 'db_security_service';
GRANT EXECUTE ON PROCEDURE BOOKSTORE_GROUP5_DB.sp_security_revoke_session TO 'db_security_service';
GRANT EXECUTE ON PROCEDURE BOOKSTORE_GROUP5_DB.sp_security_revoke_all_sessions TO 'db_security_service';
GRANT EXECUTE ON PROCEDURE BOOKSTORE_GROUP5_DB.sp_security_resolve_event TO 'db_security_service';
GRANT EXECUTE ON PROCEDURE BOOKSTORE_GROUP5_DB.sp_security_assign_non_admin_role TO 'db_security_service';
GRANT EXECUTE ON PROCEDURE BOOKSTORE_GROUP5_DB.sp_security_remove_non_admin_role TO 'db_security_service';
GRANT EXECUTE ON PROCEDURE BOOKSTORE_GROUP5_DB.sp_security_set_non_admin_status TO 'db_security_service';
GRANT EXECUTE ON PROCEDURE BOOKSTORE_GROUP5_DB.sp_security_create_non_admin_account TO 'db_security_service';

-- khu vực quyền dịch vụ vận hành
GRANT SELECT ON BOOKSTORE_GROUP5_DB.v_operations_table_statistics TO 'db_operations_service';
GRANT SELECT ON BOOKSTORE_GROUP5_DB.v_operations_database_summary TO 'db_operations_service';
GRANT EXECUTE ON PROCEDURE BOOKSTORE_GROUP5_DB.sp_user_get_profile TO 'db_operations_service';
GRANT EXECUTE ON PROCEDURE BOOKSTORE_GROUP5_DB.sp_user_update_profile TO 'db_operations_service';

-- khu vực quyền dịch vụ quản trị toàn quyền
GRANT SELECT ON BOOKSTORE_GROUP5_DB.v_staff_orders TO 'db_super_service';
GRANT SELECT ON BOOKSTORE_GROUP5_DB.v_staff_order_items TO 'db_super_service';
GRANT SELECT ON BOOKSTORE_GROUP5_DB.v_staff_payment_status TO 'db_super_service';
GRANT SELECT ON BOOKSTORE_GROUP5_DB.v_manager_inventory TO 'db_super_service';
GRANT SELECT ON BOOKSTORE_GROUP5_DB.v_manager_inventory_transactions TO 'db_super_service';
GRANT SELECT ON BOOKSTORE_GROUP5_DB.v_manager_orders TO 'db_super_service';
GRANT SELECT ON BOOKSTORE_GROUP5_DB.v_manager_payments TO 'db_super_service';
GRANT SELECT ON BOOKSTORE_GROUP5_DB.v_manager_staff_basic TO 'db_super_service';
GRANT SELECT ON BOOKSTORE_GROUP5_DB.v_manager_reviews TO 'db_super_service';
GRANT SELECT ON BOOKSTORE_GROUP5_DB.v_security_users TO 'db_super_service';
GRANT SELECT ON BOOKSTORE_GROUP5_DB.v_security_sessions TO 'db_super_service';
GRANT SELECT ON BOOKSTORE_GROUP5_DB.v_security_login_attempts TO 'db_super_service';
GRANT SELECT ON BOOKSTORE_GROUP5_DB.v_security_events TO 'db_super_service';
GRANT SELECT ON BOOKSTORE_GROUP5_DB.v_security_audit_logs TO 'db_super_service';
GRANT SELECT ON BOOKSTORE_GROUP5_DB.v_security_password_history_meta TO 'db_super_service';
GRANT SELECT ON BOOKSTORE_GROUP5_DB.v_operations_table_statistics TO 'db_super_service';
GRANT SELECT ON BOOKSTORE_GROUP5_DB.v_operations_database_summary TO 'db_super_service';
GRANT EXECUTE ON BOOKSTORE_GROUP5_DB.* TO 'db_super_service';

-- khu vực quyền sao lưu
GRANT SELECT, SHOW VIEW, TRIGGER ON BOOKSTORE_GROUP5_DB.* TO 'db_backup';

-- khu vực quyền triển khai lược đồ
GRANT ALL PRIVILEGES ON BOOKSTORE_GROUP5_DB.* TO 'db_migrator';
