-- =====================================================================
-- Giỏ hàng của khách (orders_cart, orders_cartitem).
--
--   sp_cart_add           thêm sách vào giỏ; sách đã có thì cộng thêm số lượng
--   sp_cart_list          đọc giỏ của khách (trang /orders/cart/)
--   sp_cart_set_quantity  đặt số lượng mới cho một sách trong giỏ (nút + / −)
--   sp_cart_remove        gỡ một sách khỏi giỏ
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
--   NOT_IN_CART     sách không có trong giỏ của khách này
--   BOOK_UNAVAILABLE sách trong giỏ đã bị ẩn (ngừng bán) – chỉ còn gỡ được
--
-- Trang giỏ hàng (chốt 2026-11-15):
--   - Tăng/giảm dùng chung sp_cart_set_quantity nhận SỐ LƯỢNG CUỐI CÙNG (1–5),
--     không nhận "+1": bấm đúp, hai tab, gửi lại form vẫn ra đúng con số đó.
--   - Đang 1 cuốn thì nút "−" bị khóa; bỏ sách phải bấm Gỡ (sp_cart_remove),
--     không hỏi xác nhận.
--   - Sách bị ẩn: hiện mờ "Ngừng bán", chỉ gỡ được (BOOK_UNAVAILABLE).
--     Sách hết hàng: hiện mờ "Hết hàng", không tăng được (OUT_OF_STOCK);
--     giảm vẫn cho vì vô hại. Hai loại này không tính vào "Tạm tính".
--   - sp_cart_list trả in_stock (0/1), không trả số tồn kho.
--   - Sách không có trong giỏ → NOT_IN_CART dù sách có tồn tại hay không,
--     nên không dò được sách ẩn qua các thủ tục này.
--
-- Root tạo bằng `python manage.py db_apply`. Chạy lại nhiều lần được.
-- =====================================================================

DROP PROCEDURE IF EXISTS sp_cart_add;
DROP PROCEDURE IF EXISTS sp_cart_list;
DROP PROCEDURE IF EXISTS sp_cart_set_quantity;
DROP PROCEDURE IF EXISTS sp_cart_remove;

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

-- AI-TRACE#238 | Claude Opus 5.5 | Thủ tục đọc giỏ của khách: sách, giá hiện tại, số lượng, tình trạng còn bán/còn hàng, không trả số tồn kho | CẤM XÓA CHÚ THÍCH NÀY
CREATE DEFINER = 'bookstore_definer'@'localhost' PROCEDURE sp_cart_list(
    IN p_user_id  BIGINT
)
SQL SECURITY DEFINER
READS SQL DATA
BEGIN
    DECLARE v_customer INT DEFAULT 0;

    IF p_user_id IS NULL OR p_user_id <= 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'INVALID_INPUT';
    END IF;

    SELECT COUNT(*) INTO v_customer
      FROM accounts_user
     WHERE id = p_user_id AND is_active = 1 AND is_staff = 0 AND email_verified = 1;
    IF v_customer = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'NOT_CUSTOMER';
    END IF;

    SELECT b.id, b.title, b.author, b.cover_image, b.price, i.quantity,
           b.is_active, (b.stock > 0) AS in_stock
      FROM orders_cart c
      JOIN orders_cartitem i ON i.cart_id = c.id
      JOIN catalog_book b    ON b.id = i.book_id
     WHERE c.user_id = p_user_id
     ORDER BY i.added_at, i.id
     LIMIT 30;
END$$

-- AI-TRACE#239 | Claude Opus 5.5 | Thủ tục đặt số lượng mới (1–5) cho sách trong giỏ: dùng cho cả tăng và giảm, khóa giỏ chống bấm trùng, sách ẩn không đổi được, hết hàng không tăng được | CẤM XÓA CHÚ THÍCH NÀY
CREATE DEFINER = 'bookstore_definer'@'localhost' PROCEDURE sp_cart_set_quantity(
    IN p_user_id   BIGINT,
    IN p_book_id   BIGINT,
    IN p_quantity  INT
)
SQL SECURITY DEFINER
MODIFIES SQL DATA
BEGIN
    DECLARE v_customer INT DEFAULT 0;
    DECLARE v_cart_id  BIGINT DEFAULT NULL;
    DECLARE v_old      INT DEFAULT NULL;
    DECLARE v_active   TINYINT DEFAULT NULL;
    DECLARE v_stock    INT DEFAULT NULL;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

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

    SELECT id INTO v_cart_id FROM orders_cart WHERE user_id = p_user_id FOR UPDATE;
    IF v_cart_id IS NOT NULL THEN
        SELECT quantity INTO v_old
          FROM orders_cartitem
         WHERE cart_id = v_cart_id AND book_id = p_book_id;
    END IF;
    IF v_old IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'NOT_IN_CART';
    END IF;

    SELECT is_active, stock INTO v_active, v_stock
      FROM catalog_book
     WHERE id = p_book_id
       FOR SHARE;
    IF v_active IS NULL OR v_active <> 1 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'BOOK_UNAVAILABLE';
    END IF;
    IF p_quantity > v_old AND v_stock <= 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'OUT_OF_STOCK';
    END IF;

    IF p_quantity <> v_old THEN
        UPDATE orders_cartitem
           SET quantity = p_quantity
         WHERE cart_id = v_cart_id AND book_id = p_book_id;
        UPDATE orders_cart SET updated_at = CURRENT_TIMESTAMP(6) WHERE id = v_cart_id;
    END IF;

    COMMIT;
END$$

-- AI-TRACE#240 | Claude Opus 5.5 | Thủ tục gỡ một sách khỏi giỏ của khách; gỡ được cả sách đã ngừng bán hoặc hết hàng | CẤM XÓA CHÚ THÍCH NÀY
CREATE DEFINER = 'bookstore_definer'@'localhost' PROCEDURE sp_cart_remove(
    IN p_user_id  BIGINT,
    IN p_book_id  BIGINT
)
SQL SECURITY DEFINER
MODIFIES SQL DATA
BEGIN
    DECLARE v_customer INT DEFAULT 0;
    DECLARE v_cart_id  BIGINT DEFAULT NULL;
    DECLARE v_deleted  INT DEFAULT 0;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    IF p_user_id IS NULL OR p_user_id <= 0 OR p_book_id IS NULL OR p_book_id <= 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'INVALID_INPUT';
    END IF;

    SELECT COUNT(*) INTO v_customer
      FROM accounts_user
     WHERE id = p_user_id AND is_active = 1 AND is_staff = 0 AND email_verified = 1;
    IF v_customer = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'NOT_CUSTOMER';
    END IF;

    START TRANSACTION;

    SELECT id INTO v_cart_id FROM orders_cart WHERE user_id = p_user_id FOR UPDATE;
    IF v_cart_id IS NOT NULL THEN
        DELETE FROM orders_cartitem WHERE cart_id = v_cart_id AND book_id = p_book_id;
        SET v_deleted = ROW_COUNT();
    END IF;
    IF v_deleted = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'NOT_IN_CART';
    END IF;

    UPDATE orders_cart SET updated_at = CURRENT_TIMESTAMP(6) WHERE id = v_cart_id;

    COMMIT;
END$$

DELIMITER ;
