-- =====================================================================
-- Bảo vệ xác thực 2 bước của nhân viên (bảng ở schema/10_two_factor.sql).
--
-- Chỉ app_auth có quyền trên accounts_totpdevice và accounts_recoverycode
-- (khách bật/tắt 2 bước, ghi bước thời gian khi đăng nhập). Trigger dưới đây
-- chặn app_auth (và app_customer, phòng khi cấp nhầm quyền) đụng vào 2 bước
-- của NHÂN VIÊN:
--   - không tạo, không xóa thiết bị TOTP của nhân viên: admin chỉ cài/cài lại
--     bằng lệnh trên máy chủ (tao_admin, dat_lai_2fa_admin, tài khoản migrate);
--   - với thiết bị của nhân viên chỉ được tăng last_used_step (lúc admin đăng
--     nhập), không đổi chuỗi bí mật, không đổi chủ, không lùi bước thời gian;
--   - không tạo/sửa/xóa mã dự phòng của nhân viên (admin không có mã dự phòng).
-- Nhờ vậy SQL injection ở trang tài khoản (kết nối app_auth) cũng không thay
-- được Google Authenticator của admin bằng điện thoại của kẻ tấn công.
-- Với khách: last_used_step cũng không được lùi (chống dùng lại mã cũ).
-- =====================================================================

DROP TRIGGER IF EXISTS trg_totp_guard_insert;
DROP TRIGGER IF EXISTS trg_totp_guard_update;
DROP TRIGGER IF EXISTS trg_totp_guard_delete;
DROP TRIGGER IF EXISTS trg_recovery_guard_insert;
DROP TRIGGER IF EXISTS trg_recovery_guard_update;
DROP TRIGGER IF EXISTS trg_recovery_guard_delete;

DELIMITER $$

-- AI-TRACE#472 | Claude Opus 5.5 | Tài khoản ứng dụng không được tạo thiết bị TOTP cho nhân viên | CẤM XÓA CHÚ THÍCH NÀY
CREATE DEFINER = 'bookstore_definer'@'localhost'
TRIGGER trg_totp_guard_insert BEFORE INSERT ON accounts_totpdevice
FOR EACH ROW
BEGIN
    IF SUBSTRING_INDEX(USER(), '@', 1) IN ('app_customer', 'app_auth')
       AND EXISTS (SELECT 1 FROM accounts_user WHERE id = NEW.user_id AND (is_staff <> 0 OR is_superuser <> 0)) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'tai khoan ung dung khong duoc cai 2 buoc cho nhan vien';
    END IF;
END$$

-- AI-TRACE#473 | Claude Opus 5.5 | Thiết bị của nhân viên chỉ được tăng bước thời gian; mọi thiết bị không được lùi bước | CẤM XÓA CHÚ THÍCH NÀY
CREATE DEFINER = 'bookstore_definer'@'localhost'
TRIGGER trg_totp_guard_update BEFORE UPDATE ON accounts_totpdevice
FOR EACH ROW
BEGIN
    IF SUBSTRING_INDEX(USER(), '@', 1) IN ('app_customer', 'app_auth') THEN
        IF OLD.last_used_step IS NOT NULL
           AND (NEW.last_used_step IS NULL OR NEW.last_used_step < OLD.last_used_step) THEN
            SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'khong duoc lui buoc thoi gian cua ma 2 buoc';
        END IF;
        IF EXISTS (SELECT 1 FROM accounts_user WHERE id = OLD.user_id AND (is_staff <> 0 OR is_superuser <> 0))
           AND NOT (NEW.id <=> OLD.id AND NEW.user_id <=> OLD.user_id
                AND NEW.secret_encrypted <=> OLD.secret_encrypted
                AND NEW.confirmed_at <=> OLD.confirmed_at
                AND NEW.created_at <=> OLD.created_at) THEN
            SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'tai khoan ung dung chi duoc ghi buoc thoi gian cho 2 buoc cua nhan vien';
        END IF;
    END IF;
END$$

-- AI-TRACE#474 | Claude Opus 5.5 | Tài khoản ứng dụng không được xóa thiết bị TOTP của nhân viên | CẤM XÓA CHÚ THÍCH NÀY
CREATE DEFINER = 'bookstore_definer'@'localhost'
TRIGGER trg_totp_guard_delete BEFORE DELETE ON accounts_totpdevice
FOR EACH ROW
BEGIN
    IF SUBSTRING_INDEX(USER(), '@', 1) IN ('app_customer', 'app_auth')
       AND EXISTS (SELECT 1 FROM accounts_user WHERE id = OLD.user_id AND (is_staff <> 0 OR is_superuser <> 0)) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'tai khoan ung dung khong duoc go 2 buoc cua nhan vien';
    END IF;
END$$

-- AI-TRACE#475 | Claude Opus 5.5 | Tài khoản ứng dụng không được tạo/sửa/xóa mã dự phòng của nhân viên | CẤM XÓA CHÚ THÍCH NÀY
CREATE DEFINER = 'bookstore_definer'@'localhost'
TRIGGER trg_recovery_guard_insert BEFORE INSERT ON accounts_recoverycode
FOR EACH ROW
BEGIN
    IF SUBSTRING_INDEX(USER(), '@', 1) IN ('app_customer', 'app_auth')
       AND EXISTS (SELECT 1 FROM accounts_user WHERE id = NEW.user_id AND (is_staff <> 0 OR is_superuser <> 0)) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'nhan vien khong co ma du phong';
    END IF;
END$$

CREATE DEFINER = 'bookstore_definer'@'localhost'
TRIGGER trg_recovery_guard_update BEFORE UPDATE ON accounts_recoverycode
FOR EACH ROW
BEGIN
    IF SUBSTRING_INDEX(USER(), '@', 1) IN ('app_customer', 'app_auth') THEN
        IF EXISTS (SELECT 1 FROM accounts_user WHERE id = OLD.user_id AND (is_staff <> 0 OR is_superuser <> 0)) THEN
            SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'nhan vien khong co ma du phong';
        END IF;
        -- Mã dự phòng chỉ đi một chiều: chưa dùng -> đã dùng; không đổi mã, không "hồi sinh" mã đã dùng
        IF NOT (NEW.id <=> OLD.id AND NEW.user_id <=> OLD.user_id AND NEW.code_hash <=> OLD.code_hash
                AND NEW.created_at <=> OLD.created_at)
           OR (OLD.used_at IS NOT NULL AND NOT (NEW.used_at <=> OLD.used_at)) THEN
            SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'ma du phong chi duoc danh dau da dung mot lan';
        END IF;
    END IF;
END$$

CREATE DEFINER = 'bookstore_definer'@'localhost'
TRIGGER trg_recovery_guard_delete BEFORE DELETE ON accounts_recoverycode
FOR EACH ROW
BEGIN
    IF SUBSTRING_INDEX(USER(), '@', 1) IN ('app_customer', 'app_auth')
       AND EXISTS (SELECT 1 FROM accounts_user WHERE id = OLD.user_id AND (is_staff <> 0 OR is_superuser <> 0)) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'nhan vien khong co ma du phong';
    END IF;
END$$

DELIMITER ;
