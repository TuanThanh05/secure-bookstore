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

## Giao diện: màu, chữ, component

**Màu và khoảng cách** khai báo một lần bằng biến CSS ở đầu `static/css/base.css` (`--color-primary`, `--space-md`, `--radius-lg`…). Viết CSS mới thì dùng biến, không gõ mã màu trực tiếp.

| Biến | Giá trị | Dùng cho |
| --- | --- | --- |
| `--color-bg` | `#fbf9f6` | Nền trang (màu giấy) |
| `--color-text` | `#1b1c1a` | Chữ chính |
| `--color-primary` | `#8b1e2f` | Đỏ đô: nút, giá, link nhấn |
| `--color-gold` | `#c29800` | Sao đánh giá |
| `--color-border` | `#e8e3dc` | Viền thẻ, đường kẻ |

**Font** tự host trong `static/fonts/` (không dùng Google Fonts vì CSP chặn): *Playfair Display* cho tiêu đề, *Plus Jakarta Sans* cho chữ thường. Cả hai có bộ ký tự tiếng Việt, giấy phép OFL (file `OFL-*.txt` đi kèm).

**Icon** là sprite SVG `static/img/icons.svg` (Material Symbols, Apache 2.0). Không chèn `<svg>` tay, dùng component:

```html
{% include "components/icon.html" with name="search" %}
{% include "components/icon.html" with name="star" size="sm" %}
```

Icon có sẵn: `search`, `shopping-bag`, `star`, `star-half`, `star-empty`, `arrow-forward`, `logo`, `person`, `login`, `logout`, `close`, `info`, `chevron-left`, `chevron-right`, `book`. Cần icon mới thì báo nhóm trưởng thêm vào sprite.

**Component** nằm trong `templates/components/`, gọi bằng `{% include ... with ... %}`, dữ liệu truyền vào qua tham số:

| Component | Tham số | Ví dụ |
| --- | --- | --- |
| `book_card.html` | `book`, `cart_add_url` | `{% include "components/book_card.html" with book=book cart_add_url=cart_add_url %}` |
| `search_bar.html` | `action`, `q`, `category` | `{% include "components/search_bar.html" with action=home_url q=q category=current_category %}` |
| `category_filter.html` | `categories`, `current`, `q` | `{% include "components/category_filter.html" with categories=categories current=current_category q=q %}` |
| `icon.html` | `name`, `size` (`sm`/`lg`, không bắt buộc) | như trên |
| `navbar.html`, `footer.html`, `messages.html` | – | layout tự gọi, trang con không gọi |

**Filter** riêng của dự án nằm trong `backend/core/templatetags/bookstore.py`, cần `{% load bookstore %}`:

- `{{ book.price|vnd }}` → `420.000 ₫`
- `{% for s in book.rating|stars %}` → 5 phần tử `star` / `star-half` / `star-empty`
- `{{ book.id|tone }}` → số 0–3 để chọn màu bìa tạm

## Dữ liệu từ backend

Tên biến mỗi trang nhận được ghi trong `docs/contract.md`. Khi backend chưa xong, dựng giao diện với dữ liệu giả theo đúng tên biến trong file đó.
