# security-tests/

Thư mục của người kiểm thử: script tấn công thử và bằng chứng trước/sau cho báo cáo.

| Nơi | Chứa |
| --- | --- |
| `security-tests/<muc>_<ten>.py` | Script tự động, ví dụ `06_race_condition.py` (50 request đặt đơn song song) |
| `security-tests/payloads/` | Payload dùng lại (XSS, SQLi, file upload độc) |
| `security-tests/evidence/` | Ảnh chụp, log, output: đặt tên `<muc>_<ten>_<truoc|sau>.png` |

Quy tắc:
- Chỉ tấn công máy của nhóm (localhost / máy demo). Không quét hay tấn công hệ thống của người khác.
- Không lưu mật khẩu, token, cookie thật vào file trong repo; ảnh chụp có thông tin nhạy cảm thì che đi.
- Mỗi kịch bản ghi: mục checklist (số ở `PROJECT_CONTEXT.md`), bước làm, kết quả trên nhánh `demo-vulnerable`, kết quả trên `main`.
