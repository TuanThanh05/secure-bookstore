-- =====================================================================
-- Nhật ký hệ thống cho admin (chốt 2026-11-16).
--   sp_staff_security_events  đọc core_securityevent (nhật ký bảo mật)
--   sp_staff_audit_log        đọc core_auditlog (nhật ký thay đổi dữ liệu)
--   sp_purge_old_logs         xóa log cũ hơn 1 năm (chỉ Event gọi)
--   ev_purge_old_logs         Event mỗi ngày gọi sp_purge_old_logs
--
-- Hai thủ tục đọc chỉ r_staff được EXECUTE, tự kiểm tra p_actor_id là nhân
-- viên (NOT_STAFF). Trả 2 bộ kết quả: (1) tổng số dòng khớp bộ lọc, (2) một
-- trang dữ liệu mới nhất trước. Mọi bộ lọc đều tùy chọn (NULL = không lọc).
-- Giới hạn: mỗi trang 1–100 dòng, offset tối đa 100000, khoảng ngày tối đa
-- 400 ngày; từ khóa tìm kiếm thoát \ % _ (LIKE).
--
-- Không khóa cứng log (chốt): tài khoản ứng dụng chỉ có INSERT trên 2 bảng log
-- như trước; chỉ definer có DELETE, dùng trong sp_purge_old_logs. Xóa theo lô
-- 5000 dòng để không giữ khóa lâu.
--
-- Mã lỗi: INVALID_INPUT, NOT_STAFF.
-- Root tạo bằng `python manage.py db_apply`. Chạy lại nhiều lần được.
-- =====================================================================

DROP EVENT IF EXISTS ev_purge_old_logs;
DROP PROCEDURE IF EXISTS sp_staff_security_events;
DROP PROCEDURE IF EXISTS sp_staff_audit_log;
DROP PROCEDURE IF EXISTS sp_purge_old_logs;

DELIMITER $$

-- AI-TRACE#322 | Claude Opus 5.5 | Thủ tục admin đọc nhật ký bảo mật: lọc loại, mức độ, khoảng ngày, username/IP; trả tổng số và một trang mới nhất trước | CẤM XÓA CHÚ THÍCH NÀY
CREATE DEFINER = 'bookstore_definer'@'localhost' PROCEDURE sp_staff_security_events(
    IN p_actor_id    BIGINT,
    IN p_event_type  VARCHAR(40),
    IN p_severity    VARCHAR(10),
    IN p_from        DATETIME(6),
    IN p_to          DATETIME(6),
    IN p_keyword     VARCHAR(255),
    IN p_offset      INT,
    IN p_limit       INT
)
SQL SECURITY DEFINER
READS SQL DATA
BEGIN
    DECLARE v_staff   INT DEFAULT 0;
    DECLARE v_pattern VARCHAR(400) DEFAULT NULL;

    IF p_actor_id IS NULL OR p_actor_id <= 0
       OR (p_event_type IS NOT NULL AND NOT REGEXP_LIKE(p_event_type, '^[a-z_]{1,40}$', 'c'))
       OR (p_severity IS NOT NULL AND p_severity NOT IN ('info', 'warning', 'critical'))
       OR (p_from IS NOT NULL AND p_to IS NOT NULL AND (p_from > p_to OR p_to > p_from + INTERVAL 400 DAY))
       OR (p_keyword IS NOT NULL AND CHAR_LENGTH(p_keyword) > 150)
       OR p_offset IS NULL OR p_offset < 0 OR p_offset > 100000
       OR p_limit IS NULL OR p_limit < 1 OR p_limit > 100
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

    SELECT COUNT(*)
      FROM core_securityevent e
      LEFT JOIN accounts_user u ON u.id = e.user_id
     WHERE (p_event_type IS NULL OR e.event_type = p_event_type)
       AND (p_severity IS NULL OR e.severity = p_severity)
       AND (p_from IS NULL OR e.created_at >= p_from)
       AND (p_to IS NULL OR e.created_at < p_to)
       AND (v_pattern IS NULL OR e.username_attempted LIKE v_pattern OR u.username LIKE v_pattern
            OR e.ip_address LIKE v_pattern);

    SELECT e.id, e.created_at, e.event_type, e.severity, e.user_id, u.username, e.username_attempted,
           e.ip_address, e.method, e.path, e.user_agent, e.detail
      FROM core_securityevent e
      LEFT JOIN accounts_user u ON u.id = e.user_id
     WHERE (p_event_type IS NULL OR e.event_type = p_event_type)
       AND (p_severity IS NULL OR e.severity = p_severity)
       AND (p_from IS NULL OR e.created_at >= p_from)
       AND (p_to IS NULL OR e.created_at < p_to)
       AND (v_pattern IS NULL OR e.username_attempted LIKE v_pattern OR u.username LIKE v_pattern
            OR e.ip_address LIKE v_pattern)
     ORDER BY e.created_at DESC, e.id DESC
     LIMIT p_offset, p_limit;
END$$

-- AI-TRACE#323 | Claude Opus 5.5 | Thủ tục admin đọc nhật ký thay đổi dữ liệu: lọc bảng, hành động, khoảng ngày, id bản ghi; kèm username người thực hiện | CẤM XÓA CHÚ THÍCH NÀY
CREATE DEFINER = 'bookstore_definer'@'localhost' PROCEDURE sp_staff_audit_log(
    IN p_actor_id   BIGINT,
    IN p_table      VARCHAR(64),
    IN p_action     VARCHAR(10),
    IN p_from       DATETIME(6),
    IN p_to         DATETIME(6),
    IN p_record_id  BIGINT,
    IN p_offset     INT,
    IN p_limit      INT
)
SQL SECURITY DEFINER
READS SQL DATA
BEGIN
    DECLARE v_staff INT DEFAULT 0;

    IF p_actor_id IS NULL OR p_actor_id <= 0
       OR (p_table IS NOT NULL AND NOT REGEXP_LIKE(p_table, '^[a-z_]{1,64}$', 'c'))
       OR (p_action IS NOT NULL AND p_action NOT IN ('INSERT', 'UPDATE', 'DELETE'))
       OR (p_from IS NOT NULL AND p_to IS NOT NULL AND (p_from > p_to OR p_to > p_from + INTERVAL 400 DAY))
       OR (p_record_id IS NOT NULL AND p_record_id <= 0)
       OR p_offset IS NULL OR p_offset < 0 OR p_offset > 100000
       OR p_limit IS NULL OR p_limit < 1 OR p_limit > 100
    THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'INVALID_INPUT';
    END IF;

    SELECT COUNT(*) INTO v_staff
      FROM accounts_user
     WHERE id = p_actor_id AND is_staff = 1 AND is_active = 1;
    IF v_staff = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'NOT_STAFF';
    END IF;

    SELECT COUNT(*)
      FROM core_auditlog a
     WHERE (p_table IS NULL OR a.table_name = p_table)
       AND (p_action IS NULL OR a.action = p_action)
       AND (p_from IS NULL OR a.created_at >= p_from)
       AND (p_to IS NULL OR a.created_at < p_to)
       AND (p_record_id IS NULL OR a.record_id = p_record_id);

    SELECT a.id, a.created_at, a.table_name, a.record_id, a.action, a.old_value, a.new_value,
           a.db_user, a.app_user_id, u.username
      FROM core_auditlog a
      LEFT JOIN accounts_user u ON u.id = a.app_user_id
     WHERE (p_table IS NULL OR a.table_name = p_table)
       AND (p_action IS NULL OR a.action = p_action)
       AND (p_from IS NULL OR a.created_at >= p_from)
       AND (p_to IS NULL OR a.created_at < p_to)
       AND (p_record_id IS NULL OR a.record_id = p_record_id)
     ORDER BY a.created_at DESC, a.id DESC
     LIMIT p_offset, p_limit;
END$$

-- AI-TRACE#324 | Claude Opus 5.5 | Thủ tục xóa nhật ký bảo mật và nhật ký thay đổi cũ hơn 1 năm, theo lô 5000 dòng, tối đa 40 lô mỗi lần chạy | CẤM XÓA CHÚ THÍCH NÀY
CREATE DEFINER = 'bookstore_definer'@'localhost' PROCEDURE sp_purge_old_logs(
    OUT p_deleted INT
)
SQL SECURITY DEFINER
MODIFIES SQL DATA
BEGIN
    DECLARE v_cutoff DATETIME(6) DEFAULT UTC_TIMESTAMP(6) - INTERVAL 1 YEAR;
    DECLARE v_batch  INT DEFAULT 0;
    DECLARE v_rounds INT DEFAULT 0;

    SET p_deleted = 0;

    purge_security: LOOP
        DELETE FROM core_securityevent WHERE created_at < v_cutoff ORDER BY created_at LIMIT 5000;
        SET v_batch = ROW_COUNT();
        SET p_deleted = p_deleted + v_batch;
        SET v_rounds = v_rounds + 1;
        IF v_batch < 5000 OR v_rounds >= 40 THEN
            LEAVE purge_security;
        END IF;
    END LOOP;

    SET v_rounds = 0;
    purge_audit: LOOP
        DELETE FROM core_auditlog WHERE created_at < v_cutoff ORDER BY created_at LIMIT 5000;
        SET v_batch = ROW_COUNT();
        SET p_deleted = p_deleted + v_batch;
        SET v_rounds = v_rounds + 1;
        IF v_batch < 5000 OR v_rounds >= 40 THEN
            LEAVE purge_audit;
        END IF;
    END LOOP;
END$$

-- AI-TRACE#325 | Claude Opus 5.5 | MySQL Event mỗi ngày (03:00 giờ Việt Nam) gọi sp_purge_old_logs để giữ nhật ký tối đa 1 năm | CẤM XÓA CHÚ THÍCH NÀY
CREATE DEFINER = 'bookstore_definer'@'localhost' EVENT ev_purge_old_logs
    ON SCHEDULE EVERY 1 DAY
    STARTS (TIMESTAMP(UTC_DATE()) + INTERVAL 20 HOUR)
    ON COMPLETION PRESERVE
    ENABLE
    COMMENT 'Xóa nhật ký bảo mật và nhật ký thay đổi cũ hơn 1 năm'
    DO
    BEGIN
        DECLARE v_deleted INT DEFAULT 0;
        CALL sp_purge_old_logs(v_deleted);
    END$$

DELIMITER ;
