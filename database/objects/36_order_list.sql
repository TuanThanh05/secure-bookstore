-- =====================================================================
-- Trang "Đơn hàng của tôi" của khách (chốt 2026-11-16):
--   sp_order_list_mine   danh sách đơn của CHÍNH khách đang đăng nhập, theo nhóm
--
-- Không dùng view: mọi khách vào CSDL bằng cùng một tài khoản app_customer,
-- MySQL không biết người đang xem là khách nào, nên một view "đơn của khách"
-- sẽ trả đơn của tất cả mọi người. Thủ tục nhận user_id do Django lấy từ phiên
-- đăng nhập và lọc WHERE user_id ngay trong CSDL.
--
-- Nhóm:
--   'active'   Đang xử lý: pending, paid, confirmed, packed, shipped
--   'history'  Lịch sử (trạng thái cuối): delivered, cancelled
--
-- Trả 2 bộ kết quả (mẫu như trang nhật ký):
--   1. tổng số đơn của nhóm
--   2. một trang: code, status, total, created_at, expires_at, paid_at,
--      cancelled_at, số cuốn, số đầu sách, tên cuốn đầu tiên
-- Không trả SĐT/địa chỉ (đã mã hóa) – xem ở trang chi tiết đơn (sp_order_get).
--
-- Mã lỗi: INVALID_INPUT, NOT_CUSTOMER.
-- Root tạo bằng `python manage.py db_apply`. Chạy lại nhiều lần được.
-- =====================================================================

DROP PROCEDURE IF EXISTS sp_order_list_mine;

DELIMITER $$

-- AI-TRACE#364 | Claude Opus 5.5 | Thủ tục đọc danh sách đơn của chính khách theo nhóm Đang xử lý / Lịch sử, trả tổng số và một trang (mới nhất trước), không trả thông tin giao hàng | CẤM XÓA CHÚ THÍCH NÀY
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
