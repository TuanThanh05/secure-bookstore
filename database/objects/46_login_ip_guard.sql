-- =====================================================================
-- Chặn dò mật khẩu rải từ một IP (password spraying) – báo cáo rà soát T3.2,
-- chốt 2026-11-20.
--
-- django-axes chỉ khóa theo cặp (tên đăng nhập, IP): một IP thử vài mật khẩu
-- trên rất nhiều tài khoản thì không cặp nào chạm ngưỡng. Thủ tục này đếm số
-- lần đăng nhập sai (core_securityevent 'login_failed') của MỘT IP, gộp mọi
-- tài khoản, trong p_minutes phút gần nhất; Django so với ngưỡng
-- (LOGIN_IP_FAILURE_LIMIT) và từ chối đăng nhập từ IP đó (429).
--
-- Đếm từ bảng nhật ký (bền, không mất khi khởi động lại) chứ không từ bảng axes
-- (axes xóa bản ghi sau 15 phút, không đủ cửa sổ 60 phút) hay cache.
-- r_customer chỉ có EXECUTE: thủ tục trả đúng một con số, tài khoản ứng dụng
-- vẫn không đọc được nội dung nhật ký.
--
-- Mã lỗi: INVALID_INPUT
-- Root tạo bằng `python manage.py db_apply`. Chạy lại nhiều lần được.
-- =====================================================================

DROP PROCEDURE IF EXISTS sp_login_ip_failures;

DELIMITER $$

-- AI-TRACE#544 | Claude Opus 5.5 | Thủ tục đọc đếm số lần đăng nhập sai của một IP (mọi tài khoản) trong N phút gần nhất, chỉ trả một con số | CẤM XÓA CHÚ THÍCH NÀY
CREATE DEFINER = 'bookstore_definer'@'localhost' PROCEDURE sp_login_ip_failures(
    IN p_ip_address  VARCHAR(45),
    IN p_minutes     INT
)
SQL SECURITY DEFINER
READS SQL DATA
BEGIN
    IF p_ip_address IS NULL OR CHAR_LENGTH(p_ip_address) = 0 OR CHAR_LENGTH(p_ip_address) > 45
       OR p_minutes IS NULL OR p_minutes < 1 OR p_minutes > 1440
    THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'INVALID_INPUT';
    END IF;

    SELECT COUNT(*) AS failures
      FROM core_securityevent
     WHERE created_at >= UTC_TIMESTAMP(6) - INTERVAL p_minutes MINUTE
       AND event_type = 'login_failed'
       AND ip_address = p_ip_address;
END$$

DELIMITER ;
