# secure-bookstore

[![CI](https://github.com/TuanThanh05/secure-bookstore/actions/workflows/ci.yml/badge.svg)](https://github.com/TuanThanh05/secure-bookstore/actions/workflows/ci.yml)

Đồ án môn **An toàn ứng dụng Web và Cơ sở dữ liệu** (PTIT TP.HCM): xây dựng trang web bán sách **đảm bảo an toàn bảo mật**.
Trọng tâm là bảo mật; bán sách chỉ là bối cảnh.

> Đọc [`docs/PROJECT_CONTEXT.md`](docs/PROJECT_CONTEXT.md) trước: quyết định đã chốt, các biện pháp bảo mật, cấu trúc repo. Checklist bảo mật: [`docs/SECURITY_CHECKLIST.md`](docs/SECURITY_CHECKLIST.md). Code do AI viết và giải thích từng hàm: [`docs/AI_TRACE.md`](docs/AI_TRACE.md).

## Công nghệ

| Phần | Lựa chọn |
| --- | --- |
| Ngôn ngữ, framework | Python 3.14, Django 6.1 |
| Giao diện | Template Django (HTML/CSS/JS), không SPA, không JS inline (CSP) |
| CSDL | MySQL 8.4 LTS (Docker Compose), tài khoản MySQL riêng theo vai trò |
| Triển khai | Nginx (HTTPS) → Gunicorn → Django |

## Cấu trúc

```
backend/         Django: bookstore (settings), core, accounts, catalog, orders, payments, dashboard
frontend/        templates/ và static/ (xem frontend/README.md)
database/        lược đồ, tài khoản, trigger/view/thủ tục, cấu hình MySQL
deploy/          Nginx, Gunicorn
security-tests/  script kiểm thử bảo mật và bằng chứng
docs/            tài liệu từng chức năng, PROJECT_CONTEXT, SECURITY_CHECKLIST, AI_TRACE, hợp đồng FE–BE
```

## Chạy thử (máy cá nhân)

```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                   # điền giá trị; KHÔNG commit .env
```

Sau đó dựng MySQL 8.4 (Docker hoặc cài thường) và chạy 4 lệnh theo [`database/README.md`](database/README.md):
`db_setup` → `migrate` → `db_apply` → `runserver`.

## Quy tắc bắt buộc

- Không commit `.env`, mật khẩu, khóa bí mật.
- Không `raw()`/`cursor.execute` nối chuỗi; không `|safe`/`mark_safe` với dữ liệu người dùng; không `@csrf_exempt`; không đổi dữ liệu bằng GET.
- Làm trên nhánh tính năng, mở Pull Request vào `main`; không push thẳng lên `main`; chờ CI xanh rồi Squash and merge.
- Sau `git pull`: có migration mới thì `migrate --settings=bookstore.settings.migrate`; `database/02_trigger_thu_tuc.sql` hoặc `03_phan_quyen.sql` đổi thì `db_apply`; `requirements.txt` đổi thì `pip install -r requirements.txt`.
- Trong code chỉ dùng chú thích một dòng; giải thích dài và đánh dấu code do AI viết ghi vào [`docs/AI_TRACE.md`](docs/AI_TRACE.md) (cách ghi: [`docs/ai-trace.md`](docs/ai-trace.md)).
