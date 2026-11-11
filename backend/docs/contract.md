# Hợp đồng frontend – backend

Mỗi trang một dòng. Frontend dựng template theo cột "Biến trong template" (dùng dữ liệu giả trước), backend viết view trả đúng các biến đó và xử lý đúng các trường gửi lên. Đổi hợp đồng thì sửa file này trong cùng PR.

Quy ước:
- URL name dạng `app:ten` (dùng `{% url 'app:ten' %}`, không gõ cứng đường dẫn).
- Mọi form `POST` có `{% csrf_token %}`. GET không đổi dữ liệu.
- Biến chỉ in bằng `{{ ... }}` (tự escape), không `|safe`.
- "Quyền": ai được vào trang (khách vãng lai / khách đã đăng nhập / nhân viên + quyền gì).

| URL name | Đường dẫn | Template | Quyền | Biến trong template | Trường gửi lên (POST) |
| --- | --- | --- | --- | --- | --- |
| `catalog:home` | `/` | `shop/home.html` | Mọi người | (trang tạm, chưa có) | – |
| `accounts:register` | `/account/register/` | `account/register.html` | Chưa đăng nhập | `form` | `username`, `email`, `password1`, `password2` |
| `accounts:login` | `/account/login/` | `account/login.html` | Chưa đăng nhập | `form`, `next` | `username`, `password`, `next` |
| `accounts:logout` | `/account/logout/` | – (redirect) | Đã đăng nhập | – | (chỉ POST + CSRF) |

Hai dòng `accounts:*` là ví dụ để bạn làm phần account sửa lại cho đúng khi bắt đầu.
