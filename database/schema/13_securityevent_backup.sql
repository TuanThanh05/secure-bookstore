-- =====================================================================
-- Lược đồ v1.12 (2026-11-21): loại sự kiện cho sao lưu / khôi phục CSDL
-- (dựng lại gói sao lưu tạm gác ngày 2026-11-19, xem docs/sao-luu-csdl.md).
-- Migration core/0014 đọc file này. Giữ nguyên toàn bộ danh sách của
-- 12_securityevent_order_hold.sql, thêm 5 loại cuối.
-- Lệnh sao lưu chạy trên máy chủ (manage.py), ghi log với ip_address = 'cli'.
-- =====================================================================

-- AI-TRACE#555 | Claude Opus 5.5 | Mở rộng CHECK loại sự kiện bảo mật thêm 5 loại cho sao lưu, xuất file .sql, khôi phục và kiểm tra khôi phục | CẤM XÓA CHÚ THÍCH NÀY
ALTER TABLE core_securityevent DROP CHECK ck_secevent_type;

ALTER TABLE core_securityevent ADD CONSTRAINT ck_secevent_type CHECK (event_type IN (
    'login_success',
    'login_failed',
    'account_locked',
    'logout',
    'password_changed',
    'password_reset_requested',
    'otp_failed',
    'access_denied',
    'idor_attempt',
    'db_permission_denied',
    'payment_signature_invalid',
    'payment_replay',
    'payment_amount_mismatch',
    'upload_rejected',
    'rate_limited',
    'csrf_failed',
    'invalid_input',
    'register_success',          -- tạo tài khoản xong ở bước 2
    'register_existing_email',   -- bước 1 nhập email đã có tài khoản (gửi thư báo, không gửi link)
    'register_link_invalid',     -- link đăng ký sai, hết hạn, đã dùng, hoặc phiên đăng ký hết hạn (detail.reason)
    'captcha_failed',            -- Cloudflare Turnstile không đạt: thiếu token, bị từ chối, sai hostname/action, Siteverify lỗi (detail.reason, detail.codes)
    'email_sent',
    'email_send_failed',
    'sensitive_data_viewed',
    'profile_updated',
    'two_factor_enabled',        -- khách bật / admin cài 2 bước (detail.via: web | cli)
    'two_factor_disabled',       -- khách tắt / admin cài lại 2 bước bằng lệnh
    'two_factor_recovery_used',  -- đăng nhập bằng một mã dự phòng (detail.remaining)
    'order_hold_abuse',          -- bỏ 3 đơn chưa thanh toán trong 24 giờ, tài khoản bị khóa 24 giờ (detail.via: cancel | expired, detail.locked_until)
    'backup_created',            -- sao lưu thành công (detail: file, dung lượng, số bảng, số ảnh)
    'backup_failed',             -- sao lưu lỗi (detail: thông báo ngắn)
    'backup_exported',           -- giải mã một bản sao lưu ra file .sql trần để demo
    'restore_performed',         -- khôi phục đè lên CSDL (detail: file, CSDL đích)
    'restore_verified'           -- kiểm tra khôi phục vào CSDL tạm (detail: kết quả)
));
