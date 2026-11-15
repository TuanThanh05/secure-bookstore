-- =====================================================================
-- Đọc danh mục sách cho KHÁCH (mọi người xem, kể cả chưa đăng nhập).
--
--   sp_public_category_list   thể loại để hiện bộ lọc: id, name, slug
--   sp_public_book_list       sách đang bán, lọc theo thể loại và từ khóa
--   sp_public_book_get        một cuốn sách đang bán (trang chi tiết), kèm tên thể loại
--
-- Ban đầu (issue #9) định làm view v_public_books / v_public_categories.
-- Đổi sang THỦ TỤC ĐỌC vì MySQL 8.0/8.4 từ chối view SQL SECURITY DEFINER có
-- WHERE/JOIN/GROUP BY khi phiên người gọi đang bật role (app_customer luôn bật
-- r_customer) – lỗi 1143/1356. Thủ tục DEFINER không bị lỗi này.
--
-- Phân quyền: r_customer chỉ có EXECUTE hai thủ tục, KHÔNG có quyền nào trên
-- catalog_book, catalog_category, catalog_review. Django luôn dùng kết nối
-- app_customer cho trang cửa hàng, nên khách chưa đăng nhập cũng xem được.
--
-- Cột trả về của sp_public_book_list (hợp đồng, khớp issue #9, không thêm bớt):
--   id, title, author, isbn, category_id, description, price, cover_image,
--   created_at, in_stock (0/1 = stock > 0, không lộ số tồn kho),
--   rating (ROUND(AVG, 1) của đánh giá is_visible = 1, NULL khi chưa có),
--   review_count
-- KHÔNG BAO GIỜ trả: cost_price, stock, is_active, updated_at.
-- Chỉ sách is_active = 1. Sách ẩn không lộ qua bất kỳ tham số nào.
--
-- Tìm kiếm: từ khóa tối đa 100 ký tự, tìm trong tên sách hoặc tác giả bằng
-- LIKE với tham số (không có SQL động). Ký tự đại diện % và _ trong từ khóa
-- được thoát, nên chỉ tìm đúng chữ người dùng gõ. Kết quả tối đa 200 cuốn,
-- mới nhất trước (chưa có phân trang).
--
-- Lỗi: SIGNAL SQLSTATE '45000' 'INVALID_INPUT' khi tham số sai.
-- Root tạo bằng `python manage.py db_apply`. Chạy lại nhiều lần được.
-- =====================================================================

DROP VIEW IF EXISTS v_public_books;
DROP VIEW IF EXISTS v_public_categories;
DROP PROCEDURE IF EXISTS sp_public_category_list;
DROP PROCEDURE IF EXISTS sp_public_book_list;
DROP PROCEDURE IF EXISTS sp_public_book_get;

DELIMITER $$

-- AI-TRACE#189 | Claude Opus 5.5 | Thủ tục trả thể loại cho bộ lọc của cửa hàng, chỉ id, tên, slug | CẤM XÓA CHÚ THÍCH NÀY
CREATE DEFINER = 'bookstore_definer'@'localhost' PROCEDURE sp_public_category_list()
SQL SECURITY DEFINER
READS SQL DATA
BEGIN
    SELECT id, name, slug
      FROM catalog_category
     ORDER BY name;
END$$

-- AI-TRACE#190 | Claude Opus 5.5 | Thủ tục trả sách đang bán cho khách: lọc thể loại, tìm tên/tác giả, điểm đánh giá, không lộ giá nhập và tồn kho | CẤM XÓA CHÚ THÍCH NÀY
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

-- AI-TRACE#211 | Claude Opus 5.5 | Thủ tục trả một sách đang bán cho trang chi tiết, kèm tên thể loại và điểm đánh giá; sách ẩn trả rỗng | CẤM XÓA CHÚ THÍCH NÀY
CREATE DEFINER = 'bookstore_definer'@'localhost' PROCEDURE sp_public_book_get(
    IN p_book_id  BIGINT
)
SQL SECURITY DEFINER
READS SQL DATA
BEGIN
    IF p_book_id IS NULL OR p_book_id <= 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'INVALID_INPUT';
    END IF;

    -- Cùng bộ cột với sp_public_book_list, thêm category_name ở cuối.
    -- Sách ẩn hoặc không tồn tại: 0 dòng như nhau, không phân biệt được.
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
