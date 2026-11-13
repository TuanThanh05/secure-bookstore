# SECURITY CHECKLIST – Web bán sách đảm bảo an toàn bảo mật

> Tách từ `PROJECT_CONTEXT.md` ngày 2026-11-11 (mục 4 và 5 cũ) vì file ngữ cảnh đã quá dài. Đánh dấu `[x]` khi mục đã làm xong và người kiểm thử đã xác nhận.

---

## 4. Checklist bảo mật theo chức năng

Ký hiệu: **[BB]** bắt buộc · **[NL]** nên làm · **[CĐ]** cộng điểm.

### 1. Đăng ký
- Django lo: băm mật khẩu, 4 validator, CSRF, ORM.
- [x] [BB] Tối thiểu 12 ký tự.
- [x] [BB] Kiểm tra đầu vào ở server bằng Django Form (email, SĐT regex, độ dài họ tên, ký tự username).
- [x] [BB] Chống mass assignment: form chỉ khai báo trường cho phép, không gửi được `is_staff`/`is_superuser`.
- [ ] [NL] Xác minh email: `is_active=False` cho tới khi bấm link có token 24 giờ.
- [ ] [NL] CAPTCHA.
- [ ] [CĐ] Kiểm tra mật khẩu đã bị lộ qua Have I Been Pwned (k-anonymity).
- Demo: Burp thêm `is_staff=1` → vẫn là khách thường; mật khẩu `12345678` bị từ chối; `auth_user` lưu `pbkdf2_sha256$...`, `argon2`.

### 2. Đăng nhập, đăng xuất, quên mật khẩu
- Django lo: đổi session ID khi đăng nhập, so sánh mật khẩu an toàn, token reset có hạn.
- Django KHÔNG có: giới hạn đăng nhập sai, khóa tài khoản, 2FA, CAPTCHA.
- [x] [BB] Sai 5 lần thì khóa 15 phút, theo username và IP (`django-axes`).
- [x] [BB] Thông báo lỗi chung cho mọi trường hợp sai.
- [x] [BB] Đăng xuất bằng POST, xóa session ở server.
- [x] [BB] Chống open redirect với `next` (`url_has_allowed_host_and_scheme`).
- [ ] [NL] 2FA TOTP, bắt buộc với admin (`django-otp`).
- [ ] [NL] CAPTCHA sau 3 lần sai.
- [ ] [NL] `PASSWORD_RESET_TIMEOUT = 1800`, giới hạn số lần yêu cầu reset mỗi giờ.
- [ ] [CĐ] Email cảnh báo khi đăng nhập từ IP lạ hoặc khi đổi mật khẩu.
- Demo: Burp Intruder/Hydra bị khóa sau 5 lần; hai thông báo lỗi giống nhau; `?next=https://evil.com` không chuyển hướng ra ngoài.

### 3. Xem sách và tìm kiếm
- Django lo: ORM, auto-escape.
- [ ] [BB] Chỉ dùng ORM. Nếu dùng SQL thì tham số hóa (`cursor.execute("... LIKE %s", [q])`).
- [ ] [BB] `sort` theo whitelist (`price`, `-price`, `title`, `-created_at`).
- [ ] [BB] `page`, `category_id` là số nguyên; từ khóa tối đa 100 ký tự; phân trang 20 kết quả.
- [ ] [BB] Sách ẩn hoặc ngừng bán trả 404 khi vào URL trực tiếp.
- [ ] [NL] JS dùng `textContent`, không dùng `innerHTML` (chống DOM XSS).
- [ ] [NL] Rate limit tìm kiếm 30 request/phút/IP.
- Demo: sqlmap trên bản lỗi lấy được DB, bản an toàn thì không; `<script>alert(1)</script>` hiển thị nguyên chữ; `sort=password` bị bỏ qua.

### 4. Đánh giá sách
- Django lo: auto-escape (chống stored XSS), CSRF.
- [ ] [BB] Không `|safe`. Nếu cho định dạng thì lọc bằng `nh3`/`bleach` với whitelist.
- [ ] [BB] Phải đăng nhập; chỉ người đã mua (đơn đã giao) mới được đánh giá; mỗi người một đánh giá cho mỗi sách (`unique_together`).
- [ ] [BB] Chống IDOR khi sửa/xóa: `Review.objects.get(id=pk, user=request.user)`.
- [ ] [BB] Số sao 1–5 (form + CHECK ở CSDL); nội dung tối đa 2.000 ký tự.
- [ ] [NL] CSP làm lớp chặn thứ hai.
- [ ] [NL] Tối đa 5 đánh giá/giờ/tài khoản.
- [ ] [CĐ] Admin duyệt hoặc ẩn đánh giá.
- Demo: payload `<img onerror=...>` (bản `|safe` chạy script, bản an toàn thì không; `HttpOnly` chặn lấy cookie); `rating=100` bị từ chối; A xóa đánh giá của B nhận 404.

### 5. Giỏ hàng và tạo đơn (Django không lo logic này – ghi điểm tốt nhất)
- [ ] [BB] Giá luôn lấy từ CSDL; form chỉ gửi `book_id`, `quantity`.
- [ ] [BB] Số lượng: số nguyên, từ 1 đến 10, không vượt tồn kho.
- [ ] [BB] Tổng tiền, ship, giảm giá tính ở server; lưu giá lúc đặt vào `OrderItem.unit_price`.
- [ ] [BB] Giỏ gắn với user/session; dòng giỏ của người khác trả 404.
- [ ] [BB] Thao tác giỏ dùng POST.
- [ ] [NL] Mã giảm giá: có hạn, giới hạn lượt, mỗi tài khoản một lần, không cộng dồn, trừ lượt nguyên tử.
- [ ] [NL] Báo cho khách khi giá đã đổi so với lúc thêm vào giỏ.
- Demo (case study "Tấn công tính năng đặt hàng", chương 2): `price=1000`; `quantity=-3`; dùng lại mã giảm giá.

### 6. Đặt đơn (race condition)
- Django không tự chống race condition. Nhóm xử lý ở tầng CSDL bằng stored procedure, Django chỉ gọi `sp_place_order` từ `orders/services.py`.
- [ ] [BB] Đặt đơn qua `sp_place_order(p_user_id, p_items_json)`: bên trong `START TRANSACTION` → `SELECT ... FOR UPDATE` khóa các dòng sách → kiểm tra kho → trừ kho → tạo `orders`/`order_items` (giá lấy từ bảng `books`) → `COMMIT`; thiếu hàng thì `ROLLBACK` và `SIGNAL` lỗi.
- [ ] [BB] Khóa theo `id` tăng dần để tránh deadlock.
- [ ] [BB] `app_customer` không có quyền `UPDATE` trên `books` hay `INSERT` trực tiếp vào `orders`; chỉ có `EXECUTE` trên `sp_place_order`. Thủ tục khai báo `SQL SECURITY DEFINER` với definer là một user riêng không đăng nhập được.
- [ ] [BB] `PositiveIntegerField` + `CheckConstraint(stock >= 0)`.
- [ ] [BB] MySQL dùng InnoDB.
- [ ] [NL] `idempotency_key` UUID UNIQUE chống submit hai lần; khóa nút sau khi bấm.
- [ ] [NL] Đơn chưa thanh toán sau 15 phút thì tự hủy và cộng trả kho.
- [ ] [CĐ] Tối đa 3 đơn chưa thanh toán mỗi tài khoản.
- Demo: kho = 1, 50 request song song (script `threading`/`httpx` hoặc Burp "Send group in parallel"). Bản lỗi: nhiều đơn, kho âm. Bản an toàn: đúng 1 đơn.

### 7. Thanh toán (giả lập cổng kiểu VNPay/MoMo sandbox)
- [ ] [BB] Máy trạng thái: `pending → paid → shipped → delivered`, `pending → cancelled`; các chuyển đổi khác bị từ chối.
- [ ] [BB] Chỉ chủ đơn thanh toán đơn `pending` của mình.
- [ ] [BB] Số tiền lấy từ `order.total`.
- [ ] [BB] Callback: kiểm tra HMAC-SHA256 (`hmac.compare_digest`), khớp số tiền và mã đơn, `transaction_id` UNIQUE.
- [ ] [BB] Đổi trạng thái thành `paid` chỉ qua `sp_confirm_payment(p_order_code, p_amount, p_transaction_id)`; thủ tục tự kiểm tra đơn đang `pending` và số tiền khớp. Không tài khoản ứng dụng nào được `UPDATE` cột `orders.status` thành `paid` trực tiếp.
- [ ] [BB] Chỉ đổi thành `paid` qua callback server-to-server, không tin return URL.
- [ ] [BB] Không lưu số thẻ/CVV (nếu có thì chỉ 4 số cuối).
- [ ] [NL] Secret key để trong `.env`.
- [ ] [NL] Log mọi giao dịch và callback bị từ chối.
- [ ] [CĐ] Nhập lại mật khẩu/OTP với đơn giá trị lớn.
- Demo: callback giả không có chữ ký; replay callback cũ; thanh toán đơn đã hủy.

### 8. Lịch sử đơn và hồ sơ (IDOR – OWASP A01:2021)
- [ ] [BB] `@login_required` / `LoginRequiredMixin` cho mọi view.
- [ ] [BB] Lọc theo user: `get_object_or_404(Order, id=pk, user=request.user)` (cả hóa đơn, hủy đơn, PDF).
- [ ] [BB] Trả 404 thay vì 403.
- [ ] [BB] Form hồ sơ không cho đổi `username`/`is_staff`/`email`; đổi mật khẩu phải nhập mật khẩu cũ.
- [ ] [NL] Mã đơn dùng UUID (chỉ là lớp phụ).
- [ ] [NL] Đổi email phải xác minh email mới và báo email cũ.
- [ ] [NL] Che SĐT/địa chỉ (`09******89`).
- Demo: `/orders/12` → `/orders/13`; Burp Intruder quét id 1–100; chưa đăng nhập thì bị chuyển sang trang đăng nhập.

### 9. Admin quản lý sách và đơn
- Django lo: `/admin/` cần `is_staff`, permission/group, làm sạch tên file, `django_admin_log`.
- [ ] [BB] Group "Quản lý sách" và "Quản lý đơn" theo quyền tối thiểu; chỉ 1 superuser.
- [ ] [BB] Trang quản trị tự viết dùng `@permission_required` / `PermissionRequiredMixin` (lớp 1), và mọi truy vấn trong app `dashboard` đi qua kết nối `staff` (lớp 2).
- [ ] [BB] Nhân viên xem đơn qua view `v_staff_orders` (SĐT, địa chỉ đã che); chỉ được đổi trạng thái `paid → shipped → delivered` (quyền cột `UPDATE (status)` cho `app_staff`, kết hợp kiểm tra ở Django).
- [ ] [BB] Upload ảnh: Pillow `verify()`, chỉ JPG/PNG/WebP, tối đa 2MB, tên UUID, không nhận SVG.
- [ ] [BB] Kiểm tra dữ liệu sách (giá > 0, kho ≥ 0, ISBN); escape mô tả.
- [ ] [BB] 2FA bắt buộc cho staff.
- [ ] [NL] Đổi đường dẫn `/admin/`; trang `/admin/` cũ làm honeypot.
- [ ] [NL] Giới hạn IP vào trang quản trị (Nginx).
- [ ] [NL] Xóa mềm (`is_active=False`).
- [ ] [NL] Admin hết phiên sau 15 phút không hoạt động.
- Demo: upload `shell.php`, `shell.php.jpg`, SVG có script đều bị từ chối; tài khoản "Quản lý sách" xóa sách nhận 403; xem audit log.

---

## 5. Checklist ngoài chức năng

### A. Quản lý phiên
- [ ] [BB] `SESSION_COOKIE_SECURE = True`, `CSRF_COOKIE_SECURE = True`.
- [ ] [BB] `SESSION_COOKIE_AGE = 1800` + `SESSION_SAVE_EVERY_REQUEST = True`.
- [ ] [BB] `SESSION_EXPIRE_AT_BROWSER_CLOSE = True`.
- [ ] [NL] Đổi mật khẩu thì đăng xuất thiết bị khác (`update_session_auth_hash`).
- [ ] [NL] `SESSION_COOKIE_NAME = 'bs_sid'`.
- [ ] [CĐ] Trang "Thiết bị đang đăng nhập" / gắn phiên với User-Agent.
- Demo: DevTools xem cờ cookie; `document.cookie` không thấy session ID; cookie cũ không dùng lại được (chống cookie replay).

### B. Cấu hình Django và header
- [ ] [BB] `DEBUG = False`; trang `404.html`, `500.html` riêng.
- [ ] [BB] Bí mật để trong `.env` (`django-environ`/`python-decouple`), `.env` nằm trong `.gitignore`, commit `.env.example`, sinh `SECRET_KEY` mới.
- [ ] [BB] `ALLOWED_HOSTS` không dùng `'*'`.
- [ ] [BB] `SECURE_SSL_REDIRECT`, `SECURE_HSTS_SECONDS = 7_776_000` (90 ngày, chốt tạm 2026-11-10), `SECURE_HSTS_PRELOAD = False` + tắt cảnh báo `security.W021` (không có domain thật), `SECURE_HSTS_INCLUDE_SUBDOMAINS`, `SECURE_PROXY_SSL_HEADER`.
- [ ] [NL] CSP `default-src 'self'`, không có script inline (Django 6.0+ có middleware sẵn, bản cũ dùng `django-csp`); frontend chuyển JS inline ra file `.js`.
- [ ] [NL] `Permissions-Policy`.
- [ ] [NL] `python manage.py check --deploy` sạch cảnh báo.
- [ ] [CĐ] Argon2 (`argon2-cffi`).
- Demo: so sánh trang lỗi khi `DEBUG=True` và `False`; `curl -I` xem header; iframe bị chặn; ảnh chụp `check --deploy` trước/sau.

### C. Máy chủ triển khai
- [ ] [BB] Gunicorn sau Nginx; Nginx phục vụ `static/`, `media/`.
- [ ] [BB] HTTPS TLS 1.2/1.3 (tự ký/`mkcert` cho demo), chuyển HTTP sang HTTPS.
- [ ] [BB] `server_tokens off`, `autoindex off`, chỉ GET/POST/HEAD, `client_max_body_size 2m`.
- [ ] [BB] `media/` không được thực thi.
- [ ] [BB] Chặn `.env`, `.git/`, `*.sql`, `*.bak`, `*.log`.
- [ ] [BB] Gunicorn chạy bằng user riêng (không phải root); `.env` quyền 600.
- [ ] [NL] `limit_req_zone`: 10 request/giây/IP, 5 request/phút cho `/login`.
- [ ] [NL] `ufw` chỉ mở 22/80/443; SSH dùng key, tắt đăng nhập bằng mật khẩu và root.
- [ ] [NL] `pip-audit`/Dependabot; ghim phiên bản trong `requirements.txt`.
- [ ] [CĐ] Fail2ban hoặc ModSecurity + OWASP CRS.
- Demo: nikto/ZAP trước/sau; `curl -I` ẩn phiên bản; `/.env` bị 403/404; `PUT`/`TRACE` bị 405; nmap chỉ thấy 22/80/443.

### D. Cơ sở dữ liệu (40% điểm, MySQL)
- [ ] [BB] (1) `mysql_secure_installation`; plugin `validate_password` mức MEDIUM trở lên.
- [ ] [BB] (2) Không có SQL nối chuỗi, kể cả trong stored procedure.
- [ ] [BB] (3) Ba tài khoản ứng dụng, mỗi tài khoản quyền tối thiểu theo vai trò (chương 6.2):
    - `app_customer@<host tự dò>` (role `r_customer`): `SELECT` trên các view công khai; `EXECUTE` trên các thủ tục của khách (xem mục 2); `SELECT, INSERT, UPDATE` trên `accounts_user` (trigger chặn leo thang), `SELECT` trên `auth_*`/`accounts_user_groups`, CRUD trên `django_session`; `INSERT` trên `core_securityevent`. **Không có quyền nào trên bảng nghiệp vụ.** (Phần Django đã làm ở bước 5.)
    - `app_staff@<host tự dò>` (role `r_staff`): `SELECT` trên các view nhân viên; `EXECUTE` trên các thủ tục nhân viên; quyền theo cột trên các bảng auth; `INSERT` trên `core_securityevent`. **Không có quyền nào trên bảng nghiệp vụ**, không đọc được SĐT/địa chỉ gốc.
    - `bookstore_definer@localhost`: tài khoản **khóa đăng nhập** (`ACCOUNT LOCK`), chỉ dùng làm definer cho thủ tục và view; có quyền trên bảng nghiệp vụ.
    - `bookstore_migrate@<host tự dò>`: `SELECT, INSERT, UPDATE, DELETE, CREATE, DROP, ALTER, INDEX, REFERENCES` trên `bookstore.*` (+ toàn quyền trên `test\_bookstore.*`); chỉ dùng khi chạy migrate/createsuperuser/test. Không tạo được trigger/view/thủ tục (root làm qua `db_apply`).
    - Không tài khoản nào có `DELETE`/`UPDATE` trên `audit_log`.
- [ ] [BB] (3) Stored procedure cho thao tác nhạy cảm: `sp_place_order`, `sp_confirm_payment`, `sp_cancel_expired_orders` (`SQL SECURITY DEFINER`, definer là user không đăng nhập được); tham số kiểm tra kiểu và giới hạn bên trong thủ tục; không ghép chuỗi động.
- [ ] [BB] (3) View theo vai trò: `v_public_books` (chỉ sách đang bán, không có giá nhập), `v_staff_orders` (SĐT, địa chỉ đã che).
- [ ] [BB] (4)(5) `my.cnf`: `bind-address = 127.0.0.1`, `local_infile = 0`, `secure_file_priv`, `skip-symbolic-links`; gỡ plugin thừa.
- [ ] [BB] (7) Không cấp `FILE`, `SUPER`, `PROCESS`, `GRANT OPTION`; chạy dịch vụ bằng user `mysql`.
- [ ] [BB] (10) Mã hóa SĐT, địa chỉ bằng AES-GCM (thư viện `cryptography`, key trong `.env`).
- [ ] [NL] (10) TLS giữa Django và MySQL (`require_secure_transport = ON`).
- [ ] [NL] (8) `max_connections`, `max_user_connections` = 50, `max_execution_time` = 5 giây, index cột tìm kiếm.
- [ ] [NL] (9)(6) MySQL 8.0/8.4 LTS; ghi lại quy trình vá lỗi.
- [ ] [NL] Trigger ghi `audit_log` cho `books` (giá, kho) và `orders` (trạng thái).
- [ ] [NL] Backup `mysqldump` + cron, mã hóa file, lưu khác máy, thử khôi phục.
- [ ] [CĐ] Mã hóa tablespace InnoDB.
- Demo:
    - Đăng nhập MySQL bằng `app_customer`: `UPDATE books SET stock = 9999`, `UPDATE orders SET status='paid'`, `DROP TABLE books`, `SELECT * FROM mysql.user`, `LOAD_FILE('/etc/passwd')` đều bị từ chối; chỉ `CALL sp_place_order(...)` chạy được. So sánh `SHOW GRANTS` của 3 tài khoản.
    - Phòng thủ 2 lớp: trên nhánh `demo-vulnerable`, gỡ `@permission_required` ở một trang dashboard nhưng cho trang đó chạy bằng kết nối `default`; khách gọi vào → MySQL trả "command denied", `security.log` ghi lại.
    - Tấn công SQLi trên bản lỗi: sqlmap đọc được dữ liệu nhưng không sửa được tồn kho/trạng thái đơn, không đọc `mysql.user`, không ghi file.
    - Cột SĐT là chuỗi mã hóa; `app_staff` đọc `v_staff_orders` chỉ thấy SĐT đã che; kết nối 3306 từ máy ngoài thất bại; xem audit log; khôi phục từ backup.

### E. Ghi log, giám sát, mã nguồn
- [ ] [BB] `security.log` ghi: đăng nhập thành công/thất bại, khóa tài khoản, đổi mật khẩu, truy cập trái phép, callback/upload bị từ chối (thời gian, user, IP, hành động, kết quả); dùng signal `user_logged_in`, `user_login_failed`.
- [ ] [BB] Không ghi mật khẩu, token, số thẻ, session ID vào log.
- [ ] [BB] Không commit bí mật; nếu lỡ commit thì đổi key ngay.
- [ ] [NL] `RotatingFileHandler`, file log quyền 640.
- [ ] [NL] Branch protection cho `main` (bắt buộc PR + 1 review), Dependabot, secret scanning.
- [ ] [NL] `bandit -r .` chạy trong GitHub Actions.
- [ ] [CĐ] Dashboard sự kiện bảo mật / email cảnh báo khi một IP đăng nhập sai quá 20 lần/giờ.
- Demo: chạy lại brute-force và IDOR rồi xem `security.log`; ảnh chụp kết quả bandit/Dependabot trước và sau.
