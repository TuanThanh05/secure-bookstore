-- =====================================================================
-- Đơn hàng đã tạo thì không sửa được (chốt 2026-11-16).
--
-- Yêu cầu: thanh toán xong không thể tự tăng số lượng sách hay thêm sách
-- khác vào đơn. Lớp 1 là quyền: không tài khoản ứng dụng nào có quyền ghi
-- orders_order/orders_orderitem, không có thủ tục nào sửa đơn. Lớp 2 là các
-- trigger dưới đây, chặn ngay trong CSDL kể cả khi definer hoặc một thủ tục
-- sau này có lỗi:
--
--   orders_orderitem (chi tiết đơn)
--     - Chỉ thêm được khi đơn đang 'pending' và chưa thanh toán (đúng lúc
--       sp_place_order tạo đơn). Đơn đã thanh toán/đang giao/đã hủy → chặn.
--     - Tổng tiền các dòng không bao giờ vượt subtotal đã chốt của đơn.
--       sp_place_order chép giỏ sang đơn nên các dòng cộng lại vừa đúng bằng
--       subtotal; sau đó chèn thêm bất kỳ dòng nào cũng vượt → chặn. Nhờ vậy
--       đơn đang chờ thanh toán cũng không bị thêm sách sau khi tạo.
--     - Không bao giờ sửa (giá, số lượng, tên sách) và không bao giờ xóa.
--   orders_order (đơn)
--     - Không bao giờ đổi: mã đơn, người đặt, tiền sách, phí ship, tổng tiền,
--       thông tin giao hàng, mã chống trùng, ngày tạo, hạn thanh toán.
--     - Chỉ đổi trạng thái theo đúng chiều:
--         pending → paid, pending → cancelled, paid → shipped, shipped → delivered
--       paid_at chỉ được ghi một lần lúc chuyển sang 'paid',
--       cancelled_at chỉ được ghi một lần lúc chuyển sang 'cancelled'.
--     - Không bao giờ xóa đơn (giữ lịch sử).
--
-- Mã lỗi: ORDER_LOCKED. Chạy bằng quyền bookstore_definer (khóa đăng nhập).
-- Root tạo trigger bằng `python manage.py db_apply`. Chạy lại nhiều lần được.
-- =====================================================================

DROP TRIGGER IF EXISTS trg_orderitem_guard_insert;
DROP TRIGGER IF EXISTS trg_orderitem_guard_update;
DROP TRIGGER IF EXISTS trg_orderitem_guard_delete;
DROP TRIGGER IF EXISTS trg_order_guard_update;
DROP TRIGGER IF EXISTS trg_order_guard_delete;

DELIMITER $$

-- AI-TRACE#262 | Claude Opus 5.5 | Trigger chỉ cho thêm sách vào đơn đang chờ thanh toán lúc tạo đơn: tổng các dòng không vượt subtotal đã chốt, đơn đã thanh toán/giao/hủy bị chặn | CẤM XÓA CHÚ THÍCH NÀY
CREATE DEFINER = 'bookstore_definer'@'localhost'
TRIGGER trg_orderitem_guard_insert
BEFORE INSERT ON orders_orderitem
FOR EACH ROW
BEGIN
    DECLARE v_status   VARCHAR(20) DEFAULT NULL;
    DECLARE v_paid_at  DATETIME(6) DEFAULT NULL;
    DECLARE v_subtotal BIGINT DEFAULT 0;
    DECLARE v_lines    BIGINT DEFAULT 0;

    SELECT status, paid_at, subtotal INTO v_status, v_paid_at, v_subtotal
      FROM orders_order
     WHERE id = NEW.order_id;
    IF v_status IS NULL OR v_status <> 'pending' OR v_paid_at IS NOT NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ORDER_LOCKED';
    END IF;

    SELECT COALESCE(SUM(unit_price * quantity), 0) INTO v_lines
      FROM orders_orderitem
     WHERE order_id = NEW.order_id;
    IF v_lines + NEW.unit_price * NEW.quantity > v_subtotal THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ORDER_LOCKED';
    END IF;
END$$

-- AI-TRACE#263 | Claude Opus 5.5 | Trigger cấm sửa và xóa chi tiết đơn hàng (giá, số lượng, tên sách) | CẤM XÓA CHÚ THÍCH NÀY
CREATE DEFINER = 'bookstore_definer'@'localhost'
TRIGGER trg_orderitem_guard_update
BEFORE UPDATE ON orders_orderitem
FOR EACH ROW
BEGIN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ORDER_LOCKED';
END$$

CREATE DEFINER = 'bookstore_definer'@'localhost'
TRIGGER trg_orderitem_guard_delete
BEFORE DELETE ON orders_orderitem
FOR EACH ROW
BEGIN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ORDER_LOCKED';
END$$

-- AI-TRACE#264 | Claude Opus 5.5 | Trigger cấm đổi tiền, thông tin giao hàng của đơn; trạng thái chỉ đi đúng chiều, mốc thanh toán/hủy ghi một lần | CẤM XÓA CHÚ THÍCH NÀY
CREATE DEFINER = 'bookstore_definer'@'localhost'
TRIGGER trg_order_guard_update
BEFORE UPDATE ON orders_order
FOR EACH ROW
BEGIN
    -- <=> là so sánh an toàn với NULL (NULL <=> NULL là đúng).
    IF NOT (NEW.id <=> OLD.id AND NEW.code <=> OLD.code AND NEW.user_id <=> OLD.user_id
            AND NEW.subtotal <=> OLD.subtotal AND NEW.shipping_fee <=> OLD.shipping_fee
            AND NEW.total <=> OLD.total AND NEW.shipping_name <=> OLD.shipping_name
            AND NEW.shipping_phone_encrypted <=> OLD.shipping_phone_encrypted
            AND NEW.shipping_address_encrypted <=> OLD.shipping_address_encrypted
            AND NEW.idempotency_key <=> OLD.idempotency_key
            AND NEW.created_at <=> OLD.created_at AND NEW.expires_at <=> OLD.expires_at) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ORDER_LOCKED';
    END IF;

    IF NOT (NEW.status <=> OLD.status) AND NOT (
           (OLD.status = 'pending' AND NEW.status IN ('paid', 'cancelled'))
        OR (OLD.status = 'paid'    AND NEW.status = 'shipped')
        OR (OLD.status = 'shipped' AND NEW.status = 'delivered')) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ORDER_LOCKED';
    END IF;

    IF NOT (NEW.paid_at <=> OLD.paid_at)
       AND NOT (OLD.paid_at IS NULL AND OLD.status = 'pending' AND NEW.status = 'paid') THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ORDER_LOCKED';
    END IF;

    IF NOT (NEW.cancelled_at <=> OLD.cancelled_at)
       AND NOT (OLD.cancelled_at IS NULL AND OLD.status = 'pending' AND NEW.status = 'cancelled') THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ORDER_LOCKED';
    END IF;
END$$

-- AI-TRACE#265 | Claude Opus 5.5 | Trigger cấm xóa đơn hàng để giữ lịch sử | CẤM XÓA CHÚ THÍCH NÀY
CREATE DEFINER = 'bookstore_definer'@'localhost'
TRIGGER trg_order_guard_delete
BEFORE DELETE ON orders_order
FOR EACH ROW
BEGIN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ORDER_LOCKED';
END$$

DELIMITER ;
