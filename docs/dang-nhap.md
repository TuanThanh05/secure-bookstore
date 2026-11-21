# Đăng nhập: chỉ bằng tên đăng nhập, chặn IP dò mật khẩu rải, xác thực lại chỉ bằng mật khẩu

Báo cáo rà soát bảo mật mục **T3.2** (mức trung bình), chốt ngày 2026-11-20.

## 1. Vấn đề

**a. Dò ngược email ↔ tên đăng nhập.** Trước đây ô đăng nhập nhận *tên đăng nhập hoặc email*:
`LoginForm.clean_username` tra `email → username` rồi mới kiểm mật khẩu, và form xác thực lại của khách
(`CustomerReauthForm`) cũng làm vậy. django-axes khóa theo cặp (tên đăng nhập, IP), nên khi một tài khoản đang bị
khóa thì nhập **email** của nó cũng hiện thông báo khóa. Ai biết một trong hai thứ (email hoặc tên đăng nhập) sẽ
dò ra được thứ còn lại, ví dụ email lộ ở chỗ khác, hoặc tên đăng nhập lộ trong nhật ký. Đó là bước thu thập
thông tin trước khi dò mật khẩu hay lừa đảo qua thư.

**b. Dò mật khẩu rải (password spraying).** axes chỉ đếm theo cặp (tên đăng nhập, IP). Một IP thử 1–4 mật khẩu
phổ biến trên **rất nhiều** tài khoản thì không cặp nào chạm ngưỡng 5, nên không bị chặn.

Tái hiện trên code cũ (main `f8ef043`, sandbox): 20 lần sai với 20 tên khác nhau từ một IP, lần thứ 21 đúng mật khẩu
vẫn **đăng nhập được (302)**. Nhập email đúng + mật khẩu đúng cũng **đăng nhập được**.

## 2. Cách sửa (đã chốt)

| Phần | Làm gì |
|---|---|
| Chỉ tên đăng nhập | `LoginForm` và `CustomerReauthForm` bỏ hẳn việc tra email. Nhãn ô là "Tên đăng nhập", tối đa 50 ký tự (bằng cột `username`). Gõ email thì bị coi là tên không tồn tại và nhận đúng câu chung "Tên đăng nhập hoặc mật khẩu không đúng." Sau đó T2.2 bỏ hẳn ô tên đăng nhập ở mọi form xác thực lại (mục 6). |
| Quên tên đăng nhập | Dùng "Quên mật khẩu" (nhập email). Thư đặt lại mật khẩu ghi thêm dòng **"Tên đăng nhập của bạn: …"**. Thư chỉ tới hộp thư của chủ tài khoản, và trang quên mật khẩu vẫn trả lời giống nhau cho mọi email. |
| Chặn IP (S1) | Một IP đăng nhập sai **≥ 20 lần trong 60 phút gần nhất**, gộp mọi tài khoản, thì trang đăng nhập trả **429** *trước khi* kiểm mật khẩu (không gọi `authenticate`, đúng mật khẩu cũng không vào được). Có ghi log `rate_limited` (`warning`, `detail.kind = "login_ip"`). Trang đăng nhập (GET) và "Quên mật khẩu" vẫn mở được. Khi số lần sai trong 60 phút tụt xuống dưới 20 thì hết bị chặn. |

Ngưỡng nằm trong `settings/base.py`: `LOGIN_IP_FAILURE_LIMIT = 20`, `LOGIN_IP_FAILURE_WINDOW_MINUTES = 60`.

### Vì sao đếm từ bảng nhật ký

- Bền: không mất khi khởi động lại hay đổi tiến trình. Cache (LocMemCache) thì mất khi khởi động lại và mỗi worker đếm riêng.
- Bản ghi axes hết hạn sau 15 phút (`AXES_COOLOFF_TIME`), không đủ cửa sổ 60 phút, và chỉ tính theo từng cặp tên + IP.
- Mỗi lần đăng nhập sai đã được ghi `login_failed` kèm IP thật (`core.client_ip`, chỉ tin `X-Real-IP` từ Nginx).

### Phân quyền

Thủ tục `sp_login_ip_failures(ip, phút)` (phần 46 của `database/02_trigger_thu_tuc.sql`, DEFINER, `READS SQL DATA`) chỉ
trả **một con số**. `r_customer` chỉ có `EXECUTE` thủ tục này, còn `SELECT core_securityevent` vẫn bị cấm (1142), nên
lỗi SQL injection trên tài khoản ứng dụng cũng không đọc được nhật ký qua đây. `app_staff`, `app_session`, `app_auth`
không gọi được (1370). Tham số được kiểm: IP 1–45 ký tự, cửa sổ 1–1440 phút.

### Còn hở gì (chấp nhận)

- Kẻ tấn công có nhiều IP (botnet, proxy xoay vòng) thì mỗi IP dưới 20 lần vẫn lọt. Lớp này chỉ chặn spraying từ một nguồn.
- Nhiều người dùng chung một IP công cộng (NAT trường, quán cà phê) có thể cùng bị chặn tối đa 60 phút nếu có người
  trong mạng đó dò mật khẩu. Họ vẫn đặt lại mật khẩu được, nhưng không đăng nhập được trong thời gian này.
- Bản ghi nhật ký cũ hơn 60 phút không làm chậm truy vấn: đã có chỉ mục `ix_secevent_created`.

## 3. Thành phần trong code

| File | Nội dung |
|---|---|
| `backend/accounts/forms.py` | `LoginForm`, `CustomerReauthForm`: bỏ tra email; `USERNAME_MAX_LENGTH = 50` |
| `backend/accounts/services.py` | `login_ip_blocked(request)` gọi `sp_login_ip_failures`; thủ tục chưa tạo (1305) thì không chặn, lỗi khác thì báo lên |
| `backend/accounts/views.py` | `SecureLoginView.post`: chặn 429 + log trước khi kiểm mật khẩu |
| `frontend/templates/account/email/password_reset.txt` | thêm dòng tên đăng nhập |
| phần 46 của `database/02_trigger_thu_tuc.sql`, `database/03_phan_quyen.sql` | thủ tục + quyền |
| `backend/core/management/commands/db_check_grants.py` | thêm 4 kiểm tra (tổng 138) |
| `backend/accounts/tests/test_login_username_only.py` | test mới |

## 4. Kiểm tra

```zsh
cd backend
python manage.py db_apply
python manage.py db_check_grants      # "Cả 138 kiểm tra phân quyền đều đúng."
python manage.py test accounts.tests.test_login_username_only --settings=bookstore.settings.migrate
```

Thử tay: đăng nhập sai 20 lần bằng 20 tên khác nhau, lần thứ 21 nhập đúng tài khoản thật thì phải ra trang báo
"Có quá nhiều lần đăng nhập sai từ mạng của bạn…" (429). Ở trang Nhật ký hệ thống có dòng "Vượt giới hạn tần suất" với IP đó.
Nhập email + mật khẩu đúng thì phải ra "Tên đăng nhập hoặc mật khẩu không đúng."

## 5. Khi triển khai bản này

1. `git pull`, rồi `python manage.py db_apply` (tạo thủ tục, cấp quyền). Không có migration mới.
2. `python manage.py db_check_grants`.
3. Báo người dùng: từ nay chỉ đăng nhập bằng **tên đăng nhập**. Ai quên thì bấm "Quên mật khẩu", thư sẽ ghi tên đăng nhập.

## 6. Xác thực lại chỉ bằng mật khẩu (T2.2, chốt 2026-11-20)

**Vấn đề (báo cáo rà soát T2.2):** các form xác thực lại có ô tên đăng nhập. Code gọi `authenticate()` với tên người dùng **tự gõ**, rồi mới so với người đang đăng nhập. Người đã đăng nhập dùng form này thử được mật khẩu của tài khoản khác, mỗi lần sai còn làm tăng bộ đếm khóa axes của nạn nhân.

**Cách sửa:** bỏ hẳn ô tên đăng nhập ở 3 form:

| Form | Ai dùng | Còn lại |
|---|---|---|
| `accounts.forms.CustomerReauthForm` (`/account/xac-thuc-lai/`) | Khách | Ô mật khẩu |
| `dashboard.forms.ReauthForm` (`/dashboard/xac-thuc-lai/`) | Admin | Ô mật khẩu |
| `dashboard.forms.AccountActionForm` (khóa/mở khóa tài khoản khách) | Admin | Lý do + ô mật khẩu |

- Cả ba kế thừa `accounts.forms.CurrentUserPasswordForm`: `authenticate(request, username=request.user.get_username(), password=…)`. Tên đăng nhập **chỉ lấy từ phiên**, không bao giờ từ form; gửi thêm trường `username` trong POST cũng bị bỏ qua.
- Trang hiện dòng chữ "Xác nhận bằng tài khoản: <tên>" để người dùng biết đang xác thực cho ai. Kèm một ô `autocomplete="username"` ẩn, **không có thuộc tính `name`** nên không gửi lên server; ô này chỉ để trình quản lý mật khẩu nhận đúng tài khoản.
- Sai mật khẩu: báo "Mật khẩu không đúng.", axes đếm vào **chính tài khoản đó** (5 lần → tạm khóa 15 phút), ghi `login_failed` (cũng được tính vào ngưỡng chặn IP ở mục 2).
- Log `access_denied` `user_mismatch` không còn: trường hợp đó không xảy ra được nữa.

