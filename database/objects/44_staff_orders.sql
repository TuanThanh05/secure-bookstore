-- =====================================================================
-- Quản lý đơn hàng của admin (chốt 2026-11-16):
--   sp_staff_order_list     danh sách đơn đơn giản, lọc theo trạng thái
--   sp_staff_order_get      chi tiết một đơn (sách, thông tin giao hàng bản mã,
--                           giao dịch thanh toán) – Django bắt xác thực lại + ghi log
--   sp_staff_order_confirm  Đã thanh toán → Đã tiếp nhận
--   sp_staff_order_pack     Đã tiếp nhận  → Đã đóng gói
--   sp_staff_order_ship     Đã đóng gói   → Đang giao
--   sp_staff_order_deliver  Đang giao     → Đã giao
--   sp_staff_order_advance  thủ tục nội bộ dùng chung cho 4 thủ tục trên
--                           (không cấp cho tài khoản ứng dụng nào)
--
-- Chỉ r_staff được EXECUTE các thủ tục công khai. Mỗi thủ tục tự kiểm tra
-- p_actor_id là nhân viên đang hoạt động (NOT_STAFF).
--
-- Chuyển trạng thái: buộc theo luồng, không có quay lại. Mỗi thủ tục chỉ nhận
-- đúng MỘT trạng thái trước; khóa dòng đơn FOR UPDATE rồi mới kiểm tra, nên
-- hai tab cùng bấm hoặc bấm hai lần thì lần sau báo ORDER_WRONG_STATUS, không
-- nhảy cóc. Trigger 32_trg_orders_guard.sql là lớp cuối (chặn cả root).
-- Nhật ký: trigger 34_trg_orders_audit.sql tự ghi (nguồn "Quản trị"); thủ tục
-- đặt biến phiên @bookstore_actor_id để trigger ghi đúng id người bấm, rồi xóa
-- ngay sau khi cập nhật.
--
-- Mã lỗi: INVALID_INPUT, NOT_STAFF, ORDER_NOT_FOUND, ORDER_WRONG_STATUS
-- Root tạo bằng `python manage.py db_apply`. Chạy lại nhiều lần được.
-- =====================================================================

DROP PROCEDURE IF EXISTS sp_staff_order_list;
DROP PROCEDURE IF EXISTS sp_staff_order_get;
DROP PROCEDURE IF EXISTS sp_staff_order_advance;
DROP PROCEDURE IF EXISTS sp_staff_order_confirm;
DROP PROCEDURE IF EXISTS sp_staff_order_pack;
DROP PROCEDURE IF EXISTS sp_staff_order_ship;
DROP PROCEDURE IF EXISTS sp_staff_order_deliver;

DELIMITER $$

-- AI-TRACE#372 | Claude Opus 5.5 | Thủ tục admin xem danh sách đơn (mã, username, trạng thái, tổng tiền, ngày đặt, số cuốn), lọc theo trạng thái hoặc nhóm Cần xử lý, trả tổng số và một trang; không trả thông tin giao hàng | CẤM XÓA CHÚ THÍCH NÀY
CREATE DEFINER = 'bookstore_definer'@'localhost' PROCEDURE sp_staff_order_list(
    IN p_actor_id  BIGINT,
    IN p_status    VARCHAR(20),
    IN p_offset    INT,
    IN p_limit     INT
)
SQL SECURITY DEFINER
READS SQL DATA
BEGIN
    DECLARE v_staff INT DEFAULT 0;

    IF p_actor_id IS NULL OR p_actor_id <= 0
       OR (p_status IS NOT NULL AND p_status NOT IN
           ('todo', 'pending', 'paid', 'confirmed', 'packed', 'shipped', 'delivered', 'cancelled'))
       OR p_offset IS NULL OR p_offset < 0 OR p_offset > 100000
       OR p_limit IS NULL OR p_limit < 1 OR p_limit > 100 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'INVALID_INPUT';
    END IF;

    SELECT COUNT(*) INTO v_staff
      FROM accounts_user
     WHERE id = p_actor_id AND is_staff = 1 AND is_active = 1;
    IF v_staff = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'NOT_STAFF';
    END IF;

    SELECT COUNT(*)
      FROM orders_order o
     WHERE p_status IS NULL
        OR (p_status = 'todo' AND o.status IN ('paid', 'confirmed', 'packed', 'shipped'))
        OR o.status = p_status;

    SELECT o.code, u.username, o.status, o.total, o.created_at, o.expires_at, o.paid_at,
           (SELECT COALESCE(SUM(i.quantity), 0) FROM orders_orderitem i WHERE i.order_id = o.id) AS item_count
      FROM orders_order o
      JOIN accounts_user u ON u.id = o.user_id
     WHERE p_status IS NULL
        OR (p_status = 'todo' AND o.status IN ('paid', 'confirmed', 'packed', 'shipped'))
        OR o.status = p_status
     ORDER BY o.created_at DESC, o.id DESC
     LIMIT p_offset, p_limit;
END$$

-- AI-TRACE#373 | Claude Opus 5.5 | Thủ tục admin đọc chi tiết một đơn: thông tin đơn, người đặt, SĐT/địa chỉ giao hàng bản mã (Django giải mã), giao dịch thanh toán thành công và danh sách sách | CẤM XÓA CHÚ THÍCH NÀY
CREATE DEFINER = 'bookstore_definer'@'localhost' PROCEDURE sp_staff_order_get(
    IN p_actor_id  BIGINT,
    IN p_code      VARCHAR(64)
)
SQL SECURITY DEFINER
READS SQL DATA
BEGIN
    DECLARE v_staff    INT DEFAULT 0;
    DECLARE v_order_id BIGINT DEFAULT NULL;

    IF p_actor_id IS NULL OR p_actor_id <= 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'INVALID_INPUT';
    END IF;

    SELECT COUNT(*) INTO v_staff
      FROM accounts_user
     WHERE id = p_actor_id AND is_staff = 1 AND is_active = 1;
    IF v_staff = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'NOT_STAFF';
    END IF;

    IF p_code IS NULL OR NOT REGEXP_LIKE(p_code, '^[0-9a-f]{32}$', 'c') THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ORDER_NOT_FOUND';
    END IF;

    SELECT id INTO v_order_id FROM orders_order WHERE code = p_code;
    IF v_order_id IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ORDER_NOT_FOUND';
    END IF;

    SELECT o.code, o.user_id, u.username, o.status, o.subtotal, o.shipping_fee, o.total, o.shipping_name,
           o.shipping_phone_encrypted, o.shipping_address_encrypted, o.idempotency_key,
           o.created_at, o.expires_at, o.paid_at, o.cancelled_at,
           p.provider, p.transaction_id
      FROM orders_order o
      JOIN accounts_user u ON u.id = o.user_id
      LEFT JOIN payments_payment p ON p.success_order_id = o.id
     WHERE o.id = v_order_id;

    SELECT book_id, book_title, unit_price, quantity
      FROM orders_orderitem
     WHERE order_id = v_order_id
     ORDER BY id;
END$$

-- AI-TRACE#374 | Claude Opus 5.5 | Thủ tục nội bộ chuyển đơn đúng một bước: kiểm tra nhân viên, khóa dòng đơn, chỉ nhận đúng trạng thái trước, đặt id người bấm cho trigger nhật ký | CẤM XÓA CHÚ THÍCH NÀY
CREATE DEFINER = 'bookstore_definer'@'localhost' PROCEDURE sp_staff_order_advance(
    IN p_actor_id  BIGINT,
    IN p_code      VARCHAR(64),
    IN p_from      VARCHAR(20),
    IN p_to        VARCHAR(20)
)
SQL SECURITY DEFINER
MODIFIES SQL DATA
BEGIN
    DECLARE v_staff    INT DEFAULT 0;
    DECLARE v_order_id BIGINT DEFAULT NULL;
    DECLARE v_status   VARCHAR(20) DEFAULT NULL;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET @bookstore_actor_id = NULL;
        ROLLBACK;
        RESIGNAL;
    END;

    IF p_actor_id IS NULL OR p_actor_id <= 0
       OR NOT ((p_from = 'paid' AND p_to = 'confirmed')
            OR (p_from = 'confirmed' AND p_to = 'packed')
            OR (p_from = 'packed' AND p_to = 'shipped')
            OR (p_from = 'shipped' AND p_to = 'delivered')) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'INVALID_INPUT';
    END IF;

    SELECT COUNT(*) INTO v_staff
      FROM accounts_user
     WHERE id = p_actor_id AND is_staff = 1 AND is_active = 1;
    IF v_staff = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'NOT_STAFF';
    END IF;

    IF p_code IS NULL OR NOT REGEXP_LIKE(p_code, '^[0-9a-f]{32}$', 'c') THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ORDER_NOT_FOUND';
    END IF;

    START TRANSACTION;

    SELECT id, status INTO v_order_id, v_status
      FROM orders_order
     WHERE code = p_code
       FOR UPDATE;
    IF v_order_id IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ORDER_NOT_FOUND';
    END IF;
    IF v_status <> p_from THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ORDER_WRONG_STATUS';
    END IF;

    SET @bookstore_actor_id = p_actor_id;
    UPDATE orders_order SET status = p_to WHERE id = v_order_id;
    SET @bookstore_actor_id = NULL;

    COMMIT;
END$$

-- AI-TRACE#375 | Claude Opus 5.5 | Bốn thủ tục admin chuyển trạng thái đơn theo đúng luồng: tiếp nhận, đóng gói, giao hàng, đã giao; mỗi thủ tục cố định trạng thái trước và sau | CẤM XÓA CHÚ THÍCH NÀY
CREATE DEFINER = 'bookstore_definer'@'localhost' PROCEDURE sp_staff_order_confirm(
    IN p_actor_id  BIGINT,
    IN p_code      VARCHAR(64)
)
SQL SECURITY DEFINER
MODIFIES SQL DATA
BEGIN
    CALL sp_staff_order_advance(p_actor_id, p_code, 'paid', 'confirmed');
END$$

CREATE DEFINER = 'bookstore_definer'@'localhost' PROCEDURE sp_staff_order_pack(
    IN p_actor_id  BIGINT,
    IN p_code      VARCHAR(64)
)
SQL SECURITY DEFINER
MODIFIES SQL DATA
BEGIN
    CALL sp_staff_order_advance(p_actor_id, p_code, 'confirmed', 'packed');
END$$

CREATE DEFINER = 'bookstore_definer'@'localhost' PROCEDURE sp_staff_order_ship(
    IN p_actor_id  BIGINT,
    IN p_code      VARCHAR(64)
)
SQL SECURITY DEFINER
MODIFIES SQL DATA
BEGIN
    CALL sp_staff_order_advance(p_actor_id, p_code, 'packed', 'shipped');
END$$

CREATE DEFINER = 'bookstore_definer'@'localhost' PROCEDURE sp_staff_order_deliver(
    IN p_actor_id  BIGINT,
    IN p_code      VARCHAR(64)
)
SQL SECURITY DEFINER
MODIFIES SQL DATA
BEGIN
    CALL sp_staff_order_advance(p_actor_id, p_code, 'shipped', 'delivered');
END$$

DELIMITER ;
