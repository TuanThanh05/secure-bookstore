# Phiên đăng nhập: tách tài khoản, băm khóa, giới hạn phiên admin

Tài liệu này giải thích phát hiện số 13 và cách sửa. Đọc kèm `docs/nhat-ky-he-thong.md` (log) và `database/grants/01_role_privileges.sql` (quyền).

## 1. Phát hiện số 13: chiếm phiên admin qua lớp 2

Trước bản sửa:

- Django lưu mọi phiên, kể cả phiên admin, trong bảng `django_session` qua kết nối `default` (tài khoản `app_customer`).
- Cột `session_key` chính là giá trị cookie `bs_sid`.
- `session_data` chỉ là JSON nén rồi base64, có chữ ký bằng `SECRET_KEY`. Chữ ký không gắn với dòng, nên chép `session_data` sang dòng khác vẫn hợp lệ.
- `r_customer` có cả SELECT, INSERT, UPDATE, DELETE trên bảng này.

Giả định: kẻ tấn công đã vượt lớp 1 (ví dụ một lỗi SQL injection trong code dùng `app_customer`). Cách làm này gọi là giả định đã bị xâm nhập (assume breach). Khi đó:

1. Chỉ một câu SELECT kiểu `UNION` là đủ đọc `session_key` của admin.
2. Kẻ tấn công đặt giá trị đó làm cookie `bs_sid` và Django nhận họ là admin.
3. Họ có thể dùng UPDATE để kéo dài hạn phiên, hoặc chép dữ liệu phiên admin sang phiên của mình.

Từ quyền khách hàng, kẻ tấn công leo lên quyền quản trị.

## 2. Cách sửa: ba lớp

| Lớp | Làm gì | Chặn được gì |
|---|---|---|
| Tách tài khoản `app_session` | Bảng phiên chỉ đọc/ghi được bằng kết nối `session` (tài khoản `app_session`, role `r_session`). `r_customer` bị thu hồi mọi quyền trên `django_session`. | SQL injection qua `app_customer` hay `app_staff` không đọc, không sửa được bảng phiên (MySQL trả lỗi 1142). |
| Băm khóa phiên, chữ ký gắn với dòng | Bảng chỉ lưu `sha256(cookie)` (40 ký tự đầu). Chữ ký `session_data` có muối chứa chính mã băm của dòng. | Lộ cả mật khẩu `app_session` và đọc được bảng: mã băm không dùng làm cookie được. Chép `session_data` sang dòng khác thì chữ ký sai và phiên thành rỗng (ẩn danh). |
| Phiên nhân viên tối đa 1 giờ | Lúc nhân viên đăng nhập, ghi giờ vào phiên (`staff_login_at`, nằm trong phần đã ký). Middleware kiểm tra mỗi request. | Cookie admin bị lộ cách khác (máy bị chiếm, trình duyệt) chỉ dùng được tối đa 1 giờ kể từ lúc đăng nhập, dù vẫn có thao tác. |

Thời hạn 30 phút không thao tác (`SESSION_COOKIE_AGE`) vẫn giữ cho mọi người. Khách hàng không bị giới hạn 1 giờ. Không ràng buộc phiên với IP hay trình duyệt.

### Còn hở gì

- Cookie trong trình duyệt bị lộ (mã độc trên máy, XSS) thì vẫn dùng được cho tới khi hết phiên. Các lớp khác hạn chế việc này: `HttpOnly`, CSP không cho JS inline, hỏi lại mật khẩu trước thao tác nguy hiểm, hạn 30 phút, và 1 giờ với admin.
- Lộ `SECRET_KEY` thì kẻ tấn công tự ký được dữ liệu phiên. Khóa này không bao giờ nằm trong CSDL hay repo.

## 3. Thành phần trong code

- `backend/core/session_store.py`: `SessionStore` (dùng qua `SESSION_ENGINE = "core.session_store"`), `stored_key(cookie)`, và `SessionStore.decode_row(session)` để đọc một dòng lấy thẳng từ bảng (lệnh `doi_mat_khau_admin` dùng hàm này; `Session.get_decoded()` giờ trả `{}`).
- `backend/core/db_routers.py`: `SessionRouter` đưa model của app `sessions` sang `settings.SESSION_DB_ALIAS`.
  - Web dùng `"session"`.
  - `settings/migrate.py` (test, lệnh quản trị) dùng `"default"`, vì `TestCase` không cho truy vấn qua alias khác `default`.
- `backend/core/middleware.py`: `remember_staff_login` (signal `user_logged_in`) và `StaffSessionLimitMiddleware`.
  - Khi quá giờ, middleware đăng xuất, hiện thông báo và chuyển về trang đăng nhập.
  - Log ghi `logout` với `detail.reason = "absolute_timeout"`.
  - Thiếu giờ đăng nhập, hoặc giờ đăng nhập nằm ở tương lai, cũng bị coi là hết hạn.
- `backend/bookstore/settings/base.py`: kết nối `"session"`, `SESSION_DB_ALIAS`, `SESSION_ENGINE`, `STAFF_SESSION_MAX_AGE = 3600`.
- `db_setup` tạo role `r_session` và tài khoản `app_session` (tối đa 50 kết nối, mật khẩu `DB_SESSION_PASSWORD`).
- `database/grants/01_role_privileges.sql`: `REVOKE IF EXISTS` với `r_customer`, `GRANT` 4 quyền trên `django_session` cho `r_session`.

## 4. Kiểm tra

Kiểm tra tự động:

- `core/tests/test_session_store.py`: bảng chỉ có mã băm; dùng mã băm làm cookie bị từ chối; chép `session_data` bị từ chối; giới hạn 1 giờ; khách không bị giới hạn.
- `db_check_grants` (CI chạy trên MySQL thật):
  - `app_customer` và `app_staff` đọc/sửa/xóa `django_session` → 1142.
  - `app_session` chỉ có bảng phiên: đọc `accounts_user` → 1142; gọi thủ tục → 1370.
  - Ba tài khoản phải khác nhau.

Thử tay trên máy (sau khi đăng nhập admin ở trình duyệt):

```sql
-- bằng root: chỉ thấy mã băm 40 ký tự, không khớp cookie bs_sid trong trình duyệt
SELECT session_key, expire_date FROM django_session;
```

```zsh
# bằng app_customer: phải ra lỗi 1142
mysql -h 127.0.0.1 -u app_customer -p bookstore -e "SELECT session_key FROM django_session"
```

## 5. Khi triển khai bản này

- Thêm `DB_SESSION_PASSWORD` (và `DB_SESSION_USER=app_session`) vào `.env`, rồi chạy lại `db_setup`, `migrate`, `db_apply`, `db_check_grants`.
- Các phiên cũ (lưu theo cookie gốc) không còn khớp nữa, nên mọi người phải đăng nhập lại một lần. Có thể xóa bảng phiên cũ bằng root: `DELETE FROM django_session;`
