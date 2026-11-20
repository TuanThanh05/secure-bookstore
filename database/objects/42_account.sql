-- =====================================================================
-- Quản lý tài khoản khách cho admin (chốt 2026-11-16).
--   sp_staff_account_list    xem danh sách, lọc theo trạng thái và username
--                            (gộp 3 nhu cầu xem/lọc vào 1 thủ tục)
--   sp_staff_account_get     xem một tài khoản (trang xác nhận khóa/mở khóa)
--   sp_staff_account_lock    khóa tài khoản (is_active = 0), có lý do
--   sp_staff_account_unlock  mở khóa (is_active = 1), có lý do
--
-- Chỉ r_staff được EXECUTE. Mỗi thủ tục tự kiểm tra p_actor_id là nhân viên
-- đang hoạt động (NOT_STAFF). Chỉ thao tác trên tài khoản KHÁCH (is_staff = 0):
-- tài khoản nhân viên, kể cả chính admin, coi như không tồn tại
-- (ACCOUNT_NOT_FOUND) nên admin không tự khóa mình được.
--
-- Trạng thái (ưu tiên từ trên xuống):
--   locked       is_active = 0                       → "Đã khóa"
--   temp_locked  axes ghi ≥ p_failure_limit lần sai trong p_cooloff_minutes
--                phút gần nhất                        → "Tạm khóa" (lý do xem log)
--   unverified   chưa xác nhận email                  → "Chưa xác nhận email"
--   active       còn lại                              → "Hoạt động"
-- Ngưỡng axes truyền từ Django (AXES_FAILURE_LIMIT, AXES_COOLOFF_TIME) để
-- không ghi cứng hai chỗ.
--
-- SĐT trả về là bản mã AES-GCM (Django giải mã, che bớt khi hiển thị). Không
-- trả password, is_superuser.
--
-- Khóa/mở khóa: khóa dòng user FOR UPDATE, ghi core_auditlog (cũ/mới + lý do)
-- trong cùng giao dịch. Trigger trg_user_guard_update (10_...) cho app_staff đổi
-- đúng cột is_active của khách, các cột khác vẫn bị chặn; app_staff không có
-- quyền UPDATE(is_active) trực tiếp nên chỉ hai thủ tục này đổi được.
-- Khóa xong, Django xóa mọi phiên của khách đó (dashboard.account_services.lock_account
-- → core.session_store.end_user_sessions; bảng phiên thuộc app_session nên không xóa ở đây).
-- Phòng hờ: core.middleware.InactiveAccountSessionMiddleware hủy phiên của tài khoản
-- is_active = 0 ở request kế tiếp, nên phiên cũ không sống lại khi mở khóa.
--
-- Mã lỗi: INVALID_INPUT, NOT_STAFF, ACCOUNT_NOT_FOUND, ALREADY_LOCKED, NOT_LOCKED
-- Root tạo bằng `python manage.py db_apply`. Chạy lại nhiều lần được.
-- =====================================================================

DROP PROCEDURE IF EXISTS sp_staff_account_list;
DROP PROCEDURE IF EXISTS sp_staff_account_get;
DROP PROCEDURE IF EXISTS sp_staff_account_lock;
DROP PROCEDURE IF EXISTS sp_staff_account_unlock;

DELIMITER $$

-- AI-TRACE#293 | Claude Opus 5.5 | Thủ tục admin xem tài khoản khách, lọc theo trạng thái (hoạt động/đã khóa/tạm khóa/chưa xác nhận) và username, SĐT trả bản mã | CẤM XÓA CHÚ THÍCH NÀY
CREATE DEFINER = 'bookstore_definer'@'localhost' PROCEDURE sp_staff_account_list(
    IN p_actor_id         BIGINT,
    IN p_status           VARCHAR(20),
    IN p_keyword          VARCHAR(255),
    IN p_failure_limit    INT,
    IN p_cooloff_minutes  INT
)
SQL SECURITY DEFINER
READS SQL DATA
BEGIN
    DECLARE v_staff   INT DEFAULT 0;
    DECLARE v_pattern VARCHAR(400) DEFAULT NULL;

    IF p_actor_id IS NULL OR p_actor_id <= 0
       OR (p_status IS NOT NULL AND p_status NOT IN ('active', 'locked', 'temp_locked', 'unverified'))
       OR (p_keyword IS NOT NULL AND CHAR_LENGTH(p_keyword) > 150)
       OR p_failure_limit IS NULL OR p_failure_limit < 1 OR p_failure_limit > 100
       OR p_cooloff_minutes IS NULL OR p_cooloff_minutes < 1 OR p_cooloff_minutes > 1440
    THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'INVALID_INPUT';
    END IF;

    SELECT COUNT(*) INTO v_staff
      FROM accounts_user
     WHERE id = p_actor_id AND is_staff = 1 AND is_active = 1;
    IF v_staff = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'NOT_STAFF';
    END IF;

    IF p_keyword IS NOT NULL AND CHAR_LENGTH(TRIM(p_keyword)) > 0 THEN
        SET v_pattern = CONCAT('%', REPLACE(REPLACE(REPLACE(TRIM(p_keyword), '\\', '\\\\'), '%', '\\%'), '_', '\\_'), '%');
    END IF;

    SELECT id, username, email, phone_encrypted, status, date_joined, last_login
      FROM (
        SELECT u.id, u.username, u.email, u.phone_encrypted, u.date_joined, u.last_login,
               CASE
                   WHEN u.is_active = 0 THEN 'locked'
                   WHEN EXISTS (
                        SELECT 1 FROM axes_accessattempt a
                         WHERE a.username = u.username
                           AND a.failures_since_start >= p_failure_limit
                           AND a.attempt_time > UTC_TIMESTAMP(6) - INTERVAL p_cooloff_minutes MINUTE
                   ) THEN 'temp_locked'
                   WHEN u.email_verified = 0 THEN 'unverified'
                   ELSE 'active'
               END AS status
          FROM accounts_user u
         WHERE u.is_staff = 0
           AND (v_pattern IS NULL OR u.username LIKE v_pattern)
      ) t
     WHERE p_status IS NULL OR t.status = p_status
     ORDER BY date_joined DESC, id DESC
     LIMIT 200;
END$$

-- AI-TRACE#294 | Claude Opus 5.5 | Thủ tục admin xem một tài khoản khách theo id (cùng cột và trạng thái như danh sách), tài khoản nhân viên coi như không có | CẤM XÓA CHÚ THÍCH NÀY
CREATE DEFINER = 'bookstore_definer'@'localhost' PROCEDURE sp_staff_account_get(
    IN p_actor_id         BIGINT,
    IN p_user_id          BIGINT,
    IN p_failure_limit    INT,
    IN p_cooloff_minutes  INT
)
SQL SECURITY DEFINER
READS SQL DATA
BEGIN
    DECLARE v_staff INT DEFAULT 0;
    DECLARE v_found INT DEFAULT 0;

    IF p_actor_id IS NULL OR p_actor_id <= 0 OR p_user_id IS NULL OR p_user_id <= 0
       OR p_failure_limit IS NULL OR p_failure_limit < 1 OR p_failure_limit > 100
       OR p_cooloff_minutes IS NULL OR p_cooloff_minutes < 1 OR p_cooloff_minutes > 1440
    THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'INVALID_INPUT';
    END IF;

    SELECT COUNT(*) INTO v_staff
      FROM accounts_user
     WHERE id = p_actor_id AND is_staff = 1 AND is_active = 1;
    IF v_staff = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'NOT_STAFF';
    END IF;

    SELECT COUNT(*) INTO v_found FROM accounts_user WHERE id = p_user_id AND is_staff = 0;
    IF v_found = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ACCOUNT_NOT_FOUND';
    END IF;

    SELECT u.id, u.username, u.email, u.phone_encrypted,
           CASE
               WHEN u.is_active = 0 THEN 'locked'
               WHEN EXISTS (
                    SELECT 1 FROM axes_accessattempt a
                     WHERE a.username = u.username
                       AND a.failures_since_start >= p_failure_limit
                       AND a.attempt_time > UTC_TIMESTAMP(6) - INTERVAL p_cooloff_minutes MINUTE
               ) THEN 'temp_locked'
               WHEN u.email_verified = 0 THEN 'unverified'
               ELSE 'active'
           END AS status,
           u.date_joined, u.last_login
      FROM accounts_user u
     WHERE u.id = p_user_id AND u.is_staff = 0;
END$$

-- AI-TRACE#295 | Claude Opus 5.5 | Thủ tục admin khóa tài khoản khách: kiểm tra lý do, khóa dòng, đặt is_active = 0, ghi core_auditlog kèm lý do cùng giao dịch | CẤM XÓA CHÚ THÍCH NÀY
CREATE DEFINER = 'bookstore_definer'@'localhost' PROCEDURE sp_staff_account_lock(
    IN p_actor_id  BIGINT,
    IN p_user_id   BIGINT,
    IN p_reason    VARCHAR(500)
)
SQL SECURITY DEFINER
MODIFIES SQL DATA
BEGIN
    DECLARE v_staff  INT DEFAULT 0;
    DECLARE v_active TINYINT DEFAULT NULL;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    IF p_actor_id IS NULL OR p_actor_id <= 0 OR p_user_id IS NULL OR p_user_id <= 0
       OR p_reason IS NULL OR CHAR_LENGTH(TRIM(p_reason)) < 5 OR CHAR_LENGTH(p_reason) > 255
    THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'INVALID_INPUT';
    END IF;

    SELECT COUNT(*) INTO v_staff
      FROM accounts_user
     WHERE id = p_actor_id AND is_staff = 1 AND is_active = 1;
    IF v_staff = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'NOT_STAFF';
    END IF;

    START TRANSACTION;

    SELECT is_active INTO v_active
      FROM accounts_user
     WHERE id = p_user_id AND is_staff = 0
       FOR UPDATE;
    IF v_active IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ACCOUNT_NOT_FOUND';
    END IF;
    IF v_active = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ALREADY_LOCKED';
    END IF;

    UPDATE accounts_user SET is_active = 0 WHERE id = p_user_id;

    INSERT INTO core_auditlog (table_name, record_id, action, old_value, new_value, db_user, app_user_id)
    VALUES ('accounts_user', p_user_id, 'UPDATE',
            JSON_OBJECT('is_active', 1),
            JSON_OBJECT('is_active', 0, 'reason', TRIM(p_reason)),
            USER(), p_actor_id);

    COMMIT;
END$$

-- AI-TRACE#296 | Claude Opus 5.5 | Thủ tục admin mở khóa tài khoản khách: kiểm tra lý do, khóa dòng, đặt is_active = 1, ghi core_auditlog kèm lý do cùng giao dịch | CẤM XÓA CHÚ THÍCH NÀY
CREATE DEFINER = 'bookstore_definer'@'localhost' PROCEDURE sp_staff_account_unlock(
    IN p_actor_id  BIGINT,
    IN p_user_id   BIGINT,
    IN p_reason    VARCHAR(500)
)
SQL SECURITY DEFINER
MODIFIES SQL DATA
BEGIN
    DECLARE v_staff  INT DEFAULT 0;
    DECLARE v_active TINYINT DEFAULT NULL;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    IF p_actor_id IS NULL OR p_actor_id <= 0 OR p_user_id IS NULL OR p_user_id <= 0
       OR p_reason IS NULL OR CHAR_LENGTH(TRIM(p_reason)) < 5 OR CHAR_LENGTH(p_reason) > 255
    THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'INVALID_INPUT';
    END IF;

    SELECT COUNT(*) INTO v_staff
      FROM accounts_user
     WHERE id = p_actor_id AND is_staff = 1 AND is_active = 1;
    IF v_staff = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'NOT_STAFF';
    END IF;

    START TRANSACTION;

    SELECT is_active INTO v_active
      FROM accounts_user
     WHERE id = p_user_id AND is_staff = 0
       FOR UPDATE;
    IF v_active IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ACCOUNT_NOT_FOUND';
    END IF;
    IF v_active = 1 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'NOT_LOCKED';
    END IF;

    UPDATE accounts_user SET is_active = 1 WHERE id = p_user_id;

    INSERT INTO core_auditlog (table_name, record_id, action, old_value, new_value, db_user, app_user_id)
    VALUES ('accounts_user', p_user_id, 'UPDATE',
            JSON_OBJECT('is_active', 0),
            JSON_OBJECT('is_active', 1, 'reason', TRIM(p_reason)),
            USER(), p_actor_id);

    COMMIT;
END$$

DELIMITER ;
