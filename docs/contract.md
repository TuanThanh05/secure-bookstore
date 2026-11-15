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
| `accounts:check_email` | `/account/kiem-tra-email/` | `account/check_email.html` | Mọi người | `verify_minutes` | – |
| `accounts:verify_email` | `/account/xac-nhan-email/<token>/` | `account/verify_email.html` | Mọi người (có link trong thư) | `username` (link hợp lệ) hoặc `error`, `expired` (link hỏng, trả 400) | Chỉ POST + CSRF mới xác nhận; GET chỉ hiện nút |
| `accounts:resend_verification` | `/account/gui-lai-xac-nhan/` | `account/resend_verification.html` | Mọi người | `form` | `email` (luôn chuyển tới `check_email`, dù email có tồn tại hay không) |

Đăng ký thành công hay email đã có tài khoản đều chuyển tới `accounts:check_email` (không lộ email nào đã đăng ký). Khách chưa xác nhận email đăng nhập đúng mật khẩu thì nhận lỗi `email_unverified`; nhân viên được miễn.

## BookCard: một cuốn sách hiển thị trên lưới

Component `components/book_card.html` nhận biến `book` có đúng các thuộc tính sau. Dữ liệu lấy từ thủ tục `sp_public_book_list` qua `catalog.services.list_public_books()`.

| Thuộc tính | Kiểu | Ghi chú |
| --- | --- | --- |
| `id` | int | Khóa sách |
| `title` | str | Tên sách |
| `author` | str | Tác giả |
| `category_id` | int | Thể loại |
| `price` | int | Giá (đồng), hiển thị bằng filter `vnd` |
| `rating` | float hoặc `None` | Điểm trung bình 0–5 (chỉ đánh giá đang hiện); `None` = chưa có đánh giá |
| `review_count` | int | Số lượt đánh giá đang hiện |
| `in_stock` | bool | `False` thì hiện "Hết hàng" và khóa nút giỏ |
| `cover_url` | str | **Luôn có giá trị**: ảnh đã upload, hoặc ảnh mặc định `img/book-cover-default.webp` khi sách chưa có ảnh |
| `isbn`, `description`, `created_at` | str / str hoặc `None` / datetime | Có sẵn cho trang chi tiết sách sau này |

Khi thêm vào giỏ, form chỉ gửi `book_id` và `quantity`. **Không gửi giá**: giá luôn lấy lại từ CSDL ở phía server.

## Danh mục sách cho khách: `sp_public_book_list` và `sp_public_category_list`

Chốt 2026-11-15, thay cho `v_public_books` / `v_public_categories` trong issue #9: MySQL từ chối view `SQL SECURITY DEFINER` có WHERE/JOIN/GROUP BY khi phiên người gọi bật role, mà điều kiện "chỉ sách đang hiện" cần WHERE. File: `database/objects/20_public_catalog.sql`.

- **Ai xem được:** mọi người, kể cả chưa đăng nhập (Django luôn dùng kết nối `app_customer`). `r_customer` chỉ có `EXECUTE` hai thủ tục, **không có quyền nào** trên `catalog_book`, `catalog_category`, `catalog_review` (đọc thẳng → lỗi 1142).
- **`sp_public_category_list()`** → `id`, `name`, `slug`, theo tên.
- **`sp_public_book_list(p_category_id, p_query)`** → đúng các cột: `id`, `title`, `author`, `isbn`, `category_id`, `description`, `price`, `cover_image`, `created_at`, `in_stock` (0/1, `stock > 0`), `rating` (`ROUND(AVG, 1)` của đánh giá `is_visible = 1`, NULL khi chưa có), `review_count`.
  - **Không bao giờ trả** `cost_price`, `stock`, `is_active`, `updated_at`. Chỉ sách `is_active = 1`.
  - `p_category_id`: NULL = mọi thể loại; số ≤ 0 → `INVALID_INPUT`.
  - `p_query`: NULL/rỗng = không lọc; tối đa 100 ký tự (hơn → `INVALID_INPUT`); tìm trong tên sách hoặc tác giả, không phân biệt hoa/thường và dấu; ký tự `%`, `_`, `\` được thoát nên chỉ tìm đúng chữ người dùng gõ. Không có SQL động.
  - Mới nhất trước (`created_at DESC`), tối đa 200 cuốn (chưa có phân trang).
- **Django:** `catalog/services.py` giữ nguyên `list_categories()` và `list_public_books(category_id=None, q="")`; gọi `callproc` với tham số truyền riêng; `catalog/views.py` và template không đổi.
- **Kiểm thử:** `catalog/tests/test_public_catalog.py`, `catalog/tests/test_home.py`; `db_check_grants` có 4 dòng cho phần này. Đã chạy trên CSDL thật: sách ẩn và thể loại chỉ có sách ẩn không lộ, đánh giá ẩn không được tính, `' OR 1=1 -- `, `%' UNION SELECT password FROM accounts_user -- `, `%`, `_` đều trả 0 kết quả, không lỗi 500.

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
