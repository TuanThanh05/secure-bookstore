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
- **Ghi bằng kết nối `auth` (`app_auth`)**, không phải `app_customer` (chỉ còn đọc). Trigger chỉ cho đổi họ, tên, SĐT, mật khẩu, `last_login` của khách; xem `docs/quyen-ghi-tai-khoan.md`.
- **Log** `profile_updated` chỉ ghi tên cột thay đổi (`detail.fields`), không ghi giá trị (không lộ SĐT trong log). Không thay đổi gì thì không ghi log. Loại sự kiện mới được thêm vào CHECK bằng `database/schema/04_...` + migration `core/0005`.
- Nhân viên vào 2 trang này bị chuyển sang trang thông tin quản trị (luồng sửa thông tin admin làm riêng).

## 7. Mã hóa SĐT (`core/crypto.py`) – lỗ hổng CSDL số 10

- **AES-256-GCM** (thư viện `cryptography`): vừa mã hóa vừa có thẻ xác thực, nên dữ liệu bị sửa trong CSDL sẽ bị phát hiện khi giải mã (không trả ra chuỗi rác).
- **Khóa** `FIELD_ENCRYPTION_KEY` (32 byte, base64) trong `.env`, không nằm trong CSDL và không commit. Kẻ lấy được bản sao CSDL (SQL injection, file backup lộ) chỉ thấy chuỗi `v1.<base64>`. Thiếu khóa hoặc khóa sai độ dài → `ImproperlyConfigured`. CI sinh khóa ngẫu nhiên cho mỗi lần chạy.
- **Nonce ngẫu nhiên 12 byte mỗi lần** (`os.urandom`): cùng một số điện thoại mã hóa 2 lần ra 2 chuỗi khác nhau, không so sánh/đoán được.
- **Ngữ cảnh (associated data)** `accounts_user.phone_encrypted:<id>`: bản mã của người A chép sang dòng người B sẽ giải mã thất bại (chống tráo dữ liệu giữa các dòng).
- Định dạng có tiền tố phiên bản `v1.` để sau này đổi thuật toán/khóa vẫn phân biệt được dữ liệu cũ.
- **Mất khóa = mất SĐT đã lưu.** Khóa máy demo phải được sao lưu riêng, an toàn.

## 8. Lịch sử mật khẩu – không dùng lại 5 mật khẩu gần nhất

- **Quy tắc:** mật khẩu mới không được trùng với 5 mật khẩu gần nhất, **tính cả mật khẩu đang dùng**. Áp dụng cho mọi đường đặt mật khẩu: đổi mật khẩu, quên mật khẩu, lệnh `changepassword` (và lệnh đổi mật khẩu admin sau này). Lúc đăng ký thì chưa có lịch sử nên không kiểm tra.
- **Bảng** `accounts_passwordhistory` (trong `database/schema/01_tables.sql`): `user_id`, `password_hash`, `created_at`, khóa ngoại tới `accounts_user` với `ON DELETE CASCADE`.
- **Chia việc giữa CSDL và Django:**

  | Việc | Ai làm | Vì sao |
  | --- | --- | --- |
  | Ghi mã băm mới, xóa bớt để còn 5 dòng | Trigger `trg_pwhist_after_insert` / `trg_pwhist_after_update` (`database/objects/11_...`), chạy bằng quyền `bookstore_definer` | Không sót đường nào, kể cả sửa thẳng bằng SQL. `app_customer` không cần quyền ghi bảng lịch sử |
  | So sánh mật khẩu mới với 5 mã băm | `accounts/validators.PasswordHistoryValidator`, khai báo trong `AUTH_PASSWORD_VALIDATORS` | Mã băm có **muối ngẫu nhiên**: cùng một mật khẩu cho ra chuỗi khác nhau, nên không so chuỗi băm được. Phải gọi `check_password(mật khẩu mới, mã băm cũ)`, mà chỉ Django có mật khẩu gốc |

- **Quyền tối thiểu:** `r_customer` chỉ có `SELECT` trên bảng lịch sử. Mức lộ không tăng vì `r_customer` vốn đã đọc được `accounts_user.password` để kiểm tra đăng nhập. Kẻ tấn công có SQL injection cũng không xóa được lịch sử để quay lại dùng mật khẩu cũ (thử INSERT/UPDATE/DELETE bằng `app_customer` đều bị MySQL từ chối, lỗi 1142).
- **Thông báo lỗi chung:** "Mật khẩu này trùng với một trong 5 mật khẩu gần nhất…", không nói trùng lần thứ mấy.
- **Dự phòng:** nếu bảng lịch sử chưa có dòng nào (ví dụ CSDL test không có trigger), validator vẫn so với mật khẩu đang dùng trong `accounts_user`.
- **Thời gian:** mỗi lần đổi băm thử tối đa 5 lần (PBKDF2), khoảng nửa giây. Chấp nhận được vì chỉ người đã đăng nhập hoặc có link đặt lại mới tới bước này.
- **Đánh đổi đã biết:** khi nâng cấp Django tăng số vòng băm, Django tự băm lại mật khẩu của khách lúc đăng nhập. Cột `password` đổi dù mật khẩu không đổi, trigger ghi thêm một dòng trùng, nên lịch sử thực tế ngắn đi một mật khẩu. Hiếm gặp, chấp nhận.
- Số 5 xuất hiện ở hai chỗ phải khớp nhau: `OPTIONS history_count` trong `settings/base.py` và `OFFSET 4` trong trigger.
- **Kiểm thử:** `accounts/tests/test_password_history.py` (7 test). Trigger chỉ kiểm tra được trên CSDL thật vì CSDL test không có trigger: đăng ký 1 dòng, đổi 6 lần còn 5 dòng, sửa cột khác không thêm dòng.

## 8b. Quy tắc mật khẩu và độ dài tối đa 64 ký tự

`AUTH_PASSWORD_VALIDATORS` (`settings/base.py`) có 6 quy tắc. Cả 4 chỗ đặt mật khẩu đều kiểm tra đủ: đăng ký bước 2, đổi mật khẩu, đặt lại mật khẩu, lệnh `doi_mat_khau_admin`.

| Quy tắc | Chặn gì |
|---|---|
| `UserAttributeSimilarityValidator` | Mật khẩu giống tên đăng nhập, email, họ tên |
| `MinimumLengthValidator` (12) | Ngắn hơn 12 ký tự |
| `accounts.validators.MaximumLengthValidator` (64) | Dài hơn 64 ký tự |
| `CommonPasswordValidator` | Khoảng 20.000 mật khẩu phổ biến có sẵn trong Django |
| `NumericPasswordValidator` | Toàn chữ số |
| `PasswordHistoryValidator` (5) | Trùng 5 mật khẩu gần nhất (mục 8) |

**Vì sao có giới hạn tối đa:**
- Mỗi lần kiểm tra mật khẩu là một lần băm Argon2, vốn được thiết kế cho chậm. Không có giới hạn thì kẻ tấn công gửi mật khẩu dài hàng trăm nghìn ký tự để máy chủ tốn công băm, một dạng từ chối dịch vụ.
- Chọn **64** vì đó là mức NIST SP 800-63B yêu cầu phải cho phép tối thiểu. Mức này vẫn đủ chỗ cho mật khẩu do trình quản lý mật khẩu sinh ra và cho cụm mật khẩu dài.
- Nhóm đã cân nhắc 20 ký tự và bỏ (2026-11-20), vì mức đó chặn đúng kiểu mật khẩu mạnh nhất.

**Vì sao chặn cả ở form, không chỉ ở validator:**
- Validator chỉ chạy khi **đặt** mật khẩu, và Django chạy **mọi** validator rồi mới gộp lỗi. `PasswordHistoryValidator` vẫn băm chuỗi dài để so với 5 mã băm cũ.
- Trang đăng nhập và xác thực lại không chạy validator nào, mà gọi thẳng `authenticate()`, tức là băm luôn.
- Vì vậy `accounts.forms.cap_password_fields` gắn giới hạn 64 vào **mọi ô mật khẩu**: đăng nhập, xác thực lại (khách và admin, kể cả form khóa/mở khóa tài khoản), đăng ký, đổi mật khẩu (cả ô mật khẩu hiện tại), đặt lại mật khẩu (`CustomerSetPasswordForm`).
- Quá 64 ký tự thì form báo lỗi ngay, không gọi `authenticate()`, `check_password()` hay validator, nên không băm gì cả. Thuộc tính `maxlength` trên ô nhập chỉ để người dùng đỡ gõ thừa; lớp chặn thật nằm ở form.
- Lần nhập quá dài không bị axes tính là một lần sai. Điều này không mở đường dò mật khẩu, vì không có mật khẩu hợp lệ nào dài hơn 64 ký tự.

**Không có** quy tắc bắt buộc chữ hoa, chữ số, ký tự đặc biệt. NIST khuyên dùng độ dài và danh sách chặn thay vì bắt trộn ký tự, vì bắt trộn thì người dùng đặt kiểu `Password1!`.

**Kiểm thử:** `accounts/tests/test_password_max_length.py`:
- 64 ký tự thì đăng nhập được, 65 thì bị chặn ở từng form.
- Dùng mock để chắc chắn `authenticate()` và `validate_password()` không được gọi.
- Tắt `cap_password_fields` thì 5 test báo lỗi.

**Khi áp dụng:** tài khoản nào đang có mật khẩu dài hơn 64 ký tự sẽ không đăng nhập được nữa. Khách thì dùng "Quên mật khẩu"; admin thì dùng lệnh `doi_mat_khau_admin`.

## 9. Đổi mật khẩu quản trị viên – chỉ trên máy chủ

```bash
cd backend
python manage.py doi_mat_khau_admin <tên đăng nhập> --settings=bookstore.settings.migrate
```

- **Trên web không có đường nào đổi được mật khẩu nhân viên.** Không có nút đổi, không có quên mật khẩu (trang quên mật khẩu và đổi mật khẩu của khách đều loại nhân viên), project không bật `django.contrib.admin`. Kẻ chiếm được phiên, biết mật khẩu hoặc đọc trộm được hộp thư cũng không đổi được mật khẩu admin qua web. Đây là nguyên tắc **khôi phục tài khoản quyền cao qua kênh ngoài**: chỉ người vào được máy chủ và có mật khẩu tài khoản `bookstore_migrate` mới làm được.
- **Lệnh làm gì** (`accounts/management/commands/doi_mat_khau_admin.py`):
  1. Từ chối nếu đang chạy bằng tài khoản web (`app_customer`/`app_staff`), trước khi hỏi mật khẩu.
  2. Chỉ nhận tài khoản `is_staff`; tên khách hoặc tên không tồn tại đều bị từ chối.
  3. Hỏi mật khẩu 2 lần bằng `getpass` (không hiện trên màn hình, không lưu vào lịch sử terminal), kiểm tra đủ `AUTH_PASSWORD_VALIDATORS`, kể cả **không trùng 5 mật khẩu gần nhất**. Sai 3 lần thì dừng, mật khẩu giữ nguyên.
  4. Lưu bằng `save(update_fields=["password"])`; trigger ghi lịch sử mật khẩu như mọi lần đổi khác.
  5. **Xóa mọi phiên đang mở của nhân viên đó** ngay lập tức (phiên của người khác giữ nguyên). Kể cả không xóa, Django cũng tự hủy phiên cũ ở request tiếp theo vì mã băm mật khẩu lưu trong phiên không còn khớp.
  6. Ghi log `password_changed` với `ip_address = cli`, `detail = {"via": "cli", "sessions_ended": n}`.
  7. Gửi thư báo tới email gốc, **không kèm link nào** (không có gì để bấm vào trên web).
- **Email gốc phải là email thật**: kiểm tra email của tài khoản admin sau `createsuperuser`.
- Trang thông tin quản trị ghi "Không thể đổi mật khẩu". Đây chỉ là lớp gây nhiễu, **không tính là biện pháp bảo mật**; biện pháp thật là không có đường đổi trên web.
- **Kiểm thử:** `accounts/tests/test_admin_password_command.py` (9 test).

## 10. Cập nhật thông tin của quản trị viên (họ, tên, SĐT)

- **Luồng:** trang Thông tin tài khoản → nút "Cập nhật thông tin" (`/dashboard/thong-tin/cap-nhat/`) → xác thực lại loại của admin (`dashboard:reauth`, 2 phút) → sửa → lưu. Cả GET lẫn POST đều cần xác thực lại còn hạn.
- **Chỉ sửa họ, tên, SĐT**, giống khách (`dashboard/forms.StaffProfileUpdateForm` kế thừa form của khách, cùng quy tắc kiểm tra). Gửi thêm `email`, `username`, `is_superuser` trong request đều bị bỏ qua.
- **Không bao giờ hiện SĐT hiện tại:** ô SĐT luôn trống, để trống nghĩa là giữ số cũ. Trang sửa cũng không hiện email. Khớp với việc email/SĐT của admin luôn bị ẩn và chỉ hiện qua trang xem có ghi log `sensitive_data_viewed`.
- **Ghi bằng kết nối `staff` (`app_staff`), không phải `default`:** trigger `trg_user_guard_update` chặn `app_customer` sửa dòng nhân viên. Hai lớp ở CSDL:

  | Lớp | Cách làm | Chặn được |
  | --- | --- | --- |
  | Quyền theo cột (`grants/01_...`) | `GRANT SELECT (id), UPDATE (first_name, last_name, phone_encrypted) ON accounts_user TO r_staff` | `app_staff` đổi mật khẩu, email, `is_staff`, `is_superuser`, hay đọc email: MySQL từ chối, lỗi 1143 |
  | Trigger (`objects/10_...`) | `app_staff` sửa dòng có `is_staff = 0` → `SIGNAL` | `app_staff` sửa tên/SĐT của khách: lỗi 1644 |

  Django lưu bằng `save(using="staff", update_fields=[...])` nên câu UPDATE chỉ chứa đúng các cột đã đổi.
- **Đánh đổi đã biết:** ở lớp CSDL, `app_staff` vẫn sửa được tên/SĐT của admin khác (MySQL không biết admin nào đang dùng web). Lớp Django chặn việc này: view chỉ sửa `request.user`, không nhận id từ request.
- **Log** `profile_updated` chỉ ghi tên cột, không ghi giá trị. Không đổi gì thì không ghi.
- **Kiểm thử:** `dashboard/tests/test_profile_update.py` (10 test). Trong test, kết nối `staff` là kết nối riêng nên sẽ chờ khóa của transaction test; test kiểm tra code gọi `using="staff"` rồi cho ghi qua `default`. Quyền theo cột và trigger được kiểm tra trên CSDL thật (bảng trên).
