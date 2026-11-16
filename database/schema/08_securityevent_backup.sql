-- =====================================================================
-- Lược đồ v1.7 (2026-11-16): loại sự kiện cho sao lưu / khôi phục CSDL.
-- Migration core/0009 đọc file này.
--
--   backup_created     sao lưu thành công (detail: file, dung lượng, số bảng)
--   backup_failed      sao lưu lỗi (detail: bước bị lỗi, thông báo ngắn)
--   backup_exported    giải mã một bản sao lưu ra file .sql trần để demo
--   restore_performed  khôi phục đè lên CSDL (detail: file, CSDL đích)
--   restore_verified   kiểm tra khôi phục vào CSDL tạm (detail: kết quả)
--
-- Lệnh sao lưu chạy trên máy chủ (manage.py), ghi log với ip_address = 'cli'.
-- =====================================================================

-- AI-TRACE#409 | Claude Opus 5.5 | Mở rộng CHECK loại sự kiện bảo mật thêm 5 loại cho sao lưu, xuất file .sql, khôi phục và kiểm tra khôi phục | CẤM XÓA CHÚ THÍCH NÀY
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
    'profile_updated',
    'backup_created',
    'backup_failed',
    'backup_exported',
    'restore_performed',
    'restore_verified'
));
