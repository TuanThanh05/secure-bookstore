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
| `orders:cart` | `/orders/cart/` | `shop/cart.html` | Khách đã đăng nhập (ẩn danh → đăng nhập; nhân viên → về dashboard); không lưu cache | `cart` (`Cart`: `lines` là list `CartLine`, `subtotal`, `item_count`, `has_unavailable`), `cart_max` (= 5), `cart_update_url`, `cart_remove_url` | – (chỉ GET) |
| `orders:cart_update` | `/orders/cart/cap-nhat/` | – (redirect về `orders:cart` kèm thông báo) | Như `orders:cart` | – | `book_id`, `quantity` (**số lượng cuối cùng** 1–5; chỉ POST + CSRF) |
| `orders:cart_remove` | `/orders/cart/go/` | – (redirect về `orders:cart` kèm thông báo) | Như `orders:cart` | – | `book_id` (chỉ POST + CSRF) |
| `orders:checkout` | `/orders/dat-hang/` | `shop/checkout.html` | Khách đã đăng nhập (ẩn danh → đăng nhập; nhân viên → dashboard); giỏ không rỗng, không có sách ngừng bán/hết hàng; không lưu cache | `form` (`CheckoutForm`), `cart`, `shipping_fee` (30.000), `total` | `shipping_name`, `phone`, `address` (chỉ POST + CSRF; mã chống trùng nằm trong phiên, không có trong form) |
| `orders:order_detail` | `/orders/don/<code>/` | `shop/order_detail.html` | Chỉ chủ đơn; mã sai mẫu, đơn không có hay đơn của người khác đều 404; không lưu cache | `order` (`Order`: `code`, `status`, `status_label`, `subtotal`, `shipping_fee`, `total`, `shipping_name`, `shipping_phone`, `shipping_address`, `created_at`, `expires_at`, `paid_at`, `cancelled_at`, `awaiting_payment`, `expired`, `can_cancel`, `lines` là list `OrderLine`) | – (chỉ GET) |
| `orders:order_cancel` | `/orders/don/<code>/huy/` | – (redirect về trang đơn kèm thông báo) | Chỉ chủ đơn (đơn người khác/mã sai → 404); nhân viên → dashboard | – | – (chỉ POST + CSRF, sau bước xác nhận `<details>` trên trang đơn) |
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

## Trang giỏ hàng: `sp_cart_list`, `sp_cart_set_quantity`, `sp_cart_remove`

Chốt 2026-11-15. Mỗi sách một dòng: ảnh, tên (dẫn tới trang chi tiết nếu còn bán), tác giả, giá hiện tại, nút **−** / số lượng / **+**, thành tiền, nút **Gỡ**. Bên phải là ô **Tạm tính** ("Giá chốt khi đặt hàng") và nút **Đặt hàng** làm mờ (sắp có).

| Thủ tục | Tham số | Kết quả |
| --- | --- | --- |
| `sp_cart_list` | `p_user_id` | Tối đa 30 dòng, theo thứ tự thêm vào: `id` sách, `title`, `author`, `cover_image`, `price` (giá hiện tại), `quantity`, `is_active`, `in_stock` (0/1). Không trả số tồn kho, giá nhập |
| `sp_cart_set_quantity` | `p_user_id`, `p_book_id`, `p_quantity` | Đặt số lượng mới 1–5 (dùng cho cả tăng và giảm) |
| `sp_cart_remove` | `p_user_id`, `p_book_id` | Gỡ sách khỏi giỏ, không hỏi xác nhận |

**Vì sao tăng/giảm gửi số lượng cuối cùng chứ không gửi "+1":** nút "+" của dòng đang có 2 cuốn gửi `quantity=3`. Bấm đúp, mở hai tab hay gửi lại form thì kết quả vẫn là 3, không bị cộng dồn ngoài ý muốn.

| Tình huống | Hiển thị / kết quả |
| --- | --- |
| Đang 1 cuốn | Nút "−" bị khóa; muốn bỏ thì bấm Gỡ |
| Đang 5 cuốn | Nút "+" bị khóa; gửi thẳng `quantity=6` → `INVALID_INPUT` |
| Sách bị admin ẩn | Mờ, nhãn "Ngừng bán", không có link, chỉ còn Gỡ; đổi số lượng → `BOOK_UNAVAILABLE` |
| Sách hết hàng | Mờ, nhãn "Hết hàng", chỉ còn Gỡ; thủ tục chặn tăng (`OUT_OF_STOCK`), giảm vẫn cho vì vô hại |
| Tạm tính | Chỉ cộng sách còn bán và còn hàng, có ghi chú khi có sách bị loại |

| Mã lỗi mới | Thông báo |
| --- | --- |
| `NOT_IN_CART` | Sách này không có trong giỏ hàng. |
| `BOOK_UNAVAILABLE` | Sách đã ngừng bán, chỉ có thể gỡ khỏi giỏ. |

Sách không có trong giỏ luôn trả `NOT_IN_CART`, dù sách có tồn tại hay đang ẩn, nên không dò được sách ẩn qua các URL này. Hai thủ tục ghi khóa dòng giỏ `FOR UPDATE` (cùng thứ tự khóa với `sp_cart_add`, `sp_place_order`) nên chạy đồng thời không deadlock, không sai số.

`r_customer` chỉ có `EXECUTE`. Django: `orders.cart_services.get_cart(request)`, `set_cart_quantity(request, book_id, quantity)`, `remove_from_cart(request, book_id)` lấy user từ phiên; id/số lượng sai kiểu bị chặn trước khi xuống CSDL; đổi số lượng và gỡ chung giới hạn 60 lần/60 giây (`CART_UPDATE_RATE_*`). Các form trên trang giỏ luôn quay về `/orders/cart/`, không nhận `next`.

Bảo mật đã kiểm tra (test `orders/tests/test_cart_page.py`, `db_check_grants` tổng 39 + chạy thật trong sandbox): `user_id`, giá, `next` gửi kèm bị bỏ qua; thiếu CSRF → 403; GET các URL ghi → 405; `app_customer` SELECT/UPDATE/DELETE thẳng `orders_cartitem` → 1142; gọi 3 thủ tục bằng id quản trị → `NOT_CUSTOMER`; 5 vòng chạy đồng thời đổi số lượng, gỡ và thêm vào giỏ cùng lúc → không lỗi lạ, một giỏ, số lượng luôn 1–5.

## Đặt đơn: `sp_place_order` và `orders.services.place_order`

Chốt 2026-11-14, bổ sung 2026-11-16 (nhánh đặt hàng). Đổi chữ ký thủ tục hoặc hàm thì sửa mục này trong cùng PR.

**Luồng:** trang giỏ → nút **Đặt hàng** (`/orders/dat-hang/`) → điền tên người nhận, SĐT, địa chỉ (tên và SĐT điền sẵn từ hồ sơ, vẫn sửa được; địa chỉ nhập mới mỗi lần) → **Xác nhận đặt hàng** → trang đơn `/orders/don/<mã đơn>/` (trạng thái "Chờ thanh toán", hạn thanh toán 15 phút, nút Thanh toán mờ cho tới nhánh thanh toán). Nút **Đặt hàng** ở trang chi tiết sách gửi cùng form thêm vào giỏ (`then=cart`) rồi chuyển sang trang giỏ.

**Thủ tục MySQL** (`database/objects/30_sp_place_order.sql`), `r_customer` chỉ có `EXECUTE`:

| Tham số | Kiểu | Ghi chú |
| --- | --- | --- |
| `p_user_id` | IN BIGINT | Luôn là `request.user.pk`, không bao giờ lấy từ form; thủ tục tự kiểm tra lại là khách hợp lệ |
| `p_idempotency_key` | IN CHAR(32) | 32 ký tự hex thường, Django sinh và giữ trong phiên (`checkout_idempotency_key`), không nhận từ form |
| `p_shipping_name` | IN VARCHAR(255) | Tên người nhận, 1–100 ký tự sau khi bỏ khoảng trắng hai đầu |
| `p_phone_encrypted` | IN VARCHAR(512) | SĐT đã mã hóa AES-GCM ở Django |
| `p_address_encrypted` | IN VARCHAR(1024) | Địa chỉ đã mã hóa AES-GCM ở Django |
| `p_order_code` | OUT CHAR(32) | Mã đơn (`RANDOM_BYTES`), dùng trên URL thay cho id |
| `p_created` | OUT TINYINT | `1` = đơn mới, `0` = gửi lại cùng mã yêu cầu, trả mã đơn cũ |

Danh sách sách, số lượng, giá đều do thủ tục đọc từ giỏ và `catalog_book`. Phí ship cố định 30.000 đ (`SHIPPING_FEE` ở Django chỉ để hiển thị trước); hạn thanh toán 15 phút. Kho bị trừ ngay khi tạo đơn.

**Chống giữ kho (chốt 2026-11-16):** mỗi khách tối đa **1 đơn chờ thanh toán còn hạn** (`PENDING_EXISTS`), kiểm tra khi đang giữ khóa giỏ nên nhiều tab bấm cùng lúc cũng chỉ ra 1 đơn; Django giới hạn thêm 5 lần đặt/10 phút (`ORDER_PLACE_RATE_*`). Hủy đơn quá hạn và trả kho làm ở nhánh thanh toán.

**Mã hóa:** SĐT và địa chỉ mã hóa AES-GCM, ngữ cảnh `orders_order.<cột>:<user_id>:<idempotency_key>` (`shipping_context`). Bản mã chép sang đơn khác, người khác hoặc cột khác đều không giải mã được.

**Hàm Django** (`backend/orders/services.py`):

```python
place_order(request, idempotency_key, shipping_name, phone, address) -> PlaceOrderResult(order_code, created)
get_order(request, code) -> Order
```

- `place_order` nhận SĐT, địa chỉ **chưa mã hóa** (đã qua `CheckoutForm`) và tự mã hóa; không gọi bên trong `transaction.atomic`.
- Lỗi nghiệp vụ raise `OrderError` có `.code` và `.message`. Frontend chỉ hiển thị `.message`:

| `code` | `message` | View làm gì |
| --- | --- | --- |
| `OUT_OF_STOCK` | Một số sách vừa hết hàng hoặc không đủ số lượng, vui lòng kiểm tra lại giỏ. | Về giỏ |
| `BOOK_INACTIVE` | Một số sách đã ngừng bán. Hãy gỡ chúng khỏi giỏ trước khi đặt hàng. | Về giỏ |
| `CART_EMPTY` | Giỏ hàng đang trống. | Về giỏ |
| `PENDING_EXISTS` | Bạn đang có một đơn chờ thanh toán... | Về đơn đó nếu phiên còn nhớ mã (`last_order_code`), không thì ở lại form |
| `INVALID_INPUT`, `NOT_CUSTOMER`, `RATE_LIMITED` | (xem `ORDER_ERROR_MESSAGES`) | Ở lại form, mã 400 |
| `ORDER_NOT_FOUND` | Không tìm thấy đơn hàng. | `get_order`: trang đơn trả 404 |

- Thành công: xóa mã chống trùng khỏi phiên (lần đặt sau có mã mới), nhớ `last_order_code`, chuyển sang trang đơn. Bấm đúp: cùng mã → thủ tục trả lại đơn cũ.
- Mọi lỗi khác (mất kết nối, lỗi quyền 1142...) được ném nguyên ra ngoài để ghi log, không đổi thành `OrderError`.

## Đọc đơn: `sp_order_get`

`sp_order_get(p_user_id, p_code)` (cùng file 30) trả 2 bộ kết quả: dòng đơn (kể cả `idempotency_key` để Django giải mã, không đưa ra template) và các sách (`book_id`, `book_title`, `unit_price`, `quantity` lúc đặt). Mã sai mẫu, đơn không có hay đơn của người khác đều `ORDER_NOT_FOUND` → 404 như nhau, nên không dò được mã đơn của người khác (IDOR). Trang chi tiết đơn `never_cache` vì có SĐT, địa chỉ.

## Hủy đơn và đơn quá hạn: `sp_order_cancel`, `sp_cancel_expired_orders`, `ev_cancel_expired_orders`

Chốt 2026-11-16 (nhánh A, làm trước khung thanh toán). File `database/objects/33_order_cancel.sql`.

Kho bị trừ ngay khi tạo đơn, nên **hủy đơn = cộng lại đúng số cuốn trong chi tiết đơn**, cùng giao dịch với việc đổi trạng thái sang `cancelled` (ghi `cancelled_at`).

| Ai | Cách | Điều kiện |
| --- | --- | --- |
| Khách | Nút **Hủy đơn hàng** trên trang đơn → hộp xác nhận (`<details>`, không JS) → **Xác nhận hủy đơn** (POST) → `sp_order_cancel(user_id, code)` | Đơn của chính mình, đang `pending` (kể cả đã quá hạn mà Event chưa kịp hủy) |
| Hệ thống | MySQL Event `ev_cancel_expired_orders` mỗi phút → `sp_cancel_expired_orders` → `sp_order_expire_one` từng đơn | Đơn `pending` có `expires_at <= UTC_TIMESTAMP()`, tối đa 200 đơn mỗi lần |

**Không hủy được:** đơn đã thanh toán, đang giao, đã giao, đã hủy → `ORDER_NOT_CANCELLABLE` ("Đơn hàng này không còn hủy được..."). Không có hoàn tiền; trigger khóa đơn cũng chỉ cho `pending → cancelled`.

**Chống race condition:** mỗi lần hủy khóa dòng đơn `FOR UPDATE` rồi mới kiểm tra lại trạng thái. Khách bấm hủy đúng lúc Event chạy, hoặc bấm nhiều lần cùng lúc, thì chỉ một bên hủy được, kho cộng đúng một lần. Thứ tự khóa đơn → sách; `sp_place_order` khóa giỏ → sách và không khóa dòng đơn cũ, nên không deadlock. Thủ tục thanh toán sau này cũng khóa dòng đơn và chỉ nhận khi `expires_at` còn hạn, nên không có đơn vừa "đã thanh toán" vừa "đã hủy".

**Một đơn lỗi không chặn các đơn khác:** mỗi đơn quá hạn hủy trong giao dịch riêng (`sp_order_expire_one` có `ROLLBACK; RESIGNAL`), vòng lặp bắt lỗi rồi đi tiếp; đơn lỗi được thử lại ở phút sau.

**Quyền:** `r_customer` chỉ có `EXECUTE sp_order_cancel`. `sp_cancel_expired_orders`, `sp_order_expire_one` không cấp cho tài khoản ứng dụng nào (chỉ Event gọi). Definer cần `UPDATE orders_order` và **quyền `EVENT` trên CSDL**: thiếu quyền này Event không chạy (log MySQL: "user no longer has EVENT privilege"). Lần đầu chạy `db_apply`, Event có thể chạy trúng khoảng giữa lúc tạo Event và lúc cấp quyền rồi báo lỗi một lần trong log MySQL; phút sau chạy bình thường. Cần `event_scheduler = ON` (`database/config/my.cnf` đã bật). Kiểm tra Event: `SELECT EVENT_NAME, STATUS FROM information_schema.EVENTS;` bằng root.

**Django:** `orders.services.cancel_order(request, code)` lấy user từ phiên, mã đơn sai mẫu không xuống CSDL, giới hạn 10 lần/10 phút (`ORDER_CANCEL_RATE_*`). `Order.can_cancel` = đang `pending`. Trang đơn hiện nhãn: Chờ thanh toán, Quá hạn thanh toán (kèm "sẽ được hệ thống tự hủy trong ít phút"), Đã hủy (kèm thời điểm hủy), Đã thanh toán.

**Đã kiểm tra** (test `orders/tests/test_order_cancel.py`, `db_check_grants` tổng 51 + chạy thật trong sandbox): Event hủy đơn quá hạn và trả kho, không đụng đơn còn hạn; Event chạy được dù `bookstore_definer` bị khóa đăng nhập; khách hủy đơn → kho cộng lại; hủy lần 2, hủy đơn đã thanh toán → `ORDER_NOT_CANCELLABLE`; khách A hủy đơn khách B → 404, đơn B không đổi; GET → 405, thiếu CSRF → 403; `app_customer` gọi `sp_cancel_expired_orders`/`sp_order_expire_one` → 1370; gọi `sp_order_cancel` bằng id quản trị → `NOT_CUSTOMER`. Chạy đồng thời 5 vòng khách hủy + Event cùng một đơn → 1 bên hủy, kho đúng; 3 vòng bấm hủy 4 lần cùng lúc → 1 thành công, kho đúng; một đơn bị khóa ở phiên khác → các đơn quá hạn còn lại vẫn được hủy, đơn bị khóa được hủy ở lần sau.

## Đơn đã tạo không sửa được: `32_trg_orders_guard.sql`

Chốt 2026-11-16: thanh toán xong (và cả lúc đang chờ thanh toán) không thể tăng số lượng hay thêm sách khác vào đơn. Hai lớp:

1. **Quyền:** không tài khoản ứng dụng nào có quyền ghi `orders_order`, `orders_orderitem`; không có thủ tục nào sửa đơn.
2. **Trigger** (chặn cả root, cả khi một thủ tục sau này viết sai), mã lỗi `ORDER_LOCKED`:

| Bảng | Quy tắc |
| --- | --- |
| `orders_orderitem` | Chỉ thêm khi đơn `pending`, chưa thanh toán và **tổng các dòng không vượt `subtotal` đã chốt** (lúc tạo đơn các dòng cộng lại vừa bằng `subtotal`, nên sau đó thêm bất kỳ dòng nào cũng bị chặn). Không bao giờ sửa, không bao giờ xóa |
| `orders_order` | Không đổi mã đơn, người đặt, tiền sách, phí ship, tổng tiền, thông tin giao hàng, mã chống trùng, ngày tạo, hạn thanh toán. Trạng thái chỉ đi `pending → paid/cancelled`, `paid → shipped`, `shipped → delivered`; `paid_at`, `cancelled_at` ghi một lần đúng lúc chuyển trạng thái. Không xóa đơn |

Đã thử bằng root trong sandbox: thêm sách vào đơn đang chờ hay đã thanh toán, tăng số lượng, sửa giá, sửa tổng tiền, sửa người nhận, nhảy `pending → shipped`, quay lại `pending`, hủy đơn đã thanh toán, xóa dòng, xóa đơn → đều `ORDER_LOCKED`; `pending → paid`, `paid → shipped` đi qua.

**Bảo mật đã kiểm tra** (test `orders/tests/test_checkout.py`, `test_place_order.py`, `db_check_grants` tổng 46 + chạy thật): `total`, `user_id`, `idempotency_key` gửi kèm form bị bỏ qua; thiếu CSRF → 403; khách B mở đơn của khách A → 404; mã đơn chứa `' OR 1=1` → 404 không xuống CSDL; `app_customer` đọc/sửa thẳng `orders_order`, thêm thẳng `orders_orderitem` → 1142; gọi thủ tục bằng id quản trị → `NOT_CUSTOMER`; CSDL chỉ lưu bản mã (`v1.`...). Chạy đồng thời: cùng khách bấm 4 lần cùng mã → 1 đơn mới + 3 lần trả lại đơn cũ; cùng khách 3 tab khác mã → 1 đơn + 2 `PENDING_EXISTS`; hai khách tranh cuốn cuối → 1 đơn + 1 `OUT_OF_STOCK`, kho về 0, không âm.


## Thanh toán mô phỏng: `sp_payment_simulate`

Chốt 2026-11-16, tạm thời khi chưa có cổng thật. Chi tiết: `docs/thanh-toan-mo-phong.md`.

- Bật bằng `PAYMENT_SIMULATION=True` trong `.env`; tắt thì nút hiện "Chưa cấu hình cổng thanh toán".
- `POST /payments/mo-phong/<mã đơn>/` (`payments:simulate`) → `payments.services.simulate_payment(request, code)` → `sp_payment_simulate(user_id, code, client_ip, OUT transaction_id)`.
- Thủ tục khóa dòng đơn của chính khách, chỉ nhận đơn `pending` còn hạn, ghi một dòng `payments_payment` (`provider = 'simulated'`, số tiền lấy từ `total` của đơn) rồi đổi đơn sang `paid` trong cùng giao dịch. Mã lỗi: `ORDER_NOT_FOUND` (→ 404 + `idor_attempt`), `ORDER_ALREADY_PAID`, `ORDER_NOT_PAYABLE`, `ORDER_EXPIRED`, `NOT_CUSTOMER`, `INVALID_INPUT`; service thêm `NOT_CONFIGURED`, `RATE_LIMITED`.
- Giao dịch đã ghi không sửa/xóa được (trigger `PAYMENT_LOCKED`); một đơn tối đa một giao dịch thành công (UNIQUE `uq_payment_success_order`).

## Luồng trạng thái đơn sau khi thanh toán (chốt 2026-11-16)

```
pending → paid → confirmed → packed → shipped → delivered
Chờ thanh toán → Đã thanh toán → Đã tiếp nhận → Đã đóng gói → Đang giao → Đã giao
pending → cancelled (khách hủy hoặc quá hạn)
```

- Lược đồ `database/schema/07_order_status_flow.sql` (migration `core/0008_order_status_flow`): thêm `confirmed`, `packed` vào CHECK `ck_order_status`; `ck_order_paid_has_time` bắt buộc `paid_at` với mọi trạng thái từ `paid` trở đi.
- Trigger `32_trg_orders_guard.sql` chỉ cho đi tới **đúng một bước**, không nhảy cóc, không quay lại (kể cả root sửa tay → `ORDER_LOCKED`). Đơn từ `paid` trở đi không hủy được. `sp_payment_simulate` coi mọi trạng thái từ `paid` trở đi là `ORDER_ALREADY_PAID`.
- Bốn bước sau `paid` do admin bấm (gói "Quản lý đơn hàng", nhánh sau). Trigger 34 tự ghi nhật ký từng bước.

## Đơn hàng của tôi: `sp_order_list_mine`

Trang `/orders/` (`orders:list`), hai tab:

| Tab | `status=` | Trạng thái |
| --- | --- | --- |
| Đang xử lý | `active` (mặc định) | pending, paid, confirmed, packed, shipped |
| Lịch sử | `history` | delivered, cancelled (trạng thái cuối) |

- **Không dùng view**: mọi khách vào CSDL bằng cùng tài khoản `app_customer`, MySQL không biết ai đang xem, nên view "đơn của khách" sẽ trả đơn của mọi người. Thủ tục `sp_order_list_mine(user_id, group, offset, limit)` nhận `user_id` do Django lấy từ phiên và lọc `WHERE user_id` trong CSDL. Chỉ `r_customer` được gọi; `app_staff` gọi → 1370; id quản trị → `NOT_CUSTOMER`.
- Trả 2 bộ kết quả: tổng số + một trang (mới nhất trước): mã đơn, trạng thái, tổng tiền, các mốc thời gian, số cuốn, số đầu sách, tên cuốn đầu. **Không trả SĐT/địa chỉ** (xem ở trang chi tiết đơn). Kiểm tra: nhóm chỉ `active`/`history`, `limit` 1–50, `offset` 0–100000 → sai là `INVALID_INPUT`.
- Django: `orders.services.list_my_orders(request, group, page)` (nhóm sai không xuống CSDL, 10 đơn mỗi trang, `OrderSummary` chỉ đọc), view `order_list` (`login_required`, `never_cache`, `require_safe`, nhân viên → dashboard, tab sai → Đang xử lý, `trang` sai → 1). Mỗi đơn là một thẻ bấm sang `/orders/don/<mã đơn>/`; đơn chờ thanh toán đã quá hạn hiện "Quá hạn thanh toán".
- Đã kiểm tra trên CSDL thật: tổng số mỗi tab khớp với đếm trực tiếp; khách B không thấy đơn khách A; phân trang đúng; nhóm/limit/offset sai bị từ chối; trigger chặn paid → shipped, packed → delivered (nhảy cóc), confirmed → paid, packed → confirmed, delivered → shipped/cancelled (quay lại) và trạng thái lạ; nhật ký đơn ghi đủ pending, paid, confirmed, packed, shipped, delivered.
