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

-- Phiên đăng nhập (SESSION_ENGINE mặc định lưu trong CSDL)
GRANT SELECT, INSERT, UPDATE, DELETE ON django_session TO 'r_customer';

-- Nhật ký bảo mật: chỉ được ghi thêm, không đọc/sửa/xóa
GRANT INSERT ON core_securityevent             TO 'r_customer';

-- ---------------------------------------------------------------------
-- r_staff: kết nối "staff" (app_staff), chỉ app dashboard dùng
-- Phần lớn quyền (view v_staff_*, thủ tục sp_book_*...) thêm ở các bước sau.
-- ---------------------------------------------------------------------
GRANT INSERT ON core_securityevent             TO 'r_staff';
