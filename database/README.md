# database/ – MySQL 8.4 cho secure-bookstore

## Có gì trong thư mục này

| File | Nội dung | Ai chạy |
| --- | --- | --- |
| `schema/01_tables.sql` | Các bảng nghiệp vụ (sách, đơn, thanh toán, log) | `migrate` tự đọc (migration `core/0001_business_schema`) |
| `objects/NN_*.sql` | Trigger, view, thủ tục (`DEFINER = bookstore_definer`) | `db_apply` (root) |
| `grants/NN_*.sql` | Quyền của role `r_customer`, `r_staff` và của definer | `db_apply` (root), sau `objects/` |
| `config/my.cnf` | Cấu hình bảo mật MySQL cho container Docker | Docker đọc mỗi lần bật |
| `.env.db.example` | Mẫu mật khẩu root và `bookstore_migrate` | Sao chép thành `.env.db` (không commit) |

Bảng `accounts_user` và các bảng của Django (phiên, quyền...) do `migrate` tạo từ `models.py`.

## Dựng lần đầu

Cần: Python `.venv` đã cài `requirements.txt`, file `.env` ở gốc repo đã điền `DB_CUSTOMER_PASSWORD`, `DB_STAFF_PASSWORD`.

### Bước A – Có một MySQL 8.4 đang chạy (chọn 1 trong 2)

**Cách 1 – Docker (Linux, hoặc ai đã có Docker)**

```bash
cp database/.env.db.example database/.env.db && chmod 600 database/.env.db   # điền 2 mật khẩu
sudo systemctl start docker          # nếu dịch vụ Docker đang tắt
docker compose up -d
docker compose ps                    # đợi STATUS ghi (healthy), lần đầu khoảng 30 giây
```

**Cách 2 – Cài MySQL thường (Windows)**

1. Tải MySQL Installer bản **8.4 LTS** từ trang MySQL. Không dùng XAMPP: XAMPP chứa MariaDB, không phải MySQL.
2. Chọn cài **MySQL Server 8.4**, cổng `3306`, kiểu xác thực mặc định (mạnh), đặt mật khẩu root mạnh.
3. `copy database\.env.db.example database\.env.db`, rồi điền `MYSQL_ROOT_PASSWORD` = mật khẩu root vừa đặt, và tự chọn `DB_MIGRATE_PASSWORD`.

### Bước B – Tạo tài khoản, bảng, quyền (giống nhau trên mọi máy)

```bash
cd backend
python manage.py db_setup                                         # CSDL, role, 4 tài khoản
python manage.py migrate --settings=bookstore.settings.migrate    # tạo bảng
python manage.py db_apply                                         # trigger + cấp quyền
python manage.py createsuperuser --settings=bookstore.settings.migrate
python manage.py runserver                                        # web chạy bằng app_customer
```

## Dùng hằng ngày (Docker)

```bash
sudo systemctl start docker && docker compose up -d     # bắt đầu làm
docker compose down                                     # xong việc: tắt MySQL, dữ liệu vẫn còn
sudo systemctl stop docker.socket docker                # tắt luôn dịch vụ Docker (nếu muốn)
```

`docker compose down -v` mới xóa dữ liệu. Sau lệnh đó phải làm lại Bước B.

## Khi nào chạy lại lệnh nào

| Bạn vừa... | Chạy |
| --- | --- |
| Đổi mật khẩu trong `.env` hoặc `database/.env.db` (`DB_MIGRATE_PASSWORD`) | `db_setup` |
| `git pull` có migration mới | `migrate --settings=bookstore.settings.migrate` |
| Thêm/sửa file trong `objects/` hoặc `grants/` | `db_apply` |
| Muốn làm lại sạch từ đầu (Docker) | `docker compose down -v`, `up -d`, rồi cả Bước B |

Các lệnh đều chạy lại nhiều lần được, không hỏng dữ liệu.

## Quy ước khi viết thêm

- Trigger/view/thủ tục: file mới trong `objects/`, tên bắt đầu bằng số theo thứ tự phụ thuộc (`1x_` trigger, `2x_` view, `3x_` thủ tục). Mỗi file tự `DROP ... IF EXISTS` trước khi tạo; được dùng `DELIMITER`. Luôn ghi `DEFINER = 'bookstore_definer'@'localhost'`.
- Đối tượng mới cần quyền: thêm `GRANT ... TO 'r_customer'` (hoặc `r_staff`) vào `grants/`, rồi chạy `db_apply`.
- Không sửa `schema/01_tables.sql` sau khi cả nhóm đã migrate. Đổi lược đồ: thêm `schema/02_...sql` và một migration mới đọc file đó.
- `manage.py test` tạo CSDL tạm `test_bookstore` **không có** trigger và phân quyền. Kiểm tra phân quyền thì thử trên CSDL thật.

## Lỗi hay gặp

| Lỗi | Nguyên nhân, cách sửa |
| --- | --- |
| `Lỗi kết nối MySQL (2003 ...)` | MySQL chưa bật. Docker: `docker compose ps`; Windows: mở Services, bật MySQL84 |
| `(1045, "Access denied for user 'root'...")` | Sai `MYSQL_ROOT_PASSWORD` trong `database/.env.db` |
| `Access denied for user 'app_customer'@'...'` khi `runserver` | Chưa chạy `db_setup`, hoặc vừa đổi mật khẩu trong `.env` mà chưa chạy lại `db_setup` |
| `Mật khẩu ... quá yếu` | Mật khẩu cần ≥ 12 ký tự, có chữ hoa, chữ thường, số, ký tự đặc biệt |
| `command denied` khi đăng nhập web | Chưa chạy `db_apply` sau `migrate` |
| `MySQL ... quá cũ` | Cần MySQL 8.4 (Django 6.1 từ chối 8.0 và MariaDB) |
| `pip install mysqlclient` lỗi trên Arch | `sudo pacman -S --needed mariadb-libs pkgconf base-devel`, rồi cài lại |
