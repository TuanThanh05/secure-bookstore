-- =====================================================================
-- Lược đồ v1.8 (2026-11-19): thêm loại sự kiện 'captcha_failed' (Cloudflare
-- Turnstile ở trang đăng ký bước 1 không đạt).
-- Migration core/0010 đọc file này.
-- Giữ nguyên toàn bộ danh sách của 08_securityevent_signup.sql.
-- =====================================================================

-- AI-TRACE#440 | Claude Opus 5.5 | Thêm loại sự kiện CAPTCHA không đạt vào danh sách cho phép | CẤM XÓA CHÚ THÍCH NÀY
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
    'profile_updated'
));
