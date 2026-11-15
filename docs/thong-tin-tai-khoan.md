# Trang thông tin tài khoản: khách hàng và quản trị viên

Tài liệu giải thích thiết kế bảo mật của 2 trang:

- `accounts:profile` (`/account/profile/`): trang của khách hàng.
- `dashboard:profile` (`/dashboard/thong-tin/`): trang của nhân viên/quản trị viên.

Hai trang hiện cùng các trường (họ, tên, tên đăng nhập, email, số điện thoại, ngày tham gia), nhưng **cách xử lý email và số điện thoại khác nhau**.

## 1. Vì sao tách 2 view thay vì dùng chung

| | Khách hàng | Quản trị viên |
| --- | --- | --- |
| View | `accounts.views.profile` | `dashboard.views.profile`, `dashboard.views.profile_contact` |
| Quyền vào | `@login_required`; nhân viên bị chuyển sang trang quản trị | `@staff_required`; khách nhận 403 |
| Email, SĐT | Hiện đầy đủ (dữ liệu của chính mình) | **Mặc định không gửi xuống trình duyệt**; chỉ hiện sau khi xác thực lại |

Nhân viên vào `/account/profile/` bị chuyển sang `/dashboard/thong-tin/`. Nếu không chuyển, trang của khách sẽ trở thành "cửa sau" để xem email của quản trị viên mà không cần xác thực lại.

## 2. Vì sao giấu email và SĐT của quản trị viên

Tài khoản quản trị viên là mục tiêu giá trị nhất của kẻ tấn công. Email của quản trị viên dùng được để:

- dò mật khẩu hoặc gửi thư lừa đảo nhắm thẳng vào người đó (spear phishing);
- đặt lại mật khẩu, nếu sau này có chức năng quên mật khẩu.

Rủi ro thực tế là **phiên đăng nhập bị chiếm**: quản trị viên quên đăng xuất ở máy dùng chung, hoặc cookie phiên bị đánh cắp. Khi đó kẻ tấn công vào thẳng trang thông tin. Giấu email/SĐT sau bước xác thực lại nghĩa là **chỉ có phiên đăng nhập thôi chưa đủ**, phải biết cả mật khẩu.

## 3. Cách làm

1. **Không gửi dữ liệu xuống trình duyệt.** Trang mặc định chỉ có `••••••••••`. Email không có trong HTML, cũng không nằm trong thuộc tính ẩn hay JavaScript, nên "Xem nguồn trang" hay DevTools cũng không thấy. Đây là khác biệt với kiểu ẩn bằng CSS/JS, vốn chỉ che mắt.
2. **Nút con mắt là một link** tới `dashboard:profile_contact` (`/dashboard/thong-tin/lien-he/`), không phải nút JavaScript. View này có `@recent_auth_required`:
   - chưa xác thực lại trong `REAUTH_MAX_AGE` (2 phút) → chuyển tới `dashboard:reauth?next=...`;
   - nhập đúng tên đăng nhập + mật khẩu **của chính mình** → quay lại, trang hiện email/SĐT.
3. **Xác thực lại đi qua `authenticate()`**, nên nhập sai cũng bị axes đếm (khóa sau 5 lần) và ghi `login_failed`. Nhập đúng tài khoản của nhân viên khác thì bị từ chối và ghi `access_denied` (`user_mismatch`).
4. **Ghi log mỗi lần xem**: sự kiện `sensitive_data_viewed` với `detail = {"fields": ["email", "phone"], "owner": "self"}`. Loại sự kiện mới được thêm vào CHECK `ck_secevent_type` bằng `database/schema/03_securityevent_sensitive_view.sql` + migration `core/0004`.
5. **Không lưu cache** (`@never_cache` → `Cache-Control: no-store`) cho cả 2 trang. Nếu không, sau khi rời máy, người khác bấm Back vẫn thấy trang đã hiện email lấy từ bộ nhớ đệm của trình duyệt.
6. **Trang thường luôn giấu**: kể cả vừa xác thực lại xong, `/dashboard/thong-tin/` vẫn giấu. Chỉ trang `/lien-he/` mới hiện, nên dữ liệu không vô tình xuất hiện ở lần tải trang sau.

## 4. Đánh đổi đã biết

- **Một lần xác thực lại dùng chung 2 phút** cho mọi khu vực nhạy cảm (Quản lý tài khoản, xem email/SĐT). Mục đích của xác thực lại là chứng minh "đúng người đang ngồi trước máy", nên dùng chung là hợp lý và đỡ phiền.
- Quản trị viên phải nhập lại mật khẩu mỗi khi muốn xem email của chính mình. Nhóm chấp nhận sự phiền này, vì đây là dữ liệu nhạy cảm của tài khoản quyền cao nhất.
- Số điện thoại được giải mã bằng `core/crypto.py` (xem mục 6). Dữ liệu hỏng hoặc sai khóa thì trang ghi "Không đọc được…" thay vì báo lỗi 500.
- Thanh menu trái tô sáng "Quản lý tài khoản" khi đang ở trang xác thực lại, kể cả khi xác thực lại để xem thông tin cá nhân.

## 5. Kiểm thử

- `accounts/tests/test_profile.py`: khách thấy email/tên của mình; chưa đăng nhập → trang đăng nhập; nhân viên bị chuyển sang trang quản trị; có `no-store`; POST → 405.
- `dashboard/tests/test_profile.py`:
  - email không có trong HTML trang thường, kể cả sau khi xác thực lại;
  - khách nhận 403;
  - `/lien-he/` chưa xác thực lại → chuyển tới trang xác thực lại;
  - xác thực đúng → hiện email + ghi `sensitive_data_viewed`;
  - quá 2 phút, sai mật khẩu, hoặc xác thực bằng tài khoản người khác → không hiện;
  - trang xác thực lại ghi thời hạn lấy từ settings.

## 6. Cập nhật thông tin của khách (họ, tên, SĐT)

Luồng: trang Thông tin tài khoản → nút **Cập nhật thông tin** → nếu chưa xác thực lại trong `REAUTH_MAX_AGE` (2 phút) thì chuyển tới **trang xác thực lại riêng của khách** `accounts:reauth` (`/account/xac-thuc-lai/`) → nhập tên đăng nhập (hoặc email) + mật khẩu → quay về form `accounts:profile_update` (`/account/cap-nhat/`).

- **Trang xác thực lại tách riêng khỏi trang của admin** (`accounts/decorators.customer_recent_auth_required`, view `accounts.views.reauth`), cùng cơ chế lưu mốc thời gian trong session của `core/decorators.py`. Bên dưới nút "Xác thực" có link **Quên mật khẩu?**. Nhập sai bị axes đếm; nhập đúng tài khoản người khác bị từ chối và ghi `access_denied`. Tham số `next` chỉ được trỏ trong site.
- **Chỉ sửa được họ, tên, SĐT.** Form là `forms.Form` liệt kê 3 ô (không phải `ModelForm`), service `update_profile` chỉ gán đúng 3 cột và lưu bằng `save(update_fields=...)`. Gửi thêm `username`, `email`, `is_staff` trong request cũng bị bỏ qua (chống mass assignment).
- **Kiểm tra đầu vào ở server:** họ/tên tối đa 50 ký tự, chỉ chữ cái (có dấu), khoảng trắng, `-`, `'`; SĐT Việt Nam 10 số bắt đầu 03/05/07/08/09, chấp nhận dấu cách, dấu chấm, `+84` rồi chuẩn hóa về dạng `09xxxxxxxx`.
- **Cả GET lẫn POST** đều cần xác thực lại còn hạn: để quá 2 phút rồi mới bấm Lưu thì bị chuyển sang trang xác thực lại, dữ liệu không được lưu.
- **Log** `profile_updated` chỉ ghi tên cột thay đổi (`detail.fields`), không ghi giá trị (không lộ SĐT trong log). Không thay đổi gì thì không ghi log. Loại sự kiện mới được thêm vào CHECK bằng `database/schema/04_...` + migration `core/0005`.
- Nhân viên vào 2 trang này bị chuyển sang trang thông tin quản trị (luồng sửa thông tin admin làm riêng).

## 7. Mã hóa SĐT (`core/crypto.py`) – lỗ hổng CSDL số 10

- **AES-256-GCM** (thư viện `cryptography`): vừa mã hóa vừa có thẻ xác thực, nên dữ liệu bị sửa trong CSDL sẽ bị phát hiện khi giải mã (không trả ra chuỗi rác).
- **Khóa** `FIELD_ENCRYPTION_KEY` (32 byte, base64) trong `.env`, không nằm trong CSDL và không commit. Kẻ lấy được bản sao CSDL (SQL injection, file backup lộ) chỉ thấy chuỗi `v1.<base64>`. Thiếu khóa hoặc khóa sai độ dài → `ImproperlyConfigured`. CI sinh khóa ngẫu nhiên cho mỗi lần chạy.
- **Nonce ngẫu nhiên 12 byte mỗi lần** (`os.urandom`): cùng một số điện thoại mã hóa 2 lần ra 2 chuỗi khác nhau, không so sánh/đoán được.
- **Ngữ cảnh (associated data)** `accounts_user.phone_encrypted:<id>`: bản mã của người A chép sang dòng người B sẽ giải mã thất bại (chống tráo dữ liệu giữa các dòng).
- Định dạng có tiền tố phiên bản `v1.` để sau này đổi thuật toán/khóa vẫn phân biệt được dữ liệu cũ.
- **Mất khóa = mất SĐT đã lưu.** Khóa máy demo phải được sao lưu riêng, an toàn.
