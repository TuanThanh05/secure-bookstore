-- =====================================================================
-- Lược đồ v1.3: thêm loại sự kiện 'profile_updated' (khách sửa họ, tên, SĐT).
-- Migration core/0005 đọc file này.
-- Giữ nguyên toàn bộ danh sách của 03_securityevent_sensitive_view.sql.
-- =====================================================================

-- AI-TRACE#078 | Claude Opus 5.5 | Thêm loại sự kiện cập nhật hồ sơ vào danh sách cho phép | CẤM XÓA CHÚ THÍCH NÀY
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
    'register_success',
    'register_existing_email',
    'email_sent',
    'email_send_failed',
    'email_verified',
    'email_verify_failed',
    'login_blocked_unverified',
    'sensitive_data_viewed',
    'profile_updated'            -- khách sửa hồ sơ (detail.fields: tên cột, không có giá trị)
));
