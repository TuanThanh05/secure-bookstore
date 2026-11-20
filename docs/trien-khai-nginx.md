# Triển khai sau Nginx và IP thật của người dùng

Mô hình triển khai: trình duyệt → Nginx (HTTPS) → Gunicorn (`127.0.0.1:8000`) → Django → MySQL. Nginx là phần mềm mã nguồn mở, miễn phí.

File cấu hình nằm trong `deploy/`:
- `deploy/nginx/secure-bookstore.conf`
- `deploy/gunicorn.conf.py`

## 1. Phát hiện số 12: mọi người chung một IP sau Nginx

Trước bản sửa, Django lấy IP người dùng từ `request.META["REMOTE_ADDR"]`. Các chỗ đọc là: log bảo mật (`core/security_log.py`), django-axes (không cài `django-ipware` thì axes dùng `REMOTE_ADDR`), giới hạn đăng ký theo IP, Turnstile (`remoteip`), thanh toán mô phỏng.

Khi chạy sau Nginx, `REMOTE_ADDR` là địa chỉ của chính Nginx (`127.0.0.1`), nên **mọi người dùng trên Internet có chung một IP**. Hậu quả:

1. **Khóa đăng nhập của bất kỳ ai, kể cả admin.** axes khóa theo cặp `username + ip_address`, để người dùng thật ở IP khác vẫn vào được. Mọi người chung IP thì 5 lần sai (dùng tên đăng nhập hoặc email của nạn nhân) là chủ tài khoản ở bất kỳ đâu cũng bị khóa 15 phút. Lặp lại mỗi 15 phút thì admin không bao giờ vào được trên web. Trên máy chủ vẫn mở được bằng lệnh `axes_reset`.
2. **Chặn đăng ký của cả hệ thống:** giới hạn 5 lần/10 phút/IP (`accounts.services.allow_signup_step`) bị dùng chung cho mọi người.
3. **Mất dấu vết điều tra:** log và axes ghi toàn `127.0.0.1`. Turnstile và thanh toán mô phỏng cũng nhận sai IP.

Khi chạy `runserver` trên máy dev (không có Nginx) thì không bị, vì `REMOTE_ADDR` đã là IP thật.

**Tái hiện qua Nginx thật trong sandbox** (code `main` `c1cc0c9`, kẻ tấn công từ `127.0.0.66`, admin từ `127.0.0.9`):

| | Code cũ | Code mới |
|---|---|---|
| Admin nhập đúng mật khẩu sau 5 lần sai của kẻ tấn công | **429, bị khóa** | 302, vào được |
| Kẻ tấn công nhập đúng mật khẩu từ IP của mình | 429 | 429 (chỉ IP này bị khóa) |
| Kẻ tấn công gửi header giả `X-Real-IP: 10.1.2.3` | 429 | 429 (header giả bị Nginx ghi đè) |
| IP ghi trong axes và log | `127.0.0.1` | `127.0.0.66`, `127.0.0.9` (đúng) |

## 2. Cách sửa: cả hai phía

**Nginx** ghi đè header bằng IP thật của kết nối:

```nginx
proxy_set_header X-Real-IP $remote_addr;
proxy_set_header X-Forwarded-For $remote_addr;
```

Phải là **ghi đè**. Không dùng `$proxy_add_x_forwarded_for`, vì biến này nối IP thật vào sau giá trị client tự gửi.

**Django:** `core/client_ip.client_ip(request)` là hàm duy nhất để lấy IP.

- Chỉ tin header `X-Real-IP` khi `REMOTE_ADDR` nằm trong `TRUSTED_PROXY_IPS` (đọc từ `.env`).
- Header phải là một địa chỉ IP hợp lệ, nếu không thì bỏ qua và dùng `REMOTE_ADDR`.
- Không có proxy tin cậy (máy dev) thì luôn dùng `REMOTE_ADDR`. Client gửi `X-Real-IP` giả cũng vô ích.
- Mọi chỗ dùng IP đều đi qua hàm này: log, axes (`AXES_CLIENT_IP_CALLABLE`), giới hạn đăng ký, Turnstile, thanh toán.
- `settings/prod.py` báo lỗi nếu thiếu `TRUSTED_PROXY_IPS`, nên máy chủ thật không thể quên cấu hình này.

**Cái bẫy cần tránh:** nếu Django tin `X-Forwarded-For` từ bất kỳ ai thì kẻ tấn công đổi IP giả sau mỗi lần thử. Như vậy là **vượt luôn axes** (dò mật khẩu không giới hạn) và log ghi IP giả. Đây là lý do có `TRUSTED_PROXY_IPS`, và test `test_spoofed_header_from_outside_does_not_bypass_lockout` kiểm tra đúng trường hợp này.

## 3. Cấu hình Nginx (`deploy/nginx/secure-bookstore.conf`)

| Phần | Làm gì |
|---|---|
| `listen 80` | Chỉ chuyển sang HTTPS (301) |
| `listen 443 ssl`, TLS 1.2/1.3, `ssl_session_tickets off` | HTTPS. HSTS do Django gửi (`SECURE_HSTS_SECONDS`) |
| `server_tokens off` | Không lộ phiên bản Nginx |
| `client_max_body_size 3m`, timeout 15 giây | Ảnh bìa tối đa 2 MB; chống gửi body chậm |
| `/static/` | File sau `collectstatic`, có `nosniff` |
| `/media/covers/` | Chỉ file `.webp`, kèm CSP `default-src 'none'`; mọi thứ khác dưới `/media/` → 404 |
| `location /` | `proxy_pass` tới Gunicorn; ghi đè `X-Real-IP`, `X-Forwarded-For`, `X-Forwarded-Proto` |

Gunicorn (`deploy/gunicorn.conf.py`):
- Chỉ nghe `127.0.0.1:8000`, nên từ ngoài không vào thẳng được, phải qua Nginx.
- **1 tiến trình, 4 luồng**, để bộ đếm giới hạn tần suất (cache bộ nhớ) dùng chung một chỗ.
- Không ghi access log, vì Nginx đã ghi và đường dẫn có thể chứa mã một lần.

## 4. Chạy demo trên máy (Arch Linux)

1. Cài:
   ```zsh
   sudo pacman -S nginx
   ```
   Gunicorn đã có trong `requirements.txt`, nên chạy `pip install -r requirements.txt` là có.
2. Tên miền demo: thêm `127.0.0.1 bookstore.local` vào `/etc/hosts`.
3. Chứng chỉ tự ký (trình duyệt sẽ cảnh báo, bấm chấp nhận khi demo):
   ```zsh
   sudo mkdir -p /etc/nginx/ssl
   ```
   ```zsh
   sudo openssl req -x509 -newkey rsa:2048 -nodes -days 365 -subj "/CN=bookstore.local" -addext "subjectAltName=DNS:bookstore.local" -keyout /etc/nginx/ssl/bookstore.key -out /etc/nginx/ssl/bookstore.crt
   ```
   Khóa `bookstore.key` là bí mật: không commit, không gửi cho ai.
4. Nginx của Arch không tự đọc `conf.d/`:
   - Trong `/etc/nginx/nginx.conf`, thêm `include /etc/nginx/conf.d/*.conf;` vào khối `http { }` và xóa khối `server { listen 80; ... }` mặc định.
   - Chép `deploy/nginx/secure-bookstore.conf` vào `/etc/nginx/conf.d/`.
   - Sửa các dòng có chữ `ĐỔI`, nhất là đường dẫn `/srv/secure-bookstore/` thành thư mục repo.
   - Nginx chạy bằng user `http`, nên phải đọc được thư mục `staticfiles/` và `media/`. Thư mục home thường là `700`; nếu bị 403 thì chép hai thư mục này sang `/srv/secure-bookstore/`.
5. `.env` cho prod:
   - `DJANGO_ALLOWED_HOSTS=bookstore.local`
   - `DJANGO_CSRF_TRUSTED_ORIGINS=https://bookstore.local`
   - `TRUSTED_PROXY_IPS=127.0.0.1`
   - Key Turnstile thật, và thêm hostname `bookstore.local` vào widget trên Cloudflare.
6. File tĩnh, rồi chạy Gunicorn và Nginx:
   ```zsh
   cd backend && python manage.py collectstatic --settings=bookstore.settings.prod
   ```
   ```zsh
   gunicorn -c ../deploy/gunicorn.conf.py
   ```
   ```zsh
   sudo nginx -t && sudo systemctl restart nginx
   ```
7. Mở `https://bookstore.local`.

## 5. Kiểm tra

Kiểm tra tự động:
- `core/tests/test_client_ip.py`:
  - Đọc IP: có hoặc không có proxy tin cậy; header giả từ ngoài bị bỏ qua; header sai định dạng (rỗng, chữ, nhiều IP, `999.1.1.1`) thì quay về `REMOTE_ADDR`; IPv6.
  - Tái hiện phát hiện số 12 qua giả lập Nginx: admin không bị khóa bởi IP khác; chỉ IP kẻ tấn công bị khóa và log ghi đúng IP; đổi header giả mỗi lần cũng không vượt được axes.
- CI chạy `check --deploy` với `TRUSTED_PROXY_IPS=127.0.0.1`.

Thử tay sau khi dựng Nginx (bước 4):
- Đăng nhập sai 5 lần, rồi vào trang Nhật ký: cột IP phải là IP thật, không phải `127.0.0.1`.
- Kiểm tra từ ngoài không vào thẳng Gunicorn được (lệnh dưới phải lỗi kết nối):
  ```zsh
  curl http://<IP LAN của máy>:8000/
  ```

## 6. Giới hạn đã biết

- Access log của Nginx ghi cả đường dẫn, kể cả link đăng ký và đặt lại mật khẩu. Các mã này chỉ dùng một lần và có hạn, nhưng vẫn nên giữ quyền đọc log ở mức root.
- Chỉ 1 tiến trình Gunicorn. Muốn nhiều tiến trình thì phải chuyển cache sang chỗ dùng chung (ví dụ Redis) trước.
- Nếu sau này có thêm một tầng proxy nữa (Cloudflare proxy, load balancer) thì phải xem lại `TRUSTED_PROXY_IPS` và cách Nginx lấy IP (module `real_ip`).
