-- Phần 10: Trigger bảo vệ bảng tài khoản (chặn leo thang đặc quyền)
-- =====================================================================
-- Chặn leo thang đặc quyền ngay trong CSDL (lớp phòng thủ thứ 2).
--
-- Vấn đề: Django đăng nhập, đăng ký, đổi mật khẩu đều chạy bằng kết nối
-- `default` (tài khoản app_customer) và lệnh user.save() của Django luôn
-- ghi lại MỌI cột, kể cả is_staff, is_superuser. Vì vậy không thể chỉ cấp
-- quyền UPDATE theo cột như kế hoạch ban đầu (save() sẽ bị MySQL từ chối).
--
-- Cách làm (cập nhật 2026-11-19): app_customer chỉ còn SELECT trên accounts_user.
-- Mọi lệnh GHI của Django (đăng ký, last_login, hồ sơ, đổi/đặt lại mật khẩu) đi
-- qua tài khoản riêng app_auth (core.db_routers.AccountWriteRouter). 2 trigger dưới
-- đây từ chối mọi câu lệnh của app_auth (và app_customer, phòng khi cấp nhầm quyền)
-- có ý định:
--   - tạo user với is_staff = 1 hoặc is_superuser = 1;
--   - đổi giá trị is_staff, is_superuser của user đã có;
--   - sửa dòng của nhân viên/quản trị, trừ cột last_login (để nhân viên vẫn
--     đăng nhập được qua trang đăng nhập chung). Chặn kiểu tấn công ghi đè
--     mật khẩu/email của admin rồi chiếm tài khoản;
--   - sửa dòng của khách ở các cột web không bao giờ đổi: is_active (tự mở khóa),
--     email, username (đổi email rồi "quên mật khẩu" để chiếm tài khoản),
--     email_verified, date_joined. Khóa/mở khóa chỉ qua thủ tục của admin.
--     Chỉ còn đổi được password, last_login, first_name, last_name, phone_encrypted.
-- Ghi lại đúng giá trị cũ (như user.save() bình thường) vẫn được phép.
--
-- Với app_staff (kết nối "staff" của dashboard): quyền theo cột chỉ cho sửa
-- first_name, last_name, phone_encrypted; trigger chặn thêm việc sửa dòng
-- của KHÁCH (is_staff = 0). Kết nối staff bị lạm dụng cũng không sửa được
-- tên/SĐT của khách hàng. Ngoại lệ duy nhất (2026-11-16): cột is_active của
-- khách, chỉ đổi được qua thủ tục khóa/mở khóa tài khoản.
--
-- Hệ quả cho code:
--   - Tạo tài khoản admin: chạy createsuperuser bằng settings.migrate.
--   - Đổi mật khẩu nhân viên: chỉ bằng lệnh trên máy chủ
--     `python manage.py doi_mat_khau_admin <tên> --settings=bookstore.settings.migrate`.
--     Trên web không có đường nào đổi được mật khẩu nhân viên.
-- Kể cả khi có lỗi SQL injection trên web, kẻ tấn công cũng không tự
-- nâng mình lên nhân viên/quản trị được.
--
-- USER() trả về tài khoản MySQL đang kết nối (người gọi), không phải
-- người tạo trigger, nên kiểm tra được ai đang chạy câu lệnh.
--
-- Root tạo trigger này bằng `python manage.py db_apply` (sau migrate).
-- DEFINER là bookstore_definer (khóa đăng nhập), không phải root.
-- Chạy lại nhiều lần được (DROP ... IF EXISTS rồi tạo lại).
-- =====================================================================

DROP TRIGGER IF EXISTS trg_user_guard_insert;
DROP TRIGGER IF EXISTS trg_user_guard_update;

DELIMITER $$

CREATE DEFINER = 'bookstore_definer'@'localhost'
TRIGGER trg_user_guard_insert
BEFORE INSERT ON accounts_user
FOR EACH ROW
BEGIN
    IF SUBSTRING_INDEX(USER(), '@', 1) IN ('app_customer', 'app_auth')
       AND (NEW.is_staff <> 0 OR NEW.is_superuser <> 0) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'tai khoan ung dung khong duoc tao tai khoan nhan vien/quan tri';
    END IF;
END$$

CREATE DEFINER = 'bookstore_definer'@'localhost'
TRIGGER trg_user_guard_update
BEFORE UPDATE ON accounts_user
FOR EACH ROW
BEGIN
    IF SUBSTRING_INDEX(USER(), '@', 1) IN ('app_customer', 'app_auth') THEN
        IF NEW.is_staff <> OLD.is_staff OR NEW.is_superuser <> OLD.is_superuser THEN
            SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'tai khoan ung dung khong duoc thay doi is_staff/is_superuser';
        END IF;
        -- Dòng của nhân viên: chỉ được đổi last_login.
        -- <=> là so sánh an toàn với NULL (NULL <=> NULL là đúng).
        IF OLD.is_staff = 1 AND NOT (
               NEW.id <=> OLD.id AND NEW.password <=> OLD.password
           AND NEW.username <=> OLD.username AND NEW.email <=> OLD.email
           AND NEW.first_name <=> OLD.first_name AND NEW.last_name <=> OLD.last_name
           AND NEW.is_active <=> OLD.is_active AND NEW.date_joined <=> OLD.date_joined
           AND NEW.phone_encrypted <=> OLD.phone_encrypted
           AND NEW.email_verified <=> OLD.email_verified) THEN
            SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'tai khoan ung dung chi duoc cap nhat last_login cua nhan vien';
        END IF;
        -- AI-TRACE#459 | Claude Opus 5.5 | Dòng của khách: cấm đổi is_active, email, username, email_verified, date_joined (chặn tự mở khóa và đổi email để chiếm tài khoản) | CẤM XÓA CHÚ THÍCH NÀY
        IF OLD.is_staff = 0 AND NOT (
               NEW.id <=> OLD.id AND NEW.username <=> OLD.username
           AND NEW.email <=> OLD.email AND NEW.is_active <=> OLD.is_active
           AND NEW.email_verified <=> OLD.email_verified
           AND NEW.date_joined <=> OLD.date_joined) THEN
            SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'tai khoan ung dung khong duoc doi trang thai, email, ten dang nhap cua khach';
        END IF;
    END IF;
    -- AI-TRACE#534 | Claude Opus 5.5 | app_auth không được đổi auto_locked_until (khóa tự động vì giữ kho): chỉ thủ tục DEFINER đặt/gỡ cột này | CẤM XÓA CHÚ THÍCH NÀY
    -- app_customer không có quyền UPDATE trên bảng này (chỉ SELECT), nên lệnh đổi cột
    -- này với USER() = app_customer chỉ có thể đến từ thủ tục DEFINER (33_order_cancel.sql).
    IF SUBSTRING_INDEX(USER(), '@', 1) = 'app_auth'
       AND NOT (NEW.auto_locked_until <=> OLD.auto_locked_until) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'app_auth khong duoc doi khoa tu dong (auto_locked_until)';
    END IF;
    -- app_staff: chỉ được sửa dòng của nhân viên (cột nào thì quyền theo cột đã giới hạn).
    -- Riêng dòng của khách: chỉ được đổi đúng cột is_active (khóa/mở khóa). app_staff
    -- không có quyền UPDATE(is_active) trực tiếp, nên thay đổi này chỉ có thể đến từ
    -- sp_staff_account_lock/unlock (42_account.sql, chạy bằng quyền definer, ghi nhật ký).
    -- AI-TRACE#099 | Claude Opus 5.5 | Chặn app_staff sửa dòng của khách hàng, trừ cột is_active do thủ tục khóa/mở khóa đổi | CẤM XÓA CHÚ THÍCH NÀY
    IF SUBSTRING_INDEX(USER(), '@', 1) = 'app_staff' AND OLD.is_staff <> 1 AND NOT (
           NEW.id <=> OLD.id AND NEW.password <=> OLD.password
       AND NEW.username <=> OLD.username AND NEW.email <=> OLD.email
       AND NEW.first_name <=> OLD.first_name AND NEW.last_name <=> OLD.last_name
       AND NEW.is_staff <=> OLD.is_staff AND NEW.is_superuser <=> OLD.is_superuser
       AND NEW.date_joined <=> OLD.date_joined AND NEW.last_login <=> OLD.last_login
       AND NEW.phone_encrypted <=> OLD.phone_encrypted
       AND NEW.email_verified <=> OLD.email_verified) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'app_staff khong duoc sua thong tin cua khach hang';
    END IF;
END$$

DELIMITER ;


-- Phần 11: Trigger ghi lịch sử mật khẩu
-- =====================================================================
-- Ghi lịch sử mật khẩu (bảng accounts_passwordhistory, `database/01_bang.sql`).
--
-- Mỗi khi cột accounts_user.password có giá trị mới (tạo tài khoản, đổi
-- mật khẩu, đặt lại mật khẩu, lệnh changepassword, kể cả ai đó sửa thẳng
-- bằng SQL), trigger thêm mã băm mới vào lịch sử rồi xóa bớt, chỉ giữ
-- 5 dòng mới nhất của tài khoản đó. Dòng mới nhất là mật khẩu đang dùng.
--
-- Vì sao dùng trigger cho phần GHI:
--   - không sót đường nào: mọi câu INSERT/UPDATE vào accounts_user đều đi qua;
--   - trigger chạy bằng quyền bookstore_definer, nên app_customer không cần
--     quyền INSERT/DELETE trên bảng lịch sử (chỉ có SELECT để Django so sánh).
-- Phần SO SÁNH nằm ở Django (accounts/validators.py) vì mã băm có muối
-- ngẫu nhiên: chỉ check_password() với mật khẩu gốc mới biết có trùng không.
--
-- Bỏ qua mật khẩu "không dùng được" của Django (bắt đầu bằng '!').
-- Số 5 phải khớp OPTIONS history_count của PasswordHistoryValidator trong
-- bookstore/settings/base.py.
--
-- Root tạo bằng `python manage.py db_apply`. Chạy lại nhiều lần được.
-- =====================================================================

DROP TRIGGER IF EXISTS trg_pwhist_after_insert;
DROP TRIGGER IF EXISTS trg_pwhist_after_update;

DELIMITER $$

-- AI-TRACE#086 | Claude Opus 5.5 | Trigger lưu mật khẩu đầu tiên của tài khoản mới vào lịch sử | CẤM XÓA CHÚ THÍCH NÀY
CREATE DEFINER = 'bookstore_definer'@'localhost'
TRIGGER trg_pwhist_after_insert
AFTER INSERT ON accounts_user
FOR EACH ROW
BEGIN
    IF NEW.password IS NOT NULL AND NEW.password <> '' AND LEFT(NEW.password, 1) <> '!' THEN
        INSERT INTO accounts_passwordhistory (user_id, password_hash)
        VALUES (NEW.id, NEW.password);
    END IF;
END$$

-- AI-TRACE#087 | Claude Opus 5.5 | Trigger lưu mật khẩu mới vào lịch sử khi đổi và chỉ giữ 5 dòng mới nhất | CẤM XÓA CHÚ THÍCH NÀY
CREATE DEFINER = 'bookstore_definer'@'localhost'
TRIGGER trg_pwhist_after_update
AFTER UPDATE ON accounts_user
FOR EACH ROW
BEGIN
    DECLARE v_cut_id BIGINT DEFAULT NULL;

    IF NOT (NEW.password <=> OLD.password)
       AND NEW.password IS NOT NULL AND NEW.password <> '' AND LEFT(NEW.password, 1) <> '!' THEN

        INSERT INTO accounts_passwordhistory (user_id, password_hash)
        VALUES (NEW.id, NEW.password);

        -- id của dòng mới thứ 5; mọi dòng cũ hơn dòng đó bị xóa.
        -- Chưa đủ 5 dòng thì SELECT không có kết quả, v_cut_id giữ NULL.
        SELECT id INTO v_cut_id
          FROM accounts_passwordhistory
         WHERE user_id = NEW.id
         ORDER BY id DESC
         LIMIT 1 OFFSET 4;

        IF v_cut_id IS NOT NULL THEN
            DELETE FROM accounts_passwordhistory
             WHERE user_id = NEW.id AND id < v_cut_id;
        END IF;
    END IF;
END$$

DELIMITER ;


-- Phần 12: Trigger bảo vệ xác thực 2 bước của nhân viên
-- =====================================================================
-- Bảo vệ xác thực 2 bước của nhân viên (bảng ở `database/01_bang.sql`).
--
-- Chỉ app_auth có quyền trên accounts_totpdevice và accounts_recoverycode
-- (khách bật/tắt 2 bước, ghi bước thời gian khi đăng nhập). Trigger dưới đây
-- chặn app_auth (và app_customer, phòng khi cấp nhầm quyền) đụng vào 2 bước
-- của NHÂN VIÊN:
--   - không tạo, không xóa thiết bị TOTP của nhân viên: admin chỉ cài/cài lại
--     bằng lệnh trên máy chủ (tao_admin, dat_lai_2fa_admin, tài khoản migrate);
--   - với thiết bị của nhân viên chỉ được tăng last_used_step (lúc admin đăng
--     nhập), không đổi chuỗi bí mật, không đổi chủ, không lùi bước thời gian;
--   - không tạo/sửa/xóa mã dự phòng của nhân viên (admin không có mã dự phòng).
-- Nhờ vậy SQL injection ở trang tài khoản (kết nối app_auth) cũng không thay
-- được Google Authenticator của admin bằng điện thoại của kẻ tấn công.
-- Với khách: last_used_step cũng không được lùi (chống dùng lại mã cũ).
-- =====================================================================

DROP TRIGGER IF EXISTS trg_totp_guard_insert;
DROP TRIGGER IF EXISTS trg_totp_guard_update;
DROP TRIGGER IF EXISTS trg_totp_guard_delete;
DROP TRIGGER IF EXISTS trg_recovery_guard_insert;
DROP TRIGGER IF EXISTS trg_recovery_guard_update;
DROP TRIGGER IF EXISTS trg_recovery_guard_delete;

DELIMITER $$

-- AI-TRACE#472 | Claude Opus 5.5 | Tài khoản ứng dụng không được tạo thiết bị TOTP cho nhân viên | CẤM XÓA CHÚ THÍCH NÀY
CREATE DEFINER = 'bookstore_definer'@'localhost'
TRIGGER trg_totp_guard_insert BEFORE INSERT ON accounts_totpdevice
FOR EACH ROW
BEGIN
    IF SUBSTRING_INDEX(USER(), '@', 1) IN ('app_customer', 'app_auth')
       AND EXISTS (SELECT 1 FROM accounts_user WHERE id = NEW.user_id AND (is_staff <> 0 OR is_superuser <> 0)) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'tai khoan ung dung khong duoc cai 2 buoc cho nhan vien';
    END IF;
END$$

-- AI-TRACE#473 | Claude Opus 5.5 | Thiết bị của nhân viên chỉ được tăng bước thời gian; mọi thiết bị không được lùi bước | CẤM XÓA CHÚ THÍCH NÀY
CREATE DEFINER = 'bookstore_definer'@'localhost'
TRIGGER trg_totp_guard_update BEFORE UPDATE ON accounts_totpdevice
FOR EACH ROW
BEGIN
    IF SUBSTRING_INDEX(USER(), '@', 1) IN ('app_customer', 'app_auth') THEN
        IF OLD.last_used_step IS NOT NULL
           AND (NEW.last_used_step IS NULL OR NEW.last_used_step < OLD.last_used_step) THEN
            SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'khong duoc lui buoc thoi gian cua ma 2 buoc';
        END IF;
        IF EXISTS (SELECT 1 FROM accounts_user WHERE id = OLD.user_id AND (is_staff <> 0 OR is_superuser <> 0))
           AND NOT (NEW.id <=> OLD.id AND NEW.user_id <=> OLD.user_id
                AND NEW.secret_encrypted <=> OLD.secret_encrypted
                AND NEW.confirmed_at <=> OLD.confirmed_at
                AND NEW.created_at <=> OLD.created_at) THEN
            SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'tai khoan ung dung chi duoc ghi buoc thoi gian cho 2 buoc cua nhan vien';
        END IF;
    END IF;
END$$

-- AI-TRACE#474 | Claude Opus 5.5 | Tài khoản ứng dụng không được xóa thiết bị TOTP của nhân viên | CẤM XÓA CHÚ THÍCH NÀY
CREATE DEFINER = 'bookstore_definer'@'localhost'
TRIGGER trg_totp_guard_delete BEFORE DELETE ON accounts_totpdevice
FOR EACH ROW
BEGIN
    IF SUBSTRING_INDEX(USER(), '@', 1) IN ('app_customer', 'app_auth')
       AND EXISTS (SELECT 1 FROM accounts_user WHERE id = OLD.user_id AND (is_staff <> 0 OR is_superuser <> 0)) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'tai khoan ung dung khong duoc go 2 buoc cua nhan vien';
    END IF;
END$$

-- AI-TRACE#475 | Claude Opus 5.5 | Tài khoản ứng dụng không được tạo/sửa/xóa mã dự phòng của nhân viên | CẤM XÓA CHÚ THÍCH NÀY
CREATE DEFINER = 'bookstore_definer'@'localhost'
TRIGGER trg_recovery_guard_insert BEFORE INSERT ON accounts_recoverycode
FOR EACH ROW
BEGIN
    IF SUBSTRING_INDEX(USER(), '@', 1) IN ('app_customer', 'app_auth')
       AND EXISTS (SELECT 1 FROM accounts_user WHERE id = NEW.user_id AND (is_staff <> 0 OR is_superuser <> 0)) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'nhan vien khong co ma du phong';
    END IF;
END$$

CREATE DEFINER = 'bookstore_definer'@'localhost'
TRIGGER trg_recovery_guard_update BEFORE UPDATE ON accounts_recoverycode
FOR EACH ROW
BEGIN
    IF SUBSTRING_INDEX(USER(), '@', 1) IN ('app_customer', 'app_auth') THEN
        IF EXISTS (SELECT 1 FROM accounts_user WHERE id = OLD.user_id AND (is_staff <> 0 OR is_superuser <> 0)) THEN
            SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'nhan vien khong co ma du phong';
        END IF;
        -- Mã dự phòng chỉ đi một chiều: chưa dùng -> đã dùng; không đổi mã, không "hồi sinh" mã đã dùng
        IF NOT (NEW.id <=> OLD.id AND NEW.user_id <=> OLD.user_id AND NEW.code_hash <=> OLD.code_hash
                AND NEW.created_at <=> OLD.created_at)
           OR (OLD.used_at IS NOT NULL AND NOT (NEW.used_at <=> OLD.used_at)) THEN
            SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'ma du phong chi duoc danh dau da dung mot lan';
        END IF;
    END IF;
END$$

CREATE DEFINER = 'bookstore_definer'@'localhost'
TRIGGER trg_recovery_guard_delete BEFORE DELETE ON accounts_recoverycode
FOR EACH ROW
BEGIN
    IF SUBSTRING_INDEX(USER(), '@', 1) IN ('app_customer', 'app_auth')
       AND EXISTS (SELECT 1 FROM accounts_user WHERE id = OLD.user_id AND (is_staff <> 0 OR is_superuser <> 0)) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'nhan vien khong co ma du phong';
    END IF;
END$$

DELIMITER ;


-- Phần 20: Thủ tục đọc danh mục sách cho khách
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


-- Phần 21: Thủ tục đánh giá sách
-- =====================================================================
-- Đánh giá sách của khách (catalog_review).
--
--   sp_review_save       gửi đánh giá; nếu đã có thì SỬA đánh giá cũ
--   sp_review_get_mine   đánh giá của chính mình cho một sách (điền sẵn form sửa)
--   sp_review_can_write  khách này đã được đánh giá sách này chưa (để hiện form)
--   sp_review_list       đánh giá đang hiện của một sách, tên người viết đã che
--
-- Ai được đánh giá (siết lại 2026-11-20, cách a): khách đang hoạt động, đã xác
-- nhận email, KHÔNG phải nhân viên, VÀ có ít nhất một đơn ở trạng thái
-- 'delivered' (admin bấm "Đã giao") chứa đúng cuốn sách đó. Đơn chờ thanh toán,
-- đã thanh toán, đang giao, đã hủy đều không tính. Trạng thái đơn chỉ đi tới
-- (trigger 32), nên đã nhận sách thì luôn sửa được đánh giá của mình.
-- Đánh giá cũ của khách chưa nhận sách đã bị xóa (trước khi gom SQL).
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
--   NOT_PURCHASED   khách chưa có đơn "Đã giao" chứa cuốn sách này
--
-- Root tạo bằng `python manage.py db_apply`. Chạy lại nhiều lần được.
-- =====================================================================

DROP PROCEDURE IF EXISTS sp_review_save;
DROP PROCEDURE IF EXISTS sp_review_get_mine;
DROP PROCEDURE IF EXISTS sp_review_can_write;
DROP PROCEDURE IF EXISTS sp_review_list;

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

    -- AI-TRACE#513 | Claude Opus 5.5 | Chỉ khách có đơn "Đã giao" chứa đúng cuốn sách mới được gửi/sửa đánh giá | CẤM XÓA CHÚ THÍCH NÀY
    IF NOT EXISTS (
        SELECT 1
          FROM orders_orderitem i
          JOIN orders_order o ON o.id = i.order_id
         WHERE i.book_id = p_book_id AND o.user_id = p_user_id AND o.status = 'delivered'
    ) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'NOT_PURCHASED';
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

-- AI-TRACE#514 | Claude Opus 5.5 | Thủ tục đọc: khách có được đánh giá sách này không (khách hợp lệ, sách đang hiện, đã nhận sách); trả đúng một dòng 0/1 | CẤM XÓA CHÚ THÍCH NÀY
CREATE DEFINER = 'bookstore_definer'@'localhost' PROCEDURE sp_review_can_write(
    IN p_user_id  BIGINT,
    IN p_book_id  BIGINT
)
SQL SECURITY DEFINER
READS SQL DATA
BEGIN
    IF p_user_id IS NULL OR p_user_id <= 0 OR p_book_id IS NULL OR p_book_id <= 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'INVALID_INPUT';
    END IF;

    SELECT EXISTS (
               SELECT 1
                 FROM accounts_user u
                 JOIN orders_order o ON o.user_id = u.id
                 JOIN orders_orderitem i ON i.order_id = o.id
                 JOIN catalog_book b ON b.id = i.book_id
                WHERE u.id = p_user_id AND u.is_active = 1 AND u.is_staff = 0 AND u.email_verified = 1
                  AND i.book_id = p_book_id AND b.is_active = 1 AND o.status = 'delivered'
           ) AS can_write;
END$$

-- AI-TRACE#212 | Claude Opus 5.5 | Thủ tục trả đánh giá đang hiện của một sách đang bán, che username ngay trong CSDL, mới nhất trước | CẤM XÓA CHÚ THÍCH NÀY
CREATE DEFINER = 'bookstore_definer'@'localhost' PROCEDURE sp_review_list(
    IN p_book_id  BIGINT
)
SQL SECURITY DEFINER
READS SQL DATA
BEGIN
    IF p_book_id IS NULL OR p_book_id <= 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'INVALID_INPUT';
    END IF;

    -- Username được che tại đây (ký tự đầu + dấu sao + ký tự cuối, chốt
    -- 2026-11-15), nên tên thật không rời khỏi CSDL. Không trả user_id, email.
    -- Chỉ đánh giá is_visible = 1 của sách đang hiện; tối đa 50 dòng.
    SELECT CASE
               WHEN CHAR_LENGTH(u.username) <= 1 THEN '*'
               WHEN CHAR_LENGTH(u.username) = 2 THEN CONCAT(LEFT(u.username, 1), '*')
               ELSE CONCAT(LEFT(u.username, 1),
                           REPEAT('*', CHAR_LENGTH(u.username) - 2),
                           RIGHT(u.username, 1))
           END              AS display_name,
           r.rating,
           r.content,
           r.created_at,
           r.updated_at
      FROM catalog_review r
      JOIN catalog_book b  ON b.id = r.book_id AND b.is_active = 1
      JOIN accounts_user u ON u.id = r.user_id
     WHERE r.book_id = p_book_id AND r.is_visible = 1
     ORDER BY r.created_at DESC, r.id DESC
     LIMIT 50;
END$$

DELIMITER ;


-- Phần 30: Thủ tục đặt hàng sp_place_order
-- =====================================================================
-- sp_place_order: biến giỏ hàng của một người dùng thành đơn hàng.
--
-- Đây là NƠI DUY NHẤT được tạo đơn và trừ kho. app_customer chỉ có quyền
-- EXECUTE trên thủ tục này, không có quyền nào trên các bảng nó đụng tới
-- (quyền tối thiểu, chương 6.2). Thủ tục chạy bằng quyền của
-- bookstore_definer (SQL SECURITY DEFINER, tài khoản khóa đăng nhập).
--
-- Chống race condition (SECURITY_CHECKLIST mục 6):
--   1. Khóa dòng giỏ của người dùng (FOR UPDATE): hai lần bấm của CÙNG một
--      người phải xếp hàng, lần sau thấy đơn đã có thì trả lại mã cũ.
--   2. Khóa các dòng sách trong giỏ (FOR UPDATE): hai người KHÁC nhau cùng
--      mua cuốn cuối thì người đến sau phải chờ, rồi nhận OUT_OF_STOCK.
--   Thứ tự khóa sách: InnoDB khóa dòng theo thứ tự nó đọc. Câu khóa đi từ
--   orders_cartitem theo chỉ mục UNIQUE (cart_id, book_id) nên đọc sách theo
--   book_id tăng dần (STRAIGHT_JOIN giữ đúng thứ tự bảng). Mọi giao dịch
--   khóa theo cùng một thứ tự → không có vòng chờ → không deadlock.
--
-- Tham số:
--   p_user_id           id người dùng, Django lấy từ request.user (KHÔNG từ form)
--   p_idempotency_key   32 ký tự hex thường, Django sinh khi mở trang đặt hàng
--   p_shipping_name     tên người nhận, 1–100 ký tự (tham số khai báo 255 để
--                       chuỗi dài quá vẫn vào được thủ tục và nhận INVALID_INPUT)
--   p_phone_encrypted   SĐT đã mã hóa AES-GCM ở Django
--   p_address_encrypted địa chỉ đã mã hóa AES-GCM ở Django
--   p_hold_minutes      số phút giữ kho chờ thanh toán (settings ORDER_HOLD_MINUTES, 1–60)
--   p_max_items         tổng số cuốn tối đa của một đơn (settings ORDER_MAX_ITEMS, 1–150)
--   p_order_code (OUT)  mã đơn (32 ký tự hex)
--   p_created    (OUT)  1 = đơn mới tạo, 0 = bấm lại, trả mã đơn cũ
--
-- Lỗi (SIGNAL SQLSTATE '45000', MESSAGE_TEXT là đúng 1 trong 8 mã):
--   INVALID_INPUT   tham số sai, hoặc mã yêu cầu đã thuộc người khác
--   NOT_CUSTOMER    người gọi là nhân viên, bị khóa hoặc chưa xác nhận email
--   PENDING_EXISTS  khách đang có 1 đơn chờ thanh toán còn hạn
--   CART_EMPTY      giỏ rỗng hoặc chưa có giỏ
--   BOOK_INACTIVE   có sách đã ngừng bán
--   OUT_OF_STOCK    có sách không đủ số lượng
--   ORDER_TOO_LARGE tổng số cuốn trong giỏ vượt p_max_items
--   ACCOUNT_LOCKED  tài khoản đang bị khóa tự động vì giữ kho (auto_locked_until)
--
-- Bổ sung 2026-11-20 (báo cáo rà soát T3.4 – giữ kho không thanh toán): thời gian
-- giữ kho rút còn 5 phút và truyền từ Django; mỗi đơn tối đa 20 cuốn; tài khoản bỏ
-- 3 đơn chưa thanh toán trong 24 giờ bị khóa 24 giờ (33_order_cancel.sql).
--
-- Bổ sung 2026-11-16 (nhánh đặt hàng):
--   - Tự kiểm tra lại người gọi là khách hợp lệ (NOT_CUSTOMER), như các thủ
--     tục giỏ hàng.
--   - Chống "giữ kho": kho bị trừ ngay khi tạo đơn, nên mỗi khách chỉ được có
--     tối đa 1 đơn 'pending' còn hạn. Kiểm tra sau khi khóa giỏ nên hai lần
--     đặt cùng lúc của cùng một người không lọt qua được.
--   - Đơn đã tạo không sửa được: trigger ở 32_trg_orders_guard.sql.
-- Lỗi ở bất kỳ bước nào: ROLLBACK, không có đơn dở dang, kho và giỏ giữ nguyên.
--
-- Root tạo thủ tục bằng `python manage.py db_apply`. Chạy lại nhiều lần được.
-- =====================================================================

DROP PROCEDURE IF EXISTS sp_place_order;
DROP PROCEDURE IF EXISTS sp_order_get;

DELIMITER $$

-- AI-TRACE#001 | Claude Opus 5.5 | Thủ tục đặt đơn: khóa giỏ và sách, kiểm tra kho, tạo đơn, trừ kho | CẤM XÓA CHÚ THÍCH NÀY | đã viết lại bởi Claude Opus 5.5 khi thêm thời gian giữ kho, giới hạn số cuốn và khóa giữ kho
CREATE DEFINER = 'bookstore_definer'@'localhost' PROCEDURE sp_place_order(
    IN  p_user_id           BIGINT,
    IN  p_idempotency_key   CHAR(32),
    IN  p_shipping_name     VARCHAR(255),
    IN  p_phone_encrypted   VARCHAR(512),
    IN  p_address_encrypted VARCHAR(1024),
    IN  p_hold_minutes      INT,
    IN  p_max_items         INT,
    OUT p_order_code        CHAR(32),
    OUT p_created           TINYINT
)
SQL SECURITY DEFINER
MODIFIES SQL DATA
proc: BEGIN
    -- Phí ship cố định (chốt 2026-11-14)
    DECLARE c_shipping_fee   INT UNSIGNED DEFAULT 30000;

    DECLARE v_now            DATETIME(6);
    DECLARE v_cart_id        BIGINT DEFAULT NULL;
    DECLARE v_existing_code  CHAR(32) DEFAULT NULL;
    DECLARE v_existing_user  BIGINT DEFAULT NULL;
    DECLARE v_line_count     INT DEFAULT 0;
    DECLARE v_inactive_count INT DEFAULT 0;
    DECLARE v_short_count    INT DEFAULT 0;
    DECLARE v_subtotal       BIGINT DEFAULT 0;
    DECLARE v_order_id       BIGINT;
    DECLARE v_code           CHAR(32);
    DECLARE v_customer       INT DEFAULT 0;
    DECLARE v_pending_count  INT DEFAULT 0;
    DECLARE v_item_total     BIGINT DEFAULT 0;
    DECLARE v_locked_until   DATETIME(6) DEFAULT NULL;

    -- Bước 1: lỗi ở đâu cũng hủy toàn bộ giao dịch rồi báo lỗi ra ngoài
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    SET p_order_code = NULL;
    SET p_created = 0;

    -- Bước 2: kiểm tra tham số trước khi đụng vào dữ liệu.
    -- REGEXP_LIKE(..., 'c') so khớp phân biệt hoa/thường (collation của CSDL
    -- không phân biệt, nên REGEXP thường sẽ nhận cả 'ABC...').
    IF p_user_id IS NULL OR p_user_id <= 0
       OR p_idempotency_key IS NULL
       OR NOT REGEXP_LIKE(p_idempotency_key, '^[0-9a-f]{32}$', 'c')
       OR p_shipping_name IS NULL
       OR CHAR_LENGTH(TRIM(p_shipping_name)) = 0
       OR CHAR_LENGTH(p_shipping_name) > 100
       OR p_phone_encrypted IS NULL OR CHAR_LENGTH(p_phone_encrypted) = 0
       OR p_address_encrypted IS NULL OR CHAR_LENGTH(p_address_encrypted) = 0
       OR p_hold_minutes IS NULL OR p_hold_minutes < 1 OR p_hold_minutes > 60
       OR p_max_items IS NULL OR p_max_items < 1 OR p_max_items > 150
    THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'INVALID_INPUT';
    END IF;

    -- AI-TRACE#259 | Claude Opus 5.5 | sp_place_order tự kiểm tra lại người gọi là khách hợp lệ (đang hoạt động, không phải nhân viên, đã xác nhận email) | CẤM XÓA CHÚ THÍCH NÀY
    SELECT COUNT(*) INTO v_customer
      FROM accounts_user
     WHERE id = p_user_id AND is_active = 1 AND is_staff = 0 AND email_verified = 1;
    IF v_customer = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'NOT_CUSTOMER';
    END IF;

    SET v_now = UTC_TIMESTAMP(6);

    -- AI-TRACE#533 | Claude Opus 5.5 | sp_place_order từ chối tài khoản đang bị khóa tự động vì giữ kho (lớp 2, kể cả khi gọi thẳng thủ tục) | CẤM XÓA CHÚ THÍCH NÀY
    SELECT auto_locked_until INTO v_locked_until FROM accounts_user WHERE id = p_user_id;
    IF v_locked_until IS NOT NULL AND v_locked_until > v_now THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ACCOUNT_LOCKED';
    END IF;

    -- Bước 3: mở giao dịch
    START TRANSACTION;

    -- Bước 4: khóa giỏ của người dùng. Lần bấm thứ hai của cùng người này
    -- đứng chờ ở đây cho tới khi lần đầu COMMIT.
    SELECT id INTO v_cart_id
      FROM orders_cart
     WHERE user_id = p_user_id
       FOR UPDATE;

    -- Bước 5: mã yêu cầu đã có đơn → bấm lại, trả mã đơn cũ
    SELECT code, user_id INTO v_existing_code, v_existing_user
      FROM orders_order
     WHERE idempotency_key = p_idempotency_key;

    IF v_existing_code IS NOT NULL THEN
        IF v_existing_user <> p_user_id THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'INVALID_INPUT';
        END IF;
        SET p_order_code = v_existing_code;
        SET p_created = 0;
        COMMIT;
        LEAVE proc;
    END IF;

    IF v_cart_id IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'CART_EMPTY';
    END IF;

    -- AI-TRACE#260 | Claude Opus 5.5 | Chống giữ kho: mỗi khách tối đa 1 đơn chờ thanh toán còn hạn, kiểm tra khi đang giữ khóa giỏ | CẤM XÓA CHÚ THÍCH NÀY
    SELECT COUNT(*) INTO v_pending_count
      FROM orders_order
     WHERE user_id = p_user_id AND status = 'pending' AND expires_at > v_now;
    IF v_pending_count > 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'PENDING_EXISTS';
    END IF;

    -- Bước 6: khóa các dòng sách trong giỏ và tính toán trong cùng một câu.
    -- Giá lấy từ catalog_book, không bao giờ từ phía người dùng.
    SELECT COUNT(*),
           COALESCE(SUM(b.is_active = 0), 0),
           COALESCE(SUM(b.stock < ci.quantity), 0),
           COALESCE(SUM(b.price * ci.quantity), 0),
           COALESCE(SUM(ci.quantity), 0)
      INTO v_line_count, v_inactive_count, v_short_count, v_subtotal, v_item_total
      FROM orders_cartitem ci
      STRAIGHT_JOIN catalog_book b ON b.id = ci.book_id
     WHERE ci.cart_id = v_cart_id
       FOR UPDATE;

    -- Bước 7: kiểm tra giỏ
    IF v_line_count = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'CART_EMPTY';
    END IF;
    IF v_item_total > p_max_items THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ORDER_TOO_LARGE';
    END IF;
    IF v_inactive_count > 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'BOOK_INACTIVE';
    END IF;
    IF v_short_count > 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'OUT_OF_STOCK';
    END IF;

    -- Bước 8: tạo đơn. Mã đơn ngẫu nhiên mật mã (RANDOM_BYTES), không dùng
    -- UUID() vì UUID sinh theo thời gian nên đoán được.
    SET v_code = LOWER(HEX(RANDOM_BYTES(16)));

    INSERT INTO orders_order (
        code, user_id, status, subtotal, shipping_fee, total,
        shipping_name, shipping_phone_encrypted, shipping_address_encrypted,
        idempotency_key, created_at, updated_at, expires_at
    ) VALUES (
        v_code, p_user_id, 'pending', v_subtotal, c_shipping_fee, v_subtotal + c_shipping_fee,
        TRIM(p_shipping_name), p_phone_encrypted, p_address_encrypted,
        p_idempotency_key, v_now, v_now, v_now + INTERVAL p_hold_minutes MINUTE
    );
    SET v_order_id = LAST_INSERT_ID();

    -- Bước 9: chép giỏ sang chi tiết đơn (tên sách, giá lúc đặt)
    INSERT INTO orders_orderitem (order_id, book_id, book_title, unit_price, quantity)
    SELECT v_order_id, b.id, b.title, b.price, ci.quantity
      FROM orders_cartitem ci
      JOIN catalog_book b ON b.id = ci.book_id
     WHERE ci.cart_id = v_cart_id;

    -- Bước 10: trừ kho, xóa giỏ, chốt giao dịch
    UPDATE catalog_book b
      JOIN orders_cartitem ci ON ci.book_id = b.id
       SET b.stock = b.stock - ci.quantity
     WHERE ci.cart_id = v_cart_id;

    DELETE FROM orders_cartitem WHERE cart_id = v_cart_id;

    SET p_order_code = v_code;
    SET p_created = 1;
    COMMIT;
END proc$$

-- AI-TRACE#261 | Claude Opus 5.5 | Thủ tục đọc một đơn của chính khách theo mã đơn: dòng đầu là đơn, bộ kết quả thứ hai là các sách; đơn của người khác báo như không tồn tại | CẤM XÓA CHÚ THÍCH NÀY
-- Trả 2 bộ kết quả:
--   1. đơn: code, status, subtotal, shipping_fee, total, shipping_name,
--      shipping_phone_encrypted, shipping_address_encrypted, idempotency_key
--      (Django dùng làm ngữ cảnh giải mã, không đưa ra template), created_at,
--      expires_at, paid_at, cancelled_at
--   2. sách: book_id, book_title, unit_price, quantity
-- Mã đơn sai mẫu, đơn không có hoặc đơn của người khác → ORDER_NOT_FOUND như
-- nhau (chống IDOR: không dò được mã đơn của người khác).
CREATE DEFINER = 'bookstore_definer'@'localhost' PROCEDURE sp_order_get(
    IN p_user_id  BIGINT,
    IN p_code     VARCHAR(64)
)
SQL SECURITY DEFINER
READS SQL DATA
BEGIN
    DECLARE v_customer INT DEFAULT 0;
    DECLARE v_order_id BIGINT DEFAULT NULL;

    IF p_user_id IS NULL OR p_user_id <= 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'INVALID_INPUT';
    END IF;

    SELECT COUNT(*) INTO v_customer
      FROM accounts_user
     WHERE id = p_user_id AND is_active = 1 AND is_staff = 0 AND email_verified = 1;
    IF v_customer = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'NOT_CUSTOMER';
    END IF;

    IF p_code IS NULL OR NOT REGEXP_LIKE(p_code, '^[0-9a-f]{32}$', 'c') THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ORDER_NOT_FOUND';
    END IF;

    SELECT id INTO v_order_id
      FROM orders_order
     WHERE code = p_code AND user_id = p_user_id;
    IF v_order_id IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ORDER_NOT_FOUND';
    END IF;

    SELECT code, status, subtotal, shipping_fee, total, shipping_name,
           shipping_phone_encrypted, shipping_address_encrypted, idempotency_key,
           created_at, expires_at, paid_at, cancelled_at
      FROM orders_order
     WHERE id = v_order_id;

    SELECT book_id, book_title, unit_price, quantity
      FROM orders_orderitem
     WHERE order_id = v_order_id
     ORDER BY id;
END$$

DELIMITER ;


-- Phần 31: Thủ tục giỏ hàng
-- =====================================================================
-- Giỏ hàng của khách (orders_cart, orders_cartitem).
--
--   sp_cart_add           thêm sách vào giỏ; sách đã có thì cộng thêm số lượng
--   sp_cart_list          đọc giỏ của khách (trang /orders/cart/)
--   sp_cart_set_quantity  đặt số lượng mới cho một sách trong giỏ (nút + / −)
--   sp_cart_remove        gỡ một sách khỏi giỏ
--
-- Chốt 2026-11-15:
--   - Mỗi đầu sách trong giỏ tối đa 5 cuốn (bảng còn CHECK 1..10 làm giới hạn
--     ngoài cùng). Cộng dồn vượt 5 → CART_LIMIT, không tự đổi số lượng.
--   - Mỗi giỏ tối đa 30 đầu sách khác nhau → CART_FULL (chống lạm dụng).
--   - Chỉ khách đang hoạt động, đã xác nhận email, không phải nhân viên.
--   - Chỉ sách đang hiện và còn hàng (stock > 0). KHÔNG so số lượng với tồn
--     kho thật ở bước này để khách không dò được số tồn kho; sp_place_order
--     kiểm tra tồn kho chính xác (có khóa dòng) lúc đặt hàng.
--
-- Bảo mật / race condition:
--   - p_user_id do Django lấy từ phiên đăng nhập, thủ tục kiểm tra lại.
--   - Giỏ tạo bằng INSERT ... ON DUPLICATE KEY UPDATE trên UNIQUE(user_id),
--     rồi khóa dòng giỏ FOR UPDATE, nên hai lần bấm cùng lúc xếp hàng, cộng
--     đúng, không tạo hai giỏ hay hai dòng.
--   - Thứ tự khóa giống sp_place_order (giỏ trước, sách sau; ở đây sách chỉ
--     khóa chia sẻ FOR SHARE) để hai thủ tục không chờ chéo nhau (deadlock).
--   - r_customer chỉ có EXECUTE; không có quyền nào trên orders_cart*.
--
-- Lỗi (SIGNAL SQLSTATE '45000', MESSAGE_TEXT là đúng một mã):
--   INVALID_INPUT   tham số sai (số lượng ngoài 1–5)
--   NOT_CUSTOMER    không phải khách hợp lệ
--   BOOK_NOT_FOUND  sách không tồn tại hoặc đang ẩn
--   OUT_OF_STOCK    sách hết hàng
--   CART_LIMIT      tổng số cuốn của sách này trong giỏ sẽ vượt 5
--   CART_FULL       giỏ đã có 30 đầu sách
--   NOT_IN_CART     sách không có trong giỏ của khách này
--   BOOK_UNAVAILABLE sách trong giỏ đã bị ẩn (ngừng bán) – chỉ còn gỡ được
--
-- Trang giỏ hàng (chốt 2026-11-15):
--   - Tăng/giảm dùng chung sp_cart_set_quantity nhận SỐ LƯỢNG CUỐI CÙNG (1–5),
--     không nhận "+1": bấm đúp, hai tab, gửi lại form vẫn ra đúng con số đó.
--   - Đang 1 cuốn thì nút "−" bị khóa; bỏ sách phải bấm Gỡ (sp_cart_remove),
--     không hỏi xác nhận.
--   - Sách bị ẩn: hiện mờ "Ngừng bán", chỉ gỡ được (BOOK_UNAVAILABLE).
--     Sách hết hàng: hiện mờ "Hết hàng", không tăng được (OUT_OF_STOCK);
--     giảm vẫn cho vì vô hại. Hai loại này không tính vào "Tạm tính".
--   - sp_cart_list trả in_stock (0/1), không trả số tồn kho.
--   - Sách không có trong giỏ → NOT_IN_CART dù sách có tồn tại hay không,
--     nên không dò được sách ẩn qua các thủ tục này.
--
-- Root tạo bằng `python manage.py db_apply`. Chạy lại nhiều lần được.
-- =====================================================================

DROP PROCEDURE IF EXISTS sp_cart_add;
DROP PROCEDURE IF EXISTS sp_cart_list;
DROP PROCEDURE IF EXISTS sp_cart_set_quantity;
DROP PROCEDURE IF EXISTS sp_cart_remove;

DELIMITER $$

-- AI-TRACE#226 | Claude Opus 5.5 | Thủ tục thêm sách vào giỏ: kiểm tra khách, sách còn hàng, cộng dồn tối đa 5 cuốn, tối đa 30 đầu sách, khóa giỏ chống bấm trùng | CẤM XÓA CHÚ THÍCH NÀY
CREATE DEFINER = 'bookstore_definer'@'localhost' PROCEDURE sp_cart_add(
    IN  p_user_id       BIGINT,
    IN  p_book_id       BIGINT,
    IN  p_quantity      INT,
    OUT p_new_quantity  INT
)
SQL SECURITY DEFINER
MODIFIES SQL DATA
BEGIN
    DECLARE v_customer INT DEFAULT 0;
    DECLARE v_stock    INT DEFAULT NULL;
    DECLARE v_cart_id  BIGINT DEFAULT NULL;
    DECLARE v_old      INT DEFAULT NULL;
    DECLARE v_items    INT DEFAULT 0;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    SET p_new_quantity = NULL;

    IF p_user_id IS NULL OR p_user_id <= 0
       OR p_book_id IS NULL OR p_book_id <= 0
       OR p_quantity IS NULL OR p_quantity < 1 OR p_quantity > 5
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

    -- Giỏ của khách: tạo nếu chưa có, lấy id nếu đã có, rồi khóa dòng giỏ
    INSERT INTO orders_cart (user_id) VALUES (p_user_id)
    ON DUPLICATE KEY UPDATE id = LAST_INSERT_ID(id);
    SET v_cart_id = LAST_INSERT_ID();

    SELECT id INTO v_cart_id FROM orders_cart WHERE id = v_cart_id FOR UPDATE;

    SELECT stock INTO v_stock
      FROM catalog_book
     WHERE id = p_book_id AND is_active = 1
       FOR SHARE;
    IF v_stock IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'BOOK_NOT_FOUND';
    END IF;
    IF v_stock <= 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'OUT_OF_STOCK';
    END IF;

    SELECT quantity INTO v_old
      FROM orders_cartitem
     WHERE cart_id = v_cart_id AND book_id = p_book_id;

    IF v_old IS NULL THEN
        SELECT COUNT(*) INTO v_items FROM orders_cartitem WHERE cart_id = v_cart_id;
        IF v_items >= 30 THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'CART_FULL';
        END IF;
        INSERT INTO orders_cartitem (cart_id, book_id, quantity)
        VALUES (v_cart_id, p_book_id, p_quantity);
        SET p_new_quantity = p_quantity;
    ELSE
        IF v_old + p_quantity > 5 THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'CART_LIMIT';
        END IF;
        UPDATE orders_cartitem
           SET quantity = v_old + p_quantity
         WHERE cart_id = v_cart_id AND book_id = p_book_id;
        SET p_new_quantity = v_old + p_quantity;
    END IF;

    UPDATE orders_cart SET updated_at = CURRENT_TIMESTAMP(6) WHERE id = v_cart_id;

    COMMIT;
END$$

-- AI-TRACE#238 | Claude Opus 5.5 | Thủ tục đọc giỏ của khách: sách, giá hiện tại, số lượng, tình trạng còn bán/còn hàng, không trả số tồn kho | CẤM XÓA CHÚ THÍCH NÀY
CREATE DEFINER = 'bookstore_definer'@'localhost' PROCEDURE sp_cart_list(
    IN p_user_id  BIGINT
)
SQL SECURITY DEFINER
READS SQL DATA
BEGIN
    DECLARE v_customer INT DEFAULT 0;

    IF p_user_id IS NULL OR p_user_id <= 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'INVALID_INPUT';
    END IF;

    SELECT COUNT(*) INTO v_customer
      FROM accounts_user
     WHERE id = p_user_id AND is_active = 1 AND is_staff = 0 AND email_verified = 1;
    IF v_customer = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'NOT_CUSTOMER';
    END IF;

    SELECT b.id, b.title, b.author, b.cover_image, b.price, i.quantity,
           b.is_active, (b.stock > 0) AS in_stock
      FROM orders_cart c
      JOIN orders_cartitem i ON i.cart_id = c.id
      JOIN catalog_book b    ON b.id = i.book_id
     WHERE c.user_id = p_user_id
     ORDER BY i.added_at, i.id
     LIMIT 30;
END$$

-- AI-TRACE#239 | Claude Opus 5.5 | Thủ tục đặt số lượng mới (1–5) cho sách trong giỏ: dùng cho cả tăng và giảm, khóa giỏ chống bấm trùng, sách ẩn không đổi được, hết hàng không tăng được | CẤM XÓA CHÚ THÍCH NÀY
CREATE DEFINER = 'bookstore_definer'@'localhost' PROCEDURE sp_cart_set_quantity(
    IN p_user_id   BIGINT,
    IN p_book_id   BIGINT,
    IN p_quantity  INT
)
SQL SECURITY DEFINER
MODIFIES SQL DATA
BEGIN
    DECLARE v_customer INT DEFAULT 0;
    DECLARE v_cart_id  BIGINT DEFAULT NULL;
    DECLARE v_old      INT DEFAULT NULL;
    DECLARE v_active   TINYINT DEFAULT NULL;
    DECLARE v_stock    INT DEFAULT NULL;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    IF p_user_id IS NULL OR p_user_id <= 0
       OR p_book_id IS NULL OR p_book_id <= 0
       OR p_quantity IS NULL OR p_quantity < 1 OR p_quantity > 5
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

    SELECT id INTO v_cart_id FROM orders_cart WHERE user_id = p_user_id FOR UPDATE;
    IF v_cart_id IS NOT NULL THEN
        SELECT quantity INTO v_old
          FROM orders_cartitem
         WHERE cart_id = v_cart_id AND book_id = p_book_id;
    END IF;
    IF v_old IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'NOT_IN_CART';
    END IF;

    SELECT is_active, stock INTO v_active, v_stock
      FROM catalog_book
     WHERE id = p_book_id
       FOR SHARE;
    IF v_active IS NULL OR v_active <> 1 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'BOOK_UNAVAILABLE';
    END IF;
    IF p_quantity > v_old AND v_stock <= 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'OUT_OF_STOCK';
    END IF;

    IF p_quantity <> v_old THEN
        UPDATE orders_cartitem
           SET quantity = p_quantity
         WHERE cart_id = v_cart_id AND book_id = p_book_id;
        UPDATE orders_cart SET updated_at = CURRENT_TIMESTAMP(6) WHERE id = v_cart_id;
    END IF;

    COMMIT;
END$$

-- AI-TRACE#240 | Claude Opus 5.5 | Thủ tục gỡ một sách khỏi giỏ của khách; gỡ được cả sách đã ngừng bán hoặc hết hàng | CẤM XÓA CHÚ THÍCH NÀY
CREATE DEFINER = 'bookstore_definer'@'localhost' PROCEDURE sp_cart_remove(
    IN p_user_id  BIGINT,
    IN p_book_id  BIGINT
)
SQL SECURITY DEFINER
MODIFIES SQL DATA
BEGIN
    DECLARE v_customer INT DEFAULT 0;
    DECLARE v_cart_id  BIGINT DEFAULT NULL;
    DECLARE v_deleted  INT DEFAULT 0;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    IF p_user_id IS NULL OR p_user_id <= 0 OR p_book_id IS NULL OR p_book_id <= 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'INVALID_INPUT';
    END IF;

    SELECT COUNT(*) INTO v_customer
      FROM accounts_user
     WHERE id = p_user_id AND is_active = 1 AND is_staff = 0 AND email_verified = 1;
    IF v_customer = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'NOT_CUSTOMER';
    END IF;

    START TRANSACTION;

    SELECT id INTO v_cart_id FROM orders_cart WHERE user_id = p_user_id FOR UPDATE;
    IF v_cart_id IS NOT NULL THEN
        DELETE FROM orders_cartitem WHERE cart_id = v_cart_id AND book_id = p_book_id;
        SET v_deleted = ROW_COUNT();
    END IF;
    IF v_deleted = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'NOT_IN_CART';
    END IF;

    UPDATE orders_cart SET updated_at = CURRENT_TIMESTAMP(6) WHERE id = v_cart_id;

    COMMIT;
END$$

DELIMITER ;


-- Phần 32: Trigger khóa đơn hàng đã tạo
-- =====================================================================
-- Đơn hàng đã tạo thì không sửa được (chốt 2026-11-16).
--
-- Yêu cầu: thanh toán xong không thể tự tăng số lượng sách hay thêm sách
-- khác vào đơn. Lớp 1 là quyền: không tài khoản ứng dụng nào có quyền ghi
-- orders_order/orders_orderitem, không có thủ tục nào sửa đơn. Lớp 2 là các
-- trigger dưới đây, chặn ngay trong CSDL kể cả khi definer hoặc một thủ tục
-- sau này có lỗi:
--
--   orders_orderitem (chi tiết đơn)
--     - Chỉ thêm được khi đơn đang 'pending' và chưa thanh toán (đúng lúc
--       sp_place_order tạo đơn). Đơn đã thanh toán/đang giao/đã hủy → chặn.
--     - Tổng tiền các dòng không bao giờ vượt subtotal đã chốt của đơn.
--       sp_place_order chép giỏ sang đơn nên các dòng cộng lại vừa đúng bằng
--       subtotal; sau đó chèn thêm bất kỳ dòng nào cũng vượt → chặn. Nhờ vậy
--       đơn đang chờ thanh toán cũng không bị thêm sách sau khi tạo.
--     - Không bao giờ sửa (giá, số lượng, tên sách) và không bao giờ xóa.
--   orders_order (đơn)
--     - Không bao giờ đổi: mã đơn, người đặt, tiền sách, phí ship, tổng tiền,
--       thông tin giao hàng, mã chống trùng, ngày tạo, hạn thanh toán.
--     - Chỉ đổi trạng thái theo đúng chiều:
--         pending → paid, pending → cancelled,
--         paid → confirmed → packed → shipped → delivered (từng bước một,
--         không nhảy cóc, không quay lại – chốt 2026-11-16)
--       paid_at chỉ được ghi một lần lúc chuyển sang 'paid',
--       cancelled_at chỉ được ghi một lần lúc chuyển sang 'cancelled'.
--     - Không bao giờ xóa đơn (giữ lịch sử).
--
-- Mã lỗi: ORDER_LOCKED. Chạy bằng quyền bookstore_definer (khóa đăng nhập).
-- Root tạo trigger bằng `python manage.py db_apply`. Chạy lại nhiều lần được.
-- =====================================================================

DROP TRIGGER IF EXISTS trg_orderitem_guard_insert;
DROP TRIGGER IF EXISTS trg_orderitem_guard_update;
DROP TRIGGER IF EXISTS trg_orderitem_guard_delete;
DROP TRIGGER IF EXISTS trg_order_guard_update;
DROP TRIGGER IF EXISTS trg_order_guard_delete;

DELIMITER $$

-- AI-TRACE#262 | Claude Opus 5.5 | Trigger chỉ cho thêm sách vào đơn đang chờ thanh toán lúc tạo đơn: tổng các dòng không vượt subtotal đã chốt, đơn đã thanh toán/giao/hủy bị chặn | CẤM XÓA CHÚ THÍCH NÀY
CREATE DEFINER = 'bookstore_definer'@'localhost'
TRIGGER trg_orderitem_guard_insert
BEFORE INSERT ON orders_orderitem
FOR EACH ROW
BEGIN
    DECLARE v_status   VARCHAR(20) DEFAULT NULL;
    DECLARE v_paid_at  DATETIME(6) DEFAULT NULL;
    DECLARE v_subtotal BIGINT DEFAULT 0;
    DECLARE v_lines    BIGINT DEFAULT 0;

    SELECT status, paid_at, subtotal INTO v_status, v_paid_at, v_subtotal
      FROM orders_order
     WHERE id = NEW.order_id;
    IF v_status IS NULL OR v_status <> 'pending' OR v_paid_at IS NOT NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ORDER_LOCKED';
    END IF;

    SELECT COALESCE(SUM(unit_price * quantity), 0) INTO v_lines
      FROM orders_orderitem
     WHERE order_id = NEW.order_id;
    IF v_lines + NEW.unit_price * NEW.quantity > v_subtotal THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ORDER_LOCKED';
    END IF;
END$$

-- AI-TRACE#263 | Claude Opus 5.5 | Trigger cấm sửa và xóa chi tiết đơn hàng (giá, số lượng, tên sách) | CẤM XÓA CHÚ THÍCH NÀY
CREATE DEFINER = 'bookstore_definer'@'localhost'
TRIGGER trg_orderitem_guard_update
BEFORE UPDATE ON orders_orderitem
FOR EACH ROW
BEGIN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ORDER_LOCKED';
END$$

CREATE DEFINER = 'bookstore_definer'@'localhost'
TRIGGER trg_orderitem_guard_delete
BEFORE DELETE ON orders_orderitem
FOR EACH ROW
BEGIN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ORDER_LOCKED';
END$$

-- AI-TRACE#264 | Claude Opus 5.5 | Trigger cấm đổi tiền, thông tin giao hàng của đơn; trạng thái chỉ đi tới đúng một bước (đã thanh toán → tiếp nhận → đóng gói → đang giao → đã giao), không quay lại; mốc thanh toán/hủy ghi một lần | CẤM XÓA CHÚ THÍCH NÀY
CREATE DEFINER = 'bookstore_definer'@'localhost'
TRIGGER trg_order_guard_update
BEFORE UPDATE ON orders_order
FOR EACH ROW
BEGIN
    -- <=> là so sánh an toàn với NULL (NULL <=> NULL là đúng).
    IF NOT (NEW.id <=> OLD.id AND NEW.code <=> OLD.code AND NEW.user_id <=> OLD.user_id
            AND NEW.subtotal <=> OLD.subtotal AND NEW.shipping_fee <=> OLD.shipping_fee
            AND NEW.total <=> OLD.total AND NEW.shipping_name <=> OLD.shipping_name
            AND NEW.shipping_phone_encrypted <=> OLD.shipping_phone_encrypted
            AND NEW.shipping_address_encrypted <=> OLD.shipping_address_encrypted
            AND NEW.idempotency_key <=> OLD.idempotency_key
            AND NEW.created_at <=> OLD.created_at AND NEW.expires_at <=> OLD.expires_at) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ORDER_LOCKED';
    END IF;

    IF NOT (NEW.status <=> OLD.status) AND NOT (
           (OLD.status = 'pending' AND NEW.status IN ('paid', 'cancelled'))
        OR (OLD.status = 'paid'      AND NEW.status = 'confirmed')
        OR (OLD.status = 'confirmed' AND NEW.status = 'packed')
        OR (OLD.status = 'packed'    AND NEW.status = 'shipped')
        OR (OLD.status = 'shipped'   AND NEW.status = 'delivered')) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ORDER_LOCKED';
    END IF;

    IF NOT (NEW.paid_at <=> OLD.paid_at)
       AND NOT (OLD.paid_at IS NULL AND OLD.status = 'pending' AND NEW.status = 'paid') THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ORDER_LOCKED';
    END IF;

    IF NOT (NEW.cancelled_at <=> OLD.cancelled_at)
       AND NOT (OLD.cancelled_at IS NULL AND OLD.status = 'pending' AND NEW.status = 'cancelled') THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ORDER_LOCKED';
    END IF;
END$$

-- AI-TRACE#265 | Claude Opus 5.5 | Trigger cấm xóa đơn hàng để giữ lịch sử | CẤM XÓA CHÚ THÍCH NÀY
CREATE DEFINER = 'bookstore_definer'@'localhost'
TRIGGER trg_order_guard_delete
BEFORE DELETE ON orders_order
FOR EACH ROW
BEGIN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ORDER_LOCKED';
END$$

DELIMITER ;


-- Phần 33: Thủ tục hủy đơn, hủy đơn quá hạn và Event
-- =====================================================================
-- Hậu xử lý đơn hàng (chốt 2026-11-16, nhánh A trước khung thanh toán):
--   sp_order_cancel           khách tự hủy đơn chưa thanh toán của chính mình
--   sp_cancel_expired_orders  hủy mọi đơn chờ thanh toán đã quá hạn (hạn do sp_place_order đặt, 5 phút)
--   sp_order_hold_check       (nội bộ) đếm đơn bỏ không thanh toán, đủ ngưỡng thì khóa tài khoản 24 giờ
--   ev_cancel_expired_orders  MySQL Event gọi thủ tục trên mỗi phút
--
-- Kho bị trừ ngay khi tạo đơn (sp_place_order), nên hủy đơn = cộng lại đúng
-- số cuốn trong chi tiết đơn, cùng giao dịch với việc đổi trạng thái.
--
-- Quy tắc:
--   - Chỉ đơn 'pending' mới hủy được. Đơn đã thanh toán không hủy (không có
--     hoàn tiền); trigger 32_trg_orders_guard.sql cũng chặn paid → cancelled.
--   - Khách hủy được cả đơn đã quá hạn mà Event chưa kịp xử lý.
--   - Mỗi đơn hủy trong một giao dịch riêng, khóa dòng đơn FOR UPDATE rồi mới
--     kiểm tra lại trạng thái: khách bấm hủy đúng lúc Event chạy (hoặc bấm hai
--     lần) thì chỉ một bên hủy được, kho chỉ được cộng một lần.
--   - Thứ tự khóa: đơn → sách. sp_place_order khóa giỏ → sách và không khóa
--     dòng đơn cũ nào, nên không tạo vòng chờ (không deadlock).
--   - Sau này thủ tục ghi nhận thanh toán cũng khóa dòng đơn FOR UPDATE và
--     chỉ nhận khi expires_at > lúc đó; Event chỉ hủy khi expires_at <= lúc
--     đó. Hai bên xếp hàng trên cùng dòng đơn nên không có đơn vừa "đã thanh
--     toán" vừa "đã hủy".
--
-- Chống giữ kho (báo cáo rà soát T3.4, chốt 2026-11-20):
--   Mỗi lần một đơn 'pending' bị hủy (khách bấm) hoặc hết hạn (Event), trong CÙNG
--   giao dịch gọi sp_order_hold_check: đếm số đơn của khách đó bị hủy mà chưa thanh
--   toán, tính từ mốc muộn hơn giữa (24 giờ trước) và (lần hết khóa / admin mở khóa
--   gần nhất = accounts_user.auto_locked_until cũ). Đủ 3 đơn thì đặt
--   auto_locked_until = lúc đó + 24 giờ: Django coi tài khoản là bị khóa (đăng xuất
--   mọi nơi, không đăng nhập được), sp_place_order cũng từ chối (ACCOUNT_LOCKED).
--   Ngưỡng viết ở đây (không truyền từ Django) vì đường hết hạn do Event chạy,
--   không có Django. Không dùng is_active: đó là khóa của admin (có lý do, nhật ký),
--   và trigger 10 cấm app_customer đổi is_active.
--   Admin mở khóa sớm được bằng sp_staff_account_unlock (42_account.sql).
--   Đường hết hạn tự ghi core_securityevent 'order_hold_abuse' (ip 'system');
--   đường khách hủy trả p_account_locked = 1 để Django ghi log (có IP) và đăng xuất.
--
-- Mã lỗi:
--   INVALID_INPUT, NOT_CUSTOMER
--   ORDER_NOT_FOUND        mã sai, không có, hoặc đơn của người khác (như nhau)
--   ORDER_NOT_CANCELLABLE  đơn không còn ở trạng thái chờ thanh toán
--
-- Root tạo bằng `python manage.py db_apply`. Chạy lại nhiều lần được.
-- =====================================================================

DROP EVENT IF EXISTS ev_cancel_expired_orders;
DROP PROCEDURE IF EXISTS sp_order_cancel;
DROP PROCEDURE IF EXISTS sp_order_expire_one;
DROP PROCEDURE IF EXISTS sp_cancel_expired_orders;
DROP PROCEDURE IF EXISTS sp_order_hold_check;

DELIMITER $$

-- Chỉ được gọi bên trong giao dịch của sp_order_cancel / sp_order_expire_one, sau khi
-- đã đổi đơn sang 'cancelled'. Không cấp EXECUTE cho tài khoản ứng dụng nào.
-- AI-TRACE#531 | Claude Opus 5.5 | Thủ tục nội bộ chống giữ kho: đếm đơn bị hủy chưa thanh toán trong 24 giờ (từ lần hết khóa gần nhất), đủ 3 đơn thì khóa tài khoản 24 giờ bằng auto_locked_until | CẤM XÓA CHÚ THÍCH NÀY
CREATE DEFINER = 'bookstore_definer'@'localhost' PROCEDURE sp_order_hold_check(
    IN  p_user_id  BIGINT,
    OUT p_locked   TINYINT
)
SQL SECURITY DEFINER
MODIFIES SQL DATA
BEGIN
    DECLARE c_limit        INT DEFAULT 3;
    DECLARE c_window_hours INT DEFAULT 24;
    DECLARE c_lock_hours   INT DEFAULT 24;
    DECLARE v_now          DATETIME(6);
    DECLARE v_since        DATETIME(6);
    DECLARE v_last_lock    DATETIME(6) DEFAULT NULL;
    DECLARE v_unpaid       INT DEFAULT 0;

    SET p_locked = 0;
    SET v_now = UTC_TIMESTAMP(6);

    SELECT auto_locked_until INTO v_last_lock
      FROM accounts_user
     WHERE id = p_user_id AND is_staff = 0
       FOR UPDATE;

    IF v_last_lock IS NOT NULL AND v_last_lock > v_now THEN
        SET p_locked = 1;
    ELSE
        SET v_since = v_now - INTERVAL c_window_hours HOUR;
        IF v_last_lock IS NOT NULL AND v_last_lock > v_since THEN
            SET v_since = v_last_lock;
        END IF;

        SELECT COUNT(*) INTO v_unpaid
          FROM orders_order
         WHERE user_id = p_user_id AND status = 'cancelled'
           AND paid_at IS NULL AND cancelled_at >= v_since;

        IF v_unpaid >= c_limit THEN
            UPDATE accounts_user
               SET auto_locked_until = v_now + INTERVAL c_lock_hours HOUR
             WHERE id = p_user_id AND is_staff = 0;
            SET p_locked = 1;
        END IF;
    END IF;
END$$

-- AI-TRACE#282 | Claude Opus 5.5 | Thủ tục khách tự hủy đơn chờ thanh toán của chính mình: khóa đơn, kiểm tra lại trạng thái, cộng lại kho, đổi sang cancelled trong một giao dịch | CẤM XÓA CHÚ THÍCH NÀY | đã viết lại bởi Claude Opus 5.5 khi thêm chống giữ kho (OUT p_account_locked)
CREATE DEFINER = 'bookstore_definer'@'localhost' PROCEDURE sp_order_cancel(
    IN  p_user_id         BIGINT,
    IN  p_code            VARCHAR(64),
    OUT p_account_locked  TINYINT
)
SQL SECURITY DEFINER
MODIFIES SQL DATA
BEGIN
    DECLARE v_customer INT DEFAULT 0;
    DECLARE v_order_id BIGINT DEFAULT NULL;
    DECLARE v_status   VARCHAR(20) DEFAULT NULL;
    DECLARE v_locked   TINYINT DEFAULT 0;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    SET p_account_locked = 0;

    IF p_user_id IS NULL OR p_user_id <= 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'INVALID_INPUT';
    END IF;

    SELECT COUNT(*) INTO v_customer
      FROM accounts_user
     WHERE id = p_user_id AND is_active = 1 AND is_staff = 0 AND email_verified = 1;
    IF v_customer = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'NOT_CUSTOMER';
    END IF;

    IF p_code IS NULL OR NOT REGEXP_LIKE(p_code, '^[0-9a-f]{32}$', 'c') THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ORDER_NOT_FOUND';
    END IF;

    START TRANSACTION;

    SELECT id, status INTO v_order_id, v_status
      FROM orders_order
     WHERE code = p_code AND user_id = p_user_id
       FOR UPDATE;
    IF v_order_id IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ORDER_NOT_FOUND';
    END IF;
    IF v_status <> 'pending' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ORDER_NOT_CANCELLABLE';
    END IF;

    UPDATE catalog_book b
      JOIN orders_orderitem i ON i.book_id = b.id
       SET b.stock = b.stock + i.quantity
     WHERE i.order_id = v_order_id;

    UPDATE orders_order
       SET status = 'cancelled', cancelled_at = UTC_TIMESTAMP(6)
     WHERE id = v_order_id;

    CALL sp_order_hold_check(p_user_id, v_locked);

    COMMIT;
    SET p_account_locked = v_locked;
END$$

-- AI-TRACE#283 | Claude Opus 5.5 | Thủ tục nội bộ hủy một đơn quá hạn: khóa đơn, chỉ hủy nếu vẫn pending và đã hết hạn, cộng lại kho; lỗi thì rollback riêng đơn đó | CẤM XÓA CHÚ THÍCH NÀY | đã viết lại bởi Claude Opus 5.5 khi đơn hết hạn cũng tính là bỏ đơn (chống giữ kho)
CREATE DEFINER = 'bookstore_definer'@'localhost' PROCEDURE sp_order_expire_one(
    IN  p_order_id  BIGINT,
    OUT p_done      TINYINT
)
SQL SECURITY DEFINER
MODIFIES SQL DATA
BEGIN
    DECLARE v_status  VARCHAR(20) DEFAULT NULL;
    DECLARE v_expires DATETIME(6) DEFAULT NULL;
    DECLARE v_user_id BIGINT DEFAULT NULL;
    DECLARE v_locked  TINYINT DEFAULT 0;
    DECLARE v_until   DATETIME(6) DEFAULT NULL;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    SET p_done = 0;
    START TRANSACTION;

    SELECT status, expires_at, user_id INTO v_status, v_expires, v_user_id
      FROM orders_order
     WHERE id = p_order_id
       FOR UPDATE;

    IF v_status = 'pending' AND v_expires <= UTC_TIMESTAMP(6) THEN
        UPDATE catalog_book b
          JOIN orders_orderitem i ON i.book_id = b.id
           SET b.stock = b.stock + i.quantity
         WHERE i.order_id = p_order_id;

        UPDATE orders_order
           SET status = 'cancelled', cancelled_at = UTC_TIMESTAMP(6)
         WHERE id = p_order_id;
        SET p_done = 1;

        -- AI-TRACE#532 | Claude Opus 5.5 | Đơn hết hạn cũng tính là bỏ đơn: gọi kiểm tra giữ kho, vừa khóa thì tự ghi log order_hold_abuse (Event không có Django) | CẤM XÓA CHÚ THÍCH NÀY
        SELECT auto_locked_until INTO v_until FROM accounts_user WHERE id = v_user_id;
        CALL sp_order_hold_check(v_user_id, v_locked);
        IF v_locked = 1 AND NOT (v_until IS NOT NULL AND v_until > UTC_TIMESTAMP(6)) THEN
            INSERT INTO core_securityevent (event_type, severity, user_id, ip_address, detail)
            SELECT 'order_hold_abuse', 'warning', u.id, 'system',
                   JSON_OBJECT('via', 'expired', 'order_id', p_order_id,
                               'locked_until', DATE_FORMAT(u.auto_locked_until, '%Y-%m-%dT%H:%i:%sZ'))
              FROM accounts_user u
             WHERE u.id = v_user_id;
        END IF;
    END IF;

    COMMIT;
END$$

-- AI-TRACE#284 | Claude Opus 5.5 | Thủ tục hủy các đơn chờ thanh toán đã quá hạn (tối đa 200 đơn mỗi lần), mỗi đơn một giao dịch, một đơn lỗi không chặn các đơn khác | CẤM XÓA CHÚ THÍCH NÀY
CREATE DEFINER = 'bookstore_definer'@'localhost' PROCEDURE sp_cancel_expired_orders(
    OUT p_cancelled INT
)
SQL SECURITY DEFINER
MODIFIES SQL DATA
BEGIN
    DECLARE v_done     INT DEFAULT 0;
    DECLARE v_failed   INT DEFAULT 0;
    DECLARE v_order_id BIGINT;
    DECLARE v_one      TINYINT DEFAULT 0;
    DECLARE cur_expired CURSOR FOR
        SELECT id
          FROM orders_order
         WHERE status = 'pending' AND expires_at <= UTC_TIMESTAMP(6)
         ORDER BY expires_at, id
         LIMIT 200;
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET v_done = 1;

    SET p_cancelled = 0;
    OPEN cur_expired;
    expire_loop: LOOP
        FETCH cur_expired INTO v_order_id;
        IF v_done = 1 THEN
            LEAVE expire_loop;
        END IF;
        BEGIN
            DECLARE CONTINUE HANDLER FOR SQLEXCEPTION SET v_failed = v_failed + 1;
            SET v_one = 0;
            CALL sp_order_expire_one(v_order_id, v_one);
            SET p_cancelled = p_cancelled + COALESCE(v_one, 0);
        END;
    END LOOP;
    CLOSE cur_expired;
END$$

-- AI-TRACE#285 | Claude Opus 5.5 | MySQL Event mỗi phút gọi sp_cancel_expired_orders để trả kho cho đơn quá hạn thanh toán | CẤM XÓA CHÚ THÍCH NÀY
CREATE DEFINER = 'bookstore_definer'@'localhost' EVENT ev_cancel_expired_orders
    ON SCHEDULE EVERY 1 MINUTE
    ON COMPLETION PRESERVE
    ENABLE
    COMMENT 'Hủy đơn chờ thanh toán quá hạn, cộng lại kho, khóa tài khoản giữ kho'
    DO
    BEGIN
        DECLARE v_count INT DEFAULT 0;
        CALL sp_cancel_expired_orders(v_count);
    END$$

DELIMITER ;


-- Phần 34: Trigger ghi nhật ký đơn hàng
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
--   app_staff          → staff     (quản lý đơn của admin; app_user_id = id
--                                   admin do thủ tục 44_staff_orders.sql đặt
--                                   vào biến phiên @bookstore_actor_id)
--   khác (root...)     → other
-- Thủ tục admin đổi trạng thái đơn KHÔNG tự ghi thêm core_auditlog cho việc
-- đổi trạng thái (trigger đã ghi), chỉ ghi phần riêng như lý do.
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

-- AI-TRACE#321 | Claude Opus 5.5 | Trigger ghi nhật ký khi đơn đổi trạng thái (chờ → đã thanh toán/đã hủy...), kèm nguồn gây ra và id người làm (khách là chủ đơn, admin lấy từ biến phiên do thủ tục đặt); không đổi trạng thái thì không ghi | CẤM XÓA CHÚ THÍCH NÀY
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
                USER(), CASE v_account
                            WHEN 'app_customer' THEN NEW.user_id
                            WHEN 'app_staff' THEN @bookstore_actor_id
                            ELSE NULL END);
    END IF;
END$$

DELIMITER ;


-- Phần 35: Thủ tục thanh toán mô phỏng
-- =====================================================================
-- Thanh toán mô phỏng (chốt 2026-11-16, tạm thời trước khi có cổng thật):
--   sp_payment_simulate        khách bấm "Thanh toán (mô phỏng)" cho đơn của mình
--   trg_payment_guard_update   giao dịch đã ghi không sửa được
--   trg_payment_guard_delete   giao dịch đã ghi không xóa được
--
-- Django chỉ cho gọi khi PAYMENT_SIMULATION=True trong .env. Khi có cổng thật,
-- thủ tục ghi nhận của cổng ghi vào cùng bảng payments_payment, đổi đơn sang
-- 'paid' theo đúng cách dưới đây; thủ tục này và quyền EXECUTE của nó bỏ đi.
--
-- Quy tắc:
--   - Chỉ chủ đơn, là khách hợp lệ (NOT_CUSTOMER như các thủ tục khác).
--   - Khóa dòng đơn FOR UPDATE rồi mới kiểm tra lại trạng thái và hạn: khách
--     bấm hai lần cùng lúc thì chỉ một lần thành công; khách bấm đúng lúc
--     Event hủy đơn quá hạn thì hai bên xếp hàng trên cùng dòng đơn – thủ tục
--     này chỉ nhận khi expires_at > lúc đó, Event chỉ hủy khi expires_at <=
--     lúc đó, nên không có đơn vừa "đã thanh toán" vừa "đã hủy".
--   - Số tiền ghi vào giao dịch lấy từ total của đơn trong CSDL, không nhận
--     từ ứng dụng. Mã giao dịch sinh ngẫu nhiên ngay trong CSDL.
--   - Ghi giao dịch và đổi đơn sang 'paid' trong cùng một giao dịch. Trigger
--     34_trg_orders_audit.sql tự ghi nhật ký đơn chuyển sang 'paid'.
--   - Lớp cuối: UNIQUE uq_payment_success_order (một đơn tối đa một giao dịch
--     thành công) và trigger 32 (chỉ pending → paid, paid_at ghi một lần).
--
-- Mã lỗi:
--   INVALID_INPUT, NOT_CUSTOMER
--   ORDER_NOT_FOUND     mã sai, không có, hoặc đơn của người khác (như nhau)
--   ORDER_ALREADY_PAID  đơn đã thanh toán (hoặc đã tiếp nhận, đóng gói, đang giao, đã giao)
--   ORDER_NOT_PAYABLE   đơn đã hủy
--   ORDER_EXPIRED       đơn còn chờ nhưng đã quá hạn thanh toán
--   PAYMENT_LOCKED      (trigger) sửa hoặc xóa giao dịch đã ghi
--
-- Root tạo bằng `python manage.py db_apply`. Chạy lại nhiều lần được.
-- =====================================================================

DROP PROCEDURE IF EXISTS sp_payment_simulate;
DROP TRIGGER IF EXISTS trg_payment_guard_update;
DROP TRIGGER IF EXISTS trg_payment_guard_delete;

DELIMITER $$

-- AI-TRACE#351 | Claude Opus 5.5 | Thủ tục thanh toán mô phỏng: khóa đơn của chính khách, kiểm tra lại trạng thái và hạn, ghi giao dịch 'simulated' với số tiền lấy từ đơn rồi đổi đơn sang paid trong một giao dịch | CẤM XÓA CHÚ THÍCH NÀY
CREATE DEFINER = 'bookstore_definer'@'localhost' PROCEDURE sp_payment_simulate(
    IN  p_user_id         BIGINT,
    IN  p_code            VARCHAR(64),
    IN  p_client_ip       VARCHAR(45),
    OUT p_transaction_id  VARCHAR(64)
)
SQL SECURITY DEFINER
MODIFIES SQL DATA
BEGIN
    DECLARE v_customer INT DEFAULT 0;
    DECLARE v_order_id BIGINT DEFAULT NULL;
    DECLARE v_status   VARCHAR(20) DEFAULT NULL;
    DECLARE v_expires  DATETIME(6) DEFAULT NULL;
    DECLARE v_total    INT UNSIGNED DEFAULT 0;
    DECLARE v_txn      VARCHAR(64) DEFAULT NULL;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    SET p_transaction_id = NULL;

    IF p_user_id IS NULL OR p_user_id <= 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'INVALID_INPUT';
    END IF;
    IF p_client_ip IS NOT NULL AND NOT REGEXP_LIKE(p_client_ip, '^[0-9A-Fa-f:.]{2,45}$', 'c') THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'INVALID_INPUT';
    END IF;

    SELECT COUNT(*) INTO v_customer
      FROM accounts_user
     WHERE id = p_user_id AND is_active = 1 AND is_staff = 0 AND email_verified = 1;
    IF v_customer = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'NOT_CUSTOMER';
    END IF;

    IF p_code IS NULL OR NOT REGEXP_LIKE(p_code, '^[0-9a-f]{32}$', 'c') THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ORDER_NOT_FOUND';
    END IF;

    START TRANSACTION;

    SELECT id, status, expires_at, total INTO v_order_id, v_status, v_expires, v_total
      FROM orders_order
     WHERE code = p_code AND user_id = p_user_id
       FOR UPDATE;
    IF v_order_id IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ORDER_NOT_FOUND';
    END IF;
    IF v_status IN ('paid', 'confirmed', 'packed', 'shipped', 'delivered') THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ORDER_ALREADY_PAID';
    END IF;
    IF v_status <> 'pending' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ORDER_NOT_PAYABLE';
    END IF;
    IF v_expires <= UTC_TIMESTAMP(6) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ORDER_EXPIRED';
    END IF;

    SET v_txn = CONCAT('SIM', UPPER(HEX(RANDOM_BYTES(12))));

    INSERT INTO payments_payment
        (order_id, provider, transaction_id, amount, status, signature_valid, failure_reason, raw_payload, client_ip)
    VALUES
        (v_order_id, 'simulated', v_txn, v_total, 'success', 0, NULL,
         JSON_OBJECT('mode', 'simulated', 'order_code', p_code), p_client_ip);

    UPDATE orders_order
       SET status = 'paid', paid_at = UTC_TIMESTAMP(6)
     WHERE id = v_order_id;

    COMMIT;
    SET p_transaction_id = v_txn;
END$$

-- AI-TRACE#352 | Claude Opus 5.5 | Trigger cấm sửa và xóa giao dịch thanh toán đã ghi, kể cả root và definer | CẤM XÓA CHÚ THÍCH NÀY
CREATE DEFINER = 'bookstore_definer'@'localhost'
TRIGGER trg_payment_guard_update
BEFORE UPDATE ON payments_payment
FOR EACH ROW
BEGIN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'PAYMENT_LOCKED';
END$$

CREATE DEFINER = 'bookstore_definer'@'localhost'
TRIGGER trg_payment_guard_delete
BEFORE DELETE ON payments_payment
FOR EACH ROW
BEGIN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'PAYMENT_LOCKED';
END$$

DELIMITER ;


-- Phần 36: Thủ tục đọc đơn hàng của khách
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


-- Phần 40: Thủ tục quản lý thể loại
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


-- Phần 41: Thủ tục quản lý sách
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


-- Phần 42: Thủ tục quản lý tài khoản khách
-- =====================================================================
-- Quản lý tài khoản khách cho admin (chốt 2026-11-16).
--   sp_staff_account_list    xem danh sách, lọc theo trạng thái và username
--                            (gộp 3 nhu cầu xem/lọc vào 1 thủ tục)
--   sp_staff_account_get     xem một tài khoản (trang xác nhận khóa/mở khóa)
--   sp_staff_account_lock    khóa tài khoản (is_active = 0), có lý do
--   sp_staff_account_unlock  mở khóa (is_active = 1), có lý do; cũng gỡ khóa tự động
--                            vì giữ kho (chốt 2026-11-20, khi bắt nhầm khách thật)
--
-- Chỉ r_staff được EXECUTE. Mỗi thủ tục tự kiểm tra p_actor_id là nhân viên
-- đang hoạt động (NOT_STAFF). Chỉ thao tác trên tài khoản KHÁCH (is_staff = 0):
-- tài khoản nhân viên, kể cả chính admin, coi như không tồn tại
-- (ACCOUNT_NOT_FOUND) nên admin không tự khóa mình được.
--
-- Trạng thái (ưu tiên từ trên xuống):
--   locked       is_active = 0                       → "Đã khóa"
--   auto_locked  auto_locked_until > lúc này: tự khóa 24 giờ vì bỏ 3 đơn chưa
--                thanh toán (33_order_cancel.sql)    → "Khóa tự động (giữ kho)"
--   temp_locked  axes ghi ≥ p_failure_limit lần sai trong p_cooloff_minutes
--                phút gần nhất                        → "Tạm khóa" (lý do xem log)
--   unverified   chưa xác nhận email                  → "Chưa xác nhận email"
--   active       còn lại                              → "Hoạt động"
-- Ngưỡng axes truyền từ Django (AXES_FAILURE_LIMIT, AXES_COOLOFF_TIME) để
-- không ghi cứng hai chỗ.
--
-- SĐT trả về là bản mã AES-GCM (Django giải mã, che bớt khi hiển thị). Không
-- trả password, is_superuser.
--
-- Khóa/mở khóa: khóa dòng user FOR UPDATE, ghi core_auditlog (cũ/mới + lý do)
-- trong cùng giao dịch. Trigger trg_user_guard_update (10_...) cho app_staff đổi
-- đúng cột is_active của khách, các cột khác vẫn bị chặn; app_staff không có
-- quyền UPDATE(is_active) trực tiếp nên chỉ hai thủ tục này đổi được.
-- Khóa xong, Django xóa mọi phiên của khách đó (dashboard.account_services.lock_account
-- → core.session_store.end_user_sessions; bảng phiên thuộc app_session nên không xóa ở đây).
-- Phòng hờ: core.middleware.InactiveAccountSessionMiddleware hủy phiên của tài khoản
-- is_active = 0 ở request kế tiếp, nên phiên cũ không sống lại khi mở khóa.
--
-- Mã lỗi: INVALID_INPUT, NOT_STAFF, ACCOUNT_NOT_FOUND, ALREADY_LOCKED, NOT_LOCKED
-- Root tạo bằng `python manage.py db_apply`. Chạy lại nhiều lần được.
-- =====================================================================

DROP PROCEDURE IF EXISTS sp_staff_account_list;
DROP PROCEDURE IF EXISTS sp_staff_account_get;
DROP PROCEDURE IF EXISTS sp_staff_account_lock;
DROP PROCEDURE IF EXISTS sp_staff_account_unlock;

DELIMITER $$

-- AI-TRACE#293 | Claude Opus 5.5 | Thủ tục admin xem tài khoản khách, lọc theo trạng thái (hoạt động/đã khóa/tạm khóa/chưa xác nhận) và username, SĐT trả bản mã | CẤM XÓA CHÚ THÍCH NÀY
CREATE DEFINER = 'bookstore_definer'@'localhost' PROCEDURE sp_staff_account_list(
    IN p_actor_id         BIGINT,
    IN p_status           VARCHAR(20),
    IN p_keyword          VARCHAR(255),
    IN p_failure_limit    INT,
    IN p_cooloff_minutes  INT
)
SQL SECURITY DEFINER
READS SQL DATA
BEGIN
    DECLARE v_staff   INT DEFAULT 0;
    DECLARE v_pattern VARCHAR(400) DEFAULT NULL;

    IF p_actor_id IS NULL OR p_actor_id <= 0
       OR (p_status IS NOT NULL AND p_status NOT IN ('active', 'locked', 'auto_locked', 'temp_locked', 'unverified'))
       OR (p_keyword IS NOT NULL AND CHAR_LENGTH(p_keyword) > 150)
       OR p_failure_limit IS NULL OR p_failure_limit < 1 OR p_failure_limit > 100
       OR p_cooloff_minutes IS NULL OR p_cooloff_minutes < 1 OR p_cooloff_minutes > 1440
    THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'INVALID_INPUT';
    END IF;

    SELECT COUNT(*) INTO v_staff
      FROM accounts_user
     WHERE id = p_actor_id AND is_staff = 1 AND is_active = 1;
    IF v_staff = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'NOT_STAFF';
    END IF;

    IF p_keyword IS NOT NULL AND CHAR_LENGTH(TRIM(p_keyword)) > 0 THEN
        SET v_pattern = CONCAT('%', REPLACE(REPLACE(REPLACE(TRIM(p_keyword), '\\', '\\\\'), '%', '\\%'), '_', '\\_'), '%');
    END IF;

    SELECT id, username, email, phone_encrypted, status, date_joined, last_login
      FROM (
        SELECT u.id, u.username, u.email, u.phone_encrypted, u.date_joined, u.last_login,
               CASE
                   WHEN u.is_active = 0 THEN 'locked'
                   WHEN u.auto_locked_until > UTC_TIMESTAMP(6) THEN 'auto_locked'
                   WHEN EXISTS (
                        SELECT 1 FROM axes_accessattempt a
                         WHERE a.username = u.username
                           AND a.failures_since_start >= p_failure_limit
                           AND a.attempt_time > UTC_TIMESTAMP(6) - INTERVAL p_cooloff_minutes MINUTE
                   ) THEN 'temp_locked'
                   WHEN u.email_verified = 0 THEN 'unverified'
                   ELSE 'active'
               END AS status
          FROM accounts_user u
         WHERE u.is_staff = 0
           AND (v_pattern IS NULL OR u.username LIKE v_pattern)
      ) t
     WHERE p_status IS NULL OR t.status = p_status
     ORDER BY date_joined DESC, id DESC
     LIMIT 200;
END$$

-- AI-TRACE#294 | Claude Opus 5.5 | Thủ tục admin xem một tài khoản khách theo id (cùng cột và trạng thái như danh sách), tài khoản nhân viên coi như không có | CẤM XÓA CHÚ THÍCH NÀY
CREATE DEFINER = 'bookstore_definer'@'localhost' PROCEDURE sp_staff_account_get(
    IN p_actor_id         BIGINT,
    IN p_user_id          BIGINT,
    IN p_failure_limit    INT,
    IN p_cooloff_minutes  INT
)
SQL SECURITY DEFINER
READS SQL DATA
BEGIN
    DECLARE v_staff INT DEFAULT 0;
    DECLARE v_found INT DEFAULT 0;

    IF p_actor_id IS NULL OR p_actor_id <= 0 OR p_user_id IS NULL OR p_user_id <= 0
       OR p_failure_limit IS NULL OR p_failure_limit < 1 OR p_failure_limit > 100
       OR p_cooloff_minutes IS NULL OR p_cooloff_minutes < 1 OR p_cooloff_minutes > 1440
    THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'INVALID_INPUT';
    END IF;

    SELECT COUNT(*) INTO v_staff
      FROM accounts_user
     WHERE id = p_actor_id AND is_staff = 1 AND is_active = 1;
    IF v_staff = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'NOT_STAFF';
    END IF;

    SELECT COUNT(*) INTO v_found FROM accounts_user WHERE id = p_user_id AND is_staff = 0;
    IF v_found = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ACCOUNT_NOT_FOUND';
    END IF;

    SELECT u.id, u.username, u.email, u.phone_encrypted,
           CASE
               WHEN u.is_active = 0 THEN 'locked'
               WHEN u.auto_locked_until > UTC_TIMESTAMP(6) THEN 'auto_locked'
               WHEN EXISTS (
                    SELECT 1 FROM axes_accessattempt a
                     WHERE a.username = u.username
                       AND a.failures_since_start >= p_failure_limit
                       AND a.attempt_time > UTC_TIMESTAMP(6) - INTERVAL p_cooloff_minutes MINUTE
               ) THEN 'temp_locked'
               WHEN u.email_verified = 0 THEN 'unverified'
               ELSE 'active'
           END AS status,
           u.date_joined, u.last_login
      FROM accounts_user u
     WHERE u.id = p_user_id AND u.is_staff = 0;
END$$

-- AI-TRACE#295 | Claude Opus 5.5 | Thủ tục admin khóa tài khoản khách: kiểm tra lý do, khóa dòng, đặt is_active = 0, ghi core_auditlog kèm lý do cùng giao dịch | CẤM XÓA CHÚ THÍCH NÀY
CREATE DEFINER = 'bookstore_definer'@'localhost' PROCEDURE sp_staff_account_lock(
    IN p_actor_id  BIGINT,
    IN p_user_id   BIGINT,
    IN p_reason    VARCHAR(500)
)
SQL SECURITY DEFINER
MODIFIES SQL DATA
BEGIN
    DECLARE v_staff  INT DEFAULT 0;
    DECLARE v_active TINYINT DEFAULT NULL;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    IF p_actor_id IS NULL OR p_actor_id <= 0 OR p_user_id IS NULL OR p_user_id <= 0
       OR p_reason IS NULL OR CHAR_LENGTH(TRIM(p_reason)) < 5 OR CHAR_LENGTH(p_reason) > 255
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

    SELECT is_active INTO v_active
      FROM accounts_user
     WHERE id = p_user_id AND is_staff = 0
       FOR UPDATE;
    IF v_active IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ACCOUNT_NOT_FOUND';
    END IF;
    IF v_active = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ALREADY_LOCKED';
    END IF;

    UPDATE accounts_user SET is_active = 0 WHERE id = p_user_id;

    INSERT INTO core_auditlog (table_name, record_id, action, old_value, new_value, db_user, app_user_id)
    VALUES ('accounts_user', p_user_id, 'UPDATE',
            JSON_OBJECT('is_active', 1),
            JSON_OBJECT('is_active', 0, 'reason', TRIM(p_reason)),
            USER(), p_actor_id);

    COMMIT;
END$$

-- AI-TRACE#296 | Claude Opus 5.5 | Thủ tục admin mở khóa tài khoản khách: kiểm tra lý do, khóa dòng, đặt is_active = 1, ghi core_auditlog kèm lý do cùng giao dịch | CẤM XÓA CHÚ THÍCH NÀY | đã viết lại bởi Claude Opus 5.5 khi gỡ được cả khóa tự động vì giữ kho
CREATE DEFINER = 'bookstore_definer'@'localhost' PROCEDURE sp_staff_account_unlock(
    IN p_actor_id  BIGINT,
    IN p_user_id   BIGINT,
    IN p_reason    VARCHAR(500)
)
SQL SECURITY DEFINER
MODIFIES SQL DATA
BEGIN
    DECLARE v_staff  INT DEFAULT 0;
    DECLARE v_active TINYINT DEFAULT NULL;
    DECLARE v_until  DATETIME(6) DEFAULT NULL;
    DECLARE v_now    DATETIME(6);
    DECLARE v_auto   TINYINT DEFAULT 0;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    IF p_actor_id IS NULL OR p_actor_id <= 0 OR p_user_id IS NULL OR p_user_id <= 0
       OR p_reason IS NULL OR CHAR_LENGTH(TRIM(p_reason)) < 5 OR CHAR_LENGTH(p_reason) > 255
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
    SET v_now = UTC_TIMESTAMP(6);

    SELECT is_active, auto_locked_until INTO v_active, v_until
      FROM accounts_user
     WHERE id = p_user_id AND is_staff = 0
       FOR UPDATE;
    IF v_active IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ACCOUNT_NOT_FOUND';
    END IF;
    SET v_auto = (v_until IS NOT NULL AND v_until > v_now);
    IF v_active = 1 AND v_auto = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'NOT_LOCKED';
    END IF;

    -- Gỡ khóa tự động: đặt auto_locked_until = lúc này (không để NULL) để
    -- sp_order_hold_check chỉ đếm đơn bỏ SAU lần mở khóa này, khách không bị
    -- khóa lại ngay ở lần hủy kế tiếp.
    UPDATE accounts_user
       SET is_active = 1,
           auto_locked_until = IF(v_auto = 1, v_now, auto_locked_until)
     WHERE id = p_user_id;

    INSERT INTO core_auditlog (table_name, record_id, action, old_value, new_value, db_user, app_user_id)
    VALUES ('accounts_user', p_user_id, 'UPDATE',
            JSON_OBJECT('is_active', v_active, 'auto_locked_until', v_until),
            JSON_OBJECT('is_active', 1, 'auto_locked_until', IF(v_auto = 1, v_now, v_until),
                        'reason', TRIM(p_reason)),
            USER(), p_actor_id);

    COMMIT;
END$$

DELIMITER ;


-- Phần 43: Thủ tục nhật ký hệ thống và Event xóa log cũ
-- =====================================================================
-- Nhật ký hệ thống cho admin (chốt 2026-11-16).
--   sp_staff_security_events  đọc core_securityevent (nhật ký bảo mật)
--   sp_staff_audit_log        đọc core_auditlog (nhật ký thay đổi dữ liệu)
--   sp_purge_old_logs         xóa log cũ hơn 1 năm (chỉ Event gọi)
--   ev_purge_old_logs         Event mỗi ngày gọi sp_purge_old_logs
--
-- Hai thủ tục đọc chỉ r_staff được EXECUTE, tự kiểm tra p_actor_id là nhân
-- viên (NOT_STAFF). Trả 2 bộ kết quả: (1) tổng số dòng khớp bộ lọc, (2) một
-- trang dữ liệu mới nhất trước. Mọi bộ lọc đều tùy chọn (NULL = không lọc).
-- Giới hạn: mỗi trang 1–100 dòng, offset tối đa 100000, khoảng ngày tối đa
-- 400 ngày; từ khóa tìm kiếm thoát \ % _ (LIKE).
--
-- Không khóa cứng log (chốt): tài khoản ứng dụng chỉ có INSERT trên 2 bảng log
-- như trước; chỉ definer có DELETE, dùng trong sp_purge_old_logs. Xóa theo lô
-- 5000 dòng để không giữ khóa lâu.
--
-- Mã lỗi: INVALID_INPUT, NOT_STAFF.
-- Root tạo bằng `python manage.py db_apply`. Chạy lại nhiều lần được.
-- =====================================================================

DROP EVENT IF EXISTS ev_purge_old_logs;
DROP PROCEDURE IF EXISTS sp_staff_security_events;
DROP PROCEDURE IF EXISTS sp_staff_audit_log;
DROP PROCEDURE IF EXISTS sp_purge_old_logs;

DELIMITER $$

-- AI-TRACE#322 | Claude Opus 5.5 | Thủ tục admin đọc nhật ký bảo mật: lọc loại, mức độ, khoảng ngày, username/IP; trả tổng số và một trang mới nhất trước | CẤM XÓA CHÚ THÍCH NÀY
CREATE DEFINER = 'bookstore_definer'@'localhost' PROCEDURE sp_staff_security_events(
    IN p_actor_id    BIGINT,
    IN p_event_type  VARCHAR(40),
    IN p_severity    VARCHAR(10),
    IN p_from        DATETIME(6),
    IN p_to          DATETIME(6),
    IN p_keyword     VARCHAR(255),
    IN p_offset      INT,
    IN p_limit       INT
)
SQL SECURITY DEFINER
READS SQL DATA
BEGIN
    DECLARE v_staff   INT DEFAULT 0;
    DECLARE v_pattern VARCHAR(400) DEFAULT NULL;

    IF p_actor_id IS NULL OR p_actor_id <= 0
       OR (p_event_type IS NOT NULL AND NOT REGEXP_LIKE(p_event_type, '^[a-z_]{1,40}$', 'c'))
       OR (p_severity IS NOT NULL AND p_severity NOT IN ('info', 'warning', 'critical'))
       OR (p_from IS NOT NULL AND p_to IS NOT NULL AND (p_from > p_to OR p_to > p_from + INTERVAL 400 DAY))
       OR (p_keyword IS NOT NULL AND CHAR_LENGTH(p_keyword) > 150)
       OR p_offset IS NULL OR p_offset < 0 OR p_offset > 100000
       OR p_limit IS NULL OR p_limit < 1 OR p_limit > 100
    THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'INVALID_INPUT';
    END IF;

    SELECT COUNT(*) INTO v_staff
      FROM accounts_user
     WHERE id = p_actor_id AND is_staff = 1 AND is_active = 1;
    IF v_staff = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'NOT_STAFF';
    END IF;

    IF p_keyword IS NOT NULL AND CHAR_LENGTH(TRIM(p_keyword)) > 0 THEN
        SET v_pattern = CONCAT('%', REPLACE(REPLACE(REPLACE(TRIM(p_keyword), '\\', '\\\\'), '%', '\\%'), '_', '\\_'), '%');
    END IF;

    SELECT COUNT(*)
      FROM core_securityevent e
      LEFT JOIN accounts_user u ON u.id = e.user_id
     WHERE (p_event_type IS NULL OR e.event_type = p_event_type)
       AND (p_severity IS NULL OR e.severity = p_severity)
       AND (p_from IS NULL OR e.created_at >= p_from)
       AND (p_to IS NULL OR e.created_at < p_to)
       AND (v_pattern IS NULL OR e.username_attempted LIKE v_pattern OR u.username LIKE v_pattern
            OR e.ip_address LIKE v_pattern);

    SELECT e.id, e.created_at, e.event_type, e.severity, e.user_id, u.username, e.username_attempted,
           e.ip_address, e.method, e.path, e.user_agent, e.detail
      FROM core_securityevent e
      LEFT JOIN accounts_user u ON u.id = e.user_id
     WHERE (p_event_type IS NULL OR e.event_type = p_event_type)
       AND (p_severity IS NULL OR e.severity = p_severity)
       AND (p_from IS NULL OR e.created_at >= p_from)
       AND (p_to IS NULL OR e.created_at < p_to)
       AND (v_pattern IS NULL OR e.username_attempted LIKE v_pattern OR u.username LIKE v_pattern
            OR e.ip_address LIKE v_pattern)
     ORDER BY e.created_at DESC, e.id DESC
     LIMIT p_offset, p_limit;
END$$

-- AI-TRACE#323 | Claude Opus 5.5 | Thủ tục admin đọc nhật ký thay đổi dữ liệu: lọc bảng, hành động, khoảng ngày, id bản ghi; kèm username người thực hiện | CẤM XÓA CHÚ THÍCH NÀY
CREATE DEFINER = 'bookstore_definer'@'localhost' PROCEDURE sp_staff_audit_log(
    IN p_actor_id   BIGINT,
    IN p_table      VARCHAR(64),
    IN p_action     VARCHAR(10),
    IN p_from       DATETIME(6),
    IN p_to         DATETIME(6),
    IN p_record_id  BIGINT,
    IN p_offset     INT,
    IN p_limit      INT
)
SQL SECURITY DEFINER
READS SQL DATA
BEGIN
    DECLARE v_staff INT DEFAULT 0;

    IF p_actor_id IS NULL OR p_actor_id <= 0
       OR (p_table IS NOT NULL AND NOT REGEXP_LIKE(p_table, '^[a-z_]{1,64}$', 'c'))
       OR (p_action IS NOT NULL AND p_action NOT IN ('INSERT', 'UPDATE', 'DELETE'))
       OR (p_from IS NOT NULL AND p_to IS NOT NULL AND (p_from > p_to OR p_to > p_from + INTERVAL 400 DAY))
       OR (p_record_id IS NOT NULL AND p_record_id <= 0)
       OR p_offset IS NULL OR p_offset < 0 OR p_offset > 100000
       OR p_limit IS NULL OR p_limit < 1 OR p_limit > 100
    THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'INVALID_INPUT';
    END IF;

    SELECT COUNT(*) INTO v_staff
      FROM accounts_user
     WHERE id = p_actor_id AND is_staff = 1 AND is_active = 1;
    IF v_staff = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'NOT_STAFF';
    END IF;

    SELECT COUNT(*)
      FROM core_auditlog a
     WHERE (p_table IS NULL OR a.table_name = p_table)
       AND (p_action IS NULL OR a.action = p_action)
       AND (p_from IS NULL OR a.created_at >= p_from)
       AND (p_to IS NULL OR a.created_at < p_to)
       AND (p_record_id IS NULL OR a.record_id = p_record_id);

    SELECT a.id, a.created_at, a.table_name, a.record_id, a.action, a.old_value, a.new_value,
           a.db_user, a.app_user_id, u.username
      FROM core_auditlog a
      LEFT JOIN accounts_user u ON u.id = a.app_user_id
     WHERE (p_table IS NULL OR a.table_name = p_table)
       AND (p_action IS NULL OR a.action = p_action)
       AND (p_from IS NULL OR a.created_at >= p_from)
       AND (p_to IS NULL OR a.created_at < p_to)
       AND (p_record_id IS NULL OR a.record_id = p_record_id)
     ORDER BY a.created_at DESC, a.id DESC
     LIMIT p_offset, p_limit;
END$$

-- AI-TRACE#324 | Claude Opus 5.5 | Thủ tục xóa nhật ký bảo mật và nhật ký thay đổi cũ hơn 1 năm, theo lô 5000 dòng, tối đa 40 lô mỗi lần chạy | CẤM XÓA CHÚ THÍCH NÀY
CREATE DEFINER = 'bookstore_definer'@'localhost' PROCEDURE sp_purge_old_logs(
    OUT p_deleted INT
)
SQL SECURITY DEFINER
MODIFIES SQL DATA
BEGIN
    DECLARE v_cutoff DATETIME(6) DEFAULT UTC_TIMESTAMP(6) - INTERVAL 1 YEAR;
    DECLARE v_batch  INT DEFAULT 0;
    DECLARE v_rounds INT DEFAULT 0;

    SET p_deleted = 0;

    purge_security: LOOP
        DELETE FROM core_securityevent WHERE created_at < v_cutoff ORDER BY created_at LIMIT 5000;
        SET v_batch = ROW_COUNT();
        SET p_deleted = p_deleted + v_batch;
        SET v_rounds = v_rounds + 1;
        IF v_batch < 5000 OR v_rounds >= 40 THEN
            LEAVE purge_security;
        END IF;
    END LOOP;

    SET v_rounds = 0;
    purge_audit: LOOP
        DELETE FROM core_auditlog WHERE created_at < v_cutoff ORDER BY created_at LIMIT 5000;
        SET v_batch = ROW_COUNT();
        SET p_deleted = p_deleted + v_batch;
        SET v_rounds = v_rounds + 1;
        IF v_batch < 5000 OR v_rounds >= 40 THEN
            LEAVE purge_audit;
        END IF;
    END LOOP;
END$$

-- AI-TRACE#325 | Claude Opus 5.5 | MySQL Event mỗi ngày (03:00 giờ Việt Nam) gọi sp_purge_old_logs để giữ nhật ký tối đa 1 năm | CẤM XÓA CHÚ THÍCH NÀY
CREATE DEFINER = 'bookstore_definer'@'localhost' EVENT ev_purge_old_logs
    ON SCHEDULE EVERY 1 DAY
    STARTS (TIMESTAMP(UTC_DATE()) + INTERVAL 20 HOUR)
    ON COMPLETION PRESERVE
    ENABLE
    COMMENT 'Xóa nhật ký bảo mật và nhật ký thay đổi cũ hơn 1 năm'
    DO
    BEGIN
        DECLARE v_deleted INT DEFAULT 0;
        CALL sp_purge_old_logs(v_deleted);
    END$$

DELIMITER ;


-- Phần 44: Thủ tục quản lý đơn hàng của admin
-- =====================================================================
-- Quản lý đơn hàng của admin (chốt 2026-11-16):
--   sp_staff_order_list     danh sách đơn đơn giản, lọc theo trạng thái
--   sp_staff_order_get      chi tiết một đơn (sách, thông tin giao hàng bản mã,
--                           giao dịch thanh toán) – Django bắt xác thực lại + ghi log
--   sp_staff_order_confirm  Đã thanh toán → Đã tiếp nhận
--   sp_staff_order_pack     Đã tiếp nhận  → Đã đóng gói
--   sp_staff_order_ship     Đã đóng gói   → Đang giao
--   sp_staff_order_deliver  Đang giao     → Đã giao
--   sp_staff_order_advance  thủ tục nội bộ dùng chung cho 4 thủ tục trên
--                           (không cấp cho tài khoản ứng dụng nào)
--
-- Chỉ r_staff được EXECUTE các thủ tục công khai. Mỗi thủ tục tự kiểm tra
-- p_actor_id là nhân viên đang hoạt động (NOT_STAFF).
--
-- Chuyển trạng thái: buộc theo luồng, không có quay lại. Mỗi thủ tục chỉ nhận
-- đúng MỘT trạng thái trước; khóa dòng đơn FOR UPDATE rồi mới kiểm tra, nên
-- hai tab cùng bấm hoặc bấm hai lần thì lần sau báo ORDER_WRONG_STATUS, không
-- nhảy cóc. Trigger 32_trg_orders_guard.sql là lớp cuối (chặn cả root).
-- Nhật ký: trigger 34_trg_orders_audit.sql tự ghi (nguồn "Quản trị"); thủ tục
-- đặt biến phiên @bookstore_actor_id để trigger ghi đúng id người bấm, rồi xóa
-- ngay sau khi cập nhật.
--
-- Mã lỗi: INVALID_INPUT, NOT_STAFF, ORDER_NOT_FOUND, ORDER_WRONG_STATUS
-- Root tạo bằng `python manage.py db_apply`. Chạy lại nhiều lần được.
-- =====================================================================

DROP PROCEDURE IF EXISTS sp_staff_order_list;
DROP PROCEDURE IF EXISTS sp_staff_order_get;
DROP PROCEDURE IF EXISTS sp_staff_order_advance;
DROP PROCEDURE IF EXISTS sp_staff_order_confirm;
DROP PROCEDURE IF EXISTS sp_staff_order_pack;
DROP PROCEDURE IF EXISTS sp_staff_order_ship;
DROP PROCEDURE IF EXISTS sp_staff_order_deliver;

DELIMITER $$

-- AI-TRACE#372 | Claude Opus 5.5 | Thủ tục admin xem danh sách đơn (mã, username, trạng thái, tổng tiền, ngày đặt, số cuốn), lọc theo trạng thái hoặc nhóm Cần xử lý, trả tổng số và một trang; không trả thông tin giao hàng | CẤM XÓA CHÚ THÍCH NÀY
CREATE DEFINER = 'bookstore_definer'@'localhost' PROCEDURE sp_staff_order_list(
    IN p_actor_id  BIGINT,
    IN p_status    VARCHAR(20),
    IN p_offset    INT,
    IN p_limit     INT
)
SQL SECURITY DEFINER
READS SQL DATA
BEGIN
    DECLARE v_staff INT DEFAULT 0;

    IF p_actor_id IS NULL OR p_actor_id <= 0
       OR (p_status IS NOT NULL AND p_status NOT IN
           ('todo', 'pending', 'paid', 'confirmed', 'packed', 'shipped', 'delivered', 'cancelled'))
       OR p_offset IS NULL OR p_offset < 0 OR p_offset > 100000
       OR p_limit IS NULL OR p_limit < 1 OR p_limit > 100 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'INVALID_INPUT';
    END IF;

    SELECT COUNT(*) INTO v_staff
      FROM accounts_user
     WHERE id = p_actor_id AND is_staff = 1 AND is_active = 1;
    IF v_staff = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'NOT_STAFF';
    END IF;

    SELECT COUNT(*)
      FROM orders_order o
     WHERE p_status IS NULL
        OR (p_status = 'todo' AND o.status IN ('paid', 'confirmed', 'packed', 'shipped'))
        OR o.status = p_status;

    SELECT o.code, u.username, o.status, o.total, o.created_at, o.expires_at, o.paid_at,
           (SELECT COALESCE(SUM(i.quantity), 0) FROM orders_orderitem i WHERE i.order_id = o.id) AS item_count
      FROM orders_order o
      JOIN accounts_user u ON u.id = o.user_id
     WHERE p_status IS NULL
        OR (p_status = 'todo' AND o.status IN ('paid', 'confirmed', 'packed', 'shipped'))
        OR o.status = p_status
     ORDER BY o.created_at DESC, o.id DESC
     LIMIT p_offset, p_limit;
END$$

-- AI-TRACE#373 | Claude Opus 5.5 | Thủ tục admin đọc chi tiết một đơn: thông tin đơn, người đặt, SĐT/địa chỉ giao hàng bản mã (Django giải mã), giao dịch thanh toán thành công và danh sách sách | CẤM XÓA CHÚ THÍCH NÀY
CREATE DEFINER = 'bookstore_definer'@'localhost' PROCEDURE sp_staff_order_get(
    IN p_actor_id  BIGINT,
    IN p_code      VARCHAR(64)
)
SQL SECURITY DEFINER
READS SQL DATA
BEGIN
    DECLARE v_staff    INT DEFAULT 0;
    DECLARE v_order_id BIGINT DEFAULT NULL;

    IF p_actor_id IS NULL OR p_actor_id <= 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'INVALID_INPUT';
    END IF;

    SELECT COUNT(*) INTO v_staff
      FROM accounts_user
     WHERE id = p_actor_id AND is_staff = 1 AND is_active = 1;
    IF v_staff = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'NOT_STAFF';
    END IF;

    IF p_code IS NULL OR NOT REGEXP_LIKE(p_code, '^[0-9a-f]{32}$', 'c') THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ORDER_NOT_FOUND';
    END IF;

    SELECT id INTO v_order_id FROM orders_order WHERE code = p_code;
    IF v_order_id IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ORDER_NOT_FOUND';
    END IF;

    SELECT o.code, o.user_id, u.username, o.status, o.subtotal, o.shipping_fee, o.total, o.shipping_name,
           o.shipping_phone_encrypted, o.shipping_address_encrypted, o.idempotency_key,
           o.created_at, o.expires_at, o.paid_at, o.cancelled_at,
           p.provider, p.transaction_id
      FROM orders_order o
      JOIN accounts_user u ON u.id = o.user_id
      LEFT JOIN payments_payment p ON p.success_order_id = o.id
     WHERE o.id = v_order_id;

    SELECT book_id, book_title, unit_price, quantity
      FROM orders_orderitem
     WHERE order_id = v_order_id
     ORDER BY id;
END$$

-- AI-TRACE#374 | Claude Opus 5.5 | Thủ tục nội bộ chuyển đơn đúng một bước: kiểm tra nhân viên, khóa dòng đơn, chỉ nhận đúng trạng thái trước, đặt id người bấm cho trigger nhật ký | CẤM XÓA CHÚ THÍCH NÀY
CREATE DEFINER = 'bookstore_definer'@'localhost' PROCEDURE sp_staff_order_advance(
    IN p_actor_id  BIGINT,
    IN p_code      VARCHAR(64),
    IN p_from      VARCHAR(20),
    IN p_to        VARCHAR(20)
)
SQL SECURITY DEFINER
MODIFIES SQL DATA
BEGIN
    DECLARE v_staff    INT DEFAULT 0;
    DECLARE v_order_id BIGINT DEFAULT NULL;
    DECLARE v_status   VARCHAR(20) DEFAULT NULL;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET @bookstore_actor_id = NULL;
        ROLLBACK;
        RESIGNAL;
    END;

    IF p_actor_id IS NULL OR p_actor_id <= 0
       OR NOT ((p_from = 'paid' AND p_to = 'confirmed')
            OR (p_from = 'confirmed' AND p_to = 'packed')
            OR (p_from = 'packed' AND p_to = 'shipped')
            OR (p_from = 'shipped' AND p_to = 'delivered')) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'INVALID_INPUT';
    END IF;

    SELECT COUNT(*) INTO v_staff
      FROM accounts_user
     WHERE id = p_actor_id AND is_staff = 1 AND is_active = 1;
    IF v_staff = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'NOT_STAFF';
    END IF;

    IF p_code IS NULL OR NOT REGEXP_LIKE(p_code, '^[0-9a-f]{32}$', 'c') THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ORDER_NOT_FOUND';
    END IF;

    START TRANSACTION;

    SELECT id, status INTO v_order_id, v_status
      FROM orders_order
     WHERE code = p_code
       FOR UPDATE;
    IF v_order_id IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ORDER_NOT_FOUND';
    END IF;
    IF v_status <> p_from THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ORDER_WRONG_STATUS';
    END IF;

    SET @bookstore_actor_id = p_actor_id;
    UPDATE orders_order SET status = p_to WHERE id = v_order_id;
    SET @bookstore_actor_id = NULL;

    COMMIT;
END$$

-- AI-TRACE#375 | Claude Opus 5.5 | Bốn thủ tục admin chuyển trạng thái đơn theo đúng luồng: tiếp nhận, đóng gói, giao hàng, đã giao; mỗi thủ tục cố định trạng thái trước và sau | CẤM XÓA CHÚ THÍCH NÀY
CREATE DEFINER = 'bookstore_definer'@'localhost' PROCEDURE sp_staff_order_confirm(
    IN p_actor_id  BIGINT,
    IN p_code      VARCHAR(64)
)
SQL SECURITY DEFINER
MODIFIES SQL DATA
BEGIN
    CALL sp_staff_order_advance(p_actor_id, p_code, 'paid', 'confirmed');
END$$

CREATE DEFINER = 'bookstore_definer'@'localhost' PROCEDURE sp_staff_order_pack(
    IN p_actor_id  BIGINT,
    IN p_code      VARCHAR(64)
)
SQL SECURITY DEFINER
MODIFIES SQL DATA
BEGIN
    CALL sp_staff_order_advance(p_actor_id, p_code, 'confirmed', 'packed');
END$$

CREATE DEFINER = 'bookstore_definer'@'localhost' PROCEDURE sp_staff_order_ship(
    IN p_actor_id  BIGINT,
    IN p_code      VARCHAR(64)
)
SQL SECURITY DEFINER
MODIFIES SQL DATA
BEGIN
    CALL sp_staff_order_advance(p_actor_id, p_code, 'packed', 'shipped');
END$$

CREATE DEFINER = 'bookstore_definer'@'localhost' PROCEDURE sp_staff_order_deliver(
    IN p_actor_id  BIGINT,
    IN p_code      VARCHAR(64)
)
SQL SECURITY DEFINER
MODIFIES SQL DATA
BEGIN
    CALL sp_staff_order_advance(p_actor_id, p_code, 'shipped', 'delivered');
END$$

DELIMITER ;


-- Phần 45: Thủ tục trang Tổng quan
-- =====================================================================
-- Trang Tổng quan của admin – báo cáo cơ bản (chốt 2026-11-16):
--   sp_staff_dashboard_orders    đơn cần xử lý theo từng bước, đơn mới/hủy hôm
--                                nay, doanh thu hôm nay / 7 ngày / tháng này
--   sp_staff_dashboard_stock     số sách sắp hết, hết hàng, 5 cuốn còn ít nhất
--   sp_staff_dashboard_security  sự kiện cảnh báo/nghiêm trọng 24 giờ, đăng nhập
--                                sai hôm nay
--   sp_staff_dashboard_backup    lần sao lưu thành công, lỗi, kiểm tra khôi phục
--                                gần nhất (đọc từ nhật ký do lệnh sao lưu ghi)
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
DROP PROCEDURE IF EXISTS sp_staff_dashboard_backup;

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

-- AI-TRACE#573 | Claude Opus 5.5 | Thủ tục trạng thái sao lưu cho trang Tổng quan: bản ghi gần nhất của sao lưu thành công, sao lưu lỗi và kiểm tra khôi phục (thời điểm + chi tiết JSON không chứa bí mật) | CẤM XÓA CHÚ THÍCH NÀY
CREATE DEFINER = 'bookstore_definer'@'localhost' PROCEDURE sp_staff_dashboard_backup(
    IN p_actor_id  BIGINT
)
SQL SECURITY DEFINER
READS SQL DATA
BEGIN
    DECLARE v_staff INT DEFAULT 0;

    IF p_actor_id IS NULL OR p_actor_id <= 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'INVALID_INPUT';
    END IF;

    SELECT COUNT(*) INTO v_staff
      FROM accounts_user
     WHERE id = p_actor_id AND is_staff = 1 AND is_active = 1;
    IF v_staff = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'NOT_STAFF';
    END IF;

    SELECT e.event_type, e.created_at, e.detail
      FROM core_securityevent e
      JOIN (SELECT event_type, MAX(id) AS id
              FROM core_securityevent
             WHERE event_type IN ('backup_created', 'backup_failed', 'restore_verified')
             GROUP BY event_type) latest ON latest.id = e.id;
END$$

DELIMITER ;


-- Phần 46: Thủ tục đếm đăng nhập sai theo IP
-- =====================================================================
-- Chặn dò mật khẩu rải từ một IP (password spraying) – báo cáo rà soát T3.2,
-- chốt 2026-11-20.
--
-- django-axes chỉ khóa theo cặp (tên đăng nhập, IP): một IP thử vài mật khẩu
-- trên rất nhiều tài khoản thì không cặp nào chạm ngưỡng. Thủ tục này đếm số
-- lần đăng nhập sai (core_securityevent 'login_failed') của MỘT IP, gộp mọi
-- tài khoản, trong p_minutes phút gần nhất; Django so với ngưỡng
-- (LOGIN_IP_FAILURE_LIMIT) và từ chối đăng nhập từ IP đó (429).
--
-- Đếm từ bảng nhật ký (bền, không mất khi khởi động lại) chứ không từ bảng axes
-- (axes xóa bản ghi sau 15 phút, không đủ cửa sổ 60 phút) hay cache.
-- r_customer chỉ có EXECUTE: thủ tục trả đúng một con số, tài khoản ứng dụng
-- vẫn không đọc được nội dung nhật ký.
--
-- Mã lỗi: INVALID_INPUT
-- Root tạo bằng `python manage.py db_apply`. Chạy lại nhiều lần được.
-- =====================================================================

DROP PROCEDURE IF EXISTS sp_login_ip_failures;

DELIMITER $$

-- AI-TRACE#544 | Claude Opus 5.5 | Thủ tục đọc đếm số lần đăng nhập sai của một IP (mọi tài khoản) trong N phút gần nhất, chỉ trả một con số | CẤM XÓA CHÚ THÍCH NÀY
CREATE DEFINER = 'bookstore_definer'@'localhost' PROCEDURE sp_login_ip_failures(
    IN p_ip_address  VARCHAR(45),
    IN p_minutes     INT
)
SQL SECURITY DEFINER
READS SQL DATA
BEGIN
    IF p_ip_address IS NULL OR CHAR_LENGTH(p_ip_address) = 0 OR CHAR_LENGTH(p_ip_address) > 45
       OR p_minutes IS NULL OR p_minutes < 1 OR p_minutes > 1440
    THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'INVALID_INPUT';
    END IF;

    SELECT COUNT(*) AS failures
      FROM core_securityevent
     WHERE created_at >= UTC_TIMESTAMP(6) - INTERVAL p_minutes MINUTE
       AND event_type = 'login_failed'
       AND ip_address = p_ip_address;
END$$

DELIMITER ;
