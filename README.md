# secure-bookstore

Đồ án môn **An toàn ứng dụng Web và Cơ sở dữ liệu** (PTIT TP.HCM): xây dựng trang web bán sách **đảm bảo an toàn bảo mật**.
Trọng tâm là bảo mật; bán sách chỉ là bối cảnh.

> Trạng thái: **đang dựng bộ khung trên `main`** (bước 4/6). Chưa nhận PR tính năng.
> Đọc [`PROJECT_CONTEXT.md`](PROJECT_CONTEXT.md) trước khi làm bất cứ việc gì: quyết định đã chốt, checklist bảo mật, phân công.

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
docs/            báo cáo, slide, hợp đồng FE–BE
```

## Chạy thử (máy cá nhân)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # điền giá trị; KHÔNG commit .env
cd backend && python manage.py runserver
```

Phần MySQL (bước 5) sẽ được bổ sung hướng dẫn khi xong.

## Quy tắc bắt buộc

- Không commit `.env`, mật khẩu, khóa bí mật.
- Không `raw()`/`cursor.execute` nối chuỗi; không `|safe`/`mark_safe` với dữ liệu người dùng; không `@csrf_exempt`; không đổi dữ liệu bằng GET.
- Làm trên nhánh tính năng, mở Pull Request vào `main`; không push thẳng lên `main`.
