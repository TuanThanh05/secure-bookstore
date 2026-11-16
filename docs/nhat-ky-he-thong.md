# Nhật ký hệ thống

Chốt 2026-11-16. Trang `/dashboard/nhat-ky/` cho admin xem hai loại nhật ký. **Bắt buộc xác thực lại** (cửa sổ 2 phút), mỗi lần xem (kể cả đổi bộ lọc, sang trang) ghi `sensitive_data_viewed` với `detail.fields` = `security_log` hoặc `audit_log` và bộ lọc đang dùng. Nhật ký giữ **1 năm**, không khóa cứng (chốt).

## 1. Hai loại nhật ký

| | Nhật ký bảo mật (`core_securityevent`) | Nhật ký thay đổi dữ liệu (`core_auditlog`) |
| --- | --- | --- |
| Ai ghi | Django (`core.security_log.log_event`), cùng lúc ghi file `security.log` | Thủ tục MySQL và trigger, trong cùng giao dịch với thay đổi |
| Ghi gì | Sự kiện liên quan an toàn: đăng nhập, quyền, CSRF, dò dữ liệu... | Dữ liệu nào đổi, giá trị cũ → mới, ai đổi, qua tài khoản MySQL nào |
| Tab | **Bảo mật** `/dashboard/nhat-ky/` | **Thay đổi dữ liệu** `/dashboard/nhat-ky/thay-doi/` |
| Lọc | Loại sự kiện, mức độ, từ ngày–đến ngày, username hoặc IP | Dữ liệu (bảng), hành động, từ ngày–đến ngày, id bản ghi |

Tài khoản ứng dụng (`app_customer`, `app_staff`) chỉ có **INSERT** trên hai bảng: không đọc, sửa, xóa thẳng được. Admin đọc qua thủ tục.

## 2. Các sự kiện bảo mật đang ghi

| Nhóm | Sự kiện (`event_type`) | Mức độ |
| --- | --- | --- |
| Đăng nhập | `login_success` (cả xác thực lại: `detail.step_up`), `login_failed`, `logout`, `account_locked` (axes khóa tạm), `login_blocked_unverified` | info / warning / critical |
| Tài khoản | `register_success`, `register_existing_email`, `email_sent`, `email_send_failed`, `email_verified`, `email_verify_failed`, `password_changed`, `password_reset_requested`, `profile_updated` | info / warning |
| Truy cập | `access_denied` (403), `sensitive_data_viewed`, `rate_limited`, `invalid_input` | info / warning |
| **Mới (2026-11-16)** | `csrf_failed` – thiếu/sai CSRF (`detail.reason` của Django, không hiện cho người dùng) | warning |
| | `upload_rejected` – ảnh bìa bị từ chối (`detail.code`, không ghi tên/nội dung file) | warning |
| | `db_permission_denied` – MySQL từ chối vì thiếu quyền (1044, 1142, 1143, 1227, 1370), ghi bằng middleware `core.middleware.DbPermissionDeniedMiddleware`; người dùng chỉ thấy trang 500 | **critical** |
| | `idor_attempt` – mở/hủy đơn bằng mã **đúng định dạng** nhưng không phải đơn của mình (hoặc không có); mã rác không ghi; người dùng vẫn chỉ thấy 404 (`detail.code_prefix` 8 ký tự) | warning |

Chưa dùng: `otp_failed` (không có 2FA), `payment_*` (nhánh thanh toán).

**Không bao giờ ghi** mật khẩu, token, session ID, nội dung file, SĐT/địa chỉ.

## 3. Nhật ký thay đổi dữ liệu

| Dữ liệu | Ghi bởi | Nội dung |
| --- | --- | --- |
| Thể loại, Sách | Thủ tục `40_category.sql`, `41_book.sql` | Thêm/sửa/xóa, nhập/giảm kho, ẩn/hiện |
| Tài khoản | `42_account.sql` | Khóa/mở khóa + **lý do** |
| **Đơn hàng (mới)** | Trigger `34_trg_orders_audit.sql` | Tạo đơn (mã, tổng tiền, trạng thái), mọi lần đổi trạng thái (cũ → mới) |

**Nguồn** của thay đổi đơn hàng suy ra từ tài khoản MySQL (`USER()`): `app_customer` → Khách (kèm id khách), `event_scheduler` → Hệ thống (Event tự hủy đơn quá hạn – trong Event, `USER()` là `event_scheduler@localhost`, đã thử thật), `app_payment` → Thanh toán, `app_staff` → Quản trị, còn lại (root...) → Khác. Dùng trigger nên thủ tục nào đổi đơn cũng có log, không sót.

## 4. Thủ tục (`database/objects/43_logs.sql`)

| Thủ tục | Ai gọi | Ghi chú |
| --- | --- | --- |
| `sp_staff_security_events(actor, loại, mức độ, từ, đến, từ khóa, offset, limit)` | `r_staff` | 2 bộ kết quả: tổng số dòng, một trang mới nhất trước |
| `sp_staff_audit_log(actor, bảng, hành động, từ, đến, id bản ghi, offset, limit)` | `r_staff` | như trên, kèm username người thực hiện |
| `sp_purge_old_logs(OUT số dòng)` | **chỉ Event** `ev_purge_old_logs` (mỗi ngày 03:00 giờ VN) | Xóa log cũ hơn 1 năm ở cả hai bảng, theo lô 5000 dòng |

Kiểm tra đầu vào trong thủ tục: loại/bảng chỉ chữ thường và `_`, mức độ/hành động trong danh sách cố định, khoảng ngày ≤ 400 ngày, mỗi trang ≤ 100 dòng, offset ≤ 100000, từ khóa ≤ 150 ký tự và thoát `\ % _`. Django lọc thêm bằng danh sách cố định (form), ngày theo giờ Việt Nam đổi sang UTC.

**Chỉ mục mới:** `ix_secevent_created (created_at)` trên `core_securityevent` (`database/schema/05_log_indexes.sql`, migration `core/0006_log_indexes`) để xem mới nhất trước và xóa log cũ không phải quét toàn bảng.

**Quyền definer thêm:** `SELECT, DELETE` trên hai bảng log (DELETE chỉ dùng trong `sp_purge_old_logs`).

## 5. Đã kiểm tra

Test `dashboard/tests/test_logs.py`, `db_check_grants` tổng 66, chạy thật trong sandbox:

- Trang nhật ký chưa xác thực lại → chuyển tới trang xác thực lại; khách → 403; mỗi lần xem có log.
- Lọc loại/mức độ/ngày/username-IP đúng; loại lạ, ngày ngược → báo lỗi, không gọi CSDL; tìm `%`, `' OR 1=1 -- ` → 0 dòng; tham số sai gọi thẳng thủ tục → `INVALID_INPUT`.
- `app_customer` gọi thủ tục đọc/xóa log → 1370, đọc bảng log → 1142; `app_staff` đọc thẳng/xóa log → 1142.
- Trigger đơn hàng: khách đặt rồi hủy → 2 dòng nguồn "Khách" kèm id; Event tự hủy đơn quá hạn → nguồn "Hệ thống".
- Event xóa log: log 2 năm và 366 ngày bị xóa, log 364 ngày và audit 10 ngày còn nguyên; Event chạy được bằng quyền definer.
- 4 log mới: gửi form thiếu CSRF → `csrf_failed`; mở/hủy đơn người khác bằng mã đúng định dạng → `idor_attempt` (mã rác không ghi); upload file giả ảnh → `upload_rejected`; tạm thu hồi `EXECUTE sp_cart_list` của khách rồi mở giỏ → trang 500 và `db_permission_denied` (critical, `mysql_code` 1370).
