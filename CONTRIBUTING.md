# Quy trình làm việc của nhóm

Đọc [`PROJECT_CONTEXT.md`](PROJECT_CONTEXT.md) trước (quyết định đã chốt, checklist bảo mật), rồi dựng máy theo [`README.md`](README.md) và [`database/README.md`](database/README.md).

## Nguyên tắc

- **Không ai đẩy thẳng lên `main`.** Mọi thay đổi đi qua Pull Request (PR), có ít nhất 1 người khác duyệt và CI xanh.
- **Một chức năng = một issue = một nhánh = một PR.** Issue ghi cả yêu cầu chức năng lẫn yêu cầu bảo mật (dùng mẫu "Chức năng").
- **Không commit bí mật:** `.env`, `database/.env.db`, mật khẩu, khóa. Lỡ commit thì báo nhóm trưởng ngay và đổi mật khẩu/khóa đó; xóa commit thôi là không đủ vì ai cũng có thể đã clone.
- Code đụng tới khung (settings, `core`, `base.html`, `layouts/`, `components/`, `database/grants`...) phải qua nhóm trưởng duyệt (`.github/CODEOWNERS` tự gắn).

## Các bước cho mỗi chức năng

```bash
# 1. Lấy main mới nhất
git switch main
git pull

# 2. Tạo nhánh (tên: loại/app-việc, không dấu, gạch ngang)
git switch -c feature/accounts-dang-ky

# 3. Code, commit nhỏ, mỗi commit một ý
git add <file>
git commit -m "feat(accounts): form đăng ký chỉ nhận username, email, mật khẩu"

# 4. Đẩy nhánh lên, mở PR vào main trên GitHub (điền đủ mẫu PR)
git push -u origin feature/accounts-dang-ky
```

5. Người duyệt đọc code, bạn kiểm thử thử lại các tấn công ghi trong PR. Có góp ý thì sửa trên **cùng nhánh**, `git push` lại, PR tự cập nhật.
6. CI xanh + được duyệt → bấm **Squash and merge**, xóa nhánh. Issue tự đóng nếu PR ghi `Closes #<số>`.

Nếu `main` đã đi trước khi bạn còn đang làm: `git switch main && git pull && git switch <nhánh> && git merge main`, sửa xung đột (nếu có), chạy lại thử rồi push.

## Tên nhánh

| Tiền tố | Dùng khi |
| --- | --- |
| `feature/` | Chức năng mới: `feature/orders-dat-don` |
| `fix/` | Sửa lỗi: `fix/catalog-sort-whitelist` |
| `db/` | Chỉ đổi phần CSDL: `db/sp-place-order` |
| `docs/` | Báo cáo, tài liệu: `docs/contract-shop` |
| `test/` | Script kiểm thử bảo mật: `test/race-condition` |

`demo-vulnerable` là nhánh đặc biệt: chỉ tạo khi `main` đã hoàn thiện, cố ý gỡ biện pháp bảo mật để demo, **không bao giờ merge vào `main`**.

## Lời nhắn commit

`<loại>(<app>): <làm gì>`, viết tiếng Việt, ngắn gọn.

| Loại | Ý nghĩa |
| --- | --- |
| `feat` | Thêm chức năng |
| `fix` | Sửa lỗi |
| `security` | Thêm/sửa biện pháp bảo mật |
| `db` | View, thủ tục, trigger, quyền MySQL |
| `test` | Test, script kiểm thử |
| `docs` | Tài liệu |
| `chore` | Cấu hình, thư viện, việc lặt vặt |
| `vuln` | **Chỉ trên nhánh `demo-vulnerable`**: `vuln(6): bỏ FOR UPDATE ở sp_place_order` |

## Sau khi `git pull`

| Thấy thay đổi ở | Chạy (trong `backend/`) |
| --- | --- |
| `requirements.txt` | `pip install -r ../requirements.txt` |
| `*/migrations/*.py`, `database/schema/` | `python manage.py migrate --settings=bookstore.settings.migrate` |
| `database/objects/`, `database/grants/` | `python manage.py db_apply` |
| `.env.example` có biến mới | Thêm biến đó vào `.env` của bạn |

## Frontend – backend làm song song

Hai bên thống nhất trước trong [`docs/contract.md`](docs/contract.md): mỗi trang có URL name, template, biến backend truyền vào, trường form gửi lên. Frontend dựng giao diện với dữ liệu giả theo hợp đồng; backend viết view trả đúng các biến đó.

- **Code do AI viết phải đánh dấu `AI-TRACE`** và cập nhật `AI_TRACE.md` bằng `python scripts/ai_trace.py`. Quy định: `docs/ai-trace.md`.