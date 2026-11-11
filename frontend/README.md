# Frontend – quy tắc làm việc

Giao diện là **template Django** (HTML/CSS/JS), Django điền dữ liệu rồi trả HTML cho trình duyệt. Không có SPA, không gọi API kiểu React.

## Ai sửa file nào

| Đường dẫn | Người phụ trách | Ghi chú |
| --- | --- | --- |
| `templates/base.html`, `templates/layouts/`, `templates/components/`, `templates/errors/` | Nhóm trưởng | Sửa phải qua pull request được nhóm trưởng duyệt (CODEOWNERS) |
| `static/css/base.css`, `static/js/base.js` | Nhóm trưởng | Style và JS dùng chung |
| `templates/shop/`, `templates/account/`, `static/css/shop.css`, `static/css/account.css`, `static/js/shop.js`, `static/js/account.js` | FE 1 | Khu vực khách hàng |
| `templates/dashboard/`, `static/css/dashboard.css`, `static/js/dashboard.js` | FE 2 | Khu vực nhân viên |

## Kế thừa template (3 tầng)

```
base.html                 khung HTML chung
  └── layouts/*.html      customer.html | auth.html | admin.html
        └── trang con     shop/..., account/..., dashboard/...
```

Trang con **chỉ được điền** các block sau:

| Block | Dùng để |
| --- | --- |
| `title` | Tiêu đề tab, ví dụ `{% block title %}Giỏ hàng{% endblock %}` |
| `content` | Nội dung chính của trang |
| `extra_css` | Thêm `<link rel="stylesheet" href="{% static 'css/shop.css' %}">` |
| `extra_js` | Thêm `<script src="{% static 'js/shop.js' %}" defer></script>` |

Block `body` **chỉ** do `layouts/` điền. Chọn layout:

- `layouts/customer.html`: trang của khách (có navbar, footer)
- `layouts/auth.html`: đăng nhập, đăng ký, quên mật khẩu, 2FA (không navbar)
- `layouts/admin.html`: trang của nhân viên (có sidebar)

Mẫu một trang:

```html
{% extends "layouts/customer.html" %}
{% load static %}

{% block title %}Giỏ hàng{% endblock %}

{% block extra_css %}<link rel="stylesheet" href="{% static 'css/shop.css' %}">{% endblock %}

{% block content %}
  <h1>Giỏ hàng</h1>
  <form method="post" action="{% url 'orders:cart_update' %}">
    {% csrf_token %}
    ...
  </form>
{% endblock %}

{% block extra_js %}<script src="{% static 'js/shop.js' %}" defer></script>{% endblock %}
```

## Quy tắc bảo mật (bắt buộc)

Site bật **Content Security Policy**: trình duyệt sẽ **chặn** mọi thứ vi phạm các quy tắc dưới đây, nên vi phạm là giao diện hỏng ngay.

1. **Không JS inline:** không `<script>...</script>` có code bên trong, không `onclick="..."`, `onload="..."`. Viết JS trong file `.js`, gắn sự kiện bằng `addEventListener`.
2. **Không CSS inline:** không `style="..."`, không `<style>...</style>`. Viết trong file `.css`, dùng class.
3. **Chỉ tải tài nguyên từ chính site:** không nhúng CDN, Google Fonts, script bên ngoài. Thư viện cần dùng thì tải về đặt trong `static/`.
4. **Không `|safe`, không `mark_safe`, không `{% autoescape off %}`.** Mọi `{{ biến }}` được Django tự escape để chống XSS.
5. **Trong JS không dùng `innerHTML`, `outerHTML`, `document.write`.** Hiển thị dữ liệu bằng `textContent` để chống DOM XSS.
6. **Mọi `<form method="post">` phải có `{% csrf_token %}`.** AJAX dùng `Bookstore.postForm(url, data)` trong `base.js` (tự gửi CSRF token).
7. **Không dùng link `<a>` cho thao tác thay đổi dữ liệu** (xóa khỏi giỏ, đăng xuất...). Dùng `<form method="post">`.
8. **Mỗi file dùng `{% static %}` phải có `{% load static %}`** ở đầu (kế thừa không mang theo lệnh `load`).
9. **Comment nhiều dòng phải dùng `{% comment %}...{% endcomment %}`.** Cú pháp `{# ... #}` chỉ dùng cho **một dòng**; viết nhiều dòng thì nội dung bị in ra HTML, ai xem mã nguồn trang cũng đọc được.
10. **Ẩn nút trên giao diện không phải là phân quyền.** Kiểm tra quyền luôn làm ở view phía backend.

## Dữ liệu từ backend

Tên biến mỗi trang nhận được ghi trong `docs/contract.md`. Khi backend chưa xong, dựng giao diện với dữ liệu giả theo đúng tên biến trong file đó.
