-- =====================================================================
-- Lược đồ v1.6 (2026-11-16): luồng xử lý đơn sau khi thanh toán.
-- Migration core/0008 đọc file này.
--
-- Chốt 2026-11-16: sau "Đã thanh toán", admin đưa đơn đi lần lượt từng bước,
-- không có bước quay lại:
--
--   pending → paid → confirmed → packed → shipped → delivered
--   (Chờ thanh toán → Đã thanh toán → Đã tiếp nhận → Đã đóng gói → Đang giao → Đã giao)
--   pending → cancelled (khách hủy hoặc quá hạn)
--
-- Thêm 2 trạng thái 'confirmed', 'packed' vào CHECK trạng thái, và bắt buộc
-- có paid_at với mọi trạng thái sau khi thanh toán. Chiều chuyển trạng thái
-- do trigger 32_trg_orders_guard.sql kiểm tra.
-- =====================================================================

-- AI-TRACE#362 | Claude Opus 5.5 | Thêm trạng thái đơn Đã tiếp nhận (confirmed) và Đã đóng gói (packed), mọi trạng thái sau thanh toán bắt buộc có paid_at | CẤM XÓA CHÚ THÍCH NÀY
ALTER TABLE orders_order DROP CHECK ck_order_status;

ALTER TABLE orders_order DROP CHECK ck_order_paid_has_time;

ALTER TABLE orders_order
    ADD CONSTRAINT ck_order_status
        CHECK (status IN ('pending', 'paid', 'confirmed', 'packed', 'shipped', 'delivered', 'cancelled')),
    ADD CONSTRAINT ck_order_paid_has_time
        CHECK (status NOT IN ('paid', 'confirmed', 'packed', 'shipped', 'delivered') OR paid_at IS NOT NULL);
