# Quản lý kho sách (backend)

Phạm vi đợt này: **thể loại sách**. Sách, tồn kho, ẩn/hiện sách làm ở các bước sau. Chưa có URL, view hay template; frontend làm sau.

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

Chạy 12 câu bằng `app_customer` và `app_staff` thật, so mỗi câu với kết quả mong đợi (được phép, hoặc đúng mã lỗi 1142 / 1143 / 1370 / 1644). Câu ghi luôn có `WHERE 1 = 0` hoặc đầu vào sai nên không đổi dữ liệu. CI chạy lệnh này ngay sau `db_apply` trên MySQL 8.4. Đây cũng là bằng chứng phân quyền tốt để đưa vào báo cáo và demo.

## 3. Vì sao đọc danh sách bằng thủ tục, không bằng view

Ban đầu danh sách là view `v_staff_categories`. Kiểm tra bằng `db_check_grants` trên cả **MySQL 8.0.46 (sandbox) và MySQL 8.4 (máy nhóm)**: view `SQL SECURITY DEFINER` có JOIN hoặc GROUP BY bị từ chối (lỗi 1143/1356) khi phiên người gọi đang bật role, dù definer đủ quyền. Cấp thêm quyền theo cột cho definer cũng không khắc phục được. Chỉ khi tắt role (`SET ROLE NONE`) và cấp quyền thẳng cho user thì đọc được, nhưng như vậy phải bỏ mô hình role của đồ án.

Thủ tục `SQL SECURITY DEFINER` không bị lỗi này, nên danh sách chuyển thành `sp_category_list()`. Về bảo mật hai cách tương đương: người gọi chỉ có EXECUTE, không chạm được bảng.

**Quy ước cho các phần sau** (sách, kho, đơn hàng của admin, `v_public_books` cho khách): dữ liệu đọc cần **nhiều bảng hoặc gộp nhóm** thì dùng **thủ tục đọc**; view chỉ dùng cho truy vấn đơn giản trên **một bảng**. Mỗi đối tượng mới nên thêm một dòng vào `db_check_grants` để CI kiểm tra trên MySQL 8.4 thật.
