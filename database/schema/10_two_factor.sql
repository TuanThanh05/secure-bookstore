-- =====================================================================
-- Lược đồ v1.9 (2026-11-20): xác thực 2 bước bằng ứng dụng (TOTP, RFC 6238).
-- Migration core/0011 đọc file này. Xem docs/xac-thuc-2-buoc.md.
--
--   accounts_totpdevice   : mỗi tài khoản tối đa 1 thiết bị. Chuỗi bí mật lưu
--                           MÃ HÓA AES-GCM (core/crypto.py, ngữ cảnh gắn user_id).
--   accounts_recoverycode : 5 mã dự phòng của khách, chỉ lưu mã băm (Argon2).
--
-- Quyền: chỉ r_auth (app_auth) đọc/ghi 2 bảng này. app_customer, app_staff,
-- app_session KHÔNG có quyền gì: SQL injection ở trang khác không đọc được
-- chuỗi bí mật. Trigger 12 chặn app_auth đụng vào 2 bước của nhân viên
-- (chỉ được ghi last_used_step khi admin đăng nhập).
-- =====================================================================

-- AI-TRACE#468 | Claude Opus 5.5 | Bảng thiết bị TOTP: chuỗi bí mật mã hóa, lúc xác nhận, bước thời gian đã dùng gần nhất (chống dùng lại mã) | CẤM XÓA CHÚ THÍCH NÀY
CREATE TABLE accounts_totpdevice (
    id                BIGINT       NOT NULL AUTO_INCREMENT,
    user_id           BIGINT       NOT NULL,
    secret_encrypted  VARCHAR(255) NOT NULL,                 -- "v1." + base64(nonce + bản mã + tag)
    confirmed_at      DATETIME(6)  NULL,                     -- NULL: đang cài, chưa nhập đúng mã lần đầu
    last_used_step    BIGINT       NULL,                     -- floor(unix / 30) của mã vừa dùng; mã có bước <= số này bị từ chối
    created_at        DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),

    PRIMARY KEY (id),
    UNIQUE KEY uq_totp_user (user_id),
    CONSTRAINT fk_totp_user FOREIGN KEY (user_id)
        REFERENCES accounts_user (id) ON DELETE CASCADE,
    CONSTRAINT ck_totp_secret_format CHECK (secret_encrypted LIKE 'v1.%'),
    CONSTRAINT ck_totp_step CHECK (last_used_step IS NULL OR last_used_step >= 0)
) ENGINE=InnoDB
  COMMENT='Thiết bị xác thực 2 bước (TOTP) của mỗi tài khoản';

-- AI-TRACE#469 | Claude Opus 5.5 | Bảng mã dự phòng: chỉ mã băm, mỗi mã dùng một lần | CẤM XÓA CHÚ THÍCH NÀY
CREATE TABLE accounts_recoverycode (
    id          BIGINT       NOT NULL AUTO_INCREMENT,
    user_id     BIGINT       NOT NULL,
    code_hash   VARCHAR(128) NOT NULL,                       -- cùng định dạng cột accounts_user.password
    used_at     DATETIME(6)  NULL,
    created_at  DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),

    PRIMARY KEY (id),
    INDEX ix_recovery_user (user_id, used_at),
    CONSTRAINT fk_recovery_user FOREIGN KEY (user_id)
        REFERENCES accounts_user (id) ON DELETE CASCADE
) ENGINE=InnoDB
  COMMENT='Mã dự phòng xác thực 2 bước (chỉ mã băm)';

-- AI-TRACE#470 | Claude Opus 5.5 | Thêm 3 loại sự kiện log của xác thực 2 bước | CẤM XÓA CHÚ THÍCH NÀY
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
    'two_factor_recovery_used'   -- đăng nhập bằng một mã dự phòng (detail.remaining)
));
