# PROJECT CONTEXT – Web bán sách đảm bảo an toàn bảo mật

> File ngữ cảnh của dự án. Đọc file này trước khi làm bất kỳ việc gì trong repo.
> Nguồn chốt: tài liệu "Yêu cầu bảo mật theo chức năng – Web bán sách" (chốt ngày 2026-11-09).

---

## 1. Thông tin chung

- **Môn:** An toàn ứng dụng Web và Cơ sở dữ liệu – Bộ môn ATTT, Khoa CNTT2, PTIT TP.HCM. GV: ThS. Phan Nghĩa Hiệp.
- **Đề tài:** Xây dựng trang web bán sách đảm bảo an toàn bảo mật. **Trọng tâm là bảo mật**, bán sách chỉ là bối cảnh.
- **Đối tượng:** (1) Khách hàng, (2) Quản trị viên kiêm quản lý sách.
- **Nhóm 5 người:** 2 backend, 2 frontend, 1 kiểm thử. Làm việc qua GitHub.
- **Repo:** https://github.com/TuanThanh05/secure-bookstore (nhánh `main`; tạo trên GitHub kèm commit "Initial commit" chỉ có README 1 dòng). Đẩy khung bước 1–4 lên trước khi làm bước 5 (2026-11-10) để cả nhóm theo dõi.

### Yêu cầu chấm điểm của đề

- **Bảo mật ứng dụng web – 60%:** ≥ 4 biện pháp bảo mật máy chủ/ứng dụng web và chống ≥ 4 dạng tấn công thường gặp (căn cứ slide chương 2, 3).
- **Bảo mật CSDL – 40%:** chống ≥ 5/10 lỗ hổng CSDL trên thực tế (căn cứ slide chương 5, 6).
- Làm càng nhiều biện pháp thì điểm phần đó càng cao.
- Ngôn ngữ cho phép: C, C++, Java, C#, PHP, Python. CSDL cho phép: SQL Server, Oracle, MySQL.
- **Nộp:** 1 thư mục gồm file Word đồ án, file PowerPoint ngắn gọn, source code, bảng phân công (trang cuối file Word).
- **Bị 0 điểm nếu:** vắng buổi vấn đáp, nộp thiếu hoặc sai định dạng hay sai ngôn ngữ, nộp trễ.
- Đồ án gồm 2 phần: cơ sở lý thuyết và code demo.

### 10 lỗ hổng CSDL (chương 5)

1. Mật khẩu yếu/mặc định
2. SQL Injection
3. Đặc quyền quá mức
4. Bật tính năng thừa
5. Quản lý cấu hình lỗi
6. Tràn bộ đệm
7. Leo thang đặc quyền
8. Từ chối dịch vụ (DoS)
9. CSDL không được vá
10. Dữ liệu không mã hóa

---

## 2. Quyết định đã chốt

- **Ngôn ngữ / framework:** Python 3.14 + **Django 6.1** (`Django~=6.1.0`, chốt 2026-11-10; có sẵn CSP nên không cần `django-csp`). Nếu thư viện phụ (`django-axes`, `django-otp`, `mysqlclient`) không tương thích thì lùi về Django 5.2 LTS. Môi trường ảo `.venv/` đặt ở thư mục gốc repo; `requirements.txt` ở thư mục gốc.
- **CSDL:** MySQL **8.4 LTS chạy bằng Docker Compose** (chốt 2026-11-10; `compose.yaml` ở thư mục gốc, image `mysql:8.4`). Django 6.1 bắt buộc MySQL ≥ 8.4 (8.0 bị từ chối: `NotSupportedError`). Driver `mysqlclient==2.3.0` (trên Arch build với `mariadb-libs`, chỉ là thư viện client; server vẫn là MySQL).
  - Cổng 3306 chỉ mở trên `127.0.0.1`; mạng Docker cố định `172.28.0.0/24`, MySQL thấy Django ở `172.28.0.1` nên các tài khoản ứng dụng có host `172.28.0.1`. `root` chỉ đăng nhập từ trong container (`MYSQL_ROOT_HOST=localhost`).
  - Bắt buộc TLS giữa Django và MySQL (`require_secure_transport = ON` + `OPTIONS["ssl_mode"] = "REQUIRED"`), chứng chỉ tự ký do image sinh.
  - Mật khẩu: `DB_CUSTOMER_PASSWORD`, `DB_STAFF_PASSWORD` trong `.env` (Django + Compose cùng đọc); `MYSQL_ROOT_PASSWORD`, `DB_MIGRATE_PASSWORD` trong `database/.env.db` (chỉ container đọc, không commit). `validate_password` MEDIUM, ≥ 12 ký tự.
  - Không dùng `django-browser-reload` (quyết định 2026-11-10); khi sửa code thì tự F5.
- **Triển khai:** Nginx (HTTPS) → Gunicorn (127.0.0.1:8000) → Django → MySQL (127.0.0.1:3306), chạy trên VM Ubuntu hoặc Docker Compose.
- **Cách làm:** bảo mật được thiết kế cùng chức năng (secure by design). Mỗi chức năng là một GitHub issue gồm cả yêu cầu chức năng lẫn yêu cầu bảo mật. Người kiểm thử xác nhận cả hai thì mới đóng issue.
- **Frontend:** template Django (HTML/CSS/JS) đặt trong thư mục `frontend/`, được Django render. **Không làm SPA** (React/Vue), vì JavaScript không có trong danh sách ngôn ngữ của đề và để giữ các lớp bảo vệ mặc định của Django (CSRF token trong form, auto-escape, cookie `HttpOnly`).
- **Phân quyền 2 lớp (web + CSDL):**
  - Lớp 1 (bắt buộc ở mọi view): Django kiểm tra đăng nhập, Group/permission, quyền sở hữu dữ liệu trước khi truy vấn; không đủ quyền thì trả 403/404.
  - Lớp 2: mỗi vai trò dùng **một tài khoản MySQL riêng**. Khách hàng và các trang thông thường dùng kết nối `default` (user `app_customer`); app `dashboard` của nhân viên dùng kết nối `staff` (user `app_staff`). Nếu lớp 1 bị bỏ sót, MySQL vẫn từ chối câu lệnh vượt quyền.
  - **Dữ liệu nghiệp vụ truy cập 100% gián tiếp** (chốt 2026-11-10): sách, thể loại, đánh giá, giỏ hàng, đơn hàng, thanh toán, audit log chỉ được **đọc qua view** và **ghi qua stored procedure** (`SQL SECURITY DEFINER`). `app_customer` và `app_staff` **không có quyền nào trên các bảng nghiệp vụ**; MySQL mặc định từ chối.
  - Ngoại lệ bắt buộc: bảng nội bộ của Django và thư viện (`accounts_user`, `auth_*`, `django_session`, `django_content_type`, `axes_*`, `otp_*`) do code có sẵn của Django đọc/ghi trực tiếp, với quyền tối thiểu theo từng bảng (chỉ `SELECT` trên `auth_*`, `accounts_user_groups`; không `DELETE` trên `accounts_user`). `core_securityevent` chỉ được `INSERT`.
  - **Chống leo thang quyền bằng trigger thay cho quyền theo cột** (đổi 2026-11-10): `user.save()` của Django luôn ghi mọi cột nên `GRANT UPDATE(cột)` làm hỏng đăng ký/đổi mật khẩu. Thay bằng trigger `trg_user_guard_insert`/`trg_user_guard_update` (`database/objects/10_...`): với `app_customer`, cấm tạo user `is_staff`/`is_superuser` = 1, cấm đổi 2 cột này, và trên dòng của nhân viên chỉ được đổi `last_login` (chặn ghi đè mật khẩu admin). Hệ quả: tạo admin bằng `createsuperuser` với `settings.migrate`; nhân viên đổi mật khẩu/hồ sơ trong app `dashboard` (kết nối `staff`).
  - Quyền cấp qua **role** MySQL `r_customer`, `r_staff` (tài khoản chỉ được gán role), file `database/grants/01_role_privileges.sql`.
  - Ai tạo gì: `bookstore_migrate` chỉ tạo/sửa **bảng** (Django `migrate`, gồm bảng nghiệp vụ qua migration `core/0001_business_schema` đọc `database/schema/01_tables.sql`). Trigger/view/thủ tục ở `database/objects/`, quyền ở `database/grants/`, do **root** chạy bằng `docker compose exec db sh /database/apply.sh`, `DEFINER = bookstore_definer@localhost` (khóa đăng nhập). Lý do: khi bật binlog, tạo trigger/thủ tục cần SUPER; không cấp cho migrate và không bật `log_bin_trust_function_creators`.
  - Danh sách dự kiến – khách (`app_customer`): view `v_public_books`, `v_public_categories`, `v_book_reviews`; thủ tục `sp_cart_add_item`, `sp_cart_update_item`, `sp_cart_remove_item`, `sp_my_cart`, `sp_my_orders`, `sp_my_order_detail`, `sp_place_order`, `sp_confirm_payment`, `sp_review_upsert`. Nhân viên (`app_staff`): view `v_staff_books`, `v_staff_orders` (SĐT che), `v_staff_reviews`, `v_audit_log`, `v_security_events`; thủ tục `sp_book_create`, `sp_book_update`, `sp_book_set_stock`, `sp_book_set_active`, `sp_category_save`, `sp_order_set_status`, `sp_review_set_visible`. `sp_cancel_expired_orders` chạy tự động bằng MySQL Event Scheduler.
  - Thủ tục đọc dữ liệu "của tôi" nhận `p_user_id` từ Django; kiểm tra quyền ở Django (lớp 1) vẫn bắt buộc.
  - Phía Django: model nghiệp vụ chỉ để đọc (`managed = False`, trỏ vào view); mọi thao tác ghi đi qua `services.py` gọi `callproc`. Không dùng `/admin/` mặc định cho bảng nghiệp vụ.
  - Phần `database/` nên có 2 người: BE 2 viết thủ tục/view cho khách, BE 1 viết thủ tục/view cho nhân viên.
  - Căn cứ lý thuyết: chương 6.2 "Bảo mật các đối tượng trong CSDL" (quyền `EXECUTE` cho thủ tục, `SELECT/INSERT/UPDATE/DELETE` cho bảng và khung nhìn).
- **Demo:** mỗi biện pháp có kịch bản tấn công bản lỗi thành công và bản an toàn bị chặn.
  - Nhánh `main` luôn là bản an toàn, cũng là bản nộp cuối.
  - Bản lỗi để ở **nhánh Git riêng `demo-vulnerable`**, chỉ tạo **sau khi `main` đã hoàn thiện**. Tạo nhánh từ `main`, cố ý gỡ từng biện pháp để demo. Mỗi lỗ hổng là một commit riêng, ghi rõ mục checklist trong message (ví dụ `vuln(6): bỏ select_for_update ở đặt đơn`).
  - Không bao giờ merge `demo-vulnerable` vào `main`. Không có cờ `DEMO_VULNERABLE` trong code.

### Lược đồ CSDL – bản v1 (chốt 2026-11-10)

- File: `database/schema/01_tables.sql` (từ bước 5; thay `database/scripts-secure-bookstore.sql` cũ – xóa file cũ). Bảng `accounts_user` không còn trong file này: Django tạo từ `accounts/models.py` với cột và 2 CHECK giống hệt. File chỉ có `CREATE TABLE` (không `CREATE DATABASE`, không `DROP`), migration `core/0001_business_schema` đọc và chạy. Bản thiết kế gốc (có `accounts_user`) lưu trong Project là `claude/database/01_schema.sql`. Đã chạy thử: 14 trường hợp dữ liệu sai đều bị chặn.
- Quy ước: tên bảng/cột tiếng Anh, chú thích tiếng Việt; tên bảng theo kiểu Django `<app>_<model>`; tiền là VND số nguyên `INT UNSIGNED`; thời gian `DATETIME(6)` theo UTC; cột `*_encrypted` chứa dữ liệu mã hóa AES-GCM dạng base64; InnoDB, `utf8mb4_unicode_ci`.
- Lược đồ sẽ được chi tiết dần trong quá trình phát triển. Mọi thay đổi phải sửa vào file này (và `models.py` tương ứng) rồi ghi lại ở đây.

| App | Bảng | Ghi chú bảo mật chính |
| --- | --- | --- |
| `accounts` | `accounts_user` | Custom User (cột khớp `AbstractUser` + `phone_encrypted`, `email_verified`); vai trò dùng Group của Django, không có bảng Role riêng |
| `catalog` | `catalog_category`, `catalog_book`, `catalog_review` | `cost_price` để demo quyền theo cột; CHECK giá > 0, kho ≥ 0, ISBN, rating 1–5; mỗi người một đánh giá/sách |
| `orders` | `orders_cart`, `orders_cartitem`, `orders_order`, `orders_orderitem` | Giỏ không lưu giá; số lượng 1–10; đơn có `code` UUID, `idempotency_key`, `expires_at`; CHECK máy trạng thái và `total = subtotal + shipping_fee`; địa chỉ/SĐT giao hàng mã hóa, nhập mỗi lần đặt (không có bảng Address) |
| `payments` | `payments_payment` | Cột sinh `success_transaction_id` UNIQUE: mỗi mã giao dịch chỉ thành công 1 lần (chống replay), vẫn lưu được các lần bị từ chối |
| `core` | `core_auditlog`, `core_securityevent` | AuditLog do trigger ghi; SecurityEvent do Django ghi (song song với `security.log`); không khóa ngoại, không ai có quyền UPDATE/DELETE |

- Không làm: mã giảm giá (Coupon), sổ địa chỉ (Address), bảng Role tự tạo.
- Django tự tạo khi `migrate`: `auth_group`, `auth_permission`, `auth_group_permissions`, `accounts_user_groups`, `accounts_user_user_permissions`, `django_session`, `django_admin_log`, `django_content_type`, `django_migrations`, `axes_*`, `otp_*`.
- Chuyển sang Django: viết `models.py` khớp đúng lược đồ (có thể sinh nháp bằng `python manage.py inspectdb`), về sau bảng thật do `migrate` tạo.

Các file CSDL còn lại (chưa viết; quy ước đặt tên xem `database/README.md`):

| File | Nội dung |
| --- | --- |
| `database/objects/20_v_*.sql` | View `v_public_books`, `v_staff_orders`... |
| `database/objects/30_sp_*.sql` | `sp_place_order`, `sp_confirm_payment`, `sp_cancel_expired_orders`... |
| `database/objects/1x_trg_audit_*.sql` | Trigger ghi `core_auditlog` cho `catalog_book`, `orders_order` |
| `database/backup/` | Script `mysqldump` + mã hóa |

Đã có từ bước 5: `init/01_users_roles.sh`, `config/my.cnf`, `schema/01_tables.sql`, `objects/10_trg_accounts_user_guard.sql`, `grants/01_role_privileges.sql`, `apply.sh`, `.env.db.example`, `README.md`.

### Phân loại

- **Chức năng nghiệp vụ (9):** Đăng ký · Đăng nhập/đăng xuất/quên mật khẩu · Xem sách & tìm kiếm · Đánh giá sách · Giỏ hàng & tạo đơn · Đặt đơn (race condition) · Thanh toán · Lịch sử đơn & hồ sơ · Admin quản lý sách & đơn.
- **Thành phần ngoài chức năng (5):** A. Quản lý phiên · B. Cấu hình Django & header · C. Máy chủ triển khai · D. Cơ sở dữ liệu · E. Ghi log, giám sát, mã nguồn.
- Race condition là yêu cầu bảo mật của chức năng đặt đơn, không phải chức năng riêng.

### Django mặc định đã bảo vệ (giữ nguyên, không phá, và demo được)

- SQLi qua ORM. Không bảo vệ khi dùng `raw()`/`cursor.execute` nối chuỗi.
- XSS qua auto-escape template. Không bảo vệ khi dùng `|safe`, `mark_safe`, `innerHTML`, hoặc chèn dữ liệu vào JS.
- CSRF qua `CsrfViewMiddleware`. Không bảo vệ khi đổi dữ liệu bằng GET hoặc dùng `@csrf_exempt`.
- Băm mật khẩu PBKDF2 có salt; 4 validator mật khẩu mặc định.
- Session: ID ngẫu nhiên lưu ở server, đổi ID khi đăng nhập, cookie `HttpOnly` + `SameSite=Lax`.
- Clickjacking: `X-Frame-Options: DENY`. Có sẵn `nosniff`, `Referrer-Policy`, `COOP`, kiểm tra `ALLOWED_HOSTS`.
- Token đặt lại mật khẩu có hạn; trang "đã gửi email" giống nhau dù email có tồn tại hay không.
- Upload: làm sạch tên file (chống path traversal), giới hạn kích thước request.

### Có sẵn nhưng phải cấu hình thêm

- Session: cờ `Secure`, timeout, hết phiên khi đóng trình duyệt.
- Validator mật khẩu riêng.
- HSTS, CSP, chuyển hướng HTTPS.
- `DEBUG=False`, `ALLOWED_HOSTS`, giấu `SECRET_KEY` (mặc định project mới để `DEBUG=True`).

### Quy tắc code chung (bắt buộc)

- Không dùng `raw()` hay `cursor.execute` nối chuỗi.
- Không dùng `|safe` hay `mark_safe` với dữ liệu người dùng.
- Không dùng `@csrf_exempt`. Không đổi dữ liệu bằng request GET.
- Không dùng `fields = '__all__'` trong form/serializer.
- Giá, tổng tiền, quyền sở hữu luôn kiểm tra và tính ở server.
- Không commit `.env` hay bất kỳ bí mật nào.

---

## 3. Cấu trúc thư mục

### Hiện trạng trên máy nhóm trưởng (cập nhật 2026-11-10, sau bước 4; bước 5 đang áp dụng)

```
secure-bookstore/                 # repo Git (git init -b main), chưa commit
├── backend/
│   ├── bookstore/                # __init__.py, urls.py, wsgi.py, asgi.py
│   │   └── settings/             # __init__.py, base.py, dev.py, prod.py
│   ├── core/ accounts/ catalog/ orders/ payments/ dashboard/   # bước 3
│   └── manage.py
├── database/scripts-secure-bookstore.sql   # = lược đồ v1 (bước 5 thay bằng database/schema/)
├── deploy/  docs/  security-tests/          # rỗng
├── frontend/
│   ├── README.md                            # quy tắc cho frontend (bước 4)
│   ├── static/css/base.css js/base.js img/favicon.svg
│   └── templates/base.html, layouts/{customer,auth,admin}.html,
│                 components/{navbar,footer,messages,admin_sidebar}.html,
│                 errors/{400,403,403_csrf,404,500}.html, shop/home.html,
│                 account/ dashboard/ (rỗng)
├── .env  (không commit)  .env.example  .gitignore
└── requirements.txt
```

Còn thiếu: `README.md`, `PROJECT_CONTEXT.md` ở gốc (bước 6).

### Cấu trúc đích

Repo GitHub `secure-bookstore`:

```
secure-bookstore/
├── backend/                 # Django (Python) – 2 người backend
│   ├── bookstore/           # cấu hình project
│   │   ├── settings/        # base.py, dev.py, prod.py
│   │   ├── urls.py          # URL gốc, nối URL của từng app
│   │   └── wsgi.py / asgi.py
│   ├── core/                # dùng chung: validator, mã hóa AES, security log, middleware, mixin phân quyền
│   ├── accounts/            # đăng ký, đăng nhập, khóa TK, 2FA, quên mật khẩu, hồ sơ
│   ├── catalog/             # sách, thể loại, tìm kiếm, đánh giá
│   ├── orders/              # giỏ hàng, đặt đơn (race condition), lịch sử đơn
│   ├── payments/            # cổng thanh toán giả lập, callback HMAC
│   ├── dashboard/           # trang quản trị cho nhân viên
│   └── manage.py
├── frontend/                # giao diện – 2 người frontend
│   ├── templates/
│   │   ├── base.html        # khung chung (nhóm trưởng)
│   │   ├── layouts/         # customer.html, auth.html, admin.html (nhóm trưởng)
│   │   ├── components/      # navbar, footer, book_card, pagination, messages (dùng chung)
│   │   ├── errors/          # 404.html, 500.html
│   │   ├── shop/            # home, danh sách/chi tiết sách, tìm kiếm, giỏ hàng, thanh toán
│   │   ├── account/         # đăng nhập, đăng ký, hồ sơ, lịch sử đơn
│   │   └── dashboard/       # quản lý sách, đơn, đánh giá
│   └── static/              # css/, js/ theo khu vực (base, shop, account, dashboard), img/; không JS inline
├── database/                # phần CSDL (40% điểm), xem database/README.md
│   ├── init/                # 01_users_roles.sh: container chạy 1 lần (role, 4 tài khoản, validate_password)
│   ├── config/my.cnf        # hardening MySQL
│   ├── schema/              # 01_tables.sql (bảng nghiệp vụ), Django migration đọc
│   ├── objects/             # 10_trg_*, 20_v_*, 30_sp_*: trigger, view, thủ tục (root chạy)
│   ├── grants/              # quyền của role và definer (root chạy)
│   ├── apply.sh             # chạy objects/ rồi grants/ trong container
│   ├── .env.db.example      # mẫu mật khẩu root/migrate (.env.db không commit)
│   └── backup/              # script mysqldump + mã hóa, hướng dẫn khôi phục
├── deploy/                  # nginx.conf, gunicorn, chứng chỉ demo
├── compose.yaml             # MySQL 8.4 cho dev (bước 5)
├── security-tests/          # script race condition, payload, cấu hình sqlmap/ZAP – người kiểm thử
│   └── evidence/            # ảnh chụp bằng chứng trước/sau
├── docs/                    # báo cáo, slide, sơ đồ, bảng phân công
├── PROJECT_CONTEXT.md       # file này
├── .env.example
├── .gitignore
├── requirements.txt         # ghim phiên bản thư viện
└── README.md
```

Ghi chú kỹ thuật:

- Trong `backend/bookstore/settings/base.py`, đặt `BASE_DIR` trỏ tới `backend/` (lưu ý file nằm sâu hơn một cấp nên dùng `Path(__file__).resolve().parent.parent.parent`) và khai báo thêm `FRONTEND_DIR = BASE_DIR.parent / 'frontend'`. Sau đó đặt `TEMPLATES[0]['DIRS'] = [FRONTEND_DIR / 'templates']`, `STATICFILES_DIRS = [FRONTEND_DIR / 'static']`.
- Chọn settings bằng biến môi trường `DJANGO_SETTINGS_MODULE=bookstore.settings.dev` (máy cá nhân) hoặc `bookstore.settings.prod` (triển khai). Cấu hình bảo mật mục A, B nằm chủ yếu trong `prod.py`.
- `STATIC_ROOT` (kết quả `collectstatic`) và `MEDIA_ROOT` (ảnh upload) nằm ngoài `frontend/` và được đưa vào `.gitignore`.
- Lệnh chạy: `cd backend && python manage.py runserver` khi phát triển; Gunicorn chạy từ `backend/` khi triển khai.
- File `.env` đặt ở thư mục gốc, không commit.
- `DATABASES` có 2 kết nối cùng DB `bookstore`: `default` (`DB_CUSTOMER_USER` = `app_customer`) và `staff` (`DB_STAFF_USER` = `app_staff`, `TEST: MIRROR default`). Trong app `dashboard`, mọi truy vấn dùng `.using("staff")` và `save(using="staff")`. Router `core.db_routers.MigrateOnDefaultRouter` chỉ cho migrate trên `default`. Lệnh cần quyền cao (`migrate`, `createsuperuser`, `test`) chạy với `DJANGO_SETTINGS_MODULE=bookstore.settings.migrate`: dùng `bookstore_migrate` cho cả 2 kết nối, mật khẩu nhập tay vào biến `DB_MIGRATE_PASSWORD` (`read -rs`), không nằm trong `.env`.
- Xác thực và session luôn đi qua kết nối `default`, nên `app_customer` cần quyền trên các bảng `auth_*`, `django_session`, `axes_*`, `otp_*`.
- Gọi procedure bằng `cursor.callproc("sp_place_order", [user_id, items_json])` trong `services.py` (tham số truyền riêng, không nối chuỗi). View đọc qua model `managed = False`, `db_table = "v_staff_orders"`.
- Lỗi quyền từ MySQL (`OperationalError` 1142 "command denied") được bắt, ghi `security.log` và trả trang 403.

### Backend: các app và quy ước

| App | Chức năng | Mục checklist | Người làm |
| --- | --- | --- | --- |
| `core` | Validator mật khẩu, mã hóa AES cột nhạy cảm, ghi `security.log`, middleware header, mixin phân quyền | B, E, D(10) | Nhóm trưởng / BE 1 |
| `accounts` | Đăng ký, đăng nhập, khóa tài khoản, 2FA, quên mật khẩu, hồ sơ | 1, 2, 8 (hồ sơ), A | BE 1 |
| `catalog` | Sách, thể loại, tìm kiếm, đánh giá | 3, 4 | BE 1 |
| `orders` | Giỏ hàng, đặt đơn (race condition), lịch sử đơn | 5, 6, 8 | BE 2 |
| `payments` | Cổng thanh toán giả lập, callback HMAC (API thật duy nhất, server-to-server) | 7 | BE 2 |
| `dashboard` | Trang quản trị cho nhân viên: sách, đơn, đánh giá, upload ảnh | 9 | BE 1 |

Cấu trúc mỗi app: `models.py` (bảng + ràng buộc), `forms.py` (kiểm tra đầu vào; mọi dữ liệu người dùng đi qua form), `views.py` (giữ mỏng: kiểm tra quyền → gọi form/service → render/redirect), `services.py` (logic nghiệp vụ quan trọng: đặt đơn, trừ kho, xác minh thanh toán), `urls.py` (có `app_name`), `admin.py`, `migrations/`, `tests/` (gồm test bảo mật).

Thứ tự làm backend:
1. Bộ khung trên `main` (nhóm trưởng): settings đã tách, đọc `.env`, kết nối MySQL bằng user ít quyền, 6 app trống, `urls.py` gốc, `core` có sẵn hàm ghi log bảo mật.
2. Viết models khớp lược đồ v1 (`database/schema/01_tables.sql`; `managed = False`): User, Category, Book, Review, Cart, CartItem, Order, OrderItem, Payment, AuditLog, SecurityEvent.
3. Sau đó mới chia nhánh tính năng.

### Frontend: kế thừa template và phạm vi

- 3 tầng: `base.html` khoan các block (`title`, `extra_css`, `body`, `extra_js`) → `layouts/*.html` điền `body` và khoan `content` → trang con chỉ điền `title`, `content`, khi cần thì `extra_css`, `extra_js`.
- Nhóm trưởng giữ `base.html`, `layouts/`, `components/`; sửa các file này phải qua nhóm trưởng (đặt `CODEOWNERS`). FE 1 làm `shop/` + `account/`; FE 2 làm `dashboard/`. Mỗi người chỉ sửa CSS/JS của khu vực mình.
- Mỗi file dùng `{% static %}` phải có `{% load static %}`. Mọi `<form method="post">` có `{% csrf_token %}`. Không `|safe`, không JS/CSS inline (kể cả `style="..."`, `onclick="..."`), không `innerHTML`, không tải tài nguyên ngoài (CDN). Comment nhiều dòng dùng `{% comment %}`. Chi tiết: `frontend/README.md`.
- Template chỉ hiển thị; kiểm tra quyền luôn làm ở view, không dựa vào việc ẩn nút.

### Giao tiếp frontend – backend

- Không có API kiểu SPA. Django nhận request → view lấy dữ liệu → `render(request, "<template>", {context})` → trả HTML hoàn chỉnh.
- Gửi dữ liệu lên bằng `<form method="post">`; view xử lý xong thì `redirect` (Post/Redirect/Get).
- Ngoại lệ trả JSON: AJAX nhỏ (cập nhật giỏ hàng, gợi ý tìm kiếm) dùng `fetch` + header `X-CSRFToken`, hiển thị bằng `textContent`; callback thanh toán (server-to-server, kiểm tra HMAC). Không bật CORS.
- Hợp đồng giữa hai bên đặt trong `docs/contract.md`: mỗi trang ghi URL name, template, biến context backend truyền vào, trường form/AJAX gửi lên. Frontend dựng giao diện với dữ liệu giả theo bảng này, backend viết view sau.

Thư mục nộp bài (thay số nhóm và hỏi lại GV quy định đặt tên):

```
NhomXX_ATUDW-CSDL_WebBanSachAnToan/
├── NhomXX_BaoCao.docx        # bảng phân công ở trang cuối
├── NhomXX_ThuyetTrinh.pptx
└── SourceCode/               # không kèm .env, venv, .git
```

---

### Tiến độ dựng khung trên `main`

| Bước | Nội dung | Trạng thái |
| --- | --- | --- |
| 1 | Bỏ `assets/`, tạo `.venv` (Python 3.14.9), cài Django 6.1.3, `.gitignore`, `git init -b main` ở thư mục gốc | Xong |
| 2 | `manage.py` (mặc định dev), `bookstore/urls.py`, `wsgi.py`/`asgi.py` (mặc định prod), `settings/base.py`/`dev.py`/`prod.py`, `.env.example`, `requirements.txt`; `check` và `check --deploy` sạch; `DATABASES = {}` tạm thời | Xong |
| 3 | 6 app (`core`, `accounts`, `catalog`, `orders`, `payments`, `dashboard`) đăng ký trong `LOCAL_APPS`; Custom User `accounts.User` + `AUTH_USER_MODEL`; mỗi app có `apps.py`, `urls.py` (`app_name`), `views.py`, `models.py`, `admin.py` (chỉ ghi chú), `tests/`; `services.py` ở catalog/orders/payments/dashboard | Xong (`check` sạch, đã sinh `accounts/migrations/0001_initial.py`); chưa chạy `migrate` |
| 4 | Khung frontend: `base.html`, 3 layout (`customer`/`auth`/`admin`), components (`navbar`, `footer`, `messages`, `admin_sidebar`), trang lỗi 400/403/403_csrf/404/500, `base.css`, `base.js` (`Bookstore.postForm` gửi CSRF), favicon, `frontend/README.md`; trang chủ tạm `catalog:home`; `include("catalog.urls")`; `handler400/403/404/500` và `CSRF_FAILURE_VIEW` trỏ về `core.views` | Xong trên máy; lần đẩy đầu lên GitHub (commit `bff7e92`) thiếu một phần (`urls.py` gốc rỗng, chưa có view `catalog:home`, 2 thẻ `<title>`, thiếu `favicon.svg`, `frontend/README.md`, `tests/__init__.py`, `accounts/app.py` sai tên) → gói `sua-buoc4.zip` |
| 5 | `compose.yaml` (MySQL 8.4), `database/` (init, config, schema, objects, grants, `apply.sh`), `DATABASES` 2 kết nối + TLS, router, `settings/migrate.py`, migration `core/0001_business_schema`, `mysqlclient`; `migrate` lần đầu + `apply.sh` + `createsuperuser` | Đã gửi gói `buoc5-mysql.zip` (thử trên MySQL 8.0 trong sandbox, vì không tải được image 8.4), chờ áp dụng |
| 6 | README, CODEOWNERS, mẫu PR/issue, commit đầu tiên, đẩy lên GitHub, bật branch protection | |

Lưu ý kỹ thuật đã gặp:
- `python manage.py startapp <tên>` báo lỗi "conflicts with the name of an existing Python module" nếu thư mục app rỗng đã tồn tại; phải `rmdir` trước rồi mới `startapp`.
- File tải về bắt đầu bằng dấu chấm (`.gitignore`, `.env.example`) có thể bị trình duyệt bỏ dấu chấm; kiểm tra bằng `ls -a`. `tree` cần `-a` mới hiện file ẩn.
- Chỉ có một repo Git ở thư mục gốc; không `git init` trong thư mục con.
- Comment template: `{# ... #}` chỉ dùng cho MỘT dòng; comment nhiều dòng bằng `{# #}` bị in thẳng ra HTML (lộ ghi chú nội bộ). Nhiều dòng phải dùng `{% comment %}...{% endcomment %}`.
- Test client của Django không phục vụ `/static/` (trả 404); kiểm tra file static bằng `runserver` thật.
- Trang 500 render không cần request (không dùng layout có navbar/messages) vì lỗi có thể do CSDL.
- Custom User: username theo regex `^[A-Za-z0-9._-]{3,50}$` (`max_length=50`, nhóm trưởng đổi từ 150 xuống 50; migration `0001_initial` đã sinh theo 50), email bắt buộc và unique, có `phone_encrypted`, `email_verified`, 2 CHECK constraint giống lược đồ.
- File cấu hình app phải tên `apps.py` (đặt nhầm `app.py` thì Django lặng lẽ dùng AppConfig mặc định, mất `verbose_name`, không báo lỗi).
- `.gitignore` có `.env.*` + `!.env.example` sẽ bỏ qua luôn `database/.env.db.example` → cần thêm `!*.env*.example` hoặc `!database/.env.db.example` ở bước 5.
- Django 6.1 từ chối MySQL < 8.4 (`NotSupportedError: MySQL 8.4 or later is required`).
- Khi binlog bật, `CREATE TRIGGER`/`PROCEDURE` cần SUPER (lỗi 1419) → trigger/thủ tục do root tạo qua `apply.sh`, không qua migration.
- Trigger chạy bằng quyền của DEFINER: definer cần `TRIGGER` và `SELECT` trên bảng (thiếu `SELECT` thì lỗi 1143 khi đọc `NEW.cột`). Trong trigger, `USER()` là tài khoản gọi, `CURRENT_USER()` là definer.
- `GRANT` trên tên CSDL có `_` phải viết `test\_bookstore` (`_` là ký tự đại diện).
- Script trong `docker-entrypoint-initdb.d` dạng `.sh` không có quyền thực thi được entrypoint `source` (dùng được `docker_process_sql`); không đặt `set -u` trong đó. `IDENTIFIED BY RANDOM PASSWORD` in mật khẩu ra log, không dùng.
- `RunSQL` với chuỗi nhiều câu lệnh: Django tách bằng `sqlparse`; tự tách và bỏ câu rỗng (chỉ còn chú thích) để tránh lỗi "Query was empty".
- CSDL tạm của `manage.py test` không có trigger/phân quyền; kiểm tra phân quyền trên CSDL dev.
- Việc cần nhớ ở bước accounts: nếu Django nâng số vòng băm PBKDF2, lần đăng nhập đầu của nhân viên sẽ tự lưu lại mật khẩu bằng `app_customer` và bị trigger chặn → cần xử lý (bắt lỗi hoặc băm lại qua kết nối `staff`).

## 4. Checklist bảo mật theo chức năng

Ký hiệu: **[BB]** bắt buộc · **[NL]** nên làm · **[CĐ]** cộng điểm.

### 1. Đăng ký
- Django lo: băm mật khẩu, 4 validator, CSRF, ORM.
- [ ] [BB] Validator riêng: chữ hoa, chữ thường, số, ký tự đặc biệt, tối thiểu 10 ký tự.
- [ ] [BB] Kiểm tra đầu vào ở server bằng Django Form (email, SĐT regex, độ dài họ tên, ký tự username).
- [ ] [BB] Chống mass assignment: form chỉ khai báo trường cho phép, không gửi được `is_staff`/`is_superuser`.
- [ ] [NL] Xác minh email: `is_active=False` cho tới khi bấm link có token 24 giờ.
- [ ] [NL] CAPTCHA.
- [ ] [CĐ] Kiểm tra mật khẩu đã bị lộ qua Have I Been Pwned (k-anonymity).
- Demo: Burp thêm `is_staff=1` → vẫn là khách thường; mật khẩu `12345678` bị từ chối; `auth_user` lưu `pbkdf2_sha256$...`.

### 2. Đăng nhập, đăng xuất, quên mật khẩu
- Django lo: đổi session ID khi đăng nhập, so sánh mật khẩu an toàn, token reset có hạn.
- Django KHÔNG có: giới hạn đăng nhập sai, khóa tài khoản, 2FA, CAPTCHA.
- [ ] [BB] Sai 5 lần thì khóa 15 phút, theo username và IP (`django-axes`).
- [ ] [BB] Thông báo lỗi chung cho mọi trường hợp sai.
- [ ] [BB] Đăng xuất bằng POST, xóa session ở server.
- [ ] [BB] Chống open redirect với `next` (`url_has_allowed_host_and_scheme`).
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
    - `app_customer@172.28.0.1` (role `r_customer`): `SELECT` trên các view công khai; `EXECUTE` trên các thủ tục của khách (xem mục 2); `SELECT, INSERT, UPDATE` trên `accounts_user` (trigger chặn leo thang), `SELECT` trên `auth_*`/`accounts_user_groups`, CRUD trên `django_session`; `INSERT` trên `core_securityevent`. **Không có quyền nào trên bảng nghiệp vụ.** (Phần Django đã làm ở bước 5.)
    - `app_staff@172.28.0.1` (role `r_staff`): `SELECT` trên các view nhân viên; `EXECUTE` trên các thủ tục nhân viên; quyền theo cột trên các bảng auth; `INSERT` trên `core_securityevent`. **Không có quyền nào trên bảng nghiệp vụ**, không đọc được SĐT/địa chỉ gốc.
    - `bookstore_definer@localhost`: tài khoản **khóa đăng nhập** (`ACCOUNT LOCK`), chỉ dùng làm definer cho thủ tục và view; có quyền trên bảng nghiệp vụ.
    - `bookstore_migrate@172.28.0.1`: `SELECT, INSERT, UPDATE, DELETE, CREATE, DROP, ALTER, INDEX, REFERENCES` trên `bookstore.*` (+ toàn quyền trên `test\_bookstore.*`); chỉ dùng khi chạy migrate/createsuperuser/test. Không tạo được trigger/view/thủ tục (root làm qua `apply.sh`).
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

---

## 6. Đối chiếu yêu cầu đề

| Dạng tấn công (ch.2) | Mục |
| --- | --- |
| SQL Injection | 3, D |
| XSS (reflected, stored, DOM) | 3, 4, B |
| CSRF | mọi form, 2, 5 |
| Tấn công xác thực (brute-force, dò tài khoản) | 1, 2 |
| Khiếm khuyết thiết kế: sửa tham số, IDOR, race condition | 5, 6, 7, 8 |
| Chiếm phiên, tái sử dụng cookie | A |
| Clickjacking | B |
| Upload file độc hại | 9, C |

| Biện pháp (ch.3) | Mục |
| --- | --- |
| Bảo mật máy chủ web bằng cấu hình | C |
| Xác thực mạnh | 1, 2 |
| Trao quyền, quyền tối thiểu (web + tài khoản MySQL theo vai trò) | 8, 9, D |
| Bảo mật phiên | A |
| Bảo mật hệ thống file | 9, C |
| SSL/TLS | B, C |
| Kiểm tra đầu vào, xử lý ngoại lệ, ghi log | tất cả, B, E |

**CSDL:** riêng các mục [BB] trong D đã phủ 7/10 lỗ hổng (1, 2, 3, 4, 5, 7, 10). Ngoài ra trình bày được cơ chế bảo mật đối tượng CSDL (chương 6.2): tài khoản theo vai trò, quyền `EXECUTE` trên thủ tục, quyền trên khung nhìn, quyền theo cột.

**Thứ tự ưu tiên nếu ít thời gian:**
1. Mục 5, 6, 8
2. Mục D
3. Mục 2, A, B, C
4. Mục 3, 4

## 7. Gợi ý phân công

- **Nhóm trưởng:** bộ khung trên `main` (settings, `base.html`, `layouts/`, `components/`, app `core`), review PR, giữ `CODEOWNERS`.
- **Backend 1:** app `accounts`, `catalog`, `dashboard` (mục 1, 2, 3, 4, 9, A).
- **Backend 2:** app `orders`, `payments` và thư mục `database/` (mục 5, 6, 7, 8, D).
- **Frontend 1:** `templates/shop/`, `templates/account/` và CSS/JS tương ứng.
- **Frontend 2:** `templates/dashboard/` và CSS/JS tương ứng. Một trong hai bạn frontend kiêm mục C (Nginx/HTTPS).
- Chung cho frontend: không `|safe`/`innerHTML`, không JS inline (CSP), CAPTCHA, form OTP, trang lỗi riêng.
- **Kiểm thử:** xác nhận issue trước khi đóng; viết script trong `security-tests/`; sau khi `main` hoàn thiện thì cùng backend dựng nhánh `demo-vulnerable`, chạy Burp/sqlmap/ZAP/nikto/script race condition, lưu bằng chứng vào `security-tests/evidence/`.

Phạm vi thư mục: backend làm trong `backend/` và `database/`; frontend làm trong `frontend/`; người kiêm mục C làm trong `deploy/`; kiểm thử làm trong `security-tests/`; cả nhóm cùng viết `docs/`.
