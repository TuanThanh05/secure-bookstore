USE BOOKSTORE_GROUP5_DB;

-- khu vực khung nhìn công khai

-- khung nhìn danh sách sách công khai
CREATE OR REPLACE SQL SECURITY DEFINER VIEW v_public_books AS
SELECT
    b.id AS book_id,
    b.name AS book_name,
    b.isbn,
    b.price,
    b.publication_year,
    b.description,
    c.id AS category_id,
    c.name AS category_name,
    p.id AS publisher_id,
    p.name AS publisher_name,
    a.id AS primary_author_id,
    a.name AS primary_author_name,
    CASE WHEN b.stock_quantity > 0 THEN 'IN_STOCK' ELSE 'OUT_OF_STOCK' END AS stock_status,
    (SELECT ROUND(AVG(r.rating), 2) FROM reviews r WHERE r.book_id = b.id AND r.status = 'PUBLISHED') AS average_rating,
    (SELECT COUNT(*) FROM reviews r WHERE r.book_id = b.id AND r.status = 'PUBLISHED') AS review_count
FROM books b
INNER JOIN categories c ON c.id = b.category_id
INNER JOIN publishers p ON p.id = b.publisher_id
LEFT JOIN book_authors ba ON ba.book_id = b.id AND ba.is_primary = TRUE
LEFT JOIN authors a ON a.id = ba.author_id
WHERE b.status = 'ACTIVE';

-- khung nhìn tác giả của sách công khai
CREATE OR REPLACE SQL SECURITY DEFINER VIEW v_public_book_authors AS
SELECT
    b.id AS book_id,
    a.id AS author_id,
    a.name AS author_name,
    ba.is_primary
FROM books b
INNER JOIN book_authors ba ON ba.book_id = b.id
INNER JOIN authors a ON a.id = ba.author_id
WHERE b.status = 'ACTIVE';

-- khung nhìn hình ảnh sách công khai
CREATE OR REPLACE SQL SECURITY DEFINER VIEW v_public_book_images AS
SELECT
    bi.id AS image_id,
    bi.book_id,
    bi.image_url,
    bi.alt_text,
    bi.display_order
FROM book_images bi
INNER JOIN books b ON b.id = bi.book_id
WHERE b.status = 'ACTIVE';

-- khung nhìn đánh giá công khai
CREATE OR REPLACE SQL SECURITY DEFINER VIEW v_public_reviews AS
SELECT
    r.id AS review_id,
    r.book_id,
    b.name AS book_name,
    u.username,
    r.rating,
    r.review_text,
    r.created_at,
    r.updated_at
FROM reviews r
INNER JOIN books b ON b.id = r.book_id
INNER JOIN users u ON u.id = r.user_id
WHERE r.status = 'PUBLISHED'
  AND b.status = 'ACTIVE';

-- khu vực khung nhìn xác thực nội bộ

-- khung nhìn tài khoản phục vụ xác thực
CREATE OR REPLACE SQL SECURITY DEFINER VIEW v_auth_users AS
SELECT
    id AS user_id,
    username,
    email,
    email_verified_at,
    password_hash,
    status,
    locked_until,
    last_login_at,
    created_at,
    updated_at
FROM users;

-- khung nhìn phiên phục vụ xác thực
CREATE OR REPLACE SQL SECURITY DEFINER VIEW v_auth_sessions AS
SELECT
    id AS session_id,
    user_id,
    token_hash,
    ip_address,
    user_agent,
    created_at,
    last_seen_at,
    expires_at,
    revoked_at,
    revoke_reason
FROM sessions;

-- khung nhìn lịch sử mật khẩu phục vụ xác thực
CREATE OR REPLACE SQL SECURITY DEFINER VIEW v_auth_password_history AS
SELECT
    id,
    user_id,
    password_hash,
    change_type,
    created_at
FROM password_history;

-- khung nhìn tài khoản đăng nhập bên thứ ba phục vụ xác thực
CREATE OR REPLACE SQL SECURITY DEFINER VIEW v_auth_external_identities AS
SELECT
    id,
    user_id,
    provider,
    provider_subject,
    provider_email,
    created_at,
    last_login_at
FROM external_identities;

-- khu vực khung nhìn khách hàng

-- khung nhìn hồ sơ khách hàng
CREATE OR REPLACE SQL SECURITY DEFINER VIEW v_customer_profile AS
SELECT
    id AS user_id,
    username,
    email,
    email_verified_at,
    full_name,
    phone,
    address,
    status,
    last_login_at,
    created_at,
    updated_at
FROM users;

-- khung nhìn giỏ hàng khách hàng
CREATE OR REPLACE SQL SECURITY DEFINER VIEW v_customer_cart AS
SELECT
    c.user_id,
    c.id AS cart_id,
    ci.book_id,
    b.name AS book_name,
    ci.quantity,
    b.price AS unit_price,
    ci.quantity * b.price AS line_total,
    b.stock_quantity,
    b.status AS book_status,
    ci.created_at,
    ci.updated_at
FROM carts c
INNER JOIN cart_items ci ON ci.cart_id = c.id
INNER JOIN books b ON b.id = ci.book_id;

-- khung nhìn đơn hàng khách hàng
CREATE OR REPLACE SQL SECURITY DEFINER VIEW v_customer_orders AS
SELECT
    o.user_id,
    o.id AS order_id,
    o.order_code,
    o.recipient_name,
    o.recipient_phone,
    o.shipping_address,
    o.status,
    o.total_amount,
    o.note,
    o.cancelled_at,
    o.completed_at,
    o.created_at,
    o.updated_at
FROM orders o;

-- khung nhìn chi tiết đơn hàng khách hàng
CREATE OR REPLACE SQL SECURITY DEFINER VIEW v_customer_order_items AS
SELECT
    o.user_id,
    oi.order_id,
    oi.id AS order_item_id,
    oi.book_id,
    oi.book_name,
    oi.quantity,
    oi.unit_price,
    oi.quantity * oi.unit_price AS line_total
FROM order_items oi
INNER JOIN orders o ON o.id = oi.order_id;

-- khung nhìn thanh toán khách hàng
CREATE OR REPLACE SQL SECURITY DEFINER VIEW v_customer_payments AS
SELECT
    o.user_id,
    p.id AS payment_id,
    p.order_id,
    p.payment_code,
    p.payment_method,
    p.status,
    p.amount,
    p.paid_at,
    p.refunded_at,
    p.created_at,
    p.updated_at
FROM payments p
INNER JOIN orders o ON o.id = p.order_id;

-- khung nhìn sách khách hàng đã mua
CREATE OR REPLACE SQL SECURITY DEFINER VIEW v_customer_purchased_books AS
SELECT
    o.user_id,
    oi.book_id,
    oi.book_name,
    SUM(oi.quantity) AS total_quantity,
    MAX(o.completed_at) AS latest_purchase_at
FROM orders o
INNER JOIN order_items oi ON oi.order_id = o.id
WHERE o.status = 'COMPLETED'
GROUP BY o.user_id, oi.book_id, oi.book_name;

-- khung nhìn phiên đăng nhập khách hàng
CREATE OR REPLACE SQL SECURITY DEFINER VIEW v_customer_sessions AS
SELECT
    id AS session_id,
    user_id,
    ip_address,
    user_agent,
    created_at,
    last_seen_at,
    expires_at,
    revoked_at,
    revoke_reason
FROM sessions;

-- khung nhìn đánh giá của khách hàng
CREATE OR REPLACE SQL SECURITY DEFINER VIEW v_customer_reviews AS
SELECT
    r.user_id,
    r.id AS review_id,
    r.book_id,
    b.name AS book_name,
    r.rating,
    r.review_text,
    r.status,
    r.created_at,
    r.updated_at
FROM reviews r
INNER JOIN books b ON b.id = r.book_id;

-- khu vực khung nhìn nhân viên

-- khung nhìn đơn hàng dành cho nhân viên
CREATE OR REPLACE SQL SECURITY DEFINER VIEW v_staff_orders AS
SELECT
    o.id AS order_id,
    o.order_code,
    o.user_id AS customer_user_id,
    u.username AS customer_username,
    o.recipient_name,
    o.recipient_phone,
    o.shipping_address,
    o.status,
    o.total_amount,
    o.note,
    o.created_at,
    o.updated_at
FROM orders o
INNER JOIN users u ON u.id = o.user_id;

-- khung nhìn chi tiết đơn hàng dành cho nhân viên
CREATE OR REPLACE SQL SECURITY DEFINER VIEW v_staff_order_items AS
SELECT
    oi.order_id,
    oi.id AS order_item_id,
    oi.book_id,
    oi.book_name,
    oi.quantity,
    oi.unit_price,
    oi.quantity * oi.unit_price AS line_total
FROM order_items oi;

-- khung nhìn trạng thái thanh toán dành cho nhân viên
CREATE OR REPLACE SQL SECURITY DEFINER VIEW v_staff_payment_status AS
SELECT
    p.order_id,
    p.payment_method,
    p.status,
    p.amount,
    p.paid_at,
    p.refunded_at
FROM payments p;

-- khu vực khung nhìn quản lý cửa hàng

-- khung nhìn tồn kho dành cho quản lý
CREATE OR REPLACE SQL SECURITY DEFINER VIEW v_manager_inventory AS
SELECT
    b.id AS book_id,
    b.name AS book_name,
    b.isbn,
    b.price,
    b.stock_quantity,
    b.status,
    c.name AS category_name,
    p.name AS publisher_name,
    a.name AS primary_author_name,
    b.updated_at
FROM books b
INNER JOIN categories c ON c.id = b.category_id
INNER JOIN publishers p ON p.id = b.publisher_id
LEFT JOIN book_authors ba ON ba.book_id = b.id AND ba.is_primary = TRUE
LEFT JOIN authors a ON a.id = ba.author_id;

-- khung nhìn biến động kho dành cho quản lý
CREATE OR REPLACE SQL SECURITY DEFINER VIEW v_manager_inventory_transactions AS
SELECT
    it.id AS inventory_transaction_id,
    it.book_id,
    b.name AS book_name,
    it.supplier_id,
    s.name AS supplier_name,
    it.order_id,
    it.actor_user_id,
    u.username AS actor_username,
    it.transaction_type,
    it.quantity_change,
    it.stock_before,
    it.stock_after,
    it.note,
    it.created_at
FROM inventory_transactions it
INNER JOIN books b ON b.id = it.book_id
LEFT JOIN suppliers s ON s.id = it.supplier_id
LEFT JOIN users u ON u.id = it.actor_user_id;

-- khung nhìn đơn hàng dành cho quản lý
CREATE OR REPLACE SQL SECURITY DEFINER VIEW v_manager_orders AS
SELECT
    o.id AS order_id,
    o.order_code,
    o.user_id AS customer_user_id,
    u.username AS customer_username,
    u.email AS customer_email,
    o.recipient_name,
    o.recipient_phone,
    o.shipping_address,
    o.status,
    o.total_amount,
    o.note,
    o.cancelled_at,
    o.completed_at,
    o.created_at,
    o.updated_at
FROM orders o
INNER JOIN users u ON u.id = o.user_id;

-- khung nhìn thanh toán dành cho quản lý
CREATE OR REPLACE SQL SECURITY DEFINER VIEW v_manager_payments AS
SELECT
    p.id AS payment_id,
    p.order_id,
    p.payment_code,
    p.payment_method,
    p.status,
    p.amount,
    p.provider_transaction_id,
    p.paid_at,
    p.refunded_at,
    p.created_at,
    p.updated_at
FROM payments p;

-- khung nhìn nhân viên cơ bản dành cho quản lý
CREATE OR REPLACE SQL SECURITY DEFINER VIEW v_manager_staff_basic AS
SELECT
    u.id AS user_id,
    u.username,
    u.email,
    u.full_name,
    u.phone,
    u.status,
    u.last_login_at,
    u.created_at,
    u.updated_at
FROM users u
INNER JOIN user_roles ur ON ur.user_id = u.id
INNER JOIN roles r ON r.id = ur.role_id
WHERE r.code = 'STAFF';

-- khung nhìn đánh giá dành cho quản lý
CREATE OR REPLACE SQL SECURITY DEFINER VIEW v_manager_reviews AS
SELECT
    r.id AS review_id,
    r.user_id,
    u.username,
    r.book_id,
    b.name AS book_name,
    r.rating,
    r.review_text,
    r.status,
    r.created_at,
    r.updated_at
FROM reviews r
INNER JOIN users u ON u.id = r.user_id
INNER JOIN books b ON b.id = r.book_id;

-- khu vực khung nhìn quản trị an ninh

-- khung nhìn người dùng dành cho quản trị an ninh
CREATE OR REPLACE SQL SECURITY DEFINER VIEW v_security_users AS
SELECT
    u.id AS user_id,
    u.username,
    u.email,
    u.email_verified_at,
    u.full_name,
    u.phone,
    u.status,
    u.locked_until,
    u.last_login_at,
    u.created_at,
    u.updated_at,
    GROUP_CONCAT(r.code ORDER BY r.code SEPARATOR ',') AS role_codes
FROM users u
LEFT JOIN user_roles ur ON ur.user_id = u.id
LEFT JOIN roles r ON r.id = ur.role_id
GROUP BY
    u.id,
    u.username,
    u.email,
    u.email_verified_at,
    u.full_name,
    u.phone,
    u.status,
    u.locked_until,
    u.last_login_at,
    u.created_at,
    u.updated_at;

-- khung nhìn phiên dành cho quản trị an ninh
CREATE OR REPLACE SQL SECURITY DEFINER VIEW v_security_sessions AS
SELECT
    s.id AS session_id,
    s.user_id,
    u.username,
    s.ip_address,
    s.user_agent,
    s.created_at,
    s.last_seen_at,
    s.expires_at,
    s.revoked_at,
    s.revoke_reason
FROM sessions s
INNER JOIN users u ON u.id = s.user_id;

-- khung nhìn lịch sử đăng nhập dành cho quản trị an ninh
CREATE OR REPLACE SQL SECURITY DEFINER VIEW v_security_login_attempts AS
SELECT
    la.id AS login_attempt_id,
    la.user_id,
    u.username,
    la.login_identifier,
    la.ip_address,
    la.user_agent,
    la.success,
    la.failure_reason,
    la.attempted_at
FROM login_attempts la
LEFT JOIN users u ON u.id = la.user_id;

-- khung nhìn sự kiện bảo mật dành cho quản trị an ninh
CREATE OR REPLACE SQL SECURITY DEFINER VIEW v_security_events AS
SELECT
    se.id AS security_event_id,
    se.user_id,
    u.username,
    se.event_type,
    se.severity,
    se.source_ip,
    se.user_agent,
    se.related_entity_type,
    se.related_entity_id,
    se.details,
    se.detected_at,
    se.resolved_at,
    se.resolved_by_user_id,
    ru.username AS resolved_by_username,
    se.resolution_note
FROM security_events se
LEFT JOIN users u ON u.id = se.user_id
LEFT JOIN users ru ON ru.id = se.resolved_by_user_id;

-- khung nhìn nhật ký kiểm toán dành cho quản trị an ninh
CREATE OR REPLACE SQL SECURITY DEFINER VIEW v_security_audit_logs AS
SELECT
    al.id AS audit_log_id,
    al.actor_user_id,
    u.username AS actor_username,
    al.action,
    al.target_type,
    al.target_id,
    al.old_values,
    al.new_values,
    al.success,
    al.ip_address,
    al.user_agent,
    al.request_id,
    al.created_at
FROM audit_logs al
LEFT JOIN users u ON u.id = al.actor_user_id;

-- khung nhìn lịch sử mật khẩu không lộ hàm băm
CREATE OR REPLACE SQL SECURITY DEFINER VIEW v_security_password_history_meta AS
SELECT
    id,
    user_id,
    change_type,
    created_at
FROM password_history;

-- khu vực khung nhìn vận hành

-- khung nhìn thống kê các bảng cơ sở dữ liệu
CREATE OR REPLACE SQL SECURITY DEFINER VIEW v_operations_table_statistics AS
SELECT
    TABLE_NAME AS table_name,
    ENGINE AS engine,
    TABLE_ROWS AS estimated_rows,
    DATA_LENGTH AS data_length_bytes,
    INDEX_LENGTH AS index_length_bytes,
    DATA_LENGTH + INDEX_LENGTH AS total_length_bytes,
    CREATE_TIME AS created_at,
    UPDATE_TIME AS updated_at
FROM information_schema.TABLES
WHERE TABLE_SCHEMA = 'BOOKSTORE_GROUP5_DB'
  AND TABLE_TYPE = 'BASE TABLE';

-- khung nhìn tổng dung lượng cơ sở dữ liệu
CREATE OR REPLACE SQL SECURITY DEFINER VIEW v_operations_database_summary AS
SELECT
    'BOOKSTORE_GROUP5_DB' AS database_name,
    COUNT(*) AS table_count,
    COALESCE(SUM(TABLE_ROWS), 0) AS estimated_rows,
    COALESCE(SUM(DATA_LENGTH), 0) AS data_length_bytes,
    COALESCE(SUM(INDEX_LENGTH), 0) AS index_length_bytes,
    COALESCE(SUM(DATA_LENGTH + INDEX_LENGTH), 0) AS total_length_bytes
FROM information_schema.TABLES
WHERE TABLE_SCHEMA = 'BOOKSTORE_GROUP5_DB'
  AND TABLE_TYPE = 'BASE TABLE';
