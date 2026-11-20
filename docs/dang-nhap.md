# Đăng nhập: chỉ bằng tên đăng nhập, chặn IP dò mật khẩu rải

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
| Chỉ tên đăng nhập | `LoginForm` và `CustomerReauthForm` bỏ hẳn việc tra email. Nhãn ô là "Tên đăng nhập", tối đa 50 ký tự (bằng cột `username`). Gõ email thì bị coi là tên không tồn tại và nhận đúng câu chung "Tên đăng nhập hoặc mật khẩu không đúng." Form xác thực lại của admin (`dashboard.ReauthForm`) vốn chỉ nhận tên đăng nhập. |
| Quên tên đăng nhập | Dùng "Quên mật khẩu" (nhập email). Thư đặt lại mật khẩu ghi thêm dòng **"Tên đăng nhập của bạn: …"**. Thư chỉ tới hộp thư của chủ tài khoản, và trang quên mật khẩu vẫn trả lời giống nhau cho mọi email. |
| Chặn IP (S1) | Một IP đăng nhập sai **≥ 20 lần trong 60 phút gần nhất**, gộp mọi tài khoản, thì trang đăng nhập trả **429** *trước khi* kiểm mật khẩu (không gọi `authenticate`, đúng mật khẩu cũng không vào được). Có ghi log `rate_limited` (`warning`, `detail.kind = "login_ip"`). Trang đăng nhập (GET) và "Quên mật khẩu" vẫn mở được. Khi số lần sai trong 60 phút tụt xuống dưới 20 thì hết bị chặn. |

Ngưỡng nằm trong `settings/base.py`: `LOGIN_IP_FAILURE_LIMIT = 20`, `LOGIN_IP_FAILURE_WINDOW_MINUTES = 60`.

### Vì sao đếm từ bảng nhật ký

- Bền: không mất khi khởi động lại hay đổi tiến trình. Cache (LocMemCache) thì mất khi khởi động lại và mỗi worker đếm riêng.
- Bản ghi axes hết hạn sau 15 phút (`AXES_COOLOFF_TIME`), không đủ cửa sổ 60 phút, và chỉ tính theo từng cặp tên + IP.
- Mỗi lần đăng nhập sai đã được ghi `login_failed` kèm IP thật (`core.client_ip`, chỉ tin `X-Real-IP` từ Nginx).

### Phân quyền

Thủ tục `sp_login_ip_failures(ip, phút)` (`database/objects/46_login_ip_guard.sql`, DEFINER, `READS SQL DATA`) chỉ
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
| `database/objects/46_login_ip_guard.sql`, `database/grants/01_role_privileges.sql` | thủ tục + quyền |
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
