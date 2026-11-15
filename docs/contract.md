# Hợp đồng frontend – backend

Mỗi trang một dòng. Frontend dựng template theo cột "Biến trong template" (dùng dữ liệu giả trước), backend viết view trả đúng các biến đó và xử lý đúng các trường gửi lên. Đổi hợp đồng thì sửa file này trong cùng PR.

Quy ước:
- URL name dạng `app:ten` (dùng `{% url 'app:ten' %}`, không gõ cứng đường dẫn).
- Mọi form `POST` có `{% csrf_token %}`. GET không đổi dữ liệu.
- Biến chỉ in bằng `{{ ... }}` (tự escape), không `|safe`.
- "Quyền": ai được vào trang (khách vãng lai / khách đã đăng nhập / nhân viên + quyền gì).

| URL name | Đường dẫn | Template | Quyền | Biến trong template | Trường gửi lên (POST) |
| --- | --- | --- | --- | --- | --- |
| `catalog:home` | `/` | `shop/home.html` | Mọi người | `categories` (list: `id`, `name`), `books` (list sách, mỗi cuốn có các trường ở mục *BookCard* bên dưới), `current_category` (int hoặc `None`), `q` (chuỗi đã làm sạch), `cart_add_url` (URL của `orders:cart_add`) | – (chỉ GET: `?q=` tối đa 100 ký tự, `?category=` số nguyên dương) |
| `catalog:about` | `/gioi-thieu/` | `shop/about.html` | Mọi người | – | – |
| `catalog:book_detail` | `/sach/<id>/` | `shop/book_detail.html` | Mọi người (sách ẩn/không có → 404) | `book` (BookCard + `isbn`, `description`, `category_name`), `reviews` (list `PublicReview`), `form` (`ReviewForm` hoặc `None`), `my_review` (`MyReview` hoặc `None`), `can_review`, `open_form`, `login_url`, `cart_add_url`, `cart_max` (= 5) | – (chỉ GET) |
| `catalog:review_submit` | `/sach/<id>/danh-gia/` | – (redirect về `book_detail#danh-gia`; lỗi → hiện lại `book_detail` mã 400) | Khách đã đăng nhập (ẩn danh → đăng nhập rồi quay lại trang sách; nhân viên bị từ chối) | – | `rating` (1–5), `content` (chỉ POST + CSRF) |
| `orders:cart_add` | `/orders/cart/them/` | – (redirect về trang đang xem kèm thông báo) | Khách đã đăng nhập, đã xác nhận email (ẩn danh → đăng nhập rồi quay lại; nhân viên bị từ chối) | – | `book_id`, `quantity` (1–5), `next` (chỉ đường dẫn trong site; chỉ POST + CSRF) |
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

Khi thêm vào giỏ, form chỉ gửi `book_id`, `quantity` và `next` (trang đang xem). **Không gửi giá**: giá luôn lấy lại từ CSDL ở phía server. Nút giỏ chỉ hiện khi sách còn hàng và người xem không phải nhân viên.

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

## Đánh giá sách: `sp_review_save`, `sp_review_get_mine`

Chốt 2026-11-15. File: `database/objects/21_review.sql`, `catalog/review_services.py`, `catalog/forms.py`. Phần này chỉ có thủ tục và service; nút gửi và form trên trang làm cùng trang chi tiết sách.

- **Ai được đánh giá:** khách đang hoạt động, đã xác nhận email, không phải nhân viên (cách b). Khi có đơn hàng sẽ siết lại thành "chỉ khách đã mua sách đó" (cách a).
- **Mỗi khách một đánh giá cho mỗi sách.** Gửi lại là **sửa** đánh giá cũ (`INSERT ... ON DUPLICATE KEY UPDATE`): bấm hai lần cùng lúc vẫn chỉ một dòng. Sửa không đổi `is_visible`: đánh giá admin đã ẩn thì vẫn ẩn.
- **Hiện ngay** sau khi gửi; admin ẩn sau nếu vi phạm.
- **Tên hiển thị** (dùng khi làm danh sách đánh giá): `mask_username()` giữ ký tự đầu và cuối, giữa là dấu sao, ví dụ `an_nguyen` → `a*******n`.

| Thủ tục | Tham số | Trả về / lỗi |
| --- | --- | --- |
| `sp_review_save` | `p_user_id`, `p_book_id`, `p_rating` (1–5), `p_content` (1–2000 ký tự sau khi bỏ khoảng trắng), `OUT p_created` | `p_created` = 1 đánh giá mới, 0 là sửa. Lỗi: `INVALID_INPUT`, `NOT_CUSTOMER`, `BOOK_NOT_FOUND` (sách không có hoặc đang ẩn) |
| `sp_review_get_mine` | `p_user_id`, `p_book_id` | 0 hoặc 1 dòng: `rating`, `content`, `is_visible`, `created_at`, `updated_at` |

`r_customer` chỉ có `EXECUTE`; ghi thẳng `catalog_review` → 1142. `app_staff` gọi `sp_review_save` → 1370.

**Django:**

```python
from catalog.review_services import ReviewError, get_my_review, save_review

created = save_review(request, book_id, rating, content)   # user lấy từ request.user, không từ form
mine = get_my_review(request.user, book_id)                 # MyReview hoặc None
```

| Lớp bảo vệ | Cách làm |
| --- | --- |
| Giả mạo người gửi | `user_id` lấy từ `request.user` ở server; `ReviewForm` chỉ có `rating`, `content` (id sách nằm trên URL); thủ tục kiểm tra lại người đó là khách hợp lệ |
| Đầu vào | Điểm là số nguyên 1–5 (form `TypedChoiceField`, service, thủ tục, CHECK); id sách sai kiểu → `BOOK_NOT_FOUND` không xuống CSDL |
| XSS | Nội dung giữ nguyên chữ người gõ, chỉ hiển thị qua auto-escape, không `|safe` |
| Ký tự lạ | Bỏ ký tự điều khiển, ký tự rộng 0 và ký tự đảo chiều văn bản (U+202E...) dùng để giả mạo hiển thị; gộp quá 2 dòng trống |
| Spam | Tối đa `REVIEW_RATE_LIMIT` = 5 lần gửi/sửa mỗi `REVIEW_RATE_WINDOW` = 1 giờ cho mỗi khách; vượt → `RATE_LIMITED`, ghi log `rate_limited` |
| Race condition | UNIQUE + `ON DUPLICATE KEY UPDATE`; khóa chia sẻ dòng sách trong lúc ghi |
| CSRF, chỉ POST, bắt buộc đăng nhập | Áp dụng ở view khi làm trang chi tiết sách |

Đã chạy trên CSDL thật: gửi mới, sửa, điểm 6, nội dung rỗng, admin gửi, sách không có, sách ẩn, `app_customer` INSERT/UPDATE/DELETE thẳng (1142), giả `user_id` của admin khi gọi thủ tục (`NOT_CUSTOMER`), hai lần bấm cùng lúc (1 dòng), lần thứ 6 trong giờ (`RATE_LIMITED`), sửa đánh giá đã bị ẩn (vẫn ẩn). Test: `catalog/tests/test_reviews.py`.

## Trang chi tiết sách: `sp_public_book_get`, `sp_review_list`

Chốt 2026-11-15. Bố cục: ảnh bìa lớn bên trái; bên phải thể loại, tên, tác giả, sao, giá, bảng thông tin (tác giả, thể loại, ISBN, tình trạng), giới thiệu; nút **Đặt hàng** hiện nhưng bị làm mờ ("sắp có"); bên dưới là danh sách đánh giá và nút **Đánh giá** mở form bằng thẻ `<details>` (không cần JS, CSP giữ chặt). Ảnh bìa và tên sách trên trang chủ dẫn tới trang này.

| Thủ tục | Tham số | Trả về |
| --- | --- | --- |
| `sp_public_book_get` (`objects/20_...`) | `p_book_id` | 0 hoặc 1 dòng: cùng cột với `sp_public_book_list` + `category_name`. Sách ẩn hoặc không có → 0 dòng như nhau |
| `sp_review_list` (`objects/21_...`) | `p_book_id` | Tối đa 50 đánh giá `is_visible = 1` của sách đang hiện, mới nhất trước: `display_name` (**username đã che ngay trong CSDL**: ký tự đầu + dấu sao + ký tự cuối), `rating`, `content`, `created_at`, `updated_at`. Không trả `user_id`, email |

`r_customer` chỉ có `EXECUTE`. Django: `catalog.services.get_public_book(id)` (id sai kiểu → `None`, không xuống CSDL), `catalog.review_services.list_reviews(id)` trả `PublicReview` (thuộc tính `edited` khi `updated_at > created_at`, hiện chữ "đã sửa").

Form đánh giá theo người xem:

| Người xem | Hiển thị |
| --- | --- |
| Chưa đăng nhập | Nút "Đăng nhập để đánh giá" → `login?next=/sach/<id>/`; POST thẳng cũng bị chuyển về đăng nhập |
| Nhân viên | Không có form; POST bị từ chối |
| Khách chưa đánh giá | Nút "Đánh giá" |
| Khách đã đánh giá | Nút "Sửa đánh giá", form điền sẵn; nếu đánh giá bị ẩn thì báo "đang bị quản trị viên ẩn" |

Bảo mật đã kiểm tra (test `catalog/tests/test_book_detail.py` + chạy thật trong sandbox): sách ẩn → 404 cả trang lẫn POST; `user_id` gửi kèm form bị bỏ qua; thiếu CSRF → 403; GET `/danh-gia/` → 405; nội dung `<script>` hiện ra như chữ (`linebreaksbr` escape trước rồi mới thêm `<br>`); tên thật không có trong HTML; lỗi form hiện lại trang với mã 400 và form đang mở.

## Thêm vào giỏ hàng: `sp_cart_add`

Chốt 2026-11-15. Cạnh nút **Đặt hàng** (trang chi tiết) có ô số lượng (1–5, mặc định 1) và nút **Thêm vào giỏ**; thẻ sách ở trang chủ có nút giỏ thêm 1 cuốn. Thêm xong ở lại trang đang xem và hiện "Đã thêm vào giỏ. Trong giỏ đang có N cuốn sách này."

| Thủ tục | Tham số | Kết quả |
| --- | --- | --- |
| `sp_cart_add` (`objects/31_cart.sql`) | `p_user_id`, `p_book_id`, `p_quantity`, OUT `p_new_quantity` | Tạo giỏ nếu chưa có (UNIQUE `user_id`), cộng dồn số lượng, trả tổng số cuốn sách đó trong giỏ |

Quy tắc (kiểm tra trong thủ tục, trong một transaction, khóa dòng giỏ `FOR UPDATE` và dòng sách `FOR SHARE`):

| Mã lỗi | Khi nào | Thông báo |
| --- | --- | --- |
| `INVALID_INPUT` | `quantity` ngoài 1–5 | Số lượng phải từ 1 đến 5. |
| `NOT_CUSTOMER` | Người gọi là nhân viên, bị khóa hoặc chưa xác nhận email | Chỉ khách đã đăng nhập và xác nhận email mới thêm vào giỏ được. |
| `BOOK_NOT_FOUND` | Sách không có hoặc đang ẩn (như nhau) | Không tìm thấy sách. |
| `OUT_OF_STOCK` | Tồn kho = 0 | Sách đã hết hàng. |
| `CART_LIMIT` | Tổng trong giỏ vượt 5 cuốn/sách (báo lỗi, không tự cắt) | Mỗi sách tối đa 5 cuốn trong giỏ hàng. |
| `CART_FULL` | Giỏ đã có 30 đầu sách khác nhau | Giỏ hàng đã có 30 đầu sách. Hãy đặt hàng hoặc bớt sách trước. |
| `RATE_LIMITED` | Quá 20 lần/60 giây (Django, theo `user.pk`) | Bạn thao tác quá nhanh. Hãy thử lại sau ít phút. |

Không so số lượng với tồn kho chính xác (chỉ chặn khi hết hàng) để không lộ tồn kho qua thông báo lỗi; tồn kho thật được kiểm tra lại khi đặt đơn (`sp_place_order`).

`r_customer` chỉ có `EXECUTE sp_cart_add`, không đọc/ghi thẳng `orders_cart`, `orders_cartitem`. Django: `orders.cart_services.add_to_cart(request, book_id, quantity)` lấy user từ phiên (không nhận `user_id` từ form); `book_id` sai kiểu → `BOOK_NOT_FOUND` không xuống CSDL. `next` qua `url_has_allowed_host_and_scheme`, link ngoài site → về trang chi tiết sách.

Bảo mật đã kiểm tra (test `orders/tests/test_cart_add.py`, `db_check_grants` + chạy thật trong sandbox): open redirect (`https://evil.example`, `//evil.example`, `javascript:`) bị chặn; thiếu CSRF → 403; GET → 405; giá gửi kèm bị bỏ qua; `app_customer` INSERT/UPDATE/SELECT thẳng `orders_cartitem` → 1142; gọi thủ tục bằng id quản trị → `NOT_CUSTOMER`; 3 lần thêm 2 cuốn cùng lúc → 2, 4, `CART_LIMIT` và chỉ một giỏ.

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
