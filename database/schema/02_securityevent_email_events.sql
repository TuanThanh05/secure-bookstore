-- =====================================================================
-- Lược đồ v1.1: thêm loại sự kiện bảo mật cho luồng đăng ký + xác nhận email.
-- Migration backend/core/migrations/0003_securityevent_email_events.py đọc
-- và chạy file này (bằng tài khoản migrate). Không chạy bằng tay.
--
-- MySQL không sửa được CHECK tại chỗ: xóa ràng buộc cũ rồi tạo lại với danh
-- sách đầy đủ (giữ nguyên mọi loại cũ, thêm 7 loại mới ở cuối).
-- =====================================================================

-- AI-TRACE#032 | Claude Opus 5.5 | Mở rộng danh sách loại sự kiện bảo mật cho xác nhận email | CẤM XÓA CHÚ THÍCH NÀY
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
    'register_success',          -- tạo tài khoản mới (chưa xác nhận email)
    'register_existing_email',   -- đăng ký bằng email đã có tài khoản (không tạo gì)
    'email_sent',                -- đã gửi thư (detail.kind: verify | existing_notice)
    'email_send_failed',         -- gửi thư lỗi (SMTP)
    'email_verified',            -- xác nhận email thành công
    'email_verify_failed',       -- link xác nhận sai, hết hạn hoặc đã dùng (detail.reason)
    'login_blocked_unverified'   -- đúng mật khẩu nhưng email chưa xác nhận
));
