-- =====================================================================
-- sp_place_order: biến giỏ hàng của một người dùng thành đơn hàng.
--
-- Đây là NƠI DUY NHẤT được tạo đơn và trừ kho. app_customer chỉ có quyền
-- EXECUTE trên thủ tục này, không có quyền nào trên các bảng nó đụng tới
-- (quyền tối thiểu, chương 6.2). Thủ tục chạy bằng quyền của
-- bookstore_definer (SQL SECURITY DEFINER, tài khoản khóa đăng nhập).
--
-- Chống race condition (SECURITY_CHECKLIST mục 6):
--   1. Khóa dòng giỏ của người dùng (FOR UPDATE): hai lần bấm của CÙNG một
--      người phải xếp hàng, lần sau thấy đơn đã có thì trả lại mã cũ.
--   2. Khóa các dòng sách trong giỏ (FOR UPDATE): hai người KHÁC nhau cùng
--      mua cuốn cuối thì người đến sau phải chờ, rồi nhận OUT_OF_STOCK.
--   Thứ tự khóa sách: InnoDB khóa dòng theo thứ tự nó đọc. Câu khóa đi từ
--   orders_cartitem theo chỉ mục UNIQUE (cart_id, book_id) nên đọc sách theo
--   book_id tăng dần (STRAIGHT_JOIN giữ đúng thứ tự bảng). Mọi giao dịch
--   khóa theo cùng một thứ tự → không có vòng chờ → không deadlock.
--
-- Tham số:
--   p_user_id           id người dùng, Django lấy từ request.user (KHÔNG từ form)
--   p_idempotency_key   32 ký tự hex thường, Django sinh khi mở trang đặt hàng
--   p_shipping_name     tên người nhận, 1–100 ký tự (tham số khai báo 255 để
--                       chuỗi dài quá vẫn vào được thủ tục và nhận INVALID_INPUT)
--   p_phone_encrypted   SĐT đã mã hóa AES-GCM ở Django
--   p_address_encrypted địa chỉ đã mã hóa AES-GCM ở Django
--   p_order_code (OUT)  mã đơn (32 ký tự hex)
--   p_created    (OUT)  1 = đơn mới tạo, 0 = bấm lại, trả mã đơn cũ
--
-- Lỗi (SIGNAL SQLSTATE '45000', MESSAGE_TEXT là đúng 1 trong 4 mã):
--   INVALID_INPUT  tham số sai, hoặc mã yêu cầu đã thuộc người khác
--   CART_EMPTY     giỏ rỗng hoặc chưa có giỏ
--   BOOK_INACTIVE  có sách đã ngừng bán
--   OUT_OF_STOCK   có sách không đủ số lượng
-- Lỗi ở bất kỳ bước nào: ROLLBACK, không có đơn dở dang, kho và giỏ giữ nguyên.
--
-- Root tạo thủ tục bằng `python manage.py db_apply`. Chạy lại nhiều lần được.
-- =====================================================================

DROP PROCEDURE IF EXISTS sp_place_order;

DELIMITER $$

-- AI-TRACE#001 | Claude Opus 5.5 | Thủ tục đặt đơn: khóa giỏ và sách, kiểm tra kho, tạo đơn, trừ kho | CẤM XÓA CHÚ THÍCH NÀY
CREATE DEFINER = 'bookstore_definer'@'localhost' PROCEDURE sp_place_order(
    IN  p_user_id           BIGINT,
    IN  p_idempotency_key   CHAR(32),
    IN  p_shipping_name     VARCHAR(255),
    IN  p_phone_encrypted   VARCHAR(512),
    IN  p_address_encrypted VARCHAR(1024),
    OUT p_order_code        CHAR(32),
    OUT p_created           TINYINT
)
SQL SECURITY DEFINER
MODIFIES SQL DATA
proc: BEGIN
    -- Phí ship cố định (chốt 2026-11-14)
    DECLARE c_shipping_fee   INT UNSIGNED DEFAULT 30000;

    DECLARE v_now            DATETIME(6);
    DECLARE v_cart_id        BIGINT DEFAULT NULL;
    DECLARE v_existing_code  CHAR(32) DEFAULT NULL;
    DECLARE v_existing_user  BIGINT DEFAULT NULL;
    DECLARE v_line_count     INT DEFAULT 0;
    DECLARE v_inactive_count INT DEFAULT 0;
    DECLARE v_short_count    INT DEFAULT 0;
    DECLARE v_subtotal       BIGINT DEFAULT 0;
    DECLARE v_order_id       BIGINT;
    DECLARE v_code           CHAR(32);

    -- Bước 1: lỗi ở đâu cũng hủy toàn bộ giao dịch rồi báo lỗi ra ngoài
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    SET p_order_code = NULL;
    SET p_created = 0;

    -- Bước 2: kiểm tra tham số trước khi đụng vào dữ liệu.
    -- REGEXP_LIKE(..., 'c') so khớp phân biệt hoa/thường (collation của CSDL
    -- không phân biệt, nên REGEXP thường sẽ nhận cả 'ABC...').
    IF p_user_id IS NULL OR p_user_id <= 0
       OR p_idempotency_key IS NULL
       OR NOT REGEXP_LIKE(p_idempotency_key, '^[0-9a-f]{32}$', 'c')
       OR p_shipping_name IS NULL
       OR CHAR_LENGTH(TRIM(p_shipping_name)) = 0
       OR CHAR_LENGTH(p_shipping_name) > 100
       OR p_phone_encrypted IS NULL OR CHAR_LENGTH(p_phone_encrypted) = 0
       OR p_address_encrypted IS NULL OR CHAR_LENGTH(p_address_encrypted) = 0
    THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'INVALID_INPUT';
    END IF;

    SET v_now = UTC_TIMESTAMP(6);

    -- Bước 3: mở giao dịch
    START TRANSACTION;

    -- Bước 4: khóa giỏ của người dùng. Lần bấm thứ hai của cùng người này
    -- đứng chờ ở đây cho tới khi lần đầu COMMIT.
    SELECT id INTO v_cart_id
      FROM orders_cart
     WHERE user_id = p_user_id
       FOR UPDATE;

    -- Bước 5: mã yêu cầu đã có đơn → bấm lại, trả mã đơn cũ
    SELECT code, user_id INTO v_existing_code, v_existing_user
      FROM orders_order
     WHERE idempotency_key = p_idempotency_key;

    IF v_existing_code IS NOT NULL THEN
        IF v_existing_user <> p_user_id THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'INVALID_INPUT';
        END IF;
        SET p_order_code = v_existing_code;
        SET p_created = 0;
        COMMIT;
        LEAVE proc;
    END IF;

    IF v_cart_id IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'CART_EMPTY';
    END IF;

    -- Bước 6: khóa các dòng sách trong giỏ và tính toán trong cùng một câu.
    -- Giá lấy từ catalog_book, không bao giờ từ phía người dùng.
    SELECT COUNT(*),
           COALESCE(SUM(b.is_active = 0), 0),
           COALESCE(SUM(b.stock < ci.quantity), 0),
           COALESCE(SUM(b.price * ci.quantity), 0)
      INTO v_line_count, v_inactive_count, v_short_count, v_subtotal
      FROM orders_cartitem ci
      STRAIGHT_JOIN catalog_book b ON b.id = ci.book_id
     WHERE ci.cart_id = v_cart_id
       FOR UPDATE;

    -- Bước 7: kiểm tra giỏ
    IF v_line_count = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'CART_EMPTY';
    END IF;
    IF v_inactive_count > 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'BOOK_INACTIVE';
    END IF;
    IF v_short_count > 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'OUT_OF_STOCK';
    END IF;

    -- Bước 8: tạo đơn. Mã đơn ngẫu nhiên mật mã (RANDOM_BYTES), không dùng
    -- UUID() vì UUID sinh theo thời gian nên đoán được.
    SET v_code = LOWER(HEX(RANDOM_BYTES(16)));

    INSERT INTO orders_order (
        code, user_id, status, subtotal, shipping_fee, total,
        shipping_name, shipping_phone_encrypted, shipping_address_encrypted,
        idempotency_key, created_at, updated_at, expires_at
    ) VALUES (
        v_code, p_user_id, 'pending', v_subtotal, c_shipping_fee, v_subtotal + c_shipping_fee,
        TRIM(p_shipping_name), p_phone_encrypted, p_address_encrypted,
        p_idempotency_key, v_now, v_now, v_now + INTERVAL 15 MINUTE
    );
    SET v_order_id = LAST_INSERT_ID();

    -- Bước 9: chép giỏ sang chi tiết đơn (tên sách, giá lúc đặt)
    INSERT INTO orders_orderitem (order_id, book_id, book_title, unit_price, quantity)
    SELECT v_order_id, b.id, b.title, b.price, ci.quantity
      FROM orders_cartitem ci
      JOIN catalog_book b ON b.id = ci.book_id
     WHERE ci.cart_id = v_cart_id;

    -- Bước 10: trừ kho, xóa giỏ, chốt giao dịch
    UPDATE catalog_book b
      JOIN orders_cartitem ci ON ci.book_id = b.id
       SET b.stock = b.stock - ci.quantity
     WHERE ci.cart_id = v_cart_id;

    DELETE FROM orders_cartitem WHERE cart_id = v_cart_id;

    SET p_order_code = v_code;
    SET p_created = 1;
    COMMIT;
END proc$$

DELIMITER ;
