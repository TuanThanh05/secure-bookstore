DROP DATABASE IF EXISTS BOOKSTORE_GROUP5_DB;
CREATE DATABASE IF NOT EXISTS BOOKSTORE_GROUP5_DB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE BOOKSTORE_GROUP5_DB;

-- khu vực danh mục sách

-- bảng tác giả
CREATE TABLE authors (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    date_of_birth DATE NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- bảng thể loại
CREATE TABLE categories (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT uq_categories_name UNIQUE (name)
) ENGINE=InnoDB;

-- bảng nhà xuất bản
CREATE TABLE publishers (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    address VARCHAR(500) NULL,
    phone VARCHAR(20) NULL,
    email VARCHAR(255) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    CONSTRAINT uq_publishers_name UNIQUE (name),
    CONSTRAINT uq_publishers_email UNIQUE (email)
) ENGINE=InnoDB;

-- bảng nhà cung cấp
CREATE TABLE suppliers (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    address VARCHAR(500) NULL,
    phone VARCHAR(20) NULL,
    email VARCHAR(255) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT uq_suppliers_name UNIQUE (name),
    CONSTRAINT uq_suppliers_email UNIQUE (email)
) ENGINE=InnoDB;

-- bảng sách
CREATE TABLE books (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    category_id INT UNSIGNED NOT NULL,
    publisher_id INT UNSIGNED NOT NULL,
    name VARCHAR(255) NOT NULL,
    isbn VARCHAR(20) NULL,
    price BIGINT UNSIGNED NOT NULL,
    stock_quantity INT UNSIGNED NOT NULL DEFAULT 0,
    publication_year SMALLINT UNSIGNED NULL,
    description TEXT NULL,
    status ENUM('DRAFT', 'ACTIVE', 'INACTIVE') NOT NULL DEFAULT 'DRAFT',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT uq_books_isbn UNIQUE (isbn),
    CONSTRAINT fk_books_category FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_books_publisher FOREIGN KEY (publisher_id) REFERENCES publishers(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT chk_books_price CHECK (price > 0),
    CONSTRAINT chk_books_publication_year CHECK (publication_year IS NULL OR publication_year BETWEEN 1000 AND 9999),
    INDEX idx_books_category_status (category_id, status),
    INDEX idx_books_name (name)
) ENGINE=InnoDB;

-- bảng liên kết sách và tác giả
CREATE TABLE book_authors (
    book_id INT UNSIGNED NOT NULL,
    author_id INT UNSIGNED NOT NULL,
    is_primary BOOLEAN NOT NULL DEFAULT FALSE,
    primary_book_id INT UNSIGNED GENERATED ALWAYS AS (CASE WHEN is_primary = TRUE THEN book_id ELSE NULL END) STORED,

    PRIMARY KEY (book_id, author_id),
    CONSTRAINT uq_book_authors_primary UNIQUE (primary_book_id),
    CONSTRAINT fk_book_authors_book FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_book_authors_author FOREIGN KEY (author_id) REFERENCES authors(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT chk_book_authors_is_primary CHECK (is_primary IN (0, 1)),
    INDEX idx_book_authors_author (author_id)
) ENGINE=InnoDB;

-- bảng hình ảnh sách
CREATE TABLE book_images (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    book_id INT UNSIGNED NOT NULL,
    image_url VARCHAR(500) NOT NULL,
    alt_text VARCHAR(255) NULL,
    display_order SMALLINT UNSIGNED NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT uq_book_images_order UNIQUE (book_id, display_order),
    CONSTRAINT fk_book_images_book FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

-- khu vực người dùng và xác thực

-- bảng người dùng
CREATE TABLE users (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL,
    email_verified_at DATETIME NULL,
    password_hash VARCHAR(255) NULL,
    full_name VARCHAR(150) NOT NULL,
    phone VARCHAR(20) NULL,
    address VARCHAR(500) NULL,
    status ENUM('ACTIVE', 'LOCKED', 'DISABLED') NOT NULL DEFAULT 'ACTIVE',
    locked_until DATETIME NULL,
    last_login_at DATETIME NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT uq_users_username UNIQUE (username),
    CONSTRAINT uq_users_email UNIQUE (email),
    CONSTRAINT uq_users_phone UNIQUE (phone),
    CONSTRAINT chk_users_username CHECK (CHAR_LENGTH(TRIM(username)) BETWEEN 3 AND 100),
    CONSTRAINT chk_users_email_verified_at CHECK (email_verified_at IS NULL OR email_verified_at >= created_at),
    CONSTRAINT chk_users_locked_until CHECK (locked_until IS NULL OR locked_until >= created_at),
    CONSTRAINT chk_users_last_login_at CHECK (last_login_at IS NULL OR last_login_at >= created_at)
) ENGINE=InnoDB;

-- bảng tài khoản đăng nhập bên thứ ba
CREATE TABLE external_identities (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id INT UNSIGNED NOT NULL,
    provider ENUM('GOOGLE') NOT NULL,
    provider_subject VARCHAR(255) NOT NULL,
    provider_email VARCHAR(255) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_login_at DATETIME NULL,

    CONSTRAINT uq_external_identities_provider_subject UNIQUE (provider, provider_subject),
    CONSTRAINT uq_external_identities_user_provider UNIQUE (user_id, provider),
    CONSTRAINT fk_external_identities_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT chk_external_identities_last_login CHECK (last_login_at IS NULL OR last_login_at >= created_at)
) ENGINE=InnoDB;

-- bảng vai trò
CREATE TABLE roles (
    id SMALLINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(50) NOT NULL,
    name VARCHAR(100) NOT NULL,
    description VARCHAR(500) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_roles_code UNIQUE (code),
    CONSTRAINT uq_roles_name UNIQUE (name)
) ENGINE=InnoDB;

-- bảng gán vai trò người dùng
CREATE TABLE user_roles (
    user_id INT UNSIGNED NOT NULL,
    role_id SMALLINT UNSIGNED NOT NULL,
    assigned_by_user_id INT UNSIGNED NULL,
    assigned_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, role_id),
    CONSTRAINT fk_user_roles_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_user_roles_role FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_user_roles_assigner FOREIGN KEY (assigned_by_user_id) REFERENCES users(id) ON DELETE SET NULL ON UPDATE CASCADE,
    INDEX idx_user_roles_role (role_id)
) ENGINE=InnoDB;

-- bảng lịch sử mật khẩu
CREATE TABLE password_history (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id INT UNSIGNED NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    change_type ENUM('REGISTER', 'CHANGE', 'RESET') NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_password_history_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE,
    INDEX idx_password_history_user_time (user_id, created_at)
) ENGINE=InnoDB;

-- bảng phiên đăng nhập
CREATE TABLE sessions (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id INT UNSIGNED NOT NULL,
    token_hash CHAR(64) NOT NULL,
    ip_address VARCHAR(45) NULL,
    user_agent VARCHAR(500) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_seen_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME NOT NULL,
    revoked_at DATETIME NULL,
    revoke_reason VARCHAR(255) NULL,
    CONSTRAINT uq_sessions_token_hash UNIQUE (token_hash),
    CONSTRAINT fk_sessions_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT chk_sessions_last_seen CHECK (last_seen_at >= created_at),
    CONSTRAINT chk_sessions_expiry CHECK (expires_at > created_at),
    CONSTRAINT chk_sessions_revoked CHECK (revoked_at IS NULL OR revoked_at >= created_at),
    INDEX idx_sessions_user_expiry (user_id, expires_at),
    INDEX idx_sessions_expiry_revoked (expires_at, revoked_at)
) ENGINE=InnoDB;

-- bảng lịch sử đăng nhập
CREATE TABLE login_attempts (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id INT UNSIGNED NULL,
    login_identifier VARCHAR(255) NOT NULL,
    ip_address VARCHAR(45) NOT NULL,
    user_agent VARCHAR(500) NULL,
    success BOOLEAN NOT NULL,
    failure_reason ENUM('INVALID_CREDENTIALS', 'ACCOUNT_LOCKED', 'ACCOUNT_DISABLED', 'RATE_LIMITED', 'CAPTCHA_FAILED', 'OTHER') NULL,
    attempted_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_login_attempts_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT chk_login_attempts_result CHECK ((success = TRUE AND failure_reason IS NULL) OR (success = FALSE AND failure_reason IS NOT NULL)),
    INDEX idx_login_attempts_ip_time (ip_address, attempted_at),
    INDEX idx_login_attempts_user_time (user_id, attempted_at),
    INDEX idx_login_attempts_identifier_time (login_identifier, attempted_at)
) ENGINE=InnoDB;

-- bảng mã xác minh email
CREATE TABLE email_verification_tokens (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id INT UNSIGNED NOT NULL,
    purpose ENUM('VERIFY_ACCOUNT', 'CHANGE_EMAIL') NOT NULL,
    target_email VARCHAR(255) NOT NULL,
    token_hash CHAR(64) NOT NULL,
    requested_ip VARCHAR(45) NULL,
    user_agent VARCHAR(500) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME NOT NULL,
    consumed_at DATETIME NULL,
    revoked_at DATETIME NULL,

    CONSTRAINT uq_email_verification_tokens_hash UNIQUE (token_hash),
    CONSTRAINT fk_email_verification_tokens_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT chk_email_verification_tokens_expiry CHECK (expires_at > created_at),
    CONSTRAINT chk_email_verification_tokens_consumed CHECK (consumed_at IS NULL OR consumed_at >= created_at),
    CONSTRAINT chk_email_verification_tokens_revoked CHECK (revoked_at IS NULL OR revoked_at >= created_at),
    CONSTRAINT chk_email_verification_tokens_terminal CHECK (NOT (consumed_at IS NOT NULL AND revoked_at IS NOT NULL)),
    INDEX idx_email_verification_tokens_user_purpose (user_id, purpose, created_at)
) ENGINE=InnoDB;

-- bảng mã đặt lại mật khẩu
CREATE TABLE password_reset_tokens (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id INT UNSIGNED NOT NULL,
    token_hash CHAR(64) NOT NULL,
    requested_ip VARCHAR(45) NULL,
    user_agent VARCHAR(500) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME NOT NULL,
    used_at DATETIME NULL,
    revoked_at DATETIME NULL,

    CONSTRAINT uq_password_reset_tokens_hash UNIQUE (token_hash),
    CONSTRAINT fk_password_reset_tokens_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT chk_password_reset_tokens_expiry CHECK (expires_at > created_at),
    CONSTRAINT chk_password_reset_tokens_used CHECK (used_at IS NULL OR used_at >= created_at),
    CONSTRAINT chk_password_reset_tokens_revoked CHECK (revoked_at IS NULL OR revoked_at >= created_at),
    CONSTRAINT chk_password_reset_tokens_terminal CHECK (NOT (used_at IS NOT NULL AND revoked_at IS NOT NULL)),
    INDEX idx_password_reset_tokens_user_time (user_id, created_at)
) ENGINE=InnoDB;

-- khu vực giỏ hàng và đơn hàng

-- bảng giỏ hàng
CREATE TABLE carts (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id INT UNSIGNED NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT uq_carts_user UNIQUE (user_id),
    CONSTRAINT fk_carts_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

-- bảng sản phẩm trong giỏ hàng
CREATE TABLE cart_items (
    cart_id BIGINT UNSIGNED NOT NULL,
    book_id INT UNSIGNED NOT NULL,
    quantity INT UNSIGNED NOT NULL DEFAULT 1,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    PRIMARY KEY (cart_id, book_id),
    CONSTRAINT fk_cart_items_cart FOREIGN KEY (cart_id) REFERENCES carts(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_cart_items_book FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT chk_cart_items_quantity CHECK (quantity > 0),
    INDEX idx_cart_items_book (book_id)
) ENGINE=InnoDB;

-- bảng đơn hàng
CREATE TABLE orders (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id INT UNSIGNED NOT NULL,
    order_code VARCHAR(32) NOT NULL,
    recipient_name VARCHAR(150) NOT NULL,
    recipient_phone VARCHAR(20) NOT NULL,
    shipping_address VARCHAR(500) NOT NULL,
    status ENUM('PENDING', 'CONFIRMED', 'PROCESSING', 'SHIPPING', 'COMPLETED', 'CANCELLED') NOT NULL DEFAULT 'PENDING',
    total_amount BIGINT UNSIGNED NOT NULL,
    note VARCHAR(1000) NULL,
    cancelled_at DATETIME NULL,
    completed_at DATETIME NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT uq_orders_code UNIQUE (order_code),
    CONSTRAINT fk_orders_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT chk_orders_total_amount CHECK (total_amount > 0),
    CONSTRAINT chk_orders_cancelled_at CHECK (cancelled_at IS NULL OR cancelled_at >= created_at),
    CONSTRAINT chk_orders_completed_at CHECK (completed_at IS NULL OR completed_at >= created_at),
    CONSTRAINT chk_orders_terminal_time CHECK (NOT (cancelled_at IS NOT NULL AND completed_at IS NOT NULL)),
    INDEX idx_orders_user_created (user_id, created_at),
    INDEX idx_orders_status_created (status, created_at)
) ENGINE=InnoDB;

-- bảng chi tiết đơn hàng
CREATE TABLE order_items (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    order_id BIGINT UNSIGNED NOT NULL,
    book_id INT UNSIGNED NOT NULL,
    book_name VARCHAR(255) NOT NULL,
    quantity INT UNSIGNED NOT NULL,
    unit_price BIGINT UNSIGNED NOT NULL,

    CONSTRAINT uq_order_items_order_book UNIQUE (order_id, book_id),
    CONSTRAINT fk_order_items_order FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_order_items_book FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT chk_order_items_quantity CHECK (quantity > 0),
    CONSTRAINT chk_order_items_unit_price CHECK (unit_price > 0),
    INDEX idx_order_items_book (book_id)
) ENGINE=InnoDB;

-- bảng lịch sử trạng thái đơn hàng
CREATE TABLE order_status_history (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    order_id BIGINT UNSIGNED NOT NULL,
    old_status ENUM('PENDING', 'CONFIRMED', 'PROCESSING', 'SHIPPING', 'COMPLETED', 'CANCELLED') NULL,
    new_status ENUM('PENDING', 'CONFIRMED', 'PROCESSING', 'SHIPPING', 'COMPLETED', 'CANCELLED') NOT NULL,
    changed_by_user_id INT UNSIGNED NULL,
    reason VARCHAR(500) NULL,
    changed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_order_status_history_order FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_order_status_history_user FOREIGN KEY (changed_by_user_id) REFERENCES users(id) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT chk_order_status_history_change CHECK (old_status IS NULL OR old_status <> new_status),
    INDEX idx_order_status_history_order_time (order_id, changed_at)
) ENGINE=InnoDB;

-- khu vực thanh toán

-- bảng thanh toán
CREATE TABLE payments (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    order_id BIGINT UNSIGNED NOT NULL,
    payment_code VARCHAR(64) NOT NULL,
    payment_method ENUM('COD', 'MOMO') NOT NULL,
    status ENUM('PENDING', 'PAID', 'FAILED', 'CANCELLED', 'REFUNDED') NOT NULL DEFAULT 'PENDING',
    amount BIGINT UNSIGNED NOT NULL,
    provider_request_id VARCHAR(128) NULL,
    provider_transaction_id VARCHAR(128) NULL,
    paid_at DATETIME NULL,
    refunded_at DATETIME NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT uq_payments_code UNIQUE (payment_code),
    CONSTRAINT uq_payments_provider_request UNIQUE (provider_request_id),
    CONSTRAINT uq_payments_provider_transaction UNIQUE (provider_transaction_id),
    CONSTRAINT fk_payments_order FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT chk_payments_amount CHECK (amount > 0),
    CONSTRAINT chk_payments_paid_at CHECK ((status IN ('PAID', 'REFUNDED') AND paid_at IS NOT NULL) OR (status NOT IN ('PAID', 'REFUNDED') AND paid_at IS NULL)),
    CONSTRAINT chk_payments_refunded_at CHECK ((status = 'REFUNDED' AND refunded_at IS NOT NULL) OR (status <> 'REFUNDED' AND refunded_at IS NULL)),
    INDEX idx_payments_order_created (order_id, created_at),
    INDEX idx_payments_status_created (status, created_at)
) ENGINE=InnoDB;

-- bảng sự kiện thanh toán
CREATE TABLE payment_events (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    payment_id BIGINT UNSIGNED NOT NULL,
    event_type ENUM('CREATED', 'RETURN_RECEIVED', 'IPN_RECEIVED', 'VERIFIED', 'PAID', 'FAILED', 'REFUND_REQUESTED', 'REFUNDED') NOT NULL,
    provider_event_id VARCHAR(128) NULL,
    signature_valid BOOLEAN NULL,
    source_ip VARCHAR(45) NULL,
    payload JSON NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_payment_events_provider_event UNIQUE (provider_event_id),
    CONSTRAINT fk_payment_events_payment FOREIGN KEY (payment_id) REFERENCES payments(id) ON DELETE CASCADE ON UPDATE CASCADE,
    INDEX idx_payment_events_payment_time (payment_id, created_at),
    INDEX idx_payment_events_type_time (event_type, created_at)
) ENGINE=InnoDB;

-- khu vực kho hàng

-- bảng biến động tồn kho
CREATE TABLE inventory_transactions (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    book_id INT UNSIGNED NOT NULL,
    supplier_id INT UNSIGNED NULL,
    order_id BIGINT UNSIGNED NULL,
    actor_user_id INT UNSIGNED NULL,
    transaction_type ENUM('IMPORT', 'SALE', 'CANCEL_RESTORE', 'ADJUSTMENT') NOT NULL,
    quantity_change INT NOT NULL,
    stock_before INT UNSIGNED NOT NULL,
    stock_after INT UNSIGNED NOT NULL,
    note VARCHAR(500) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_inventory_transactions_book FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_inventory_transactions_supplier FOREIGN KEY (supplier_id) REFERENCES suppliers(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_inventory_transactions_order FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_inventory_transactions_actor FOREIGN KEY (actor_user_id) REFERENCES users(id) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT chk_inventory_transactions_quantity CHECK (quantity_change <> 0),
    CONSTRAINT chk_inventory_transactions_balance CHECK (CAST(stock_before AS SIGNED) + quantity_change = CAST(stock_after AS SIGNED)),
    CONSTRAINT chk_inventory_transactions_import CHECK (transaction_type <> 'IMPORT' OR (quantity_change > 0 AND supplier_id IS NOT NULL)),
    CONSTRAINT chk_inventory_transactions_sale CHECK (transaction_type <> 'SALE' OR (quantity_change < 0 AND order_id IS NOT NULL)),
    CONSTRAINT chk_inventory_transactions_cancel_restore CHECK (transaction_type <> 'CANCEL_RESTORE' OR (quantity_change > 0 AND order_id IS NOT NULL)),
    INDEX idx_inventory_transactions_book_time (book_id, created_at),
    INDEX idx_inventory_transactions_order (order_id),
    INDEX idx_inventory_transactions_supplier (supplier_id)
) ENGINE=InnoDB;

-- khu vực nghiệp vụ mở rộng

-- bảng đánh giá sách
CREATE TABLE reviews (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id INT UNSIGNED NOT NULL,
    book_id INT UNSIGNED NOT NULL,
    rating TINYINT UNSIGNED NOT NULL,
    review_text TEXT NULL,
    status ENUM('PUBLISHED', 'HIDDEN') NOT NULL DEFAULT 'PUBLISHED',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT uq_reviews_user_book UNIQUE (user_id, book_id),
    CONSTRAINT fk_reviews_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_reviews_book FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT chk_reviews_rating CHECK (rating BETWEEN 1 AND 5),
    INDEX idx_reviews_book_status (book_id, status)
) ENGINE=InnoDB;

-- khu vực kiểm toán và sự kiện bảo mật

-- bảng nhật ký kiểm toán
CREATE TABLE audit_logs (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    actor_user_id INT UNSIGNED NULL,
    action VARCHAR(100) NOT NULL,
    target_type VARCHAR(100) NOT NULL,
    target_id VARCHAR(100) NULL,
    old_values JSON NULL,
    new_values JSON NULL,
    success BOOLEAN NOT NULL DEFAULT TRUE,
    ip_address VARCHAR(45) NULL,
    user_agent VARCHAR(500) NULL,
    request_id VARCHAR(64) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_audit_logs_actor FOREIGN KEY (actor_user_id) REFERENCES users(id) ON DELETE SET NULL ON UPDATE CASCADE,
    INDEX idx_audit_logs_actor_time (actor_user_id, created_at),
    INDEX idx_audit_logs_target_time (target_type, target_id, created_at),
    INDEX idx_audit_logs_action_time (action, created_at)
) ENGINE=InnoDB;

-- bảng sự kiện bảo mật
CREATE TABLE security_events (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id INT UNSIGNED NULL,
    event_type VARCHAR(100) NOT NULL,
    severity ENUM('INFO', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL') NOT NULL DEFAULT 'INFO',
    source_ip VARCHAR(45) NULL,
    user_agent VARCHAR(500) NULL,
    related_entity_type VARCHAR(100) NULL,
    related_entity_id VARCHAR(100) NULL,
    details JSON NULL,
    detected_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resolved_at DATETIME NULL,

    CONSTRAINT fk_security_events_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT chk_security_events_resolved CHECK (resolved_at IS NULL OR resolved_at >= detected_at),
    INDEX idx_security_events_severity_time (severity, detected_at),
    INDEX idx_security_events_type_time (event_type, detected_at),
    INDEX idx_security_events_user_time (user_id, detected_at)
) ENGINE=InnoDB;