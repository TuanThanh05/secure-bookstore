# AI_TRACE – code do AI viết

File tạm, sinh bằng `python scripts/ai_trace.py`. Không sửa tay các cột Model, File, Class / Hàm, Dòng, Làm gì. Chỉ điền tay cột **Người dùng** và **Đã duyệt** (`[x]`). Quy định: `docs/ai-trace.md`.

| ID | Model | Người dùng | File | Class / Hàm | Dòng | Làm gì | Đã duyệt |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 001 | Claude Opus 5.5 | TuanThanh | `database/objects/30_sp_place_order.sql` | `PROCEDURE sp_place_order` | 43 | Thủ tục đặt đơn: khóa giỏ và sách, kiểm tra kho, tạo đơn, trừ kho | [ ] |
| 002 | Claude Opus 5.5 | TuanThanh | `backend/orders/services.py` | `OrderError` | 16 | Lỗi nghiệp vụ khi đặt đơn, mang mã lỗi và câu tiếng Việt | [ ] |
| 003 | Claude Opus 5.5 | TuanThanh | `backend/orders/services.py` | `PlaceOrderResult` | 24 | Kết quả đặt đơn gồm mã đơn và cờ đơn mới | [ ] |
| 004 | Claude Opus 5.5 | TuanThanh | `backend/orders/services.py` | `new_idempotency_key` | 30 | Sinh mã yêu cầu chống bấm đặt hàng hai lần | [ ] |
| 005 | Claude Opus 5.5 | TuanThanh | `backend/orders/services.py` | `place_order` | 35 | Gọi thủ tục sp_place_order và đổi lỗi SIGNAL thành OrderError | [ ] |
| 006 | Claude Opus 5.5 | TuanThanh | `backend/orders/services.py` | `_signal_code` | 55 | Đọc mã lỗi nghiệp vụ từ lỗi MySQL 1644 do SIGNAL | [ ] |
| 007 | Claude Opus 5.5 | TuanThanh | `backend/orders/tests/test_place_order.py` | `PlaceOrderTests` | 14 | Test place_order bằng cursor giả, không cần thủ tục thật | [ ] |
| 008 | Claude Opus 5.5 |  | `backend/accounts/tokens.py` | `EmailTokenResult` | 9 | Kết quả đọc mã xác nhận email gồm trạng thái và dữ liệu | [ ] |
| 009 | Claude Opus 5.5 |  | `backend/accounts/tokens.py` | `make_email_token` | 16 | Tạo mã xác nhận email ký bằng SECRET_KEY kèm salt riêng | [ ] |
| 010 | Claude Opus 5.5 |  | `backend/accounts/tokens.py` | `read_email_token` | 21 | Kiểm tra chữ ký và hạn dùng của mã xác nhận email | [ ] |
| 011 | Claude Opus 5.5 |  | `backend/accounts/tests/test_email_token.py` | `EmailTokenTests` | 12 | Test tạo và kiểm tra mã xác nhận email: hợp lệ, hết hạn, bị sửa | [ ] |
| 012 | Claude Opus 5.5 |  | `backend/accounts/forms.py` | `RegisterForm.clean_email` | 15 | Chuẩn hóa email đăng ký về dạng chữ thường, bỏ khoảng trắng | [ ] |
| 013 | Claude Opus 5.5 |  | `backend/accounts/forms.py` | `RegisterForm.validate_unique` | 19 | Bỏ kiểm tra trùng email để không lộ email nào đã có tài khoản | [ ] |
| 014 | Claude Opus 5.5 |  | `backend/accounts/forms.py` | `LoginForm.confirm_login_allowed` | 55 | Chặn khách chưa xác nhận email đăng nhập, nhân viên được miễn | [ ] |
| 015 | Claude Opus 5.5 |  | `backend/accounts/forms.py` | `ResendVerificationForm` | 63 | Form gửi lại thư xác nhận, chỉ nhận một ô email | [ ] |
| 016 | Claude Opus 5.5 |  | `backend/accounts/emails.py` | `_allow_send` | 15 | Giới hạn mỗi địa chỉ email chỉ nhận một thư trong một khoảng thời gian | [ ] |
| 017 | Claude Opus 5.5 |  | `backend/accounts/emails.py` | `_send` | 21 | Gửi một thư văn bản thuần, lỗi SMTP chỉ ghi log không lộ ra ngoài | [ ] |
| 018 | Claude Opus 5.5 |  | `backend/accounts/emails.py` | `send_verification_email` | 36 | Gửi thư chứa link xác nhận email có hạn dùng | [ ] |
| 019 | Claude Opus 5.5 |  | `backend/accounts/emails.py` | `send_existing_account_email` | 44 | Báo cho chủ email biết có người dùng email này để đăng ký lại | [ ] |
| 020 | Claude Opus 5.5 |  | `backend/accounts/services.py` | `register_account` | 11 | Đăng ký: email mới thì tạo tài khoản, email đã có thì xử lý y hệt bề ngoài | [ ] |
| 021 | Claude Opus 5.5 |  | `backend/accounts/services.py` | `find_pending_user` | 35 | Tìm tài khoản ứng với mã xác nhận, chỉ khi còn chờ xác nhận | [ ] |
| 022 | Claude Opus 5.5 |  | `backend/accounts/services.py` | `mark_email_verified` | 50 | Đánh dấu email đã xác nhận, chỉ cập nhật đúng một cột | [ ] |
| 023 | Claude Opus 5.5 |  | `backend/accounts/services.py` | `resend_verification` | 57 | Gửi lại thư xác nhận nếu tài khoản tồn tại và chưa xác nhận | [ ] |
| 024 | Claude Opus 5.5 |  | `backend/accounts/views.py` | `check_email` | 35 | Trang báo kiểm tra hộp thư, giống nhau cho mọi trường hợp | [ ] |
| 025 | Claude Opus 5.5 |  | `backend/accounts/views.py` | `verify_email` | 41 | Xác nhận email: GET chỉ hiện nút, POST có CSRF mới kích hoạt | [ ] |
| 026 | Claude Opus 5.5 |  | `backend/accounts/views.py` | `resend_verification_view` | 56 | Gửi lại thư xác nhận, trả lời giống nhau dù email có tồn tại hay không | [ ] |
| 027 | Claude Opus 5.5 |  | `frontend/templates/account/check_email.html` | `<h1 class="auth__title">Kiểm tra hộp thư</h1>` | 7 | Trang kiểm tra hộp thư dùng chung cho đăng ký và gửi lại thư | [ ] |
| 028 | Claude Opus 5.5 |  | `frontend/templates/account/verify_email.html` | `<h1 class="auth__title">Xác nhận email</h1>` | 7 | Trang xác nhận email có nút gửi form POST, báo lỗi khi link hỏng | [ ] |
| 029 | Claude Opus 5.5 |  | `frontend/templates/account/resend_verification.html` | `<h1 class="auth__title">Gửi lại thư xác nhận</h1>` | 7 | Form nhập email để gửi lại thư xác nhận | [ ] |
| 030 | Claude Opus 5.5 |  | `frontend/static/css/account.css` | `.auth__notice` | 197 | Khung thông báo trên các trang xác nhận email | [ ] |
| 031 | Claude Opus 5.5 |  | `backend/accounts/tests/test_email_verification.py` | `EmailVerificationTests` | 19 | Test luồng xác nhận email: đăng ký, xác nhận, gửi lại, chặn đăng nhập | [ ] |
| 032 | Claude Opus 5.5 |  | `database/schema/02_securityevent_email_events.sql` | `ALTER TABLE core_securityevent DROP CHECK ck_secevent_type;` | 10 | Mở rộng danh sách loại sự kiện bảo mật cho xác nhận email | [ ] |
| 033 | Claude Opus 5.5 |  | `backend/core/mail_backends.py` | `ReadableConsoleEmailBackend` | 4 | In thư ra terminal dạng chữ đọc được thay vì base64 khi chạy máy dev | [ ] |
