-- =====================================================================
-- Chặn leo thang đặc quyền ngay trong CSDL (lớp phòng thủ thứ 2).
--
-- Vấn đề: Django đăng nhập, đăng ký, đổi mật khẩu đều chạy bằng kết nối
-- `default` (tài khoản app_customer) và lệnh user.save() của Django luôn
-- ghi lại MỌI cột, kể cả is_staff, is_superuser. Vì vậy không thể chỉ cấp
-- quyền UPDATE theo cột như kế hoạch ban đầu (save() sẽ bị MySQL từ chối).
--
-- Cách làm: cấp INSERT/UPDATE trên accounts_user cho app_customer, nhưng
-- 2 trigger dưới đây từ chối mọi câu lệnh của app_customer có ý định:
--   - tạo user với is_staff = 1 hoặc is_superuser = 1;
--   - đổi giá trị is_staff, is_superuser của user đã có;
--   - sửa dòng của nhân viên/quản trị, trừ cột last_login (để nhân viên vẫn
--     đăng nhập được qua trang đăng nhập chung). Chặn kiểu tấn công ghi đè
--     mật khẩu/email của admin rồi chiếm tài khoản.
-- Ghi lại đúng giá trị cũ (như user.save() bình thường) vẫn được phép.
--
-- Với app_staff (kết nối "staff" của dashboard): quyền theo cột chỉ cho sửa
-- first_name, last_name, phone_encrypted; trigger chặn thêm việc sửa dòng
-- của KHÁCH (is_staff = 0). Kết nối staff bị lạm dụng cũng không sửa được
-- tên/SĐT của khách hàng. Ngoại lệ duy nhất (2026-11-16): cột is_active của
-- khách, chỉ đổi được qua thủ tục khóa/mở khóa tài khoản.
--
-- Hệ quả cho code:
--   - Tạo tài khoản admin: chạy createsuperuser bằng settings.migrate.
--   - Đổi mật khẩu nhân viên: chỉ bằng lệnh trên máy chủ
--     `python manage.py doi_mat_khau_admin <tên> --settings=bookstore.settings.migrate`.
--     Trên web không có đường nào đổi được mật khẩu nhân viên.
-- Kể cả khi có lỗi SQL injection trên web, kẻ tấn công cũng không tự
-- nâng mình lên nhân viên/quản trị được.
--
-- USER() trả về tài khoản MySQL đang kết nối (người gọi), không phải
-- người tạo trigger, nên kiểm tra được ai đang chạy câu lệnh.
--
-- Root tạo trigger này bằng `python manage.py db_apply` (sau migrate).
-- DEFINER là bookstore_definer (khóa đăng nhập), không phải root.
-- Chạy lại nhiều lần được (DROP ... IF EXISTS rồi tạo lại).
-- =====================================================================

DROP TRIGGER IF EXISTS trg_user_guard_insert;
DROP TRIGGER IF EXISTS trg_user_guard_update;

DELIMITER $$

CREATE DEFINER = 'bookstore_definer'@'localhost'
TRIGGER trg_user_guard_insert
BEFORE INSERT ON accounts_user
FOR EACH ROW
BEGIN
    IF SUBSTRING_INDEX(USER(), '@', 1) = 'app_customer'
       AND (NEW.is_staff <> 0 OR NEW.is_superuser <> 0) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'app_customer khong duoc tao tai khoan nhan vien/quan tri';
    END IF;
END$$

CREATE DEFINER = 'bookstore_definer'@'localhost'
TRIGGER trg_user_guard_update
BEFORE UPDATE ON accounts_user
FOR EACH ROW
BEGIN
    IF SUBSTRING_INDEX(USER(), '@', 1) = 'app_customer' THEN
        IF NEW.is_staff <> OLD.is_staff OR NEW.is_superuser <> OLD.is_superuser THEN
            SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'app_customer khong duoc thay doi is_staff/is_superuser';
        END IF;
        -- Dòng của nhân viên: chỉ được đổi last_login.
        -- <=> là so sánh an toàn với NULL (NULL <=> NULL là đúng).
        IF OLD.is_staff = 1 AND NOT (
               NEW.id <=> OLD.id AND NEW.password <=> OLD.password
           AND NEW.username <=> OLD.username AND NEW.email <=> OLD.email
           AND NEW.first_name <=> OLD.first_name AND NEW.last_name <=> OLD.last_name
           AND NEW.is_active <=> OLD.is_active AND NEW.date_joined <=> OLD.date_joined
           AND NEW.phone_encrypted <=> OLD.phone_encrypted
           AND NEW.email_verified <=> OLD.email_verified) THEN
            SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'app_customer chi duoc cap nhat last_login cua nhan vien';
        END IF;
    END IF;
    -- app_staff: chỉ được sửa dòng của nhân viên (cột nào thì quyền theo cột đã giới hạn).
    -- Riêng dòng của khách: chỉ được đổi đúng cột is_active (khóa/mở khóa). app_staff
    -- không có quyền UPDATE(is_active) trực tiếp, nên thay đổi này chỉ có thể đến từ
    -- sp_staff_account_lock/unlock (42_account.sql, chạy bằng quyền definer, ghi nhật ký).
    -- AI-TRACE#099 | Claude Opus 5.5 | Chặn app_staff sửa dòng của khách hàng, trừ cột is_active do thủ tục khóa/mở khóa đổi | CẤM XÓA CHÚ THÍCH NÀY
    IF SUBSTRING_INDEX(USER(), '@', 1) = 'app_staff' AND OLD.is_staff <> 1 AND NOT (
           NEW.id <=> OLD.id AND NEW.password <=> OLD.password
       AND NEW.username <=> OLD.username AND NEW.email <=> OLD.email
       AND NEW.first_name <=> OLD.first_name AND NEW.last_name <=> OLD.last_name
       AND NEW.is_staff <=> OLD.is_staff AND NEW.is_superuser <=> OLD.is_superuser
       AND NEW.date_joined <=> OLD.date_joined AND NEW.last_login <=> OLD.last_login
       AND NEW.phone_encrypted <=> OLD.phone_encrypted
       AND NEW.email_verified <=> OLD.email_verified) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'app_staff khong duoc sua thong tin cua khach hang';
    END IF;
END$$

DELIMITER ;
