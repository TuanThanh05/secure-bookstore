# Ghi lại code do AI viết (`docs/AI_TRACE.md`)

Nhóm được dùng AI hỗ trợ viết code, nhưng mọi hàm do AI viết phải được ghi lại để người duyệt biết chỗ nào cần đọc kỹ, và mỗi người biết phần nào phải hiểu chắc trước buổi vấn đáp. Buổi vấn đáp hỏi người, không hỏi AI.

Từ ngày 21/11/2026 không còn dòng `AI-TRACE` trong code, cũng không còn script sinh bảng. Mọi thứ ghi tay trong `docs/AI_TRACE.md`.

## 1. Khi nào phải ghi

Khi một hàm, class, khối template, khối CSS hoặc đối tượng SQL (bảng, view, thủ tục, trigger, Event) do AI viết ra, hoặc có hơn một nửa nội dung do AI viết lại. Chỉ hỏi AI để hiểu lỗi rồi tự viết thì không cần ghi.

## 2. Cách ghi một mục

Thêm vào đúng chỗ trong `docs/AI_TRACE.md`: mục lớn theo thư mục (`backend`, `frontend`, `database`, `deploy`, `.github`), trong đó tiêu đề `###` theo file, các mục theo thứ tự xuất hiện trong file.

```
**hàm `place_order` | backend/orders/services.py | Claude Opus 5.5**  
Đặt đơn: user lấy từ phiên, mã hóa SĐT/địa chỉ, giới hạn tần suất rồi gọi sp_place_order.
```

- Dòng đầu: loại (`hàm`, `class`, `thủ tục`, `trigger`, `bảng`, `khối CSS`, `khối HTML`...) và tên, đường dẫn file, tên model AI đúng như trong công cụ.
- Dòng sau: hàm làm gì, cụ thể. Cần giải thích dài (lý do bảo mật, các bước) thì viết ở đây, không viết khối chú thích nhiều dòng trong code.
- Mục cũ có số `#NNN` (ID của dòng AI-TRACE trước đây). Mục mới không cần số.

## 3. Sửa, viết lại, xóa

- Tự viết lại hàm do AI viết: giữ mục, thêm câu "Đã viết lại bởi <tên> khi <lý do>."
- Hàm bị bỏ hẳn khỏi code: xóa mục trong cùng PR và ghi lý do trong mô tả PR.
- Đổi tên hoặc chuyển hàm sang file khác: sửa dòng đầu của mục cho đúng.

## 4. Trong code

Chỉ dùng chú thích một dòng giải thích ngay dòng code đó. Không viết khối chú thích nhiều dòng, không viết docstring nhiều dòng.

## 5. Mẫu PR

Mục "Đánh dấu AI" liệt kê các hàm do AI viết trong PR (hoặc "Không dùng AI") và tick ô đã ghi mục vào `docs/AI_TRACE.md`.
