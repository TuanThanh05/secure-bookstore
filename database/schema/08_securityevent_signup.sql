-- =====================================================================
-- Lược đồ v1.7 (2026-11-19): đăng ký bắt đầu bằng email (sửa lỗ hổng chiếm tài khoản
-- trước khi đăng ký – account pre-hijacking).
-- Migration core/0009 đọc file này.
--
-- Luồng cũ tạo tài khoản ngay khi gửi form rồi mới gửi link xác nhận email.
-- Luồng mới chỉ tạo tài khoản sau khi người dùng mở link trong thư, nên bỏ
-- 3 loại sự kiện của luồng cũ và thêm 1 loại mới:
--   - bỏ:   'email_verified', 'email_verify_failed', 'login_blocked_unverified'
--   - thêm: 'register_link_invalid' (link đăng ký sai/hết hạn/đã dùng, hoặc
--           phiên đăng ký hết hạn; detail.reason)
-- Các dòng log của 3 loại bị bỏ (chỉ có ở CSDL đã chạy luồng cũ) được xóa
-- trước, nếu không ràng buộc CHECK mới không thêm được.
-- Giữ nguyên phần còn lại của danh sách trong 04_securityevent_profile_updated.sql.
-- =====================================================================

-- AI-TRACE#428 | Claude Opus 5.5 | Bỏ loại sự kiện của luồng xác nhận email cũ, thêm loại link đăng ký không hợp lệ | CẤM XÓA CHÚ THÍCH NÀY
ALTER TABLE core_securityevent DROP CHECK ck_secevent_type;

DELETE FROM core_securityevent
 WHERE event_type IN ('email_verified', 'email_verify_failed', 'login_blocked_unverified');

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
    'email_sent',
    'email_send_failed',
    'sensitive_data_viewed',
    'profile_updated'
));
