-- =====================================================================
-- Quản lý thể loại sách (catalog_category) – chỉ nhân viên.
--
--   sp_category_list     danh sách thể loại kèm số sách, cho dashboard đọc
--   sp_category_create   thêm thể loại
--   sp_category_rename   sửa tên (slug đổi theo tên)
--   sp_category_delete   xóa thể loại chưa có sách nào
--
-- Phân quyền (quyền tối thiểu, chương 6.2):
--   - Chỉ r_staff (app_staff) được EXECUTE bốn thủ tục.
--     app_customer không có quyền nào ở đây, gọi là MySQL từ chối.
--   - Không tài khoản ứng dụng nào được INSERT/UPDATE/DELETE thẳng vào
--     catalog_category; mọi thay đổi phải đi qua thủ tục.
--   - Thủ tục tự kiểm tra p_actor_id là nhân viên đang hoạt động (NOT_STAFF),
--     phòng khi kết nối staff bị dùng sai.
--
-- Mỗi thay đổi ghi một dòng core_auditlog trong CÙNG giao dịch: giá trị cũ/mới,
-- tài khoản MySQL gọi thủ tục (USER(), vì CURRENT_USER() trong thủ tục DEFINER
-- luôn là bookstore_definer) và id nhân viên trên web.
--
-- Slug do Django tạo từ tên ("Văn học" → van-hoc); thủ tục chỉ kiểm tra định dạng.
--
-- Lỗi (SIGNAL SQLSTATE '45000', MESSAGE_TEXT là đúng một mã):
--   INVALID_INPUT       tham số sai (tên rỗng/quá 100 ký tự, slug sai định dạng)
--   NOT_STAFF           p_actor_id không phải nhân viên đang hoạt động
--   CATEGORY_EXISTS     trùng tên hoặc slug (ràng buộc UNIQUE, lỗi 1062)
--   CATEGORY_NOT_FOUND  không có thể loại với id này
--   CATEGORY_IN_USE     thể loại còn sách (kể cả sách đang ẩn)
-- Lỗi ở bước nào cũng ROLLBACK: không có thay đổi dở dang, không có log lẻ.
--
-- Race condition:
--   - Hai lần thêm cùng tên: UNIQUE chặn lần sau → CATEGORY_EXISTS.
--   - Xóa đúng lúc có sách được thêm vào thể loại: thủ tục khóa dòng thể loại
--     (FOR UPDATE) nên câu thêm sách phải chờ; nếu vẫn lọt, khóa ngoại
--     ON DELETE RESTRICT chặn (lỗi 1451) → CATEGORY_IN_USE.
--
-- Vì sao danh sách là THỦ TỤC chứ không phải VIEW: trên MySQL 8.0 và 8.4, view
-- SQL SECURITY DEFINER có JOIN/GROUP BY bị từ chối (lỗi 1143/1356) khi phiên
-- người gọi đang bật role (app_staff luôn bật r_staff), dù definer đủ quyền.
-- Đã thử và xác nhận trên cả hai bản (python manage.py db_check_grants).
-- Thủ tục DEFINER không bị lỗi này. Dòng DROP VIEW bên dưới xóa view cũ.
--
-- Root tạo bằng `python manage.py db_apply`. Chạy lại nhiều lần được.
-- =====================================================================

DROP VIEW IF EXISTS v_staff_categories;
DROP PROCEDURE IF EXISTS sp_category_list;
DROP PROCEDURE IF EXISTS sp_category_create;
DROP PROCEDURE IF EXISTS sp_category_rename;
DROP PROCEDURE IF EXISTS sp_category_delete;

DELIMITER $$

-- AI-TRACE#101 | Claude Opus 5.5 | Thủ tục trả danh sách thể loại kèm tổng số sách và số sách đang hiện, chỉ cho nhân viên | CẤM XÓA CHÚ THÍCH NÀY
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

-- AI-TRACE#102 | Claude Opus 5.5 | Thủ tục thêm thể loại: kiểm tra nhân viên và đầu vào, chặn trùng, ghi nhật ký | CẤM XÓA CHÚ THÍCH NÀY
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

-- AI-TRACE#103 | Claude Opus 5.5 | Thủ tục sửa tên thể loại: khóa dòng, đổi tên và slug, chặn trùng, ghi nhật ký | CẤM XÓA CHÚ THÍCH NÀY
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

-- AI-TRACE#104 | Claude Opus 5.5 | Thủ tục xóa thể loại: khóa dòng, từ chối nếu còn sách, ghi nhật ký | CẤM XÓA CHÚ THÍCH NÀY
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
