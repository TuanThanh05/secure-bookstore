# Quản lý tài khoản khách (dashboard)

Chốt 2026-11-16. Trang `/dashboard/tai-khoan/` cho admin xem, lọc, khóa và mở khóa tài khoản **khách hàng**. Tài khoản nhân viên (kể cả chính admin) không hiện trong danh sách và không khóa được.

## 1. Admin thấy gì

| Cột | Ghi chú |
| --- | --- |
| Username | Đầy đủ |
| Email | Che bớt: `a***n@example.test` (giữ ký tự đầu, cuối của phần trước `@` và tên miền) |
| Số điện thoại | Che bớt: `090****567`. CSDL lưu bản mã AES-GCM, Django giải mã rồi mới che |
| Trạng thái | Hoạt động / Đã khóa / Tạm khóa / Chưa xác nhận email |
| Ngày tạo, Đăng nhập gần nhất | |
| Thao tác | **Khóa** (tài khoản chưa khóa) hoặc **Mở khóa** (tài khoản đã khóa) |

Bộ lọc: trạng thái (danh sách cố định) và username (tìm gần đúng, tối đa 150 ký tự). Tối đa 200 dòng mỗi lần, 20 dòng mỗi trang.

**Xem email, SĐT đầy đủ:** nút "Xem email, SĐT đầy đủ" → `/dashboard/tai-khoan/day-du/`, cần **xác thực lại** (cửa sổ 2 phút như trang thông tin admin), mỗi lần xem ghi log `sensitive_data_viewed` (`detail`: các cột, số dòng, bộ lọc).

**Trạng thái** (ưu tiên từ trên xuống):

| Trạng thái | Khi nào |
| --- | --- |
| Đã khóa | Admin đã khóa (`is_active = 0`) |
| Khóa tự động (giữ kho) | `auto_locked_until` còn hạn: khách hủy hoặc bỏ 3 đơn chưa thanh toán trong 24 giờ bị khóa 24 giờ (xem `docs/contract.md` mục Hủy đơn – Chống giữ kho). Admin bấm **Mở khóa** để gỡ sớm (cần lý do + mật khẩu như thường) |
| Tạm khóa | django-axes ghi ≥ `AXES_FAILURE_LIMIT` (5) lần đăng nhập sai trong `AXES_COOLOFF_TIME` (15 phút) gần nhất. Trang chỉ ghi "Tạm khóa", lý do xem trong log |
| Chưa xác nhận email | `email_verified = 0` |
| Hoạt động | Còn lại |

## 2. Thủ tục (`database/objects/42_account.sql`)

Chỉ `r_staff` được EXECUTE; `r_customer` gọi → lỗi 1370. Mỗi thủ tục tự kiểm tra `p_actor_id` là nhân viên đang hoạt động (`NOT_STAFF`).

| Thủ tục | Tham số | Kết quả |
| --- | --- | --- |
| `sp_staff_account_list` | `actor`, `status` (`active`/`locked`/`temp_locked`/`unverified` hoặc NULL), `keyword` (username, NULL = không lọc), ngưỡng axes (số lần, số phút) | Gộp xem + lọc trạng thái + lọc username vào một thủ tục (chốt). `LIKE` có thoát `\`, `%`, `_` |
| `sp_staff_account_get` | `actor`, `user_id`, ngưỡng axes | Một tài khoản khách (trang xác nhận) |
| `sp_staff_account_lock` | `actor`, `user_id`, `reason` (5–255 ký tự) | `is_active = 0` + `core_auditlog` (lý do, `USER()`, id admin) cùng giao dịch |
| `sp_staff_account_unlock` | như trên | `is_active = 1` + `core_auditlog` |

Mã lỗi: `INVALID_INPUT`, `NOT_STAFF`, `ACCOUNT_NOT_FOUND` (không có hoặc là tài khoản nhân viên – như nhau), `ALREADY_LOCKED`, `NOT_LOCKED`. Khóa/mở khóa khóa dòng user `FOR UPDATE` nên bấm cùng lúc nhiều lần chỉ một lần thành công, nhật ký không ghi trùng.

Ngưỡng axes truyền từ Django (`AXES_FAILURE_LIMIT`, `AXES_COOLOFF_TIME`) để không ghi cứng hai chỗ. Thủ tục không trả `password`, `is_superuser`.

**Trigger** `trg_user_guard_update` (`10_trg_accounts_user_guard.sql`) vẫn chặn `app_staff` sửa dòng của khách, **trừ đúng cột `is_active`**. `app_staff` không có quyền `UPDATE(is_active)` trực tiếp (lỗi 1143), nên chỉ hai thủ tục khóa/mở khóa đổi được, và luôn có nhật ký.

**Quyền definer thêm:** `UPDATE(is_active)` trên `accounts_user`, `SELECT` trên `axes_accessattempt`.

## 3. Khóa / mở khóa: xác thực riêng cho từng lần

Chốt: mỗi lần khóa hay mở khóa **đều phải nhập lại mật khẩu**, kể cả khi admin vừa xác thực lại 2 phút trước, và lần xác thực đó **chỉ có hiệu lực đúng một lần**.

Cách làm: form xác nhận (`/dashboard/tai-khoan/<id>/khoa/` hoặc `/mo-khoa/`) gồm **Lý do**, **Tên đăng nhập**, **Mật khẩu** của admin. Mật khẩu được kiểm tra bằng `authenticate()` cho đúng lần gửi đó rồi gọi thủ tục ngay; không lưu dấu "đã xác thực" vào phiên, nên lần sau phải nhập lại. Vì đi qua `authenticate()`, nhập sai bị django-axes đếm như đăng nhập sai (5 lần → tạm khóa 15 phút). Nhập tài khoản/mật khẩu của người khác → từ chối + log `access_denied`. Thành công → log `login_success` với `detail.step_up = true`, `action`, `target_id`.

**Sau khi khóa:** mọi phiên đang mở của khách bị **xóa ngay** (mọi thiết bị) và khách không đăng nhập được cho tới khi mở khóa. Thông báo cho admin ghi số phiên đã đăng xuất; log `logout` (`detail.reason = "account_locked"`, `target_id`, `sessions_ended`).

**Lỗi đã sửa (2026-11-20, báo cáo rà soát T3.1 / SA-05):** trước đây chỉ đặt `is_active = 0`. Django coi phiên đó là "chưa đăng nhập" nhưng **không xóa** dòng phiên; vì `SESSION_SAVE_EVERY_REQUEST = True`, mỗi request mang cookie đó trong lúc bị khóa còn gia hạn phiên thêm 30 phút. Khi admin **mở khóa**, cookie cũ (có thể đã bị đánh cắp – lý do khóa) lập tức dùng lại được mà không cần mật khẩu. Hai lớp sửa:

1. `lock_account` gọi `core.session_store.end_user_sessions(user_id)` sau khi `sp_staff_account_lock` thành công (đọc từng dòng phiên bằng đúng khóa đã băm, xóa dòng có `_auth_user_id` của khách). Thủ tục báo lỗi thì không xóa gì.
2. `core.middleware.InactiveAccountSessionMiddleware` (ngay sau `AuthenticationMiddleware`): phiên còn `_auth_user_id` mà người dùng không còn hợp lệ (bị khóa bằng bất kỳ cách nào, kể cả sửa thẳng CSDL) thì `session.flush()` + log `logout` (`detail.reason = "account_inactive"`).

Kiểm tra: `core/tests/test_inactive_session.py` (2/4 test trượt trên code cũ: phiên bị đánh cắp sống lại sau khi mở khóa); sandbox: khóa bằng thủ tục thật → 1 phiên bị xóa, mở khóa → cookie cũ vẫn phải đăng nhập lại; khóa bằng root `UPDATE` (không qua hàm) → middleware vẫn hủy phiên.

## 4. Bảo mật đã kiểm tra

Test `dashboard/tests/test_accounts.py`, `db_check_grants` tổng 58, chạy thật trong sandbox:

- Danh sách không có tài khoản nhân viên; email/SĐT đầy đủ không có trong HTML trang thường; trang đầy đủ chưa xác thực lại → chuyển tới trang xác thực lại; xem đầy đủ → có log.
- Tìm username bằng `%`, `' OR 1=1 -- ` → 0 kết quả; trạng thái lạ → bỏ qua (thủ tục cũng từ chối `INVALID_INPUT`).
- Vừa xác thực lại xong, gửi form khóa với mật khẩu sai hoặc không có mật khẩu → 400, không khóa. Lý do dưới 5 ký tự → 400.
- Khóa đúng → `is_active = 0`, nhật ký có lý do; khách đang đăng nhập bấm tiếp → bị chuyển về trang đăng nhập; mở khóa đúng → `is_active = 1`.
- Mở trang khóa của tài khoản admin hoặc id không có → 404. Khách vào trang quản lý → 403; ẩn danh → trang đăng nhập; thiếu CSRF → 403.
- `app_staff`: sửa tên khách → trigger chặn (1644); `UPDATE is_active` thẳng → 1143. `app_customer` gọi 4 thủ tục → 1370.
- 4 lần khóa (hoặc mở khóa) cùng lúc → 1 thành công, 3 `ALREADY_LOCKED`/`NOT_LOCKED`, nhật ký đúng 1 dòng mỗi thao tác.
