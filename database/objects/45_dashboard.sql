-- =====================================================================
-- Trang Tổng quan của admin – báo cáo cơ bản (chốt 2026-11-16):
--   sp_staff_dashboard_orders    đơn cần xử lý theo từng bước, đơn mới/hủy hôm
--                                nay, doanh thu hôm nay / 7 ngày / tháng này
--   sp_staff_dashboard_stock     số sách sắp hết, hết hàng, 5 cuốn còn ít nhất
--   sp_staff_dashboard_security  sự kiện cảnh báo/nghiêm trọng 24 giờ, đăng nhập
--                                sai hôm nay
--
-- Không dùng view: cần COUNT/SUM/WHERE, mà MySQL từ chối view DEFINER có lọc
-- hoặc gộp nhóm khi phiên đang bật role (lỗi 1143/1356). Chỉ r_staff được
-- EXECUTE; mỗi thủ tục tự kiểm tra p_actor_id là nhân viên (NOT_STAFF).
--
-- Mốc thời gian (đầu ngày, đầu tháng theo giờ Việt Nam) do Django tính rồi
-- truyền xuống dạng UTC; ngưỡng "sắp hết" lấy từ LOW_STOCK_THRESHOLD của
-- Django (không ghi cứng hai nơi).
--
-- Doanh thu: tổng `total` của đơn từ "Đã thanh toán" trở đi, tính theo
-- paid_at (đơn đã thanh toán không hủy được nên không bị trừ lại); gồm cả
-- thanh toán mô phỏng.
--
-- Không trả dữ liệu cá nhân nào (chỉ con số, tên sách).
-- Mã lỗi: INVALID_INPUT, NOT_STAFF. Root tạo bằng `python manage.py db_apply`.
-- =====================================================================

DROP PROCEDURE IF EXISTS sp_staff_dashboard_orders;
DROP PROCEDURE IF EXISTS sp_staff_dashboard_stock;
DROP PROCEDURE IF EXISTS sp_staff_dashboard_security;

DELIMITER $$

-- AI-TRACE#392 | Claude Opus 5.5 | Thủ tục tổng quan đơn hàng: số đơn cần xử lý theo từng bước, đơn mới và đơn hủy hôm nay, doanh thu hôm nay/7 ngày/tháng này theo ngày thanh toán | CẤM XÓA CHÚ THÍCH NÀY
CREATE DEFINER = 'bookstore_definer'@'localhost' PROCEDURE sp_staff_dashboard_orders(
    IN p_actor_id     BIGINT,
    IN p_today_start  DATETIME(6),
    IN p_week_start   DATETIME(6),
    IN p_month_start  DATETIME(6)
)
SQL SECURITY DEFINER
READS SQL DATA
BEGIN
    DECLARE v_staff INT DEFAULT 0;

    IF p_actor_id IS NULL OR p_actor_id <= 0
       OR p_today_start IS NULL OR p_week_start IS NULL OR p_month_start IS NULL
       OR p_week_start > p_today_start OR p_month_start > p_today_start
       OR p_today_start > UTC_TIMESTAMP(6) + INTERVAL 1 DAY
       OR p_week_start < p_today_start - INTERVAL 7 DAY
       OR p_month_start < p_today_start - INTERVAL 32 DAY THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'INVALID_INPUT';
    END IF;

    SELECT COUNT(*) INTO v_staff
      FROM accounts_user
     WHERE id = p_actor_id AND is_staff = 1 AND is_active = 1;
    IF v_staff = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'NOT_STAFF';
    END IF;

    SELECT
        COALESCE(SUM(status = 'paid'), 0)                                         AS paid_count,
        COALESCE(SUM(status = 'confirmed'), 0)                                    AS confirmed_count,
        COALESCE(SUM(status = 'packed'), 0)                                       AS packed_count,
        COALESCE(SUM(status = 'shipped'), 0)                                      AS shipped_count,
        COALESCE(SUM(created_at >= p_today_start), 0)                             AS new_today,
        COALESCE(SUM(status = 'cancelled' AND cancelled_at >= p_today_start), 0)  AS cancelled_today,
        COALESCE(SUM(IF(paid_at >= p_today_start, total, 0)), 0)                  AS revenue_today,
        COALESCE(SUM(IF(paid_at >= p_week_start, total, 0)), 0)                   AS revenue_week,
        COALESCE(SUM(IF(paid_at >= p_month_start, total, 0)), 0)                  AS revenue_month
      FROM orders_order
     WHERE status IN ('paid', 'confirmed', 'packed', 'shipped')
        OR created_at >= LEAST(p_today_start, p_week_start, p_month_start)
        OR cancelled_at >= p_today_start
        OR paid_at >= LEAST(p_today_start, p_week_start, p_month_start);
END$$

-- AI-TRACE#393 | Claude Opus 5.5 | Thủ tục tổng quan kho: số sách đang bán sắp hết (1 đến ngưỡng) và hết hàng, 5 cuốn đang bán còn ít nhất | CẤM XÓA CHÚ THÍCH NÀY
CREATE DEFINER = 'bookstore_definer'@'localhost' PROCEDURE sp_staff_dashboard_stock(
    IN p_actor_id        BIGINT,
    IN p_low_threshold   INT
)
SQL SECURITY DEFINER
READS SQL DATA
BEGIN
    DECLARE v_staff INT DEFAULT 0;

    IF p_actor_id IS NULL OR p_actor_id <= 0
       OR p_low_threshold IS NULL OR p_low_threshold < 1 OR p_low_threshold > 1000 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'INVALID_INPUT';
    END IF;

    SELECT COUNT(*) INTO v_staff
      FROM accounts_user
     WHERE id = p_actor_id AND is_staff = 1 AND is_active = 1;
    IF v_staff = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'NOT_STAFF';
    END IF;

    SELECT COALESCE(SUM(stock BETWEEN 1 AND p_low_threshold), 0) AS low_count,
           COALESCE(SUM(stock = 0), 0)                           AS out_count
      FROM catalog_book
     WHERE is_active = 1;

    SELECT id, title, stock
      FROM catalog_book
     WHERE is_active = 1 AND stock <= p_low_threshold
     ORDER BY stock, title, id
     LIMIT 5;
END$$

-- AI-TRACE#394 | Claude Opus 5.5 | Thủ tục tổng quan bảo mật: số sự kiện mức cảnh báo/nghiêm trọng trong 24 giờ và số lần đăng nhập sai từ đầu ngày, chỉ trả con số | CẤM XÓA CHÚ THÍCH NÀY
CREATE DEFINER = 'bookstore_definer'@'localhost' PROCEDURE sp_staff_dashboard_security(
    IN p_actor_id     BIGINT,
    IN p_today_start  DATETIME(6)
)
SQL SECURITY DEFINER
READS SQL DATA
BEGIN
    DECLARE v_staff INT DEFAULT 0;
    DECLARE v_since DATETIME(6) DEFAULT UTC_TIMESTAMP(6) - INTERVAL 24 HOUR;

    IF p_actor_id IS NULL OR p_actor_id <= 0
       OR p_today_start IS NULL
       OR p_today_start > UTC_TIMESTAMP(6) + INTERVAL 1 DAY
       OR p_today_start < UTC_TIMESTAMP(6) - INTERVAL 2 DAY THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'INVALID_INPUT';
    END IF;

    SELECT COUNT(*) INTO v_staff
      FROM accounts_user
     WHERE id = p_actor_id AND is_staff = 1 AND is_active = 1;
    IF v_staff = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'NOT_STAFF';
    END IF;

    SELECT COALESCE(SUM(created_at >= v_since AND severity = 'warning'), 0)        AS warning_24h,
           COALESCE(SUM(created_at >= v_since AND severity = 'critical'), 0)       AS critical_24h,
           COALESCE(SUM(created_at >= p_today_start AND event_type = 'login_failed'), 0) AS login_failed_today
      FROM core_securityevent
     WHERE created_at >= LEAST(v_since, p_today_start);
END$$

DELIMITER ;
