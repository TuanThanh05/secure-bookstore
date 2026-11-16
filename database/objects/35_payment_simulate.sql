-- =====================================================================
-- Thanh toán mô phỏng (chốt 2026-11-16, tạm thời trước khi có cổng thật):
--   sp_payment_simulate        khách bấm "Thanh toán (mô phỏng)" cho đơn của mình
--   trg_payment_guard_update   giao dịch đã ghi không sửa được
--   trg_payment_guard_delete   giao dịch đã ghi không xóa được
--
-- Django chỉ cho gọi khi PAYMENT_SIMULATION=True trong .env. Khi có cổng thật,
-- thủ tục ghi nhận của cổng ghi vào cùng bảng payments_payment, đổi đơn sang
-- 'paid' theo đúng cách dưới đây; thủ tục này và quyền EXECUTE của nó bỏ đi.
--
-- Quy tắc:
--   - Chỉ chủ đơn, là khách hợp lệ (NOT_CUSTOMER như các thủ tục khác).
--   - Khóa dòng đơn FOR UPDATE rồi mới kiểm tra lại trạng thái và hạn: khách
--     bấm hai lần cùng lúc thì chỉ một lần thành công; khách bấm đúng lúc
--     Event hủy đơn quá hạn thì hai bên xếp hàng trên cùng dòng đơn – thủ tục
--     này chỉ nhận khi expires_at > lúc đó, Event chỉ hủy khi expires_at <=
--     lúc đó, nên không có đơn vừa "đã thanh toán" vừa "đã hủy".
--   - Số tiền ghi vào giao dịch lấy từ total của đơn trong CSDL, không nhận
--     từ ứng dụng. Mã giao dịch sinh ngẫu nhiên ngay trong CSDL.
--   - Ghi giao dịch và đổi đơn sang 'paid' trong cùng một giao dịch. Trigger
--     34_trg_orders_audit.sql tự ghi nhật ký đơn chuyển sang 'paid'.
--   - Lớp cuối: UNIQUE uq_payment_success_order (một đơn tối đa một giao dịch
--     thành công) và trigger 32 (chỉ pending → paid, paid_at ghi một lần).
--
-- Mã lỗi:
--   INVALID_INPUT, NOT_CUSTOMER
--   ORDER_NOT_FOUND     mã sai, không có, hoặc đơn của người khác (như nhau)
--   ORDER_ALREADY_PAID  đơn đã thanh toán (hoặc đã tiếp nhận, đóng gói, đang giao, đã giao)
--   ORDER_NOT_PAYABLE   đơn đã hủy
--   ORDER_EXPIRED       đơn còn chờ nhưng đã quá hạn thanh toán
--   PAYMENT_LOCKED      (trigger) sửa hoặc xóa giao dịch đã ghi
--
-- Root tạo bằng `python manage.py db_apply`. Chạy lại nhiều lần được.
-- =====================================================================

DROP PROCEDURE IF EXISTS sp_payment_simulate;
DROP TRIGGER IF EXISTS trg_payment_guard_update;
DROP TRIGGER IF EXISTS trg_payment_guard_delete;

DELIMITER $$

-- AI-TRACE#351 | Claude Opus 5.5 | Thủ tục thanh toán mô phỏng: khóa đơn của chính khách, kiểm tra lại trạng thái và hạn, ghi giao dịch 'simulated' với số tiền lấy từ đơn rồi đổi đơn sang paid trong một giao dịch | CẤM XÓA CHÚ THÍCH NÀY
CREATE DEFINER = 'bookstore_definer'@'localhost' PROCEDURE sp_payment_simulate(
    IN  p_user_id         BIGINT,
    IN  p_code            VARCHAR(64),
    IN  p_client_ip       VARCHAR(45),
    OUT p_transaction_id  VARCHAR(64)
)
SQL SECURITY DEFINER
MODIFIES SQL DATA
BEGIN
    DECLARE v_customer INT DEFAULT 0;
    DECLARE v_order_id BIGINT DEFAULT NULL;
    DECLARE v_status   VARCHAR(20) DEFAULT NULL;
    DECLARE v_expires  DATETIME(6) DEFAULT NULL;
    DECLARE v_total    INT UNSIGNED DEFAULT 0;
    DECLARE v_txn      VARCHAR(64) DEFAULT NULL;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    SET p_transaction_id = NULL;

    IF p_user_id IS NULL OR p_user_id <= 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'INVALID_INPUT';
    END IF;
    IF p_client_ip IS NOT NULL AND NOT REGEXP_LIKE(p_client_ip, '^[0-9A-Fa-f:.]{2,45}$', 'c') THEN
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

    SELECT id, status, expires_at, total INTO v_order_id, v_status, v_expires, v_total
      FROM orders_order
     WHERE code = p_code AND user_id = p_user_id
       FOR UPDATE;
    IF v_order_id IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ORDER_NOT_FOUND';
    END IF;
    IF v_status IN ('paid', 'confirmed', 'packed', 'shipped', 'delivered') THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ORDER_ALREADY_PAID';
    END IF;
    IF v_status <> 'pending' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ORDER_NOT_PAYABLE';
    END IF;
    IF v_expires <= UTC_TIMESTAMP(6) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ORDER_EXPIRED';
    END IF;

    SET v_txn = CONCAT('SIM', UPPER(HEX(RANDOM_BYTES(12))));

    INSERT INTO payments_payment
        (order_id, provider, transaction_id, amount, status, signature_valid, failure_reason, raw_payload, client_ip)
    VALUES
        (v_order_id, 'simulated', v_txn, v_total, 'success', 0, NULL,
         JSON_OBJECT('mode', 'simulated', 'order_code', p_code), p_client_ip);

    UPDATE orders_order
       SET status = 'paid', paid_at = UTC_TIMESTAMP(6)
     WHERE id = v_order_id;

    COMMIT;
    SET p_transaction_id = v_txn;
END$$

-- AI-TRACE#352 | Claude Opus 5.5 | Trigger cấm sửa và xóa giao dịch thanh toán đã ghi, kể cả root và definer | CẤM XÓA CHÚ THÍCH NÀY
CREATE DEFINER = 'bookstore_definer'@'localhost'
TRIGGER trg_payment_guard_update
BEFORE UPDATE ON payments_payment
FOR EACH ROW
BEGIN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'PAYMENT_LOCKED';
END$$

CREATE DEFINER = 'bookstore_definer'@'localhost'
TRIGGER trg_payment_guard_delete
BEFORE DELETE ON payments_payment
FOR EACH ROW
BEGIN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'PAYMENT_LOCKED';
END$$

DELIMITER ;
