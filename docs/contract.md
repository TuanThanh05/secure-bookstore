# Hợp đồng frontend – backend

Mỗi trang một dòng. Frontend dựng template theo cột "Biến trong template" (dùng dữ liệu giả trước), backend viết view trả đúng các biến đó và xử lý đúng các trường gửi lên. Đổi hợp đồng thì sửa file này trong cùng PR.

Quy ước:
- URL name dạng `app:ten` (dùng `{% url 'app:ten' %}`, không gõ cứng đường dẫn).
- Mọi form `POST` có `{% csrf_token %}`. GET không đổi dữ liệu.
- Biến chỉ in bằng `{{ ... }}` (tự escape), không `|safe`.
- "Quyền": ai được vào trang (khách vãng lai / khách đã đăng nhập / nhân viên + quyền gì).

| URL name | Đường dẫn | Template | Quyền | Biến trong template | Trường gửi lên (POST) |
| --- | --- | --- | --- | --- | --- |
| `catalog:home` | `/` | `shop/home.html` | Mọi người | `categories` (list: `id`, `name`), `books` (list sách, mỗi cuốn có các trường ở mục *BookCard* bên dưới), `current_category` (int hoặc `None`), `q` (chuỗi đã làm sạch), `cart_add_url` (`None` cho tới khi app orders có URL thêm vào giỏ) | – (chỉ GET: `?q=` tối đa 100 ký tự, `?category=` số nguyên dương) |
| `catalog:about` | `/gioi-thieu/` | `shop/about.html` | Mọi người | – | – |
| `accounts:register` | `/account/register/` | `account/register.html` | Chưa đăng nhập | `form` | `username`, `email`, `password1`, `password2` |
| `accounts:login` | `/account/login/` | `account/login.html` | Chưa đăng nhập | `form`, `next` | `username`, `password`, `next` |
| `accounts:logout` | `/account/logout/` | – (redirect) | Đã đăng nhập | – | (chỉ POST + CSRF) |

Các dòng `accounts:*` là ví dụ để bạn làm phần account sửa lại cho đúng khi bắt đầu.

## BookCard: một cuốn sách hiển thị trên lưới

Component `components/book_card.html` nhận biến `book` có đúng các thuộc tính sau. Tên trùng với cột của view `v_public_books` sẽ tạo sau, nên khi bỏ dữ liệu giả trong `catalog/services.py` thì template không phải sửa.

| Thuộc tính | Kiểu | Ghi chú |
| --- | --- | --- |
| `id` | int | Khóa sách; cũng dùng chọn màu bìa tạm |
| `title` | str | Tên sách |
| `author` | str | Tác giả |
| `category_id` | int | Thể loại |
| `price` | int | Giá (đồng), hiển thị bằng filter `vnd` |
| `rating` | float hoặc `None` | Điểm trung bình 0–5; `None` = chưa có đánh giá |
| `review_count` | int | Số lượt đánh giá |
| `in_stock` | bool | `False` thì hiện "Hết hàng" và khóa nút giỏ |
| `cover_url` | str | Đường dẫn ảnh bìa; rỗng thì hiện bìa tạm có màu |

Khi thêm vào giỏ, form chỉ gửi `book_id` và `quantity`. **Không gửi giá**: giá luôn lấy lại từ CSDL ở phía server.
