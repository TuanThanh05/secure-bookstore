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

## Đặt đơn: `sp_place_order` và `orders.services.place_order`

Chốt 2026-11-14. Đổi chữ ký thủ tục hoặc hàm thì sửa mục này trong cùng PR.

**Thủ tục MySQL** (`database/objects/30_sp_place_order.sql`), `r_customer` chỉ có `EXECUTE`:

| Tham số | Kiểu | Ghi chú |
| --- | --- | --- |
| `p_user_id` | IN BIGINT | Luôn là `request.user.pk`, không bao giờ lấy từ form |
| `p_idempotency_key` | IN CHAR(32) | 32 ký tự hex thường, sinh bằng `new_idempotency_key()` khi mở trang đặt hàng |
| `p_shipping_name` | IN VARCHAR(255) | Tên người nhận, 1–100 ký tự sau khi bỏ khoảng trắng hai đầu |
| `p_phone_encrypted` | IN VARCHAR(512) | SĐT đã mã hóa AES-GCM ở Django (đợt 2) |
| `p_address_encrypted` | IN VARCHAR(1024) | Địa chỉ đã mã hóa AES-GCM ở Django (đợt 2) |
| `p_order_code` | OUT CHAR(32) | Mã đơn, dùng trên URL thay cho id |
| `p_created` | OUT TINYINT | `1` = đơn mới, `0` = gửi lại cùng mã yêu cầu, trả mã đơn cũ |

Danh sách sách, số lượng, giá đều do thủ tục đọc từ giỏ và `catalog_book`. Phí ship cố định 30.000 đ; hạn thanh toán 15 phút.

**Hàm Django** (`backend/orders/services.py`):

```python
place_order(user, idempotency_key, shipping_name, phone_encrypted, address_encrypted) -> PlaceOrderResult(order_code, created)
```

- Không gọi bên trong `transaction.atomic` (hàm sẽ raise `RuntimeError`): thủ tục tự quản giao dịch.
- Lỗi nghiệp vụ raise `OrderError` có `.code` và `.message`. Frontend chỉ hiển thị `.message`:

| `code` | `message` | Frontend làm gì |
| --- | --- | --- |
| `OUT_OF_STOCK` | Một số sách vừa hết hàng, vui lòng kiểm tra lại giỏ. | Quay lại giỏ |
| `BOOK_INACTIVE` | Một số sách đã ngừng bán. | Quay lại giỏ |
| `CART_EMPTY` | Giỏ hàng đang trống. | Quay lại giỏ |
| `INVALID_INPUT` | Thông tin giao hàng không hợp lệ. | Ở lại form đặt hàng |

- `created = True`: chuyển sang trang đơn, báo "Đặt hàng thành công". `created = False`: chuyển tới đơn cũ, không báo lỗi.
- Mọi lỗi khác (mất kết nối, lỗi quyền 1142...) được ném nguyên ra ngoài để ghi log, không đổi thành `OrderError`.
