# PROJECT CONTEXT – Web bán sách đảm bảo an toàn bảo mật

> File ngữ cảnh của dự án: đề bài, kiến trúc, những gì đã có và cách các lớp bảo mật khớp với yêu cầu chấm điểm.
> **Cập nhật 2026-11-21**, đối chiếu `main` `4196e7f` (sau PR #56) + gói một tài khoản một phiên. Bản cũ (2026-11-09 → 13) mô tả kế hoạch ban đầu; nhiều chi tiết trong đó đã thay đổi và được thay bằng nội dung dưới đây.
> Giải thích kỹ thuật từng chức năng: thư mục `docs/`. Nhật ký quyết định chi tiết của nhóm trưởng lưu ngoài repo.

---

## 1. Thông tin chung

- **Môn:** An toàn ứng dụng Web và Cơ sở dữ liệu – Bộ môn ATTT, Khoa CNTT2, PTIT TP.HCM. GV: ThS. Phan Nghĩa Hiệp.
- **Đề tài:** Xây dựng trang web bán sách đảm bảo an toàn bảo mật. **Trọng tâm là bảo mật**, bán sách chỉ là bối cảnh.
- **Đối tượng:** (1) Khách hàng, (2) Quản trị viên kiêm quản lý sách (**chỉ một admin**).
- **Nhóm 5 người** (2 backend, 2 frontend, 1 kiểm thử). Từ 2026-11-15 nhóm trưởng tự làm toàn bộ phần code; Claude viết code kèm giải thích, nhóm trưởng tự commit, mở PR, chờ CI xanh rồi squash-merge.
- **Repo:** https://github.com/TuanThanh05/secure-bookstore (public, nhánh `main`). Commit dùng email `...@users.noreply.github.com`.
- **Dự định trước khi nộp:** làm sạch `main`, tải dự án về, gỡ repo cũ rồi đăng lại repo mới (để bỏ lịch sử git có file sao lưu từng lọt lên ở PR #41).

### Yêu cầu chấm điểm của đề

- **Bảo mật ứng dụng web – 60%:** ≥ 4 biện pháp bảo mật máy chủ/ứng dụng web và chống ≥ 4 dạng tấn công thường gặp (slide chương 2, 3).
- **Bảo mật CSDL – 40%:** chống ≥ 5/10 lỗ hổng CSDL thực tế (slide chương 5, 6).
- Làm càng nhiều biện pháp thì điểm phần đó càng cao.
- Ngôn ngữ cho phép: C, C++, Java, C#, PHP, Python. CSDL cho phép: SQL Server, Oracle, MySQL. **Dự án: chỉ Python + MySQL** (sai ngôn ngữ là 0 điểm).
- **Nộp:** 1 thư mục gồm file Word đồ án (cơ sở lý thuyết + code demo, bảng phân công ở trang cuối), file PowerPoint ngắn gọn, source code (không kèm `.env`, `database/.env.db`, venv, `.git`, `backups/`).
- **Bị 0 điểm nếu:** vắng buổi vấn đáp, nộp thiếu, sai định dạng, sai ngôn ngữ, nộp trễ.

---

## 2. Công nghệ

| Thành phần | Lựa chọn |
| --- | --- |
| Ngôn ngữ, framework | Python 3.14, Django 6.1.3 (CSP có sẵn) |
| CSDL | MySQL 8.4 LTS (Django 6.1 từ chối 8.0 và MariaDB); `mysqlclient` 2.3.0 |
| Thư viện bảo mật | `argon2-cffi` (băm mật khẩu Argon2id), `django-axes` 9.0.0 (khóa đăng nhập), `cryptography` (AES-GCM), `pyotp` + `segno` (TOTP + mã QR), `Pillow` (làm sạch ảnh bìa) |
| Giao diện | Template Django + CSS thuần, font và icon tự host; **không SPA, không CDN, không JS/CSS inline, không `|safe`, không `innerHTML`**. Ngoại lệ duy nhất: Cloudflare Turnstile ở trang đăng ký bước 1 |
| Máy nhóm trưởng | Arch Linux, MySQL chạy bằng `sudo docker compose` (`compose.yaml`) |
| Triển khai mẫu | Nginx (HTTPS) → Gunicorn (1 worker) → Django → MySQL; cấu hình mẫu trong `deploy/` |
| CI (GitHub Actions) | MySQL 8.4 service → `db_setup` → `migrate` → `db_apply` → `db_check_grants` → `check` / `check --deploy` → `makemigrations --check` → test → `bandit -r backend -q` |

---

## 3. Kiến trúc bảo mật

### 3.1 Phân quyền hai lớp

- **Lớp 1 – Django:** mọi view kiểm tra đăng nhập, vai trò (`staff_required`), quyền sở hữu dữ liệu trước khi gọi CSDL; trang nhạy cảm có thêm xác thực lại.
- **Lớp 2 – MySQL:** mỗi vai trò dùng **một tài khoản MySQL riêng**, quyền tối thiểu cấp qua role. Nếu lớp 1 bị bỏ sót hoặc bị SQL injection, MySQL vẫn từ chối câu lệnh vượt quyền.

| Tài khoản MySQL | Role | Dùng cho | Quyền chính |
| --- | --- | --- | --- |
| `app_customer` | `r_customer` | Trang khách, kết nối `default` | `EXECUTE` các thủ tục của khách; chỉ `SELECT` trên `accounts_user`; `INSERT` vào bảng log |
| `app_staff` | `r_staff` | Dashboard admin, kết nối `staff` | `EXECUTE` các thủ tục quản trị |
| `app_session` | `r_session` | Bảng phiên `django_session` | Chỉ bảng phiên (lưu mã băm cookie, chữ ký gắn dòng) |
| `app_auth` | `r_auth` | Mọi lệnh ghi `accounts_user`, bảng 2FA, bảng django-axes | Ghi có trigger bảo vệ từng cột |
| `bookstore_definer@localhost` | – | `DEFINER` của trigger, thủ tục, Event | Khóa đăng nhập, mật khẩu ngẫu nhiên không lưu |
| `bookstore_migrate` | – | `migrate`, `test` (`--settings=bookstore.settings.migrate`) | Tạo/sửa bảng; mật khẩu chỉ trong `database/.env.db` |
| `bookstore_backup@localhost` | – | Lệnh sao lưu | Chỉ đọc (`SELECT, SHOW VIEW, TRIGGER, EVENT`, `SHOW_ROUTINE`), chỉ đăng nhập tại chỗ |

Router Django: `SessionRouter`, `TwoFactorRouter`, `LockoutRouter` (bảng axes → `app_auth`), `AccountWriteRouter` (ghi `User` → `app_auth`), `MigrateOnDefaultRouter`. Lệnh `python manage.py db_check_grants` thử thật **142** trường hợp quyền (được/bị từ chối) trên từng tài khoản; CI chạy lệnh này mỗi PR.

### 3.2 Truy cập dữ liệu gián tiếp

- **Ghi** dữ liệu nghiệp vụ chỉ qua **thủ tục `SQL SECURITY DEFINER`**: tự kiểm tra lại người gọi (`NOT_STAFF`, `NOT_CUSTOMER`), kiểm tra đầu vào, khóa dòng `FOR UPDATE`, `SIGNAL` đúng một mã lỗi, ghi `core_auditlog` trong cùng giao dịch.
- **Đọc** qua **thủ tục đọc** (`READS SQL DATA`): lọc theo `user_id` từ phiên, che dữ liệu nhạy cảm ngay trong thủ tục, trả bản mã cho Django giải mã. View chỉ dùng khi là phép chiếu cột thuần trên một bảng.
- Tài khoản ứng dụng **không có quyền trên bảng nghiệp vụ**; Django gọi thủ tục bằng `callproc` với tham số tách riêng.
- Dữ liệu đã chốt (đơn hàng, giao dịch thanh toán) khóa bằng trigger; trạng thái đơn chỉ đi tới đúng một bước.
- Việc chạy nền dùng MySQL Event: tự hủy đơn quá hạn (mỗi phút, trả kho), xóa log cũ hơn 1 năm.
- Đối tượng CSDL nằm trong `database/`: `01_bang.sql` (bảng, CHECK – migration đọc), `02_trigger_thu_tuc.sql` (trigger, thủ tục, Event – root chạy bằng `db_apply`), `03_phan_quyen.sql` (quyền), `config/my.cnf` (hardening).

### 3.3 Dữ liệu nhạy cảm

- Mật khẩu băm **Argon2id**; tối thiểu 12, tối đa 64 ký tự; không trùng 5 mật khẩu gần nhất (trigger ghi lịch sử).
- SĐT, địa chỉ giao hàng, bí mật TOTP mã hóa **AES-GCM** (`FIELD_ENCRYPTION_KEY`), ngữ cảnh gắn chủ sở hữu.
- Kết nối Django ↔ MySQL bắt buộc TLS; bản sao lưu mã hóa AES-256-GCM bằng khóa riêng.
- Bí mật chia hai file không commit: `.env` (web đọc) và `database/.env.db` (chỉ lệnh quản trị đọc: mật khẩu root, migrate, sao lưu, khóa sao lưu).

---

## 4. Chức năng đã có (`main` `4196e7f`)

**Khách hàng**
- Đăng ký bắt đầu bằng email: chứng minh sở hữu email qua link hạn 5 phút rồi mới tạo tài khoản (chống chiếm tài khoản trước khi đăng ký); Cloudflare Turnstile ở bước 1.
- Đăng nhập **chỉ bằng tên đăng nhập**; quên mật khẩu (thư kèm tên đăng nhập); đổi mật khẩu; xác thực 2 bước TOTP tự bật, 5 mã dự phòng.
- Thông tin tài khoản (SĐT mã hóa, xem đầy đủ cần xác thực lại bằng mật khẩu).
- Xem sách, tìm kiếm, lọc thể loại, phân trang; trang chi tiết sách.
- Đánh giá sách: chỉ khách có đơn **Đã giao** chứa cuốn đó; mỗi sách một đánh giá, gửi lại là sửa; tên hiển thị che bớt.
- Giỏ hàng (tối đa 5 cuốn mỗi sách, 30 đầu sách); đặt hàng (1 đơn chờ thanh toán/khách, tối đa 20 cuốn/đơn, giữ kho 5 phút, chống race condition bằng khóa dòng); hủy đơn; bỏ 3 đơn chưa thanh toán trong 24 giờ thì tài khoản bị khóa 24 giờ.
- Thanh toán mô phỏng (bật bằng cờ `PAYMENT_SIMULATION`); Đơn hàng của tôi (đang xử lý / lịch sử).

**Quản trị viên** (`/dashboard/`, xác thực 2 bước bắt buộc, phiên tối đa 1 giờ)
- Tổng quan: đơn theo bước, doanh thu, kho, bảo mật, trạng thái sao lưu.
- Quản lý kho sách và thể loại; upload ảnh bìa (kiểm tra nội dung thật, lưu lại WebP, tên UUID).
- Quản lý đơn hàng: luồng Đã thanh toán → Đã tiếp nhận → Đã đóng gói → Đang giao → Đã giao; chi tiết đơn cần xác thực lại.
- Quản lý tài khoản khách: danh sách che email/SĐT, khóa/mở khóa nhập mật khẩu admin cho từng lần kèm lý do (khóa là xóa mọi phiên của khách).
- Nhật ký hệ thống: nhật ký bảo mật + nhật ký thao tác (vào trang cần xác thực lại).
- Thông tin tài khoản admin.

**Chỉ chạy bằng lệnh trên máy chủ** (không có trên web)
- `tao_admin` (admin duy nhất, cài 2FA ngay), `doi_mat_khau_admin`, `dat_lai_2fa_admin`.
- `db_setup`, `db_apply`, `db_check_grants`.
- `db_backup`, `db_backup_verify`, `db_restore`, `db_backup_export` (`docs/sao-luu-csdl.md`).

**Một tài khoản chỉ một phiên** (admin và khách): đăng nhập mới đẩy phiên cũ ra, phiên cũ thấy thông báo, chủ tài khoản nhận thư kèm IP (`docs/phien-dang-nhap.md` mục 6).

**Chưa làm:** admin ẩn/hiện đánh giá (tạm bỏ); cổng thanh toán thật VNPay/MoMo (gác, dùng mô phỏng).

---

## 5. Đối chiếu yêu cầu chấm điểm

### 5.1 Dạng tấn công lên ứng dụng web (chương 2)

| Dạng tấn công | Hệ thống chống bằng |
| --- | --- |
| SQL Injection | Chỉ gọi thủ tục với tham số tách riêng; `LIKE` thoát ký tự đại diện; tài khoản ứng dụng không có quyền trên bảng (injection cũng không đọc/ghi được bảng) |
| XSS | Auto-escape, không `|safe`/`innerHTML`, CSP chặt, lọc ký tự điều khiển và ký tự đảo chiều văn bản |
| CSRF | `CsrfViewMiddleware`, mọi thay đổi bằng POST, không `csrf_exempt`, cookie `SameSite=Lax` |
| Tấn công xác thực | Argon2id, axes khóa 5 lần/15 phút, chặn IP sai ≥ 20 lần/60 phút, 2FA, chỉ đăng nhập bằng tên đăng nhập (không dò được email), thông báo lỗi chung, xác thực lại chỉ bằng mật khẩu của chính mình |
| Chiếm tài khoản trước khi đăng ký | Đăng ký bắt đầu bằng email, chưa chứng minh email thì không tạo tài khoản |
| Chiếm phiên / tái sử dụng cookie | Cookie `HttpOnly`, `Secure`, đổi session ID khi đăng nhập, bảng phiên chỉ lưu mã băm + chữ ký, khóa tài khoản xóa mọi phiên, một tài khoản một phiên (phiên cũ bị đẩy ra + thư cảnh báo) |
| IDOR, sửa tham số | Thủ tục luôn kèm `user_id` từ phiên, không nhận giá/tổng tiền từ form, mã đơn ngẫu nhiên, thăm dò mã đơn ghi `idor_attempt` |
| Race condition | Khóa dòng `FOR UPDATE` theo thứ tự cố định, mã chống trùng do server sinh, UNIQUE |
| Lạm dụng nghiệp vụ (giữ kho) | Giữ kho 5 phút, 20 cuốn/đơn, 3 đơn bỏ dở/24 giờ thì khóa 24 giờ |
| Clickjacking | `X-Frame-Options: DENY`, CSP `frame-ancestors` |
| Upload file độc hại | Kiểm tra nội dung ảnh thật, giới hạn kích thước và số điểm ảnh, lưu lại WebP, tên UUID, Nginx chỉ phục vụ `.webp` |
| Open redirect | `next` kiểm tra bằng `url_has_allowed_host_and_scheme` |
| Lộ bí mật qua log | Che mã trong URL (`redact_path`), Nginx không ghi access log đường dẫn chứa mã |

### 5.2 Biện pháp bảo mật máy chủ, ứng dụng web (chương 3)

| Biện pháp | Hệ thống |
| --- | --- |
| Cấu hình máy chủ web | `prod.py` (`DEBUG=False`, HSTS, HTTPS, header), Nginx mẫu, Gunicorn 1 worker, IP thật sau proxy (`TRUSTED_PROXY_IPS`) |
| Xác thực mạnh | Argon2id, chính sách mật khẩu, 2FA TOTP, khóa đăng nhập |
| Phân quyền tối thiểu | Hai lớp Django + MySQL, 4 tài khoản ứng dụng, một admin |
| Bảo mật phiên | Bảng phiên riêng, mã băm cookie, phiên admin 1 giờ, một tài khoản một phiên, xác thực lại 2 phút cho thao tác nhạy cảm |
| SSL/TLS | HTTPS (Nginx), TLS bắt buộc giữa Django và MySQL |
| Kiểm tra đầu vào, xử lý lỗi | Kiểm tra 3 lớp: form → service → thủ tục/CHECK/trigger; trang lỗi riêng |
| Ghi log, giám sát | `core_securityevent` + `logs/security.log`, `core_auditlog` do trigger/thủ tục ghi, trang Nhật ký, cảnh báo trên Tổng quan |
| Sao lưu, khôi phục | Sao lưu toàn bộ mã hóa, off-site, kiểm tra khôi phục, khôi phục có tự sao lưu trước |

### 5.3 10 lỗ hổng CSDL (chương 5)

| # | Lỗ hổng | Hệ thống |
| --- | --- | --- |
| 1 | Mật khẩu yếu/mặc định | `validate_password` MEDIUM ≥ 12 ký tự cho tài khoản MySQL; definer mật khẩu ngẫu nhiên và khóa đăng nhập; root chỉ vào được từ máy chủ |
| 2 | SQL Injection | Thủ tục + tham số tách riêng; tài khoản ứng dụng không có quyền trên bảng |
| 3 | Đặc quyền quá mức | Một tài khoản cho mỗi vai trò, chỉ `EXECUTE`; `db_check_grants` 142 kiểm tra |
| 4 | Bật tính năng thừa | `local_infile = OFF`, `secure_file_priv` giới hạn, `skip-name-resolve` |
| 5 | Quản lý cấu hình lỗi | `my.cnf` hardening, `require_secure_transport = ON`, cổng Docker chỉ mở cho `127.0.0.1` |
| 6 | Tràn bộ đệm | Giới hạn độ dài đầu vào ở form, thủ tục và CHECK; MySQL 8.4 LTS |
| 7 | Leo thang đặc quyền | Trigger chặn tạo/nâng quyền nhân viên và đổi cột nhạy cảm; definer khóa; `bookstore_migrate` không có SUPER |
| 8 | Từ chối dịch vụ | `max_execution_time`, `max_connections`, `MAX_USER_CONNECTIONS` từng tài khoản, giới hạn tần suất, giới hạn số dòng trả về |
| 9 | CSDL không được vá | MySQL 8.4 LTS; Dependabot (cần xác nhận đã bật trên GitHub) |
| 10 | Dữ liệu không mã hóa | AES-GCM cho SĐT/địa chỉ/bí mật TOTP, Argon2id, TLS, sao lưu mã hóa |

Ngoài ra trình bày được cơ chế bảo mật đối tượng CSDL (chương 6.2): tài khoản theo vai trò, quyền `EXECUTE` trên thủ tục, thủ tục `SQL SECURITY DEFINER`, trigger bảo vệ dòng/cột, Event chạy nền.

---

## 6. Cấu trúc repo

```
secure-bookstore/
├── backend/
│   ├── bookstore/settings/   # base, dev, prod, migrate
│   ├── core/                 # client_ip, security_log, session_store, db_routers, middleware, decorators, backup, captcha,
│   │                         # lệnh db_setup/db_apply/db_check_grants/db_backup*/db_restore, migration bảng nghiệp vụ 0001
│   ├── accounts/             # đăng ký, đăng nhập, 2FA, quên/đổi mật khẩu, hồ sơ, lệnh tao_admin/doi_mat_khau_admin/dat_lai_2fa_admin
│   ├── catalog/              # sách, thể loại, đánh giá, ảnh bìa
│   ├── orders/               # giỏ hàng, đặt hàng, hủy đơn, đơn của tôi
│   ├── payments/             # thanh toán mô phỏng
│   └── dashboard/            # trang quản trị
├── frontend/                 # templates/ (base, layouts, components, shop, account, dashboard, errors), static/
├── database/                 # 01_bang.sql, 02_trigger_thu_tuc.sql, 03_phan_quyen.sql, config/my.cnf, .env.db.example
├── deploy/                   # nginx/, gunicorn.conf.py
├── docs/                     # tài liệu từng chức năng, contract.md, PROJECT_CONTEXT.md, SECURITY_CHECKLIST.md, AI_TRACE.md
├── security-tests/           # dành cho kiểm thử
├── compose.yaml  requirements.txt  .env.example  README.md
```

Cài đặt một máy (chi tiết `database/README.md`): `db_setup` → `migrate --settings=bookstore.settings.migrate` → `db_apply --settings=bookstore.settings.migrate` → `db_check_grants` → `runserver`. Tạo admin: `tao_admin`.

---

## 7. Quy tắc chung (tóm tắt)

- Không dùng `raw()`/`cursor.execute` nối chuỗi với dữ liệu người dùng; không `|safe`, `mark_safe`, `csrf_exempt`; không đổi dữ liệu bằng GET; không `fields = '__all__'`.
- Giá, tổng tiền, quyền sở hữu luôn tính và kiểm tra ở server/CSDL.
- Trong code chỉ có chú thích một dòng. Giải thích dài và đánh dấu code do AI viết nằm trong `docs/AI_TRACE.md` (mỗi mục: loại + tên | file | AI viết, rồi giải thích); cách ghi ở `docs/ai-trace.md`.
- Không bao giờ commit `.env`, `database/.env.db`, khóa, mật khẩu, file sao lưu.
- Không đẩy thẳng lên `main`; mỗi thay đổi một nhánh + PR, chờ CI xanh rồi Squash and merge.
- Thao tác quản trị hệ thống nguy hiểm chỉ là lệnh `manage.py` trên máy chủ.

---

## 8. Demo

- Mỗi biện pháp có kịch bản: tấn công trên bản lỗi thành công, trên bản an toàn bị chặn.
- `main` luôn là bản an toàn và là bản nộp. Bản lỗi để ở nhánh riêng `demo-vulnerable`, tạo từ `main` **sau khi `main` hoàn thiện**, mỗi lỗ hổng một commit; không bao giờ merge vào `main`, không có cờ bật lỗi trong code.
- Bằng chứng tái hiện đã có sẵn trong bộ test: mỗi lỗ hổng do nhóm trưởng tự phát hiện hoặc do báo cáo rà soát nêu đều có test tái hiện trên mã cũ (ví dụ chiếm tài khoản trước khi đăng ký, token trong nhật ký, dò email qua trạng thái khóa, khóa tài khoản người khác qua trang xác thực lại).
- Báo cáo rà soát bảo mật bằng AI và phản hồi của nhóm: file `phan-hoi-bao-cao-ra-soat-bao-mat.md` (lưu ngoài repo).
