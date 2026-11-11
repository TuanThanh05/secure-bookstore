## Làm gì

<!-- 1–3 câu: PR này thêm/sửa gì. -->

Closes #<!-- số issue -->

## Yêu cầu bảo mật đã làm

<!-- Liệt kê các mục checklist trong PROJECT_CONTEXT.md mà PR này hoàn thành, ví dụ:
- [x] (1) Chống mass assignment: form chỉ có trường cho phép
- [x] (2) Thông báo lỗi đăng nhập chung cho mọi trường hợp -->

## Cách kiểm thử

<!-- Các bước để người duyệt / bạn kiểm thử tự làm lại: lệnh, URL, dữ liệu, payload tấn công thử.
Ví dụ: Burp gửi thêm is_staff=1 khi đăng ký → tài khoản vẫn là khách thường. -->

## Tự kiểm tra trước khi mở PR

- [ ] Không có `.env`, `database/.env.db`, mật khẩu, khóa bí mật trong diff
- [ ] Không `raw()` / `cursor.execute` nối chuỗi; SQL đều truyền tham số
- [ ] Không `|safe`, `mark_safe`, `innerHTML`; không JS/CSS inline (CSP)
- [ ] Mọi `<form method="post">` có `{% csrf_token %}`; GET không đổi dữ liệu
- [ ] View có kiểm tra quyền (`@login_required`, `@permission_required`, lọc theo `request.user`)
- [ ] `python manage.py check` sạch
- [ ] Có migration mới / file mới trong `database/objects` hoặc `database/grants`: đã ghi rõ ở trên để mọi người chạy `migrate` / `db_apply`
