-- =====================================================================
-- Lược đồ v1.10 (2026-11-20): chỉ khách đã nhận sách mới được đánh giá.
-- Migration core/0012 đọc file này.
--
-- Nhóm trưởng chốt (2026-11-20, mức c): XÓA HẲN các đánh giá hiện có của khách
-- chưa có đơn 'delivered' chứa cuốn sách đó (dữ liệu thử trước khi siết luật).
-- Từ nay sp_review_save (objects/21_review.sql) tự chặn bằng NOT_PURCHASED.
-- Xóa dữ liệu nên migration KHÔNG đảo ngược được.
-- =====================================================================

-- AI-TRACE#515 | Claude Opus 5.5 | Xóa đánh giá của khách chưa nhận sách (không có đơn đã giao chứa cuốn sách đó) | CẤM XÓA CHÚ THÍCH NÀY
DELETE r
  FROM catalog_review r
 WHERE NOT EXISTS (
        SELECT 1
          FROM orders_orderitem i
          JOIN orders_order o ON o.id = i.order_id
         WHERE i.book_id = r.book_id AND o.user_id = r.user_id AND o.status = 'delivered'
       );
