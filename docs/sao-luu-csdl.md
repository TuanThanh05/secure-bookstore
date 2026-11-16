# Sao lưu và khôi phục CSDL

Chốt 2026-11-16, theo **Chương 7 "Sao lưu, khôi phục dự phòng"** của bài giảng. Mọi thao tác **chỉ chạy bằng lệnh `manage.py` trên máy chủ**, không có nút trên web (web có nút thì ứng dụng web phải có quyền gần như root, và ai chiếm được tài khoản admin sẽ tải được nguyên CSDL). Trang Tổng quan chỉ hiện trạng thái.

## 1. Bài giảng yêu cầu → hệ thống làm

| Bài giảng (mục 7.1) | Hệ thống |
| --- | --- |
| Sao lưu toàn bộ (full backup) | `mysqldump --single-transaction --routines --triggers --events`: bảng + dữ liệu + thủ tục + trigger + Event. `--single-transaction` chụp một thời điểm nhất quán mà **không khóa bảng**, khách vẫn đặt hàng bình thường trong lúc sao lưu. Sao lưu log giao dịch (binlog, khôi phục theo thời điểm) **không làm** (hướng mở rộng, mục 7). |
| Sao lưu file | Ảnh bìa `media/covers/` đi kèm trong cùng gói (chỉ file tên UUID `.webp`), vì CSDL khôi phục xong vẫn trỏ tới ảnh. |
| Bảo vệ file sao lưu: mật khẩu, **mã hóa** | Mỗi bản sao lưu đều **nén (gzip) rồi mã hóa AES-256-GCM** bằng khóa riêng `BACKUP_ENCRYPTION_KEY` (khác khóa mã hóa SĐT `FIELD_ENCRYPTION_KEY`). GCM có thẻ xác thực: sai khóa, sửa 1 byte hay file bị cắt đều bị phát hiện. Kèm file `.sha256` để kiểm tra nhanh. File quyền 600, thư mục 700, nằm ngoài thư mục web, không commit (`.gitignore`). |
| "Dọn dẹp" bản cũ | Mỗi lần sao lưu tự xóa bản **cũ hơn 1 năm** (`BACKUP_RETENTION_DAYS = 365`), tính theo thời điểm ghi trong tên file (không theo ngày sửa file – dễ bị đổi). File lạ trong thư mục không bao giờ bị xóa. |
| On-site + **off-site** | Bản chính ở `BACKUP_DIR`; nếu đặt `BACKUP_OFFSITE_DIR` (ổ khác, USB, thư mục đồng bộ cloud) thì chép thêm một bản và so SHA-256. File đã mã hóa nên mang đi đâu cũng không lộ dữ liệu. |
| Khôi phục là việc khó, cần quy trình | `db_restore` (khôi phục thật, có xác nhận + tự sao lưu trước) và `db_backup_verify` (thử khôi phục vào CSDL tạm rồi đối chiếu). |
| Tần suất phù hợp | Chốt: **chạy tay khi demo** (không đặt lịch tự chạy). |

Thêm cho môn bảo mật:
- **Tài khoản MySQL riêng `bookstore_backup`, chỉ đọc:** `SELECT, SHOW VIEW, TRIGGER, EVENT` trên CSDL + `SHOW_ROUTINE`. Không INSERT/UPDATE/DELETE/DROP, không FILE, không LOCK TABLES, không PROCESS. Chỉ `@localhost` → chỉ đăng nhập được ngay trên máy/container MySQL (Docker: kết nối từ máy bạn hiện là `172.28.0.1` nên bị từ chối). Lộ mật khẩu tài khoản này cũng không phá được dữ liệu. Lệnh `db_backup_verify` kiểm tra lại điều này mỗi lần chạy.
- **Bí mật không nằm chỗ web đọc:** `DB_BACKUP_PASSWORD` và `BACKUP_ENCRYPTION_KEY` để trong `database/.env.db` (web không đọc file này), không trong `.env`.
- **Mật khẩu không lộ trên dòng lệnh:** mật khẩu đưa vào `mysqldump`/`mysql` qua stdin, không nằm trong tham số (lệnh `ps` không thấy).
- **Chống "tar slip":** khi mở gói, thành phần lạ (`../`, đường dẫn tuyệt đối, tên ảnh không phải UUID, link) bị từ chối; dữ liệu giải mã chỉ được dùng sau khi thẻ GCM khớp.
- **Nhật ký:** `backup_created`, `backup_failed` (nghiêm trọng), `backup_exported` (cảnh báo), `restore_performed` (cảnh báo), `restore_verified` – ghi `ip_address = cli`, detail chỉ có tên file, dung lượng, kết quả.

## 2. Cài đặt (một lần)

1. `database/.env.db` thêm 2 dòng (xem `database/.env.db.example`):
   ```
   DB_BACKUP_PASSWORD=<sinh: python -c "import secrets; print(secrets.token_urlsafe(24) + '-Aa9')">
   BACKUP_ENCRYPTION_KEY=<sinh: python -c "import base64, secrets; print(base64.b64encode(secrets.token_bytes(32)).decode())">
   ```
   **Mất `BACKUP_ENCRYPTION_KEY` = mất mọi bản sao lưu.** Cất thêm một bản khóa ở nơi khác chỗ để file sao lưu.
2. `.env` (máy Arch, MySQL trong Docker): `BACKUP_DUMP_PREFIX=sudo docker compose exec -T db` (lệnh sẽ hỏi mật khẩu sudo). Tùy chọn `BACKUP_OFFSITE_DIR=/đường/dẫn/khác`.
3. `python manage.py db_setup` (tạo `bookstore_backup`), `migrate`, `db_apply` (cấp quyền chỉ đọc).

## 3. Các lệnh

| Lệnh | Làm gì |
| --- | --- |
| `python manage.py db_backup` | Tạo `backups/bookstore-<UTC>.tar.gz.enc` + `.sha256` (gói gồm `manifest.json`, `bookstore.sql`, `media/covers/*`), chép off-site, xóa bản > 1 năm, ghi log. |
| `python manage.py db_backup_verify [file] --settings=bookstore.settings.migrate` | Giải mã bản mới nhất (hoặc file chỉ định), khôi phục vào CSDL tạm `<tên>_restore_check`, tắt Event của bản tạm, so số dòng từng bảng + số thủ tục/trigger/Event với manifest (đếm lúc sao lưu), kiểm tra `bookstore_backup` chỉ đọc, rồi xóa CSDL tạm. Cần mật khẩu root. |
| `python manage.py db_backup_export <file>` | **Demo:** giải mã một bản ra `backups/plain/<tên>.sql` – file `.sql` trần chạy được như `seed_data.sql`. In cảnh báo, bắt gõ `XUAT-SQL`, quyền 600, ghi log mức cảnh báo. **Xóa file trần ngay sau demo.** |
| `python manage.py db_restore <file> --settings=bookstore.settings.migrate` | Khôi phục **đè** lên CSDL từ `.tar.gz.enc` hoặc `.sql` trần: bắt gõ lại tên CSDL, **tự sao lưu bản hiện tại trước**, chạy SQL bằng root, chép lại ảnh bìa, chạy `db_apply` để cấp lại quyền (xóa/tạo lại thủ tục làm mất quyền EXECUTE), ghi log. Sau đó chạy `db_check_grants`. |

Ghi chú khôi phục:
- File `.sql` chỉ chứa **CSDL**, không chứa tài khoản MySQL và quyền. Máy mới tinh: `db_setup` → `migrate` → `db_restore` (lệnh tự chạy `db_apply`).
- Khôi phục thay cả bảng `core_securityevent`, `django_session`: nhật ký sau thời điểm sao lưu mất (trừ dòng `restore_performed` ghi sau cùng), mọi người bị đăng xuất.
- Đếm số dòng trong manifest lấy ngay trước `mysqldump` (khác giao dịch): nếu có người đặt hàng đúng lúc sao lưu, `db_backup_verify` có thể báo lệch 1–2 dòng ở bảng đơn – chạy sao lưu lúc vắng.

## 4. Trang Tổng quan

Ô **Sao lưu CSDL**: lần sao lưu thành công gần nhất (thời điểm, dung lượng), lần lỗi gần nhất, kết quả kiểm tra khôi phục gần nhất. Tô đỏ khi lần gần nhất bị lỗi, khi chưa có bản sao lưu trong 7 ngày, hoặc kiểm tra khôi phục không đạt. Không có nút nào. Đọc bằng thủ tục `sp_staff_dashboard_backup` (chỉ `r_staff`) từ nhật ký bảo mật.

## 5. Kịch bản demo (5 phút)

1. `db_backup` → chỉ cho thầy file `.tar.gz.enc` mở bằng trình soạn thảo chỉ là byte rác (đã mã hóa); `ls -l` thấy quyền `-rw-------`.
2. `db_backup_verify` → bảng đối chiếu "Lúc sao lưu / Khôi phục" khớp từng bảng, "bookstore_backup: chỉ đọc".
3. `db_backup_export <file>` → mở `backups/plain/*.sql`: là SQL thuần (CREATE TABLE, INSERT, CREATE PROCEDURE...), chạy được.
4. Thêm một thể loại trên dashboard → `db_restore <file>` → thể loại vừa thêm biến mất (về đúng lúc sao lưu), web vẫn chạy, `db_check_grants` đúng hết.
5. Sửa 1 byte trong file `.enc` rồi `db_backup_export` → "Giải mã thất bại: sai khóa hoặc file đã bị sửa".
6. Đăng nhập MySQL bằng `bookstore_backup` thử `DELETE` → lỗi 1142 (không có quyền ghi).
7. Trang Tổng quan → ô Sao lưu CSDL; Nhật ký hệ thống → các dòng "Sao lưu CSDL", "Kiểm tra khôi phục", "Khôi phục CSDL".

## 6. Đã kiểm tra

- Chạy thật trong sandbox (MySQL 8.0, `mysqldump` tại chỗ): sao lưu 24 bảng + ảnh bìa (file lạ `evil.php` trong `media/covers/` bị bỏ qua); chép off-site; bản giả cũ hơn 1 năm ở cả 2 thư mục bị xóa; `db_backup_verify` khớp toàn bộ 24 bảng, 44 thủ tục, 13 trigger, 2 Event, tài khoản sao lưu chỉ đọc, CSDL tạm bị xóa sau đó; xuất `.sql` trần (gõ sai xác nhận → hủy); thêm một thể loại rồi `db_restore` từ file mã hóa → thể loại biến mất, ảnh bìa trở lại, `db_check_grants` đúng hết; khôi phục từ file `.sql` trần cũng đạt; sửa 1 byte / sai khóa → từ chối; `bookstore_backup` chạy `DELETE` → 1142.
- Test `core/tests/test_backup.py`: mã hóa/giải mã, sai khóa, sửa/cắt file, khóa sai độ dài, thành phần lạ trong gói, SQL không khớp manifest, `.sha256` sai, giữ 1 năm theo tên file, mật khẩu chỉ qua stdin (không có trong tham số, không dùng shell), lỗi `mysqldump`, lệnh xuất/khôi phục hủy khi gõ sai xác nhận, sao lưu lỗi ghi `backup_failed`. Test `dashboard/tests/test_overview.py`: ô trạng thái sao lưu (đạt, chưa có, lỗi).

## 7. Hướng mở rộng (không làm)

Bật binlog + sao lưu binlog định kỳ để khôi phục tới một thời điểm bất kỳ (point-in-time recovery, mục 7.1.2.4 "sao lưu log giao dịch"); đặt lịch tự chạy (systemd timer/cron); đẩy bản off-site lên cloud qua kênh mã hóa.
