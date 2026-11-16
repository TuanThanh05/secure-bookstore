-- =====================================================================
-- Lược đồ v1.5 (2026-11-16): giao dịch thanh toán mô phỏng.
-- Migration core/0007 đọc file này.
--
-- Chốt 2026-11-16: tạm thời chưa có cổng thanh toán thật, khách bấm nút
-- "Thanh toán (mô phỏng)" (chỉ bật khi PAYMENT_SIMULATION=True trong .env).
-- Mỗi lần thanh toán vẫn ghi một dòng payments_payment loại 'simulated' để
-- sau này lắp cổng thật chỉ cần ghi vào đúng bảng này.
--
--   - provider: bỏ giá trị mặc định 'mockpay' (thủ tục phải ghi rõ cổng nào),
--     chỉ nhận 'simulated', 'momo', 'vnpay'.
--   - Giao dịch thành công: bắt buộc có transaction_id và chữ ký hợp lệ, trừ
--     loại 'simulated' (không có cổng nên không có chữ ký; ghi signature_valid
--     = 0 cho đúng sự thật thay vì giả là 1).
--   - Mỗi đơn chỉ có tối đa MỘT giao dịch thành công (cột sinh tự động +
--     UNIQUE), chặn trả tiền hai lần cho một đơn ngay trong CSDL.
-- =====================================================================

-- AI-TRACE#349 | Claude Opus 5.5 | Cho phép giao dịch thanh toán mô phỏng không có chữ ký, giới hạn tên cổng, mỗi đơn tối đa một giao dịch thành công | CẤM XÓA CHÚ THÍCH NÀY
ALTER TABLE payments_payment ALTER COLUMN provider DROP DEFAULT;

ALTER TABLE payments_payment DROP CHECK ck_payment_success_valid;

ALTER TABLE payments_payment
    ADD CONSTRAINT ck_payment_success_valid CHECK (
        status <> 'success'
        OR (transaction_id IS NOT NULL AND (signature_valid = 1 OR provider = 'simulated'))
    ),
    ADD CONSTRAINT ck_payment_provider CHECK (provider IN ('simulated', 'momo', 'vnpay'));

ALTER TABLE payments_payment
    ADD COLUMN success_order_id BIGINT
        GENERATED ALWAYS AS (IF(status = 'success', order_id, NULL)) STORED,
    ADD CONSTRAINT uq_payment_success_order UNIQUE (success_order_id);
