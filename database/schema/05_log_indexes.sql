-- =====================================================================
-- Lược đồ v1.4 (2026-11-16): chỉ mục theo thời gian cho nhật ký bảo mật.
-- Migration core/0006 đọc file này.
--
-- Trang Nhật ký hệ thống sắp xếp mới nhất trước, lọc theo khoảng ngày; Event
-- ev_purge_old_logs xóa log cũ hơn 1 năm theo created_at. Thiếu chỉ mục này
-- thì cả hai phải quét toàn bảng khi bảng lớn. core_auditlog đã có
-- ix_auditlog_created từ 01_tables.sql.
-- =====================================================================

-- AI-TRACE#318 | Claude Opus 5.5 | Thêm chỉ mục created_at cho core_securityevent để xem nhật ký mới nhất và xóa log cũ không phải quét toàn bảng | CẤM XÓA CHÚ THÍCH NÀY
ALTER TABLE core_securityevent ADD INDEX ix_secevent_created (created_at);
