# Thanh toán mô phỏng

Chốt 2026-11-16. Nhóm chưa đăng ký được tài khoản sandbox của VNPay hay MoMo, nên **tạm thời** khách thanh toán bằng một nút mô phỏng để các phần sau (lịch sử đơn, quản lý đơn của admin) làm tiếp được. Không có tiền thật nào chuyển đi. Khi có cổng thật sẽ quay lại thay phần này (xem mục 6).

## 1. Khách thấy gì

- Trang chi tiết đơn (`/orders/don/<mã đơn>/`), đơn đang **Chờ thanh toán** và còn hạn → nút **Thanh toán (mô phỏng)**.
- Bấm nút → hiện hộp xác nhận (`<details>`, không JS): ghi rõ là thanh toán mô phỏng, số tiền, và sau khi thanh toán đơn không hủy, không sửa được → **Xác nhận thanh toán** (POST).
- Thành công → đơn chuyển **Đã thanh toán**, hiện thời điểm thanh toán, thông báo kèm mã giao dịch (dạng `SIM` + 24 ký tự hex). Nút hủy đơn biến mất.
- Đơn quá hạn, đã hủy, đã thanh toán → không có nút.

## 2. Bật / tắt

`.env`:

```
PAYMENT_SIMULATION=True
```

- `False` hoặc không ghi (mặc định) → nút xám **Thanh toán** kèm "Chưa cấu hình cổng thanh toán"; gửi POST thẳng vào URL cũng bị từ chối ở service, không xuống CSDL.
- Đổi xong phải khởi động lại `runserver`.

## 3. Luồng xử lý

```
Trang đơn ──POST /payments/mo-phong/<mã đơn>/ (CSRF)──► payments.views.simulate
    @login_required, @require_POST, nhân viên → về dashboard
        │
        ▼
payments.services.simulate_payment(request, code)
    - PAYMENT_SIMULATION tắt          → NOT_CONFIGURED
    - ẩn danh / nhân viên             → NOT_CUSTOMER
    - mã đơn sai mẫu (32 hex thường)  → ORDER_NOT_FOUND, không xuống CSDL
    - giới hạn 10 lần / 10 phút (PAYMENT_SIMULATE_RATE_*), vượt → ghi log rate_limited
    - user_id lấy từ phiên, IP lấy từ REMOTE_ADDR; không nhận số tiền từ form
        │  callproc (kết nối default = app_customer)
        ▼
sp_payment_simulate(user_id, code, client_ip, OUT transaction_id)   [SQL SECURITY DEFINER]
    1. Kiểm tra: id hợp lệ, IP đúng mẫu, là khách hợp lệ (NOT_CUSTOMER), mã đơn đúng mẫu
    2. START TRANSACTION; khóa dòng đơn của chính khách FOR UPDATE
    3. Kiểm tra lại: không thấy → ORDER_NOT_FOUND; đã paid/shipped/delivered → ORDER_ALREADY_PAID;
       đã hủy → ORDER_NOT_PAYABLE; quá hạn → ORDER_EXPIRED
    4. Mã giao dịch = 'SIM' + HEX(RANDOM_BYTES(12)), sinh ngay trong CSDL
    5. INSERT payments_payment: provider 'simulated', amount = total của đơn trong CSDL,
       status 'success', signature_valid 0 (không có cổng nên không có chữ ký), raw_payload, client_ip
    6. UPDATE orders_order: status 'paid', paid_at
    7. COMMIT (lỗi bất kỳ → ROLLBACK; RESIGNAL)
        │
        ▼
Trigger 34_trg_orders_audit.sql tự ghi core_auditlog: đơn pending → paid, nguồn "Khách"
```

Lỗi nghiệp vụ hiện thông báo tiếng Việt rồi quay về trang đơn. `ORDER_NOT_FOUND` (đơn người khác, mã không có) → **404**, và nếu mã đúng định dạng thì ghi log `idor_attempt` như trang đơn và nút hủy đơn.

## 4. Các lớp bảo vệ

| Mối nguy | Chặn ở đâu |
| --- | --- |
| Thanh toán đơn của người khác (IDOR) | Thủ tục tìm đơn theo `code` **và** `user_id` lấy từ phiên; sai → cùng lỗi như mã không có → 404 + log `idor_attempt` |
| Sửa số tiền | Không nhận số tiền từ client; thủ tục lấy `total` từ dòng đơn trong CSDL |
| Bấm hai lần, mở hai tab bấm cùng lúc | Khóa dòng đơn `FOR UPDATE` rồi kiểm tra lại trạng thái; lớp cuối là UNIQUE `uq_payment_success_order` (một đơn tối đa một giao dịch thành công) |
| Bấm đúng lúc Event hủy đơn quá hạn | Hai bên xếp hàng trên cùng dòng đơn: thủ tục chỉ nhận khi `expires_at > lúc đó`, Event chỉ hủy khi `expires_at <= lúc đó` → không có đơn vừa "đã thanh toán" vừa "đã hủy", kho không lệch |
| Thanh toán rồi hủy để lấy lại sách | `sp_order_cancel` chỉ hủy `pending`; trigger 32 chỉ cho `pending → paid`, `pending → cancelled` |
| Thanh toán rồi sửa đơn | Trigger 32 khóa tiền, sách, thông tin giao hàng; `paid_at` chỉ ghi một lần |
| Sửa/xóa giao dịch đã ghi | Không tài khoản ứng dụng nào có quyền trên `payments_payment`; trigger `trg_payment_guard_update/delete` báo `PAYMENT_LOCKED`, chặn cả root |
| Ghi giao dịch "thành công" giả của cổng thật mà không có chữ ký | CHECK `ck_payment_success_valid`: thành công phải có mã giao dịch và chữ ký hợp lệ, chỉ loại `simulated` được miễn chữ ký |
| Gọi thẳng URL khi đã tắt mô phỏng | Service từ chối `NOT_CONFIGURED` trước khi xuống CSDL |
| Spam nút | Giới hạn tần suất theo tài khoản + log `rate_limited` |
| CSRF, GET | `require_POST` → GET trả 405; thiếu token CSRF → 403 (và log `csrf_failed`) |

## 5. CSDL

- Lược đồ `database/schema/06_payment_simulated.sql` (migration `core/0007_payment_simulated`):
  - bỏ giá trị mặc định `'mockpay'` của `provider`, CHECK `ck_payment_provider`: chỉ `simulated`, `momo`, `vnpay`;
  - CHECK `ck_payment_success_valid` mới: thành công bắt buộc có `transaction_id` và `signature_valid = 1`, trừ `provider = 'simulated'`;
  - cột sinh tự động `success_order_id` + UNIQUE `uq_payment_success_order`.
- Đối tượng `database/objects/35_payment_simulate.sql`: `sp_payment_simulate`, `trg_payment_guard_update`, `trg_payment_guard_delete`.
- Quyền: definer `SELECT, INSERT, TRIGGER` trên `payments_payment` (đã có `UPDATE orders_order`); `r_customer` chỉ `EXECUTE sp_payment_simulate`. `db_check_grants` thêm 5 kiểm tra (tổng 71): `app_customer` gọi được thủ tục, không đọc/ghi thẳng `payments_payment`; `app_staff` không gọi được thủ tục, không đọc bảng.

## 6. Khi có cổng thật (VNPay/MoMo)

1. Thêm thủ tục ghi nhận của cổng, ghi vào **cùng bảng** `payments_payment` (`provider` = `vnpay`/`momo`, `signature_valid`, mọi lần báo về kể cả bị từ chối), đổi đơn sang `paid` theo đúng các bước 2–7 ở mục 3.
2. Thêm kiểm tra chữ ký, số tiền, hạn, mã giao dịch dùng một lần; nếu dùng khóa sandbox công khai thì thêm bước server tự tra cứu giao dịch với cổng.
3. Đặt `PAYMENT_SIMULATION=False`, bỏ `sp_payment_simulate` và dòng `GRANT EXECUTE ... sp_payment_simulate TO 'r_customer'`.
4. Lịch sử đơn và quản lý đơn của admin không phải sửa, vì chỉ đọc trạng thái đơn và bảng `payments_payment`.

## 7. Đã kiểm tra

- Test `payments/tests/test_simulate.py` (15 test): tắt cờ không xuống CSDL; mã đơn sai mẫu bị chặn; nhân viên/ẩn danh bị chặn; đổi lỗi SIGNAL; lỗi quyền và lỗi lạ không bị nuốt; giới hạn tần suất + log; từ chối trong `transaction.atomic`; view: thành công kèm mã giao dịch, đơn người khác 404 + `idor_attempt`, thông báo lỗi nghiệp vụ, GET 405, thiếu CSRF 403, nút chỉ hiện khi bật cờ và đơn còn chờ, tắt cờ hiện "Chưa cấu hình cổng thanh toán". Tổng 404 test.
- Chạy thật trên MySQL trong sandbox:
  - thanh toán đơn còn hạn → đơn `paid` có `paid_at`; một dòng `payments_payment` loại `simulated`, `signature_valid = 0`, số tiền đúng bằng `total`, IP; nhật ký đơn ghi `pending → paid` nguồn **Khách**;
  - thanh toán lần 2 → `ORDER_ALREADY_PAID`; hủy đơn đã thanh toán → `ORDER_NOT_CANCELLABLE`; khách khác → `ORDER_NOT_FOUND`; id quản trị → `NOT_CUSTOMER`; đơn quá hạn → `ORDER_EXPIRED`; đơn đã hủy → `ORDER_NOT_PAYABLE`; IP chứa ký tự lạ → `INVALID_INPUT`;
  - root `UPDATE`/`DELETE payments_payment` → `PAYMENT_LOCKED`; root chèn giao dịch thành công thứ hai cho cùng đơn → lỗi 1062 `uq_payment_success_order`; root chèn giao dịch `momo` thành công không chữ ký → vi phạm `ck_payment_success_valid`; `provider = 'mockpay'` → vi phạm `ck_payment_provider`;
  - 6 luồng bấm thanh toán cùng lúc một đơn → 1 thành công, 5 `ORDER_ALREADY_PAID`, đúng 1 dòng giao dịch;
  - 10 vòng bấm thanh toán đúng lúc đơn hết hạn và thủ tục hủy đơn quá hạn chạy liên tục → mỗi vòng hoặc `paid` + 1 giao dịch + kho giữ nguyên, hoặc `cancelled` + 0 giao dịch + kho trả lại; không vòng nào lệch.
- `db_check_grants` 71/71, `makemigrations --check` không đổi, `bandit -r backend -q` sạch, quét ký tự vô hình sạch.
