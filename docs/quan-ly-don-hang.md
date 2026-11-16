# Quản lý đơn hàng (admin)

Chốt 2026-11-16. Trang `/dashboard/don-hang/` trong dashboard.

## 1. Luồng đơn

```
Chờ thanh toán → Đã thanh toán → Đã tiếp nhận → Đã đóng gói → Đang giao → Đã giao
   (khách)          (khách)        (admin)        (admin)       (admin)     (admin)
```

- Admin bấm 4 bước sau "Đã thanh toán", **lần lượt từng bước, không có quay lại**. Đơn chờ thanh toán, đã giao, đã hủy: admin chỉ xem.
- Mỗi bước là một thủ tục riêng và một URL riêng:

| Nút | URL (POST) | Thủ tục | Trạng thái trước → sau |
| --- | --- | --- | --- |
| Tiếp nhận đơn | `/dashboard/don-hang/<mã>/tiep-nhan/` | `sp_staff_order_confirm` | paid → confirmed |
| Đóng gói xong | `/dashboard/don-hang/<mã>/dong-goi/` | `sp_staff_order_pack` | confirmed → packed |
| Bắt đầu giao | `/dashboard/don-hang/<mã>/giao-hang/` | `sp_staff_order_ship` | packed → shipped |
| Giao thành công | `/dashboard/don-hang/<mã>/da-giao/` | `sp_staff_order_deliver` | shipped → delivered |

- Bấm nút → hộp xác nhận (`<details>`, không JS, **không nhập lại mật khẩu**) → **Xác nhận** (POST, CSRF). Xong quay lại đúng trang đang xem (chỉ nhận đường dẫn bắt đầu bằng `/dashboard/don-hang/`, chống open redirect).

## 2. Trang danh sách

- Cột: mã đơn (8 ký tự đầu, bấm để xem chi tiết), khách (username), ngày đặt, số cuốn, tổng tiền, trạng thái, nút bước tiếp theo.
- **Không có SĐT/địa chỉ** ở danh sách.
- Lọc: Tất cả, **Cần xử lý** (đã thanh toán, đã tiếp nhận, đã đóng gói, đang giao), hoặc từng trạng thái. Lựa chọn cố định, sai thì báo "Bộ lọc không hợp lệ" và không gọi CSDL. 20 đơn mỗi trang.

## 3. Trang chi tiết

- `/dashboard/don-hang/<mã>/`: trạng thái, khách, các mốc thời gian, mã giao dịch thanh toán (ghi "mô phỏng" nếu là thanh toán mô phỏng), người nhận, **SĐT, địa chỉ giao hàng**, sách và tiền, nút bước tiếp theo.
- **Phải xác thực lại** (`recent_auth_required`, 2 phút) và **mỗi lần xem ghi log** `sensitive_data_viewed` (`fields`: người nhận, SĐT, địa chỉ; `owner`: customer; 8 ký tự đầu mã đơn) – giống xem email/SĐT ở Quản lý tài khoản.
- SĐT/địa chỉ lưu mã hóa AES-GCM; thủ tục trả bản mã, Django giải mã với ngữ cảnh gắn chủ đơn + mã chống trùng của đơn (`orders.services.shipping_context`). Không giải mã được → "Không đọc được".

## 4. CSDL – `database/objects/44_staff_orders.sql`

- `sp_staff_order_list(actor, status, offset, limit)`: 2 bộ kết quả (tổng + trang), `status` NULL / `todo` / một trong 7 trạng thái, `limit` 1–100, `offset` ≤ 100000.
- `sp_staff_order_get(actor, code)`: thông tin đơn + `user_id`, `idempotency_key` (để giải mã) + giao dịch thành công (`payments_payment.success_order_id`), rồi danh sách sách.
- `sp_staff_order_confirm/pack/ship/deliver(actor, code)`: mỗi thủ tục cố định trạng thái trước/sau, cùng gọi thủ tục nội bộ `sp_staff_order_advance`:
  1. kiểm tra `actor` là nhân viên đang hoạt động (`NOT_STAFF`), mã đơn đúng mẫu;
  2. khóa dòng đơn `FOR UPDATE`, kiểm tra **đúng trạng thái trước**, sai → `ORDER_WRONG_STATUS`;
  3. đặt biến phiên `@bookstore_actor_id`, đổi trạng thái, xóa biến ngay; `COMMIT`.
- Lớp cuối: trigger `32_trg_orders_guard.sql` chỉ cho đi tới đúng một bước (chặn cả root).
- Nhật ký: trigger `34_trg_orders_audit.sql` tự ghi mỗi bước, nguồn **Quản trị**, `app_user_id` = id admin lấy từ `@bookstore_actor_id` (chỉ khi tài khoản MySQL là `app_staff`). Thủ tục không tự ghi thêm (không trùng).
- Quyền: `r_staff` EXECUTE 6 thủ tục công khai; `sp_staff_order_advance` không cấp cho tài khoản ứng dụng nào; `r_customer` không có gì. `app_staff` vẫn không có quyền ghi thẳng `orders_order`. `db_check_grants` thêm 7 kiểm tra (tổng 80).

Mã lỗi: `INVALID_INPUT`, `NOT_STAFF`, `ORDER_NOT_FOUND` (→ 404), `ORDER_WRONG_STATUS` ("Đơn hàng không còn ở bước này... Hãy tải lại trang").

## 5. Đã kiểm tra

- Test `dashboard/tests/test_orders.py` (17 test): bộ lọc/mã đơn/tên bước sai không xuống CSDL; mỗi bước gọi đúng thủ tục qua kết nối `staff`; giải mã đúng ngữ cảnh chủ đơn; lỗi quyền không bị nuốt; nút bước tiếp theo theo trạng thái; view: chỉ nhân viên (khách 403, ẩn danh đi đăng nhập), danh sách không có SĐT, chi tiết bắt xác thực lại + ghi log, mã không có 404, GET 405, thiếu CSRF 403, sai bước báo lỗi, redirect chỉ trong mục đơn hàng.
- Chạy thật trên MySQL trong sandbox: tiếp nhận đơn chờ thanh toán, đóng gói trước khi tiếp nhận → `ORDER_WRONG_STATUS`; 5 luồng bấm "Tiếp nhận" cùng lúc → 1 thành công, 4 `ORDER_WRONG_STATUS`; đi hết pack → ship → deliver; bấm "đã giao" lần 2 → `ORDER_WRONG_STATUS`; nhật ký đơn: `pending`, `paid` (Khách, id khách), `confirmed`, `packed`, `shipped`, `delivered` (Quản trị, id admin); biến phiên không còn sau thủ tục; chi tiết giải mã đúng SĐT/địa chỉ và hiện mã giao dịch; tổng "Cần xử lý" khớp đếm trực tiếp; id khách làm actor → `NOT_STAFF`.
