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
| 012 | Claude Opus 5.5 |  | `backend/accounts/forms.py` | `RegisterForm.clean_email` | 23 | Chuẩn hóa email đăng ký về dạng chữ thường, bỏ khoảng trắng | [ ] |
| 013 | Claude Opus 5.5 |  | `backend/accounts/forms.py` | `RegisterForm.validate_unique` | 27 | Bỏ kiểm tra trùng email để không lộ email nào đã có tài khoản | [ ] |
| 014 | Claude Opus 5.5 |  | `backend/accounts/forms.py` | `LoginForm.confirm_login_allowed` | 63 | Chặn khách chưa xác nhận email đăng nhập, nhân viên được miễn | [ ] |
| 015 | Claude Opus 5.5 |  | `backend/accounts/forms.py` | `ResendVerificationForm` | 71 | Form gửi lại thư xác nhận, chỉ nhận một ô email | [ ] |
| 016 | Claude Opus 5.5 |  | `backend/accounts/emails.py` | `_allow_send` | 15 | Giới hạn mỗi địa chỉ email chỉ nhận một thư mỗi loại trong một khoảng thời gian | [ ] |
| 017 | Claude Opus 5.5 |  | `backend/accounts/emails.py` | `_send` | 21 | Gửi một thư văn bản thuần, lỗi SMTP chỉ ghi log không lộ ra ngoài | [ ] |
| 018 | Claude Opus 5.5 |  | `backend/accounts/emails.py` | `send_verification_email` | 36 | Gửi thư chứa link xác nhận email có hạn dùng | [ ] |
| 019 | Claude Opus 5.5 |  | `backend/accounts/emails.py` | `send_existing_account_email` | 44 | Báo cho chủ email biết có người dùng email này để đăng ký lại | [ ] |
| 020 | Claude Opus 5.5 |  | `backend/accounts/services.py` | `register_account` | 14 | Đăng ký: email mới thì tạo tài khoản, email đã có thì xử lý y hệt bề ngoài | [ ] |
| 021 | Claude Opus 5.5 |  | `backend/accounts/services.py` | `find_pending_user` | 38 | Tìm tài khoản ứng với mã xác nhận, chỉ khi còn chờ xác nhận | [ ] |
| 022 | Claude Opus 5.5 |  | `backend/accounts/services.py` | `mark_email_verified` | 53 | Đánh dấu email đã xác nhận, chỉ cập nhật đúng một cột | [ ] |
| 023 | Claude Opus 5.5 |  | `backend/accounts/services.py` | `resend_verification` | 60 | Gửi lại thư xác nhận nếu tài khoản tồn tại và chưa xác nhận | [ ] |
| 024 | Claude Opus 5.5 |  | `backend/accounts/views.py` | `check_email` | 60 | Trang báo kiểm tra hộp thư, giống nhau cho mọi trường hợp | [ ] |
| 025 | Claude Opus 5.5 |  | `backend/accounts/views.py` | `verify_email` | 66 | Xác nhận email: GET chỉ hiện nút, POST có CSRF mới kích hoạt | [ ] |
| 026 | Claude Opus 5.5 |  | `backend/accounts/views.py` | `resend_verification_view` | 81 | Gửi lại thư xác nhận, trả lời giống nhau dù email có tồn tại hay không | [ ] |
| 027 | Claude Opus 5.5 |  | `frontend/templates/account/check_email.html` | `<h1 class="auth__title">Kiểm tra hộp thư</h1>` | 7 | Trang kiểm tra hộp thư dùng chung cho đăng ký và gửi lại thư | [ ] |
| 028 | Claude Opus 5.5 |  | `frontend/templates/account/verify_email.html` | `<h1 class="auth__title">Xác nhận email</h1>` | 7 | Trang xác nhận email có nút gửi form POST, báo lỗi khi link hỏng | [ ] |
| 029 | Claude Opus 5.5 |  | `frontend/templates/account/resend_verification.html` | `<h1 class="auth__title">Gửi lại thư xác nhận</h1>` | 7 | Form nhập email để gửi lại thư xác nhận | [ ] |
| 030 | Claude Opus 5.5 |  | `frontend/static/css/account.css` | `.auth__notice` | 197 | Khung thông báo trên các trang xác nhận email | [ ] |
| 031 | Claude Opus 5.5 |  | `backend/accounts/tests/test_email_verification.py` | `EmailVerificationTests` | 19 | Test luồng xác nhận email: đăng ký, xác nhận, gửi lại, chặn đăng nhập | [ ] |
| 032 | Claude Opus 5.5 |  | `database/schema/02_securityevent_email_events.sql` | `ALTER TABLE core_securityevent DROP CHECK ck_secevent_type;` | 10 | Mở rộng danh sách loại sự kiện bảo mật cho xác nhận email | [ ] |
| 033 | Claude Opus 5.5 |  | `backend/core/mail_backends.py` | `ReadableConsoleEmailBackend` | 4 | In thư ra terminal dạng chữ đọc được thay vì base64 khi chạy máy dev | [ ] |
| 034 | Claude Opus 5.5 |  | `backend/accounts/profile.py` | `ProfileView` | 9 | Dữ liệu trang thông tin tài khoản, email và SĐT có thể bị giấu | [ ] |
| 035 | Claude Opus 5.5 |  | `backend/accounts/profile.py` | `build_profile` | 43 | Tạo dữ liệu trang thông tin, chỉ đưa email và SĐT khi được phép | [ ] |
| 036 | Claude Opus 5.5 |  | `backend/accounts/views.py` | `profile` | 150 | Trang thông tin của khách, nhân viên bị chuyển sang trang quản trị | [ ] |
| 037 | Claude Opus 5.5 |  | `backend/dashboard/views.py` | `profile` | 46 | Trang thông tin của nhân viên, mặc định không gửi email và SĐT | [ ] |
| 038 | Claude Opus 5.5 |  | `backend/dashboard/views.py` | `profile_contact` | 54 | Hiện email và SĐT của chính nhân viên sau khi xác thực lại, có ghi log | [ ] |
| 039 | Claude Opus 5.5 |  | `frontend/templates/account/profile.html` | `<header class="area-header">` | 6 | Bảng thông tin tài khoản của khách, hiện đầy đủ email và SĐT | [ ] |
| 040 | Claude Opus 5.5 |  | `frontend/templates/dashboard/profile.html` | `<header class="dash-header">` | 6 | Bảng thông tin nhân viên, email và SĐT ẩn sau nút con mắt cần xác thực lại | [ ] |
| 041 | Claude Opus 5.5 |  | `frontend/static/css/dashboard.css` | `.dash-info` | 49 | Kiểu bảng thông tin tài khoản và ô bị ẩn có nút con mắt | [ ] |
| 042 | Claude Opus 5.5 |  | `database/schema/03_securityevent_sensitive_view.sql` | `ALTER TABLE core_securityevent DROP CHECK ck_secevent_type;` | 7 | Thêm loại sự kiện xem dữ liệu nhạy cảm vào danh sách cho phép | [ ] |
| 043 | Claude Opus 5.5 |  | `backend/core/migrations/0003_securityevent_email_events.py` | `_statements` | 9 | Đọc file SQL mở rộng danh sách sự kiện cho xác nhận email | [ ] |
| 044 | Claude Opus 5.5 |  | `backend/core/migrations/0004_securityevent_sensitive_view.py` | `_statements` | 9 | Đọc file SQL thêm loại sự kiện xem dữ liệu nhạy cảm | [ ] |
| 045 | Claude Opus 5.5 |  | `backend/accounts/tests/test_profile.py` | `CustomerProfileTests` | 11 | Test trang thông tin của khách: hiện email, chặn nhân viên, không lưu cache | [ ] |
| 046 | Claude Opus 5.5 |  | `backend/dashboard/tests/test_profile.py` | `StaffProfileTests` | 15 | Test trang thông tin nhân viên: giấu email, hiện sau xác thực lại, ghi log | [ ] |
| 047 | Claude Opus 5.5 |  | `backend/accounts/emails.py` | `send_password_reset_email` | 54 | Gửi thư chứa link đặt lại mật khẩu có hạn dùng | [ ] |
| 048 | Claude Opus 5.5 |  | `backend/accounts/emails.py` | `send_password_changed_email` | 61 | Báo cho chủ tài khoản biết mật khẩu vừa được đổi | [ ] |
| 049 | Claude Opus 5.5 |  | `backend/accounts/forms.py` | `CustomerPasswordResetForm` | 79 | Form quên mật khẩu chỉ gửi cho khách, dùng thư và giới hạn của nhóm | [ ] |
| 050 | Claude Opus 5.5 |  | `backend/accounts/views.py` | `CustomerPasswordResetView` | 93 | Trang quên mật khẩu: nhập email, ghi log, trả lời giống nhau cho mọi email | [ ] |
| 051 | Claude Opus 5.5 |  | `backend/accounts/views.py` | `password_reset_done` | 105 | Trang báo đã gửi thư đặt lại mật khẩu kèm thời hạn link | [ ] |
| 052 | Claude Opus 5.5 |  | `backend/accounts/views.py` | `CustomerPasswordResetConfirmView` | 112 | Đặt mật khẩu mới từ link: chặn nhân viên, xác nhận email, mở khóa axes, báo thư | [ ] |
| 053 | Claude Opus 5.5 |  | `frontend/templates/account/password_reset.html` | `<h1 class="auth__title">Quên mật khẩu</h1>` | 7 | Form nhập email để nhận link đặt lại mật khẩu | [ ] |
| 054 | Claude Opus 5.5 |  | `frontend/templates/account/password_reset_done.html` | `<h1 class="auth__title">Kiểm tra hộp thư</h1>` | 7 | Trang báo đã gửi link đặt lại mật khẩu, giống nhau cho mọi email | [ ] |
| 055 | Claude Opus 5.5 |  | `frontend/templates/account/password_reset_confirm.html` | `<h1 class="auth__title">Đặt mật khẩu mới</h1>` | 8 | Trang đặt mật khẩu mới từ link, báo lỗi khi link hết hạn hoặc đã dùng | [ ] |
| 056 | Claude Opus 5.5 |  | `backend/accounts/tests/test_password_reset.py` | `PasswordResetTests` | 21 | Test luồng quên mật khẩu: gửi link, đặt lại, link hết hạn, chặn nhân viên | [ ] |
| 057 | Claude Opus 5.5 |  | `backend/accounts/forms.py` | `CustomerPasswordChangeForm` | 97 | Form đổi mật khẩu: mật khẩu hiện tại và hai ô mật khẩu mới | [ ] |
| 058 | Claude Opus 5.5 |  | `backend/accounts/services.py` | `record_password_change_failure` | 72 | Đếm số lần nhập sai mật khẩu hiện tại khi đổi mật khẩu, trả về tổng số lần | [ ] |
| 059 | Claude Opus 5.5 |  | `backend/accounts/services.py` | `clear_password_change_failures` | 83 | Xóa bộ đếm nhập sai sau khi đổi mật khẩu thành công | [ ] |
| 060 | Claude Opus 5.5 |  | `backend/accounts/views.py` | `password_change` | 160 | Đổi mật khẩu cho khách: giữ phiên hiện tại, đăng xuất thiết bị khác, sai nhiều lần thì đăng xuất | [ ] |
| 061 | Claude Opus 5.5 |  | `frontend/templates/account/password_change.html` | `<header class="area-header">` | 7 | Form đổi mật khẩu trong khu vực tài khoản khách, có nút hiện mật khẩu | [ ] |
| 062 | Claude Opus 5.5 |  | `frontend/static/css/account-area.css` | `.area-actions { display: flex; flex-wrap: wrap; gap: var(--s` | 35 | Kiểu nút thao tác và form đổi mật khẩu trong khu vực tài khoản | [ ] |
| 063 | Claude Opus 5.5 |  | `backend/accounts/tests/test_password_change.py` | `PasswordChangeTests` | 15 | Test đổi mật khẩu: mật khẩu cũ, đăng xuất thiết bị khác, sai nhiều lần, chặn nhân viên | [ ] |
| 064 | Claude Opus 5.5 |  | `backend/core/crypto.py` | `DecryptionError` | 15 | Lỗi khi dữ liệu mã hóa bị sửa, sai khóa hoặc sai định dạng | [ ] |
| 065 | Claude Opus 5.5 |  | `backend/core/crypto.py` | `_aead` | 20 | Đọc khóa AES-256 từ settings, báo lỗi cấu hình nếu sai độ dài | [ ] |
| 066 | Claude Opus 5.5 |  | `backend/core/crypto.py` | `encrypt_field` | 31 | Mã hóa AES-GCM một chuỗi, gắn ngữ cảnh để không đem sang dòng khác được | [ ] |
| 067 | Claude Opus 5.5 |  | `backend/core/crypto.py` | `decrypt_field` | 38 | Giải mã AES-GCM, kiểm tra thẻ xác thực và ngữ cảnh trước khi trả về | [ ] |
| 068 | Claude Opus 5.5 |  | `backend/accounts/profile.py` | `phone_context` | 21 | Ngữ cảnh mã hóa SĐT gắn với id người dùng, chống tráo bản mã giữa các dòng | [ ] |
| 069 | Claude Opus 5.5 |  | `backend/accounts/profile.py` | `encrypt_phone` | 26 | Mã hóa SĐT trước khi lưu, chuỗi rỗng thì lưu NULL | [ ] |
| 070 | Claude Opus 5.5 |  | `backend/accounts/profile.py` | `decrypt_phone` | 33 | Giải mã SĐT để hiển thị, lỗi giải mã thì trả câu báo thay vì làm hỏng trang | [ ] |
| 071 | Claude Opus 5.5 |  | `backend/accounts/decorators.py` | `customer_required` | 11 | Chỉ cho khách đã đăng nhập, nhân viên bị chuyển sang trang quản trị | [ ] |
| 072 | Claude Opus 5.5 |  | `backend/accounts/decorators.py` | `customer_recent_auth_required` | 24 | Bắt khách xác thực lại trong vài phút gần đây, chuyển tới trang xác thực riêng của khách | [ ] |
| 073 | Claude Opus 5.5 |  | `backend/accounts/forms.py` | `CustomerReauthForm` | 112 | Form xác thực lại của khách, nhận tên đăng nhập hoặc email và mật khẩu | [ ] |
| 074 | Claude Opus 5.5 |  | `backend/accounts/forms.py` | `ProfileUpdateForm` | 143 | Form cập nhật họ, tên, SĐT của khách; không có ô username hay email | [ ] |
| 075 | Claude Opus 5.5 |  | `backend/accounts/services.py` | `update_profile` | 88 | Lưu họ, tên, SĐT đã mã hóa; chỉ ghi cột thay đổi và log tên cột, không log giá trị | [ ] |
| 076 | Claude Opus 5.5 |  | `backend/accounts/views.py` | `reauth` | 201 | Trang xác thực lại riêng cho khách, có link quên mật khẩu, next chỉ trỏ trong site | [ ] |
| 077 | Claude Opus 5.5 |  | `backend/accounts/views.py` | `profile_update` | 223 | Cập nhật họ, tên, SĐT của khách sau khi xác thực lại | [ ] |
| 078 | Claude Opus 5.5 |  | `database/schema/04_securityevent_profile_updated.sql` | `ALTER TABLE core_securityevent DROP CHECK ck_secevent_type;` | 7 | Thêm loại sự kiện cập nhật hồ sơ vào danh sách cho phép | [ ] |
| 079 | Claude Opus 5.5 |  | `backend/core/migrations/0005_securityevent_profile_updated.py` | `_statements` | 9 | Đọc file SQL thêm loại sự kiện cập nhật hồ sơ | [ ] |
| 080 | Claude Opus 5.5 |  | `frontend/templates/account/reauth.html` | `<header class="area-header">` | 7 | Trang xác thực lại của khách: tên đăng nhập, mật khẩu, nút xác thực và link quên mật khẩu | [ ] |
| 081 | Claude Opus 5.5 |  | `frontend/templates/account/profile_update.html` | `<header class="area-header">` | 6 | Form sửa họ, tên, SĐT; tên đăng nhập và email chỉ hiển thị, không sửa | [ ] |
| 082 | Claude Opus 5.5 |  | `backend/core/tests/test_crypto.py` | `FieldCryptoTests` | 13 | Test mã hóa AES-GCM: giải mã đúng, nonce ngẫu nhiên, chặn sửa dữ liệu, sai khóa, sai ngữ cảnh | [ ] |
| 083 | Claude Opus 5.5 |  | `backend/accounts/tests/test_profile_update.py` | `ProfileUpdateTests` | 17 | Test xác thực lại của khách và cập nhật họ, tên, SĐT mã hóa | [ ] |
