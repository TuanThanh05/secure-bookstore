# AI_TRACE – code do AI viết

File tạm, sinh bằng `python scripts/ai_trace.py`. Không sửa tay các cột Model, File, Class / Hàm, Dòng, Làm gì. Chỉ điền tay cột **Người dùng** và **Đã duyệt** (`[x]`). Quy định: `docs/ai-trace.md`.

| ID | Model | Người dùng | File | Class / Hàm | Dòng | Làm gì | Đã duyệt |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 001 | Claude Opus 5.5 | TuanThanh | `database/objects/30_sp_place_order.sql` | `PROCEDURE sp_place_order` | 54 | Thủ tục đặt đơn: khóa giỏ và sách, kiểm tra kho, tạo đơn, trừ kho | [ ] |
| 002 | Claude Opus 5.5 | TuanThanh | `backend/orders/services.py` | `OrderError` | 50 | Lỗi nghiệp vụ khi đặt đơn, mang mã lỗi và câu tiếng Việt | [ ] |
| 003 | Claude Opus 5.5 | TuanThanh | `backend/orders/services.py` | `PlaceOrderResult` | 58 | Kết quả đặt đơn gồm mã đơn và cờ đơn mới | [ ] |
| 004 | Claude Opus 5.5 | TuanThanh | `backend/orders/services.py` | `new_idempotency_key` | 64 | Sinh mã yêu cầu chống bấm đặt hàng hai lần | [ ] |
| 005 | Claude Opus 5.5 | TuanThanh | `backend/orders/services.py` | `place_order` | 88 | Đặt đơn: user lấy từ phiên, mã hóa SĐT/địa chỉ, giới hạn tần suất rồi gọi sp_place_order và đổi lỗi SIGNAL thành OrderError | [ ] |
| 006 | Claude Opus 5.5 | TuanThanh | `backend/orders/services.py` | `_signal_code` | 119 | Đọc mã lỗi nghiệp vụ từ lỗi MySQL 1644 do SIGNAL | [ ] |
| 007 | Claude Opus 5.5 | TuanThanh | `backend/orders/tests/test_place_order.py` | `PlaceOrderTests` | 17 | Test place_order bằng cursor giả: user lấy từ phiên, SĐT/địa chỉ được mã hóa theo ngữ cảnh đơn, giới hạn tần suất, đổi lỗi SIGNAL | [ ] |
| 008 | Claude Opus 5.5 |  | `backend/accounts/tokens.py` | `EmailTokenResult` | 9 | Kết quả đọc mã xác nhận email gồm trạng thái và dữ liệu | [ ] |
| 009 | Claude Opus 5.5 |  | `backend/accounts/tokens.py` | `make_email_token` | 16 | Tạo mã xác nhận email ký bằng SECRET_KEY kèm salt riêng | [ ] |
| 010 | Claude Opus 5.5 |  | `backend/accounts/tokens.py` | `read_email_token` | 21 | Kiểm tra chữ ký và hạn dùng của mã xác nhận email | [ ] |
| 011 | Claude Opus 5.5 |  | `backend/accounts/tests/test_email_token.py` | `EmailTokenTests` | 12 | Test tạo và kiểm tra mã xác nhận email: hợp lệ, hết hạn, bị sửa | [ ] |
| 012 | Claude Opus 5.5 |  | `backend/accounts/forms.py` | `RegisterForm.clean_email` | 23 | Chuẩn hóa email đăng ký về dạng chữ thường, bỏ khoảng trắng | [ ] |
| 013 | Claude Opus 5.5 |  | `backend/accounts/forms.py` | `RegisterForm.validate_unique` | 27 | Bỏ kiểm tra trùng email để không lộ email nào đã có tài khoản | [ ] |
| 014 | Claude Opus 5.5 |  | `backend/accounts/forms.py` | `LoginForm.confirm_login_allowed` | 63 | Chặn khách chưa xác nhận email đăng nhập, nhân viên được miễn | [ ] |
| 015 | Claude Opus 5.5 |  | `backend/accounts/forms.py` | `ResendVerificationForm` | 71 | Form gửi lại thư xác nhận, chỉ nhận một ô email | [ ] |
| 016 | Claude Opus 5.5 |  | `backend/accounts/emails.py` | `_allow_send` | 16 | Giới hạn mỗi địa chỉ email chỉ nhận một thư mỗi loại trong một khoảng thời gian | [ ] |
| 017 | Claude Opus 5.5 |  | `backend/accounts/emails.py` | `_send` | 22 | Gửi một thư văn bản thuần, lỗi SMTP chỉ ghi log không lộ ra ngoài | [ ] |
| 018 | Claude Opus 5.5 |  | `backend/accounts/emails.py` | `send_verification_email` | 37 | Gửi thư chứa link xác nhận email có hạn dùng | [ ] |
| 019 | Claude Opus 5.5 |  | `backend/accounts/emails.py` | `send_existing_account_email` | 45 | Báo cho chủ email biết có người dùng email này để đăng ký lại | [ ] |
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
| 037 | Claude Opus 5.5 |  | `backend/dashboard/views.py` | `profile` | 31 | Trang thông tin của nhân viên, mặc định không gửi email và SĐT | [ ] |
| 038 | Claude Opus 5.5 |  | `backend/dashboard/views.py` | `profile_contact` | 39 | Hiện email và SĐT của chính nhân viên sau khi xác thực lại, có ghi log | [ ] |
| 039 | Claude Opus 5.5 |  | `frontend/templates/account/profile.html` | `<header class="area-header">` | 6 | Bảng thông tin tài khoản của khách, hiện đầy đủ email và SĐT | [ ] |
| 040 | Claude Opus 5.5 |  | `frontend/templates/dashboard/profile.html` | `<header class="dash-header">` | 6 | Bảng thông tin nhân viên, email và SĐT ẩn sau nút con mắt cần xác thực lại | [ ] |
| 041 | Claude Opus 5.5 |  | `frontend/static/css/dashboard.css` | `.dash-info` | 49 | Kiểu bảng thông tin tài khoản và ô bị ẩn có nút con mắt | [ ] |
| 042 | Claude Opus 5.5 |  | `database/schema/03_securityevent_sensitive_view.sql` | `ALTER TABLE core_securityevent DROP CHECK ck_secevent_type;` | 7 | Thêm loại sự kiện xem dữ liệu nhạy cảm vào danh sách cho phép | [ ] |
| 043 | Claude Opus 5.5 |  | `backend/core/migrations/0003_securityevent_email_events.py` | `_statements` | 9 | Đọc file SQL mở rộng danh sách sự kiện cho xác nhận email | [ ] |
| 044 | Claude Opus 5.5 |  | `backend/core/migrations/0004_securityevent_sensitive_view.py` | `_statements` | 9 | Đọc file SQL thêm loại sự kiện xem dữ liệu nhạy cảm | [ ] |
| 045 | Claude Opus 5.5 |  | `backend/accounts/tests/test_profile.py` | `CustomerProfileTests` | 11 | Test trang thông tin của khách: hiện email, chặn nhân viên, không lưu cache | [ ] |
| 046 | Claude Opus 5.5 |  | `backend/dashboard/tests/test_profile.py` | `StaffProfileTests` | 15 | Test trang thông tin nhân viên: giấu email, hiện sau xác thực lại, ghi log | [ ] |
| 047 | Claude Opus 5.5 |  | `backend/accounts/emails.py` | `send_password_reset_email` | 55 | Gửi thư chứa link đặt lại mật khẩu có hạn dùng | [ ] |
| 048 | Claude Opus 5.5 |  | `backend/accounts/emails.py` | `send_password_changed_email` | 62 | Báo cho chủ tài khoản biết mật khẩu vừa được đổi | [ ] |
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
| 084 | Claude Opus 5.5 |  | `frontend/static/css/account-area.css` | `.area-form--center { margin-left: auto; margin-right: auto; ` | 44 | Căn giữa form xác thực lại và đổi mật khẩu theo chiều ngang vùng nội dung tài khoản | [ ] |
| 085 | Claude Opus 5.5 |  | `database/schema/01_tables.sql` | `TABLE accounts_passwordhistory` | 40 | Bảng lưu 5 mã băm mật khẩu gần nhất của mỗi tài khoản | [ ] |
| 086 | Claude Opus 5.5 |  | `database/objects/11_trg_accounts_password_history.sql` | `CREATE DEFINER = 'bookstore_definer'@'localhost'` | 28 | Trigger lưu mật khẩu đầu tiên của tài khoản mới vào lịch sử | [ ] |
| 087 | Claude Opus 5.5 |  | `database/objects/11_trg_accounts_password_history.sql` | `CREATE DEFINER = 'bookstore_definer'@'localhost'` | 40 | Trigger lưu mật khẩu mới vào lịch sử khi đổi và chỉ giữ 5 dòng mới nhất | [ ] |
| 088 | Claude Opus 5.5 |  | `backend/accounts/models.py` | `PasswordHistory` | 58 | Model chỉ đọc cho bảng lịch sử mã băm mật khẩu do trigger ghi | [ ] |
| 089 | Claude Opus 5.5 |  | `backend/accounts/validators.py` | `PasswordHistoryValidator` | 7 | Chặn mật khẩu mới trùng một trong N mật khẩu gần nhất, tính cả mật khẩu đang dùng | [ ] |
| 090 | Claude Opus 5.5 |  | `backend/accounts/tests/test_password_history.py` | `PasswordHistoryTests` | 18 | Test chặn dùng lại 5 mật khẩu gần nhất, tính cả mật khẩu hiện tại, qua validator và trang đổi mật khẩu | [ ] |
| 091 | Claude Opus 5.5 |  | `backend/accounts/management/commands/doi_mat_khau_admin.py` | `Command` | 19 | Lệnh máy chủ đổi mật khẩu nhân viên: kiểm tra quy tắc mật khẩu, đăng xuất mọi phiên, ghi log, gửi thư báo | [ ] |
| 092 | Claude Opus 5.5 |  | `backend/accounts/emails.py` | `send_staff_password_changed_email` | 73 | Báo cho nhân viên biết mật khẩu vừa được đổi bằng lệnh trên máy chủ, không kèm link | [ ] |
| 093 | Claude Opus 5.5 |  | `backend/accounts/tests/test_admin_password_command.py` | `AdminPasswordCommandTests` | 24 | Test lệnh đổi mật khẩu admin: chỉ nhân viên, quy tắc mật khẩu, đăng xuất phiên, log, thư báo, chặn kết nối web | [ ] |
| 094 | Claude Opus 5.5 |  | `backend/dashboard/forms.py` | `StaffProfileUpdateForm` | 38 | Form sửa họ, tên, SĐT của nhân viên; ô SĐT luôn trống, để trống là giữ số cũ | [ ] |
| 095 | Claude Opus 5.5 |  | `backend/dashboard/services.py` | `update_staff_profile` | 17 | Lưu họ, tên, SĐT của nhân viên bằng kết nối staff, chỉ ghi cột thay đổi, log tên cột | [ ] |
| 096 | Claude Opus 5.5 |  | `backend/dashboard/views.py` | `profile_update` | 54 | Nhân viên sửa họ, tên, SĐT của chính mình sau khi xác thực lại, không hiện SĐT cũ | [ ] |
| 097 | Claude Opus 5.5 |  | `frontend/templates/dashboard/profile_update.html` | `<header class="dash-header">` | 6 | Form sửa họ, tên, SĐT của nhân viên; không hiện email và SĐT hiện tại | [ ] |
| 098 | Claude Opus 5.5 |  | `frontend/static/css/dashboard.css` | `.dash-actions { display: flex; flex-wrap: wrap; gap: var(--s` | 72 | Kiểu form cập nhật thông tin nhân viên và hàng nút thao tác | [ ] |
| 099 | Claude Opus 5.5 |  | `database/objects/10_trg_accounts_user_guard.sql` | `IF SUBSTRING_INDEX(USER(), '@', 1) = 'app_staff' AND OLD.is_` | 84 | Chặn app_staff sửa dòng của khách hàng, trừ cột is_active do thủ tục khóa/mở khóa đổi | [ ] |
| 100 | Claude Opus 5.5 |  | `backend/dashboard/tests/test_profile_update.py` | `StaffProfileUpdateTests` | 19 | Test nhân viên cập nhật họ, tên, SĐT: xác thực lại, không lộ SĐT cũ, để trống giữ số, chặn mass assignment | [ ] |
| 101 | Claude Opus 5.5 |  | `database/objects/40_category.sql` | `PROCEDURE sp_category_list` | 54 | Thủ tục trả danh sách thể loại kèm tổng số sách và số sách đang hiện, chỉ cho nhân viên | [ ] |
| 102 | Claude Opus 5.5 |  | `database/objects/40_category.sql` | `PROCEDURE sp_category_create` | 71 | Thủ tục thêm thể loại: kiểm tra nhân viên và đầu vào, chặn trùng, ghi nhật ký | [ ] |
| 103 | Claude Opus 5.5 |  | `database/objects/40_category.sql` | `PROCEDURE sp_category_rename` | 125 | Thủ tục sửa tên thể loại: khóa dòng, đổi tên và slug, chặn trùng, ghi nhật ký | [ ] |
| 104 | Claude Opus 5.5 |  | `database/objects/40_category.sql` | `PROCEDURE sp_category_delete` | 196 | Thủ tục xóa thể loại: khóa dòng, từ chối nếu còn sách, ghi nhật ký | [ ] |
| 106 | Claude Opus 5.5 |  | `backend/catalog/staff_services.py` | `StaffCategory` | 22 | Một dòng thể loại trả về từ sp_category_list, kèm số sách và cờ xóa được | [ ] |
| 107 | Claude Opus 5.5 |  | `backend/catalog/staff_services.py` | `CategoryError` | 37 | Lỗi nghiệp vụ khi quản lý thể loại, mang mã lỗi và câu tiếng Việt | [ ] |
| 108 | Claude Opus 5.5 |  | `backend/catalog/staff_services.py` | `clean_name` | 45 | Chuẩn hóa tên thể loại: bỏ khoảng trắng thừa, kiểm tra độ dài | [ ] |
| 109 | Claude Opus 5.5 |  | `backend/catalog/staff_services.py` | `make_slug` | 53 | Tạo slug không dấu từ tên tiếng Việt, xử lý riêng chữ đ | [ ] |
| 110 | Claude Opus 5.5 |  | `backend/catalog/staff_services.py` | `_call` | 63 | Gọi một thủ tục qua kết nối staff, đổi lỗi SIGNAL thành exception nghiệp vụ tương ứng | [ ] |
| 111 | Claude Opus 5.5 |  | `backend/catalog/staff_services.py` | `list_categories` | 92 | Danh sách thể loại cho nhân viên, gọi sp_category_list qua kết nối staff | [ ] |
| 112 | Claude Opus 5.5 |  | `backend/catalog/staff_services.py` | `create_category` | 105 | Thêm thể loại bằng sp_category_create, trả id mới | [ ] |
| 113 | Claude Opus 5.5 |  | `backend/catalog/staff_services.py` | `rename_category` | 111 | Sửa tên thể loại bằng sp_category_rename, slug đổi theo tên | [ ] |
| 114 | Claude Opus 5.5 |  | `backend/catalog/staff_services.py` | `delete_category` | 117 | Xóa thể loại bằng sp_category_delete | [ ] |
| 115 | Claude Opus 5.5 |  | `backend/catalog/staff_services.py` | `_category_id` | 84 | Đổi id thể loại nhận từ request thành số nguyên, sai kiểu thì coi như không tìm thấy | [ ] |
| 116 | Claude Opus 5.5 |  | `backend/core/management/commands/db_check_grants.py` | `Command` | 96 | Lệnh kiểm tra phân quyền trên CSDL thật: chạy từng câu bằng app_customer/app_staff, so với kết quả mong đợi | [ ] |
| 117 | Claude Opus 5.5 |  | `backend/catalog/tests/test_staff_categories.py` | `SlugAndNameTests` | 22 | Test tạo slug và chuẩn hóa tên thể loại tiếng Việt | [ ] |
| 118 | Claude Opus 5.5 |  | `backend/catalog/tests/test_staff_categories.py` | `CategoryProcedureTests` | 48 | Test gọi thủ tục thể loại bằng cursor giả qua kết nối staff, đổi lỗi SIGNAL | [ ] |
| 119 | Claude Opus 5.5 |  | `backend/catalog/tests/test_staff_categories.py` | `CategoryListTests` | 101 | Test đọc danh sách thể loại qua sp_category_list và lệnh kiểm tra quyền từ chối settings.migrate | [ ] |
| 120 | Claude Opus 5.5 |  | `database/objects/41_book.sql` | `CREATE DEFINER = 'bookstore_definer'@'localhost'` | 58 | View một bảng cho nhân viên xem mọi cột của sách, kể cả giá nhập và tồn kho | [ ] |
| 121 | Claude Opus 5.5 |  | `database/objects/41_book.sql` | `PROCEDURE sp_book_create` | 68 | Thủ tục thêm sách: kiểm tra nhân viên, đầu vào, thể loại, chặn trùng ISBN, ghi nhật ký | [ ] |
| 122 | Claude Opus 5.5 |  | `database/objects/41_book.sql` | `PROCEDURE sp_book_update` | 156 | Thủ tục sửa thông tin sách (không đụng tồn kho và ẩn/hiện), khóa dòng, ghi giá trị cũ/mới | [ ] |
| 123 | Claude Opus 5.5 |  | `database/objects/41_book.sql` | `PROCEDURE sp_book_set_active` | 256 | Thủ tục ẩn hoặc hiện sách, khóa dòng, ghi nhật ký | [ ] |
| 124 | Claude Opus 5.5 |  | `database/objects/41_book.sql` | `PROCEDURE sp_book_restock` | 310 | Thủ tục nhập thêm hàng: khóa dòng sách, chặn vượt 10.000 cuốn, ghi tồn kho trước và sau | [ ] |
| 125 | Claude Opus 5.5 |  | `database/objects/41_book.sql` | `PROCEDURE sp_book_reduce_stock` | 367 | Thủ tục giảm kho ngoại lệ: khóa dòng sách, không cho âm, ghi tồn kho trước và sau | [ ] |
| 126 | Claude Opus 5.5 |  | `database/objects/41_book.sql` | `PROCEDURE sp_book_delete` | 424 | Thủ tục xóa hẳn sách: khóa dòng, chỉ xóa sách đã ẩn và chưa từng có trong đơn, ghi nhật ký | [ ] |
| 127 | Claude Opus 5.5 |  | `backend/catalog/models.py` | `StaffConnectionManager` | 12 | Manager luôn đọc qua kết nối staff, vì chỉ app_staff có quyền SELECT view của nhân viên | [ ] |
| 128 | Claude Opus 5.5 |  | `backend/catalog/models.py` | `StaffBook` | 18 | Model chỉ đọc view một bảng v_staff_books, trả đường dẫn ảnh bìa hoặc ảnh mặc định | [ ] |
| 129 | Claude Opus 5.5 |  | `backend/catalog/book_services.py` | `BookError` | 27 | Lỗi nghiệp vụ khi quản lý sách, mang mã lỗi và câu tiếng Việt | [ ] |
| 130 | Claude Opus 5.5 |  | `backend/catalog/book_services.py` | `clean_isbn` | 35 | Chuẩn hóa ISBN (bỏ gạch, khoảng trắng) và kiểm tra chữ số kiểm tra ISBN-10/ISBN-13 | [ ] |
| 131 | Claude Opus 5.5 |  | `backend/catalog/book_services.py` | `_int_in_range` | 49 | Đổi giá trị từ form thành số nguyên trong khoảng cho phép, sai thì báo mã lỗi | [ ] |
| 132 | Claude Opus 5.5 |  | `backend/catalog/book_services.py` | `clean_book_fields` | 62 | Chuẩn hóa và kiểm tra các trường thông tin sách trước khi gọi thủ tục | [ ] |
| 133 | Claude Opus 5.5 |  | `backend/catalog/book_services.py` | `_book_id` | 86 | Đổi id sách nhận từ request thành số nguyên, sai kiểu thì coi như không tìm thấy | [ ] |
| 134 | Claude Opus 5.5 |  | `backend/catalog/book_services.py` | `_call_book` | 94 | Gọi thủ tục sách với bảng mã lỗi của sách | [ ] |
| 135 | Claude Opus 5.5 |  | `backend/catalog/book_services.py` | `list_books` | 99 | Danh sách sách cho nhân viên, lọc theo thể loại, tác giả, tên sách, trạng thái bằng ORM | [ ] |
| 136 | Claude Opus 5.5 |  | `backend/catalog/book_services.py` | `get_book` | 116 | Lấy một sách theo id cho form sửa, không có thì báo BOOK_NOT_FOUND | [ ] |
| 137 | Claude Opus 5.5 |  | `backend/catalog/book_services.py` | `create_book` | 124 | Thêm sách bằng sp_book_create kèm tồn kho ban đầu và ảnh bìa tùy chọn; lỗi thì xóa ảnh vừa lưu | [ ] |
| 138 | Claude Opus 5.5 |  | `backend/catalog/book_services.py` | `update_book` | 138 | Sửa thông tin sách bằng sp_book_update: giữ ảnh cũ, thay ảnh mới hoặc bỏ ảnh; chỉ xóa file cũ khi CSDL đã lưu xong | [ ] |
| 139 | Claude Opus 5.5 |  | `backend/catalog/book_services.py` | `set_book_active` | 162 | Ẩn hoặc hiện sách bằng sp_book_set_active | [ ] |
| 140 | Claude Opus 5.5 |  | `backend/catalog/book_services.py` | `restock_book` | 167 | Nhập thêm hàng bằng sp_book_restock, trả tồn kho mới | [ ] |
| 141 | Claude Opus 5.5 |  | `backend/catalog/book_services.py` | `reduce_book_stock` | 173 | Giảm kho ngoại lệ bằng sp_book_reduce_stock, trả tồn kho mới | [ ] |
| 142 | Claude Opus 5.5 |  | `backend/catalog/book_services.py` | `delete_book` | 179 | Xóa hẳn sách bằng sp_book_delete (đang ẩn, chưa có đơn), xong thì xóa file ảnh bìa | [ ] |
| 143 | Claude Opus 5.5 |  | `backend/catalog/tests/test_staff_books.py` | `BookFieldTests` | 34 | Test chuẩn hóa ISBN, kiểm tra chữ số kiểm tra và các giới hạn thông tin sách | [ ] |
| 144 | Claude Opus 5.5 |  | `backend/catalog/tests/test_staff_books.py` | `BookProcedureTests` | 75 | Test gọi sáu thủ tục sách bằng cursor giả qua kết nối staff, đổi lỗi SIGNAL thành BookError | [ ] |
| 145 | Claude Opus 5.5 |  | `backend/catalog/tests/test_staff_books.py` | `StaffBookReadTests` | 165 | Test model sách đọc qua kết nối staff, lọc theo thể loại/tác giả/tên và đường dẫn ảnh bìa | [ ] |
| 146 | Claude Opus 5.5 |  | `backend/catalog/covers.py` | `CoverError` | 26 | Lỗi khi xử lý ảnh bìa upload, mang mã lỗi và câu tiếng Việt | [ ] |
| 147 | Claude Opus 5.5 |  | `backend/catalog/covers.py` | `_read_limited` | 34 | Đọc file upload có giới hạn dung lượng, không tin kích thước client gửi | [ ] |
| 148 | Claude Opus 5.5 |  | `backend/catalog/covers.py` | `sanitize_cover` | 47 | Xác nhận đúng là ảnh JPEG/PNG/WebP thật, chặn ảnh bom giải nén, rồi lưu lại thành WebP sạch metadata | [ ] |
| 149 | Claude Opus 5.5 |  | `backend/catalog/covers.py` | `_cover_file` | 81 | Đường dẫn tuyệt đối của ảnh bìa, chỉ nhận đúng mẫu covers/<uuid>.<đuôi> và phải nằm trong MEDIA_ROOT/covers | [ ] |
| 150 | Claude Opus 5.5 |  | `backend/catalog/covers.py` | `save_cover` | 92 | Kiểm tra và lưu ảnh bìa mới vào MEDIA_ROOT/covers với tên UUID, trả đường dẫn để ghi vào CSDL | [ ] |
| 151 | Claude Opus 5.5 |  | `backend/catalog/covers.py` | `delete_cover` | 104 | Xóa file ảnh bìa đã upload; bỏ qua mọi đường dẫn không đúng mẫu nên không xóa được file khác | [ ] |
| 152 | Claude Opus 5.5 |  | `backend/catalog/tests/test_covers.py` | `SanitizeCoverTests` | 38 | Test kiểm tra ảnh bìa: nhận ảnh thật, chặn file giả, ảnh bom, file quá lớn, xóa metadata và nội dung cài kèm | [ ] |
| 153 | Claude Opus 5.5 |  | `backend/catalog/tests/test_covers.py` | `CoverStorageTests` | 107 | Test lưu và xóa file ảnh bìa: tên UUID trong media/covers, không xóa được file ngoài thư mục | [ ] |
| 154 | Claude Opus 5.5 |  | `backend/catalog/tests/test_covers.py` | `BookCoverFlowTests` | 141 | Test ảnh bìa trong luồng thêm/sửa/xóa sách: dọn file khi CSDL báo lỗi, xóa ảnh cũ khi thay hoặc bỏ | [ ] |
| 155 | Claude Opus 5.5 |  | `backend/dashboard/catalog_forms.py` | `attach_error` | 32 | Gắn lỗi nghiệp vụ từ service vào đúng ô của form, không có ô phù hợp thì thành lỗi chung | [ ] |
| 156 | Claude Opus 5.5 |  | `backend/dashboard/catalog_forms.py` | `BookForm` | 41 | Form thông tin sách dùng chung cho thêm và sửa: kiểm tra độ dài, khoảng giá, ISBN, thể loại, dung lượng ảnh | [ ] |
| 157 | Claude Opus 5.5 |  | `backend/dashboard/catalog_forms.py` | `BookCreateForm` | 83 | Form thêm sách: thêm ô tồn kho ban đầu 0 đến 10.000 | [ ] |
| 158 | Claude Opus 5.5 |  | `backend/dashboard/catalog_forms.py` | `BookEditForm` | 88 | Form sửa sách: thêm ô bỏ ảnh bìa, không cho vừa chọn ảnh mới vừa bỏ ảnh | [ ] |
| 159 | Claude Opus 5.5 |  | `backend/dashboard/catalog_forms.py` | `StockForm` | 99 | Form số lượng nhập kho hoặc giảm kho, 1 đến 10.000 cuốn | [ ] |
| 160 | Claude Opus 5.5 |  | `backend/dashboard/catalog_forms.py` | `CategoryForm` | 104 | Form tên thể loại dùng cho thêm và sửa tên | [ ] |
| 161 | Claude Opus 5.5 |  | `backend/dashboard/catalog_views.py` | `_book_or_404` | 44 | Lấy sách theo id trong URL, không có thì trả 404 | [ ] |
| 162 | Claude Opus 5.5 |  | `backend/dashboard/catalog_views.py` | `books` | 52 | Trang danh sách sách: lọc theo tên, tác giả, thể loại, trạng thái, phân trang, cảnh báo tồn kho thấp | [ ] |
| 163 | Claude Opus 5.5 |  | `backend/dashboard/catalog_views.py` | `book_create` | 83 | Trang thêm sách: form thông tin, tồn kho ban đầu, ảnh bìa; lỗi service gắn vào đúng ô | [ ] |
| 164 | Claude Opus 5.5 |  | `backend/dashboard/catalog_views.py` | `book_edit` | 106 | Trang sửa sách: form thông tin và ảnh, kèm khung tồn kho, trạng thái và nút xóa | [ ] |
| 165 | Claude Opus 5.5 |  | `backend/dashboard/catalog_views.py` | `_change_stock` | 140 | Xử lý chung form nhập kho/giảm kho: kiểm tra số lượng, gọi service, báo kết quả rồi quay lại trang sửa | [ ] |
| 166 | Claude Opus 5.5 |  | `backend/dashboard/catalog_views.py` | `book_restock` | 157 | Nhập thêm hàng cho một sách (POST) | [ ] |
| 167 | Claude Opus 5.5 |  | `backend/dashboard/catalog_views.py` | `book_reduce` | 165 | Giảm kho ngoại lệ cho một sách (POST) | [ ] |
| 168 | Claude Opus 5.5 |  | `backend/dashboard/catalog_views.py` | `book_toggle` | 173 | Ẩn hoặc hiện sách theo trạng thái gửi lên rõ ràng, không đảo trạng thái mù | [ ] |
| 169 | Claude Opus 5.5 |  | `backend/dashboard/catalog_views.py` | `book_delete` | 192 | Xóa hẳn sách: cần xác thực lại, có trang xác nhận, chỉ xóa sách đang ẩn | [ ] |
| 170 | Claude Opus 5.5 |  | `backend/dashboard/catalog_views.py` | `categories` | 213 | Trang thể loại: danh sách kèm số sách, form thêm, form sửa tên từng dòng | [ ] |
| 171 | Claude Opus 5.5 |  | `backend/dashboard/catalog_views.py` | `category_rename` | 232 | Sửa tên thể loại (POST), báo lỗi trùng tên hoặc không tồn tại | [ ] |
| 172 | Claude Opus 5.5 |  | `backend/dashboard/catalog_views.py` | `category_delete` | 250 | Xóa thể loại: cần xác thực lại, có trang xác nhận, chỉ xóa thể loại không còn sách | [ ] |
| 173 | Claude Opus 5.5 |  | `frontend/templates/dashboard/partials/field.html` | `<div class="dash-field{% if field.errors %} has-error{% endi` | 1 | Hiển thị một ô form dashboard: nhãn, ô nhập, gợi ý, lỗi gắn aria-describedby | [ ] |
| 174 | Claude Opus 5.5 |  | `frontend/templates/dashboard/books.html` | `<header class="dash-header dash-header--row">` | 6 | Trang danh sách sách: bộ lọc GET, bảng sách có ảnh, giá nhập, tồn kho, trạng thái, phân trang | [ ] |
| 175 | Claude Opus 5.5 |  | `frontend/templates/dashboard/partials/book_fields.html` | `<div class="dash-grid">` | 1 | Nhóm ô thông tin sách dùng chung cho trang thêm và trang sửa | [ ] |
| 176 | Claude Opus 5.5 |  | `frontend/templates/dashboard/book_create.html` | `<a class="dash-back" href="{% url 'dashboard:books' %}">{% i` | 6 | Trang thêm sách: form multipart gồm thông tin, tồn kho ban đầu và ảnh bìa | [ ] |
| 177 | Claude Opus 5.5 |  | `frontend/templates/dashboard/book_edit.html` | `<a class="dash-back" href="{% url 'dashboard:books' %}">{% i` | 6 | Trang sửa sách: khung thông tin và ảnh, khung tồn kho, khung trạng thái, vùng xóa | [ ] |
| 178 | Claude Opus 5.5 |  | `frontend/templates/dashboard/book_delete.html` | `<section class="dash-confirm" aria-labelledby="xac-nhan">` | 6 | Trang xác nhận xóa sách vĩnh viễn, nêu rõ hậu quả | [ ] |
| 179 | Claude Opus 5.5 |  | `frontend/templates/dashboard/categories.html` | `<header class="dash-header">` | 6 | Trang thể loại: form thêm, bảng thể loại có số sách, sửa tên từng dòng, liên kết xóa khi không còn sách | [ ] |
| 180 | Claude Opus 5.5 |  | `frontend/templates/dashboard/category_delete.html` | `<section class="dash-confirm" aria-labelledby="xac-nhan">` | 6 | Trang xác nhận xóa thể loại không còn sách | [ ] |
| 181 | Claude Opus 5.5 |  | `frontend/static/css/dashboard.css` | `.dash-header--row { display: flex; flex-wrap: wrap; align-it` | 83 | Kiểu trang kho sách: bộ lọc, bảng, nhãn trạng thái, khung, form, ảnh bìa, phân trang, xác nhận xóa | [ ] |
| 182 | Claude Opus 5.5 |  | `backend/dashboard/tests/test_catalog_views.py` | `CatalogViewTestBase` | 45 | Khung test trang kho sách: tài khoản admin, giả lập service, đánh dấu đã xác thực lại | [ ] |
| 183 | Claude Opus 5.5 |  | `backend/dashboard/tests/test_catalog_views.py` | `CatalogAccessTests` | 70 | Test phân quyền trang kho sách: ẩn danh phải đăng nhập, khách bị 403, POST thiếu CSRF bị chặn, GET không đổi dữ liệu | [ ] |
| 184 | Claude Opus 5.5 |  | `backend/dashboard/tests/test_catalog_views.py` | `BookListViewTests` | 120 | Test trang danh sách sách: truyền bộ lọc, bỏ qua giá trị lạ, nhãn tồn kho, escape dữ liệu | [ ] |
| 185 | Claude Opus 5.5 |  | `backend/dashboard/tests/test_catalog_views.py` | `BookFormViewTests` | 152 | Test thêm và sửa sách: gửi dữ liệu sạch, ảnh, gắn lỗi service vào đúng ô, 404 khi không có sách | [ ] |
| 186 | Claude Opus 5.5 |  | `backend/dashboard/tests/test_catalog_views.py` | `BookStockAndStatusTests` | 207 | Test nhập kho, giảm kho, ẩn hiện: chỉ POST, kiểm tra số lượng, trạng thái rõ ràng, báo lỗi service | [ ] |
| 187 | Claude Opus 5.5 |  | `backend/dashboard/tests/test_catalog_views.py` | `DeleteFlowTests` | 239 | Test xóa sách và xóa thể loại: bắt buộc xác thực lại, có trang xác nhận, chặn khi sách đang hiện hoặc thể loại còn sách | [ ] |
| 188 | Claude Opus 5.5 |  | `backend/dashboard/tests/test_catalog_views.py` | `CategoryViewTests` | 287 | Test trang thể loại: thêm, báo trùng tên đúng ô, đổi tên | [ ] |
| 189 | Claude Opus 5.5 |  | `database/objects/20_public_catalog.sql` | `PROCEDURE sp_public_category_list` | 42 | Thủ tục trả thể loại cho bộ lọc của cửa hàng, chỉ id, tên, slug | [ ] |
| 190 | Claude Opus 5.5 |  | `database/objects/20_public_catalog.sql` | `PROCEDURE sp_public_book_list` | 52 | Thủ tục trả sách đang bán cho khách: lọc thể loại, tìm tên/tác giả, điểm đánh giá, không lộ giá nhập và tồn kho | [ ] |
| 191 | Claude Opus 5.5 |  | `backend/catalog/services.py` | `Category` | 11 | Một thể loại hiển thị trên bộ lọc của cửa hàng | [ ] |
| 192 | Claude Opus 5.5 |  | `backend/catalog/services.py` | `BookCard` | 19 | Một thẻ sách cho khách, đúng cột hợp đồng của sp_public_book_list, kèm đường dẫn ảnh bìa hoặc ảnh mặc định | [ ] |
| 193 | Claude Opus 5.5 |  | `backend/catalog/services.py` | `_read` | 43 | Gọi thủ tục đọc của cửa hàng bằng kết nối app_customer, trả mọi dòng của kết quả đầu tiên | [ ] |
| 194 | Claude Opus 5.5 |  | `backend/catalog/services.py` | `list_categories` | 53 | Danh sách thể loại cho bộ lọc, gọi sp_public_category_list | [ ] |
| 195 | Claude Opus 5.5 |  | `backend/catalog/services.py` | `list_public_books` | 68 | Sách đang bán cho khách, lọc thể loại và từ khóa, gọi sp_public_book_list với tham số truyền riêng | [ ] |
| 196 | Claude Opus 5.5 |  | `backend/catalog/tests/test_home.py` | `HomePageTests` | 15 | Test trang chủ: hiển thị sách thật qua service, lọc thể loại, tìm kiếm, đầu vào độc hại, không script inline | [ ] |
| 197 | Claude Opus 5.5 |  | `backend/catalog/tests/test_public_catalog.py` | `PublicCatalogServiceTests` | 14 | Test service danh mục cho khách: gọi đúng thủ tục bằng kết nối app_customer, tham số truyền riêng, đổi dòng thành BookCard | [ ] |
| 198 | Claude Opus 5.5 |  | `database/objects/21_review.sql` | `PROCEDURE sp_review_save` | 41 | Thủ tục gửi hoặc sửa đánh giá: kiểm tra khách hợp lệ, sách đang hiện, điểm và nội dung, không tạo trùng | [ ] |
| 199 | Claude Opus 5.5 |  | `database/objects/21_review.sql` | `PROCEDURE sp_review_get_mine` | 105 | Thủ tục trả đánh giá của chính khách cho một sách để điền sẵn form sửa | [ ] |
| 200 | Claude Opus 5.5 |  | `backend/catalog/review_services.py` | `ReviewError` | 23 | Lỗi nghiệp vụ khi gửi đánh giá, mang mã lỗi và câu tiếng Việt | [ ] |
| 201 | Claude Opus 5.5 |  | `backend/catalog/review_services.py` | `MyReview` | 31 | Đánh giá của chính khách cho một sách, dùng để điền sẵn form sửa | [ ] |
| 202 | Claude Opus 5.5 |  | `backend/catalog/review_services.py` | `clean_content` | 55 | Chuẩn hóa nội dung đánh giá: thống nhất xuống dòng, bỏ ký tự điều khiển và ký tự đảo chiều văn bản, kiểm tra độ dài | [ ] |
| 203 | Claude Opus 5.5 |  | `backend/catalog/review_services.py` | `_int_in_range` | 65 | Đổi điểm và id sách nhận từ request thành số nguyên trong khoảng cho phép | [ ] |
| 204 | Claude Opus 5.5 |  | `backend/catalog/review_services.py` | `mask_username` | 78 | Che username khi hiển thị đánh giá: giữ ký tự đầu và cuối, giữa là dấu sao | [ ] |
| 205 | Claude Opus 5.5 |  | `backend/catalog/review_services.py` | `_allow_review` | 88 | Giới hạn mỗi khách gửi/sửa tối đa REVIEW_RATE_LIMIT đánh giá trong REVIEW_RATE_WINDOW giây | [ ] |
| 206 | Claude Opus 5.5 |  | `backend/catalog/review_services.py` | `save_review` | 102 | Gửi hoặc sửa đánh giá bằng sp_review_save; user lấy từ phiên đăng nhập, có giới hạn tần suất; trả True nếu là đánh giá mới | [ ] |
| 207 | Claude Opus 5.5 |  | `backend/catalog/review_services.py` | `get_my_review` | 131 | Lấy đánh giá của chính khách cho một sách bằng sp_review_get_mine, chưa có thì trả None | [ ] |
| 208 | Claude Opus 5.5 |  | `backend/catalog/forms.py` | `ReviewForm` | 9 | Form đánh giá sách: chọn 1–5 sao và nội dung tối đa 2000 ký tự; không có ô user hay sách | [ ] |
| 209 | Claude Opus 5.5 |  | `backend/catalog/tests/test_reviews.py` | `ReviewInputTests` | 31 | Test chuẩn hóa nội dung đánh giá, che username và form đánh giá | [ ] |
| 210 | Claude Opus 5.5 |  | `backend/catalog/tests/test_reviews.py` | `SaveReviewTests` | 64 | Test gửi đánh giá bằng cursor giả: user lấy từ phiên, chặn nhân viên, giới hạn tần suất, đổi lỗi SIGNAL | [ ] |
| 211 | Claude Opus 5.5 |  | `database/objects/20_public_catalog.sql` | `PROCEDURE sp_public_book_get` | 103 | Thủ tục trả một sách đang bán cho trang chi tiết, kèm tên thể loại và điểm đánh giá; sách ẩn trả rỗng | [ ] |
| 212 | Claude Opus 5.5 |  | `database/objects/21_review.sql` | `PROCEDURE sp_review_list` | 122 | Thủ tục trả đánh giá đang hiện của một sách đang bán, che username ngay trong CSDL, mới nhất trước | [ ] |
| 213 | Claude Opus 5.5 |  | `backend/catalog/services.py` | `_book_from_row` | 58 | Đổi một dòng của thủ tục đọc sách thành BookCard, thêm tên thể loại nếu có | [ ] |
| 214 | Claude Opus 5.5 |  | `backend/catalog/services.py` | `get_public_book` | 75 | Một sách đang bán cho trang chi tiết bằng sp_public_book_get; id sai hoặc sách ẩn trả None | [ ] |
| 215 | Claude Opus 5.5 |  | `backend/catalog/review_services.py` | `PublicReview` | 41 | Một đánh giá hiển thị công khai: tên đã che, số sao, nội dung, thời gian, cờ đã sửa | [ ] |
| 216 | Claude Opus 5.5 |  | `backend/catalog/review_services.py` | `list_reviews` | 149 | Danh sách đánh giá đang hiện của một sách bằng sp_review_list, tên đã được che trong CSDL | [ ] |
| 217 | Claude Opus 5.5 |  | `backend/catalog/views.py` | `_render_detail` | 40 | Dựng trang chi tiết sách: thông tin sách, danh sách đánh giá, form đánh giá theo từng loại người xem | [ ] |
| 218 | Claude Opus 5.5 |  | `backend/catalog/views.py` | `book_detail` | 61 | Trang chi tiết sách cho mọi người xem; sách ẩn hoặc không tồn tại trả 404 | [ ] |
| 219 | Claude Opus 5.5 |  | `backend/catalog/views.py` | `review_submit` | 70 | Nhận form gửi/sửa đánh giá (chỉ POST, CSRF, khách đã đăng nhập); lỗi thì hiện lại form, thành công thì quay về trang sách | [ ] |
| 220 | Claude Opus 5.5 |  | `frontend/templates/shop/book_detail.html` | `<a class="detail-back" href="{% url 'catalog:home' %}">{% in` | 7 | Trang chi tiết sách: ảnh bìa lớn bên trái, thông tin theo hàng bên phải, nút đặt hàng mờ, danh sách và form đánh giá | [ ] |
| 221 | Claude Opus 5.5 |  | `frontend/templates/components/book_card.html` | `<a class="book-card__cover" href="{% url 'catalog:book_detai` | 3 | Ảnh bìa và tên sách trong thẻ sách dẫn tới trang chi tiết | [ ] |
| 222 | Claude Opus 5.5 |  | `frontend/static/css/shop.css` | `.book-card__cover { display: block; }` | 200 | Kiểu trang chi tiết sách: ảnh lớn, thông tin, nút đặt hàng mờ, danh sách và form đánh giá | [ ] |
| 223 | Claude Opus 5.5 |  | `backend/catalog/tests/test_book_detail.py` | `BookDetailViewTests` | 21 | Test trang chi tiết sách và gửi đánh giá: 404 sách ẩn, form theo loại người xem, CSRF, chỉ POST, escape nội dung | [ ] |
| 224 | Claude Opus 5.5 |  | `backend/catalog/tests/test_public_catalog.py` | `PublicBookDetailServiceTests` | 74 | Test lấy một sách cho trang chi tiết: id sai không xuống CSDL, sách ẩn trả None, có tên thể loại | [ ] |
| 225 | Claude Opus 5.5 |  | `frontend/static/css/dashboard.css` | `.dash-field input[type="file"]` | 135 | Kiểu ô chọn ảnh bìa dạng vùng viền đứt có nút viên thuốc và khung xem ảnh bìa hiện tại | [ ] |
| 226 | Claude Opus 5.5 |  | `database/objects/31_cart.sql` | `PROCEDURE sp_cart_add` | 59 | Thủ tục thêm sách vào giỏ: kiểm tra khách, sách còn hàng, cộng dồn tối đa 5 cuốn, tối đa 30 đầu sách, khóa giỏ chống bấm trùng | [ ] |
| 227 | Claude Opus 5.5 |  | `backend/orders/cart_services.py` | `CartError` | 26 | Lỗi nghiệp vụ khi thêm vào giỏ, mang mã lỗi và câu tiếng Việt | [ ] |
| 228 | Claude Opus 5.5 |  | `backend/orders/cart_services.py` | `_int_in_range` | 34 | Đổi id sách và số lượng nhận từ request thành số nguyên trong khoảng cho phép | [ ] |
| 229 | Claude Opus 5.5 |  | `backend/orders/cart_services.py` | `_allow_cart_action` | 47 | Giới hạn tần suất thao tác giỏ hàng theo từng khách: thêm vào giỏ (CART_ADD_RATE_*) và đổi số lượng/gỡ (CART_UPDATE_RATE_*) | [ ] |
| 230 | Claude Opus 5.5 |  | `backend/orders/cart_services.py` | `add_to_cart` | 97 | Thêm sách vào giỏ bằng sp_cart_add; user lấy từ phiên đăng nhập, có giới hạn tần suất; trả số cuốn của sách đó trong giỏ sau khi thêm | [ ] |
| 231 | Claude Opus 5.5 |  | `backend/orders/forms.py` | `CartAddForm` | 10 | Form thêm vào giỏ: chỉ id sách và số lượng 1–5, không có giá hay user | [ ] |
| 232 | Claude Opus 5.5 |  | `backend/orders/views.py` | `_safe_back_url` | 114 | Chỉ quay lại địa chỉ nội bộ an toàn sau khi thêm vào giỏ, chặn open redirect | [ ] |
| 233 | Claude Opus 5.5 |  | `backend/orders/views.py` | `cart_add` | 125 | Nhận form thêm vào giỏ (chỉ POST, CSRF): ẩn danh đi đăng nhập, nhân viên bị từ chối, xong thì ở lại trang đang xem kèm thông báo | [ ] |
| 234 | Claude Opus 5.5 |  | `frontend/templates/shop/book_detail.html` | `{% if book.in_stock and not user.is_staff %}` | 48 | Form thêm vào giỏ cạnh nút đặt hàng: ô số lượng 1–5, khóa khi hết hàng; nút Đặt hàng gửi cùng form rồi chuyển sang giỏ | [ ] |
| 235 | Claude Opus 5.5 |  | `frontend/static/css/shop.css` | `.cart-add { display: flex; align-items: center; gap: var(--s` | 274 | Kiểu form thêm vào giỏ ở trang chi tiết: ô số lượng gọn cạnh nút | [ ] |
| 236 | Claude Opus 5.5 |  | `backend/orders/tests/test_cart_add.py` | `AddToCartServiceTests` | 25 | Test service thêm vào giỏ bằng cursor giả: user lấy từ phiên, số lượng 1–5, chặn nhân viên, giới hạn tần suất, đổi lỗi SIGNAL | [ ] |
| 237 | Claude Opus 5.5 |  | `backend/orders/tests/test_cart_add.py` | `CartAddViewTests` | 99 | Test view thêm vào giỏ: chỉ POST, CSRF, ẩn danh đi đăng nhập, nhân viên bị từ chối, chặn open redirect, ở lại trang đang xem | [ ] |
| 238 | Claude Opus 5.5 |  | `database/objects/31_cart.sql` | `PROCEDURE sp_cart_list` | 144 | Thủ tục đọc giỏ của khách: sách, giá hiện tại, số lượng, tình trạng còn bán/còn hàng, không trả số tồn kho | [ ] |
| 239 | Claude Opus 5.5 |  | `database/objects/31_cart.sql` | `PROCEDURE sp_cart_set_quantity` | 174 | Thủ tục đặt số lượng mới (1–5) cho sách trong giỏ: dùng cho cả tăng và giảm, khóa giỏ chống bấm trùng, sách ẩn không đổi được, hết hàng không tăng được | [ ] |
| 240 | Claude Opus 5.5 |  | `database/objects/31_cart.sql` | `PROCEDURE sp_cart_remove` | 242 | Thủ tục gỡ một sách khỏi giỏ của khách; gỡ được cả sách đã ngừng bán hoặc hết hàng | [ ] |
| 241 | Claude Opus 5.5 |  | `backend/orders/cart_services.py` | `_guard_cart_write` | 60 | Kiểm tra chung trước khi gọi thủ tục giỏ hàng: chỉ khách, không trong transaction.atomic, giới hạn tần suất có ghi log | [ ] |
| 242 | Claude Opus 5.5 |  | `backend/orders/cart_services.py` | `_call_cart_proc` | 71 | Gọi thủ tục giỏ hàng với tham số truyền riêng, đổi lỗi SIGNAL thành CartError; lỗi khác (thiếu quyền...) để nguyên | [ ] |
| 243 | Claude Opus 5.5 |  | `backend/orders/cart_services.py` | `CartLine` | 107 | Một dòng trong giỏ cho template: giá hiện tại, thành tiền, tình trạng và nút nào được bấm (tăng/giảm/gỡ) | [ ] |
| 244 | Claude Opus 5.5 |  | `backend/orders/cart_services.py` | `Cart` | 150 | Cả giỏ hàng: các dòng, tạm tính và số cuốn chỉ tính sách còn bán và còn hàng | [ ] |
| 245 | Claude Opus 5.5 |  | `backend/orders/cart_services.py` | `get_cart` | 168 | Đọc giỏ của khách đang đăng nhập bằng sp_cart_list | [ ] |
| 246 | Claude Opus 5.5 |  | `backend/orders/cart_services.py` | `set_cart_quantity` | 179 | Đặt số lượng mới (1–5) cho sách trong giỏ bằng sp_cart_set_quantity, dùng cho nút tăng và giảm | [ ] |
| 247 | Claude Opus 5.5 |  | `backend/orders/cart_services.py` | `remove_from_cart` | 190 | Gỡ một sách khỏi giỏ bằng sp_cart_remove | [ ] |
| 248 | Claude Opus 5.5 |  | `backend/orders/forms.py` | `CartQuantityForm` | 16 | Form đổi số lượng trong giỏ: id sách và số lượng cuối cùng 1–5 | [ ] |
| 249 | Claude Opus 5.5 |  | `backend/orders/forms.py` | `CartRemoveForm` | 22 | Form gỡ sách khỏi giỏ: chỉ id sách | [ ] |
| 250 | Claude Opus 5.5 |  | `backend/orders/views.py` | `cart` | 23 | Trang giỏ hàng của khách: đọc bằng sp_cart_list, không lưu cache; nhân viên không có giỏ | [ ] |
| 251 | Claude Opus 5.5 |  | `backend/orders/views.py` | `_cart_page_guard` | 39 | Kiểm tra chung cho form trên trang giỏ: ẩn danh đi đăng nhập rồi quay lại giỏ, nhân viên bị từ chối | [ ] |
| 252 | Claude Opus 5.5 |  | `backend/orders/views.py` | `cart_update` | 50 | Nhận nút tăng/giảm trên trang giỏ (chỉ POST, CSRF): gửi số lượng cuối cùng, xong quay về giỏ | [ ] |
| 253 | Claude Opus 5.5 |  | `backend/orders/views.py` | `cart_remove` | 69 | Nhận nút gỡ sách trên trang giỏ (chỉ POST, CSRF), không hỏi xác nhận, xong quay về giỏ | [ ] |
| 254 | Claude Opus 5.5 |  | `frontend/templates/shop/cart.html` | `<div class="cart">` | 11 | Danh sách sách trong giỏ: nút −/+ gửi số lượng cuối cùng, nút Gỡ, sách ngừng bán/hết hàng hiện mờ chỉ gỡ được, tạm tính và nút đặt hàng (khóa khi còn sách không bán được) | [ ] |
| 255 | Claude Opus 5.5 |  | `frontend/static/css/account-area.css` | `.cart { display: grid; grid-template-columns: minmax(0, 1fr)` | 48 | Kiểu trang giỏ hàng: danh sách sách bên trái, ô tạm tính bên phải, sách không bán được hiện mờ, xếp dọc trên màn hình hẹp | [ ] |
| 256 | Claude Opus 5.5 |  | `backend/orders/tests/test_cart_page.py` | `CartDataTests` | 30 | Test dữ liệu giỏ: tạm tính chỉ tính sách còn bán, nút tăng/giảm khóa đúng lúc, nhãn ngừng bán/hết hàng | [ ] |
| 257 | Claude Opus 5.5 |  | `backend/orders/tests/test_cart_page.py` | `CartPageServiceTests` | 53 | Test service trang giỏ bằng cursor giả: user lấy từ phiên, id/số lượng kiểm tra trước khi xuống CSDL, giới hạn tần suất, đổi lỗi SIGNAL | [ ] |
| 258 | Claude Opus 5.5 |  | `backend/orders/tests/test_cart_page.py` | `CartPageViewTests` | 131 | Test view trang giỏ: hiển thị dòng, nút khóa, không cache; form chỉ POST + CSRF, ẩn danh đi đăng nhập, nhân viên bị từ chối, luôn quay về giỏ | [ ] |
| 259 | Claude Opus 5.5 |  | `database/objects/30_sp_place_order.sql` | `SELECT COUNT(*) INTO v_customer` | 108 | sp_place_order tự kiểm tra lại người gọi là khách hợp lệ (đang hoạt động, không phải nhân viên, đã xác nhận email) | [ ] |
| 260 | Claude Opus 5.5 |  | `database/objects/30_sp_place_order.sql` | `SELECT COUNT(*) INTO v_pending_count` | 147 | Chống giữ kho: mỗi khách tối đa 1 đơn chờ thanh toán còn hạn, kiểm tra khi đang giữ khóa giỏ | [ ] |
| 261 | Claude Opus 5.5 |  | `database/objects/30_sp_place_order.sql` | `-- Trả 2 bộ kết quả:` | 213 | Thủ tục đọc một đơn của chính khách theo mã đơn: dòng đầu là đơn, bộ kết quả thứ hai là các sách; đơn của người khác báo như không tồn tại | [ ] |
| 262 | Claude Opus 5.5 |  | `database/objects/32_trg_orders_guard.sql` | `CREATE DEFINER = 'bookstore_definer'@'localhost'` | 41 | Trigger chỉ cho thêm sách vào đơn đang chờ thanh toán lúc tạo đơn: tổng các dòng không vượt subtotal đã chốt, đơn đã thanh toán/giao/hủy bị chặn | [ ] |
| 263 | Claude Opus 5.5 |  | `database/objects/32_trg_orders_guard.sql` | `CREATE DEFINER = 'bookstore_definer'@'localhost'` | 67 | Trigger cấm sửa và xóa chi tiết đơn hàng (giá, số lượng, tên sách) | [ ] |
| 264 | Claude Opus 5.5 |  | `database/objects/32_trg_orders_guard.sql` | `CREATE DEFINER = 'bookstore_definer'@'localhost'` | 84 | Trigger cấm đổi tiền, thông tin giao hàng của đơn; trạng thái chỉ đi tới đúng một bước (đã thanh toán → tiếp nhận → đóng gói → đang giao → đã giao), không quay lại; mốc thanh toán/hủy ghi một lần | [ ] |
| 265 | Claude Opus 5.5 |  | `database/objects/32_trg_orders_guard.sql` | `CREATE DEFINER = 'bookstore_definer'@'localhost'` | 121 | Trigger cấm xóa đơn hàng để giữ lịch sử | [ ] |
| 266 | Claude Opus 5.5 |  | `backend/orders/services.py` | `shipping_context` | 69 | Ngữ cảnh mã hóa SĐT/địa chỉ giao hàng gắn với người đặt và mã chống trùng của đơn, bản mã chép sang đơn khác sẽ không giải mã được | [ ] |
| 267 | Claude Opus 5.5 |  | `backend/orders/services.py` | `_allow_place_order` | 74 | Giới hạn số lần đặt hàng của mỗi khách theo ORDER_PLACE_RATE_* | [ ] |
| 268 | Claude Opus 5.5 |  | `backend/orders/services.py` | `OrderLine` | 127 | Một sách trong đơn: tên và giá chụp lúc đặt | [ ] |
| 269 | Claude Opus 5.5 |  | `backend/orders/services.py` | `Order` | 140 | Đơn hàng cho template: trạng thái, tiền, thông tin giao hàng đã giải mã, hạn thanh toán; không chứa mã chống trùng | [ ] |
| 270 | Claude Opus 5.5 |  | `backend/orders/services.py` | `get_order` | 187 | Đọc một đơn của chính khách bằng sp_order_get; mã đơn sai mẫu bị chặn trước khi xuống CSDL, đơn người khác báo không tìm thấy | [ ] |
| 271 | Claude Opus 5.5 |  | `backend/orders/forms.py` | `CheckoutForm` | 31 | Form thông tin giao hàng: tên người nhận, SĐT Việt Nam, địa chỉ; bỏ ký tự điều khiển/vô hình, gom khoảng trắng | [ ] |
| 272 | Claude Opus 5.5 |  | `backend/orders/views.py` | `_checkout_key` | 168 | Mã chống bấm trùng của lần đặt hàng: sinh ở server, chỉ lưu trong phiên, không nhận từ form | [ ] |
| 273 | Claude Opus 5.5 |  | `backend/orders/views.py` | `checkout` | 182 | Trang đặt hàng: kiểm tra giỏ (không rỗng, không có sách ngừng bán/hết hàng), form giao hàng điền sẵn từ hồ sơ, gọi sp_place_order, xong chuyển tới trang đơn | [ ] |
| 274 | Claude Opus 5.5 |  | `backend/orders/views.py` | `order_detail` | 229 | Trang chi tiết đơn của chính khách theo mã đơn (kèm cờ bật thanh toán mô phỏng); mã sai hoặc đơn người khác đều trả 404 như nhau | [ ] |
| 275 | Claude Opus 5.5 |  | `frontend/templates/shop/checkout.html` | `<header class="area-header">` | 6 | Trang đặt hàng: form giao hàng bên trái, tóm tắt giỏ, phí ship và tổng tiền bên phải; giá chỉ để xem, server tính lại | [ ] |
| 276 | Claude Opus 5.5 |  | `frontend/templates/shop/order_detail.html` | `<header class="area-header">` | 6 | Trang chi tiết đơn: mã đơn, trạng thái, hạn thanh toán, sách và giá lúc đặt, thông tin giao hàng; nút thanh toán (mô phỏng khi bật trong .env), hủy đơn khi còn chờ thanh toán | [ ] |
| 277 | Claude Opus 5.5 |  | `frontend/static/css/account-area.css` | `.checkout { display: grid; grid-template-columns: minmax(0, ` | 91 | Kiểu trang đặt hàng (form + tóm tắt) và trang chi tiết đơn (bảng sách, nhãn trạng thái) | [ ] |
| 278 | Claude Opus 5.5 |  | `backend/orders/tests/test_checkout.py` | `CheckoutFormTests` | 35 | Test form giao hàng: chuẩn hóa SĐT, chặn tên có thẻ HTML/ký tự lạ, địa chỉ quá ngắn, bỏ ký tự vô hình | [ ] |
| 279 | Claude Opus 5.5 |  | `backend/orders/tests/test_checkout.py` | `GetOrderServiceTests` | 61 | Test get_order bằng cursor giả: mã đơn sai mẫu không xuống CSDL, giải mã đúng ngữ cảnh, đơn người khác báo không tìm thấy, hạn thanh toán | [ ] |
| 280 | Claude Opus 5.5 |  | `backend/orders/tests/test_checkout.py` | `CheckoutViewTests` | 114 | Test view đặt hàng và xem đơn: giỏ phải sạch, mã chống trùng chỉ trong phiên, giá/user_id từ form bị bỏ qua, IDOR trả 404, CSRF, nhân viên bị từ chối | [ ] |
| 281 | Claude Opus 5.5 |  | `backend/orders/tests/test_checkout.py` | `BuyNowButtonTests` | 207 | Test nút Đặt hàng ở trang chi tiết sách: thêm vào giỏ rồi chuyển sang giỏ | [ ] |
| 282 | Claude Opus 5.5 |  | `database/objects/33_order_cancel.sql` | `PROCEDURE sp_order_cancel` | 39 | Thủ tục khách tự hủy đơn chờ thanh toán của chính mình: khóa đơn, kiểm tra lại trạng thái, cộng lại kho, đổi sang cancelled trong một giao dịch | [ ] |
| 283 | Claude Opus 5.5 |  | `database/objects/33_order_cancel.sql` | `PROCEDURE sp_order_expire_one` | 97 | Thủ tục nội bộ hủy một đơn quá hạn: khóa đơn, chỉ hủy nếu vẫn pending và đã hết hạn, cộng lại kho; lỗi thì rollback riêng đơn đó | [ ] |
| 284 | Claude Opus 5.5 |  | `database/objects/33_order_cancel.sql` | `PROCEDURE sp_cancel_expired_orders` | 137 | Thủ tục hủy các đơn chờ thanh toán đã quá hạn (tối đa 200 đơn mỗi lần), mỗi đơn một giao dịch, một đơn lỗi không chặn các đơn khác | [ ] |
| 285 | Claude Opus 5.5 |  | `database/objects/33_order_cancel.sql` | `CREATE DEFINER = 'bookstore_definer'@'localhost' EVENT ev_ca` | 173 | MySQL Event mỗi phút gọi sp_cancel_expired_orders để trả kho cho đơn quá hạn thanh toán | [ ] |
| 286 | Claude Opus 5.5 |  | `backend/orders/services.py` | `_allow_cancel_order` | 222 | Giới hạn số lần bấm hủy đơn của mỗi khách theo ORDER_CANCEL_RATE_* | [ ] |
| 287 | Claude Opus 5.5 |  | `backend/orders/services.py` | `cancel_order` | 236 | Khách hủy đơn chờ thanh toán của chính mình bằng sp_order_cancel; mã đơn sai mẫu không xuống CSDL, kho được cộng lại trong thủ tục | [ ] |
| 288 | Claude Opus 5.5 |  | `backend/orders/views.py` | `order_cancel` | 245 | Nhận nút hủy đơn (chỉ POST, CSRF, sau bước xác nhận trên trang đơn): đơn người khác/mã sai trả 404, xong quay về trang đơn | [ ] |
| 289 | Claude Opus 5.5 |  | `frontend/templates/shop/order_detail.html` | `<details class="order__cancel">` | 79 | Hủy đơn hai bước bằng details (không JS): bấm Hủy đơn mới hiện nút xác nhận gửi POST | [ ] |
| 290 | Claude Opus 5.5 |  | `frontend/static/css/account-area.css` | `.order__status--cancelled, .order__status--expired { color: ` | 124 | Kiểu khối hủy đơn hai bước và nhãn trạng thái đã hủy/quá hạn | [ ] |
| 291 | Claude Opus 5.5 |  | `backend/orders/tests/test_order_cancel.py` | `CancelOrderServiceTests` | 28 | Test service hủy đơn bằng cursor giả: mã đơn sai mẫu không xuống CSDL, chặn nhân viên/ẩn danh, giới hạn tần suất, đổi lỗi SIGNAL | [ ] |
| 292 | Claude Opus 5.5 |  | `backend/orders/tests/test_order_cancel.py` | `OrderCancelViewTests` | 99 | Test view hủy đơn: chỉ POST + CSRF, đơn người khác/mã sai trả 404, nhân viên/ẩn danh bị chặn, nút hủy hai bước chỉ hiện khi còn chờ thanh toán | [ ] |
| 293 | Claude Opus 5.5 |  | `database/objects/42_account.sql` | `PROCEDURE sp_staff_account_list` | 44 | Thủ tục admin xem tài khoản khách, lọc theo trạng thái (hoạt động/đã khóa/tạm khóa/chưa xác nhận) và username, SĐT trả bản mã | [ ] |
| 294 | Claude Opus 5.5 |  | `database/objects/42_account.sql` | `PROCEDURE sp_staff_account_get` | 101 | Thủ tục admin xem một tài khoản khách theo id (cùng cột và trạng thái như danh sách), tài khoản nhân viên coi như không có | [ ] |
| 295 | Claude Opus 5.5 |  | `database/objects/42_account.sql` | `PROCEDURE sp_staff_account_lock` | 150 | Thủ tục admin khóa tài khoản khách: kiểm tra lý do, khóa dòng, đặt is_active = 0, ghi core_auditlog kèm lý do cùng giao dịch | [ ] |
| 296 | Claude Opus 5.5 |  | `database/objects/42_account.sql` | `PROCEDURE sp_staff_account_unlock` | 205 | Thủ tục admin mở khóa tài khoản khách: kiểm tra lý do, khóa dòng, đặt is_active = 1, ghi core_auditlog kèm lý do cùng giao dịch | [ ] |
| 297 | Claude Opus 5.5 |  | `backend/dashboard/account_services.py` | `AccountError` | 34 | Lỗi nghiệp vụ khi quản lý tài khoản khách, mang mã lỗi và câu tiếng Việt | [ ] |
| 298 | Claude Opus 5.5 |  | `backend/dashboard/account_services.py` | `mask_email` | 42 | Che bớt email (giữ ký tự đầu, cuối của phần trước @ và tên miền) và SĐT (giữ 3 số đầu, 3 số cuối) | [ ] |
| 299 | Claude Opus 5.5 |  | `backend/dashboard/account_services.py` | `StaffAccount` | 60 | Một tài khoản khách cho trang admin: trạng thái, email/SĐT bản đầy đủ và bản che, ngày tạo, lần đăng nhập cuối | [ ] |
| 300 | Claude Opus 5.5 |  | `backend/dashboard/account_services.py` | `_call` | 126 | Gọi thủ tục quản lý tài khoản qua kết nối staff, đổi lỗi SIGNAL thành AccountError, lỗi khác (thiếu quyền...) để nguyên | [ ] |
| 301 | Claude Opus 5.5 |  | `backend/dashboard/account_services.py` | `list_accounts` | 145 | Danh sách tài khoản khách qua sp_staff_account_list, lọc trạng thái và username (kiểm tra trước khi xuống CSDL) | [ ] |
| 302 | Claude Opus 5.5 |  | `backend/dashboard/account_services.py` | `get_account` | 157 | Một tài khoản khách qua sp_staff_account_get cho trang xác nhận khóa/mở khóa | [ ] |
| 303 | Claude Opus 5.5 |  | `backend/dashboard/account_services.py` | `lock_account` | 173 | Khóa và mở khóa tài khoản khách qua sp_staff_account_lock/unlock, kèm lý do ghi vào nhật ký | [ ] |
| 304 | Claude Opus 5.5 |  | `backend/dashboard/forms.py` | `AccountFilterForm` | 56 | Bộ lọc danh sách tài khoản khách: trạng thái (giá trị cố định) và username (bỏ ký tự điều khiển, tối đa 150 ký tự) | [ ] |
| 305 | Claude Opus 5.5 |  | `backend/dashboard/forms.py` | `AccountActionForm` | 71 | Form khóa/mở khóa: lý do 5–255 ký tự và nhập lại tài khoản + mật khẩu admin, kiểm tra riêng cho đúng lần gửi này (không dùng lại xác thực cũ) | [ ] |
| 306 | Claude Opus 5.5 |  | `backend/dashboard/account_views.py` | `_account_page` | 17 | Dữ liệu chung cho trang danh sách tài khoản: lọc từ GET, gọi thủ tục, phân trang | [ ] |
| 307 | Claude Opus 5.5 |  | `backend/dashboard/account_views.py` | `accounts` | 40 | Trang quản lý tài khoản: danh sách khách, email và SĐT đã che, lọc theo trạng thái và username | [ ] |
| 308 | Claude Opus 5.5 |  | `backend/dashboard/account_views.py` | `accounts_full` | 49 | Xem email và SĐT đầy đủ của khách: cần xác thực lại, ghi log sensitive_data_viewed kèm bộ lọc và số dòng | [ ] |
| 309 | Claude Opus 5.5 |  | `backend/dashboard/account_views.py` | `_account_action` | 71 | Khóa/mở khóa tài khoản: mỗi lần đều nhập lý do và mật khẩu admin ngay trong form (xác thực một lần, không dựa vào xác thực trước đó), ghi log bước xác thực | [ ] |
| 310 | Claude Opus 5.5 |  | `frontend/templates/dashboard/accounts.html` | `<header class="dash-header dash-header--row">` | 6 | Trang quản lý tài khoản: lọc theo trạng thái và username, bảng khách hàng với email/SĐT che bớt (bản đầy đủ cần xác thực lại), nút khóa/mở khóa | [ ] |
| 311 | Claude Opus 5.5 |  | `frontend/templates/dashboard/account_action.html` | `<section class="dash-confirm" aria-labelledby="xac-nhan">` | 6 | Trang xác nhận khóa/mở khóa: thông tin tài khoản (đã che), lý do và nhập lại tài khoản + mật khẩu admin cho riêng lần này | [ ] |
| 312 | Claude Opus 5.5 |  | `frontend/static/css/dashboard.css` | `.dash-note { margin: 0 0 var(--space-md); padding: var(--spa` | 204 | Kiểu trang quản lý tài khoản: ghi chú trạng thái xem dữ liệu nhạy cảm, nút nhỏ trong bảng, form xác nhận một cột | [ ] |
| 313 | Claude Opus 5.5 |  | `backend/dashboard/tests/test_accounts.py` | `MaskingTests` | 32 | Test che email/SĐT và nhãn trạng thái tài khoản | [ ] |
| 314 | Claude Opus 5.5 |  | `backend/dashboard/tests/test_accounts.py` | `AccountServiceTests` | 52 | Test service tài khoản bằng cursor giả: tham số đúng thứ tự, ngưỡng axes từ settings, giải mã SĐT đúng ngữ cảnh, chặn đầu vào sai, đổi lỗi SIGNAL | [ ] |
| 315 | Claude Opus 5.5 |  | `backend/dashboard/tests/test_accounts.py` | `AccountViewTests` | 118 | Test trang quản lý tài khoản: chỉ admin, email/SĐT che mặc định, bản đầy đủ cần xác thực lại và ghi log, khóa/mở khóa luôn đòi nhập mật khẩu dù vừa xác thực, CSRF | [ ] |
| 316 | Claude Opus 5.5 |  | `frontend/static/css/dashboard.css` | `.btn--danger.btn--sm { background: var(--color-primary); bor` | 211 | Nút khóa nhỏ trong bảng tài khoản dùng màu nút chính và căn giữa khung xác nhận trong vùng quản trị | [ ] |
| 317 | Claude Opus 5.5 |  | `frontend/static/css/dashboard.css` | `.dash-confirm:has(> .dash-form)` | 217 | Khung xác nhận khóa tài khoản chia hai cột: thông tin bên trái, form bên phải, về một cột trên màn hình nhỏ | [ ] |
| 318 | Claude Opus 5.5 |  | `database/schema/05_log_indexes.sql` | `ALTER TABLE core_securityevent ADD INDEX ix_secevent_created` | 11 | Thêm chỉ mục created_at cho core_securityevent để xem nhật ký mới nhất và xóa log cũ không phải quét toàn bảng | [ ] |
| 319 | Claude Opus 5.5 |  | `backend/core/migrations/0006_log_indexes.py` | `_statements` | 9 | Đọc file SQL thêm chỉ mục thời gian cho nhật ký bảo mật | [ ] |
| 320 | Claude Opus 5.5 |  | `database/objects/34_trg_orders_audit.sql` | `CREATE DEFINER = 'bookstore_definer'@'localhost'` | 29 | Trigger ghi nhật ký khi tạo đơn: mã đơn, trạng thái, tổng tiền, nguồn gây ra (khách/hệ thống/...) suy từ tài khoản MySQL | [ ] |
| 321 | Claude Opus 5.5 |  | `database/objects/34_trg_orders_audit.sql` | `CREATE DEFINER = 'bookstore_definer'@'localhost'` | 50 | Trigger ghi nhật ký khi đơn đổi trạng thái (chờ → đã thanh toán/đã hủy...), kèm nguồn gây ra và id người làm (khách là chủ đơn, admin lấy từ biến phiên do thủ tục đặt); không đổi trạng thái thì không ghi | [ ] |
| 322 | Claude Opus 5.5 |  | `database/objects/43_logs.sql` | `PROCEDURE sp_staff_security_events` | 29 | Thủ tục admin đọc nhật ký bảo mật: lọc loại, mức độ, khoảng ngày, username/IP; trả tổng số và một trang mới nhất trước | [ ] |
| 323 | Claude Opus 5.5 |  | `database/objects/43_logs.sql` | `PROCEDURE sp_staff_audit_log` | 92 | Thủ tục admin đọc nhật ký thay đổi dữ liệu: lọc bảng, hành động, khoảng ngày, id bản ghi; kèm username người thực hiện | [ ] |
| 324 | Claude Opus 5.5 |  | `database/objects/43_logs.sql` | `PROCEDURE sp_purge_old_logs` | 147 | Thủ tục xóa nhật ký bảo mật và nhật ký thay đổi cũ hơn 1 năm, theo lô 5000 dòng, tối đa 40 lô mỗi lần chạy | [ ] |
| 325 | Claude Opus 5.5 |  | `database/objects/43_logs.sql` | `CREATE DEFINER = 'bookstore_definer'@'localhost' EVENT ev_pu` | 182 | MySQL Event mỗi ngày (03:00 giờ Việt Nam) gọi sp_purge_old_logs để giữ nhật ký tối đa 1 năm | [ ] |
| 326 | Claude Opus 5.5 |  | `backend/core/views.py` | `csrf_failure` | 34 | Trang lỗi CSRF ghi sự kiện csrf_failed (lý do của Django chỉ vào log, không hiện cho người dùng) | [ ] |
| 327 | Claude Opus 5.5 |  | `backend/dashboard/catalog_views.py` | `_log_upload_rejected` | 36 | Ghi sự kiện upload_rejected khi ảnh bìa bị từ chối (chỉ mã lỗi, không ghi tên hay nội dung file) | [ ] |
| 328 | Claude Opus 5.5 |  | `backend/orders/views.py` | `_log_order_probe` | 157 | Ghi idor_attempt khi khách mở/hủy đơn bằng mã đúng định dạng nhưng không phải đơn của mình (hoặc không có); người dùng vẫn chỉ thấy 404 | [ ] |
| 329 | Claude Opus 5.5 |  | `backend/core/middleware.py` | `DbPermissionDeniedMiddleware` | 14 | Middleware ghi db_permission_denied (mức critical) khi MySQL từ chối câu lệnh vì thiếu quyền – dấu hiệu tấn công hoặc lỗi phân quyền; lỗi vẫn đi tiếp thành trang 500 | [ ] |
| 330 | Claude Opus 5.5 |  | `backend/dashboard/log_services.py` | `LogError` | 57 | Lỗi khi đọc nhật ký hệ thống, mang mã lỗi và câu tiếng Việt | [ ] |
| 331 | Claude Opus 5.5 |  | `backend/dashboard/log_services.py` | `SecurityEventRow` | 87 | Một dòng nhật ký bảo mật cho template: nhãn tiếng Việt, mức độ, người dùng, IP, đường dẫn, chi tiết dạng cặp khóa–giá trị | [ ] |
| 332 | Claude Opus 5.5 |  | `backend/dashboard/log_services.py` | `AuditRow` | 120 | Một dòng nhật ký thay đổi dữ liệu: bảng, hành động, danh sách thay đổi cũ → mới, nguồn (khách/hệ thống/quản trị), người thực hiện | [ ] |
| 333 | Claude Opus 5.5 |  | `backend/dashboard/log_services.py` | `_read` | 167 | Gọi thủ tục đọc nhật ký qua kết nối staff: bộ kết quả 1 là tổng số dòng, bộ 2 là trang dữ liệu; đổi lỗi SIGNAL thành LogError | [ ] |
| 334 | Claude Opus 5.5 |  | `backend/dashboard/log_services.py` | `list_security_events` | 189 | Đọc một trang nhật ký bảo mật qua sp_staff_security_events, thời gian lọc đổi về UTC | [ ] |
| 335 | Claude Opus 5.5 |  | `backend/dashboard/log_services.py` | `list_audit_log` | 201 | Đọc một trang nhật ký thay đổi dữ liệu qua sp_staff_audit_log | [ ] |
| 336 | Claude Opus 5.5 |  | `backend/dashboard/forms.py` | `_LogDateRangeForm` | 88 | Phần lọc ngày dùng chung cho hai tab nhật ký: từ ngày/đến ngày theo giờ Việt Nam, đổi thành khoảng [bắt đầu, kết thúc) có múi giờ, tối đa 400 ngày | [ ] |
| 337 | Claude Opus 5.5 |  | `backend/dashboard/forms.py` | `SecurityLogFilterForm` | 111 | Bộ lọc tab nhật ký bảo mật: loại sự kiện, mức độ (danh sách cố định), khoảng ngày, username/IP | [ ] |
| 338 | Claude Opus 5.5 |  | `backend/dashboard/forms.py` | `AuditLogFilterForm` | 127 | Bộ lọc tab nhật ký thay đổi dữ liệu: bảng, hành động (danh sách cố định), khoảng ngày, id bản ghi | [ ] |
| 339 | Claude Opus 5.5 |  | `backend/dashboard/log_views.py` | `_pager` | 14 | Dữ liệu phân trang cho trang nhật ký: dùng Paginator trên tổng số dòng thủ tục trả về, giữ bộ lọc trong link trang | [ ] |
| 340 | Claude Opus 5.5 |  | `backend/dashboard/log_views.py` | `logs` | 34 | Tab nhật ký bảo mật: cần xác thực lại, lọc loại/mức độ/ngày/username-IP, mỗi lần xem ghi log | [ ] |
| 341 | Claude Opus 5.5 |  | `backend/dashboard/log_views.py` | `logs_audit` | 65 | Tab nhật ký thay đổi dữ liệu: cần xác thực lại, lọc bảng/hành động/ngày/id bản ghi, mỗi lần xem ghi log | [ ] |
| 342 | Claude Opus 5.5 |  | `frontend/templates/dashboard/logs.html` | `<header class="dash-header">` | 6 | Trang nhật ký hệ thống: hai tab bảo mật/thay đổi dữ liệu, bộ lọc GET, bảng mới nhất trước, mức độ tô màu, chi tiết mở bằng details, phân trang | [ ] |
| 343 | Claude Opus 5.5 |  | `frontend/static/css/dashboard.css` | `.dash-tabs { display: flex; gap: var(--space-xs); margin-bot` | 234 | Kiểu trang nhật ký hệ thống: tab, dòng cảnh báo/nghiêm trọng tô nền, chữ đơn cách cho IP và đường dẫn, chi tiết và danh sách thay đổi gọn | [ ] |
| 344 | Claude Opus 5.5 |  | `backend/dashboard/tests/test_logs.py` | `LogRowTests` | 39 | Test dữ liệu nhật ký: nhãn tiếng Việt, danh sách thay đổi cũ → mới, nguồn, đọc JSON lỗi không làm hỏng trang | [ ] |
| 345 | Claude Opus 5.5 |  | `backend/dashboard/tests/test_logs.py` | `LogServiceTests` | 66 | Test service đọc nhật ký bằng cursor giả: tham số đúng thứ tự, thời gian đổi về UTC, phân trang có trần, đổi lỗi SIGNAL, lỗi quyền để nguyên | [ ] |
| 346 | Claude Opus 5.5 |  | `backend/dashboard/tests/test_logs.py` | `LogFilterFormTests` | 110 | Test bộ lọc nhật ký: loại/mức độ chỉ nhận giá trị cố định, ngày theo giờ Việt Nam đổi thành khoảng có múi giờ, chặn khoảng ngược và quá 400 ngày | [ ] |
| 347 | Claude Opus 5.5 |  | `backend/dashboard/tests/test_logs.py` | `LogViewTests` | 134 | Test trang nhật ký: chỉ admin, bắt buộc xác thực lại, mỗi lần xem ghi log, lọc chuyển đúng xuống service, bộ lọc sai không gọi CSDL | [ ] |
| 348 | Claude Opus 5.5 |  | `backend/dashboard/tests/test_logs.py` | `NewSecurityEventTests` | 185 | Test 4 log bổ sung: CSRF, MySQL từ chối quyền (middleware), nghi IDOR khi mở đơn người khác, mã đơn rác không ghi | [ ] |
| 349 | Claude Opus 5.5 |  | `database/schema/06_payment_simulated.sql` | `ALTER TABLE payments_payment ALTER COLUMN provider DROP DEFA` | 19 | Cho phép giao dịch thanh toán mô phỏng không có chữ ký, giới hạn tên cổng, mỗi đơn tối đa một giao dịch thành công | [ ] |
| 350 | Claude Opus 5.5 |  | `backend/core/migrations/0007_payment_simulated.py` | `_statements` | 19 | Đọc file SQL cho phép giao dịch thanh toán mô phỏng và chặn một đơn thanh toán hai lần | [ ] |
| 351 | Claude Opus 5.5 |  | `database/objects/35_payment_simulate.sql` | `PROCEDURE sp_payment_simulate` | 42 | Thủ tục thanh toán mô phỏng: khóa đơn của chính khách, kiểm tra lại trạng thái và hạn, ghi giao dịch 'simulated' với số tiền lấy từ đơn rồi đổi đơn sang paid trong một giao dịch | [ ] |
| 352 | Claude Opus 5.5 |  | `database/objects/35_payment_simulate.sql` | `CREATE DEFINER = 'bookstore_definer'@'localhost'` | 120 | Trigger cấm sửa và xóa giao dịch thanh toán đã ghi, kể cả root và definer | [ ] |
| 353 | Claude Opus 5.5 |  | `backend/payments/services.py` | `PaymentError` | 22 | Lỗi nghiệp vụ khi thanh toán, mang mã lỗi và câu tiếng Việt | [ ] |
| 354 | Claude Opus 5.5 |  | `backend/payments/services.py` | `_allow_simulate` | 30 | Giới hạn số lần bấm thanh toán mô phỏng của mỗi khách theo PAYMENT_SIMULATE_RATE_* | [ ] |
| 355 | Claude Opus 5.5 |  | `backend/payments/services.py` | `_signal_code` | 44 | Đọc mã lỗi nghiệp vụ thanh toán từ lỗi MySQL 1644 do SIGNAL | [ ] |
| 356 | Claude Opus 5.5 |  | `backend/payments/services.py` | `simulate_payment` | 57 | Thanh toán mô phỏng: chỉ khi PAYMENT_SIMULATION bật, user lấy từ phiên, mã đơn sai mẫu không xuống CSDL, giới hạn tần suất rồi gọi sp_payment_simulate, trả mã giao dịch | [ ] |
| 357 | Claude Opus 5.5 |  | `backend/payments/views.py` | `simulate` | 12 | Nhận nút thanh toán mô phỏng (chỉ POST, CSRF, sau bước xác nhận trên trang đơn): đơn người khác/mã sai trả 404 và ghi idor_attempt, xong quay về trang đơn | [ ] |
| 358 | Claude Opus 5.5 |  | `frontend/templates/shop/order_detail.html` | `<details class="order__pay">` | 42 | Thanh toán mô phỏng hai bước bằng details (không JS): bấm nút mới hiện số tiền và nút xác nhận gửi POST | [ ] |
| 359 | Claude Opus 5.5 |  | `frontend/static/css/account-area.css` | `.order__pay summary { display: inline-flex; cursor: pointer;` | 133 | Kiểu khối thanh toán mô phỏng hai bước trên trang đơn | [ ] |
| 360 | Claude Opus 5.5 |  | `backend/payments/tests/test_simulate.py` | `SimulatePaymentServiceTests` | 30 | Test service thanh toán mô phỏng bằng cursor giả: tắt cờ thì không xuống CSDL, mã đơn sai mẫu bị chặn, chặn nhân viên/ẩn danh, giới hạn tần suất, đổi lỗi SIGNAL, lấy mã giao dịch từ tham số OUT | [ ] |
| 361 | Claude Opus 5.5 |  | `backend/payments/tests/test_simulate.py` | `SimulateViewTests` | 112 | Test view thanh toán mô phỏng: chỉ POST + CSRF, đơn người khác/mã sai trả 404 và ghi idor_attempt, nhân viên/ẩn danh bị chặn, nút chỉ hiện khi bật cờ và đơn còn chờ thanh toán | [ ] |
| 362 | Claude Opus 5.5 |  | `database/schema/07_order_status_flow.sql` | `ALTER TABLE orders_order DROP CHECK ck_order_status;` | 17 | Thêm trạng thái đơn Đã tiếp nhận (confirmed) và Đã đóng gói (packed), mọi trạng thái sau thanh toán bắt buộc có paid_at | [ ] |
| 363 | Claude Opus 5.5 |  | `backend/core/migrations/0008_order_status_flow.py` | `_statements` | 18 | Đọc file SQL thêm hai trạng thái đơn Đã tiếp nhận và Đã đóng gói | [ ] |
| 364 | Claude Opus 5.5 |  | `database/objects/36_order_list.sql` | `PROCEDURE sp_order_list_mine` | 28 | Thủ tục đọc danh sách đơn của chính khách theo nhóm Đang xử lý / Lịch sử, trả tổng số và một trang (mới nhất trước), không trả thông tin giao hàng | [ ] |
| 365 | Claude Opus 5.5 |  | `backend/orders/services.py` | `OrderSummary` | 261 | Một dòng trong danh sách đơn của khách: mã, trạng thái, tổng tiền, thời gian, số cuốn và tên cuốn đầu; không chứa thông tin giao hàng | [ ] |
| 366 | Claude Opus 5.5 |  | `backend/orders/services.py` | `list_my_orders` | 292 | Đọc một trang đơn của chính khách theo nhóm Đang xử lý/Lịch sử bằng sp_order_list_mine; nhóm sai bị chặn trước khi xuống CSDL, trả tổng số và danh sách | [ ] |
| 367 | Claude Opus 5.5 |  | `backend/orders/views.py` | `order_list` | 95 | Trang Đơn hàng của tôi: hai tab Đang xử lý/Lịch sử đọc bằng sp_order_list_mine, phân trang, không lưu cache; nhân viên không có đơn | [ ] |
| 368 | Claude Opus 5.5 |  | `frontend/templates/account/orders.html` | `<header class="area-header">` | 6 | Trang Đơn hàng của tôi: hai tab, mỗi đơn hiện mã, ngày đặt, sách, số cuốn, tổng tiền, trạng thái và link sang chi tiết; phân trang | [ ] |
| 369 | Claude Opus 5.5 |  | `frontend/static/css/account-area.css` | `.order__status--confirmed, .order__status--packed { color: v` | 140 | Kiểu danh sách Đơn hàng của tôi (thẻ đơn bấm được, phân trang) và nhãn trạng thái Đã tiếp nhận/Đã đóng gói | [ ] |
| 370 | Claude Opus 5.5 |  | `backend/orders/tests/test_order_list.py` | `ListMyOrdersServiceTests` | 33 | Test service danh sách đơn của khách bằng cursor giả: nhóm sai không xuống CSDL, chặn nhân viên/ẩn danh, tính offset theo trang, đọc 2 bộ kết quả, đổi lỗi SIGNAL, nhãn quá hạn | [ ] |
| 371 | Claude Opus 5.5 |  | `backend/orders/tests/test_order_list.py` | `OrderListViewTests` | 94 | Test trang Đơn hàng của tôi: hai tab, tab sai về Đang xử lý, trang sai về 1, link sang chi tiết, trạng thái rỗng, nhân viên/ẩn danh bị chặn, không lưu cache | [ ] |
| 372 | Claude Opus 5.5 |  | `database/objects/44_staff_orders.sql` | `PROCEDURE sp_staff_order_list` | 38 | Thủ tục admin xem danh sách đơn (mã, username, trạng thái, tổng tiền, ngày đặt, số cuốn), lọc theo trạng thái hoặc nhóm Cần xử lý, trả tổng số và một trang; không trả thông tin giao hàng | [ ] |
| 373 | Claude Opus 5.5 |  | `database/objects/44_staff_orders.sql` | `PROCEDURE sp_staff_order_get` | 82 | Thủ tục admin đọc chi tiết một đơn: thông tin đơn, người đặt, SĐT/địa chỉ giao hàng bản mã (Django giải mã), giao dịch thanh toán thành công và danh sách sách | [ ] |
| 374 | Claude Opus 5.5 |  | `database/objects/44_staff_orders.sql` | `PROCEDURE sp_staff_order_advance` | 128 | Thủ tục nội bộ chuyển đơn đúng một bước: kiểm tra nhân viên, khóa dòng đơn, chỉ nhận đúng trạng thái trước, đặt id người bấm cho trigger nhật ký | [ ] |
| 375 | Claude Opus 5.5 |  | `database/objects/44_staff_orders.sql` | `PROCEDURE sp_staff_order_confirm` | 188 | Bốn thủ tục admin chuyển trạng thái đơn theo đúng luồng: tiếp nhận, đóng gói, giao hàng, đã giao; mỗi thủ tục cố định trạng thái trước và sau | [ ] |
| 376 | Claude Opus 5.5 |  | `backend/dashboard/order_services.py` | `OrderAdminError` | 45 | Lỗi nghiệp vụ khi admin quản lý đơn hàng, mang mã lỗi và câu tiếng Việt | [ ] |
| 377 | Claude Opus 5.5 |  | `backend/dashboard/order_services.py` | `StaffOrderRow` | 78 | Một dòng đơn trên trang quản lý đơn: mã, username, trạng thái, tổng tiền, ngày đặt, số cuốn và bước tiếp theo admin được bấm | [ ] |
| 378 | Claude Opus 5.5 |  | `backend/dashboard/order_services.py` | `StaffOrderDetail` | 91 | Chi tiết một đơn cho admin: người đặt, tiền, thông tin giao hàng đã giải mã, giao dịch thanh toán, danh sách sách | [ ] |
| 379 | Claude Opus 5.5 |  | `backend/dashboard/order_services.py` | `list_orders` | 132 | Đọc một trang đơn qua sp_staff_order_list (kết nối staff), bộ lọc sai bị chặn trước khi xuống CSDL, trả tổng số và danh sách | [ ] |
| 380 | Claude Opus 5.5 |  | `backend/dashboard/order_services.py` | `get_order` | 160 | Đọc chi tiết một đơn qua sp_staff_order_get, giải mã SĐT/địa chỉ giao hàng bằng ngữ cảnh gắn chủ đơn; mã đơn sai mẫu không xuống CSDL | [ ] |
| 381 | Claude Opus 5.5 |  | `backend/dashboard/order_services.py` | `advance_order` | 191 | Chuyển đơn đúng một bước bằng thủ tục riêng của từng bước (tiếp nhận/đóng gói/giao hàng/đã giao); tên bước và mã đơn kiểm tra trước khi xuống CSDL | [ ] |
| 382 | Claude Opus 5.5 |  | `backend/dashboard/forms.py` | `OrderFilterForm` | 140 | Bộ lọc trang quản lý đơn: chỉ chọn trong danh sách trạng thái cố định (hoặc Cần xử lý) | [ ] |
| 383 | Claude Opus 5.5 |  | `backend/dashboard/order_views.py` | `orders` | 25 | Trang quản lý đơn hàng: lọc theo trạng thái, bảng đơn đơn giản (không có thông tin giao hàng), nút bước tiếp theo, phân trang | [ ] |
| 384 | Claude Opus 5.5 |  | `backend/dashboard/order_views.py` | `order_detail` | 49 | Trang chi tiết đơn cho admin: cần xác thực lại, hiện SĐT/địa chỉ giao hàng, mỗi lần xem ghi log sensitive_data_viewed; mã sai hoặc không có trả 404 | [ ] |
| 385 | Claude Opus 5.5 |  | `backend/dashboard/order_views.py` | `order_advance` | 76 | Nhận nút chuyển trạng thái đơn (chỉ POST, CSRF, sau bước xác nhận bằng details): mỗi bước một URL, sai bước báo lỗi, mã không có trả 404, xong quay lại trang đang xem | [ ] |
| 386 | Claude Opus 5.5 |  | `frontend/templates/dashboard/partials/order_action.html` | `<details class="dash-step">` | 3 | Nút bước tiếp theo của đơn, xác nhận hai bước bằng details (không JS, không nhập mật khẩu), gửi POST tới URL riêng của bước đó | [ ] |
| 387 | Claude Opus 5.5 |  | `frontend/templates/dashboard/orders.html` | `<header class="dash-header">` | 6 | Trang quản lý đơn hàng: lọc trạng thái, bảng mã đơn/khách/ngày đặt/số cuốn/tổng tiền/trạng thái, link chi tiết (cần xác thực lại), nút bước tiếp theo, phân trang | [ ] |
| 388 | Claude Opus 5.5 |  | `frontend/templates/dashboard/order_detail.html` | `<header class="dash-header dash-header--row">` | 6 | Trang chi tiết đơn cho admin: trạng thái, khách, các mốc thời gian, giao dịch thanh toán, thông tin giao hàng (đã ghi log khi xem), sách và tiền, nút bước tiếp theo | [ ] |
| 389 | Claude Opus 5.5 |  | `frontend/static/css/dashboard.css` | `.dash-order__code { font-family: ui-monospace, SFMono-Regula` | 255 | Kiểu trang quản lý đơn: mã đơn chữ đơn cách, nút bước tiếp theo xác nhận bằng details, hai thẻ thông tin đơn/giao hàng | [ ] |
| 390 | Claude Opus 5.5 |  | `backend/dashboard/tests/test_orders.py` | `OrderAdminServiceTests` | 39 | Test service quản lý đơn bằng cursor giả: bộ lọc/mã đơn/tên bước sai không xuống CSDL, gọi đúng thủ tục từng bước qua kết nối staff, giải mã thông tin giao hàng, đổi lỗi SIGNAL, nút bước tiếp theo theo trạng thái | [ ] |
| 391 | Claude Opus 5.5 |  | `backend/dashboard/tests/test_orders.py` | `OrderAdminViewTests` | 132 | Test view quản lý đơn: chỉ nhân viên, danh sách không có thông tin giao hàng, chi tiết cần xác thực lại và ghi log, nút chuyển bước chỉ POST + CSRF, sai bước báo lỗi, mã không có trả 404, chỉ quay lại trang trong mục đơn hàng | [ ] |
| 392 | Claude Opus 5.5 |  | `database/objects/45_dashboard.sql` | `PROCEDURE sp_staff_dashboard_orders` | 31 | Thủ tục tổng quan đơn hàng: số đơn cần xử lý theo từng bước, đơn mới và đơn hủy hôm nay, doanh thu hôm nay/7 ngày/tháng này theo ngày thanh toán | [ ] |
| 393 | Claude Opus 5.5 |  | `database/objects/45_dashboard.sql` | `PROCEDURE sp_staff_dashboard_stock` | 76 | Thủ tục tổng quan kho: số sách đang bán sắp hết (1 đến ngưỡng) và hết hàng, 5 cuốn đang bán còn ít nhất | [ ] |
| 394 | Claude Opus 5.5 |  | `database/objects/45_dashboard.sql` | `PROCEDURE sp_staff_dashboard_security` | 110 | Thủ tục tổng quan bảo mật: số sự kiện mức cảnh báo/nghiêm trọng trong 24 giờ và số lần đăng nhập sai từ đầu ngày, chỉ trả con số | [ ] |
| 395 | Claude Opus 5.5 |  | `backend/dashboard/overview_services.py` | `OverviewError` | 17 | Lỗi nghiệp vụ khi đọc trang tổng quan, mang mã lỗi và câu tiếng Việt | [ ] |
| 396 | Claude Opus 5.5 |  | `backend/dashboard/overview_services.py` | `Overview` | 32 | Số liệu trang tổng quan: đơn cần xử lý theo bước, đơn mới/hủy hôm nay, doanh thu, kho, bảo mật | [ ] |
| 397 | Claude Opus 5.5 |  | `backend/dashboard/overview_services.py` | `period_starts` | 57 | Tính mốc đầu ngày hôm nay, đầu 7 ngày gần nhất (gồm hôm nay) và đầu tháng theo giờ Việt Nam rồi đổi về UTC không múi giờ để truyền xuống thủ tục | [ ] |
| 398 | Claude Opus 5.5 |  | `backend/dashboard/overview_services.py` | `get_overview` | 86 | Đọc số liệu tổng quan bằng 3 thủ tục (đơn và doanh thu, kho, bảo mật) qua kết nối staff, ngưỡng sắp hết lấy từ LOW_STOCK_THRESHOLD | [ ] |
| 399 | Claude Opus 5.5 |  | `backend/dashboard/views.py` | `index` | 18 | Trang Tổng quan: báo cáo cơ bản đọc bằng 3 thủ tục, không lưu cache, chỉ có con số nên không bắt xác thực lại | [ ] |
| 400 | Claude Opus 5.5 |  | `frontend/templates/dashboard/index.html` | `<header class="dash-header">` | 6 | Trang Tổng quan: đơn cần xử lý theo bước (bấm sang Quản lý đơn có lọc sẵn), đơn mới/hủy hôm nay, doanh thu, kho sắp hết/hết hàng và 5 cuốn còn ít nhất, bảo mật 24 giờ | [ ] |
| 401 | Claude Opus 5.5 |  | `frontend/static/css/dashboard.css` | `.dash-overview { margin-bottom: var(--space-xl); }` | 270 | Kiểu trang Tổng quan: nhóm số liệu có tiêu đề, thẻ số bấm được, thẻ cảnh báo đỏ, dải 4 bước đơn hàng, lưới kho/bảo mật | [ ] |
| 402 | Claude Opus 5.5 |  | `backend/dashboard/tests/test_overview.py` | `OverviewServiceTests` | 27 | Test service tổng quan: mốc ngày/7 ngày/tháng theo giờ Việt Nam đổi về UTC, gọi đúng 3 thủ tục qua kết nối staff với ngưỡng sắp hết từ settings, đọc nhiều bộ kết quả, đổi lỗi SIGNAL | [ ] |
| 403 | Claude Opus 5.5 |  | `backend/dashboard/tests/test_overview.py` | `OverviewViewTests` | 73 | Test trang Tổng quan: chỉ nhân viên, hiện các nhóm số liệu và link lọc sẵn, thẻ nghiêm trọng tô đỏ khi có sự kiện, không lưu cache, lỗi nghiệp vụ hiện thông báo | [ ] |
