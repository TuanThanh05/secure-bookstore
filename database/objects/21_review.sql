-- =====================================================================
-- Đánh giá sách của khách (catalog_review).
--
--   sp_review_save      gửi đánh giá; nếu đã có thì SỬA đánh giá cũ
--   sp_review_get_mine  đánh giá của chính mình cho một sách (điền sẵn form sửa)
--
-- Ai được đánh giá (chốt 2026-11-15, cách b): khách đang hoạt động, đã xác
-- nhận email, KHÔNG phải nhân viên. Sau này khi có đơn hàng sẽ siết lại thành
-- "chỉ khách đã mua sách đó" (cách a).
--
-- Bảo mật:
--   - p_user_id do Django lấy từ phiên đăng nhập (request.user.pk), không bao
--     giờ lấy từ form; thủ tục vẫn tự kiểm tra lại người đó là khách hợp lệ.
--   - Chỉ sách đang hiện (is_active = 1); sách ẩn hay không tồn tại đều báo
--     BOOK_NOT_FOUND như nhau.
--   - Điểm 1–5; nội dung 1–2000 ký tự sau khi bỏ khoảng trắng hai đầu (bảng
--     còn có CHECK ck_review_rating, ck_review_content_not_blank).
--   - Mỗi khách một đánh giá cho mỗi sách (UNIQUE uq_review_user_book). Gửi lại
--     là sửa; dùng INSERT ... ON DUPLICATE KEY UPDATE nên hai lần bấm cùng lúc
--     không tạo hai dòng, không lỗi.
--   - Sửa không đổi is_visible: đánh giá admin đã ẩn thì vẫn ẩn.
--   - r_customer chỉ có EXECUTE; không có INSERT/UPDATE/DELETE trên bảng.
--   - Nội dung hiển thị luôn qua auto-escape của Django, không dùng |safe.
--
-- Lỗi (SIGNAL SQLSTATE '45000', MESSAGE_TEXT là đúng một mã):
--   INVALID_INPUT   tham số sai
--   NOT_CUSTOMER    tài khoản không phải khách hợp lệ (nhân viên, bị khóa,
--                   chưa xác nhận email, không tồn tại)
--   BOOK_NOT_FOUND  sách không tồn tại hoặc đang ẩn
--
-- Root tạo bằng `python manage.py db_apply`. Chạy lại nhiều lần được.
-- =====================================================================

DROP PROCEDURE IF EXISTS sp_review_save;
DROP PROCEDURE IF EXISTS sp_review_get_mine;

DELIMITER $$

-- AI-TRACE#198 | Claude Opus 5.5 | Thủ tục gửi hoặc sửa đánh giá: kiểm tra khách hợp lệ, sách đang hiện, điểm và nội dung, không tạo trùng | CẤM XÓA CHÚ THÍCH NÀY
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

    SELECT COUNT(*) INTO v_existed
      FROM catalog_review
     WHERE user_id = p_user_id AND book_id = p_book_id;

    INSERT INTO catalog_review (user_id, book_id, rating, content)
    VALUES (p_user_id, p_book_id, p_rating, v_content) AS new_review
    ON DUPLICATE KEY UPDATE rating = new_review.rating, content = new_review.content;

    SET p_created = IF(v_existed = 0, 1, 0);

    COMMIT;
END$$

-- AI-TRACE#199 | Claude Opus 5.5 | Thủ tục trả đánh giá của chính khách cho một sách để điền sẵn form sửa | CẤM XÓA CHÚ THÍCH NÀY
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

DELIMITER ;
