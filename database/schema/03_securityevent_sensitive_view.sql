-- =====================================================================
-- Lược đồ v1.2: thêm loại sự kiện 'sensitive_data_viewed' (nhân viên xem
-- email/SĐT sau khi xác thực lại). Migration core/0004 đọc file này.
-- Giữ nguyên toàn bộ danh sách của 02_securityevent_email_events.sql.
-- =====================================================================

-- AI-TRACE#042 | Claude Opus 5.5 | Thêm loại sự kiện xem dữ liệu nhạy cảm vào danh sách cho phép | CẤM XÓA CHÚ THÍCH NÀY
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
    'sensitive_data_viewed'      -- xem dữ liệu nhạy cảm (detail.fields, detail.owner)
));
