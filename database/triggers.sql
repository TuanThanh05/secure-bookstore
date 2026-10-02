USE BOOKSTORE_GROUP5_DB;

-- khu vực trigger bảo vệ dữ liệu thanh toán

-- trigger tự đồng bộ số tiền thanh toán với tổng tiền đơn hàng khi tạo
DROP TRIGGER IF EXISTS trg_payments_before_insert;
DELIMITER $$
CREATE TRIGGER trg_payments_before_insert
BEFORE INSERT ON payments
FOR EACH ROW
BEGIN
    DECLARE v_total BIGINT UNSIGNED;

    SELECT total_amount INTO v_total
    FROM orders
    WHERE id = NEW.order_id;

    IF v_total IS NULL OR v_total = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Không tìm thấy tổng tiền hợp lệ của đơn hàng';
    END IF;

    SET NEW.amount = v_total;
END$$
DELIMITER ;

-- trigger không cho sửa trực tiếp số tiền thanh toán
DROP TRIGGER IF EXISTS trg_payments_before_update;
DELIMITER $$
CREATE TRIGGER trg_payments_before_update
BEFORE UPDATE ON payments
FOR EACH ROW
BEGIN
    IF NEW.amount <> OLD.amount THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Không được sửa trực tiếp số tiền thanh toán';
    END IF;
END$$
DELIMITER ;

-- khu vực trigger bảo vệ nhật ký kiểm toán

-- trigger không cho sửa nhật ký kiểm toán
DROP TRIGGER IF EXISTS trg_audit_logs_block_update;
DELIMITER $$
CREATE TRIGGER trg_audit_logs_block_update
BEFORE UPDATE ON audit_logs
FOR EACH ROW
BEGIN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Nhật ký kiểm toán không được phép sửa';
END$$
DELIMITER ;

-- trigger không cho xóa nhật ký kiểm toán
DROP TRIGGER IF EXISTS trg_audit_logs_block_delete;
DELIMITER $$
CREATE TRIGGER trg_audit_logs_block_delete
BEFORE DELETE ON audit_logs
FOR EACH ROW
BEGIN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Nhật ký kiểm toán không được phép xóa';
END$$
DELIMITER ;
