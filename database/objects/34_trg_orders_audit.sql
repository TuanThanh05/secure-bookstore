-- =====================================================================
-- Nhật ký đơn hàng (chốt 2026-11-16): mọi lần tạo đơn và đổi trạng thái đơn
-- đều ghi vào core_auditlog bằng trigger, nên thủ tục nào đổi đơn (đặt hàng,
-- khách hủy, Event tự hủy, thanh toán sau này) cũng có dấu vết, không sót.
--
-- source (ai gây ra thay đổi) suy ra từ USER() – tài khoản MySQL đang chạy câu
-- lệnh (người gọi thủ tục DEFINER, hoặc definer khi Event chạy):
--   app_customer       → customer  (app_user_id = chủ đơn)
--   event_scheduler    → system    (Event hủy đơn quá hạn: trong Event, USER()
--                                   là event_scheduler@localhost – đã thử thật)
--   bookstore_definer  → system
--   app_payment        → payment   (nhánh thanh toán, sau này)
--   app_staff          → staff     (quản lý đơn của admin, sau này)
--   khác (root...)     → other
-- Thủ tục admin đổi trạng thái đơn sau này KHÔNG tự ghi thêm core_auditlog
-- cho việc đổi trạng thái (trigger đã ghi), chỉ ghi phần riêng như lý do.
--
-- Chạy bằng quyền bookstore_definer (đã có INSERT core_auditlog, TRIGGER trên
-- orders_order). Root tạo bằng `python manage.py db_apply`. Chạy lại được.
-- =====================================================================

DROP TRIGGER IF EXISTS trg_order_audit_insert;
DROP TRIGGER IF EXISTS trg_order_audit_update;

DELIMITER $$

-- AI-TRACE#320 | Claude Opus 5.5 | Trigger ghi nhật ký khi tạo đơn: mã đơn, trạng thái, tổng tiền, nguồn gây ra (khách/hệ thống/...) suy từ tài khoản MySQL | CẤM XÓA CHÚ THÍCH NÀY
CREATE DEFINER = 'bookstore_definer'@'localhost'
TRIGGER trg_order_audit_insert
AFTER INSERT ON orders_order
FOR EACH ROW
BEGIN
    DECLARE v_account VARCHAR(100) DEFAULT SUBSTRING_INDEX(USER(), '@', 1);
    DECLARE v_source  VARCHAR(20)  DEFAULT CASE SUBSTRING_INDEX(USER(), '@', 1)
        WHEN 'app_customer' THEN 'customer'
        WHEN 'event_scheduler' THEN 'system'
        WHEN 'bookstore_definer' THEN 'system'
        WHEN 'app_payment' THEN 'payment'
        WHEN 'app_staff' THEN 'staff'
        ELSE 'other' END;

    INSERT INTO core_auditlog (table_name, record_id, action, old_value, new_value, db_user, app_user_id)
    VALUES ('orders_order', NEW.id, 'INSERT', NULL,
            JSON_OBJECT('code', NEW.code, 'status', NEW.status, 'total', NEW.total, 'source', v_source),
            USER(), IF(v_account = 'app_customer', NEW.user_id, NULL));
END$$

-- AI-TRACE#321 | Claude Opus 5.5 | Trigger ghi nhật ký khi đơn đổi trạng thái (chờ → đã thanh toán/đã hủy...), kèm nguồn gây ra; không đổi trạng thái thì không ghi | CẤM XÓA CHÚ THÍCH NÀY
CREATE DEFINER = 'bookstore_definer'@'localhost'
TRIGGER trg_order_audit_update
AFTER UPDATE ON orders_order
FOR EACH ROW
BEGIN
    DECLARE v_account VARCHAR(100) DEFAULT SUBSTRING_INDEX(USER(), '@', 1);
    DECLARE v_source  VARCHAR(20)  DEFAULT CASE SUBSTRING_INDEX(USER(), '@', 1)
        WHEN 'app_customer' THEN 'customer'
        WHEN 'event_scheduler' THEN 'system'
        WHEN 'bookstore_definer' THEN 'system'
        WHEN 'app_payment' THEN 'payment'
        WHEN 'app_staff' THEN 'staff'
        ELSE 'other' END;

    IF NOT (NEW.status <=> OLD.status) THEN
        INSERT INTO core_auditlog (table_name, record_id, action, old_value, new_value, db_user, app_user_id)
        VALUES ('orders_order', NEW.id, 'UPDATE',
                JSON_OBJECT('status', OLD.status),
                JSON_OBJECT('code', NEW.code, 'status', NEW.status, 'source', v_source),
                USER(), IF(v_account = 'app_customer', NEW.user_id, NULL));
    END IF;
END$$

DELIMITER ;
