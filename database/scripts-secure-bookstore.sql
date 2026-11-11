-- =====================================================================
-- secure-bookstore – Lược đồ CSDL (bản thiết kế chốt)
-- Hệ quản trị: MySQL 8.0.16+ (cần bản hỗ trợ CHECK constraint)
-- Vị trí đề xuất trong repo: database/init/01_schema.sql
--
-- Quy ước:
--   - Tên bảng, cột: tiếng Anh. Chú thích: tiếng Việt.
--   - Tên bảng theo quy ước của Django: <app>_<model> (accounts_user, catalog_book...)
--     để về sau viết models.py khớp đúng tên, không phải đổi.
--   - Tiền tệ: VND, lưu số nguyên (INT UNSIGNED), không dùng số thực.
--   - Thời gian: DATETIME(6), lưu theo UTC (Django USE_TZ = True).
--   - Cột *_encrypted: dữ liệu đã mã hóa AES-GCM ở tầng ứng dụng, lưu dạng base64.
--   - Mọi bảng dùng InnoDB (cần cho transaction, khóa dòng, khóa ngoại).
--
-- Script này CHỈ tạo bảng, ràng buộc, chỉ mục.
-- Các phần khác nằm ở file riêng trong database/:
--   procedures/ (sp_place_order, sp_confirm_payment, sp_cancel_expired_orders)
--   views/      (v_public_books, v_staff_orders)
--   triggers/   (ghi core_auditlog)
--   init/02_users_grants.sql (app_customer, app_staff, bookstore_migrate)
--
-- Các bảng Django và thư viện tự tạo khi chạy migrate (KHÔNG viết ở đây):
--   auth_group, auth_permission, auth_group_permissions (vai trò và quyền),
--   accounts_user_groups, accounts_user_user_permissions (bảng nối user với vai trò),
--   django_session, django_admin_log, django_content_type, django_migrations,
--   axes_* (khóa tài khoản), otp_* (2FA).
-- =====================================================================

CREATE DATABASE IF NOT EXISTS bookstore
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE bookstore;

-- CẢNH BÁO: các lệnh DROP dưới đây xóa sạch dữ liệu.
-- Chỉ dùng trên CSDL nháp khi cần chạy lại script từ đầu. Không chạy trên máy demo thật.
SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS core_securityevent;
DROP TABLE IF EXISTS core_auditlog;
DROP TABLE IF EXISTS payments_payment;
DROP TABLE IF EXISTS orders_orderitem;
DROP TABLE IF EXISTS orders_order;
DROP TABLE IF EXISTS orders_cartitem;
DROP TABLE IF EXISTS orders_cart;
DROP TABLE IF EXISTS catalog_review;
DROP TABLE IF EXISTS catalog_book;
DROP TABLE IF EXISTS catalog_category;
DROP TABLE IF EXISTS accounts_user;
SET FOREIGN_KEY_CHECKS = 1;


-- =====================================================================
-- APP accounts
-- =====================================================================

-- Người dùng. Dùng chung cho khách hàng và nhân viên.
-- MySQL không có kế thừa: đây là một bảng bình thường.
-- Các cột từ id đến date_joined khớp với khuôn AbstractUser của Django
-- (phía Python, model User kế thừa AbstractUser); 2 cột cuối là trường nhóm tự thêm.
-- Vai trò gán qua Group của Django (bảng auth_group + accounts_user_groups do Django tạo).
CREATE TABLE accounts_user (
    id                BIGINT       NOT NULL AUTO_INCREMENT,
    password          VARCHAR(128) NOT NULL,                 -- chuỗi băm PBKDF2/Argon2 do Django tạo, không bao giờ là mật khẩu rõ
    last_login        DATETIME(6)  NULL,
    is_superuser      TINYINT(1)   NOT NULL DEFAULT 0,
    username          VARCHAR(150) NOT NULL,
    first_name        VARCHAR(150) NOT NULL DEFAULT '',
    last_name         VARCHAR(150) NOT NULL DEFAULT '',
    email             VARCHAR(254) NOT NULL,
    is_staff          TINYINT(1)   NOT NULL DEFAULT 0,       -- 1 = được vào khu vực nhân viên
    is_active         TINYINT(1)   NOT NULL DEFAULT 1,       -- 0 = chưa xác minh email hoặc bị khóa (xóa mềm)
    date_joined       DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),

    -- Trường bổ sung của nhóm
    phone_encrypted   VARCHAR(512) NULL,                     -- SĐT đã mã hóa AES-GCM
    email_verified    TINYINT(1)   NOT NULL DEFAULT 0,

    PRIMARY KEY (id),
    CONSTRAINT uq_user_username UNIQUE (username),
    CONSTRAINT uq_user_email    UNIQUE (email),
    -- username chỉ gồm chữ, số và . _ - (chặn ký tự lạ ngay từ CSDL)
    CONSTRAINT ck_user_username_format CHECK (username REGEXP '^[A-Za-z0-9._-]{3,150}$'),
    -- superuser bắt buộc phải là staff
    CONSTRAINT ck_user_superuser_is_staff CHECK (is_superuser = 0 OR is_staff = 1)
) ENGINE=InnoDB
  COMMENT='Người dùng hệ thống (khách hàng và nhân viên)';


-- =====================================================================
-- APP catalog
-- =====================================================================

-- Thể loại sách
CREATE TABLE catalog_category (
    id          BIGINT       NOT NULL AUTO_INCREMENT,
    name        VARCHAR(100) NOT NULL,
    slug        VARCHAR(120) NOT NULL,                       -- dùng trên URL, ví dụ: van-hoc
    created_at  DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),

    PRIMARY KEY (id),
    CONSTRAINT uq_category_name UNIQUE (name),
    CONSTRAINT uq_category_slug UNIQUE (slug),
    CONSTRAINT ck_category_slug_format CHECK (slug REGEXP '^[a-z0-9]+(-[a-z0-9]+)*$')
) ENGINE=InnoDB
  COMMENT='Thể loại sách';


-- Sách
CREATE TABLE catalog_book (
    id           BIGINT       NOT NULL AUTO_INCREMENT,
    title        VARCHAR(255) NOT NULL,
    author       VARCHAR(255) NOT NULL,
    isbn         VARCHAR(13)  NOT NULL,                      -- ISBN-10 hoặc ISBN-13, không có dấu gạch
    category_id  BIGINT       NOT NULL,
    description  TEXT         NULL,
    cover_image  VARCHAR(255) NULL,                          -- đường dẫn file trong MEDIA_ROOT, tên file là UUID
    price        INT UNSIGNED NOT NULL,                      -- giá bán (VND)
    cost_price   INT UNSIGNED NOT NULL DEFAULT 0,            -- giá nhập: khách KHÔNG được xem (demo quyền theo cột)
    stock        INT UNSIGNED NOT NULL DEFAULT 0,            -- tồn kho: chỉ thay đổi qua stored procedure hoặc tài khoản nhân viên
    is_active    TINYINT(1)   NOT NULL DEFAULT 1,            -- 0 = ẩn / ngừng bán (xóa mềm)
    created_at   DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at   DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),

    PRIMARY KEY (id),
    CONSTRAINT uq_book_isbn UNIQUE (isbn),
    CONSTRAINT fk_book_category FOREIGN KEY (category_id)
        REFERENCES catalog_category (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,                -- không cho xóa thể loại còn sách
    CONSTRAINT ck_book_price_positive  CHECK (price > 0),
    CONSTRAINT ck_book_stock_non_neg   CHECK (stock >= 0),    -- lớp chặn cuối cho race condition: kho không bao giờ âm
    CONSTRAINT ck_book_isbn_format     CHECK (isbn REGEXP '^([0-9]{9}[0-9X]|[0-9]{13})$'),

    INDEX ix_book_title (title),
    INDEX ix_book_author (author),
    INDEX ix_book_active_category (is_active, category_id)   -- phục vụ trang danh sách sách đang bán theo thể loại
) ENGINE=InnoDB
  COMMENT='Sách';


-- Đánh giá sách
CREATE TABLE catalog_review (
    id          BIGINT            NOT NULL AUTO_INCREMENT,
    user_id     BIGINT            NOT NULL,
    book_id     BIGINT            NOT NULL,
    rating      TINYINT UNSIGNED  NOT NULL,                  -- số sao 1..5
    content     VARCHAR(2000)     NOT NULL,                  -- hiển thị qua auto-escape, không dùng |safe
    is_visible  TINYINT(1)        NOT NULL DEFAULT 1,        -- nhân viên có thể ẩn đánh giá vi phạm
    created_at  DATETIME(6)       NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at  DATETIME(6)       NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),

    PRIMARY KEY (id),
    CONSTRAINT uq_review_user_book UNIQUE (user_id, book_id), -- mỗi người một đánh giá cho mỗi sách
    CONSTRAINT fk_review_user FOREIGN KEY (user_id)
        REFERENCES accounts_user (id) ON DELETE CASCADE,
    CONSTRAINT fk_review_book FOREIGN KEY (book_id)
        REFERENCES catalog_book (id) ON DELETE CASCADE,
    CONSTRAINT ck_review_rating CHECK (rating BETWEEN 1 AND 5),
    CONSTRAINT ck_review_content_not_blank CHECK (CHAR_LENGTH(TRIM(content)) > 0),

    INDEX ix_review_book_visible (book_id, is_visible, created_at)
) ENGINE=InnoDB
  COMMENT='Đánh giá sách của khách đã mua';


-- =====================================================================
-- APP orders
-- =====================================================================

-- Giỏ hàng: mỗi người dùng một giỏ
CREATE TABLE orders_cart (
    id          BIGINT      NOT NULL AUTO_INCREMENT,
    user_id     BIGINT      NOT NULL,
    created_at  DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at  DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),

    PRIMARY KEY (id),
    CONSTRAINT uq_cart_user UNIQUE (user_id),
    CONSTRAINT fk_cart_user FOREIGN KEY (user_id)
        REFERENCES accounts_user (id) ON DELETE CASCADE
) ENGINE=InnoDB
  COMMENT='Giỏ hàng';


-- Dòng trong giỏ hàng.
-- KHÔNG lưu giá: giá luôn lấy từ catalog_book tại thời điểm đặt đơn (chống sửa giá phía client).
CREATE TABLE orders_cartitem (
    id        BIGINT            NOT NULL AUTO_INCREMENT,
    cart_id   BIGINT            NOT NULL,
    book_id   BIGINT            NOT NULL,
    quantity  SMALLINT UNSIGNED NOT NULL DEFAULT 1,
    added_at  DATETIME(6)       NOT NULL DEFAULT CURRENT_TIMESTAMP(6),

    PRIMARY KEY (id),
    CONSTRAINT uq_cartitem_cart_book UNIQUE (cart_id, book_id),
    CONSTRAINT fk_cartitem_cart FOREIGN KEY (cart_id)
        REFERENCES orders_cart (id) ON DELETE CASCADE,
    CONSTRAINT fk_cartitem_book FOREIGN KEY (book_id)
        REFERENCES catalog_book (id) ON DELETE CASCADE,
    CONSTRAINT ck_cartitem_quantity CHECK (quantity BETWEEN 1 AND 10)  -- chặn số âm, 0, số quá lớn
) ENGINE=InnoDB
  COMMENT='Sách trong giỏ hàng';


-- Đơn hàng.
-- Chỉ được TẠO qua sp_place_order và chuyển sang 'paid' qua sp_confirm_payment.
-- Thông tin giao hàng là bản chụp lúc đặt (không có bảng địa chỉ riêng).
CREATE TABLE orders_order (
    id                          BIGINT        NOT NULL AUTO_INCREMENT,
    code                        CHAR(32)      NOT NULL,      -- mã công khai (UUID hex), dùng trên URL thay cho id để khó đoán
    user_id                     BIGINT        NOT NULL,
    status                      VARCHAR(20)   NOT NULL DEFAULT 'pending',
    subtotal                    INT UNSIGNED  NOT NULL,      -- tổng tiền sách, tính ở server
    shipping_fee                INT UNSIGNED  NOT NULL DEFAULT 0,
    total                       INT UNSIGNED  NOT NULL,      -- = subtotal + shipping_fee
    shipping_name               VARCHAR(100)  NOT NULL,
    shipping_phone_encrypted    VARCHAR(512)  NOT NULL,      -- SĐT giao hàng đã mã hóa
    shipping_address_encrypted  VARCHAR(1024) NOT NULL,      -- địa chỉ giao hàng đã mã hóa
    idempotency_key             CHAR(32)      NOT NULL,      -- chống bấm "Đặt hàng" hai lần tạo hai đơn
    created_at                  DATETIME(6)   NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at                  DATETIME(6)   NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    expires_at                  DATETIME(6)   NOT NULL,      -- hạn thanh toán (created_at + 15 phút)
    paid_at                     DATETIME(6)   NULL,
    cancelled_at                DATETIME(6)   NULL,

    PRIMARY KEY (id),
    CONSTRAINT uq_order_code            UNIQUE (code),
    CONSTRAINT uq_order_idempotency_key UNIQUE (idempotency_key),
    CONSTRAINT fk_order_user FOREIGN KEY (user_id)
        REFERENCES accounts_user (id) ON DELETE RESTRICT,     -- không xóa user còn đơn hàng (giữ lịch sử)
    -- Máy trạng thái: chỉ các giá trị hợp lệ
    CONSTRAINT ck_order_status CHECK (status IN ('pending', 'paid', 'shipped', 'delivered', 'cancelled')),
    CONSTRAINT ck_order_total CHECK (total = subtotal + shipping_fee),
    CONSTRAINT ck_order_subtotal_positive CHECK (subtotal > 0),
    -- Đơn đã thanh toán (hoặc đang giao, đã giao) bắt buộc có paid_at
    CONSTRAINT ck_order_paid_has_time CHECK (status NOT IN ('paid', 'shipped', 'delivered') OR paid_at IS NOT NULL),
    -- Đơn đã hủy bắt buộc có cancelled_at
    CONSTRAINT ck_order_cancelled_has_time CHECK (status <> 'cancelled' OR cancelled_at IS NOT NULL),
    CONSTRAINT ck_order_expires_after_created CHECK (expires_at > created_at),

    INDEX ix_order_user_created (user_id, created_at),        -- trang lịch sử đơn của khách
    INDEX ix_order_status_expires (status, expires_at)        -- sp_cancel_expired_orders tìm đơn quá hạn
) ENGINE=InnoDB
  COMMENT='Đơn hàng';


-- Chi tiết đơn hàng: chụp lại tên sách và giá tại thời điểm đặt
CREATE TABLE orders_orderitem (
    id          BIGINT            NOT NULL AUTO_INCREMENT,
    order_id    BIGINT            NOT NULL,
    book_id     BIGINT            NOT NULL,
    book_title  VARCHAR(255)      NOT NULL,                  -- tên sách lúc đặt
    unit_price  INT UNSIGNED      NOT NULL,                  -- giá lúc đặt, lấy từ catalog_book (không lấy từ form)
    quantity    SMALLINT UNSIGNED NOT NULL,

    PRIMARY KEY (id),
    CONSTRAINT uq_orderitem_order_book UNIQUE (order_id, book_id),
    CONSTRAINT fk_orderitem_order FOREIGN KEY (order_id)
        REFERENCES orders_order (id) ON DELETE RESTRICT,
    CONSTRAINT fk_orderitem_book FOREIGN KEY (book_id)
        REFERENCES catalog_book (id) ON DELETE RESTRICT,      -- không xóa sách đã có trong đơn (dùng xóa mềm)
    CONSTRAINT ck_orderitem_unit_price CHECK (unit_price > 0),
    CONSTRAINT ck_orderitem_quantity   CHECK (quantity BETWEEN 1 AND 10)
) ENGINE=InnoDB
  COMMENT='Chi tiết đơn hàng';


-- =====================================================================
-- APP payments
-- =====================================================================

-- Giao dịch thanh toán (cổng giả lập). Lưu cả callback bị từ chối để làm bằng chứng.
CREATE TABLE payments_payment (
    id                BIGINT        NOT NULL AUTO_INCREMENT,
    order_id          BIGINT        NOT NULL,
    provider          VARCHAR(30)   NOT NULL DEFAULT 'mockpay',
    transaction_id    VARCHAR(64)   NULL,                    -- mã giao dịch do cổng gửi về (có thể thiếu nếu callback giả)
    amount            INT UNSIGNED  NOT NULL,                -- số tiền cổng báo về
    status            VARCHAR(20)   NOT NULL,                -- success | failed | rejected
    signature_valid   TINYINT(1)    NOT NULL DEFAULT 0,      -- chữ ký HMAC có hợp lệ không
    failure_reason    VARCHAR(255)  NULL,                    -- lý do từ chối: sai chữ ký, sai số tiền, replay...
    raw_payload       JSON          NULL,                    -- nội dung callback (không chứa secret)
    client_ip         VARCHAR(45)   NULL,                    -- IPv4 hoặc IPv6
    created_at        DATETIME(6)   NOT NULL DEFAULT CURRENT_TIMESTAMP(6),

    -- Cột sinh tự động: chỉ có giá trị khi giao dịch thành công.
    -- Đặt UNIQUE trên cột này để một transaction_id chỉ được ghi nhận thành công MỘT lần (chống replay),
    -- nhưng vẫn lưu được nhiều lần thử bị từ chối dùng lại cùng mã.
    success_transaction_id VARCHAR(64)
        GENERATED ALWAYS AS (IF(status = 'success', transaction_id, NULL)) STORED,

    PRIMARY KEY (id),
    CONSTRAINT uq_payment_success_txn UNIQUE (success_transaction_id),
    CONSTRAINT fk_payment_order FOREIGN KEY (order_id)
        REFERENCES orders_order (id) ON DELETE RESTRICT,
    CONSTRAINT ck_payment_status CHECK (status IN ('success', 'failed', 'rejected')),
    -- Giao dịch thành công bắt buộc có chữ ký hợp lệ và có transaction_id
    CONSTRAINT ck_payment_success_valid CHECK (
        status <> 'success' OR (signature_valid = 1 AND transaction_id IS NOT NULL)
    ),

    INDEX ix_payment_order (order_id, created_at)
) ENGINE=InnoDB
  COMMENT='Giao dịch thanh toán';


-- =====================================================================
-- APP core – nhật ký
-- =====================================================================

-- Nhật ký thay đổi dữ liệu. Do TRIGGER ghi (database/triggers/), ứng dụng không ghi trực tiếp.
-- Không tài khoản ứng dụng nào có quyền UPDATE/DELETE trên bảng này.
-- Không đặt khóa ngoại để log vẫn còn nguyên khi bản ghi gốc bị xóa.
CREATE TABLE core_auditlog (
    id           BIGINT      NOT NULL AUTO_INCREMENT,
    table_name   VARCHAR(64) NOT NULL,                       -- bảng bị thay đổi, ví dụ catalog_book
    record_id    BIGINT      NOT NULL,                       -- id của bản ghi bị thay đổi
    action       VARCHAR(10) NOT NULL,                       -- INSERT | UPDATE | DELETE
    old_value    JSON        NULL,                           -- giá trị trước khi đổi (chỉ các cột quan trọng)
    new_value    JSON        NULL,                           -- giá trị sau khi đổi
    db_user      VARCHAR(100) NOT NULL,                      -- tài khoản MySQL thực hiện (CURRENT_USER())
    app_user_id  BIGINT      NULL,                           -- nhân viên/khách trên web, Django gán qua biến @app_user_id
    created_at   DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),

    PRIMARY KEY (id),
    CONSTRAINT ck_auditlog_action CHECK (action IN ('INSERT', 'UPDATE', 'DELETE')),

    INDEX ix_auditlog_record (table_name, record_id),
    INDEX ix_auditlog_created (created_at)
) ENGINE=InnoDB
  COMMENT='Nhật ký thay đổi dữ liệu (ghi bởi trigger)';


-- Nhật ký sự kiện bảo mật. Django ghi (app core), đồng thời ghi ra file security.log.
-- Tài khoản ứng dụng chỉ có INSERT và SELECT, không có UPDATE/DELETE.
-- Không đặt khóa ngoại tới accounts_user: log phải giữ nguyên kể cả khi user bị xóa,
-- và có thể ghi sự kiện cho username không tồn tại (dò tài khoản).
CREATE TABLE core_securityevent (
    id                  BIGINT       NOT NULL AUTO_INCREMENT,
    event_type          VARCHAR(40)  NOT NULL,
    severity            VARCHAR(10)  NOT NULL DEFAULT 'info',
    user_id             BIGINT       NULL,                   -- người dùng liên quan (nếu đã đăng nhập)
    username_attempted  VARCHAR(150) NULL,                   -- username được nhập khi đăng nhập sai
    ip_address          VARCHAR(45)  NOT NULL,
    user_agent          VARCHAR(255) NULL,
    method              VARCHAR(10)  NULL,                   -- GET, POST...
    path                VARCHAR(255) NULL,                   -- đường dẫn bị truy cập
    detail              JSON         NULL,                   -- thông tin thêm; KHÔNG chứa mật khẩu, token, session ID
    created_at          DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),

    PRIMARY KEY (id),
    CONSTRAINT ck_secevent_type CHECK (event_type IN (
        'login_success',             -- đăng nhập thành công
        'login_failed',              -- đăng nhập sai
        'account_locked',            -- tài khoản bị khóa do sai nhiều lần
        'logout',
        'password_changed',
        'password_reset_requested',
        'otp_failed',                -- nhập sai mã 2FA
        'access_denied',             -- không đủ quyền (403)
        'idor_attempt',              -- truy cập tài nguyên của người khác (trả 404)
        'db_permission_denied',      -- MySQL từ chối câu lệnh (lớp phân quyền thứ 2)
        'payment_signature_invalid', -- callback sai chữ ký
        'payment_replay',            -- callback dùng lại mã giao dịch
        'payment_amount_mismatch',   -- callback sai số tiền
        'upload_rejected',           -- file upload bị từ chối
        'rate_limited',              -- vượt giới hạn tần suất
        'csrf_failed',               -- thiếu hoặc sai CSRF token
        'invalid_input'              -- dữ liệu đầu vào bất thường (giá âm, số lượng âm...)
    )),
    CONSTRAINT ck_secevent_severity CHECK (severity IN ('info', 'warning', 'critical')),

    INDEX ix_secevent_type_created (event_type, created_at),
    INDEX ix_secevent_ip_created (ip_address, created_at),   -- tìm IP đáng ngờ (ví dụ đăng nhập sai nhiều)
    INDEX ix_secevent_user (user_id)
) ENGINE=InnoDB
  COMMENT='Nhật ký sự kiện bảo mật';

-- =====================================================================
-- Hết script lược đồ.
-- =====================================================================
