# Xác thực 2 bước bằng Google Authenticator (TOTP)

Đăng nhập cần hai thứ: **mật khẩu** (thứ bạn biết) và **mã 6 số trong ứng dụng trên điện thoại** (thứ bạn có). Lộ mật khẩu mà không có điện thoại thì vẫn không vào được.

Mã 6 số theo chuẩn TOTP (RFC 6238): điện thoại và máy chủ cùng giữ một chuỗi bí mật, cứ 30 giây cùng tính ra một mã mới từ chuỗi đó và giờ hiện tại. Mã chạy cả khi điện thoại không có mạng. Dùng được Google Authenticator, Microsoft Authenticator, Aegis…

## 1. Ai phải dùng

| Đối tượng | Quy tắc |
|---|---|
| **Admin** | **Luôn bắt buộc**. Cài ngay khi tạo admin bằng lệnh `tao_admin` trên máy chủ. Không có nút tắt trên web. Admin chưa cài thì không đăng nhập được trên web. |
| **Khách** | **Tự chọn**: nút "Bật xác thực 2 bước" ở trang Thông tin tài khoản. |

**Vì sao admin chỉ cài bằng lệnh trên máy chủ, không cài trên web lúc đăng nhập lần đầu:** nếu cho cài trên web, kẻ đã trộm được mật khẩu admin trước đó sẽ quét QR bằng **điện thoại của hắn**, và 2 bước trở thành của hắn. Lệnh trên máy chủ cần quyền vào máy chủ và tài khoản MySQL `bookstore_migrate`, cùng cách làm với `doi_mat_khau_admin`.

## 2. Các luồng

**Đăng nhập (khi cần 2 bước):**
1. Nhập mật khẩu đúng.
   - Lúc này **chưa đăng nhập**; phiên chỉ ghi "đã qua bước 1" và đổi session ID.
   - Mọi trang cần đăng nhập vẫn chuyển về trang đăng nhập.
2. Nhập mã 6 số trong vòng **5 phút**. Khách có thể nhập một **mã dự phòng** thay cho mã 6 số.
3. Đúng thì mới gọi `login()`. Lúc này session ID đổi lần nữa, và giờ đăng nhập để tính giới hạn 1 giờ của admin bắt đầu.

**Khách bật** (Thông tin tài khoản → Bật xác thực 2 bước):
1. Nhập lại mật khẩu (xác thực lại).
2. Trang hiện mã QR và chuỗi bí mật để gõ tay nếu không quét được. Lượt cài có hạn **10 phút**.
3. Nhập mã 6 số đang hiện trong ứng dụng. Mã đúng thì mới bật thật, để chắc chắn khách đã quét đúng.
4. Hiện **5 mã dự phòng đúng một lần**, kèm nút **Sao chép** và **Tải xuống** (file `key-secure-bookstore.txt`). Hệ thống gửi thư báo "đã BẬT".

**Khách tắt:** nhập mật khẩu hiện tại **và** mã 6 số (hoặc một mã dự phòng). Thiết bị và mọi mã dự phòng bị xóa, hệ thống gửi thư báo "đã TẮT".

**Mất điện thoại:**

| Đối tượng | Còn mã dự phòng | Mất cả mã dự phòng |
|---|---|---|
| Khách | Đăng nhập bằng một mã dự phòng (có thư báo), rồi tắt và bật lại để nhận bộ mã mới | Không khôi phục được. Admin chỉ hỗ trợ **khóa tài khoản** (chốt 2026-11-20) |
| Admin | (admin không có mã dự phòng) | Chạy `dat_lai_2fa_admin` trên máy chủ: gỡ thiết bị cũ, quét QR mới, đăng xuất mọi phiên, có log và thư báo |

## 3. Luật bảo mật đã áp dụng

**Chuỗi bí mật:**
- 160 bit ngẫu nhiên (`pyotp.random_base32(32)`).
- Lưu **mã hóa AES-GCM** (`core/crypto.py`). Ngữ cảnh mã hóa gắn với `user_id`, nên chép bản mã sang dòng của người khác thì không giải mã được.
- Nằm ở **bảng riêng** `accounts_totpdevice`. Chỉ `app_auth` có quyền; `app_customer`, `app_staff`, `app_session` đọc là bị lỗi 1142. SQL injection ở trang sách, giỏ hay đơn không lấy được chuỗi bí mật.

**Mã 6 số:**
- So sánh hằng thời gian (`hmac.compare_digest`).
- Chấp nhận lệch **±1 bước (±30 giây)** cho đồng hồ điện thoại. Lệch 3 bước trở lên là bị từ chối.
- **Mỗi mã chỉ dùng được một lần.** Cột `last_used_step` lưu bước thời gian vừa dùng; câu `UPDATE ... WHERE last_used_step < bước` có điều kiện, nên kẻ nhìn trộm mã không dùng lại được, và hai request gửi cùng lúc thì chỉ một cái qua.
- Trigger cấm lùi `last_used_step`.

**Mã dự phòng:**
- 5 mã dạng `XXXXX-XXXXX`, mỗi mã 50 bit. Bộ ký tự bỏ `0/O`, `1/I` cho đỡ nhầm.
- Chỉ lưu **mã băm Argon2**, mỗi mã dùng một lần (UPDATE có điều kiện).
- Trigger chỉ cho đánh dấu "đã dùng" một chiều.
- Dùng một mã là có thư báo và log `two_factor_recovery_used`.

**Chống dò mã:**
- Sai **5 lần** trong một lượt thì hủy lượt, phải nhập lại mật khẩu.
- Sai **10 lần trong 1 giờ** trên một tài khoản thì tạm chặn bước 2 của tài khoản đó, kể cả khi nhập đúng mật khẩu.
- Mỗi lần sai ghi log `otp_failed`.
- Mật khẩu sai vẫn do axes đếm như cũ.

**Trang QR:**
- Không lưu cache (`never_cache`), có CSP `default-src 'none'`.
- Ảnh lấy từ URL riêng (`/account/xac-thuc-2-buoc/ma-qr.svg`), không nhúng SVG bằng `|safe`.
- Chỉ xem được khi đang cài; bật xong thì trả 404.
- Trang cài cần xác thực lại.

**Trang mã dự phòng:**
- Hiện trong chính phản hồi của lần xác nhận, không lưu mã dạng chữ ở đâu cả (kể cả phiên); không cache.
- **Tải xuống** là link `data:text/plain` với thuộc tính `download`: không cần JS và không cần `blob:`, nên CSP vẫn giữ nguyên.
- **Sao chép** dùng file `static/js/copy-codes.js` (không JS inline). Clipboard API chỉ chạy trên HTTPS hoặc `localhost`; không chạy được thì nút ẩn đi, người dùng chép tay hoặc tải file.

**Bảo vệ 2 bước của admin ở lớp CSDL** (trigger phần 12 của `database/02_trigger_thu_tuc.sql`):
- `app_auth` không tạo, không xóa, không đổi chuỗi bí mật trong thiết bị của nhân viên; chỉ được **tăng** `last_used_step` lúc admin đăng nhập.
- `app_auth` không tạo mã dự phòng cho nhân viên.
- Vì vậy SQL injection ở trang tài khoản cũng không thay được Google Authenticator của admin.

**Thư báo:** bật, tắt, dùng mã dự phòng, cài lại 2 bước cho admin.

## 4. Lệnh trên máy chủ

Tạo admin duy nhất kèm 2 bước. Lệnh từ chối nếu đã có tài khoản nhân viên:
```zsh
python manage.py tao_admin <tên đăng nhập> <email thật> --settings=bookstore.settings.migrate
```
- Hỏi mật khẩu hai lần (đủ 6 quy tắc mật khẩu).
- In mã QR ra terminal kèm chuỗi bí mật, rồi hỏi mã 6 số.
- Sai mã 3 lần thì **không tạo gì cả** (giao dịch quay lui).

Cài lại 2 bước cho admin (mất hoặc đổi điện thoại):
```zsh
python manage.py dat_lai_2fa_admin <tên đăng nhập> --settings=bookstore.settings.migrate
```

Cả hai lệnh từ chối chạy bằng tài khoản web (`app_customer`, `app_staff`, `app_auth`, `app_session`).

**Đã có admin cũ (tạo bằng `createsuperuser`)?** Chạy `dat_lai_2fa_admin` cho admin đó là xong. Nếu muốn tạo admin mới bằng `tao_admin`, phải xóa admin cũ trước bằng root.

## 5. Máy chủ phải đúng giờ

Mã tính từ giờ hiện tại. Máy chủ lệch giờ quá 30 giây thì **mọi mã đều sai**. Bật đồng bộ giờ:
```zsh
sudo timedatectl set-ntp true
```
Container MySQL không ảnh hưởng, vì mã được tính trong Django.

## 6. Thành phần trong code

**CSDL:**
- `database/01_bang.sql` + migration `core/0001`: 2 bảng, thêm 3 loại log `two_factor_enabled`, `two_factor_disabled`, `two_factor_recovery_used`. Mã sai dùng loại có sẵn `otp_failed`.
- phần 12 của `database/02_trigger_thu_tuc.sql` (trigger), quyền trong `database/03_phan_quyen.sql`.

**Django:**
- `accounts/models.py` (`TotpDevice`, `RecoveryCode`, `managed = False`, migration `accounts/0003`).
- `core.db_routers.TwoFactorRouter`: đọc và ghi 2 bảng này qua kết nối `auth`.
- `accounts/two_factor.py`: service.
- `accounts/views.py`: `SecureLoginView`, `login_two_factor`, `two_factor_setup`, `two_factor_qr`, `two_factor_disable`.
- Lệnh: `accounts/management/commands/tao_admin.py`, `dat_lai_2fa_admin.py`, `_two_factor_cli.py`.
- Thư viện: `pyotp` (tính mã TOTP), `segno` (vẽ mã QR, không phụ thuộc thư viện nào khác).

**Không làm:**
- "Ghi nhớ thiết bị này".
- Bắt nhập mã 2 bước khi xác thực lại trước thao tác nhạy cảm (vẫn chỉ hỏi mật khẩu).
- Khôi phục cho khách mất cả điện thoại lẫn mã dự phòng.

## 7. Kiểm tra

**Tự động** (`accounts/tests/test_two_factor.py`, 28 test):
- Service: mã đúng chỉ dùng một lần; lệch 1 bước được, lệch 3 bước bị từ chối; chuỗi bí mật mã hóa gắn với người dùng; mã dự phòng lưu băm và chỉ dùng một lần.
- Luồng đăng nhập: đúng mật khẩu chưa phải đăng nhập, session ID đổi; sai 5 lần thì hủy lượt; hết hạn 5 phút; giới hạn mỗi giờ; mã dự phòng; admin chưa cài thì bị từ chối; admin không dùng được mã dự phòng.
- Bật/tắt: cần xác thực lại; QR không cache, có CSP, bật xong trả 404; mã sai thì không bật; mã dự phòng hiện một lần; có thư báo.
- Lệnh `tao_admin`: sai mã thì không tạo gì; chỉ có một admin. Lệnh `dat_lai_2fa_admin`: chuỗi bí mật được thay.
- `db_check_grants` (114 kiểm tra): `app_customer`, `app_staff`, `app_session` đọc `accounts_totpdevice` → 1142.

**Thử tay trigger bằng `app_auth`** (mỗi câu trong giao dịch rồi `ROLLBACK`), kết quả mong đợi:

| Câu lệnh bằng `app_auth` | Kết quả |
|---|---|
| Xóa thiết bị của admin | 1644 `... khong duoc go 2 buoc cua nhan vien` |
| Đổi `secret_encrypted` của admin | 1644 `... chi duoc ghi buoc thoi gian ...` |
| Thêm thiết bị hoặc mã dự phòng cho admin | 1644 |
| Lùi `last_used_step` | 1644 `khong duoc lui buoc thoi gian ...` |
| Tăng `last_used_step` của admin; cài cho khách | chạy được |

**Thử trên web:**
- Bật 2 bước cho một khách bằng điện thoại thật, đăng xuất rồi đăng nhập lại bằng mã.
- Thử nhập lại đúng mã vừa dùng: phải báo "đã được dùng".
- Thử một mã dự phòng, rồi xem log trên trang Nhật ký.
