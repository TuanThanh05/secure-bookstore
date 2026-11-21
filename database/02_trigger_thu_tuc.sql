-- Phần 10: Trigger bảo vệ bảng tài khoản (chặn leo thang đặc quyền)

DROP TRIGGER IF EXISTS trg_user_guard_insert;
DROP TRIGGER IF EXISTS trg_user_guard_update;

DELIMITER $$

CREATE DEFINER = 'bookstore_definer'@'localhost'
TRIGGER trg_user_guard_insert
BEFORE INSERT ON accounts_user
FOR EACH ROW
BEGIN
    IF SUBSTRING_INDEX(USER(), '@', 1) IN ('app_customer', 'app_auth')
       AND (NEW.is_staff <> 0 OR NEW.is_superuser <> 0) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'tai khoan ung dung khong duoc tao tai khoan nhan vien/quan tri';
    END IF;
END$$

CREATE DEFINER = 'bookstore_definer'@'localhost'
TRIGGER trg_user_guard_update
BEFORE UPDATE ON accounts_user
FOR EACH ROW
BEGIN
    IF SUBSTRING_INDEX(USER(), '@', 1) IN ('app_customer', 'app_auth') THEN
        IF NEW.is_staff <> OLD.is_staff OR NEW.is_superuser <> OLD.is_superuser THEN
            SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'tai khoan ung dung khong duoc thay doi is_staff/is_superuser';
        END IF;
        IF OLD.is_staff = 1 AND NOT (
               NEW.id <=> OLD.id AND NEW.password <=> OLD.password
           AND NEW.username <=> OLD.username AND NEW.email <=> OLD.email
           AND NEW.first_name <=> OLD.first_name AND NEW.last_name <=> OLD.last_name
           AND NEW.is_active <=> OLD.is_active AND NEW.date_joined <=> OLD.date_joined
           AND NEW.phone_encrypted <=> OLD.phone_encrypted
           AND NEW.email_verified <=> OLD.email_verified) THEN
            SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'tai khoan ung dung chi duoc cap nhat last_login cua nhan vien';
        END IF;
        IF OLD.is_staff = 0 AND NOT (
               NEW.id <=> OLD.id AND NEW.username <=> OLD.username
           AND NEW.email <=> OLD.email AND NEW.is_active <=> OLD.is_active
           AND NEW.email_verified <=> OLD.email_verified
           AND NEW.date_joined <=> OLD.date_joined) THEN
            SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'tai khoan ung dung khong duoc doi trang thai, email, ten dang nhap cua khach';
        END IF;
    END IF;
    IF SUBSTRING_INDEX(USER(), '@', 1) = 'app_auth'
       AND NOT (NEW.auto_locked_until <=> OLD.auto_locked_until) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'app_auth khong duoc doi khoa tu dong (auto_locked_until)';
    END IF;
    IF SUBSTRING_INDEX(USER(), '@', 1) = 'app_staff' AND OLD.is_staff <> 1 AND NOT (
           NEW.id <=> OLD.id AND NEW.password <=> OLD.password
       AND NEW.username <=> OLD.username AND NEW.email <=> OLD.email
       AND NEW.first_name <=> OLD.first_name AND NEW.last_name <=> OLD.last_name
       AND NEW.is_staff <=> OLD.is_staff AND NEW.is_superuser <=> OLD.is_superuser
       AND NEW.date_joined <=> OLD.date_joined AND NEW.last_login <=> OLD.last_login
       AND NEW.phone_encrypted <=> OLD.phone_encrypted
       AND NEW.email_verified <=> OLD.email_verified) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'app_staff khong duoc sua thong tin cua khach hang';
    END IF;
END$$

DELIMITER ;


-- Phần 11: Trigger ghi lịch sử mật khẩu

DROP TRIGGER IF EXISTS trg_pwhist_after_insert;
DROP TRIGGER IF EXISTS trg_pwhist_after_update;

DELIMITER $$

CREATE DEFINER = 'bookstore_definer'@'localhost'
TRIGGER trg_pwhist_after_insert
AFTER INSERT ON accounts_user
FOR EACH ROW
BEGIN
    IF NEW.password IS NOT NULL AND NEW.password <> '' AND LEFT(NEW.password, 1) <> '!' THEN
        INSERT INTO accounts_passwordhistory (user_id, password_hash)
        VALUES (NEW.id, NEW.password);
    END IF;
END$$

CREATE DEFINER = 'bookstore_definer'@'localhost'
TRIGGER trg_pwhist_after_update
AFTER UPDATE ON accounts_user
FOR EACH ROW
BEGIN
    DECLARE v_cut_id BIGINT DEFAULT NULL;

    IF NOT (NEW.password <=> OLD.password)
       AND NEW.password IS NOT NULL AND NEW.password <> '' AND LEFT(NEW.password, 1) <> '!' THEN

        INSERT INTO accounts_passwordhistory (user_id, password_hash)
        VALUES (NEW.id, NEW.password);

        SELECT id INTO v_cut_id
          FROM accounts_passwordhistory
         WHERE user_id = NEW.id
         ORDER BY id DESC
         LIMIT 1 OFFSET 4;

        IF v_cut_id IS NOT NULL THEN
            DELETE FROM accounts_passwordhistory
             WHERE user_id = NEW.id AND id < v_cut_id;
        END IF;
    END IF;
END$$

DELIMITER ;


-- Phần 12: Trigger bảo vệ xác thực 2 bước của nhân viên

DROP TRIGGER IF EXISTS trg_totp_guard_insert;
DROP TRIGGER IF EXISTS trg_totp_guard_update;
DROP TRIGGER IF EXISTS trg_totp_guard_delete;
DROP TRIGGER IF EXISTS trg_recovery_guard_insert;
DROP TRIGGER IF EXISTS trg_recovery_guard_update;
DROP TRIGGER IF EXISTS trg_recovery_guard_delete;

DELIMITER $$

CREATE DEFINER = 'bookstore_definer'@'localhost'
TRIGGER trg_totp_guard_insert BEFORE INSERT ON accounts_totpdevice
FOR EACH ROW
BEGIN
    IF SUBSTRING_INDEX(USER(), '@', 1) IN ('app_customer', 'app_auth')
       AND EXISTS (SELECT 1 FROM accounts_user WHERE id = NEW.user_id AND (is_staff <> 0 OR is_superuser <> 0)) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'tai khoan ung dung khong duoc cai 2 buoc cho nhan vien';
    END IF;
END$$

CREATE DEFINER = 'bookstore_definer'@'localhost'
TRIGGER trg_totp_guard_update BEFORE UPDATE ON accounts_totpdevice
FOR EACH ROW
BEGIN
    IF SUBSTRING_INDEX(USER(), '@', 1) IN ('app_customer', 'app_auth') THEN
        IF OLD.last_used_step IS NOT NULL
           AND (NEW.last_used_step IS NULL OR NEW.last_used_step < OLD.last_used_step) THEN
            SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'khong duoc lui buoc thoi gian cua ma 2 buoc';
        END IF;
        IF EXISTS (SELECT 1 FROM accounts_user WHERE id = OLD.user_id AND (is_staff <> 0 OR is_superuser <> 0))
           AND NOT (NEW.id <=> OLD.id AND NEW.user_id <=> OLD.user_id
                AND NEW.secret_encrypted <=> OLD.secret_encrypted
                AND NEW.confirmed_at <=> OLD.confirmed_at
                AND NEW.created_at <=> OLD.created_at) THEN
            SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'tai khoan ung dung chi duoc ghi buoc thoi gian cho 2 buoc cua nhan vien';
        END IF;
    END IF;
END$$

CREATE DEFINER = 'bookstore_definer'@'localhost'
TRIGGER trg_totp_guard_delete BEFORE DELETE ON accounts_totpdevice
FOR EACH ROW
BEGIN
    IF SUBSTRING_INDEX(USER(), '@', 1) IN ('app_customer', 'app_auth')
       AND EXISTS (SELECT 1 FROM accounts_user WHERE id = OLD.user_id AND (is_staff <> 0 OR is_superuser <> 0)) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'tai khoan ung dung khong duoc go 2 buoc cua nhan vien';
    END IF;
END$$

CREATE DEFINER = 'bookstore_definer'@'localhost'
TRIGGER trg_recovery_guard_insert BEFORE INSERT ON accounts_recoverycode
FOR EACH ROW
BEGIN
    IF SUBSTRING_INDEX(USER(), '@', 1) IN ('app_customer', 'app_auth')
       AND EXISTS (SELECT 1 FROM accounts_user WHERE id = NEW.user_id AND (is_staff <> 0 OR is_superuser <> 0)) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'nhan vien khong co ma du phong';
    END IF;
END$$

CREATE DEFINER = 'bookstore_definer'@'localhost'
TRIGGER trg_recovery_guard_update BEFORE UPDATE ON accounts_recoverycode
FOR EACH ROW
BEGIN
    IF SUBSTRING_INDEX(USER(), '@', 1) IN ('app_customer', 'app_auth') THEN
        IF EXISTS (SELECT 1 FROM accounts_user WHERE id = OLD.user_id AND (is_staff <> 0 OR is_superuser <> 0)) THEN
            SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'nhan vien khong co ma du phong';
        END IF;
        -- Mã dự phòng chỉ đi một chiều: chưa dùng -> đã dùng; không đổi mã, không "hồi sinh" mã đã dùng
        IF NOT (NEW.id <=> OLD.id AND NEW.user_id <=> OLD.user_id AND NEW.code_hash <=> OLD.code_hash
                AND NEW.created_at <=> OLD.created_at)
           OR (OLD.used_at IS NOT NULL AND NOT (NEW.used_at <=> OLD.used_at)) THEN
            SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'ma du phong chi duoc danh dau da dung mot lan';
        END IF;
    END IF;
END$$

CREATE DEFINER = 'bookstore_definer'@'localhost'
TRIGGER trg_recovery_guard_delete BEFORE DELETE ON accounts_recoverycode
FOR EACH ROW
BEGIN
    IF SUBSTRING_INDEX(USER(), '@', 1) IN ('app_customer', 'app_auth')
       AND EXISTS (SELECT 1 FROM accounts_user WHERE id = OLD.user_id AND (is_staff <> 0 OR is_superuser <> 0)) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'nhan vien khong co ma du phong';
    END IF;
END$$

DELIMITER ;


-- Phần 20: Thủ tục đọc danh mục sách cho khách

DROP VIEW IF EXISTS v_public_books;
DROP VIEW IF EXISTS v_public_categories;
DROP PROCEDURE IF EXISTS sp_public_category_list;
DROP PROCEDURE IF EXISTS sp_public_book_list;
DROP PROCEDURE IF EXISTS sp_public_book_get;

DELIMITER $$

CREATE DEFINER = 'bookstore_definer'@'localhost' PROCEDURE sp_public_category_list()
SQL SECURITY DEFINER
READS SQL DATA
BEGIN
    SELECT id, name, slug
      FROM catalog_category
     ORDER BY name;
END$$

CREATE DEFINER = 'bookstore_definer'@'localhost' PROCEDURE sp_public_book_list(
    IN p_category_id  BIGINT,
    IN p_query        VARCHAR(255)
)
SQL SECURITY DEFINER
READS SQL DATA
BEGIN
    DECLARE v_query   VARCHAR(255) DEFAULT NULL;
    DECLARE v_pattern VARCHAR(400) DEFAULT NULL;

    IF p_category_id IS NOT NULL AND p_category_id <= 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'INVALID_INPUT';
    END IF;

    SET v_query = NULLIF(TRIM(p_query), '');
    IF v_query IS NOT NULL THEN
        IF CHAR_LENGTH(v_query) > 100 THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'INVALID_INPUT';
        END IF;
        -- Thoát \ trước, rồi % và _, để LIKE coi chúng là chữ thường
        SET v_pattern = CONCAT('%',
            REPLACE(REPLACE(REPLACE(v_query, '\\', '\\\\'), '%', '\\%'), '_', '\\_'),
            '%');
    END IF;

    SELECT b.id,
           b.title,
           b.author,
           b.isbn,
           b.category_id,
           b.description,
           b.price,
           b.cover_image,
           b.created_at,
           (b.stock > 0)            AS in_stock,
           ROUND(AVG(r.rating), 1)  AS rating,
           COUNT(r.id)              AS review_count
      FROM catalog_book b
      LEFT JOIN catalog_review r
             ON r.book_id = b.id AND r.is_visible = 1
     WHERE b.is_active = 1
       AND (p_category_id IS NULL OR b.category_id = p_category_id)
       AND (v_pattern IS NULL
            OR b.title  LIKE v_pattern ESCAPE '\\'
            OR b.author LIKE v_pattern ESCAPE '\\')
     GROUP BY b.id
     ORDER BY b.created_at DESC, b.id DESC
     LIMIT 200;
END$$

CREATE DEFINER = 'bookstore_definer'@'localhost' PROCEDURE sp_public_book_get(
    IN p_book_id  BIGINT
)
SQL SECURITY DEFINER
READS SQL DATA
BEGIN
    IF p_book_id IS NULL OR p_book_id <= 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'INVALID_INPUT';
    END IF;

    SELECT b.id,
           b.title,
           b.author,
           b.isbn,
           b.category_id,
           b.description,
           b.price,
           b.cover_image,
           b.created_at,
           (b.stock > 0)            AS in_stock,
           ROUND(AVG(r.rating), 1)  AS rating,
           COUNT(r.id)              AS review_count,
           c.name                   AS category_name
      FROM catalog_book b
      JOIN catalog_category c ON c.id = b.category_id
      LEFT JOIN catalog_review r
             ON r.book_id = b.id AND r.is_visible = 1
     WHERE b.id = p_book_id AND b.is_active = 1
     GROUP BY b.id, c.name;
END$$

DELIMITER ;


-- Phần 21: Thủ tục đánh giá sách

DROP PROCEDURE IF EXISTS sp_review_save;
DROP PROCEDURE IF EXISTS sp_review_get_mine;
DROP PROCEDURE IF EXISTS sp_review_can_write;
DROP PROCEDURE IF EXISTS sp_review_list;

DELIMITER $$

CREATE DEFINER = 'bookstore_definer'@'localhost' PROCEDURE sp_review_save(
    IN  p_user_id  BIGINT,
    IN  p_book_id  BIGINT,
    IN  p_rating   INT,
    IN  p_content  VARCHAR(4000),
    OUT p_created  TINYINT
)
SQL SECURITY DEFINER
MODIFIES SQL DATA
BEGIN
    DECLARE v_content  VARCHAR(4000);
    DECLARE v_customer INT DEFAULT 0;
    DECLARE v_book     INT DEFAULT 0;
    DECLARE v_existed  INT DEFAULT 0;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    SET p_created = NULL;
    SET v_content = TRIM(p_content);

    IF p_user_id IS NULL OR p_user_id <= 0
       OR p_book_id IS NULL OR p_book_id <= 0
       OR p_rating IS NULL OR p_rating < 1 OR p_rating > 5
       OR v_content IS NULL OR CHAR_LENGTH(v_content) = 0 OR CHAR_LENGTH(v_content) > 2000
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

    -- Khóa chia sẻ dòng sách: admin không ẩn/xóa sách giữa chừng
    SELECT COUNT(*) INTO v_book
      FROM catalog_book
     WHERE id = p_book_id AND is_active = 1
       FOR SHARE;
    IF v_book = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'BOOK_NOT_FOUND';
    END IF;

    IF NOT EXISTS (
        SELECT 1
          FROM orders_orderitem i
          JOIN orders_order o ON o.id = i.order_id
         WHERE i.book_id = p_book_id AND o.user_id = p_user_id AND o.status = 'delivered'
    ) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'NOT_PURCHASED';
    END IF;

    SELECT COUNT(*) INTO v_existed
      FROM catalog_review
     WHERE user_id = p_user_id AND book_id = p_book_id;

    INSERT INTO catalog_review (user_id, book_id, rating, content)
    VALUES (p_user_id, p_book_id, p_rating, v_content) AS new_review
    ON DUPLICATE KEY UPDATE rating = new_review.rating, content = new_review.content;

    SET p_created = IF(v_existed = 0, 1, 0);

    COMMIT;
END$$

CREATE DEFINER = 'bookstore_definer'@'localhost' PROCEDURE sp_review_get_mine(
    IN p_user_id  BIGINT,
    IN p_book_id  BIGINT
)
SQL SECURITY DEFINER
READS SQL DATA
BEGIN
    IF p_user_id IS NULL OR p_user_id <= 0 OR p_book_id IS NULL OR p_book_id <= 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'INVALID_INPUT';
    END IF;

    SELECT rating, content, is_visible, created_at, updated_at
      FROM catalog_review
     WHERE user_id = p_user_id AND book_id = p_book_id;
END$$

CREATE DEFINER = 'bookstore_definer'@'localhost' PROCEDURE sp_review_can_write(
    IN p_user_id  BIGINT,
    IN p_book_id  BIGINT
)
SQL SECURITY DEFINER
READS SQL DATA
BEGIN
    IF p_user_id IS NULL OR p_user_id <= 0 OR p_book_id IS NULL OR p_book_id <= 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'INVALID_INPUT';
    END IF;

    SELECT EXISTS (
               SELECT 1
                 FROM accounts_user u
                 JOIN orders_order o ON o.user_id = u.id
                 JOIN orders_orderitem i ON i.order_id = o.id
                 JOIN catalog_book b ON b.id = i.book_id
                WHERE u.id = p_user_id AND u.is_active = 1 AND u.is_staff = 0 AND u.email_verified = 1
                  AND i.book_id = p_book_id AND b.is_active = 1 AND o.status = 'delivered'
           ) AS can_write;
END$$

CREATE DEFINER = 'bookstore_definer'@'localhost' PROCEDURE sp_review_list(
    IN p_book_id  BIGINT
)
SQL SECURITY DEFINER
READS SQL DATA
BEGIN
    IF p_book_id IS NULL OR p_book_id <= 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'INVALID_INPUT';
    END IF;

    SELECT CASE
               WHEN CHAR_LENGTH(u.username) <= 1 THEN '*'
               WHEN CHAR_LENGTH(u.username) = 2 THEN CONCAT(LEFT(u.username, 1), '*')
               ELSE CONCAT(LEFT(u.username, 1),
                           REPEAT('*', CHAR_LENGTH(u.username) - 2),
                           RIGHT(u.username, 1))
           END              AS display_name,
           r.rating,
           r.content,
           r.created_at,
           r.updated_at
      FROM catalog_review r
      JOIN catalog_book b  ON b.id = r.book_id AND b.is_active = 1
      JOIN accounts_user u ON u.id = r.user_id
     WHERE r.book_id = p_book_id AND r.is_visible = 1
     ORDER BY r.created_at DESC, r.id DESC
     LIMIT 50;
END$$

DELIMITER ;


-- Phần 30: Thủ tục đặt hàng sp_place_order

DROP PROCEDURE IF EXISTS sp_place_order;
DROP PROCEDURE IF EXISTS sp_order_get;

DELIMITER $$

CREATE DEFINER = 'bookstore_definer'@'localhost' PROCEDURE sp_place_order(
    IN  p_user_id           BIGINT,
    IN  p_idempotency_key   CHAR(32),
    IN  p_shipping_name     VARCHAR(255),
    IN  p_phone_encrypted   VARCHAR(512),
    IN  p_address_encrypted VARCHAR(1024),
    IN  p_hold_minutes      INT,
    IN  p_max_items         INT,
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
    DECLARE v_customer       INT DEFAULT 0;
    DECLARE v_pending_count  INT DEFAULT 0;
    DECLARE v_item_total     BIGINT DEFAULT 0;
    DECLARE v_locked_until   DATETIME(6) DEFAULT NULL;

    -- Bước 1: lỗi ở đâu cũng hủy toàn bộ giao dịch rồi báo lỗi ra ngoài
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    SET p_order_code = NULL;
    SET p_created = 0;

    IF p_user_id IS NULL OR p_user_id <= 0
       OR p_idempotency_key IS NULL
       OR NOT REGEXP_LIKE(p_idempotency_key, '^[0-9a-f]{32}$', 'c')
       OR p_shipping_name IS NULL
       OR CHAR_LENGTH(TRIM(p_shipping_name)) = 0
       OR CHAR_LENGTH(p_shipping_name) > 100
       OR p_phone_encrypted IS NULL OR CHAR_LENGTH(p_phone_encrypted) = 0
       OR p_address_encrypted IS NULL OR CHAR_LENGTH(p_address_encrypted) = 0
       OR p_hold_minutes IS NULL OR p_hold_minutes < 1 OR p_hold_minutes > 60
       OR p_max_items IS NULL OR p_max_items < 1 OR p_max_items > 150
    THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'INVALID_INPUT';
    END IF;

    SELECT COUNT(*) INTO v_customer
      FROM accounts_user
     WHERE id = p_user_id AND is_active = 1 AND is_staff = 0 AND email_verified = 1;
    IF v_customer = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'NOT_CUSTOMER';
    END IF;

    SET v_now = UTC_TIMESTAMP(6);

    SELECT auto_locked_until INTO v_locked_until FROM accounts_user WHERE id = p_user_id;
    IF v_locked_until IS NOT NULL AND v_locked_until > v_now THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ACCOUNT_LOCKED';
    END IF;

    -- Bước 3: mở giao dịch
    START TRANSACTION;

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

    SELECT COUNT(*) INTO v_pending_count
      FROM orders_order
     WHERE user_id = p_user_id AND status = 'pending' AND expires_at > v_now;
    IF v_pending_count > 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'PENDING_EXISTS';
    END IF;

    SELECT COUNT(*),
           COALESCE(SUM(b.is_active = 0), 0),
           COALESCE(SUM(b.stock < ci.quantity), 0),
           COALESCE(SUM(b.price * ci.quantity), 0),
           COALESCE(SUM(ci.quantity), 0)
      INTO v_line_count, v_inactive_count, v_short_count, v_subtotal, v_item_total
      FROM orders_cartitem ci
      STRAIGHT_JOIN catalog_book b ON b.id = ci.book_id
     WHERE ci.cart_id = v_cart_id
       FOR UPDATE;

    -- Bước 7: kiểm tra giỏ
    IF v_line_count = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'CART_EMPTY';
    END IF;
    IF v_item_total > p_max_items THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ORDER_TOO_LARGE';
    END IF;
    IF v_inactive_count > 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'BOOK_INACTIVE';
    END IF;
    IF v_short_count > 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'OUT_OF_STOCK';
    END IF;

    SET v_code = LOWER(HEX(RANDOM_BYTES(16)));

    INSERT INTO orders_order (
        code, user_id, status, subtotal, shipping_fee, total,
        shipping_name, shipping_phone_encrypted, shipping_address_encrypted,
        idempotency_key, created_at, updated_at, expires_at
    ) VALUES (
        v_code, p_user_id, 'pending', v_subtotal, c_shipping_fee, v_subtotal + c_shipping_fee,
        TRIM(p_shipping_name), p_phone_encrypted, p_address_encrypted,
        p_idempotency_key, v_now, v_now, v_now + INTERVAL p_hold_minutes MINUTE
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

CREATE DEFINER = 'bookstore_definer'@'localhost' PROCEDURE sp_order_get(
    IN p_user_id  BIGINT,
    IN p_code     VARCHAR(64)
)
SQL SECURITY DEFINER
READS SQL DATA
BEGIN
    DECLARE v_customer INT DEFAULT 0;
    DECLARE v_order_id BIGINT DEFAULT NULL;

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

    SELECT id INTO v_order_id
      FROM orders_order
     WHERE code = p_code AND user_id = p_user_id;
    IF v_order_id IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ORDER_NOT_FOUND';
    END IF;

    SELECT code, status, subtotal, shipping_fee, total, shipping_name,
           shipping_phone_encrypted, shipping_address_encrypted, idempotency_key,
           created_at, expires_at, paid_at, cancelled_at
      FROM orders_order
     WHERE id = v_order_id;

    SELECT book_id, book_title, unit_price, quantity
      FROM orders_orderitem
     WHERE order_id = v_order_id
     ORDER BY id;
END$$

DELIMITER ;


-- Phần 31: Thủ tục giỏ hàng

DROP PROCEDURE IF EXISTS sp_cart_add;
DROP PROCEDURE IF EXISTS sp_cart_list;
DROP PROCEDURE IF EXISTS sp_cart_set_quantity;
DROP PROCEDURE IF EXISTS sp_cart_remove;

DELIMITER $$

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


-- Phần 32: Trigger khóa đơn hàng đã tạo

DROP TRIGGER IF EXISTS trg_orderitem_guard_insert;
DROP TRIGGER IF EXISTS trg_orderitem_guard_update;
DROP TRIGGER IF EXISTS trg_orderitem_guard_delete;
DROP TRIGGER IF EXISTS trg_order_guard_update;
DROP TRIGGER IF EXISTS trg_order_guard_delete;

DELIMITER $$

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
        OR (OLD.status = 'paid'      AND NEW.status = 'confirmed')
        OR (OLD.status = 'confirmed' AND NEW.status = 'packed')
        OR (OLD.status = 'packed'    AND NEW.status = 'shipped')
        OR (OLD.status = 'shipped'   AND NEW.status = 'delivered')) THEN
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

CREATE DEFINER = 'bookstore_definer'@'localhost'
TRIGGER trg_order_guard_delete
BEFORE DELETE ON orders_order
FOR EACH ROW
BEGIN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ORDER_LOCKED';
END$$

DELIMITER ;


-- Phần 33: Thủ tục hủy đơn, hủy đơn quá hạn và Event

DROP EVENT IF EXISTS ev_cancel_expired_orders;
DROP PROCEDURE IF EXISTS sp_order_cancel;
DROP PROCEDURE IF EXISTS sp_order_expire_one;
DROP PROCEDURE IF EXISTS sp_cancel_expired_orders;
DROP PROCEDURE IF EXISTS sp_order_hold_check;

DELIMITER $$

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


-- Phần 34: Trigger ghi nhật ký đơn hàng

DROP TRIGGER IF EXISTS trg_order_audit_insert;
DROP TRIGGER IF EXISTS trg_order_audit_update;

DELIMITER $$

CREATE DEFINER = 'bookstore_definer'@'localhost'
TRIGGER trg_order_audit_insert
AFTER INSERT ON orders_order
FOR EACH ROW
BEGIN
    DECLARE v_account VARCHAR(100) DEFAULT SUBSTRING_INDEX(USER(), '@', 1);
    DECLARE v_source  VARCHAR(20)  DEFAULT CASE SUBSTRING_INDEX(USER(), '@', 1)
        WHEN 'app_customer' THEN 'customer'
        WHEN 'event_scheduler' THEN 'system'
        WHEN 'bookstore_definer' THEN 'system'
        WHEN 'app_payment' THEN 'payment'
        WHEN 'app_staff' THEN 'staff'
        ELSE 'other' END;

    INSERT INTO core_auditlog (table_name, record_id, action, old_value, new_value, db_user, app_user_id)
    VALUES ('orders_order', NEW.id, 'INSERT', NULL,
            JSON_OBJECT('code', NEW.code, 'status', NEW.status, 'total', NEW.total, 'source', v_source),
            USER(), IF(v_account = 'app_customer', NEW.user_id, NULL));
END$$

CREATE DEFINER = 'bookstore_definer'@'localhost'
TRIGGER trg_order_audit_update
AFTER UPDATE ON orders_order
FOR EACH ROW
BEGIN
    DECLARE v_account VARCHAR(100) DEFAULT SUBSTRING_INDEX(USER(), '@', 1);
    DECLARE v_source  VARCHAR(20)  DEFAULT CASE SUBSTRING_INDEX(USER(), '@', 1)
        WHEN 'app_customer' THEN 'customer'
        WHEN 'event_scheduler' THEN 'system'
        WHEN 'bookstore_definer' THEN 'system'
        WHEN 'app_payment' THEN 'payment'
        WHEN 'app_staff' THEN 'staff'
        ELSE 'other' END;

    IF NOT (NEW.status <=> OLD.status) THEN
        INSERT INTO core_auditlog (table_name, record_id, action, old_value, new_value, db_user, app_user_id)
        VALUES ('orders_order', NEW.id, 'UPDATE',
                JSON_OBJECT('status', OLD.status),
                JSON_OBJECT('code', NEW.code, 'status', NEW.status, 'source', v_source),
                USER(), CASE v_account
                            WHEN 'app_customer' THEN NEW.user_id
                            WHEN 'app_staff' THEN @bookstore_actor_id
                            ELSE NULL END);
    END IF;
END$$

DELIMITER ;


-- Phần 35: Thủ tục thanh toán mô phỏng

DROP PROCEDURE IF EXISTS sp_payment_simulate;
DROP TRIGGER IF EXISTS trg_payment_guard_update;
DROP TRIGGER IF EXISTS trg_payment_guard_delete;

DELIMITER $$

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


-- Phần 36: Thủ tục đọc đơn hàng của khách

DROP PROCEDURE IF EXISTS sp_order_list_mine;

DELIMITER $$

CREATE DEFINER = 'bookstore_definer'@'localhost' PROCEDURE sp_order_list_mine(
    IN p_user_id  BIGINT,
    IN p_group    VARCHAR(10),
    IN p_offset   INT,
    IN p_limit    INT
)
SQL SECURITY DEFINER
READS SQL DATA
BEGIN
    DECLARE v_customer INT DEFAULT 0;

    IF p_user_id IS NULL OR p_user_id <= 0
       OR p_group IS NULL OR p_group NOT IN ('active', 'history')
       OR p_offset IS NULL OR p_offset < 0 OR p_offset > 100000
       OR p_limit IS NULL OR p_limit < 1 OR p_limit > 50 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'INVALID_INPUT';
    END IF;

    SELECT COUNT(*) INTO v_customer
      FROM accounts_user
     WHERE id = p_user_id AND is_active = 1 AND is_staff = 0 AND email_verified = 1;
    IF v_customer = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'NOT_CUSTOMER';
    END IF;

    SELECT COUNT(*)
      FROM orders_order o
     WHERE o.user_id = p_user_id
       AND ((p_group = 'active'  AND o.status IN ('pending', 'paid', 'confirmed', 'packed', 'shipped'))
         OR (p_group = 'history' AND o.status IN ('delivered', 'cancelled')));

    SELECT o.code, o.status, o.total, o.created_at, o.expires_at, o.paid_at, o.cancelled_at,
           (SELECT COALESCE(SUM(i.quantity), 0) FROM orders_orderitem i WHERE i.order_id = o.id) AS item_count,
           (SELECT COUNT(*) FROM orders_orderitem i WHERE i.order_id = o.id) AS line_count,
           (SELECT i.book_title FROM orders_orderitem i WHERE i.order_id = o.id ORDER BY i.id LIMIT 1) AS first_title
      FROM orders_order o
     WHERE o.user_id = p_user_id
       AND ((p_group = 'active'  AND o.status IN ('pending', 'paid', 'confirmed', 'packed', 'shipped'))
         OR (p_group = 'history' AND o.status IN ('delivered', 'cancelled')))
     ORDER BY o.created_at DESC, o.id DESC
     LIMIT p_offset, p_limit;
END$$

DELIMITER ;


-- Phần 40: Thủ tục quản lý thể loại

DROP VIEW IF EXISTS v_staff_categories;
DROP PROCEDURE IF EXISTS sp_category_list;
DROP PROCEDURE IF EXISTS sp_category_create;
DROP PROCEDURE IF EXISTS sp_category_rename;
DROP PROCEDURE IF EXISTS sp_category_delete;

DELIMITER $$

CREATE DEFINER = 'bookstore_definer'@'localhost' PROCEDURE sp_category_list()
SQL SECURITY DEFINER
READS SQL DATA
BEGIN
    SELECT c.id,
           c.name,
           c.slug,
           COUNT(b.id)                       AS book_count,
           COALESCE(SUM(b.is_active = 1), 0) AS active_book_count,
           c.created_at
      FROM catalog_category c
      LEFT JOIN catalog_book b ON b.category_id = c.id
     GROUP BY c.id, c.name, c.slug, c.created_at
     ORDER BY c.name;
END$$

CREATE DEFINER = 'bookstore_definer'@'localhost' PROCEDURE sp_category_create(
    IN  p_actor_id     BIGINT,
    IN  p_name         VARCHAR(255),
    IN  p_slug         VARCHAR(255),
    OUT p_category_id  BIGINT
)
SQL SECURITY DEFINER
MODIFIES SQL DATA
BEGIN
    DECLARE v_staff INT DEFAULT 0;
    DECLARE v_name  VARCHAR(255);

    DECLARE EXIT HANDLER FOR 1062
    BEGIN
        ROLLBACK;
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'CATEGORY_EXISTS';
    END;
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    SET p_category_id = NULL;
    SET v_name = TRIM(p_name);

    IF p_actor_id IS NULL OR p_actor_id <= 0
       OR v_name IS NULL OR CHAR_LENGTH(v_name) = 0 OR CHAR_LENGTH(v_name) > 100
       OR p_slug IS NULL OR CHAR_LENGTH(p_slug) > 120
       OR NOT REGEXP_LIKE(p_slug, '^[a-z0-9]+(-[a-z0-9]+)*$', 'c')
    THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'INVALID_INPUT';
    END IF;

    SELECT COUNT(*) INTO v_staff
      FROM accounts_user
     WHERE id = p_actor_id AND is_staff = 1 AND is_active = 1;
    IF v_staff = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'NOT_STAFF';
    END IF;

    START TRANSACTION;

    INSERT INTO catalog_category (name, slug) VALUES (v_name, p_slug);
    SET p_category_id = LAST_INSERT_ID();

    INSERT INTO core_auditlog (table_name, record_id, action, old_value, new_value, db_user, app_user_id)
    VALUES ('catalog_category', p_category_id, 'INSERT', NULL,
            JSON_OBJECT('name', v_name, 'slug', p_slug), USER(), p_actor_id);

    COMMIT;
END$$

CREATE DEFINER = 'bookstore_definer'@'localhost' PROCEDURE sp_category_rename(
    IN  p_actor_id     BIGINT,
    IN  p_category_id  BIGINT,
    IN  p_name         VARCHAR(255),
    IN  p_slug         VARCHAR(255)
)
SQL SECURITY DEFINER
MODIFIES SQL DATA
proc: BEGIN
    DECLARE v_staff    INT DEFAULT 0;
    DECLARE v_name     VARCHAR(255);
    DECLARE v_old_name VARCHAR(100) DEFAULT NULL;
    DECLARE v_old_slug VARCHAR(120) DEFAULT NULL;

    DECLARE EXIT HANDLER FOR 1062
    BEGIN
        ROLLBACK;
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'CATEGORY_EXISTS';
    END;
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    SET v_name = TRIM(p_name);

    IF p_actor_id IS NULL OR p_actor_id <= 0
       OR p_category_id IS NULL OR p_category_id <= 0
       OR v_name IS NULL OR CHAR_LENGTH(v_name) = 0 OR CHAR_LENGTH(v_name) > 100
       OR p_slug IS NULL OR CHAR_LENGTH(p_slug) > 120
       OR NOT REGEXP_LIKE(p_slug, '^[a-z0-9]+(-[a-z0-9]+)*$', 'c')
    THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'INVALID_INPUT';
    END IF;

    SELECT COUNT(*) INTO v_staff
      FROM accounts_user
     WHERE id = p_actor_id AND is_staff = 1 AND is_active = 1;
    IF v_staff = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'NOT_STAFF';
    END IF;

    START TRANSACTION;

    SELECT name, slug INTO v_old_name, v_old_slug
      FROM catalog_category
     WHERE id = p_category_id
       FOR UPDATE;

    IF v_old_name IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'CATEGORY_NOT_FOUND';
    END IF;

    -- Không có gì đổi (so sánh phân biệt hoa/thường, dấu): không ghi, không log
    IF BINARY v_old_name = BINARY v_name AND BINARY v_old_slug = BINARY p_slug THEN
        COMMIT;
        LEAVE proc;
    END IF;

    UPDATE catalog_category SET name = v_name, slug = p_slug WHERE id = p_category_id;

    INSERT INTO core_auditlog (table_name, record_id, action, old_value, new_value, db_user, app_user_id)
    VALUES ('catalog_category', p_category_id, 'UPDATE',
            JSON_OBJECT('name', v_old_name, 'slug', v_old_slug),
            JSON_OBJECT('name', v_name, 'slug', p_slug), USER(), p_actor_id);

    COMMIT;
END$$

CREATE DEFINER = 'bookstore_definer'@'localhost' PROCEDURE sp_category_delete(
    IN  p_actor_id     BIGINT,
    IN  p_category_id  BIGINT
)
SQL SECURITY DEFINER
MODIFIES SQL DATA
BEGIN
    DECLARE v_staff    INT DEFAULT 0;
    DECLARE v_books    INT DEFAULT 0;
    DECLARE v_old_name VARCHAR(100) DEFAULT NULL;
    DECLARE v_old_slug VARCHAR(120) DEFAULT NULL;

    DECLARE EXIT HANDLER FOR 1451
    BEGIN
        ROLLBACK;
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'CATEGORY_IN_USE';
    END;
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    IF p_actor_id IS NULL OR p_actor_id <= 0
       OR p_category_id IS NULL OR p_category_id <= 0
    THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'INVALID_INPUT';
    END IF;

    SELECT COUNT(*) INTO v_staff
      FROM accounts_user
     WHERE id = p_actor_id AND is_staff = 1 AND is_active = 1;
    IF v_staff = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'NOT_STAFF';
    END IF;

    START TRANSACTION;

    -- Khóa dòng thể loại: câu thêm sách vào thể loại này phải chờ tới khi xong
    SELECT name, slug INTO v_old_name, v_old_slug
      FROM catalog_category
     WHERE id = p_category_id
       FOR UPDATE;

    IF v_old_name IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'CATEGORY_NOT_FOUND';
    END IF;

    SELECT COUNT(*) INTO v_books FROM catalog_book WHERE category_id = p_category_id;
    IF v_books > 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'CATEGORY_IN_USE';
    END IF;

    DELETE FROM catalog_category WHERE id = p_category_id;

    INSERT INTO core_auditlog (table_name, record_id, action, old_value, new_value, db_user, app_user_id)
    VALUES ('catalog_category', p_category_id, 'DELETE',
            JSON_OBJECT('name', v_old_name, 'slug', v_old_slug), NULL, USER(), p_actor_id);

    COMMIT;
END$$

DELIMITER ;


-- Phần 41: Thủ tục quản lý sách

DROP VIEW IF EXISTS v_staff_books;
DROP PROCEDURE IF EXISTS sp_book_create;
DROP PROCEDURE IF EXISTS sp_book_update;
DROP PROCEDURE IF EXISTS sp_book_set_active;
DROP PROCEDURE IF EXISTS sp_book_restock;
DROP PROCEDURE IF EXISTS sp_book_reduce_stock;
DROP PROCEDURE IF EXISTS sp_book_delete;

CREATE DEFINER = 'bookstore_definer'@'localhost'
SQL SECURITY DEFINER
VIEW v_staff_books AS
SELECT id, title, author, isbn, category_id, description, cover_image,
       price, cost_price, stock, is_active, created_at, updated_at
  FROM catalog_book;

DELIMITER $$

CREATE DEFINER = 'bookstore_definer'@'localhost' PROCEDURE sp_book_create(
    IN  p_actor_id     BIGINT,
    IN  p_title        VARCHAR(300),
    IN  p_author       VARCHAR(300),
    IN  p_isbn         VARCHAR(20),
    IN  p_category_id  BIGINT,
    IN  p_description  TEXT,
    IN  p_cover_image  VARCHAR(300),
    IN  p_price        BIGINT,
    IN  p_cost_price   BIGINT,
    IN  p_stock        BIGINT,
    OUT p_book_id      BIGINT
)
SQL SECURITY DEFINER
MODIFIES SQL DATA
BEGIN
    DECLARE v_staff    INT DEFAULT 0;
    DECLARE v_category INT DEFAULT 0;
    DECLARE v_title    VARCHAR(300);
    DECLARE v_author   VARCHAR(300);

    DECLARE EXIT HANDLER FOR 1062
    BEGIN
        ROLLBACK;
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ISBN_EXISTS';
    END;
    DECLARE EXIT HANDLER FOR 1452
    BEGIN
        ROLLBACK;
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'CATEGORY_NOT_FOUND';
    END;
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    SET p_book_id = NULL;
    SET v_title = TRIM(p_title);
    SET v_author = TRIM(p_author);

    IF p_actor_id IS NULL OR p_actor_id <= 0
       OR v_title IS NULL OR CHAR_LENGTH(v_title) = 0 OR CHAR_LENGTH(v_title) > 255
       OR v_author IS NULL OR CHAR_LENGTH(v_author) = 0 OR CHAR_LENGTH(v_author) > 255
       OR p_isbn IS NULL OR NOT REGEXP_LIKE(p_isbn, '^([0-9]{9}[0-9X]|[0-9]{13})$', 'c')
       OR p_category_id IS NULL OR p_category_id <= 0
       OR (p_description IS NOT NULL AND CHAR_LENGTH(p_description) > 5000)
       OR (p_cover_image IS NOT NULL
           AND NOT REGEXP_LIKE(p_cover_image, '^covers/[0-9a-f]{32}[.](jpg|png|webp)$', 'c'))
       OR p_price IS NULL OR p_price < 1 OR p_price > 100000000
       OR p_cost_price IS NULL OR p_cost_price < 0 OR p_cost_price > 100000000
       OR p_stock IS NULL OR p_stock < 0 OR p_stock > 10000
    THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'INVALID_INPUT';
    END IF;

    SELECT COUNT(*) INTO v_staff
      FROM accounts_user
     WHERE id = p_actor_id AND is_staff = 1 AND is_active = 1;
    IF v_staff = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'NOT_STAFF';
    END IF;

    START TRANSACTION;

    SELECT COUNT(*) INTO v_category FROM catalog_category WHERE id = p_category_id;
    IF v_category = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'CATEGORY_NOT_FOUND';
    END IF;

    INSERT INTO catalog_book (title, author, isbn, category_id, description, cover_image,
                              price, cost_price, stock, is_active)
    VALUES (v_title, v_author, p_isbn, p_category_id, p_description, p_cover_image,
            p_price, p_cost_price, p_stock, 1);
    SET p_book_id = LAST_INSERT_ID();

    INSERT INTO core_auditlog (table_name, record_id, action, old_value, new_value, db_user, app_user_id)
    VALUES ('catalog_book', p_book_id, 'INSERT', NULL,
            JSON_OBJECT('title', v_title, 'author', v_author, 'isbn', p_isbn,
                        'category_id', p_category_id, 'cover_image', p_cover_image,
                        'price', p_price, 'cost_price', p_cost_price, 'stock', p_stock,
                        'is_active', 1),
            USER(), p_actor_id);

    COMMIT;
END$$

CREATE DEFINER = 'bookstore_definer'@'localhost' PROCEDURE sp_book_update(
    IN  p_actor_id     BIGINT,
    IN  p_book_id      BIGINT,
    IN  p_title        VARCHAR(300),
    IN  p_author       VARCHAR(300),
    IN  p_isbn         VARCHAR(20),
    IN  p_category_id  BIGINT,
    IN  p_description  TEXT,
    IN  p_cover_image  VARCHAR(300),
    IN  p_price        BIGINT,
    IN  p_cost_price   BIGINT
)
SQL SECURITY DEFINER
MODIFIES SQL DATA
BEGIN
    DECLARE v_staff    INT DEFAULT 0;
    DECLARE v_category INT DEFAULT 0;
    DECLARE v_title    VARCHAR(300);
    DECLARE v_author   VARCHAR(300);
    DECLARE v_old      JSON DEFAULT NULL;

    DECLARE EXIT HANDLER FOR 1062
    BEGIN
        ROLLBACK;
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ISBN_EXISTS';
    END;
    DECLARE EXIT HANDLER FOR 1452
    BEGIN
        ROLLBACK;
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'CATEGORY_NOT_FOUND';
    END;
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    SET v_title = TRIM(p_title);
    SET v_author = TRIM(p_author);

    IF p_actor_id IS NULL OR p_actor_id <= 0
       OR p_book_id IS NULL OR p_book_id <= 0
       OR v_title IS NULL OR CHAR_LENGTH(v_title) = 0 OR CHAR_LENGTH(v_title) > 255
       OR v_author IS NULL OR CHAR_LENGTH(v_author) = 0 OR CHAR_LENGTH(v_author) > 255
       OR p_isbn IS NULL OR NOT REGEXP_LIKE(p_isbn, '^([0-9]{9}[0-9X]|[0-9]{13})$', 'c')
       OR p_category_id IS NULL OR p_category_id <= 0
       OR (p_description IS NOT NULL AND CHAR_LENGTH(p_description) > 5000)
       OR (p_cover_image IS NOT NULL
           AND NOT REGEXP_LIKE(p_cover_image, '^covers/[0-9a-f]{32}[.](jpg|png|webp)$', 'c'))
       OR p_price IS NULL OR p_price < 1 OR p_price > 100000000
       OR p_cost_price IS NULL OR p_cost_price < 0 OR p_cost_price > 100000000
    THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'INVALID_INPUT';
    END IF;

    SELECT COUNT(*) INTO v_staff
      FROM accounts_user
     WHERE id = p_actor_id AND is_staff = 1 AND is_active = 1;
    IF v_staff = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'NOT_STAFF';
    END IF;

    START TRANSACTION;

    SELECT JSON_OBJECT('title', title, 'author', author, 'isbn', isbn,
                       'category_id', category_id, 'cover_image', cover_image,
                       'price', price, 'cost_price', cost_price,
                       'description_length', CHAR_LENGTH(description))
      INTO v_old
      FROM catalog_book
     WHERE id = p_book_id
       FOR UPDATE;

    IF v_old IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'BOOK_NOT_FOUND';
    END IF;

    SELECT COUNT(*) INTO v_category FROM catalog_category WHERE id = p_category_id;
    IF v_category = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'CATEGORY_NOT_FOUND';
    END IF;

    UPDATE catalog_book
       SET title = v_title, author = v_author, isbn = p_isbn, category_id = p_category_id,
           description = p_description, cover_image = p_cover_image,
           price = p_price, cost_price = p_cost_price
     WHERE id = p_book_id;

    INSERT INTO core_auditlog (table_name, record_id, action, old_value, new_value, db_user, app_user_id)
    VALUES ('catalog_book', p_book_id, 'UPDATE', v_old,
            JSON_OBJECT('title', v_title, 'author', v_author, 'isbn', p_isbn,
                        'category_id', p_category_id, 'cover_image', p_cover_image,
                        'price', p_price, 'cost_price', p_cost_price,
                        'description_length', CHAR_LENGTH(p_description)),
            USER(), p_actor_id);

    COMMIT;
END$$

CREATE DEFINER = 'bookstore_definer'@'localhost' PROCEDURE sp_book_set_active(
    IN  p_actor_id   BIGINT,
    IN  p_book_id    BIGINT,
    IN  p_is_active  TINYINT
)
SQL SECURITY DEFINER
MODIFIES SQL DATA
proc: BEGIN
    DECLARE v_staff INT DEFAULT 0;
    DECLARE v_old   TINYINT DEFAULT NULL;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    IF p_actor_id IS NULL OR p_actor_id <= 0
       OR p_book_id IS NULL OR p_book_id <= 0
       OR p_is_active IS NULL OR p_is_active NOT IN (0, 1)
    THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'INVALID_INPUT';
    END IF;

    SELECT COUNT(*) INTO v_staff
      FROM accounts_user
     WHERE id = p_actor_id AND is_staff = 1 AND is_active = 1;
    IF v_staff = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'NOT_STAFF';
    END IF;

    START TRANSACTION;

    SELECT is_active INTO v_old FROM catalog_book WHERE id = p_book_id FOR UPDATE;
    IF v_old IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'BOOK_NOT_FOUND';
    END IF;

    IF v_old = p_is_active THEN
        COMMIT;
        LEAVE proc;
    END IF;

    UPDATE catalog_book SET is_active = p_is_active WHERE id = p_book_id;

    INSERT INTO core_auditlog (table_name, record_id, action, old_value, new_value, db_user, app_user_id)
    VALUES ('catalog_book', p_book_id, 'UPDATE',
            JSON_OBJECT('is_active', v_old), JSON_OBJECT('is_active', p_is_active),
            USER(), p_actor_id);

    COMMIT;
END$$

CREATE DEFINER = 'bookstore_definer'@'localhost' PROCEDURE sp_book_restock(
    IN  p_actor_id   BIGINT,
    IN  p_book_id    BIGINT,
    IN  p_quantity   BIGINT,
    OUT p_new_stock  BIGINT
)
SQL SECURITY DEFINER
MODIFIES SQL DATA
BEGIN
    DECLARE v_staff INT DEFAULT 0;
    DECLARE v_old   BIGINT DEFAULT NULL;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    SET p_new_stock = NULL;

    IF p_actor_id IS NULL OR p_actor_id <= 0 OR p_book_id IS NULL OR p_book_id <= 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'INVALID_INPUT';
    END IF;
    IF p_quantity IS NULL OR p_quantity < 1 OR p_quantity > 10000 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'INVALID_QUANTITY';
    END IF;

    SELECT COUNT(*) INTO v_staff
      FROM accounts_user
     WHERE id = p_actor_id AND is_staff = 1 AND is_active = 1;
    IF v_staff = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'NOT_STAFF';
    END IF;

    START TRANSACTION;

    SELECT stock INTO v_old FROM catalog_book WHERE id = p_book_id FOR UPDATE;
    IF v_old IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'BOOK_NOT_FOUND';
    END IF;
    IF v_old + p_quantity > 10000 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'STOCK_LIMIT';
    END IF;

    UPDATE catalog_book SET stock = stock + p_quantity WHERE id = p_book_id;
    SET p_new_stock = v_old + p_quantity;

    INSERT INTO core_auditlog (table_name, record_id, action, old_value, new_value, db_user, app_user_id)
    VALUES ('catalog_book', p_book_id, 'UPDATE',
            JSON_OBJECT('stock', v_old),
            JSON_OBJECT('stock', p_new_stock, 'restock', p_quantity),
            USER(), p_actor_id);

    COMMIT;
END$$

CREATE DEFINER = 'bookstore_definer'@'localhost' PROCEDURE sp_book_reduce_stock(
    IN  p_actor_id   BIGINT,
    IN  p_book_id    BIGINT,
    IN  p_quantity   BIGINT,
    OUT p_new_stock  BIGINT
)
SQL SECURITY DEFINER
MODIFIES SQL DATA
BEGIN
    DECLARE v_staff INT DEFAULT 0;
    DECLARE v_old   BIGINT DEFAULT NULL;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    SET p_new_stock = NULL;

    IF p_actor_id IS NULL OR p_actor_id <= 0 OR p_book_id IS NULL OR p_book_id <= 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'INVALID_INPUT';
    END IF;
    IF p_quantity IS NULL OR p_quantity < 1 OR p_quantity > 10000 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'INVALID_QUANTITY';
    END IF;

    SELECT COUNT(*) INTO v_staff
      FROM accounts_user
     WHERE id = p_actor_id AND is_staff = 1 AND is_active = 1;
    IF v_staff = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'NOT_STAFF';
    END IF;

    START TRANSACTION;

    SELECT stock INTO v_old FROM catalog_book WHERE id = p_book_id FOR UPDATE;
    IF v_old IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'BOOK_NOT_FOUND';
    END IF;
    IF p_quantity > v_old THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'INSUFFICIENT_STOCK';
    END IF;

    UPDATE catalog_book SET stock = stock - p_quantity WHERE id = p_book_id;
    SET p_new_stock = v_old - p_quantity;

    INSERT INTO core_auditlog (table_name, record_id, action, old_value, new_value, db_user, app_user_id)
    VALUES ('catalog_book', p_book_id, 'UPDATE',
            JSON_OBJECT('stock', v_old),
            JSON_OBJECT('stock', p_new_stock, 'reduce', p_quantity),
            USER(), p_actor_id);

    COMMIT;
END$$

CREATE DEFINER = 'bookstore_definer'@'localhost' PROCEDURE sp_book_delete(
    IN  p_actor_id  BIGINT,
    IN  p_book_id   BIGINT
)
SQL SECURITY DEFINER
MODIFIES SQL DATA
BEGIN
    DECLARE v_staff  INT DEFAULT 0;
    DECLARE v_active TINYINT DEFAULT NULL;
    DECLARE v_orders INT DEFAULT 0;
    DECLARE v_old    JSON DEFAULT NULL;

    DECLARE EXIT HANDLER FOR 1451
    BEGIN
        ROLLBACK;
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'BOOK_HAS_ORDERS';
    END;
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    IF p_actor_id IS NULL OR p_actor_id <= 0 OR p_book_id IS NULL OR p_book_id <= 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'INVALID_INPUT';
    END IF;

    SELECT COUNT(*) INTO v_staff
      FROM accounts_user
     WHERE id = p_actor_id AND is_staff = 1 AND is_active = 1;
    IF v_staff = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'NOT_STAFF';
    END IF;

    START TRANSACTION;

    SELECT is_active,
           JSON_OBJECT('title', title, 'author', author, 'isbn', isbn,
                       'category_id', category_id, 'cover_image', cover_image,
                       'price', price, 'cost_price', cost_price, 'stock', stock)
      INTO v_active, v_old
      FROM catalog_book
     WHERE id = p_book_id
       FOR UPDATE;

    IF v_old IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'BOOK_NOT_FOUND';
    END IF;
    IF v_active = 1 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'BOOK_ACTIVE';
    END IF;

    SELECT COUNT(*) INTO v_orders FROM orders_orderitem WHERE book_id = p_book_id;
    IF v_orders > 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'BOOK_HAS_ORDERS';
    END IF;

    -- Giỏ hàng và đánh giá của sách này bị xóa theo (khóa ngoại ON DELETE CASCADE)
    DELETE FROM catalog_book WHERE id = p_book_id;

    INSERT INTO core_auditlog (table_name, record_id, action, old_value, new_value, db_user, app_user_id)
    VALUES ('catalog_book', p_book_id, 'DELETE', v_old, NULL, USER(), p_actor_id);

    COMMIT;
END$$

DELIMITER ;


-- Phần 42: Thủ tục quản lý tài khoản khách

DROP PROCEDURE IF EXISTS sp_staff_account_list;
DROP PROCEDURE IF EXISTS sp_staff_account_get;
DROP PROCEDURE IF EXISTS sp_staff_account_lock;
DROP PROCEDURE IF EXISTS sp_staff_account_unlock;

DELIMITER $$

CREATE DEFINER = 'bookstore_definer'@'localhost' PROCEDURE sp_staff_account_list(
    IN p_actor_id         BIGINT,
    IN p_status           VARCHAR(20),
    IN p_keyword          VARCHAR(255),
    IN p_failure_limit    INT,
    IN p_cooloff_minutes  INT
)
SQL SECURITY DEFINER
READS SQL DATA
BEGIN
    DECLARE v_staff   INT DEFAULT 0;
    DECLARE v_pattern VARCHAR(400) DEFAULT NULL;

    IF p_actor_id IS NULL OR p_actor_id <= 0
       OR (p_status IS NOT NULL AND p_status NOT IN ('active', 'locked', 'auto_locked', 'temp_locked', 'unverified'))
       OR (p_keyword IS NOT NULL AND CHAR_LENGTH(p_keyword) > 150)
       OR p_failure_limit IS NULL OR p_failure_limit < 1 OR p_failure_limit > 100
       OR p_cooloff_minutes IS NULL OR p_cooloff_minutes < 1 OR p_cooloff_minutes > 1440
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

    SELECT id, username, email, phone_encrypted, status, date_joined, last_login
      FROM (
        SELECT u.id, u.username, u.email, u.phone_encrypted, u.date_joined, u.last_login,
               CASE
                   WHEN u.is_active = 0 THEN 'locked'
                   WHEN u.auto_locked_until > UTC_TIMESTAMP(6) THEN 'auto_locked'
                   WHEN EXISTS (
                        SELECT 1 FROM axes_accessattempt a
                         WHERE a.username = u.username
                           AND a.failures_since_start >= p_failure_limit
                           AND a.attempt_time > UTC_TIMESTAMP(6) - INTERVAL p_cooloff_minutes MINUTE
                   ) THEN 'temp_locked'
                   WHEN u.email_verified = 0 THEN 'unverified'
                   ELSE 'active'
               END AS status
          FROM accounts_user u
         WHERE u.is_staff = 0
           AND (v_pattern IS NULL OR u.username LIKE v_pattern)
      ) t
     WHERE p_status IS NULL OR t.status = p_status
     ORDER BY date_joined DESC, id DESC
     LIMIT 200;
END$$

CREATE DEFINER = 'bookstore_definer'@'localhost' PROCEDURE sp_staff_account_get(
    IN p_actor_id         BIGINT,
    IN p_user_id          BIGINT,
    IN p_failure_limit    INT,
    IN p_cooloff_minutes  INT
)
SQL SECURITY DEFINER
READS SQL DATA
BEGIN
    DECLARE v_staff INT DEFAULT 0;
    DECLARE v_found INT DEFAULT 0;

    IF p_actor_id IS NULL OR p_actor_id <= 0 OR p_user_id IS NULL OR p_user_id <= 0
       OR p_failure_limit IS NULL OR p_failure_limit < 1 OR p_failure_limit > 100
       OR p_cooloff_minutes IS NULL OR p_cooloff_minutes < 1 OR p_cooloff_minutes > 1440
    THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'INVALID_INPUT';
    END IF;

    SELECT COUNT(*) INTO v_staff
      FROM accounts_user
     WHERE id = p_actor_id AND is_staff = 1 AND is_active = 1;
    IF v_staff = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'NOT_STAFF';
    END IF;

    SELECT COUNT(*) INTO v_found FROM accounts_user WHERE id = p_user_id AND is_staff = 0;
    IF v_found = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ACCOUNT_NOT_FOUND';
    END IF;

    SELECT u.id, u.username, u.email, u.phone_encrypted,
           CASE
               WHEN u.is_active = 0 THEN 'locked'
               WHEN u.auto_locked_until > UTC_TIMESTAMP(6) THEN 'auto_locked'
               WHEN EXISTS (
                    SELECT 1 FROM axes_accessattempt a
                     WHERE a.username = u.username
                       AND a.failures_since_start >= p_failure_limit
                       AND a.attempt_time > UTC_TIMESTAMP(6) - INTERVAL p_cooloff_minutes MINUTE
               ) THEN 'temp_locked'
               WHEN u.email_verified = 0 THEN 'unverified'
               ELSE 'active'
           END AS status,
           u.date_joined, u.last_login
      FROM accounts_user u
     WHERE u.id = p_user_id AND u.is_staff = 0;
END$$

CREATE DEFINER = 'bookstore_definer'@'localhost' PROCEDURE sp_staff_account_lock(
    IN p_actor_id  BIGINT,
    IN p_user_id   BIGINT,
    IN p_reason    VARCHAR(500)
)
SQL SECURITY DEFINER
MODIFIES SQL DATA
BEGIN
    DECLARE v_staff  INT DEFAULT 0;
    DECLARE v_active TINYINT DEFAULT NULL;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    IF p_actor_id IS NULL OR p_actor_id <= 0 OR p_user_id IS NULL OR p_user_id <= 0
       OR p_reason IS NULL OR CHAR_LENGTH(TRIM(p_reason)) < 5 OR CHAR_LENGTH(p_reason) > 255
    THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'INVALID_INPUT';
    END IF;

    SELECT COUNT(*) INTO v_staff
      FROM accounts_user
     WHERE id = p_actor_id AND is_staff = 1 AND is_active = 1;
    IF v_staff = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'NOT_STAFF';
    END IF;

    START TRANSACTION;

    SELECT is_active INTO v_active
      FROM accounts_user
     WHERE id = p_user_id AND is_staff = 0
       FOR UPDATE;
    IF v_active IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ACCOUNT_NOT_FOUND';
    END IF;
    IF v_active = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ALREADY_LOCKED';
    END IF;

    UPDATE accounts_user SET is_active = 0 WHERE id = p_user_id;

    INSERT INTO core_auditlog (table_name, record_id, action, old_value, new_value, db_user, app_user_id)
    VALUES ('accounts_user', p_user_id, 'UPDATE',
            JSON_OBJECT('is_active', 1),
            JSON_OBJECT('is_active', 0, 'reason', TRIM(p_reason)),
            USER(), p_actor_id);

    COMMIT;
END$$

CREATE DEFINER = 'bookstore_definer'@'localhost' PROCEDURE sp_staff_account_unlock(
    IN p_actor_id  BIGINT,
    IN p_user_id   BIGINT,
    IN p_reason    VARCHAR(500)
)
SQL SECURITY DEFINER
MODIFIES SQL DATA
BEGIN
    DECLARE v_staff  INT DEFAULT 0;
    DECLARE v_active TINYINT DEFAULT NULL;
    DECLARE v_until  DATETIME(6) DEFAULT NULL;
    DECLARE v_now    DATETIME(6);
    DECLARE v_auto   TINYINT DEFAULT 0;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    IF p_actor_id IS NULL OR p_actor_id <= 0 OR p_user_id IS NULL OR p_user_id <= 0
       OR p_reason IS NULL OR CHAR_LENGTH(TRIM(p_reason)) < 5 OR CHAR_LENGTH(p_reason) > 255
    THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'INVALID_INPUT';
    END IF;

    SELECT COUNT(*) INTO v_staff
      FROM accounts_user
     WHERE id = p_actor_id AND is_staff = 1 AND is_active = 1;
    IF v_staff = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'NOT_STAFF';
    END IF;

    START TRANSACTION;
    SET v_now = UTC_TIMESTAMP(6);

    SELECT is_active, auto_locked_until INTO v_active, v_until
      FROM accounts_user
     WHERE id = p_user_id AND is_staff = 0
       FOR UPDATE;
    IF v_active IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ACCOUNT_NOT_FOUND';
    END IF;
    SET v_auto = (v_until IS NOT NULL AND v_until > v_now);
    IF v_active = 1 AND v_auto = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'NOT_LOCKED';
    END IF;

    UPDATE accounts_user
       SET is_active = 1,
           auto_locked_until = IF(v_auto = 1, v_now, auto_locked_until)
     WHERE id = p_user_id;

    INSERT INTO core_auditlog (table_name, record_id, action, old_value, new_value, db_user, app_user_id)
    VALUES ('accounts_user', p_user_id, 'UPDATE',
            JSON_OBJECT('is_active', v_active, 'auto_locked_until', v_until),
            JSON_OBJECT('is_active', 1, 'auto_locked_until', IF(v_auto = 1, v_now, v_until),
                        'reason', TRIM(p_reason)),
            USER(), p_actor_id);

    COMMIT;
END$$

DELIMITER ;


-- Phần 43: Thủ tục nhật ký hệ thống và Event xóa log cũ

DROP EVENT IF EXISTS ev_purge_old_logs;
DROP PROCEDURE IF EXISTS sp_staff_security_events;
DROP PROCEDURE IF EXISTS sp_staff_audit_log;
DROP PROCEDURE IF EXISTS sp_purge_old_logs;

DELIMITER $$

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


-- Phần 44: Thủ tục quản lý đơn hàng của admin

DROP PROCEDURE IF EXISTS sp_staff_order_list;
DROP PROCEDURE IF EXISTS sp_staff_order_get;
DROP PROCEDURE IF EXISTS sp_staff_order_advance;
DROP PROCEDURE IF EXISTS sp_staff_order_confirm;
DROP PROCEDURE IF EXISTS sp_staff_order_pack;
DROP PROCEDURE IF EXISTS sp_staff_order_ship;
DROP PROCEDURE IF EXISTS sp_staff_order_deliver;

DELIMITER $$

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


-- Phần 45: Thủ tục trang Tổng quan

DROP PROCEDURE IF EXISTS sp_staff_dashboard_orders;
DROP PROCEDURE IF EXISTS sp_staff_dashboard_stock;
DROP PROCEDURE IF EXISTS sp_staff_dashboard_security;
DROP PROCEDURE IF EXISTS sp_staff_dashboard_backup;

DELIMITER $$

CREATE DEFINER = 'bookstore_definer'@'localhost' PROCEDURE sp_staff_dashboard_orders(
    IN p_actor_id     BIGINT,
    IN p_today_start  DATETIME(6),
    IN p_week_start   DATETIME(6),
    IN p_month_start  DATETIME(6)
)
SQL SECURITY DEFINER
READS SQL DATA
BEGIN
    DECLARE v_staff INT DEFAULT 0;

    IF p_actor_id IS NULL OR p_actor_id <= 0
       OR p_today_start IS NULL OR p_week_start IS NULL OR p_month_start IS NULL
       OR p_week_start > p_today_start OR p_month_start > p_today_start
       OR p_today_start > UTC_TIMESTAMP(6) + INTERVAL 1 DAY
       OR p_week_start < p_today_start - INTERVAL 7 DAY
       OR p_month_start < p_today_start - INTERVAL 32 DAY THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'INVALID_INPUT';
    END IF;

    SELECT COUNT(*) INTO v_staff
      FROM accounts_user
     WHERE id = p_actor_id AND is_staff = 1 AND is_active = 1;
    IF v_staff = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'NOT_STAFF';
    END IF;

    SELECT
        COALESCE(SUM(status = 'paid'), 0)                                         AS paid_count,
        COALESCE(SUM(status = 'confirmed'), 0)                                    AS confirmed_count,
        COALESCE(SUM(status = 'packed'), 0)                                       AS packed_count,
        COALESCE(SUM(status = 'shipped'), 0)                                      AS shipped_count,
        COALESCE(SUM(created_at >= p_today_start), 0)                             AS new_today,
        COALESCE(SUM(status = 'cancelled' AND cancelled_at >= p_today_start), 0)  AS cancelled_today,
        COALESCE(SUM(IF(paid_at >= p_today_start, total, 0)), 0)                  AS revenue_today,
        COALESCE(SUM(IF(paid_at >= p_week_start, total, 0)), 0)                   AS revenue_week,
        COALESCE(SUM(IF(paid_at >= p_month_start, total, 0)), 0)                  AS revenue_month
      FROM orders_order
     WHERE status IN ('paid', 'confirmed', 'packed', 'shipped')
        OR created_at >= LEAST(p_today_start, p_week_start, p_month_start)
        OR cancelled_at >= p_today_start
        OR paid_at >= LEAST(p_today_start, p_week_start, p_month_start);
END$$

CREATE DEFINER = 'bookstore_definer'@'localhost' PROCEDURE sp_staff_dashboard_stock(
    IN p_actor_id        BIGINT,
    IN p_low_threshold   INT
)
SQL SECURITY DEFINER
READS SQL DATA
BEGIN
    DECLARE v_staff INT DEFAULT 0;

    IF p_actor_id IS NULL OR p_actor_id <= 0
       OR p_low_threshold IS NULL OR p_low_threshold < 1 OR p_low_threshold > 1000 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'INVALID_INPUT';
    END IF;

    SELECT COUNT(*) INTO v_staff
      FROM accounts_user
     WHERE id = p_actor_id AND is_staff = 1 AND is_active = 1;
    IF v_staff = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'NOT_STAFF';
    END IF;

    SELECT COALESCE(SUM(stock BETWEEN 1 AND p_low_threshold), 0) AS low_count,
           COALESCE(SUM(stock = 0), 0)                           AS out_count
      FROM catalog_book
     WHERE is_active = 1;

    SELECT id, title, stock
      FROM catalog_book
     WHERE is_active = 1 AND stock <= p_low_threshold
     ORDER BY stock, title, id
     LIMIT 5;
END$$

CREATE DEFINER = 'bookstore_definer'@'localhost' PROCEDURE sp_staff_dashboard_security(
    IN p_actor_id     BIGINT,
    IN p_today_start  DATETIME(6)
)
SQL SECURITY DEFINER
READS SQL DATA
BEGIN
    DECLARE v_staff INT DEFAULT 0;
    DECLARE v_since DATETIME(6) DEFAULT UTC_TIMESTAMP(6) - INTERVAL 24 HOUR;

    IF p_actor_id IS NULL OR p_actor_id <= 0
       OR p_today_start IS NULL
       OR p_today_start > UTC_TIMESTAMP(6) + INTERVAL 1 DAY
       OR p_today_start < UTC_TIMESTAMP(6) - INTERVAL 2 DAY THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'INVALID_INPUT';
    END IF;

    SELECT COUNT(*) INTO v_staff
      FROM accounts_user
     WHERE id = p_actor_id AND is_staff = 1 AND is_active = 1;
    IF v_staff = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'NOT_STAFF';
    END IF;

    SELECT COALESCE(SUM(created_at >= v_since AND severity = 'warning'), 0)        AS warning_24h,
           COALESCE(SUM(created_at >= v_since AND severity = 'critical'), 0)       AS critical_24h,
           COALESCE(SUM(created_at >= p_today_start AND event_type = 'login_failed'), 0) AS login_failed_today
      FROM core_securityevent
     WHERE created_at >= LEAST(v_since, p_today_start);
END$$

CREATE DEFINER = 'bookstore_definer'@'localhost' PROCEDURE sp_staff_dashboard_backup(
    IN p_actor_id  BIGINT
)
SQL SECURITY DEFINER
READS SQL DATA
BEGIN
    DECLARE v_staff INT DEFAULT 0;

    IF p_actor_id IS NULL OR p_actor_id <= 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'INVALID_INPUT';
    END IF;

    SELECT COUNT(*) INTO v_staff
      FROM accounts_user
     WHERE id = p_actor_id AND is_staff = 1 AND is_active = 1;
    IF v_staff = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'NOT_STAFF';
    END IF;

    SELECT e.event_type, e.created_at, e.detail
      FROM core_securityevent e
      JOIN (SELECT event_type, MAX(id) AS id
              FROM core_securityevent
             WHERE event_type IN ('backup_created', 'backup_failed', 'restore_verified')
             GROUP BY event_type) latest ON latest.id = e.id;
END$$

DELIMITER ;


-- Phần 46: Thủ tục đếm đăng nhập sai theo IP

DROP PROCEDURE IF EXISTS sp_login_ip_failures;

DELIMITER $$

CREATE DEFINER = 'bookstore_definer'@'localhost' PROCEDURE sp_login_ip_failures(
    IN p_ip_address  VARCHAR(45),
    IN p_minutes     INT
)
SQL SECURITY DEFINER
READS SQL DATA
BEGIN
    IF p_ip_address IS NULL OR CHAR_LENGTH(p_ip_address) = 0 OR CHAR_LENGTH(p_ip_address) > 45
       OR p_minutes IS NULL OR p_minutes < 1 OR p_minutes > 1440
    THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'INVALID_INPUT';
    END IF;

    SELECT COUNT(*) AS failures
      FROM core_securityevent
     WHERE created_at >= UTC_TIMESTAMP(6) - INTERVAL p_minutes MINUTE
       AND event_type = 'login_failed'
       AND ip_address = p_ip_address;
END$$

DELIMITER ;
