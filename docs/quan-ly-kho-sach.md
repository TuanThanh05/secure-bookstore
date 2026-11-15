# Quản lý kho sách (backend)

Đã có: **thể loại sách** (mục 1), **sách, tồn kho, ẩn/hiện** (mục 4) và **upload ảnh bìa** (mục 5). Chưa có URL, view hay template; frontend làm sau.

## 1. Thể loại sách

### Đối tượng trong CSDL (`database/objects/40_category.sql`)

| Đối tượng | Việc | Mã lỗi có thể trả |
| --- | --- | --- |
| `sp_category_list()` | Danh sách thể loại theo tên: `id`, `name`, `slug`, `book_count` (mọi sách), `active_book_count` (sách đang hiện), `created_at` | – |
| `sp_category_create(actor, name, slug, OUT id)` | Thêm thể loại | `INVALID_INPUT`, `NOT_STAFF`, `CATEGORY_EXISTS` |
| `sp_category_rename(actor, id, name, slug)` | Sửa tên, slug đổi theo tên | thêm `CATEGORY_NOT_FOUND` |
| `sp_category_delete(actor, id)` | Xóa thể loại **chưa có sách nào, kể cả sách đang ẩn** | thêm `CATEGORY_IN_USE` |

Cả bốn thủ tục đều `SQL SECURITY DEFINER` với definer là `bookstore_definer` (tài khoản khóa đăng nhập).

### Phân quyền nhiều lớp

| Lớp | Cách làm |
| --- | --- |
| Quyền MySQL | Chỉ `r_staff` được EXECUTE bốn thủ tục. `app_customer` gọi thủ tục → lỗi 1370. Không tài khoản ứng dụng nào có INSERT/UPDATE/DELETE trên `catalog_category`; `app_staff` ghi thẳng → 1142 |
| Trong thủ tục | Kiểm tra `p_actor_id` là nhân viên đang hoạt động (`NOT_STAFF`), kiểm tra độ dài tên và định dạng slug (`INVALID_INPUT`) |
| Django | `catalog/staff_services.py` luôn gọi qua kết nối `staff`; `list_categories()` trả danh sách `StaffCategory` (dataclass chỉ đọc). Id không phải số → `CATEGORY_NOT_FOUND`, không gửi xuống CSDL. Tham số luôn truyền riêng qua `callproc`, không nối chuỗi |

### Nhật ký thay đổi

Mỗi lần thêm/sửa/xóa ghi một dòng `core_auditlog` **trong cùng giao dịch** (lỗi thì cả hai cùng hủy): `table_name = catalog_category`, `action`, `old_value`/`new_value` (JSON tên và slug), `db_user = USER()` (tài khoản gọi thủ tục, ví dụ `app_staff@localhost`; không dùng `CURRENT_USER()` vì trong thủ tục DEFINER nó luôn là `bookstore_definer`), `app_user_id` = id admin. Sửa mà không đổi gì thì không ghi.

### Trùng tên và race condition

- CSDL dùng collation `utf8mb4_unicode_ci`, không phân biệt hoa/thường và dấu, nên "Văn học", "VĂN HỌC" và "van hoc" bị coi là trùng (`CATEGORY_EXISTS`). Slug cũng trùng theo.
- Bấm thêm hai lần (hai tab, mạng chậm): ràng buộc UNIQUE chặn lần sau, thủ tục đổi lỗi 1062 thành `CATEGORY_EXISTS`.
- Xóa thể loại đúng lúc có sách được thêm vào: thủ tục khóa dòng thể loại (`FOR UPDATE`), câu thêm sách phải chờ; nếu vẫn lọt, khóa ngoại `ON DELETE RESTRICT` chặn (lỗi 1451) → `CATEGORY_IN_USE`.

### Slug

Django tạo từ tên (`make_slug`): bỏ dấu, `đ` → `d`, ký tự khác chữ/số thành `-`. Ví dụ "Địa lý & Lịch sử" → `dia-ly-lich-su`. Thủ tục kiểm tra lại định dạng bằng `REGEXP_LIKE(..., 'c')`; bảng còn có CHECK `ck_category_slug_format`.

### Dùng từ Django

```python
from catalog.staff_services import CategoryError, create_category, delete_category, list_categories, rename_category

new_id = create_category(request.user, "Văn học")
rename_category(request.user, new_id, "Văn học Việt Nam")
delete_category(request.user, new_id)          # CategoryError("CATEGORY_IN_USE") nếu còn sách
for c in list_categories():                    # gọi sp_category_list qua kết nối staff
    c.name, c.book_count, c.active_book_count, c.can_delete
```

Không gọi các hàm này bên trong `transaction.atomic` (thủ tục tự mở giao dịch); làm vậy sẽ bị `RuntimeError`.

## 2. Lệnh kiểm tra phân quyền trên CSDL thật

```bash
cd backend
python manage.py db_check_grants        # KHÔNG dùng --settings=bookstore.settings.migrate
```

Chạy 19 câu bằng `app_customer` và `app_staff` thật, so mỗi câu với kết quả mong đợi (được phép, hoặc đúng mã lỗi 1142 / 1143 / 1370 / 1644). Câu ghi luôn có `WHERE 1 = 0` hoặc đầu vào sai nên không đổi dữ liệu. CI chạy lệnh này ngay sau `db_apply` trên MySQL 8.4. Đây cũng là bằng chứng phân quyền tốt để đưa vào báo cáo và demo.

## 3. Vì sao đọc danh sách bằng thủ tục, không bằng view

Ban đầu danh sách là view `v_staff_categories`. Kiểm tra bằng `db_check_grants` trên cả **MySQL 8.0.46 (sandbox) và MySQL 8.4 (máy nhóm)**: view `SQL SECURITY DEFINER` có JOIN hoặc GROUP BY bị từ chối (lỗi 1143/1356) khi phiên người gọi đang bật role, dù definer đủ quyền. Cấp thêm quyền theo cột cho definer cũng không khắc phục được. Chỉ khi tắt role (`SET ROLE NONE`) và cấp quyền thẳng cho user thì đọc được, nhưng như vậy phải bỏ mô hình role của đồ án.

Thủ tục `SQL SECURITY DEFINER` không bị lỗi này, nên danh sách chuyển thành `sp_category_list()`. Về bảo mật hai cách tương đương: người gọi chỉ có EXECUTE, không chạm được bảng.

**Quy ước cho các phần sau** (sách, kho, đơn hàng của admin, `v_public_books` cho khách): dữ liệu đọc cần **nhiều bảng hoặc gộp nhóm** thì dùng **thủ tục đọc**; view chỉ dùng cho truy vấn đơn giản trên **một bảng**. Mỗi đối tượng mới nên thêm một dòng vào `db_check_grants` để CI kiểm tra trên MySQL 8.4 thật.

## 4. Sách, tồn kho, ẩn/hiện

### Đối tượng trong CSDL (`database/objects/41_book.sql`)

| Đối tượng | Việc | Mã lỗi chính |
| --- | --- | --- |
| `v_staff_books` | View **một bảng** `catalog_book`, mọi cột kể cả giá nhập (`cost_price`) và tồn kho. Chỉ `r_staff` được SELECT | – |
| `sp_book_create` | Thêm sách, nhập luôn tồn kho ban đầu (0–10.000); sách mới ở trạng thái **hiện** | `INVALID_INPUT`, `ISBN_EXISTS`, `CATEGORY_NOT_FOUND` |
| `sp_book_update` | Sửa thông tin: tên, tác giả, ISBN, thể loại, mô tả, ảnh, giá bán, giá nhập. **Không đụng tồn kho, không ẩn/hiện** | thêm `BOOK_NOT_FOUND` |
| `sp_book_set_active` | Ẩn (0) hoặc hiện (1) | `BOOK_NOT_FOUND` |
| `sp_book_restock` | Nhập thêm 1–10.000 cuốn, tổng tồn sau khi nhập ≤ 10.000; trả tồn kho mới | `INVALID_QUANTITY`, `STOCK_LIMIT` |
| `sp_book_reduce_stock` | Giảm kho ngoại lệ (hỏng, thất lạc...), không cho âm; trả tồn kho mới | `INVALID_QUANTITY`, `INSUFFICIENT_STOCK` |
| `sp_book_delete` | Xóa hẳn: sách **phải đang ẩn** và **chưa từng có trong đơn hàng** | `BOOK_ACTIVE`, `BOOK_HAS_ORDERS` |

Tất cả theo cùng mẫu với thể loại: `SQL SECURITY DEFINER`, tự kiểm tra `NOT_STAFF`, ghi `core_auditlog` trong cùng giao dịch, lỗi thì `ROLLBACK`. Không tài khoản ứng dụng nào ghi thẳng được vào `catalog_book` (`app_staff` UPDATE thẳng → 1142).

### Giới hạn nghiệp vụ

| Trường | Giới hạn | Kiểm tra ở |
| --- | --- | --- |
| Tên sách, tác giả | 1–255 ký tự, gộp khoảng trắng thừa | Django + thủ tục |
| ISBN | ISBN-10 hoặc ISBN-13; Django bỏ gạch/khoảng trắng, đổi `x` thành `X`, **kiểm tra chữ số kiểm tra** (`INVALID_ISBN`); thủ tục kiểm tra định dạng; UNIQUE chặn trùng | Django + thủ tục + bảng |
| Mô tả | trống thì lưu NULL, tối đa 5.000 ký tự | Django + thủ tục |
| Giá bán / giá nhập | 1–100.000.000 đ / 0–100.000.000 đ | Django + thủ tục + CHECK |
| Tồn kho | 0–10.000 cuốn mỗi đầu sách, mọi lúc | Django + thủ tục + CHECK không âm |
| Ảnh bìa | NULL hoặc `covers/<32 hex>.<jpg|png|webp>`; thủ tục chặn mọi đường dẫn khác (ví dụ `../../etc/passwd`) | thủ tục |

### Nhật ký

`core_auditlog` với `table_name = catalog_book`: thêm sách (mọi giá trị), sửa (giá trị cũ/mới; mô tả chỉ ghi độ dài), ẩn/hiện, nhập kho (`{"stock": cũ}` → `{"stock": mới, "restock": n}`), giảm kho (`"reduce": n`), xóa (giá trị cuối cùng). Đọc liên tiếp các dòng là dựng lại được lịch sử tồn kho.

### Race condition

Nhập kho, giảm kho, xóa và `sp_place_order` đều khóa dòng sách bằng `FOR UPDATE`, nên chạy cùng lúc thì xếp hàng. Đã thử trong sandbox: bốn yêu cầu cùng lúc (nhập 6.000, nhập 6.000, giảm 1, nhập 3.000) trên sách tồn 0 → ba yêu cầu thành công theo thứ tự, yêu cầu nhập 6.000 thứ hai bị `STOCK_LIMIT`, tồn cuối 8.999, nhật ký nối tiếp khớp từng bước. Xóa sách đúng lúc có đơn mới: khóa ngoại `RESTRICT` của `orders_orderitem` chặn → `BOOK_HAS_ORDERS`.

### Xóa sách

Phải ẩn trước (chống bấm nhầm), và chỉ xóa được sách chưa bán. Khi xóa, sách trong **giỏ hàng** và **đánh giá** của khách bị xóa theo (khóa ngoại `CASCADE`; MySQL không kiểm tra quyền của definer trên bảng con khi cascade). Sách đã bán chỉ ẩn, nên lịch sử đơn hàng luôn còn nguyên.

### Đọc và lọc

Một view `v_staff_books`; "theo thể loại", "theo tác giả", "theo tên sách" là ba cách lọc bằng ORM, tham số luôn được truyền riêng:

```python
from catalog.book_services import list_books, get_book

list_books(category_id=4)          # theo thể loại
list_books(author="coelho")        # theo tác giả, không phân biệt hoa/thường và dấu
list_books(title="giả kim")        # theo tên sách
list_books(is_active=False)        # sách đang ẩn
book = get_book(9)                 # cho form sửa; book.cover_url luôn có giá trị
```

Tên thể loại để hiển thị: ghép với `list_categories()`.

### Ghi dữ liệu

```python
from catalog.book_services import (BookError, create_book, delete_book, reduce_book_stock,
                                   restock_book, set_book_active, update_book)

book_id = create_book(request.user, title=..., author=..., isbn=..., category_id=..., description=...,
                      price=..., cost_price=..., stock=...)
update_book(request.user, book_id, title=..., author=..., isbn=..., category_id=..., description=...,
            price=..., cost_price=...)          # giữ nguyên ảnh bìa đang có (thay/bỏ ảnh: mục 5)
set_book_active(request.user, book_id, False)
new_stock = restock_book(request.user, book_id, 50)
new_stock = reduce_book_stock(request.user, book_id, 2)
delete_book(request.user, book_id)
```

Mọi lỗi nghiệp vụ là `BookError` với `code` và `message` tiếng Việt.

### Ảnh bìa

Cột `cover_image` đã có sẵn trong `01_tables.sql`, mỗi sách đúng một ảnh. Sách chưa có ảnh: CSDL để **NULL**, `cover_url` trả ảnh mặc định `settings.BOOK_DEFAULT_COVER` (`frontend/static/img/book-cover-default.webp`). Ảnh mặc định không bao giờ bị xóa khi xóa sách hay thay ảnh. Upload ảnh: xem mục 5.

## 5. Upload ảnh bìa

### Luồng

Ảnh đi **cùng form thêm/sửa sách** (một lần gửi, `enctype="multipart/form-data"`). View truyền `request.FILES["cover"]` vào service:

```python
from catalog.covers import CoverError

create_book(request.user, ..., stock=..., cover_file=request.FILES.get("cover"))           # không có ảnh → NULL → ảnh mặc định
update_book(request.user, book_id, ..., cover_file=request.FILES.get("cover"))              # có file → thay ảnh
update_book(request.user, book_id, ..., remove_cover=True)                                  # bỏ ảnh → về ảnh mặc định
# Lỗi ảnh: CoverError (code, message); lỗi nghiệp vụ: BookError
```

Không có hàm nào nhận đường dẫn ảnh từ bên ngoài: đường dẫn chỉ do `save_cover` tạo ra.

### Các lớp kiểm tra (`catalog/covers.py`)

| # | Kiểm tra | Chặn được |
| --- | --- | --- |
| 1 | Đọc tối đa 2 MB + 1 byte, **không tin** `size` client gửi (`COVER_TOO_LARGE`). Django giữ file ≤ 2,5 MB trong RAM (`FILE_UPLOAD_MAX_MEMORY_SIZE`); production thêm `client_max_body_size` của Nginx | Làm đầy ổ đĩa, tốn RAM |
| 2 | **Bỏ qua tên file và Content-Type** của client; Pillow đọc nội dung thật, chỉ nhận `JPEG`, `PNG`, `WEBP` (`COVER_INVALID`) | `shell.php` đổi tên `.jpg`, SVG có script, GIF/BMP |
| 3 | Đọc kích thước từ header **trước khi giải nén**: mỗi cạnh ≤ 6000, tổng ≤ 25 triệu điểm ảnh (`COVER_DIMENSIONS`); cảnh báo `DecompressionBombWarning` của Pillow bị coi là lỗi | Ảnh "bom giải nén" (file nhỏ, giải nén ra hàng GB RAM) |
| 4 | `verify()` rồi mở lại và giải mã toàn bộ | File hỏng, file cắt cụt |
| 5 | **Vẽ lại thành ảnh mới**: xoay theo EXIF, nền trắng cho ảnh trong suốt, thu về tối đa 1200×1800, lưu **WebP** chất lượng 85 | Mã độc nối đuôi ảnh (polyglot `ảnh + <?php ... ?>`), **EXIF/GPS** lộ vị trí người chụp |
| 6 | Tên file `covers/<uuid4 hex>.webp`, mở bằng chế độ `xb` (không ghi đè), quyền `0644` | Path traversal qua tên file, ghi đè file khác, file thực thi được |
| 7 | Thủ tục chỉ nhận đường dẫn đúng mẫu `covers/<32 hex>.<jpg|png|webp>` | Ghi đường dẫn tùy ý vào CSDL |
| 8 | `delete_cover` chỉ xóa file đúng mẫu **và** nằm thẳng trong `MEDIA_ROOT/covers` (so sau khi `resolve()`) | Dữ liệu CSDL bị sửa thành `../../.env` để lừa xóa file |

### Thứ tự với CSDL (không để file mồ côi, không mất ảnh)

- **Thêm:** lưu file → gọi thủ tục; thủ tục lỗi (ví dụ trùng ISBN) → xóa file vừa lưu.
- **Sửa có ảnh mới:** lưu file mới → gọi thủ tục; lỗi → xóa file **mới**, giữ file cũ; thành công → xóa file **cũ**.
- **Bỏ ảnh:** thủ tục ghi NULL → xóa file cũ.
- **Xóa sách:** thủ tục xóa xong → xóa file. Thủ tục từ chối (`BOOK_HAS_ORDERS`...) → giữ file.
- Ảnh mặc định nằm ở `frontend/static`, không bao giờ nằm trong `media/covers`, nên không thể bị xóa.

Giới hạn đã biết: nếu tiến trình chết giữa lúc lưu file và gọi thủ tục, có thể còn file không ai dùng trong `media/covers` (vô hại, không ai truy cập được qua CSDL).

### Phục vụ file ảnh

- **Dev** (`DEBUG = True`): `bookstore/urls.py` tự phục vụ `/media/`. Đã thử: ảnh trả `200 image/webp`; `/media/../.env` trả 404.
- **Production (Nginx):** Django không phục vụ `/media/`. Cấu hình gợi ý:

```nginx
client_max_body_size 3m;

location /media/covers/ {
    alias /srv/secure-bookstore/media/covers/;
    location ~* \.webp$ {
        default_type image/webp;
        add_header X-Content-Type-Options nosniff always;
        add_header Content-Security-Policy "default-src 'none'" always;
    }
    location ~ { return 404; }       # chỉ file .webp, không gì khác
}
location /media/ { return 404; }
```

Thư mục `media/` đã có trong `.gitignore`, không commit ảnh người dùng.

### Kiểm thử

`catalog/tests/test_covers.py` (23 test): ảnh thật 3 định dạng, ảnh trong suốt, thu nhỏ, xóa EXIF/GPS, mã PHP/JS nối đuôi bị loại, file giả/SVG/GIF/BMP/cắt cụt/rỗng, quá 2 MB (kể cả khi `size` nói dối), ảnh bom 8000×8000, tên UUID và quyền 0644, `delete_cover` không xóa được file ngoài `covers/`, và thứ tự file ↔ CSDL khi thêm/sửa/bỏ/xóa thành công hoặc lỗi.
