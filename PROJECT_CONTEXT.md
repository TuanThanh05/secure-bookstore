# PROJECT CONTEXT – Web bán sách đảm bảo an toàn bảo mật

> File ngữ cảnh của dự án. Đọc file này trước khi làm bất kỳ việc gì trong repo.
> Nguồn chốt: tài liệu "Yêu cầu bảo mật theo chức năng – Web bán sách" (chốt ngày 2026-11-09).

---

## 1. Thông tin chung

- **Môn:** An toàn ứng dụng Web và Cơ sở dữ liệu – Bộ môn ATTT, Khoa CNTT2, PTIT TP.HCM. GV: ThS. Phan Nghĩa Hiệp.
- **Đề tài:** Xây dựng trang web bán sách đảm bảo an toàn bảo mật. **Trọng tâm là bảo mật**, bán sách chỉ là bối cảnh.
- **Đối tượng:** (1) Khách hàng, (2) Quản trị viên kiêm quản lý sách.
- **Nhóm 5 người:** 2 backend, 2 frontend, 1 kiểm thử. Làm việc qua GitHub.
- **Repo:** https://github.com/TuanThanh05/secure-bookstore (nhánh `main`; tạo trên GitHub kèm commit "Initial commit" chỉ có README 1 dòng). Lịch sử đã được viết lại 2026-11-11 để mọi commit dùng email `...@users.noreply.github.com` (không lộ email cá nhân); repo public.

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
- **CSDL:** MySQL **8.4 LTS** (Django 6.1 từ chối 8.0 và MariaDB/XAMPP). Driver `mysqlclient==2.3.0` (Arch: build với `mariadb-libs`; Windows: có wheel sẵn).
  - **Cách dựng đa nền tảng (chốt 2026-11-11):** Docker là tùy chọn. Nhóm trưởng (Arch) dùng `compose.yaml` (image `mysql:8.4`, bật/tắt theo nhu cầu bằng `up`/`down`, không tự khởi động lại, dữ liệu trong volume `mysql_data`). Các bạn Windows cài MySQL 8.4 bằng MySQL Installer. Mọi máy chạy cùng 4 lệnh: `db_setup` → `migrate --settings=bookstore.settings.migrate` → `db_apply` → `runserver` (hướng dẫn: `database/README.md`).
  - `python manage.py db_setup` (root): tạo CSDL, cài `validate_password` (MEDIUM, ≥ 12, lưu bằng `SET PERSIST`), role `r_customer`/`r_staff`, tài khoản `app_customer`, `app_staff`, `bookstore_migrate` theo **host mà MySQL thấy máy này** (tự dò bằng `USER()`: Docker `172.28.0.1` – đã xác nhận trên máy nhóm trưởng 2026-11-11; cài thường `127.0.0.1`/`localhost`), `bookstore_definer@localhost` khóa đăng nhập. Chạy lại để đồng bộ mật khẩu.
  - `python manage.py db_apply` (root): chạy `database/objects/*.sql` rồi `database/grants/*.sql` (hiểu `DELIMITER`).
  - Docker: cổng chỉ mở trên `127.0.0.1`; mạng cố định `172.28.0.0/24` (gateway `172.28.0.1` không đổi sau down/up); `MYSQL_ROOT_HOST=172.28.0.%` (root chỉ vào được từ chính máy này).
  - Bắt buộc TLS giữa Django và MySQL (`OPTIONS["ssl_mode"] = "REQUIRED"`; máy demo thêm `require_secure_transport = ON` trong `my.cnf`).
  - Mật khẩu: `DB_CUSTOMER_PASSWORD`, `DB_STAFF_PASSWORD` trong `.env`; `MYSQL_ROOT_PASSWORD`, `DB_MIGRATE_PASSWORD` trong `database/.env.db` (không commit; chỉ Docker, `db_setup`/`db_apply` và `settings/migrate.py` đọc — web lúc chạy không đọc).
  - `my.cnf` hardening đầy đủ chỉ bắt buộc trên máy demo (Docker của nhóm trưởng).
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
  - Ai tạo gì: `bookstore_migrate` chỉ tạo/sửa **bảng** (Django `migrate`, gồm bảng nghiệp vụ qua migration `core/0001_business_schema` đọc `database/schema/01_tables.sql`). Trigger/view/thủ tục ở `database/objects/`, quyền ở `database/grants/`, do **root** chạy bằng `python manage.py db_apply`, `DEFINER = bookstore_definer@localhost` (khóa đăng nhập). Lý do: khi bật binlog, tạo trigger/thủ tục cần SUPER; không cấp cho migrate và không bật `log_bin_trust_function_creators`.
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

Đã có từ bước 5: `config/my.cnf`, `schema/01_tables.sql`, `objects/10_trg_accounts_user_guard.sql`, `grants/01_role_privileges.sql`, `.env.db.example`, `README.md`; lệnh `core/management/commands/db_setup.py`, `db_apply.py` (+ `core/dbadmin.py`).

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

### Hiện trạng (cập nhật 2026-11-11: `main` sau bước 6; bước 7 đang ở nhánh `feature/frontend-home`)

```
secure-bookstore/                 # repo Git, nhánh main
├── backend/
│   ├── bookstore/                # __init__.py, urls.py, wsgi.py, asgi.py
│   │   └── settings/             # __init__.py, base.py, dev.py, prod.py, migrate.py
│   ├── core/                     # views (trang lỗi), validators.py, templatetags/bookstore.py, db_routers.py, dbadmin.py,
│   │                             # management/commands/db_setup.py, db_apply.py, migrations/0001_business_schema.py
│   ├── accounts/ catalog/ orders/ payments/ dashboard/
│   └── manage.py
├── database/                     # README.md, .env.db.example, config/, schema/, objects/, grants/
├── deploy/  docs/  security-tests/          # bước 6 thêm .gitkeep, docs/contract.md, security-tests/README.md
├── frontend/
│   ├── README.md                            # quy tắc cho frontend (bước 4)
│   ├── static/css/{fonts,base,shop}.css js/base.js fonts/ (woff2 + OFL) img/{favicon,icons}.svg
│   └── templates/base.html, layouts/{customer,auth,admin}.html,
│                 components/{navbar,footer,messages,admin_sidebar,icon,book_card,search_bar,category_filter}.html,
│                 errors/{400,403,403_csrf,404,500}.html, shop/{home,about}.html,
│                 account/ dashboard/ (rỗng)
├── .github/  CONTRIBUTING.md  compose.yaml  README.md  PROJECT_CONTEXT.md  SECURITY_CHECKLIST.md
├── .env, database/.env.db (không commit)  .env.example  .gitignore
└── requirements.txt
```

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
│   ├── config/my.cnf        # hardening MySQL (container Docker)
│   ├── schema/              # 01_tables.sql (bảng nghiệp vụ), Django migration đọc
│   ├── objects/             # 10_trg_*, 20_v_*, 30_sp_*: trigger, view, thủ tục (root chạy)
│   ├── grants/              # quyền của role và definer (root chạy bằng db_apply)
│   ├── .env.db.example      # mẫu mật khẩu root/migrate (.env.db không commit)
│   └── backup/              # script mysqldump + mã hóa, hướng dẫn khôi phục
├── deploy/                  # nginx.conf, gunicorn, chứng chỉ demo
├── compose.yaml             # MySQL 8.4 bằng Docker (tùy chọn, bước 5)
├── security-tests/          # script race condition, payload, cấu hình sqlmap/ZAP – người kiểm thử
│   └── evidence/            # ảnh chụp bằng chứng trước/sau
├── docs/                    # báo cáo, slide, sơ đồ, bảng phân công
├── PROJECT_CONTEXT.md       # file này
├── SECURITY_CHECKLIST.md    # checklist bảo mật (mục 4, 5)
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
- `DATABASES` có 2 kết nối cùng DB `bookstore`: `default` (`DB_CUSTOMER_USER` = `app_customer`) và `staff` (`DB_STAFF_USER` = `app_staff`, `TEST: MIRROR default`). Trong app `dashboard`, mọi truy vấn dùng `.using("staff")` và `save(using="staff")`. Router `core.db_routers.MigrateOnDefaultRouter` chỉ cho migrate trên `default`. Lệnh cần quyền cao (`migrate`, `createsuperuser`, `test`) chạy với `--settings=bookstore.settings.migrate`: dùng `bookstore_migrate` cho cả 2 kết nối, mật khẩu lấy từ `DB_MIGRATE_PASSWORD` trong biến môi trường hoặc `database/.env.db`, không nằm trong `.env`.
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

### Frontend: giao diện (chốt 2026-11-11)

- Thiết kế gốc làm bằng Google Stitch (`DESIGN.md`, `code.html`, `screen.png` của nhóm trưởng), rồi rút gọn và chuyển sang template Django.
- **CSS thuần**, không Tailwind, không framework. Màu, khoảng cách, bo góc khai báo bằng biến CSS ở đầu `base.css`: nền giấy `#fbf9f6`, chữ `#1b1c1a`, đỏ đô `--color-primary #8b1e2f`, vàng sao `#c29800`, viền `#e8e3dc`. CSS trang khách ở `shop.css`.
- **Thương hiệu "Secure Bookstore"**. Toàn bộ chữ trên web bằng **tiếng Việt**.
- **Header** chỉ có: logo, Giới thiệu, Đăng nhập, Đăng ký (khi đã đăng nhập: tên người dùng + nút Đăng xuất dạng form POST). Không có "bộ sưu tập tuyển chọn".
- **Footer** tối giản: "Secure Bookstore", "Thiết kế và phát triển bởi **Nhóm 7**", dòng tên môn · PTIT TP.HCM · năm. Không có trích dẫn, đăng ký nhận tin, cột link.
- **Trang chủ** `catalog:home`: hero, ô tìm kiếm (GET `q`), chip lọc thể loại ("Tất cả" là bỏ lọc, GET `category`), lưới thẻ sách (4/3/2 cột theo độ rộng màn hình). Trang `catalog:about` (`/gioi-thieu/`) giới thiệu đồ án.
- **Font tự host** (CSP cấm Google Fonts): Playfair Display (tiêu đề) và Plus Jakarta Sans (chữ thường), bản variable, các subset latin, latin-ext, vietnamese, giấy phép OFL. **Icon**: sprite SVG Material Symbols (Apache 2.0) `static/img/icons.svg`, gọi bằng `components/icon.html`.
- **Component nhận dữ liệu qua tham số** (`{% include ... with ... %}`): `book_card` (`book`, `cart_add_url`), `search_bar`, `category_filter`, `icon`. Thẻ sách có ảnh bìa nếu `cover_url` có giá trị, không thì hiện bìa tạm có màu (filter `tone`). Hết hàng thì hiện nhãn và khóa nút giỏ. Form thêm giỏ chỉ gửi `book_id` + `quantity`, không gửi giá.
- Filter riêng `core/templatetags/bookstore.py`: `vnd` (420000 → "420.000 ₫"), `stars` (điểm → 5 icon sao đầy/nửa/rỗng), `tone`.
- Dữ liệu tạm: `catalog/services.py` trả dataclass `Category`, `BookCard` (tên thuộc tính trùng cột view `v_public_books` sẽ tạo) với 8 cuốn sách giả. Khi có view thì chỉ thay phần thân hàm `list_categories()` / `list_public_books()`; view và template giữ nguyên.
- Kiểm tra đầu vào GET dùng chung `core/validators.py`: `parse_positive_int` (chỉ chữ số ASCII, > 0, tối đa 9 chữ số; sai thì bỏ qua, không báo lỗi) và `clean_search_query` (gộp khoảng trắng, cắt 100 ký tự). Thể loại không có trong danh sách thì coi như "Tất cả".

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
| 4 | Khung frontend: `base.html`, 3 layout (`customer`/`auth`/`admin`), components (`navbar`, `footer`, `messages`, `admin_sidebar`), trang lỗi 400/403/403_csrf/404/500, `base.css`, `base.js` (`Bookstore.postForm` gửi CSRF), favicon, `frontend/README.md`; trang chủ tạm `catalog:home`; `include("catalog.urls")`; `handler400/403/404/500` và `CSRF_FAILURE_VIEW` trỏ về `core.views` | Xong (lần đẩy đầu thiếu một phần, đã sửa bằng gói `sua-buoc4.zip`, commit `07ff42a`) |
| 5 | `compose.yaml` (MySQL 8.4, tùy chọn), `database/` (config, schema, objects, grants, README), lệnh `db_setup`/`db_apply`, `DATABASES` 2 kết nối + TLS, router, `settings/migrate.py`, migration `core/0001_business_schema`, `mysqlclient`; `db_setup` + `migrate` + `db_apply` + `createsuperuser` | Xong (commit `b7e2a36`, 2026-11-11): nhóm trưởng chạy được trên Arch + Docker; bản trên GitHub đã clone về chạy lại đủ 5 lệnh và các phép thử tấn công trong sandbox. Docker trên Arch cần `sudo docker compose ...` (cố ý không thêm user vào nhóm `docker` vì nhóm đó ngang quyền root) |
| 6 | `.github/` (CODEOWNERS, mẫu PR, mẫu issue Chức năng/Lỗi, `dependabot.yml`, CI `workflows/ci.yml`: MySQL 8.4 service → `db_setup` → `migrate` → `db_apply` → `check` → `check --deploy` → `makemigrations --check` → `test` → `bandit`), `CONTRIBUTING.md` (quy trình nhánh/PR/commit), `docs/contract.md` (mẫu hợp đồng FE–BE), `security-tests/README.md`, `.gitkeep` cho thư mục rỗng; cài đặt trên GitHub: ruleset bảo vệ `main`, Dependabot, secret scanning + push protection, mời collaborator | Đã gửi gói `buoc6-github.zip` 2026-11-11 (CI mô phỏng đủ các bước trong sandbox), chờ áp dụng và bật cài đặt trên GitHub |
| 7 | Trang chủ theo thiết kế Stitch (nhánh `feature/frontend-home`): `fonts.css` + font tự host, sprite icon, `base.css` viết lại theo bộ màu mới, `shop.css`, components `icon`/`book_card`/`search_bar`/`category_filter`, navbar + footer mới, `shop/home.html`, `shop/about.html`, `core/validators.py`, filter `bookstore`, dữ liệu giả trong `catalog/services.py`, 16 test; cập nhật `docs/contract.md` (biến của `catalog:home`, `catalog:about`, bảng BookCard) và `frontend/README.md` | Đã gửi gói `frontend-home.zip` 2026-11-11 (test, `check --deploy`, bandit sạch; đã xem trên Chrome desktop/mobile: không lỗi console, không vi phạm CSP), chờ mở PR |

Lưu ý kỹ thuật đã gặp:
- `python manage.py startapp <tên>` báo lỗi "conflicts with the name of an existing Python module" nếu thư mục app rỗng đã tồn tại; phải `rmdir` trước rồi mới `startapp`.
- File tải về bắt đầu bằng dấu chấm (`.gitignore`, `.env.example`) có thể bị trình duyệt bỏ dấu chấm; kiểm tra bằng `ls -a`. `tree` cần `-a` mới hiện file ẩn.
- Chỉ có một repo Git ở thư mục gốc; không `git init` trong thư mục con.
- Comment template: `{# ... #}` chỉ dùng cho MỘT dòng; comment nhiều dòng bằng `{# #}` bị in thẳng ra HTML (lộ ghi chú nội bộ). Nhiều dòng phải dùng `{% comment %}...{% endcomment %}`.
- Test client của Django không phục vụ `/static/` (trả 404); kiểm tra file static bằng `runserver` thật.
- Trang 500 render không cần request (không dùng layout có navbar/messages) vì lỗi có thể do CSDL.
- Custom User: username theo regex `^[A-Za-z0-9._-]{3,50}$` (`max_length=50`, chốt 2026-11-11, đổi từ 150; migration `0001_initial` đã sinh theo 50), email bắt buộc và unique, có `phone_encrypted`, `email_verified`, 2 CHECK constraint giống lược đồ.
- File cấu hình app phải tên `apps.py` (đặt nhầm `app.py` thì Django lặng lẽ dùng AppConfig mặc định, mất `verbose_name`, không báo lỗi).
- `.gitignore` có `.env.*` + `!.env.example` sẽ bỏ qua luôn `database/.env.db.example` → bước 5 thêm dòng `!database/.env.db.example`.
- Với MySQL, ngay cả `manage.py check` cũng cần kết nối CSDL (Django đọc phiên bản server khi kiểm tra field) → MySQL phải đang chạy và `db_setup` đã chạy; CI vì vậy có MySQL service.
- Docker trên Arch: dùng `sudo docker compose ...`; không thêm user vào nhóm `docker` (ngang quyền root).
- Django 6.1 từ chối MySQL < 8.4 (`NotSupportedError: MySQL 8.4 or later is required`).
- Khi binlog bật, `CREATE TRIGGER`/`PROCEDURE` cần SUPER (lỗi 1419) → trigger/thủ tục do root tạo qua `db_apply`, không qua migration.
- Trigger chạy bằng quyền của DEFINER: definer cần `TRIGGER` và `SELECT` trên bảng (thiếu `SELECT` thì lỗi 1143 khi đọc `NEW.cột`). Trong trigger, `USER()` là tài khoản gọi, `CURRENT_USER()` là definer.
- `GRANT` trên tên CSDL có `_` phải viết `test\_bookstore` (`_` là ký tự đại diện).
- `IDENTIFIED BY RANDOM PASSWORD` in mật khẩu ra màn hình/log, không dùng; definer được tạo với mật khẩu ngẫu nhiên sinh trong Python và không lưu.
- MySQLdb truyền tham số an toàn được cả cho tên tài khoản: `cursor.execute("CREATE USER %s@%s IDENTIFIED BY %s", (user, host, pw))`; tên CSDL (định danh) thì kiểm tra regex rồi mới chèn vào câu lệnh.
- `--settings=...` thay cho biến `DJANGO_SETTINGS_MODULE=...` để lệnh chạy giống nhau trên bash và PowerShell.
- `RunSQL` với chuỗi nhiều câu lệnh: Django tách bằng `sqlparse`; tự tách và bỏ câu rỗng (chỉ còn chú thích) để tránh lỗi "Query was empty".
- CSDL tạm của `manage.py test` không có trigger/phân quyền; kiểm tra phân quyền trên CSDL dev.
- `{% url 'app:ten' as bien %}` không báo lỗi khi URL chưa tồn tại (biến rỗng) → navbar dùng cách này cho link `accounts:*` trong lúc app accounts chưa có URL.
- `{% include %}` không mang theo `{% load %}` của trang cha: component nào dùng `{% static %}` hay filter `bookstore` phải tự `{% load %}`.
- Việc cần nhớ ở bước accounts: nếu Django nâng số vòng băm PBKDF2, lần đăng nhập đầu của nhân viên sẽ tự lưu lại mật khẩu bằng `app_customer` và bị trigger chặn → cần xử lý (bắt lỗi hoặc băm lại qua kết nối `staff`).

## 4–5. Checklist bảo mật

Đã tách sang file riêng `SECURITY_CHECKLIST.md` (cùng thư mục với file này): mục 4 là checklist theo 9 chức năng (1–9), mục 5 là checklist ngoài chức năng (A–E). Các số mục ở phần 6 bên dưới trỏ vào file đó.

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
