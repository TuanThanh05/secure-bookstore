USE BOOKSTORE_GROUP5_DB;

-- khu vực hàm tính toán dữ liệu

-- hàm tính tổng tiền giỏ hàng theo giá hiện tại
DROP FUNCTION IF EXISTS fn_calculate_cart_total;
DELIMITER $$
CREATE FUNCTION fn_calculate_cart_total(p_cart_id BIGINT UNSIGNED)
RETURNS BIGINT UNSIGNED
NOT DETERMINISTIC
READS SQL DATA
SQL SECURITY DEFINER
BEGIN
    DECLARE v_total BIGINT UNSIGNED DEFAULT 0;

    SELECT COALESCE(SUM(ci.quantity * b.price), 0)
    INTO v_total
    FROM cart_items ci
    INNER JOIN books b ON b.id = ci.book_id
    WHERE ci.cart_id = p_cart_id
      AND b.status = 'ACTIVE';

    RETURN v_total;
END$$
DELIMITER ;

-- hàm tính tổng tiền đơn hàng từ giá đã chốt trong chi tiết đơn
DROP FUNCTION IF EXISTS fn_calculate_order_total;
DELIMITER $$
CREATE FUNCTION fn_calculate_order_total(p_order_id BIGINT UNSIGNED)
RETURNS BIGINT UNSIGNED
NOT DETERMINISTIC
READS SQL DATA
SQL SECURITY DEFINER
BEGIN
    DECLARE v_total BIGINT UNSIGNED DEFAULT 0;

    SELECT COALESCE(SUM(quantity * unit_price), 0)
    INTO v_total
    FROM order_items
    WHERE order_id = p_order_id;

    RETURN v_total;
END$$
DELIMITER ;
