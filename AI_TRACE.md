# AI_TRACE – code do AI viết

File tạm, sinh bằng `python scripts/ai_trace.py`. Không sửa tay các cột Model, File, Class / Hàm, Dòng, Làm gì. Chỉ điền tay cột **Người dùng** và **Đã duyệt** (`[x]`). Quy định: `docs/ai-trace.md`.

| ID | Model | Người dùng | File | Class / Hàm | Dòng | Làm gì | Đã duyệt |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 001 | Claude Opus 5.5 |  | `database/objects/30_sp_place_order.sql` | `PROCEDURE sp_place_order` | 43 | Thủ tục đặt đơn: khóa giỏ và sách, kiểm tra kho, tạo đơn, trừ kho | [ ] |
| 002 | Claude Opus 5.5 |  | `backend/orders/services.py` | `OrderError` | 16 | Lỗi nghiệp vụ khi đặt đơn, mang mã lỗi và câu tiếng Việt | [ ] |
| 003 | Claude Opus 5.5 |  | `backend/orders/services.py` | `PlaceOrderResult` | 24 | Kết quả đặt đơn gồm mã đơn và cờ đơn mới | [ ] |
| 004 | Claude Opus 5.5 |  | `backend/orders/services.py` | `new_idempotency_key` | 30 | Sinh mã yêu cầu chống bấm đặt hàng hai lần | [ ] |
| 005 | Claude Opus 5.5 |  | `backend/orders/services.py` | `place_order` | 35 | Gọi thủ tục sp_place_order và đổi lỗi SIGNAL thành OrderError | [ ] |
| 006 | Claude Opus 5.5 |  | `backend/orders/services.py` | `_signal_code` | 55 | Đọc mã lỗi nghiệp vụ từ lỗi MySQL 1644 do SIGNAL | [ ] |
