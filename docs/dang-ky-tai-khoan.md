# Đăng ký tài khoản bắt đầu bằng email – sửa lỗ hổng chiếm tài khoản trước khi đăng ký

## 1. Lỗ hổng đã tìm thấy (2026-11-19)

**Tên:** chiếm tài khoản trước khi đăng ký (*account pre-hijacking*). Lớp lỗi này được phân tích trong bài báo của A. Sudhodanan và A. Paverd, "Pre-hijacked accounts: An Empirical Study of Security Failures in User Account Creation on the Web", USENIX Security 2022.

**Luồng cũ** (PR #13–#16):

1. Gửi form đăng ký (tên đăng nhập, email, mật khẩu) → `INSERT` ngay một dòng `accounts_user` với mật khẩu của người gửi, `email_verified = 0`. Trigger `trg_pwhist_after_insert` ghi mã băm mật khẩu đó vào `accounts_passwordhistory`.
2. Gửi link xác nhận (hạn 5 phút) tới email.
3. Người khác gửi form với **cùng email** → code thấy email đã có tài khoản chưa xác nhận, **bỏ form mới** và gửi link mới **cho tài khoản cũ**.
4. Bấm link → `email_verified = 1` → tài khoản mở ra với mật khẩu của người gửi form **đầu tiên**.

**Kịch bản tấn công** (nhóm trưởng tự kiểm chứng):

1. Kẻ tấn công đăng ký bằng `nannhan@gmail.com` với mật khẩu của hắn.
2. Nạn nhân sau đó đăng ký bằng chính email của mình, với mật khẩu riêng.
3. Nạn nhân nhận thư, bấm xác nhận.
4. Kẻ tấn công đăng nhập được bằng email nạn nhân và mật khẩu của hắn.

Thời hạn 5 phút **không** giới hạn được tấn công: đó là hạn của link, còn dòng `accounts_user` thì tồn tại mãi. Kẻ tấn công có thể "cắm" sẵn tài khoản cho nhiều email rồi chờ.

Đã tái hiện bằng test trên code cũ (`main` `d3be90a`): kẻ tấn công đăng nhập thành công, mật khẩu của nạn nhân không dùng được.

## 2. Cách sửa: tài khoản chỉ được tạo sau khi chứng minh mở được hộp thư

**Nguyên tắc:** người đặt mật khẩu phải là người mở được hộp thư. Trước khi có bằng chứng đó, CSDL không ghi gì cả.

| Bước | URL | Việc server làm |
| --- | --- | --- |
| 1. Nhập email | `/account/register/` | Không ghi CSDL. Email mới → gửi link. Email đã có tài khoản → gửi thư báo (kèm link đăng nhập và quên mật khẩu), không có link đăng ký. Cả hai đều chuyển tới cùng một trang "Kiểm tra hộp thư". |
| 2. Bấm link trong thư | `/account/dang-ky/xac-nhan/<mã>/` | Kiểm tra chữ ký, hạn 5 phút, email chưa có tài khoản. Đổi session ID (`cycle_key`), cất `{email, thời điểm}` vào phiên, chuyển ngay sang địa chỉ không có mã. |
| 3. Đặt tên đăng nhập, mật khẩu | `/account/dang-ky/hoan-tat/` | Email chỉ hiển thị, lấy từ phiên. Phiên hết hạn sau 5 phút kể từ lúc bấm link. Tạo tài khoản với `email_verified = 1`, xóa dữ liệu đăng ký khỏi phiên, chuyển sang trang đăng nhập. |

Kẻ tấn công nhập email nạn nhân ở bước 1 thì chỉ có một thư bay vào hộp thư nạn nhân. Hắn không có link nên không qua được bước 2. Không có dòng nào để "cắm sẵn", không giữ chỗ được tên đăng nhập.

## 3. Các điểm phải làm đúng (và đã kiểm thử)

1. **Email lấy từ phiên, không lấy từ form.** Nếu để email trong ô ẩn, kẻ tấn công dùng link của chính mình rồi sửa ô ẩn thành email nạn nhân. Test `test_attacker_link_cannot_be_redirected_to_victim_email` gửi thêm ô `email` và kiểm tra nó bị bỏ qua.
2. **Mã không còn trên thanh địa chỉ ở trang nhập mật khẩu.** Mở link → 302 ngay, nên mã không vào lịch sử của trang form, không lọt qua header Referer khi trang tải tài nguyên. Log của link sai ghi đường dẫn `/account/dang-ky/xac-nhan/-/` thay vì mã thật (tham số `path` mới của `log_event`).
3. **Đổi session ID khi cất email** để chống *session fixation*: kẻ tấn công không thể cài sẵn session ID cho nạn nhân rồi dùng ké phiên đã có email.
4. **Link chỉ dùng được đến khi có tài khoản.** Email đã có tài khoản thì link báo "không còn hiệu lực". Hai tab cùng nộp một lúc thì UNIQUE của cột `email` chặn tab thứ hai (bắt `IntegrityError`).
5. **Mã link chỉ ký, không mã hóa.** Phần đầu mã là JSON base64 chứa email. Ai đọc được link thì đọc được email, nhưng đó chính là email của người nhận thư. Không sửa được mã vì chữ ký HMAC dùng `SECRET_KEY` + salt riêng `accounts.signup-link`. Mã ký cho mục đích khác (salt khác) bị từ chối.
6. **Mở link bằng GET là an toàn.** Luồng cũ phải bắt bấm nút POST vì GET bật `email_verified` (trình quét thư tự mở link sẽ xác nhận hộ). Luồng mới GET chỉ ghi vào phiên của chính trình duyệt mở link, không tạo gì trong CSDL.
7. **Mật khẩu kiểm tra với email.** Form bước 2 gán email vào tài khoản trước khi kiểm tra, nên `UserAttributeSimilarityValidator` chặn mật khẩu giống email.

## 4. Giới hạn tần suất

| Giới hạn | Giá trị | Ở đâu |
| --- | --- | --- |
| Mỗi email, mỗi loại thư | 1 thư / 60 giây | `EMAIL_RESEND_INTERVAL`, `emails._allow_send` (có từ trước) |
| Mỗi email, thư đăng ký (link hoặc thư báo trùng) | 5 lần / giờ | `SIGNUP_EMAIL_LIMIT`, `SIGNUP_EMAIL_WINDOW`, `services._allow_signup_mail` |
| Mỗi IP, bước 1 | 5 lần / 10 phút → 429 | `SIGNUP_RATE_LIMIT`, `SIGNUP_RATE_WINDOW`, `services.allow_signup_step(request, "start")` |
| Mỗi IP, bước 3 | 5 lần / 10 phút → 429 | như trên, `"complete"` |

Thêm một lớp nữa ở bước 1: **Cloudflare Turnstile** (CAPTCHA), kiểm tra sau giới hạn theo IP và trước giới hạn theo email – xem `docs/captcha-turnstile.md`.

Vượt giới hạn thư theo email thì vẫn hiện trang "Kiểm tra hộp thư" như bình thường (không lộ gì), chỉ ghi log `rate_limited`. Vượt giới hạn theo IP thì báo "thao tác quá nhiều lần" (không liên quan email nào).

**Hạn chế đã biết:** bộ đếm nằm trong cache bộ nhớ mặc định của Django. Khởi động lại web thì về 0; chạy nhiều tiến trình thì mỗi tiến trình đếm riêng. Khi triển khai thật nên dùng cache chung (ví dụ Redis). Sau Nginx cần lấy IP thật (xem `claude/HANDOFF.md`, mục triển khai).

## 5. Đã bỏ hẳn luồng xác nhận email cũ

- Trang `/account/xac-nhan-email/<mã>/`, `/account/gui-lai-xac-nhan/` (giờ trả 404) và template, form, thư đi kèm.
- `register_account`, `find_pending_user`, `mark_email_verified`, `resend_verification`.
- Chặn đăng nhập "email chưa xác nhận" trong `LoginForm`.
- Đặt lại mật khẩu không còn bật `email_verified` (không còn tài khoản nào chưa xác nhận).
- 3 loại log `email_verified`, `email_verify_failed`, `login_blocked_unverified`: rút khỏi CHECK `ck_secevent_type` (`database/schema/08_securityevent_signup.sql`, migration `core/0009`). Thêm `register_link_invalid` (`detail.reason`: `expired`, `invalid`, `used`, `session`).

**Giữ lại cột `email_verified`.** Các thủ tục `sp_place_order`, `sp_cart_*`, `sp_review_save`, `sp_payment_simulate`, `sp_order_*` vẫn kiểm tra `email_verified = 1` ngay trong MySQL. Đây là lớp chặn thứ hai: nếu sau này có code tạo tài khoản khách sai đường (không qua link), MySQL vẫn từ chối mua hàng. Trạng thái "Chưa xác nhận email" ở trang Quản lý tài khoản của admin vì vậy chỉ còn xuất hiện khi có bất thường.

## 6. Kiểm thử

- `accounts/tests/test_signup.py`: 23 test, gồm đúng kịch bản tấn công ở mục 1 (`test_attacker_cannot_pre_register_victim_email`), ô email giả trong form, phiên, link hết hạn/sửa/dùng lại, hai tab, mật khẩu yếu hoặc giống email, CSRF, giới hạn theo email và IP, URL cũ trả 404.
- `accounts/tests/test_signup_token.py`: 8 test cho mã link.
- Chạy thật trên MySQL trong sandbox bằng trình duyệt (Playwright): kẻ tấn công nhập email nạn nhân → `accounts_user` không có dòng nào, kẻ tấn công mở trang hoàn tất bị 400; nạn nhân mở link → địa chỉ chuyển sang `/account/dang-ky/hoan-tat/`, tạo tài khoản → đúng 1 dòng `email_verified = 1`, `accounts_passwordhistory` 1 dòng (mật khẩu nạn nhân); mở lại link → 400; đăng nhập bằng mật khẩu kẻ tấn công thất bại, bằng mật khẩu nạn nhân thành công.
