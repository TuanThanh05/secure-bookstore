-- =====================================================================
-- Ghi lịch sử mật khẩu (bảng accounts_passwordhistory, schema/01_tables.sql).
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
