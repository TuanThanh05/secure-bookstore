-- =====================================================================
-- Hậu xử lý đơn hàng (chốt 2026-11-16, nhánh A trước khung thanh toán):
--   sp_order_cancel           khách tự hủy đơn chưa thanh toán của chính mình
--   sp_cancel_expired_orders  hủy mọi đơn chờ thanh toán đã quá hạn (hạn do sp_place_order đặt, 5 phút)
--   sp_order_hold_check       (nội bộ) đếm đơn bỏ không thanh toán, đủ ngưỡng thì khóa tài khoản 24 giờ
--   ev_cancel_expired_orders  MySQL Event gọi thủ tục trên mỗi phút
--
-- Kho bị trừ ngay khi tạo đơn (sp_place_order), nên hủy đơn = cộng lại đúng
-- số cuốn trong chi tiết đơn, cùng giao dịch với việc đổi trạng thái.
--
-- Quy tắc:
--   - Chỉ đơn 'pending' mới hủy được. Đơn đã thanh toán không hủy (không có
--     hoàn tiền); trigger 32_trg_orders_guard.sql cũng chặn paid → cancelled.
--   - Khách hủy được cả đơn đã quá hạn mà Event chưa kịp xử lý.
--   - Mỗi đơn hủy trong một giao dịch riêng, khóa dòng đơn FOR UPDATE rồi mới
--     kiểm tra lại trạng thái: khách bấm hủy đúng lúc Event chạy (hoặc bấm hai
--     lần) thì chỉ một bên hủy được, kho chỉ được cộng một lần.
--   - Thứ tự khóa: đơn → sách. sp_place_order khóa giỏ → sách và không khóa
--     dòng đơn cũ nào, nên không tạo vòng chờ (không deadlock).
--   - Sau này thủ tục ghi nhận thanh toán cũng khóa dòng đơn FOR UPDATE và
--     chỉ nhận khi expires_at > lúc đó; Event chỉ hủy khi expires_at <= lúc
--     đó. Hai bên xếp hàng trên cùng dòng đơn nên không có đơn vừa "đã thanh
--     toán" vừa "đã hủy".
--
-- Chống giữ kho (báo cáo rà soát T3.4, chốt 2026-11-20):
--   Mỗi lần một đơn 'pending' bị hủy (khách bấm) hoặc hết hạn (Event), trong CÙNG
--   giao dịch gọi sp_order_hold_check: đếm số đơn của khách đó bị hủy mà chưa thanh
--   toán, tính từ mốc muộn hơn giữa (24 giờ trước) và (lần hết khóa / admin mở khóa
--   gần nhất = accounts_user.auto_locked_until cũ). Đủ 3 đơn thì đặt
--   auto_locked_until = lúc đó + 24 giờ: Django coi tài khoản là bị khóa (đăng xuất
--   mọi nơi, không đăng nhập được), sp_place_order cũng từ chối (ACCOUNT_LOCKED).
--   Ngưỡng viết ở đây (không truyền từ Django) vì đường hết hạn do Event chạy,
--   không có Django. Không dùng is_active: đó là khóa của admin (có lý do, nhật ký),
--   và trigger 10 cấm app_customer đổi is_active.
--   Admin mở khóa sớm được bằng sp_staff_account_unlock (42_account.sql).
--   Đường hết hạn tự ghi core_securityevent 'order_hold_abuse' (ip 'system');
--   đường khách hủy trả p_account_locked = 1 để Django ghi log (có IP) và đăng xuất.
--
-- Mã lỗi:
--   INVALID_INPUT, NOT_CUSTOMER
--   ORDER_NOT_FOUND        mã sai, không có, hoặc đơn của người khác (như nhau)
--   ORDER_NOT_CANCELLABLE  đơn không còn ở trạng thái chờ thanh toán
--
-- Root tạo bằng `python manage.py db_apply`. Chạy lại nhiều lần được.
-- =====================================================================

DROP EVENT IF EXISTS ev_cancel_expired_orders;
DROP PROCEDURE IF EXISTS sp_order_cancel;
DROP PROCEDURE IF EXISTS sp_order_expire_one;
DROP PROCEDURE IF EXISTS sp_cancel_expired_orders;
DROP PROCEDURE IF EXISTS sp_order_hold_check;

DELIMITER $$

-- Chỉ được gọi bên trong giao dịch của sp_order_cancel / sp_order_expire_one, sau khi
-- đã đổi đơn sang 'cancelled'. Không cấp EXECUTE cho tài khoản ứng dụng nào.
-- AI-TRACE#531 | Claude Opus 5.5 | Thủ tục nội bộ chống giữ kho: đếm đơn bị hủy chưa thanh toán trong 24 giờ (từ lần hết khóa gần nhất), đủ 3 đơn thì khóa tài khoản 24 giờ bằng auto_locked_until | CẤM XÓA CHÚ THÍCH NÀY
CREATE DEFINER = 'bookstore_definer'@'localhost' PROCEDURE sp_order_hold_check(
    IN  p_user_id  BIGINT,
    OUT p_locked   TINYINT
)
SQL SECURITY DEFINER
MODIFIES SQL DATA
BEGIN
    DECLARE c_limit        INT DEFAULT 3;
    DECLARE c_window_hours INT DEFAULT 24;
    DECLARE c_lock_hours   INT DEFAULT 24;
    DECLARE v_now          DATETIME(6);
    DECLARE v_since        DATETIME(6);
    DECLARE v_last_lock    DATETIME(6) DEFAULT NULL;
    DECLARE v_unpaid       INT DEFAULT 0;

    SET p_locked = 0;
    SET v_now = UTC_TIMESTAMP(6);

    SELECT auto_locked_until INTO v_last_lock
      FROM accounts_user
     WHERE id = p_user_id AND is_staff = 0
       FOR UPDATE;

    IF v_last_lock IS NOT NULL AND v_last_lock > v_now THEN
        SET p_locked = 1;
    ELSE
        SET v_since = v_now - INTERVAL c_window_hours HOUR;
        IF v_last_lock IS NOT NULL AND v_last_lock > v_since THEN
            SET v_since = v_last_lock;
        END IF;

        SELECT COUNT(*) INTO v_unpaid
          FROM orders_order
         WHERE user_id = p_user_id AND status = 'cancelled'
           AND paid_at IS NULL AND cancelled_at >= v_since;

        IF v_unpaid >= c_limit THEN
            UPDATE accounts_user
               SET auto_locked_until = v_now + INTERVAL c_lock_hours HOUR
             WHERE id = p_user_id AND is_staff = 0;
            SET p_locked = 1;
        END IF;
    END IF;
END$$

-- AI-TRACE#282 | Claude Opus 5.5 | Thủ tục khách tự hủy đơn chờ thanh toán của chính mình: khóa đơn, kiểm tra lại trạng thái, cộng lại kho, đổi sang cancelled trong một giao dịch | CẤM XÓA CHÚ THÍCH NÀY | đã viết lại bởi Claude Opus 5.5 khi thêm chống giữ kho (OUT p_account_locked)
CREATE DEFINER = 'bookstore_definer'@'localhost' PROCEDURE sp_order_cancel(
    IN  p_user_id         BIGINT,
    IN  p_code            VARCHAR(64),
    OUT p_account_locked  TINYINT
)
SQL SECURITY DEFINER
MODIFIES SQL DATA
BEGIN
    DECLARE v_customer INT DEFAULT 0;
    DECLARE v_order_id BIGINT DEFAULT NULL;
    DECLARE v_status   VARCHAR(20) DEFAULT NULL;
    DECLARE v_locked   TINYINT DEFAULT 0;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    SET p_account_locked = 0;

    IF p_user_id IS NULL OR p_user_id <= 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'INVALID_INPUT';
    END IF;

    SELECT COUNT(*) INTO v_customer
      FROM accounts_user
     WHERE id = p_user_id AND is_active = 1 AND is_staff = 0 AND email_verified = 1;
    IF v_customer = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'NOT_CUSTOMER';
    END IF;

    IF p_code IS NULL OR NOT REGEXP_LIKE(p_code, '^[0-9a-f]{32}$', 'c') THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ORDER_NOT_FOUND';
    END IF;

    START TRANSACTION;

    SELECT id, status INTO v_order_id, v_status
      FROM orders_order
     WHERE code = p_code AND user_id = p_user_id
       FOR UPDATE;
    IF v_order_id IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ORDER_NOT_FOUND';
    END IF;
    IF v_status <> 'pending' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ORDER_NOT_CANCELLABLE';
    END IF;

    UPDATE catalog_book b
      JOIN orders_orderitem i ON i.book_id = b.id
       SET b.stock = b.stock + i.quantity
     WHERE i.order_id = v_order_id;

    UPDATE orders_order
       SET status = 'cancelled', cancelled_at = UTC_TIMESTAMP(6)
     WHERE id = v_order_id;

    CALL sp_order_hold_check(p_user_id, v_locked);

    COMMIT;
    SET p_account_locked = v_locked;
END$$

-- AI-TRACE#283 | Claude Opus 5.5 | Thủ tục nội bộ hủy một đơn quá hạn: khóa đơn, chỉ hủy nếu vẫn pending và đã hết hạn, cộng lại kho; lỗi thì rollback riêng đơn đó | CẤM XÓA CHÚ THÍCH NÀY | đã viết lại bởi Claude Opus 5.5 khi đơn hết hạn cũng tính là bỏ đơn (chống giữ kho)
CREATE DEFINER = 'bookstore_definer'@'localhost' PROCEDURE sp_order_expire_one(
    IN  p_order_id  BIGINT,
    OUT p_done      TINYINT
)
SQL SECURITY DEFINER
MODIFIES SQL DATA
BEGIN
    DECLARE v_status  VARCHAR(20) DEFAULT NULL;
    DECLARE v_expires DATETIME(6) DEFAULT NULL;
    DECLARE v_user_id BIGINT DEFAULT NULL;
    DECLARE v_locked  TINYINT DEFAULT 0;
    DECLARE v_until   DATETIME(6) DEFAULT NULL;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    SET p_done = 0;
    START TRANSACTION;

    SELECT status, expires_at, user_id INTO v_status, v_expires, v_user_id
      FROM orders_order
     WHERE id = p_order_id
       FOR UPDATE;

    IF v_status = 'pending' AND v_expires <= UTC_TIMESTAMP(6) THEN
        UPDATE catalog_book b
          JOIN orders_orderitem i ON i.book_id = b.id
           SET b.stock = b.stock + i.quantity
         WHERE i.order_id = p_order_id;

        UPDATE orders_order
           SET status = 'cancelled', cancelled_at = UTC_TIMESTAMP(6)
         WHERE id = p_order_id;
        SET p_done = 1;

        -- AI-TRACE#532 | Claude Opus 5.5 | Đơn hết hạn cũng tính là bỏ đơn: gọi kiểm tra giữ kho, vừa khóa thì tự ghi log order_hold_abuse (Event không có Django) | CẤM XÓA CHÚ THÍCH NÀY
        SELECT auto_locked_until INTO v_until FROM accounts_user WHERE id = v_user_id;
        CALL sp_order_hold_check(v_user_id, v_locked);
        IF v_locked = 1 AND NOT (v_until IS NOT NULL AND v_until > UTC_TIMESTAMP(6)) THEN
            INSERT INTO core_securityevent (event_type, severity, user_id, ip_address, detail)
            SELECT 'order_hold_abuse', 'warning', u.id, 'system',
                   JSON_OBJECT('via', 'expired', 'order_id', p_order_id,
                               'locked_until', DATE_FORMAT(u.auto_locked_until, '%Y-%m-%dT%H:%i:%sZ'))
              FROM accounts_user u
             WHERE u.id = v_user_id;
        END IF;
    END IF;

    COMMIT;
END$$

-- AI-TRACE#284 | Claude Opus 5.5 | Thủ tục hủy các đơn chờ thanh toán đã quá hạn (tối đa 200 đơn mỗi lần), mỗi đơn một giao dịch, một đơn lỗi không chặn các đơn khác | CẤM XÓA CHÚ THÍCH NÀY
CREATE DEFINER = 'bookstore_definer'@'localhost' PROCEDURE sp_cancel_expired_orders(
    OUT p_cancelled INT
)
SQL SECURITY DEFINER
MODIFIES SQL DATA
BEGIN
    DECLARE v_done     INT DEFAULT 0;
    DECLARE v_failed   INT DEFAULT 0;
    DECLARE v_order_id BIGINT;
    DECLARE v_one      TINYINT DEFAULT 0;
    DECLARE cur_expired CURSOR FOR
        SELECT id
          FROM orders_order
         WHERE status = 'pending' AND expires_at <= UTC_TIMESTAMP(6)
         ORDER BY expires_at, id
         LIMIT 200;
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET v_done = 1;

    SET p_cancelled = 0;
    OPEN cur_expired;
    expire_loop: LOOP
        FETCH cur_expired INTO v_order_id;
        IF v_done = 1 THEN
            LEAVE expire_loop;
        END IF;
        BEGIN
            DECLARE CONTINUE HANDLER FOR SQLEXCEPTION SET v_failed = v_failed + 1;
            SET v_one = 0;
            CALL sp_order_expire_one(v_order_id, v_one);
            SET p_cancelled = p_cancelled + COALESCE(v_one, 0);
        END;
    END LOOP;
    CLOSE cur_expired;
END$$

-- AI-TRACE#285 | Claude Opus 5.5 | MySQL Event mỗi phút gọi sp_cancel_expired_orders để trả kho cho đơn quá hạn thanh toán | CẤM XÓA CHÚ THÍCH NÀY
CREATE DEFINER = 'bookstore_definer'@'localhost' EVENT ev_cancel_expired_orders
    ON SCHEDULE EVERY 1 MINUTE
    ON COMPLETION PRESERVE
    ENABLE
    COMMENT 'Hủy đơn chờ thanh toán quá hạn, cộng lại kho, khóa tài khoản giữ kho'
    DO
    BEGIN
        DECLARE v_count INT DEFAULT 0;
        CALL sp_cancel_expired_orders(v_count);
    END$$

DELIMITER ;
