# Quyền ghi bảng tài khoản: tách `app_auth` + trigger chặn cột

Tài liệu này giải thích lỗ còn hở ở lớp 2 sau gói tách phiên, và cách đóng. Đọc kèm `docs/phien-dang-nhap.md` (cùng kiểu tách tài khoản) và phần 10 của `database/02_trigger_thu_tuc.sql`.

## 1. Lỗ hổng

Trước bản sửa, `r_customer` (tài khoản `app_customer`) có `SELECT, INSERT, UPDATE` trên `accounts_user`. Mọi trang web dùng chung `app_customer`: sách, giỏ, đơn, đánh giá, đăng nhập, đăng ký.

Giả định đã bị xâm nhập (assume breach): chỉ cần **một trang bất kỳ** có lỗi SQL injection, kẻ tấn công có thể:

1. **Tự mở khóa** tài khoản đã bị admin khóa (`UPDATE ... SET is_active = 1`).
2. **Đổi email** của khách khác thành email của mình, rồi dùng "Quên mật khẩu" để chiếm tài khoản.
3. **Đổi mật khẩu** của khách khác thành mã băm do mình tạo.
4. **Tạo tài khoản** đặt sẵn `email_verified = 1` bằng email của người chưa đăng ký. Đây là lỗi chiếm tài khoản trước khi đăng ký (`docs/dang-ky-tai-khoan.md`), chỉ đi đường khác.

Dòng của admin đã được bảo vệ từ trước: trigger chỉ cho `app_customer` đổi `last_login` của nhân viên.

Trigger không tự giải quyết hết được, vì hai lý do:
- Trigger chỉ biết **tài khoản MySQL** nào đang chạy lệnh, không biết **khách nào** đang bấm. Mọi khách dùng chung `app_customer`.
- Đổi mật khẩu là việc hợp lệ, nên không thể cấm hẳn bằng trigger. Một biến đánh dấu kiểu `@bookstore_actor_id` cũng không tin được, vì kẻ tấn công tự gán biến ngay trong câu lệnh chèn vào.

## 2. Cách sửa

| Lớp | Làm gì | Chặn được gì |
|---|---|---|
| `app_customer` chỉ đọc | `r_customer` chỉ còn `SELECT` trên `accounts_user` (`REVOKE IF EXISTS INSERT, UPDATE`). Đăng nhập, `request.user`, kiểm tra trùng email/tên vẫn chạy. | SQL injection ở mọi trang không tạo, không sửa được tài khoản nào (MySQL trả lỗi 1142). Đóng cả 4 điểm ở trên với các trang ngoài nhóm tài khoản. |
| Tài khoản ghi riêng `app_auth` | Role `r_auth` chỉ có `SELECT, INSERT, UPDATE` trên `accounts_user`. `core.db_routers.AccountWriteRouter` đưa **mọi lệnh ghi** model `User` sang kết nối `auth`: đăng ký, `last_login` khi đăng nhập, sửa hồ sơ, đổi/đặt lại mật khẩu, và lần Django tự băm lại mật khẩu lúc đăng nhập. | Chỉ nhóm lệnh ghi tài khoản của Django (ORM, không ghép SQL tay) còn quyền ghi. Lộ mật khẩu `app_auth` cũng không đụng được sách, đơn, phiên, nhật ký. |
| Trigger chặn cột | Với `app_auth` (và `app_customer`, phòng khi cấp nhầm quyền): dòng khách **cấm đổi** `is_active`, `email`, `username`, `email_verified`, `date_joined`; dòng nhân viên chỉ đổi `last_login`; không tạo hay nâng thành nhân viên. | Điểm 1 và 2 bị chặn ở mọi tài khoản ứng dụng, kể cả khi lỗi nằm ngay ở trang tài khoản. Khóa/mở khóa chỉ còn qua thủ tục của admin (`42_account.sql`, kết nối `staff`). |

Trên web, dòng của khách chỉ còn đổi được `password`, `last_login`, `first_name`, `last_name`, `phone_encrypted`. Mình đã kiểm tra: web không có chỗ nào đổi các cột bị cấm (trang hồ sơ chỉ sửa họ, tên, SĐT).

### Còn hở gì

- Nếu chính một trang tài khoản (đăng ký, đăng nhập, hồ sơ, đổi/đặt lại mật khẩu) có lỗi SQL injection thì vẫn đổi được mật khẩu của khách khác. Quyền MySQL không phân biệt được khách nào đang bấm. Diện tấn công đã thu từ cả web xuống còn vài trang, và các trang này chỉ dùng ORM.
- `app_customer` vẫn đọc được mã băm mật khẩu, vì đăng nhập cần đọc nó. Mã băm Argon2 không giải ngược được; kẻ tấn công chỉ có thể đoán rồi so, nên mật khẩu admin phải dài và ngẫu nhiên. Nhóm đã cân nhắc thêm pepper và chốt không làm (2026-11-19).

## 3. Thành phần trong code

- `backend/core/db_routers.py`: `AccountWriteRouter`.
  - Ghi `User` → `settings.AUTH_DB_ALIAS`.
  - Đọc vẫn đi `default`. Đọc hay ghi bảng liên quan (ví dụ lịch sử mật khẩu) của một đối tượng `User` vừa lưu qua `auth` cũng quay về `default`.
  - `allow_relation` cho phép nối đối tượng giữa `default` và `auth`.
- `backend/bookstore/settings/base.py`: kết nối `"auth"` (`DB_AUTH_USER`, `DB_AUTH_PASSWORD`), `AUTH_DB_ALIAS = "auth"`.
- `backend/bookstore/settings/migrate.py`: `AUTH_DB_ALIAS = "default"`, vì test và các lệnh `createsuperuser`, `doi_mat_khau_admin` chạy bằng tài khoản migrate.
- `accounts/services.complete_signup`: `transaction.atomic(using=settings.AUTH_DB_ALIAS)`, để giao dịch nằm trên đúng kết nối ghi.
- `dashboard/services.py` vẫn ghi bằng `save(using="staff")`. `using` ghi rõ thì router không đổi kết nối.
- `db_setup`: role `r_auth`, tài khoản `app_auth` (tối đa 30 kết nối).
- `database/03_phan_quyen.sql`, phần 10 của `database/02_trigger_thu_tuc.sql`.

## 4. Kiểm tra

Kiểm tra tự động:
- `core/tests/test_account_router.py`: ghi `User` đi `auth`, đọc đi `default`, bảng khác không đổi, settings migrate giữ `default`.
- `db_check_grants` (106 kiểm tra, CI chạy trên MySQL thật):
  - `app_customer` tạo tài khoản, sửa `is_active`, đổi mật khẩu → 1142.
  - `app_auth` đọc/ghi `accounts_user` được; xóa tài khoản, đọc `catalog_book`, đọc `django_session`, sửa lịch sử mật khẩu → 1142; gọi thủ tục → 1370.
  - Bốn tài khoản `default`, `staff`, `session`, `auth` phải khác nhau.

`db_check_grants` không thử trigger, vì muốn trigger chạy thì câu lệnh phải sửa dòng thật. Thử tay bằng chính `app_auth`, mỗi câu trong giao dịch rồi `ROLLBACK`. Thay `<id khách>` và `<id admin>` bằng id thật:

```zsh
mysql -h 127.0.0.1 -u app_auth -p bookstore -e "START TRANSACTION; UPDATE accounts_user SET is_active = 1 - is_active WHERE id = <id khách>; ROLLBACK;"
```

| Câu lệnh bằng `app_auth` | Kết quả mong đợi |
|---|---|
| Đổi `is_active`, `email`, `username`, `email_verified` của khách | 1644 `tai khoan ung dung khong duoc doi trang thai, email, ten dang nhap cua khach` |
| Đổi `password` của admin | 1644 `... chi duoc cap nhat last_login cua nhan vien` |
| `SET is_staff = 1` cho khách | 1644 `... khong duoc thay doi is_staff/is_superuser` |
| `INSERT` tài khoản `is_staff = 1` | 1644 `... khong duoc tao tai khoan nhan vien/quan tri` |
| Đổi `first_name`, `last_login`, `password` của khách; đổi `last_login` của admin | chạy được |

Bằng `app_customer`: mọi `UPDATE`/`INSERT` trên `accounts_user` → 1142.

Đã chạy thử trên web: đăng ký 2 bước, đăng nhập (`last_login`), xác thực lại + sửa hồ sơ, đổi mật khẩu (vẫn đăng nhập), quên/đặt lại mật khẩu, admin đăng nhập và vào dashboard. Tất cả đều chạy, không có log `db_permission_denied`.

## 5. Khi triển khai bản này

Thêm `DB_AUTH_USER=app_auth` và `DB_AUTH_PASSWORD` vào `.env`, rồi chạy lại `db_setup`, `migrate`, `db_apply`, `db_check_grants`.

## 6. Bảng khóa đăng nhập django-axes cũng chuyển sang `app_auth` (2026-11-20)

**Lỗ hổng (báo cáo rà soát T3.3):** django-axes ghi/xóa 3 bảng `axes_accessattempt`, `axes_accessattemptexpiration`, `axes_accesslog` (đếm sai, khóa 15 phút, xóa khi đăng nhập đúng/đặt lại mật khẩu/hết hạn) qua kết nối mặc định, nên `r_customer` có `DELETE` trên các bảng đó. SQL injection ở bất kỳ trang nào của khách xóa được trạng thái khóa của mọi tài khoản, kể cả admin → dò mật khẩu không giới hạn. Không thể chỉ thu hồi `DELETE` vì axes cần nó để chạy.

**Cách sửa (giống #44 tách phiên):** `core.db_routers.LockoutRouter` đưa mọi đọc/ghi của app `axes` sang kết nối `auth` (`app_auth`); axes tự mở transaction theo `router.db_for_write`, nên `select_for_update` vẫn nằm đúng transaction. File quyền thu hồi 3 bảng khỏi `r_customer` (`REVOKE IF EXISTS`, gỡ được quyền trên CSDL đã cài) và cấp cho `r_auth`: `SELECT, INSERT, UPDATE, DELETE` trên `axes_accessattempt`, `axes_accessattemptexpiration`; `SELECT, INSERT, UPDATE` trên `axes_accesslog` (không xóa nhật ký). Admin vẫn thấy "Tạm khóa" vì `sp_staff_account_list` đọc qua definer. Test/`settings.migrate` dùng `AUTH_DB_ALIAS = "default"` nên không đổi gì.

**Kiểm tra:** `db_check_grants` thêm 12 dòng (128 tổng): `app_customer`/`app_staff`/`app_session` đọc/xóa bảng axes → 1142; `app_auth` đọc/xóa/ghi → được phép, xóa `axes_accesslog` → 1142. Chạy `db_check_grants` mới trên quyền cũ: 5/128 SAI (4 dòng axes + thanh toán mô phỏng khi cờ tắt). Sandbox (kết nối thật): 5 lần sai → 429, IP khác vẫn đăng nhập được, đăng nhập đúng xóa bộ đếm của IP đó, admin thấy `temp_locked`; `core/tests/test_lockout_router.py`.

**Khi triển khai bản này:** chỉ cần `db_apply` rồi `db_check_grants` (không có biến `.env` mới, không có migration).

