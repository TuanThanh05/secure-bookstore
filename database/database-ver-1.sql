DROP DATABASE IF EXISTS BOOKSTORE_GROUP5_DB;
CREATE DATABASE BOOKSTORE_GROUP5_DB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE BOOKSTORE_GROUP5_DB;

-- PHAN SACH

CREATE TABLE authors (
	id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    date_of_birth DATE NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE categories (
	id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE, 
    description TEXT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE publishers (
	id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE, 
    address VARCHAR(255) NULL,
    phone VARCHAR(20) NULL,
    email VARCHAR(255) NULL UNIQUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE suppliers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    address VARCHAR(255) NULL,
    phone VARCHAR(20) NULL,
    email VARCHAR(255) NULL UNIQUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE books (
	id INT AUTO_INCREMENT PRIMARY KEY, 
    category_id INT NOT NULL, 
    publisher_id INT NOT NULL,
    supplier_id INT NOT NULL,
    name VARCHAR(255) NOT NULL,
    isbn VARCHAR(20) NULL UNIQUE,
    price BIGINT UNSIGNED NOT NULL,
    stock_quantity INT UNSIGNED NOT NULL DEFAULT 0,
    publication_year SMALLINT UNSIGNED NULL,
    description TEXT NULL,	
    
    CONSTRAINT fk_books_category FOREIGN KEY (category_id) REFERENCES categories(id),
    CONSTRAINT fk_books_publishers FOREIGN KEY (publisher_id) REFERENCES publishers(id),
    CONSTRAINT fk_books_supplier FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
);

CREATE TABLE book_authors (
    book_id INT NOT NULL,
    author_id INT NOT NULL,
    PRIMARY KEY (book_id, author_id),
    
    CONSTRAINT fk_book_authors_book FOREIGN KEY (book_id) REFERENCES books(id),
    CONSTRAINT fk_book_authors_author FOREIGN KEY (author_id) REFERENCES authors(id)
);

CREATE TABLE book_images (
	id INT AUTO_INCREMENT PRIMARY KEY,
    book_id INT NOT NULL,
    image_url VARCHAR(500) NOT NULL, 
    display_order TINYINT UNSIGNED NOT NULL DEFAULT 0,
    is_primary BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_book_images_books FOREIGN KEY (book_id) REFERENCES books(id)
);

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_name VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    email_verified_at TIMESTAMP NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20) NULL UNIQUE,
    phone_verified_at TIMESTAMP NULL,
    personal_identifier_hash CHAR(64) NULL UNIQUE,
    address VARCHAR(255) NULL,
    status ENUM('ACTIVE', 'LOCKED', 'DISABLED') NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT chk_users_phone_verification CHECK ( phone IS NOT NULL OR phone_verified_at IS NULL)
);	

CREATE TABLE customers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NULL,
    guest_email VARCHAR(255) NULL,
    guest_phone VARCHAR(20) NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_customers_user FOREIGN KEY (user_id) REFERENCES users(id),
    CONSTRAINT uq_customers_user UNIQUE (user_id)
);

CREATE TABLE carts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
	status ENUM( 'DRAFT', 'CHECKED_OUT', 'CANCELLED' ) NOT NULL DEFAULT 'DRAFT',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_carts_customer FOREIGN KEY (customer_id) REFERENCES customers(id)
);

CREATE TABLE cart_items (
	id INT AUTO_INCREMENT PRIMARY KEY,
    cart_id INT NOT NULL,
    book_id INT NOT NULL,
    quantity INT UNSIGNED NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_cart_items_carts FOREIGN KEY (cart_id) REFERENCES carts(id),
    CONSTRAINT fk_cart_items_books FOREIGN KEY (book_id) REFERENCES books(id),
    CONSTRAINT uq_cart_items_book UNIQUE (cart_id, book_id),
    CONSTRAINT chk_cart_items_quantity CHECK (quantity > 0)
);

CREATE TABLE reviews (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    book_id INT NOT NULL,
    rating TINYINT UNSIGNED NOT NULL,
    comment TEXT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_reviews_customer FOREIGN KEY (customer_id) REFERENCES customers(id),
    CONSTRAINT fk_reviews_book FOREIGN KEY (book_id) REFERENCES books(id),
    CONSTRAINT chk_reviews_rating CHECK (rating BETWEEN 1 AND 5),
    CONSTRAINT uq_reviews_customer_book UNIQUE (customer_id, book_id)
);

CREATE TABLE orders (
	id	INT AUTO_INCREMENT PRIMARY KEY, 
    customer_id INT NOT NULL,
	cart_id INT NOT NULL,
	order_code VARCHAR(255) NOT NULL UNIQUE,
	recipient_name VARCHAR(50) NOT NULL,
	recipient_phone VARCHAR(20) NOT NULL,
	shipping_address VARCHAR(255) NOT NULL,
	order_channel ENUM('ONLINE', 'IN_STORE') DEFAULT 'ONLINE',
	status ENUM('PENDING', 'CONFIRMED', 'SHIPPING', 'COMPLETED', 'CANCELLED') NOT NULL DEFAULT 'PENDING',
	total_amount BIGINT UNSIGNED NOT NULL,
	note TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_orders_customers FOREIGN KEY (customer_id) REFERENCES customers(id),
	CONSTRAINT fk_orders_carts FOREIGN KEY (cart_id) REFERENCES carts(id),
    CONSTRAINT chk_orders_total_amount CHECK (total_amount >= 0)
);

CREATE TABLE order_items (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    book_id INT NOT NULL,
    quantity INT UNSIGNED NOT NULL,
    unit_price BIGINT UNSIGNED NOT NULL,

    CONSTRAINT fk_order_items_order FOREIGN KEY (order_id) REFERENCES orders(id),
    CONSTRAINT fk_order_items_book FOREIGN KEY (book_id) REFERENCES books(id),
    CONSTRAINT chk_order_items_quantity CHECK (quantity > 0),
    CONSTRAINT uq_order_items_book UNIQUE (order_id, book_id)
);

CREATE TABLE payments (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    payment_method ENUM('COD', 'BANK_TRANSFER', 'MOMO', 'VNPAY') NOT NULL,
    status ENUM('PENDING', 'PAID', 'FAILED', 'REFUNDED') NOT NULL DEFAULT 'PENDING',
    amount BIGINT UNSIGNED NOT NULL,
    transaction_code VARCHAR(255) NULL UNIQUE,
    paid_at TIMESTAMP NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_payments_order FOREIGN KEY (order_id) REFERENCES orders(id)
);

-- PHAN AN TOAN BAO MAT 

CREATE TABLE roles (
	id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE user_roles (
	id INT AUTO_INCREMENT PRIMARY KEY,
	user_id INT NOT NULL,
    role_id INT NOT NULL,
    
    CONSTRAINT fk_user_roles_users FOREIGN KEY (user_id) REFERENCES users(id),
    CONSTRAINT fk_user_roles_roles FOREIGN KEY (role_id) REFERENCES roles(id),
    CONSTRAINT uq_user_role UNIQUE (user_id, role_id)
);


CREATE TABLE sessions (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NULL,
    customer_id INT NULL,
    token_hash CHAR(64) NOT NULL UNIQUE,
    ip_address VARCHAR(45) NULL,
    user_agent VARCHAR(500) NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_seen_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    revoked_at TIMESTAMP NULL,

    CONSTRAINT fk_sessions_user FOREIGN KEY (user_id) REFERENCES users(id),
    CONSTRAINT fk_sessions_customer FOREIGN KEY (customer_id) REFERENCES customers(id),
    CONSTRAINT chk_sessions_identity CHECK (user_id IS NOT NULL OR customer_id IS NOT NULL),
    CONSTRAINT chk_sessions_expiry CHECK (expires_at > created_at)
);

CREATE TABLE login_attempts (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NULL,
    login_identifier VARCHAR(255) NOT NULL,
    ip_address VARCHAR(45) NOT NULL,
    user_agent VARCHAR(500) NULL,
    success BOOLEAN NOT NULL,
    failure_reason ENUM('INVALID_CREDENTIALS', 'ACCOUNT_LOCKED', 'ACCOUNT_DISABLED', 'RATE_LIMITED', 'OTHER') NULL,
    attempted_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_login_attempts_user FOREIGN KEY (user_id) REFERENCES users(id),
    CONSTRAINT chk_login_attempts_result CHECK ((success = TRUE AND failure_reason IS NULL) OR (success = FALSE AND failure_reason IS NOT NULL))
    
--  TAM CHUA DUNG TOI, HAN CHE
-- 	INDEX idx_login_attempts_ip_time (ip_address, attempted_at),
--  INDEX idx_login_attempts_user_time ( user_id, attempted_at),
--  INDEX idx_login_attempts_identifier_time (login_identifier, attempted_at)
);

CREATE TABLE password_action_requests (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    action_type ENUM('FORGOT_PASSWORD', 'CHANGE_PASSWORD') NOT NULL,
    status ENUM('PENDING', 'VERIFIED', 'COMPLETED', 'REJECTED', 'EXPIRED', 'CANCELLED') NOT NULL DEFAULT 'PENDING',
    requested_ip VARCHAR(45) NULL,
    user_agent VARCHAR(500) NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    verified_at TIMESTAMP NULL,
    completed_at TIMESTAMP NULL,
    
    CONSTRAINT fk_password_action_requests_user FOREIGN KEY (user_id) REFERENCES users(id),
    CONSTRAINT chk_password_action_requests_expiry CHECK (expires_at > created_at)
);

CREATE TABLE password_verification_challenges (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    password_action_request_id BIGINT NOT NULL,
    method ENUM('EMAIL_LINK', 'OTP_TELEGRAM', 'OTP_WHATSAPP', 'OTP_ZALO', 'IN_APP_PUSH') NOT NULL,
    status ENUM('PENDING', 'VERIFIED', 'REJECTED', 'EXPIRED', 'REVOKED') NOT NULL DEFAULT 'PENDING',
    secret_hash CHAR(64) NULL,
    attempt_count TINYINT UNSIGNED NOT NULL DEFAULT 0,
    max_attempts TINYINT UNSIGNED NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    verified_at TIMESTAMP NULL,
    rejected_at TIMESTAMP NULL,

    CONSTRAINT fk_password_verification_request FOREIGN KEY (password_action_request_id) REFERENCES password_action_requests(id),
    CONSTRAINT chk_password_verification_expiry CHECK (expires_at > created_at),
	CONSTRAINT chk_password_verification_attempts CHECK (max_attempts IS NULL OR attempt_count <= max_attempts)
);

CREATE TABLE email_verification_tokens (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    token_hash CHAR(64) NOT NULL UNIQUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    verified_at TIMESTAMP NULL,
    revoked_at TIMESTAMP NULL,
    requested_ip VARCHAR(45) NULL,
    user_agent VARCHAR(500) NULL,

    CONSTRAINT fk_email_verification_tokens_user FOREIGN KEY (user_id) REFERENCES users(id),
    CONSTRAINT chk_email_verification_tokens_expiry CHECK (expires_at > created_at),
    CONSTRAINT chk_email_verification_tokens_verified CHECK (verified_at IS NULL OR verified_at >= created_at),
    CONSTRAINT chk_email_verification_tokens_revoked CHECK (revoked_at IS NULL OR revoked_at >= created_at),
    CONSTRAINT chk_email_verification_tokens_terminal_state CHECK (NOT (verified_at IS NOT NULL AND revoked_at IS NOT NULL))
);

CREATE TABLE audit_logs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    actor_user_id INT NULL,
    action VARCHAR(100) NOT NULL,
    target_type VARCHAR(100) NOT NULL,
    target_id VARCHAR(100) NULL,
    old_values JSON NULL,
    new_values JSON NULL,
    ip_address VARCHAR(45) NULL,
    user_agent VARCHAR(500) NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_audit_logs_actor_user FOREIGN KEY (actor_user_id) REFERENCES users(id)
);

CREATE TABLE security_events (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NULL,
    event_type VARCHAR(100) NOT NULL,
    severity ENUM('INFO', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL') NOT NULL DEFAULT 'INFO',
    source_ip VARCHAR(45) NULL,
    user_agent VARCHAR(500) NULL,
    related_entity_type VARCHAR(100) NULL,
    related_entity_id VARCHAR(100) NULL,
    details JSON NULL,
    detected_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP NULL,

    CONSTRAINT fk_security_events_user FOREIGN KEY (user_id) REFERENCES users(id),
    CONSTRAINT chk_security_events_resolved CHECK (resolved_at IS NULL OR resolved_at >= detected_at)
);

CREATE TABLE inventory_transactions (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    book_id INT NOT NULL,
    transaction_type ENUM('IMPORT', 'SALE', 'RETURN', 'ADJUSTMENT', 'CANCEL_RESTORE') NOT NULL,
    quantity_change INT NOT NULL,
    stock_before INT UNSIGNED NOT NULL,
    stock_after INT UNSIGNED NOT NULL,
    reference_type VARCHAR(100) NULL,
    reference_id VARCHAR(100) NULL,
    actor_user_id INT NULL,
    note VARCHAR(500) NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_inventory_transactions_book FOREIGN KEY (book_id) REFERENCES books(id),
    CONSTRAINT fk_inventory_transactions_actor FOREIGN KEY (actor_user_id) REFERENCES users(id),
    CONSTRAINT chk_inventory_transactions_quantity CHECK (quantity_change <> 0),
    CONSTRAINT chk_inventory_transactions_balance CHECK (CAST(stock_before AS SIGNED) + quantity_change = CAST(stock_after AS SIGNED))
);

CREATE TABLE order_status_history (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    old_status ENUM('PENDING', 'CONFIRMED', 'SHIPPING', 'COMPLETED', 'CANCELLED') NULL,
    new_status ENUM('PENDING', 'CONFIRMED', 'SHIPPING', 'COMPLETED', 'CANCELLED') NOT NULL,
    changed_by_user_id INT NULL,
    reason VARCHAR(500) NULL,
    changed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_order_status_history_order FOREIGN KEY (order_id) REFERENCES orders(id),
    CONSTRAINT fk_order_status_history_user FOREIGN KEY (changed_by_user_id) REFERENCES users(id),
    CONSTRAINT chk_order_status_history_change CHECK (old_status IS NULL OR old_status <> new_status)
);

CREATE TABLE payment_events (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    payment_id BIGINT NOT NULL,
    event_type ENUM( 'CREATED', 'CALLBACK_RECEIVED', 'WEBHOOK_RECEIVED', 'VERIFICATION_SUCCEEDED', 'VERIFICATION_FAILED', 'PAID', 'FAILED', 'REFUND_REQUESTED', 'REFUNDED') NOT NULL,
    event_status ENUM('RECEIVED', 'ACCEPTED', 'REJECTED', 'PROCESSED') NOT NULL DEFAULT 'RECEIVED',
    provider VARCHAR(100) NULL,
    provider_transaction_code VARCHAR(255) NULL,
    amount BIGINT UNSIGNED NULL,
    signature_valid BOOLEAN NULL,
    source_ip VARCHAR(45) NULL,
    details JSON NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_payment_events_payment FOREIGN KEY (payment_id) REFERENCES payments(id)
);

CREATE TABLE email_change_requests (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    request_type ENUM('NORMAL_CHANGE', 'PHONE_RECOVERY', 'MANUAL_RECOVERY') NOT NULL,
    old_email VARCHAR(255) NOT NULL,
    new_email VARCHAR(255) NOT NULL,
    status ENUM('PENDING','OLD_EMAIL_VERIFIED', 'RECOVERY_VERIFIED', 'NEW_EMAIL_VERIFIED', 'WAITING', 'APPROVED', 'COMPLETED', 'REJECTED', 'CANCELLED', 'EXPIRED') NOT NULL DEFAULT 'PENDING',
    requested_ip VARCHAR(45) NULL,
    user_agent VARCHAR(500) NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    old_email_verified_at TIMESTAMP NULL,
    recovery_verified_at TIMESTAMP NULL,
    new_email_verified_at TIMESTAMP NULL,
    identity_verified_by_user_id INT NULL,
    identity_verified_at TIMESTAMP NULL,
    approved_by_user_id INT NULL,
    approved_at TIMESTAMP NULL,
    effective_after TIMESTAMP NULL,
    completed_at TIMESTAMP NULL,
    
    CONSTRAINT fk_email_change_user FOREIGN KEY (user_id) REFERENCES users(id),
    CONSTRAINT fk_email_change_identity_verifier FOREIGN KEY (identity_verified_by_user_id) REFERENCES users(id),
	CONSTRAINT fk_email_change_approver FOREIGN KEY (approved_by_user_id) REFERENCES users(id),
    CONSTRAINT chk_email_change_email CHECK (old_email <> new_email),
    CONSTRAINT chk_email_change_expiry CHECK (expires_at > created_at),
    CONSTRAINT chk_email_change_identity_time CHECK (identity_verified_at IS NULL OR identity_verified_at >= created_at),
    CONSTRAINT chk_email_change_approval_time CHECK (approved_at IS NULL OR approved_at >= created_at),
    CONSTRAINT chk_email_change_different_staff CHECK (identity_verified_by_user_id IS NULL OR approved_by_user_id IS NULL OR identity_verified_by_user_id <> approved_by_user_id),
    CONSTRAINT chk_email_change_effective CHECK (effective_after IS NULL OR approved_at IS NULL OR effective_after >= approved_at),
    CONSTRAINT chk_email_change_completed CHECK (completed_at IS NULL OR completed_at >= created_at)
);

CREATE TABLE log_integrity_batches (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    log_type ENUM('AUDIT_LOG', 'SECURITY_EVENT', 'PAYMENT_EVENT') NOT NULL,
    first_record_id BIGINT NOT NULL,
    last_record_id BIGINT NOT NULL,
    record_count INT UNSIGNED NOT NULL,
    previous_batch_hash CHAR(64) NOT NULL,
    batch_hash CHAR(64) NOT NULL,
    hash_version TINYINT UNSIGNED NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_log_integrity_batch_range CHECK (last_record_id >= first_record_id),
    CONSTRAINT chk_log_integrity_batch_count CHECK (record_count > 0),
    CONSTRAINT uq_log_integrity_batch_hash UNIQUE (log_type, batch_hash),
    CONSTRAINT uq_log_integrity_batch_range UNIQUE (log_type, first_record_id, last_record_id)
);