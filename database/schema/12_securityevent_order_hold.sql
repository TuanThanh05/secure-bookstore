-- =====================================================================
-- Lược đồ v1.11 (2026-11-20): thêm loại sự kiện 'order_hold_abuse' (chống giữ
-- kho – báo cáo rà soát T3.4: khách bỏ 3 đơn chưa thanh toán trong 24 giờ bị khóa
-- tài khoản 24 giờ, xem database/objects/33_order_cancel.sql).
-- Migration core/0013 đọc file này. Giữ nguyên toàn bộ danh sách của
-- 10_two_factor.sql. Cột accounts_user.auto_locked_until do migration
-- accounts/0004 (Django) thêm.
-- =====================================================================

-- AI-TRACE#536 | Claude Opus 5.5 | Thêm loại sự kiện giữ kho bị khóa tài khoản vào danh sách cho phép | CẤM XÓA CHÚ THÍCH NÀY
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
    'order_hold_abuse'           -- bỏ 3 đơn chưa thanh toán trong 24 giờ, tài khoản bị khóa 24 giờ (detail.via: cancel | expired, detail.locked_until)
));
