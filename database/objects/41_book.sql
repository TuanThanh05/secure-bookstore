-- =====================================================================
-- Quản lý sách (catalog_book) – chỉ nhân viên.
--
--   v_staff_books          mọi cột của catalog_book (kể cả giá nhập, tồn kho),
--                          view MỘT bảng nên đọc được khi có role
--   sp_book_create         thêm sách, nhập luôn tồn kho ban đầu
--   sp_book_update         sửa thông tin (không đụng tồn kho, không ẩn/hiện)
--   sp_book_set_active     ẩn hoặc hiện sách
--   sp_book_restock        nhập thêm hàng
--   sp_book_reduce_stock   giảm kho ngoại lệ (hỏng, thất lạc...)
--   sp_book_delete         xóa hẳn sách: phải ẩn trước và chưa từng có trong đơn
--
-- Phân quyền: chỉ r_staff được SELECT view và EXECUTE sáu thủ tục. Không tài
-- khoản ứng dụng nào được INSERT/UPDATE/DELETE thẳng vào catalog_book.
-- Thủ tục tự kiểm tra p_actor_id là nhân viên đang hoạt động (NOT_STAFF).
--
-- Giới hạn nghiệp vụ:
--   tên sách, tác giả   1–255 ký tự (sau khi bỏ khoảng trắng hai đầu)
--   ISBN                ISBN-10 hoặc ISBN-13, không dấu gạch (Django kiểm tra
--                       thêm chữ số kiểm tra)
--   mô tả               NULL hoặc tối đa 5.000 ký tự
--   giá bán             1 – 100.000.000 đ;  giá nhập 0 – 100.000.000 đ
--   tồn kho             0 – 10.000 cuốn cho MỖI đầu sách, mọi lúc
--   ảnh bìa             NULL (Django hiện ảnh mặc định) hoặc covers/<32 hex>.<jpg|png|webp>
--
-- Mỗi thay đổi ghi core_auditlog trong CÙNG giao dịch (old/new JSON, USER(),
-- id nhân viên). Lỗi ở bước nào cũng ROLLBACK.
--
-- Lỗi (SIGNAL SQLSTATE '45000', MESSAGE_TEXT là đúng một mã):
--   INVALID_INPUT       tham số sai
--   NOT_STAFF           p_actor_id không phải nhân viên đang hoạt động
--   ISBN_EXISTS         trùng ISBN (UNIQUE, lỗi 1062)
--   CATEGORY_NOT_FOUND  thể loại không tồn tại
--   BOOK_NOT_FOUND      không có sách với id này
--   INVALID_QUANTITY    số lượng nhập/giảm ngoài 1–10.000
--   STOCK_LIMIT         nhập thêm làm tồn kho vượt 10.000
--   INSUFFICIENT_STOCK  giảm nhiều hơn số đang có
--   BOOK_ACTIVE         sách đang hiện, phải ẩn trước khi xóa
--   BOOK_HAS_ORDERS     sách đã có trong đơn hàng, chỉ được ẩn
--
-- Race condition: mọi thủ tục đổi tồn kho hoặc xóa đều khóa dòng sách
-- (FOR UPDATE), giống sp_place_order, nên nhập kho, giảm kho, xóa và khách
-- đặt hàng cùng lúc phải xếp hàng; không mất số, kho không âm (thêm CHECK
-- ck_book_stock_non_neg). Xóa đúng lúc có đơn mới: khóa ngoại RESTRICT của
-- orders_orderitem chặn (lỗi 1451) → BOOK_HAS_ORDERS.
--
-- Root tạo bằng `python manage.py db_apply`. Chạy lại nhiều lần được.
-- =====================================================================

DROP VIEW IF EXISTS v_staff_books;
DROP PROCEDURE IF EXISTS sp_book_create;
DROP PROCEDURE IF EXISTS sp_book_update;
DROP PROCEDURE IF EXISTS sp_book_set_active;
DROP PROCEDURE IF EXISTS sp_book_restock;
DROP PROCEDURE IF EXISTS sp_book_reduce_stock;
DROP PROCEDURE IF EXISTS sp_book_delete;

-- AI-TRACE#120 | Claude Opus 5.5 | View một bảng cho nhân viên xem mọi cột của sách, kể cả giá nhập và tồn kho | CẤM XÓA CHÚ THÍCH NÀY
CREATE DEFINER = 'bookstore_definer'@'localhost'
SQL SECURITY DEFINER
VIEW v_staff_books AS
SELECT id, title, author, isbn, category_id, description, cover_image,
       price, cost_price, stock, is_active, created_at, updated_at
  FROM catalog_book;

DELIMITER $$

-- AI-TRACE#121 | Claude Opus 5.5 | Thủ tục thêm sách: kiểm tra nhân viên, đầu vào, thể loại, chặn trùng ISBN, ghi nhật ký | CẤM XÓA CHÚ THÍCH NÀY
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

-- AI-TRACE#122 | Claude Opus 5.5 | Thủ tục sửa thông tin sách (không đụng tồn kho và ẩn/hiện), khóa dòng, ghi giá trị cũ/mới | CẤM XÓA CHÚ THÍCH NÀY
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

-- AI-TRACE#123 | Claude Opus 5.5 | Thủ tục ẩn hoặc hiện sách, khóa dòng, ghi nhật ký | CẤM XÓA CHÚ THÍCH NÀY
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

-- AI-TRACE#124 | Claude Opus 5.5 | Thủ tục nhập thêm hàng: khóa dòng sách, chặn vượt 10.000 cuốn, ghi tồn kho trước và sau | CẤM XÓA CHÚ THÍCH NÀY
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

-- AI-TRACE#125 | Claude Opus 5.5 | Thủ tục giảm kho ngoại lệ: khóa dòng sách, không cho âm, ghi tồn kho trước và sau | CẤM XÓA CHÚ THÍCH NÀY
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

-- AI-TRACE#126 | Claude Opus 5.5 | Thủ tục xóa hẳn sách: khóa dòng, chỉ xóa sách đã ẩn và chưa từng có trong đơn, ghi nhật ký | CẤM XÓA CHÚ THÍCH NÀY
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
