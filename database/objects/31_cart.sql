-- =====================================================================
-- Giỏ hàng của khách (orders_cart, orders_cartitem).
--
--   sp_cart_add   thêm sách vào giỏ; sách đã có thì cộng thêm số lượng
--
-- Chốt 2026-11-15:
--   - Mỗi đầu sách trong giỏ tối đa 5 cuốn (bảng còn CHECK 1..10 làm giới hạn
--     ngoài cùng). Cộng dồn vượt 5 → CART_LIMIT, không tự đổi số lượng.
--   - Mỗi giỏ tối đa 30 đầu sách khác nhau → CART_FULL (chống lạm dụng).
--   - Chỉ khách đang hoạt động, đã xác nhận email, không phải nhân viên.
--   - Chỉ sách đang hiện và còn hàng (stock > 0). KHÔNG so số lượng với tồn
--     kho thật ở bước này để khách không dò được số tồn kho; sp_place_order
--     kiểm tra tồn kho chính xác (có khóa dòng) lúc đặt hàng.
--
-- Bảo mật / race condition:
--   - p_user_id do Django lấy từ phiên đăng nhập, thủ tục kiểm tra lại.
--   - Giỏ tạo bằng INSERT ... ON DUPLICATE KEY UPDATE trên UNIQUE(user_id),
--     rồi khóa dòng giỏ FOR UPDATE, nên hai lần bấm cùng lúc xếp hàng, cộng
--     đúng, không tạo hai giỏ hay hai dòng.
--   - Thứ tự khóa giống sp_place_order (giỏ trước, sách sau; ở đây sách chỉ
--     khóa chia sẻ FOR SHARE) để hai thủ tục không chờ chéo nhau (deadlock).
--   - r_customer chỉ có EXECUTE; không có quyền nào trên orders_cart*.
--
-- Lỗi (SIGNAL SQLSTATE '45000', MESSAGE_TEXT là đúng một mã):
--   INVALID_INPUT   tham số sai (số lượng ngoài 1–5)
--   NOT_CUSTOMER    không phải khách hợp lệ
--   BOOK_NOT_FOUND  sách không tồn tại hoặc đang ẩn
--   OUT_OF_STOCK    sách hết hàng
--   CART_LIMIT      tổng số cuốn của sách này trong giỏ sẽ vượt 5
--   CART_FULL       giỏ đã có 30 đầu sách
--
-- Root tạo bằng `python manage.py db_apply`. Chạy lại nhiều lần được.
-- =====================================================================

DROP PROCEDURE IF EXISTS sp_cart_add;

DELIMITER $$

-- AI-TRACE#226 | Claude Opus 5.5 | Thủ tục thêm sách vào giỏ: kiểm tra khách, sách còn hàng, cộng dồn tối đa 5 cuốn, tối đa 30 đầu sách, khóa giỏ chống bấm trùng | CẤM XÓA CHÚ THÍCH NÀY
CREATE DEFINER = 'bookstore_definer'@'localhost' PROCEDURE sp_cart_add(
    IN  p_user_id       BIGINT,
    IN  p_book_id       BIGINT,
    IN  p_quantity      INT,
    OUT p_new_quantity  INT
)
SQL SECURITY DEFINER
MODIFIES SQL DATA
BEGIN
    DECLARE v_customer INT DEFAULT 0;
    DECLARE v_stock    INT DEFAULT NULL;
    DECLARE v_cart_id  BIGINT DEFAULT NULL;
    DECLARE v_old      INT DEFAULT NULL;
    DECLARE v_items    INT DEFAULT 0;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    SET p_new_quantity = NULL;

    IF p_user_id IS NULL OR p_user_id <= 0
       OR p_book_id IS NULL OR p_book_id <= 0
       OR p_quantity IS NULL OR p_quantity < 1 OR p_quantity > 5
    THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'INVALID_INPUT';
    END IF;

    SELECT COUNT(*) INTO v_customer
      FROM accounts_user
     WHERE id = p_user_id AND is_active = 1 AND is_staff = 0 AND email_verified = 1;
    IF v_customer = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'NOT_CUSTOMER';
    END IF;

    START TRANSACTION;

    -- Giỏ của khách: tạo nếu chưa có, lấy id nếu đã có, rồi khóa dòng giỏ
    INSERT INTO orders_cart (user_id) VALUES (p_user_id)
    ON DUPLICATE KEY UPDATE id = LAST_INSERT_ID(id);
    SET v_cart_id = LAST_INSERT_ID();

    SELECT id INTO v_cart_id FROM orders_cart WHERE id = v_cart_id FOR UPDATE;

    SELECT stock INTO v_stock
      FROM catalog_book
     WHERE id = p_book_id AND is_active = 1
       FOR SHARE;
    IF v_stock IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'BOOK_NOT_FOUND';
    END IF;
    IF v_stock <= 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'OUT_OF_STOCK';
    END IF;

    SELECT quantity INTO v_old
      FROM orders_cartitem
     WHERE cart_id = v_cart_id AND book_id = p_book_id;

    IF v_old IS NULL THEN
        SELECT COUNT(*) INTO v_items FROM orders_cartitem WHERE cart_id = v_cart_id;
        IF v_items >= 30 THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'CART_FULL';
        END IF;
        INSERT INTO orders_cartitem (cart_id, book_id, quantity)
        VALUES (v_cart_id, p_book_id, p_quantity);
        SET p_new_quantity = p_quantity;
    ELSE
        IF v_old + p_quantity > 5 THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'CART_LIMIT';
        END IF;
        UPDATE orders_cartitem
           SET quantity = v_old + p_quantity
         WHERE cart_id = v_cart_id AND book_id = p_book_id;
        SET p_new_quantity = v_old + p_quantity;
    END IF;

    UPDATE orders_cart SET updated_at = CURRENT_TIMESTAMP(6) WHERE id = v_cart_id;

    COMMIT;
END$$

DELIMITER ;
