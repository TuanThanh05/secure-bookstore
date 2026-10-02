USE BOOKSTORE_GROUP5_DB;

-- khu vực thủ tục hồ sơ người dùng

-- thủ tục xem hồ sơ của chính người dùng
DROP PROCEDURE IF EXISTS sp_user_get_profile;
DELIMITER $$
CREATE PROCEDURE sp_user_get_profile(IN p_user_id INT UNSIGNED)
SQL SECURITY DEFINER
READS SQL DATA
BEGIN
    SELECT *
    FROM v_customer_profile
    WHERE user_id = p_user_id;
END$$
DELIMITER ;

-- thủ tục cập nhật hồ sơ của chính người dùng
DROP PROCEDURE IF EXISTS sp_user_update_profile;
DELIMITER $$
CREATE PROCEDURE sp_user_update_profile(
    IN p_user_id INT UNSIGNED,
    IN p_full_name VARCHAR(150),
    IN p_phone VARCHAR(20),
    IN p_address VARCHAR(500)
)
SQL SECURITY DEFINER
MODIFIES SQL DATA
BEGIN
    IF p_full_name IS NULL OR CHAR_LENGTH(TRIM(p_full_name)) = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Họ tên không hợp lệ';
    END IF;

    UPDATE users
    SET full_name = TRIM(p_full_name),
        phone = NULLIF(TRIM(p_phone), ''),
        address = NULLIF(TRIM(p_address), '')
    WHERE id = p_user_id;

    IF ROW_COUNT() = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Không tìm thấy người dùng';
    END IF;
END$$
DELIMITER ;

-- khu vực thủ tục xác thực

-- thủ tục đăng ký tài khoản bằng mật khẩu
DROP PROCEDURE IF EXISTS sp_auth_register_local;
DELIMITER $$
CREATE PROCEDURE sp_auth_register_local(
    IN p_username VARCHAR(100),
    IN p_email VARCHAR(255),
    IN p_password_hash VARCHAR(255),
    IN p_full_name VARCHAR(150)
)
SQL SECURITY DEFINER
MODIFIES SQL DATA
BEGIN
    DECLARE v_user_id INT UNSIGNED;
    DECLARE v_role_id SMALLINT UNSIGNED;
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    IF p_username IS NULL OR CHAR_LENGTH(TRIM(p_username)) < 3 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Tên đăng nhập không hợp lệ';
    END IF;

    IF p_email IS NULL OR CHAR_LENGTH(TRIM(p_email)) = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Email không hợp lệ';
    END IF;

    IF p_password_hash IS NULL OR CHAR_LENGTH(TRIM(p_password_hash)) = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Hàm băm mật khẩu không hợp lệ';
    END IF;

    START TRANSACTION;

    INSERT INTO users (username, email, password_hash, full_name, status)
    VALUES (TRIM(p_username), LOWER(TRIM(p_email)), p_password_hash, TRIM(p_full_name), 'PENDING');

    SET v_user_id = LAST_INSERT_ID();

    INSERT INTO password_history (user_id, password_hash, change_type)
    VALUES (v_user_id, p_password_hash, 'REGISTER');

    SELECT id INTO v_role_id
    FROM roles
    WHERE code = 'CUSTOMER'
    LIMIT 1;

    IF v_role_id IS NULL THEN
        ROLLBACK;
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Vai trò khách hàng chưa được tạo';
    END IF;

    INSERT INTO user_roles (user_id, role_id, assigned_by_user_id)
    VALUES (v_user_id, v_role_id, NULL);

    COMMIT;

    SELECT v_user_id AS user_id;
END$$
DELIMITER ;

-- thủ tục đăng ký tài khoản bằng google
DROP PROCEDURE IF EXISTS sp_auth_register_google;
DELIMITER $$
CREATE PROCEDURE sp_auth_register_google(
    IN p_username VARCHAR(100),
    IN p_email VARCHAR(255),
    IN p_full_name VARCHAR(150),
    IN p_provider_subject VARCHAR(255)
)
SQL SECURITY DEFINER
MODIFIES SQL DATA
BEGIN
    DECLARE v_user_id INT UNSIGNED;
    DECLARE v_role_id SMALLINT UNSIGNED;
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    START TRANSACTION;

    INSERT INTO users (username, email, email_verified_at, password_hash, full_name, status)
    VALUES (TRIM(p_username), LOWER(TRIM(p_email)), CURRENT_TIMESTAMP, NULL, TRIM(p_full_name), 'ACTIVE');

    SET v_user_id = LAST_INSERT_ID();

    INSERT INTO external_identities (user_id, provider, provider_subject, provider_email)
    VALUES (v_user_id, 'GOOGLE', p_provider_subject, LOWER(TRIM(p_email)));

    SELECT id INTO v_role_id
    FROM roles
    WHERE code = 'CUSTOMER'
    LIMIT 1;

    IF v_role_id IS NULL THEN
        ROLLBACK;
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Vai trò khách hàng chưa được tạo';
    END IF;

    INSERT INTO user_roles (user_id, role_id, assigned_by_user_id)
    VALUES (v_user_id, v_role_id, NULL);

    COMMIT;

    SELECT v_user_id AS user_id;
END$$
DELIMITER ;

-- thủ tục cập nhật mật khẩu sau khi backend đã kiểm tra năm mật khẩu gần nhất
DROP PROCEDURE IF EXISTS sp_auth_set_password;
DELIMITER $$
CREATE PROCEDURE sp_auth_set_password(
    IN p_user_id INT UNSIGNED,
    IN p_password_hash VARCHAR(255),
    IN p_change_type VARCHAR(20)
)
SQL SECURITY DEFINER
MODIFIES SQL DATA
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    IF p_change_type NOT IN ('CHANGE', 'RESET') THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Loại thay đổi mật khẩu không hợp lệ';
    END IF;

    START TRANSACTION;

    UPDATE users
    SET password_hash = p_password_hash,
        status = CASE WHEN status = 'PENDING' AND email_verified_at IS NOT NULL THEN 'ACTIVE' ELSE status END
    WHERE id = p_user_id;

    IF ROW_COUNT() = 0 THEN
        ROLLBACK;
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Không tìm thấy người dùng';
    END IF;

    INSERT INTO password_history (user_id, password_hash, change_type)
    VALUES (p_user_id, p_password_hash, p_change_type);

    UPDATE sessions
    SET revoked_at = CURRENT_TIMESTAMP,
        revoke_reason = 'PASSWORD_CHANGED'
    WHERE user_id = p_user_id
      AND revoked_at IS NULL;

    COMMIT;
END$$
DELIMITER ;

-- thủ tục xác nhận email sau khi backend đã kiểm tra token
DROP PROCEDURE IF EXISTS sp_auth_verify_email;
DELIMITER $$
CREATE PROCEDURE sp_auth_verify_email(
    IN p_user_id INT UNSIGNED,
    IN p_verified_email VARCHAR(255)
)
SQL SECURITY DEFINER
MODIFIES SQL DATA
BEGIN
    UPDATE users
    SET email = LOWER(TRIM(p_verified_email)),
        email_verified_at = CURRENT_TIMESTAMP,
        status = CASE WHEN status = 'PENDING' AND password_hash IS NOT NULL THEN 'ACTIVE' ELSE status END
    WHERE id = p_user_id;

    IF ROW_COUNT() = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Không tìm thấy người dùng';
    END IF;
END$$
DELIMITER ;

-- thủ tục tạo phiên đăng nhập
DROP PROCEDURE IF EXISTS sp_auth_create_session;
DELIMITER $$
CREATE PROCEDURE sp_auth_create_session(
    IN p_user_id INT UNSIGNED,
    IN p_token_hash CHAR(64),
    IN p_ip_address VARCHAR(45),
    IN p_user_agent VARCHAR(500),
    IN p_expires_at DATETIME
)
SQL SECURITY DEFINER
MODIFIES SQL DATA
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM users
        WHERE id = p_user_id
          AND status = 'ACTIVE'
          AND email_verified_at IS NOT NULL
    ) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Tài khoản chưa đủ điều kiện tạo phiên đăng nhập';
    END IF;

    INSERT INTO sessions (user_id, token_hash, ip_address, user_agent, expires_at)
    VALUES (p_user_id, p_token_hash, p_ip_address, p_user_agent, p_expires_at);

    UPDATE users
    SET last_login_at = CURRENT_TIMESTAMP
    WHERE id = p_user_id;
END$$
DELIMITER ;

-- thủ tục ghi nhận lần đăng nhập
DROP PROCEDURE IF EXISTS sp_auth_record_login_attempt;
DELIMITER $$
CREATE PROCEDURE sp_auth_record_login_attempt(
    IN p_user_id INT UNSIGNED,
    IN p_login_identifier VARCHAR(255),
    IN p_ip_address VARCHAR(45),
    IN p_user_agent VARCHAR(500),
    IN p_success BOOLEAN,
    IN p_failure_reason VARCHAR(32)
)
SQL SECURITY DEFINER
MODIFIES SQL DATA
BEGIN
    IF p_success = TRUE THEN
        INSERT INTO login_attempts (user_id, login_identifier, ip_address, user_agent, success, failure_reason)
        VALUES (p_user_id, p_login_identifier, p_ip_address, p_user_agent, TRUE, NULL);
    ELSE
        IF p_failure_reason NOT IN ('INVALID_CREDENTIALS', 'ACCOUNT_PENDING', 'ACCOUNT_LOCKED', 'ACCOUNT_DISABLED', 'RATE_LIMITED', 'CAPTCHA_FAILED', 'OTHER') THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Lý do đăng nhập thất bại không hợp lệ';
        END IF;

        INSERT INTO login_attempts (user_id, login_identifier, ip_address, user_agent, success, failure_reason)
        VALUES (p_user_id, p_login_identifier, p_ip_address, p_user_agent, FALSE, p_failure_reason);
    END IF;
END$$
DELIMITER ;

-- khu vực thủ tục đọc dữ liệu khách hàng

-- thủ tục xem giỏ hàng của khách hàng
DROP PROCEDURE IF EXISTS sp_customer_get_cart;
DELIMITER $$
CREATE PROCEDURE sp_customer_get_cart(IN p_user_id INT UNSIGNED)
SQL SECURITY DEFINER
READS SQL DATA
BEGIN
    SELECT *
    FROM v_customer_cart
    WHERE user_id = p_user_id
    ORDER BY created_at;
END$$
DELIMITER ;

-- thủ tục xem danh sách đơn hàng của khách hàng
DROP PROCEDURE IF EXISTS sp_customer_get_orders;
DELIMITER $$
CREATE PROCEDURE sp_customer_get_orders(IN p_user_id INT UNSIGNED)
SQL SECURITY DEFINER
READS SQL DATA
BEGIN
    SELECT *
    FROM v_customer_orders
    WHERE user_id = p_user_id
    ORDER BY created_at DESC;
END$$
DELIMITER ;

-- thủ tục xem chi tiết một đơn hàng của khách hàng
DROP PROCEDURE IF EXISTS sp_customer_get_order_detail;
DELIMITER $$
CREATE PROCEDURE sp_customer_get_order_detail(
    IN p_user_id INT UNSIGNED,
    IN p_order_id BIGINT UNSIGNED
)
SQL SECURITY DEFINER
READS SQL DATA
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM orders
        WHERE id = p_order_id
          AND user_id = p_user_id
    ) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Không tìm thấy đơn hàng';
    END IF;

    SELECT *
    FROM v_customer_orders
    WHERE user_id = p_user_id
      AND order_id = p_order_id;

    SELECT *
    FROM v_customer_order_items
    WHERE user_id = p_user_id
      AND order_id = p_order_id
    ORDER BY order_item_id;

    SELECT *
    FROM v_customer_payments
    WHERE user_id = p_user_id
      AND order_id = p_order_id;
END$$
DELIMITER ;

-- thủ tục xem sách khách hàng đã mua
DROP PROCEDURE IF EXISTS sp_customer_get_purchased_books;
DELIMITER $$
CREATE PROCEDURE sp_customer_get_purchased_books(IN p_user_id INT UNSIGNED)
SQL SECURITY DEFINER
READS SQL DATA
BEGIN
    SELECT *
    FROM v_customer_purchased_books
    WHERE user_id = p_user_id
    ORDER BY latest_purchase_at DESC;
END$$
DELIMITER ;

-- thủ tục xem phiên đăng nhập của khách hàng
DROP PROCEDURE IF EXISTS sp_customer_get_sessions;
DELIMITER $$
CREATE PROCEDURE sp_customer_get_sessions(IN p_user_id INT UNSIGNED)
SQL SECURITY DEFINER
READS SQL DATA
BEGIN
    SELECT *
    FROM v_customer_sessions
    WHERE user_id = p_user_id
    ORDER BY created_at DESC;
END$$
DELIMITER ;

-- thủ tục xem đánh giá của khách hàng
DROP PROCEDURE IF EXISTS sp_customer_get_reviews;
DELIMITER $$
CREATE PROCEDURE sp_customer_get_reviews(IN p_user_id INT UNSIGNED)
SQL SECURITY DEFINER
READS SQL DATA
BEGIN
    SELECT *
    FROM v_customer_reviews
    WHERE user_id = p_user_id
    ORDER BY created_at DESC;
END$$
DELIMITER ;

-- khu vực thủ tục giỏ hàng

-- thủ tục thêm sách vào giỏ hàng
DROP PROCEDURE IF EXISTS sp_customer_add_cart_item;
DELIMITER $$
CREATE PROCEDURE sp_customer_add_cart_item(
    IN p_user_id INT UNSIGNED,
    IN p_book_id INT UNSIGNED,
    IN p_quantity INT UNSIGNED
)
SQL SECURITY DEFINER
MODIFIES SQL DATA
BEGIN
    DECLARE v_cart_id BIGINT UNSIGNED;
    DECLARE v_stock INT UNSIGNED;
    DECLARE v_status VARCHAR(16);
    DECLARE v_current_quantity INT UNSIGNED DEFAULT 0;
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    IF p_quantity IS NULL OR p_quantity = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Số lượng không hợp lệ';
    END IF;

    START TRANSACTION;

    INSERT IGNORE INTO carts (user_id) VALUES (p_user_id);

    SELECT id INTO v_cart_id
    FROM carts
    WHERE user_id = p_user_id
    FOR UPDATE;

    SELECT stock_quantity, status INTO v_stock, v_status
    FROM books
    WHERE id = p_book_id
    FOR UPDATE;

    IF v_status IS NULL OR v_status <> 'ACTIVE' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Sách không khả dụng';
    END IF;

    SELECT COALESCE(MAX(quantity), 0) INTO v_current_quantity
    FROM cart_items
    WHERE cart_id = v_cart_id
      AND book_id = p_book_id;

    IF v_current_quantity + p_quantity > v_stock THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Số lượng vượt quá tồn kho';
    END IF;

    INSERT INTO cart_items (cart_id, book_id, quantity)
    VALUES (v_cart_id, p_book_id, p_quantity)
    ON DUPLICATE KEY UPDATE quantity = quantity + p_quantity;

    COMMIT;
END$$
DELIMITER ;

-- thủ tục cập nhật số lượng trong giỏ hàng
DROP PROCEDURE IF EXISTS sp_customer_set_cart_item;
DELIMITER $$
CREATE PROCEDURE sp_customer_set_cart_item(
    IN p_user_id INT UNSIGNED,
    IN p_book_id INT UNSIGNED,
    IN p_quantity INT UNSIGNED
)
SQL SECURITY DEFINER
MODIFIES SQL DATA
BEGIN
    DECLARE v_cart_id BIGINT UNSIGNED;
    DECLARE v_stock INT UNSIGNED;
    DECLARE v_status VARCHAR(16);

    IF p_quantity IS NULL OR p_quantity = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Số lượng không hợp lệ';
    END IF;

    SELECT id INTO v_cart_id
    FROM carts
    WHERE user_id = p_user_id;

    IF v_cart_id IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Giỏ hàng không tồn tại';
    END IF;

    SELECT stock_quantity, status INTO v_stock, v_status
    FROM books
    WHERE id = p_book_id;

    IF v_status IS NULL OR v_status <> 'ACTIVE' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Sách không khả dụng';
    END IF;

    IF p_quantity > v_stock THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Số lượng vượt quá tồn kho';
    END IF;

    UPDATE cart_items
    SET quantity = p_quantity
    WHERE cart_id = v_cart_id
      AND book_id = p_book_id;

    IF ROW_COUNT() = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Sản phẩm không có trong giỏ hàng';
    END IF;
END$$
DELIMITER ;

-- thủ tục xóa sách khỏi giỏ hàng
DROP PROCEDURE IF EXISTS sp_customer_remove_cart_item;
DELIMITER $$
CREATE PROCEDURE sp_customer_remove_cart_item(
    IN p_user_id INT UNSIGNED,
    IN p_book_id INT UNSIGNED
)
SQL SECURITY DEFINER
MODIFIES SQL DATA
BEGIN
    DECLARE v_cart_id BIGINT UNSIGNED;

    SELECT id INTO v_cart_id
    FROM carts
    WHERE user_id = p_user_id;

    DELETE FROM cart_items
    WHERE cart_id = v_cart_id
      AND book_id = p_book_id;
END$$
DELIMITER ;

-- khu vực thủ tục đơn hàng

-- thủ tục tạo đơn hàng từ giỏ hàng
DROP PROCEDURE IF EXISTS sp_customer_create_order;
DELIMITER $$
CREATE PROCEDURE sp_customer_create_order(
    IN p_user_id INT UNSIGNED,
    IN p_recipient_name VARCHAR(150),
    IN p_recipient_phone VARCHAR(20),
    IN p_shipping_address VARCHAR(500),
    IN p_note VARCHAR(1000),
    IN p_payment_method VARCHAR(16)
)
SQL SECURITY DEFINER
MODIFIES SQL DATA
BEGIN
    DECLARE v_cart_id BIGINT UNSIGNED;
    DECLARE v_item_count INT UNSIGNED DEFAULT 0;
    DECLARE v_updated_count INT UNSIGNED DEFAULT 0;
    DECLARE v_total BIGINT UNSIGNED DEFAULT 0;
    DECLARE v_order_id BIGINT UNSIGNED;
    DECLARE v_order_code VARCHAR(32);
    DECLARE v_payment_code VARCHAR(64);
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    IF p_payment_method NOT IN ('COD', 'MOMO') THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Phương thức thanh toán không hợp lệ';
    END IF;

    IF p_recipient_name IS NULL OR CHAR_LENGTH(TRIM(p_recipient_name)) = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Tên người nhận không hợp lệ';
    END IF;

    IF p_recipient_phone IS NULL OR CHAR_LENGTH(TRIM(p_recipient_phone)) = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Số điện thoại người nhận không hợp lệ';
    END IF;

    IF p_shipping_address IS NULL OR CHAR_LENGTH(TRIM(p_shipping_address)) = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Địa chỉ giao hàng không hợp lệ';
    END IF;

    START TRANSACTION;

    SELECT id INTO v_cart_id
    FROM carts
    WHERE user_id = p_user_id
    FOR UPDATE;

    IF v_cart_id IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Giỏ hàng không tồn tại';
    END IF;

    SELECT COUNT(*) INTO v_item_count
    FROM cart_items
    WHERE cart_id = v_cart_id;

    IF v_item_count = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Giỏ hàng trống';
    END IF;

    UPDATE books b
    INNER JOIN cart_items ci ON ci.book_id = b.id
    SET b.stock_quantity = b.stock_quantity - ci.quantity
    WHERE ci.cart_id = v_cart_id
      AND b.status = 'ACTIVE'
      AND b.stock_quantity >= ci.quantity;

    SET v_updated_count = ROW_COUNT();

    IF v_updated_count <> v_item_count THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Có sách không khả dụng hoặc không đủ tồn kho';
    END IF;

    SET v_total = fn_calculate_cart_total(v_cart_id);

    IF v_total = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Tổng tiền đơn hàng không hợp lệ';
    END IF;

    SET v_order_code = REPLACE(UUID(), '-', '');

    INSERT INTO orders (
        user_id,
        order_code,
        recipient_name,
        recipient_phone,
        shipping_address,
        status,
        total_amount,
        note
    ) VALUES (
        p_user_id,
        v_order_code,
        TRIM(p_recipient_name),
        TRIM(p_recipient_phone),
        TRIM(p_shipping_address),
        'PENDING',
        v_total,
        NULLIF(TRIM(p_note), '')
    );

    SET v_order_id = LAST_INSERT_ID();

    INSERT INTO order_items (order_id, book_id, book_name, quantity, unit_price)
    SELECT
        v_order_id,
        b.id,
        b.name,
        ci.quantity,
        b.price
    FROM cart_items ci
    INNER JOIN books b ON b.id = ci.book_id
    WHERE ci.cart_id = v_cart_id;

    UPDATE orders
    SET total_amount = fn_calculate_order_total(v_order_id)
    WHERE id = v_order_id;

    INSERT INTO inventory_transactions (
        book_id,
        supplier_id,
        order_id,
        actor_user_id,
        transaction_type,
        quantity_change,
        stock_before,
        stock_after,
        note
    )
    SELECT
        b.id,
        NULL,
        v_order_id,
        p_user_id,
        'SALE',
        -CAST(oi.quantity AS SIGNED),
        b.stock_quantity + oi.quantity,
        b.stock_quantity,
        'Tạo đơn hàng'
    FROM order_items oi
    INNER JOIN books b ON b.id = oi.book_id
    WHERE oi.order_id = v_order_id;

    INSERT INTO order_status_history (order_id, old_status, new_status, changed_by_user_id, reason)
    VALUES (v_order_id, NULL, 'PENDING', p_user_id, 'Khách hàng tạo đơn');

    SET v_payment_code = CONCAT('PAY', REPLACE(UUID(), '-', ''));

    INSERT INTO payments (order_id, payment_code, payment_method, status, amount)
    VALUES (v_order_id, v_payment_code, p_payment_method, 'PENDING', v_total);

    DELETE FROM cart_items
    WHERE cart_id = v_cart_id;

    COMMIT;

    SELECT v_order_id AS order_id, v_order_code AS order_code, v_total AS total_amount;
END$$
DELIMITER ;

-- thủ tục hủy đơn hàng của khách hàng
DROP PROCEDURE IF EXISTS sp_customer_cancel_order;
DELIMITER $$
CREATE PROCEDURE sp_customer_cancel_order(
    IN p_user_id INT UNSIGNED,
    IN p_order_id BIGINT UNSIGNED,
    IN p_reason VARCHAR(500)
)
SQL SECURITY DEFINER
MODIFIES SQL DATA
BEGIN
    DECLARE v_status VARCHAR(16);
    DECLARE v_payment_status VARCHAR(16);
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    START TRANSACTION;

    SELECT status INTO v_status
    FROM orders
    WHERE id = p_order_id
      AND user_id = p_user_id
    FOR UPDATE;

    IF v_status IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Không tìm thấy đơn hàng';
    END IF;

    IF v_status NOT IN ('PENDING', 'CONFIRMED') THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Đơn hàng không còn được phép hủy';
    END IF;

    SELECT status INTO v_payment_status
    FROM payments
    WHERE order_id = p_order_id
    FOR UPDATE;

    IF v_payment_status IN ('PAID', 'REFUNDED') THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Đơn đã thanh toán cần xử lý hoàn tiền riêng';
    END IF;

    UPDATE books b
    INNER JOIN order_items oi ON oi.book_id = b.id
    SET b.stock_quantity = b.stock_quantity + oi.quantity
    WHERE oi.order_id = p_order_id;

    INSERT INTO inventory_transactions (
        book_id,
        supplier_id,
        order_id,
        actor_user_id,
        transaction_type,
        quantity_change,
        stock_before,
        stock_after,
        note
    )
    SELECT
        b.id,
        NULL,
        p_order_id,
        p_user_id,
        'CANCEL_RESTORE',
        CAST(oi.quantity AS SIGNED),
        b.stock_quantity - oi.quantity,
        b.stock_quantity,
        COALESCE(NULLIF(TRIM(p_reason), ''), 'Khách hàng hủy đơn')
    FROM order_items oi
    INNER JOIN books b ON b.id = oi.book_id
    WHERE oi.order_id = p_order_id;

    UPDATE orders
    SET status = 'CANCELLED',
        cancelled_at = CURRENT_TIMESTAMP
    WHERE id = p_order_id;

    UPDATE payments
    SET status = 'CANCELLED'
    WHERE order_id = p_order_id
      AND status IN ('PENDING', 'FAILED');

    INSERT INTO order_status_history (order_id, old_status, new_status, changed_by_user_id, reason)
    VALUES (p_order_id, v_status, 'CANCELLED', p_user_id, COALESCE(NULLIF(TRIM(p_reason), ''), 'Khách hàng hủy đơn'));

    COMMIT;
END$$
DELIMITER ;

-- khu vực thủ tục đánh giá sách

-- thủ tục tạo hoặc cập nhật đánh giá của khách hàng
DROP PROCEDURE IF EXISTS sp_customer_upsert_review;
DELIMITER $$
CREATE PROCEDURE sp_customer_upsert_review(
    IN p_user_id INT UNSIGNED,
    IN p_book_id INT UNSIGNED,
    IN p_rating TINYINT UNSIGNED,
    IN p_review_text TEXT
)
SQL SECURITY DEFINER
MODIFIES SQL DATA
BEGIN
    IF p_rating < 1 OR p_rating > 5 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Điểm đánh giá không hợp lệ';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM orders o
        INNER JOIN order_items oi ON oi.order_id = o.id
        WHERE o.user_id = p_user_id
          AND o.status = 'COMPLETED'
          AND oi.book_id = p_book_id
    ) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Chỉ khách đã mua sách mới được đánh giá';
    END IF;

    INSERT INTO reviews (user_id, book_id, rating, review_text, status)
    VALUES (p_user_id, p_book_id, p_rating, NULLIF(TRIM(p_review_text), ''), 'PUBLISHED')
    ON DUPLICATE KEY UPDATE
        rating = p_rating,
        review_text = NULLIF(TRIM(p_review_text), ''),
        status = 'PUBLISHED',
        updated_at = CURRENT_TIMESTAMP;
END$$
DELIMITER ;

-- khu vực thủ tục nhân viên

-- thủ tục chuyển trạng thái đơn hàng theo luồng xử lý của nhân viên
DROP PROCEDURE IF EXISTS sp_staff_change_order_status;
DELIMITER $$
CREATE PROCEDURE sp_staff_change_order_status(
    IN p_staff_user_id INT UNSIGNED,
    IN p_order_id BIGINT UNSIGNED,
    IN p_new_status VARCHAR(16),
    IN p_reason VARCHAR(500)
)
SQL SECURITY DEFINER
MODIFIES SQL DATA
BEGIN
    DECLARE v_old_status VARCHAR(16);
    DECLARE v_payment_method VARCHAR(16);
    DECLARE v_payment_status VARCHAR(16);
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    START TRANSACTION;

    SELECT status INTO v_old_status
    FROM orders
    WHERE id = p_order_id
    FOR UPDATE;

    IF v_old_status IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Không tìm thấy đơn hàng';
    END IF;

    IF NOT (
        (v_old_status = 'PENDING' AND p_new_status = 'CONFIRMED') OR
        (v_old_status = 'CONFIRMED' AND p_new_status = 'PROCESSING') OR
        (v_old_status = 'PROCESSING' AND p_new_status = 'SHIPPING') OR
        (v_old_status = 'SHIPPING' AND p_new_status = 'COMPLETED')
    ) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Chuyển trạng thái đơn hàng không hợp lệ';
    END IF;

    SELECT payment_method, status INTO v_payment_method, v_payment_status
    FROM payments
    WHERE order_id = p_order_id
    FOR UPDATE;

    IF p_new_status = 'COMPLETED' THEN
        IF v_payment_method = 'MOMO' AND v_payment_status <> 'PAID' THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Đơn MoMo chưa được xác nhận thanh toán';
        END IF;

        IF v_payment_method = 'COD' AND v_payment_status = 'PENDING' THEN
            UPDATE payments
            SET status = 'PAID',
                paid_at = CURRENT_TIMESTAMP
            WHERE order_id = p_order_id;
        END IF;
    END IF;

    UPDATE orders
    SET status = p_new_status,
        completed_at = CASE WHEN p_new_status = 'COMPLETED' THEN CURRENT_TIMESTAMP ELSE completed_at END
    WHERE id = p_order_id;

    INSERT INTO order_status_history (order_id, old_status, new_status, changed_by_user_id, reason)
    VALUES (p_order_id, v_old_status, p_new_status, p_staff_user_id, NULLIF(TRIM(p_reason), ''));

    COMMIT;
END$$
DELIMITER ;

-- khu vực thủ tục quản lý danh mục sách

-- thủ tục tạo tác giả
DROP PROCEDURE IF EXISTS sp_manager_create_author;
DELIMITER $$
CREATE PROCEDURE sp_manager_create_author(
    IN p_name VARCHAR(255),
    IN p_date_of_birth DATE
)
SQL SECURITY DEFINER
MODIFIES SQL DATA
BEGIN
    INSERT INTO authors (name, date_of_birth)
    VALUES (TRIM(p_name), p_date_of_birth);
END$$
DELIMITER ;

-- thủ tục cập nhật tác giả
DROP PROCEDURE IF EXISTS sp_manager_update_author;
DELIMITER $$
CREATE PROCEDURE sp_manager_update_author(
    IN p_author_id INT UNSIGNED,
    IN p_name VARCHAR(255),
    IN p_date_of_birth DATE
)
SQL SECURITY DEFINER
MODIFIES SQL DATA
BEGIN
    UPDATE authors
    SET name = TRIM(p_name),
        date_of_birth = p_date_of_birth
    WHERE id = p_author_id;
END$$
DELIMITER ;

-- thủ tục tạo thể loại
DROP PROCEDURE IF EXISTS sp_manager_create_category;
DELIMITER $$
CREATE PROCEDURE sp_manager_create_category(
    IN p_name VARCHAR(255),
    IN p_description TEXT
)
SQL SECURITY DEFINER
MODIFIES SQL DATA
BEGIN
    INSERT INTO categories (name, description)
    VALUES (TRIM(p_name), NULLIF(TRIM(p_description), ''));
END$$
DELIMITER ;

-- thủ tục cập nhật thể loại
DROP PROCEDURE IF EXISTS sp_manager_update_category;
DELIMITER $$
CREATE PROCEDURE sp_manager_update_category(
    IN p_category_id INT UNSIGNED,
    IN p_name VARCHAR(255),
    IN p_description TEXT
)
SQL SECURITY DEFINER
MODIFIES SQL DATA
BEGIN
    UPDATE categories
    SET name = TRIM(p_name),
        description = NULLIF(TRIM(p_description), '')
    WHERE id = p_category_id;
END$$
DELIMITER ;

-- thủ tục tạo nhà xuất bản
DROP PROCEDURE IF EXISTS sp_manager_create_publisher;
DELIMITER $$
CREATE PROCEDURE sp_manager_create_publisher(
    IN p_name VARCHAR(255),
    IN p_address VARCHAR(500),
    IN p_phone VARCHAR(20),
    IN p_email VARCHAR(255)
)
SQL SECURITY DEFINER
MODIFIES SQL DATA
BEGIN
    INSERT INTO publishers (name, address, phone, email)
    VALUES (TRIM(p_name), NULLIF(TRIM(p_address), ''), NULLIF(TRIM(p_phone), ''), NULLIF(LOWER(TRIM(p_email)), ''));
END$$
DELIMITER ;

-- thủ tục cập nhật nhà xuất bản
DROP PROCEDURE IF EXISTS sp_manager_update_publisher;
DELIMITER $$
CREATE PROCEDURE sp_manager_update_publisher(
    IN p_publisher_id INT UNSIGNED,
    IN p_name VARCHAR(255),
    IN p_address VARCHAR(500),
    IN p_phone VARCHAR(20),
    IN p_email VARCHAR(255)
)
SQL SECURITY DEFINER
MODIFIES SQL DATA
BEGIN
    UPDATE publishers
    SET name = TRIM(p_name),
        address = NULLIF(TRIM(p_address), ''),
        phone = NULLIF(TRIM(p_phone), ''),
        email = NULLIF(LOWER(TRIM(p_email)), '')
    WHERE id = p_publisher_id;
END$$
DELIMITER ;

-- thủ tục tạo nhà cung cấp
DROP PROCEDURE IF EXISTS sp_manager_create_supplier;
DELIMITER $$
CREATE PROCEDURE sp_manager_create_supplier(
    IN p_name VARCHAR(255),
    IN p_address VARCHAR(500),
    IN p_phone VARCHAR(20),
    IN p_email VARCHAR(255)
)
SQL SECURITY DEFINER
MODIFIES SQL DATA
BEGIN
    INSERT INTO suppliers (name, address, phone, email)
    VALUES (TRIM(p_name), NULLIF(TRIM(p_address), ''), NULLIF(TRIM(p_phone), ''), NULLIF(LOWER(TRIM(p_email)), ''));
END$$
DELIMITER ;

-- thủ tục cập nhật nhà cung cấp
DROP PROCEDURE IF EXISTS sp_manager_update_supplier;
DELIMITER $$
CREATE PROCEDURE sp_manager_update_supplier(
    IN p_supplier_id INT UNSIGNED,
    IN p_name VARCHAR(255),
    IN p_address VARCHAR(500),
    IN p_phone VARCHAR(20),
    IN p_email VARCHAR(255)
)
SQL SECURITY DEFINER
MODIFIES SQL DATA
BEGIN
    UPDATE suppliers
    SET name = TRIM(p_name),
        address = NULLIF(TRIM(p_address), ''),
        phone = NULLIF(TRIM(p_phone), ''),
        email = NULLIF(LOWER(TRIM(p_email)), '')
    WHERE id = p_supplier_id;
END$$
DELIMITER ;

-- thủ tục tạo sách
DROP PROCEDURE IF EXISTS sp_manager_create_book;
DELIMITER $$
CREATE PROCEDURE sp_manager_create_book(
    IN p_category_id INT UNSIGNED,
    IN p_publisher_id INT UNSIGNED,
    IN p_name VARCHAR(255),
    IN p_isbn VARCHAR(20),
    IN p_price BIGINT UNSIGNED,
    IN p_publication_year SMALLINT UNSIGNED,
    IN p_description TEXT,
    IN p_status VARCHAR(16)
)
SQL SECURITY DEFINER
MODIFIES SQL DATA
BEGIN
    IF p_status NOT IN ('DRAFT', 'ACTIVE', 'INACTIVE') THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Trạng thái sách không hợp lệ';
    END IF;

    INSERT INTO books (
        category_id,
        publisher_id,
        name,
        isbn,
        price,
        publication_year,
        description,
        status
    ) VALUES (
        p_category_id,
        p_publisher_id,
        TRIM(p_name),
        NULLIF(TRIM(p_isbn), ''),
        p_price,
        p_publication_year,
        NULLIF(TRIM(p_description), ''),
        p_status
    );

    SELECT LAST_INSERT_ID() AS book_id;
END$$
DELIMITER ;

-- thủ tục cập nhật sách không cho sửa trực tiếp tồn kho
DROP PROCEDURE IF EXISTS sp_manager_update_book;
DELIMITER $$
CREATE PROCEDURE sp_manager_update_book(
    IN p_book_id INT UNSIGNED,
    IN p_category_id INT UNSIGNED,
    IN p_publisher_id INT UNSIGNED,
    IN p_name VARCHAR(255),
    IN p_isbn VARCHAR(20),
    IN p_price BIGINT UNSIGNED,
    IN p_publication_year SMALLINT UNSIGNED,
    IN p_description TEXT,
    IN p_status VARCHAR(16)
)
SQL SECURITY DEFINER
MODIFIES SQL DATA
BEGIN
    IF p_status NOT IN ('DRAFT', 'ACTIVE', 'INACTIVE') THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Trạng thái sách không hợp lệ';
    END IF;

    UPDATE books
    SET category_id = p_category_id,
        publisher_id = p_publisher_id,
        name = TRIM(p_name),
        isbn = NULLIF(TRIM(p_isbn), ''),
        price = p_price,
        publication_year = p_publication_year,
        description = NULLIF(TRIM(p_description), ''),
        status = p_status
    WHERE id = p_book_id;
END$$
DELIMITER ;

-- thủ tục thêm tác giả cho sách
DROP PROCEDURE IF EXISTS sp_manager_add_book_author;
DELIMITER $$
CREATE PROCEDURE sp_manager_add_book_author(
    IN p_book_id INT UNSIGNED,
    IN p_author_id INT UNSIGNED
)
SQL SECURITY DEFINER
MODIFIES SQL DATA
BEGIN
    INSERT IGNORE INTO book_authors (book_id, author_id, is_primary)
    VALUES (p_book_id, p_author_id, FALSE);
END$$
DELIMITER ;

-- thủ tục đặt tác giả chính cho sách
DROP PROCEDURE IF EXISTS sp_manager_set_primary_author;
DELIMITER $$
CREATE PROCEDURE sp_manager_set_primary_author(
    IN p_book_id INT UNSIGNED,
    IN p_author_id INT UNSIGNED
)
SQL SECURITY DEFINER
MODIFIES SQL DATA
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    START TRANSACTION;

    IF NOT EXISTS (
        SELECT 1
        FROM book_authors
        WHERE book_id = p_book_id
          AND author_id = p_author_id
    ) THEN
        INSERT INTO book_authors (book_id, author_id, is_primary)
        VALUES (p_book_id, p_author_id, FALSE);
    END IF;

    UPDATE book_authors
    SET is_primary = FALSE
    WHERE book_id = p_book_id
      AND is_primary = TRUE;

    UPDATE book_authors
    SET is_primary = TRUE
    WHERE book_id = p_book_id
      AND author_id = p_author_id;

    COMMIT;
END$$
DELIMITER ;

-- thủ tục xóa tác giả phụ khỏi sách
DROP PROCEDURE IF EXISTS sp_manager_remove_book_author;
DELIMITER $$
CREATE PROCEDURE sp_manager_remove_book_author(
    IN p_book_id INT UNSIGNED,
    IN p_author_id INT UNSIGNED
)
SQL SECURITY DEFINER
MODIFIES SQL DATA
BEGIN
    IF EXISTS (
        SELECT 1
        FROM book_authors
        WHERE book_id = p_book_id
          AND author_id = p_author_id
          AND is_primary = TRUE
    ) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Phải chọn tác giả chính khác trước khi xóa';
    END IF;

    DELETE FROM book_authors
    WHERE book_id = p_book_id
      AND author_id = p_author_id;
END$$
DELIMITER ;

-- thủ tục thêm hình ảnh sách
DROP PROCEDURE IF EXISTS sp_manager_add_book_image;
DELIMITER $$
CREATE PROCEDURE sp_manager_add_book_image(
    IN p_book_id INT UNSIGNED,
    IN p_image_url VARCHAR(500),
    IN p_alt_text VARCHAR(255),
    IN p_display_order SMALLINT UNSIGNED
)
SQL SECURITY DEFINER
MODIFIES SQL DATA
BEGIN
    INSERT INTO book_images (book_id, image_url, alt_text, display_order)
    VALUES (p_book_id, p_image_url, NULLIF(TRIM(p_alt_text), ''), p_display_order);
END$$
DELIMITER ;

-- khu vực thủ tục kho hàng

-- thủ tục nhập kho
DROP PROCEDURE IF EXISTS sp_manager_import_inventory;
DELIMITER $$
CREATE PROCEDURE sp_manager_import_inventory(
    IN p_manager_user_id INT UNSIGNED,
    IN p_book_id INT UNSIGNED,
    IN p_supplier_id INT UNSIGNED,
    IN p_quantity INT UNSIGNED,
    IN p_note VARCHAR(500)
)
SQL SECURITY DEFINER
MODIFIES SQL DATA
BEGIN
    DECLARE v_stock_before INT UNSIGNED;
    DECLARE v_stock_after INT UNSIGNED;
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    IF p_quantity IS NULL OR p_quantity = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Số lượng nhập kho không hợp lệ';
    END IF;

    START TRANSACTION;

    SELECT stock_quantity INTO v_stock_before
    FROM books
    WHERE id = p_book_id
    FOR UPDATE;

    SET v_stock_after = v_stock_before + p_quantity;

    UPDATE books
    SET stock_quantity = v_stock_after
    WHERE id = p_book_id;

    INSERT INTO inventory_transactions (
        book_id,
        supplier_id,
        order_id,
        actor_user_id,
        transaction_type,
        quantity_change,
        stock_before,
        stock_after,
        note
    ) VALUES (
        p_book_id,
        p_supplier_id,
        NULL,
        p_manager_user_id,
        'IMPORT',
        p_quantity,
        v_stock_before,
        v_stock_after,
        NULLIF(TRIM(p_note), '')
    );

    COMMIT;
END$$
DELIMITER ;

-- thủ tục điều chỉnh tồn kho
DROP PROCEDURE IF EXISTS sp_manager_adjust_inventory;
DELIMITER $$
CREATE PROCEDURE sp_manager_adjust_inventory(
    IN p_manager_user_id INT UNSIGNED,
    IN p_book_id INT UNSIGNED,
    IN p_quantity_change INT,
    IN p_note VARCHAR(500)
)
SQL SECURITY DEFINER
MODIFIES SQL DATA
BEGIN
    DECLARE v_stock_before INT UNSIGNED;
    DECLARE v_stock_after_signed BIGINT SIGNED;
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    IF p_quantity_change = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Mức điều chỉnh tồn kho không hợp lệ';
    END IF;

    IF p_note IS NULL OR CHAR_LENGTH(TRIM(p_note)) = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Điều chỉnh kho bắt buộc phải có lý do';
    END IF;

    START TRANSACTION;

    SELECT stock_quantity INTO v_stock_before
    FROM books
    WHERE id = p_book_id
    FOR UPDATE;

    SET v_stock_after_signed = CAST(v_stock_before AS SIGNED) + p_quantity_change;

    IF v_stock_after_signed < 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Tồn kho không được âm';
    END IF;

    UPDATE books
    SET stock_quantity = CAST(v_stock_after_signed AS UNSIGNED)
    WHERE id = p_book_id;

    INSERT INTO inventory_transactions (
        book_id,
        supplier_id,
        order_id,
        actor_user_id,
        transaction_type,
        quantity_change,
        stock_before,
        stock_after,
        note
    ) VALUES (
        p_book_id,
        NULL,
        NULL,
        p_manager_user_id,
        'ADJUSTMENT',
        p_quantity_change,
        v_stock_before,
        CAST(v_stock_after_signed AS UNSIGNED),
        TRIM(p_note)
    );

    COMMIT;
END$$
DELIMITER ;

-- khu vực thủ tục quản lý nhân viên

-- thủ tục tạo tài khoản nhân viên ở trạng thái chờ kích hoạt
DROP PROCEDURE IF EXISTS sp_manager_create_staff_account;
DELIMITER $$
CREATE PROCEDURE sp_manager_create_staff_account(
    IN p_manager_user_id INT UNSIGNED,
    IN p_username VARCHAR(100),
    IN p_email VARCHAR(255),
    IN p_full_name VARCHAR(150)
)
SQL SECURITY DEFINER
MODIFIES SQL DATA
BEGIN
    DECLARE v_user_id INT UNSIGNED;
    DECLARE v_role_id SMALLINT UNSIGNED;
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    START TRANSACTION;

    INSERT INTO users (username, email, password_hash, full_name, status)
    VALUES (TRIM(p_username), LOWER(TRIM(p_email)), NULL, TRIM(p_full_name), 'PENDING');

    SET v_user_id = LAST_INSERT_ID();

    SELECT id INTO v_role_id
    FROM roles
    WHERE code = 'STAFF'
    LIMIT 1;

    IF v_role_id IS NULL THEN
        ROLLBACK;
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Vai trò nhân viên chưa được tạo';
    END IF;

    INSERT INTO user_roles (user_id, role_id, assigned_by_user_id)
    VALUES (v_user_id, v_role_id, p_manager_user_id);

    COMMIT;

    SELECT v_user_id AS user_id;
END$$
DELIMITER ;

-- thủ tục ẩn hoặc công khai đánh giá
DROP PROCEDURE IF EXISTS sp_manager_set_review_status;
DELIMITER $$
CREATE PROCEDURE sp_manager_set_review_status(
    IN p_review_id BIGINT UNSIGNED,
    IN p_status VARCHAR(16)
)
SQL SECURITY DEFINER
MODIFIES SQL DATA
BEGIN
    IF p_status NOT IN ('PUBLISHED', 'HIDDEN') THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Trạng thái đánh giá không hợp lệ';
    END IF;

    UPDATE reviews
    SET status = p_status
    WHERE id = p_review_id;
END$$
DELIMITER ;

-- khu vực thủ tục quản trị an ninh

-- thủ tục khóa tài khoản không phải quản trị viên
DROP PROCEDURE IF EXISTS sp_security_lock_user;
DELIMITER $$
CREATE PROCEDURE sp_security_lock_user(
    IN p_actor_user_id INT UNSIGNED,
    IN p_target_user_id INT UNSIGNED,
    IN p_locked_until DATETIME,
    IN p_reason VARCHAR(500)
)
SQL SECURITY DEFINER
MODIFIES SQL DATA
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    IF EXISTS (
        SELECT 1
        FROM user_roles ur
        INNER JOIN roles r ON r.id = ur.role_id
        WHERE ur.user_id = p_target_user_id
          AND r.code IN ('SECURITY_ADMIN', 'OPERATIONS_ADMIN', 'SUPER_ADMIN')
    ) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Quản trị an ninh không được khóa tài khoản quản trị viên';
    END IF;

    START TRANSACTION;

    UPDATE users
    SET status = 'LOCKED',
        locked_until = p_locked_until
    WHERE id = p_target_user_id;

    UPDATE sessions
    SET revoked_at = CURRENT_TIMESTAMP,
        revoke_reason = 'ACCOUNT_LOCKED'
    WHERE user_id = p_target_user_id
      AND revoked_at IS NULL;

    INSERT INTO audit_logs (actor_user_id, action, target_type, target_id, new_values, success)
    VALUES (
        p_actor_user_id,
        'LOCK_USER',
        'USER',
        CAST(p_target_user_id AS CHAR),
        JSON_OBJECT('locked_until', p_locked_until, 'reason', p_reason),
        TRUE
    );

    COMMIT;
END$$
DELIMITER ;

-- thủ tục mở khóa tài khoản không phải quản trị viên
DROP PROCEDURE IF EXISTS sp_security_unlock_user;
DELIMITER $$
CREATE PROCEDURE sp_security_unlock_user(
    IN p_actor_user_id INT UNSIGNED,
    IN p_target_user_id INT UNSIGNED
)
SQL SECURITY DEFINER
MODIFIES SQL DATA
BEGIN
    IF EXISTS (
        SELECT 1
        FROM user_roles ur
        INNER JOIN roles r ON r.id = ur.role_id
        WHERE ur.user_id = p_target_user_id
          AND r.code IN ('SECURITY_ADMIN', 'OPERATIONS_ADMIN', 'SUPER_ADMIN')
    ) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Quản trị an ninh không được mở khóa tài khoản quản trị viên';
    END IF;

    UPDATE users
    SET status = 'ACTIVE',
        locked_until = NULL
    WHERE id = p_target_user_id;

    INSERT INTO audit_logs (actor_user_id, action, target_type, target_id, success)
    VALUES (p_actor_user_id, 'UNLOCK_USER', 'USER', CAST(p_target_user_id AS CHAR), TRUE);
END$$
DELIMITER ;

-- thủ tục thu hồi một phiên đăng nhập
DROP PROCEDURE IF EXISTS sp_security_revoke_session;
DELIMITER $$
CREATE PROCEDURE sp_security_revoke_session(
    IN p_actor_user_id INT UNSIGNED,
    IN p_session_id BIGINT UNSIGNED,
    IN p_reason VARCHAR(255)
)
SQL SECURITY DEFINER
MODIFIES SQL DATA
BEGIN
    UPDATE sessions
    SET revoked_at = CURRENT_TIMESTAMP,
        revoke_reason = COALESCE(NULLIF(TRIM(p_reason), ''), 'SECURITY_ADMIN_REVOKED')
    WHERE id = p_session_id
      AND revoked_at IS NULL;

    INSERT INTO audit_logs (actor_user_id, action, target_type, target_id, success)
    VALUES (p_actor_user_id, 'REVOKE_SESSION', 'SESSION', CAST(p_session_id AS CHAR), TRUE);
END$$
DELIMITER ;

-- thủ tục thu hồi toàn bộ phiên của một tài khoản
DROP PROCEDURE IF EXISTS sp_security_revoke_all_sessions;
DELIMITER $$
CREATE PROCEDURE sp_security_revoke_all_sessions(
    IN p_actor_user_id INT UNSIGNED,
    IN p_target_user_id INT UNSIGNED,
    IN p_reason VARCHAR(255)
)
SQL SECURITY DEFINER
MODIFIES SQL DATA
BEGIN
    UPDATE sessions
    SET revoked_at = CURRENT_TIMESTAMP,
        revoke_reason = COALESCE(NULLIF(TRIM(p_reason), ''), 'SECURITY_ADMIN_REVOKED_ALL')
    WHERE user_id = p_target_user_id
      AND revoked_at IS NULL;

    INSERT INTO audit_logs (actor_user_id, action, target_type, target_id, success)
    VALUES (p_actor_user_id, 'REVOKE_ALL_SESSIONS', 'USER', CAST(p_target_user_id AS CHAR), TRUE);
END$$
DELIMITER ;

-- thủ tục đánh dấu sự kiện bảo mật đã xử lý
DROP PROCEDURE IF EXISTS sp_security_resolve_event;
DELIMITER $$
CREATE PROCEDURE sp_security_resolve_event(
    IN p_actor_user_id INT UNSIGNED,
    IN p_security_event_id BIGINT UNSIGNED,
    IN p_resolution_note VARCHAR(500)
)
SQL SECURITY DEFINER
MODIFIES SQL DATA
BEGIN
    UPDATE security_events
    SET resolved_at = CURRENT_TIMESTAMP,
        resolved_by_user_id = p_actor_user_id,
        resolution_note = NULLIF(TRIM(p_resolution_note), '')
    WHERE id = p_security_event_id
      AND resolved_at IS NULL;
END$$
DELIMITER ;

-- thủ tục gán vai trò không phải quản trị viên
DROP PROCEDURE IF EXISTS sp_security_assign_non_admin_role;
DELIMITER $$
CREATE PROCEDURE sp_security_assign_non_admin_role(
    IN p_actor_user_id INT UNSIGNED,
    IN p_target_user_id INT UNSIGNED,
    IN p_role_code VARCHAR(50)
)
SQL SECURITY DEFINER
MODIFIES SQL DATA
BEGIN
    DECLARE v_role_id SMALLINT UNSIGNED;

    IF p_role_code NOT IN ('CUSTOMER', 'STAFF', 'BOOK_MANAGER') THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Quản trị an ninh không được gán vai trò quản trị viên';
    END IF;

    SELECT id INTO v_role_id
    FROM roles
    WHERE code = p_role_code
    LIMIT 1;

    IF v_role_id IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Vai trò không tồn tại';
    END IF;

    INSERT IGNORE INTO user_roles (user_id, role_id, assigned_by_user_id)
    VALUES (p_target_user_id, v_role_id, p_actor_user_id);

    INSERT INTO audit_logs (actor_user_id, action, target_type, target_id, new_values, success)
    VALUES (
        p_actor_user_id,
        'ASSIGN_ROLE',
        'USER',
        CAST(p_target_user_id AS CHAR),
        JSON_OBJECT('role_code', p_role_code),
        TRUE
    );
END$$
DELIMITER ;

-- khu vực thủ tục quản trị toàn quyền

-- thủ tục gán bất kỳ vai trò ứng dụng nào
DROP PROCEDURE IF EXISTS sp_super_assign_role;
DELIMITER $$
CREATE PROCEDURE sp_super_assign_role(
    IN p_actor_user_id INT UNSIGNED,
    IN p_target_user_id INT UNSIGNED,
    IN p_role_code VARCHAR(50)
)
SQL SECURITY DEFINER
MODIFIES SQL DATA
BEGIN
    DECLARE v_role_id SMALLINT UNSIGNED;

    SELECT id INTO v_role_id
    FROM roles
    WHERE code = p_role_code
    LIMIT 1;

    IF v_role_id IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Vai trò không tồn tại';
    END IF;

    INSERT IGNORE INTO user_roles (user_id, role_id, assigned_by_user_id)
    VALUES (p_target_user_id, v_role_id, p_actor_user_id);

    INSERT INTO audit_logs (actor_user_id, action, target_type, target_id, new_values, success)
    VALUES (
        p_actor_user_id,
        'SUPER_ASSIGN_ROLE',
        'USER',
        CAST(p_target_user_id AS CHAR),
        JSON_OBJECT('role_code', p_role_code),
        TRUE
    );
END$$
DELIMITER ;


-- khu vực thủ tục phiên của khách hàng

-- thủ tục thu hồi phiên của chính khách hàng
DROP PROCEDURE IF EXISTS sp_customer_revoke_own_session;
DELIMITER $$
CREATE PROCEDURE sp_customer_revoke_own_session(
    IN p_user_id INT UNSIGNED,
    IN p_session_id BIGINT UNSIGNED
)
SQL SECURITY DEFINER
MODIFIES SQL DATA
BEGIN
    UPDATE sessions
    SET revoked_at = CURRENT_TIMESTAMP,
        revoke_reason = 'USER_LOGOUT'
    WHERE id = p_session_id
      AND user_id = p_user_id
      AND revoked_at IS NULL;

    IF ROW_COUNT() = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Không tìm thấy phiên hợp lệ';
    END IF;
END$$
DELIMITER ;

-- khu vực thủ tục hình ảnh sách

-- thủ tục cập nhật hình ảnh sách
DROP PROCEDURE IF EXISTS sp_manager_update_book_image;
DELIMITER $$
CREATE PROCEDURE sp_manager_update_book_image(
    IN p_image_id BIGINT UNSIGNED,
    IN p_image_url VARCHAR(500),
    IN p_alt_text VARCHAR(255),
    IN p_display_order SMALLINT UNSIGNED
)
SQL SECURITY DEFINER
MODIFIES SQL DATA
BEGIN
    UPDATE book_images
    SET image_url = p_image_url,
        alt_text = NULLIF(TRIM(p_alt_text), ''),
        display_order = p_display_order
    WHERE id = p_image_id;
END$$
DELIMITER ;

-- thủ tục xóa hình ảnh sách
DROP PROCEDURE IF EXISTS sp_manager_remove_book_image;
DELIMITER $$
CREATE PROCEDURE sp_manager_remove_book_image(IN p_image_id BIGINT UNSIGNED)
SQL SECURITY DEFINER
MODIFIES SQL DATA
BEGIN
    DELETE FROM book_images
    WHERE id = p_image_id;
END$$
DELIMITER ;

-- khu vực thủ tục hủy đơn của quản lý

-- thủ tục hủy đơn chưa giao và chưa thanh toán
DROP PROCEDURE IF EXISTS sp_manager_cancel_order;
DELIMITER $$
CREATE PROCEDURE sp_manager_cancel_order(
    IN p_manager_user_id INT UNSIGNED,
    IN p_order_id BIGINT UNSIGNED,
    IN p_reason VARCHAR(500)
)
SQL SECURITY DEFINER
MODIFIES SQL DATA
BEGIN
    DECLARE v_status VARCHAR(16);
    DECLARE v_payment_status VARCHAR(16);
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    START TRANSACTION;

    SELECT status INTO v_status
    FROM orders
    WHERE id = p_order_id
    FOR UPDATE;

    IF v_status IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Không tìm thấy đơn hàng';
    END IF;

    IF v_status NOT IN ('PENDING', 'CONFIRMED', 'PROCESSING') THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Đơn hàng không còn được phép hủy theo nghiệp vụ quản lý';
    END IF;

    SELECT status INTO v_payment_status
    FROM payments
    WHERE order_id = p_order_id
    FOR UPDATE;

    IF v_payment_status IN ('PAID', 'REFUNDED') THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Đơn đã thanh toán cần xử lý hoàn tiền riêng';
    END IF;

    UPDATE books b
    INNER JOIN order_items oi ON oi.book_id = b.id
    SET b.stock_quantity = b.stock_quantity + oi.quantity
    WHERE oi.order_id = p_order_id;

    INSERT INTO inventory_transactions (
        book_id,
        supplier_id,
        order_id,
        actor_user_id,
        transaction_type,
        quantity_change,
        stock_before,
        stock_after,
        note
    )
    SELECT
        b.id,
        NULL,
        p_order_id,
        p_manager_user_id,
        'CANCEL_RESTORE',
        CAST(oi.quantity AS SIGNED),
        b.stock_quantity - oi.quantity,
        b.stock_quantity,
        COALESCE(NULLIF(TRIM(p_reason), ''), 'Quản lý hủy đơn')
    FROM order_items oi
    INNER JOIN books b ON b.id = oi.book_id
    WHERE oi.order_id = p_order_id;

    UPDATE orders
    SET status = 'CANCELLED',
        cancelled_at = CURRENT_TIMESTAMP
    WHERE id = p_order_id;

    UPDATE payments
    SET status = 'CANCELLED'
    WHERE order_id = p_order_id
      AND status IN ('PENDING', 'FAILED');

    INSERT INTO order_status_history (order_id, old_status, new_status, changed_by_user_id, reason)
    VALUES (p_order_id, v_status, 'CANCELLED', p_manager_user_id, COALESCE(NULLIF(TRIM(p_reason), ''), 'Quản lý hủy đơn'));

    COMMIT;
END$$
DELIMITER ;

-- khu vực thủ tục thanh toán momo

-- thủ tục ghi kết quả momo sau khi backend đã xác minh chữ ký
DROP PROCEDURE IF EXISTS sp_payment_record_momo_result;
DELIMITER $$
CREATE PROCEDURE sp_payment_record_momo_result(
    IN p_order_id BIGINT UNSIGNED,
    IN p_provider_request_id VARCHAR(128),
    IN p_provider_transaction_id VARCHAR(128),
    IN p_provider_event_id VARCHAR(128),
    IN p_success BOOLEAN,
    IN p_source_ip VARCHAR(45),
    IN p_payload JSON
)
SQL SECURITY DEFINER
MODIFIES SQL DATA
BEGIN
    DECLARE v_payment_id BIGINT UNSIGNED;
    DECLARE v_payment_method VARCHAR(16);
    DECLARE v_payment_status VARCHAR(16);
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    START TRANSACTION;

    SELECT id, payment_method, status
    INTO v_payment_id, v_payment_method, v_payment_status
    FROM payments
    WHERE order_id = p_order_id
    FOR UPDATE;

    IF v_payment_id IS NULL OR v_payment_method <> 'MOMO' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Không tìm thấy thanh toán MoMo hợp lệ';
    END IF;

    IF p_provider_event_id IS NOT NULL AND EXISTS (
        SELECT 1
        FROM payment_events
        WHERE provider_event_id = p_provider_event_id
    ) THEN
        COMMIT;
        SELECT v_payment_id AS payment_id, v_payment_status AS payment_status, TRUE AS duplicated_event;
    ELSE
        INSERT INTO payment_events (
            payment_id,
            event_type,
            provider_event_id,
            signature_valid,
            source_ip,
            payload
        ) VALUES (
            v_payment_id,
            'IPN_RECEIVED',
            p_provider_event_id,
            TRUE,
            p_source_ip,
            p_payload
        );

        IF p_success = TRUE THEN
            UPDATE payments
            SET status = 'PAID',
                provider_request_id = COALESCE(p_provider_request_id, provider_request_id),
                provider_transaction_id = COALESCE(p_provider_transaction_id, provider_transaction_id),
                paid_at = COALESCE(paid_at, CURRENT_TIMESTAMP)
            WHERE id = v_payment_id
              AND status <> 'REFUNDED';

            INSERT INTO payment_events (payment_id, event_type, provider_event_id, signature_valid, source_ip, payload)
            VALUES (v_payment_id, 'PAID', NULL, TRUE, p_source_ip, NULL);
        ELSE
            UPDATE payments
            SET status = 'FAILED',
                provider_request_id = COALESCE(p_provider_request_id, provider_request_id)
            WHERE id = v_payment_id
              AND status = 'PENDING';

            INSERT INTO payment_events (payment_id, event_type, provider_event_id, signature_valid, source_ip, payload)
            VALUES (v_payment_id, 'FAILED', NULL, TRUE, p_source_ip, NULL);
        END IF;

        SELECT status INTO v_payment_status
        FROM payments
        WHERE id = v_payment_id;

        COMMIT;

        SELECT v_payment_id AS payment_id, v_payment_status AS payment_status, FALSE AS duplicated_event;
    END IF;
END$$
DELIMITER ;

-- khu vực thủ tục quản trị an ninh bổ sung

-- thủ tục đặt trạng thái tài khoản không phải quản trị viên
DROP PROCEDURE IF EXISTS sp_security_set_non_admin_status;
DELIMITER $$
CREATE PROCEDURE sp_security_set_non_admin_status(
    IN p_actor_user_id INT UNSIGNED,
    IN p_target_user_id INT UNSIGNED,
    IN p_status VARCHAR(16),
    IN p_reason VARCHAR(500)
)
SQL SECURITY DEFINER
MODIFIES SQL DATA
BEGIN
    DECLARE v_old_status VARCHAR(16);
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    IF p_status NOT IN ('ACTIVE', 'DISABLED') THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Trạng thái tài khoản không hợp lệ';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM user_roles ur
        INNER JOIN roles r ON r.id = ur.role_id
        WHERE ur.user_id = p_target_user_id
          AND r.code IN ('SECURITY_ADMIN', 'OPERATIONS_ADMIN', 'SUPER_ADMIN')
    ) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Quản trị an ninh không được thay đổi trạng thái quản trị viên';
    END IF;

    START TRANSACTION;

    SELECT status INTO v_old_status
    FROM users
    WHERE id = p_target_user_id
    FOR UPDATE;

    UPDATE users
    SET status = p_status,
        locked_until = NULL
    WHERE id = p_target_user_id;

    IF p_status = 'DISABLED' THEN
        UPDATE sessions
        SET revoked_at = CURRENT_TIMESTAMP,
            revoke_reason = 'ACCOUNT_DISABLED'
        WHERE user_id = p_target_user_id
          AND revoked_at IS NULL;
    END IF;

    INSERT INTO audit_logs (actor_user_id, action, target_type, target_id, old_values, new_values, success)
    VALUES (
        p_actor_user_id,
        'SET_USER_STATUS',
        'USER',
        CAST(p_target_user_id AS CHAR),
        JSON_OBJECT('status', v_old_status),
        JSON_OBJECT('status', p_status, 'reason', p_reason),
        TRUE
    );

    COMMIT;
END$$
DELIMITER ;

-- thủ tục gỡ vai trò không phải quản trị viên
DROP PROCEDURE IF EXISTS sp_security_remove_non_admin_role;
DELIMITER $$
CREATE PROCEDURE sp_security_remove_non_admin_role(
    IN p_actor_user_id INT UNSIGNED,
    IN p_target_user_id INT UNSIGNED,
    IN p_role_code VARCHAR(50)
)
SQL SECURITY DEFINER
MODIFIES SQL DATA
BEGIN
    DECLARE v_role_id SMALLINT UNSIGNED;

    IF p_role_code NOT IN ('CUSTOMER', 'STAFF', 'BOOK_MANAGER') THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Quản trị an ninh không được gỡ vai trò quản trị viên';
    END IF;

    SELECT id INTO v_role_id
    FROM roles
    WHERE code = p_role_code
    LIMIT 1;

    DELETE FROM user_roles
    WHERE user_id = p_target_user_id
      AND role_id = v_role_id;

    INSERT INTO audit_logs (actor_user_id, action, target_type, target_id, old_values, success)
    VALUES (
        p_actor_user_id,
        'REMOVE_ROLE',
        'USER',
        CAST(p_target_user_id AS CHAR),
        JSON_OBJECT('role_code', p_role_code),
        TRUE
    );
END$$
DELIMITER ;

-- thủ tục tạo tài khoản không phải quản trị viên
DROP PROCEDURE IF EXISTS sp_security_create_non_admin_account;
DELIMITER $$
CREATE PROCEDURE sp_security_create_non_admin_account(
    IN p_actor_user_id INT UNSIGNED,
    IN p_username VARCHAR(100),
    IN p_email VARCHAR(255),
    IN p_full_name VARCHAR(150),
    IN p_role_code VARCHAR(50)
)
SQL SECURITY DEFINER
MODIFIES SQL DATA
BEGIN
    DECLARE v_user_id INT UNSIGNED;
    DECLARE v_role_id SMALLINT UNSIGNED;
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    IF p_role_code NOT IN ('CUSTOMER', 'STAFF', 'BOOK_MANAGER') THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Không được tạo tài khoản quản trị viên bằng thủ tục này';
    END IF;

    START TRANSACTION;

    INSERT INTO users (username, email, password_hash, full_name, status)
    VALUES (TRIM(p_username), LOWER(TRIM(p_email)), NULL, TRIM(p_full_name), 'PENDING');

    SET v_user_id = LAST_INSERT_ID();

    SELECT id INTO v_role_id
    FROM roles
    WHERE code = p_role_code
    LIMIT 1;

    INSERT INTO user_roles (user_id, role_id, assigned_by_user_id)
    VALUES (v_user_id, v_role_id, p_actor_user_id);

    INSERT INTO audit_logs (actor_user_id, action, target_type, target_id, new_values, success)
    VALUES (
        p_actor_user_id,
        'CREATE_NON_ADMIN_ACCOUNT',
        'USER',
        CAST(v_user_id AS CHAR),
        JSON_OBJECT('role_code', p_role_code),
        TRUE
    );

    COMMIT;

    SELECT v_user_id AS user_id;
END$$
DELIMITER ;

-- khu vực thủ tục quản trị toàn quyền bổ sung

-- thủ tục gỡ bất kỳ vai trò ứng dụng nào
DROP PROCEDURE IF EXISTS sp_super_remove_role;
DELIMITER $$
CREATE PROCEDURE sp_super_remove_role(
    IN p_actor_user_id INT UNSIGNED,
    IN p_target_user_id INT UNSIGNED,
    IN p_role_code VARCHAR(50)
)
SQL SECURITY DEFINER
MODIFIES SQL DATA
BEGIN
    DECLARE v_role_id SMALLINT UNSIGNED;

    SELECT id INTO v_role_id
    FROM roles
    WHERE code = p_role_code
    LIMIT 1;

    IF v_role_id IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Vai trò không tồn tại';
    END IF;

    DELETE FROM user_roles
    WHERE user_id = p_target_user_id
      AND role_id = v_role_id;

    INSERT INTO audit_logs (actor_user_id, action, target_type, target_id, old_values, success)
    VALUES (
        p_actor_user_id,
        'SUPER_REMOVE_ROLE',
        'USER',
        CAST(p_target_user_id AS CHAR),
        JSON_OBJECT('role_code', p_role_code),
        TRUE
    );
END$$
DELIMITER ;
