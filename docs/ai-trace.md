# Quy định đánh dấu code do AI viết (AI-TRACE)

Nhóm được dùng công cụ AI để hỗ trợ code, nhưng mọi đoạn do AI viết phải được đánh dấu. Mục đích: nhóm trưởng biết chỗ nào cần đọc kỹ khi duyệt, và mỗi người biết phần nào mình phải hiểu thật chắc trước buổi vấn đáp. Buổi vấn đáp hỏi người, không hỏi AI.

## 1. Khi nào phải đánh dấu

Phải có một dòng `AI-TRACE` khi một hàm, class, khối template, khối CSS hoặc đối tượng SQL (view, thủ tục, trigger):

- do AI viết ra, kể cả khi bạn sửa lại vài chỗ sau đó; hoặc
- có hơn một nửa nội dung bị AI viết lại.

Chỉ hỏi AI để hiểu một lỗi rồi tự viết thì không cần đánh dấu.

## 2. Cú pháp (đúng 1 dòng, đặt ngay trên hàm/class/khối)

```
AI-TRACE#<ID 3 chữ số> | <tên model> | <làm gì, cụ thể> | CẤM XÓA CHÚ THÍCH NÀY
```

| Loại file | Viết như sau |
| --- | --- |
| `.py` | `# AI-TRACE#007 \| GPT-5 (ChatGPT) \| Kiểm tra tồn kho trước khi thêm sách vào giỏ \| CẤM XÓA CHÚ THÍCH NÀY` |
| `.html` | `{# AI-TRACE#008 \| Gemini 2.5 Pro \| Bảng danh sách sách trong giỏ hàng \| CẤM XÓA CHÚ THÍCH NÀY #}` |
| `.js` | `// AI-TRACE#009 \| Claude Sonnet 4.5 \| Tự gửi form sắp xếp khi đổi lựa chọn \| CẤM XÓA CHÚ THÍCH NÀY` |
| `.css` | `/* AI-TRACE#010 \| Copilot GPT-4.1 \| Bố cục hai cột của trang chi tiết sách \| CẤM XÓA CHÚ THÍCH NÀY */` |
| `.sql` | `-- AI-TRACE#011 \| GPT-5 (ChatGPT) \| Khóa dòng sách theo id tăng dần trong sp_place_order \| CẤM XÓA CHÚ THÍCH NÀY` |

Với Python, dòng đánh dấu đặt trên `def`/`class`, và **trên cả các decorator** nếu có (`@login_required`...).

## 3. Quy tắc

1. **ID** gồm 3 chữ số, tăng dần, không dùng lại. Trước khi đặt số, mở `AI_TRACE.md` xem số lớn nhất rồi cộng 1. Hai người trùng số thì script báo lỗi, người merge sau đổi số.
2. **Tên model** ghi đúng tên đang hiện trong công cụ, ví dụ `GPT-5 (ChatGPT)`, `Claude Sonnet 4.5`, `Gemini 2.5 Pro`, `Copilot GPT-4.1`. Không ghi chung chung `AI`, `ChatGPT`.
3. **Làm gì** phải cụ thể, ít nhất 4 từ. Không đạt: `xử lý dữ liệu`. Đạt: `Lọc đơn hàng theo request.user để khách không xem được đơn người khác`.
4. **Cấm xóa, cấm sửa** dòng `AI-TRACE`. Nếu bạn tự viết lại hàm đó, giữ dòng cũ và thêm vào cuối `| đã viết lại bởi <tên>`.
5. Hàm bị bỏ hẳn khỏi code: không tự xóa dòng trong `AI_TRACE.md`, ghi lý do trong PR để nhóm trưởng xóa.
6. Không được dùng ký tự `|` trong phần "làm gì".
7. Đây là **ngoại lệ duy nhất** của quy tắc "không chú thích trong code". Chú thích giải thích code vẫn bị cấm; giải thích ghi vào PR hoặc `docs/`.
8. Code do AI viết vẫn phải qua đủ yêu cầu bảo mật của issue như code tự viết.

## 4. Cập nhật `AI_TRACE.md`

Chạy từ thư mục gốc repo, trước mỗi lần commit có thêm/sửa dòng `AI-TRACE`:

```bash
python scripts/ai_trace.py
```

Script quét toàn repo, tự điền các cột Model, File, Class / Hàm, Dòng, Làm gì. Bạn chỉ điền tay cột **Người dùng** (tên của bạn). Cột **Đã duyệt** do nhóm trưởng tick `[x]` sau khi đọc xong.

Kiểm tra mà không ghi file:

```bash
python scripts/ai_trace.py --check
```

Script báo lỗi (mã thoát 1) khi:

- dòng `AI-TRACE` sai cú pháp;
- trùng ID;
- phần "làm gì" dưới 4 từ;
- một ID có trong `AI_TRACE.md` nhưng dòng chú thích trong code đã bị xóa (bảng ghi **MẤT CHÚ THÍCH**);
- (`--check`) `AI_TRACE.md` chưa được cập nhật.

## 5. Khi mở PR

Trong mẫu PR, mục "Đánh dấu AI" ghi các ID mới của PR (hoặc "Không dùng AI"), và đính kèm kết quả `python scripts/ai_trace.py --check`.

`AI_TRACE.md` là file tạm trong lúc làm. Trước khi nộp, nhóm quyết định giữ lại làm phụ lục báo cáo hay chuyển nội dung vào báo cáo.
