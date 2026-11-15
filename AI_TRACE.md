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
| 037 | Claude Opus 5.5 |  | `backend/dashboard/views.py` | `profile` | 42 | Trang thông tin của nhân viên, mặc định không gửi email và SĐT | [ ] |
| 038 | Claude Opus 5.5 |  | `backend/dashboard/views.py` | `profile_contact` | 50 | Hiện email và SĐT của chính nhân viên sau khi xác thực lại, có ghi log | [ ] |
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
| 094 | Claude Opus 5.5 |  | `backend/dashboard/forms.py` | `StaffProfileUpdateForm` | 31 | Form sửa họ, tên, SĐT của nhân viên; ô SĐT luôn trống, để trống là giữ số cũ | [ ] |
| 095 | Claude Opus 5.5 |  | `backend/dashboard/services.py` | `update_staff_profile` | 17 | Lưu họ, tên, SĐT của nhân viên bằng kết nối staff, chỉ ghi cột thay đổi, log tên cột | [ ] |
| 096 | Claude Opus 5.5 |  | `backend/dashboard/views.py` | `profile_update` | 65 | Nhân viên sửa họ, tên, SĐT của chính mình sau khi xác thực lại, không hiện SĐT cũ | [ ] |
| 097 | Claude Opus 5.5 |  | `frontend/templates/dashboard/profile_update.html` | `<header class="dash-header">` | 6 | Form sửa họ, tên, SĐT của nhân viên; không hiện email và SĐT hiện tại | [ ] |
| 098 | Claude Opus 5.5 |  | `frontend/static/css/dashboard.css` | `.dash-actions { display: flex; flex-wrap: wrap; gap: var(--s` | 72 | Kiểu form cập nhật thông tin nhân viên và hàng nút thao tác | [ ] |
| 099 | Claude Opus 5.5 |  | `database/objects/10_trg_accounts_user_guard.sql` | `IF SUBSTRING_INDEX(USER(), '@', 1) = 'app_staff' AND OLD.is_` | 80 | Chặn app_staff sửa dòng của khách hàng | [ ] |
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
| 116 | Claude Opus 5.5 |  | `backend/core/management/commands/db_check_grants.py` | `Command` | 50 | Lệnh kiểm tra phân quyền trên CSDL thật: chạy từng câu bằng app_customer/app_staff, so với kết quả mong đợi | [ ] |
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
| 161 | Claude Opus 5.5 |  | `backend/dashboard/catalog_views.py` | `_book_or_404` | 36 | Lấy sách theo id trong URL, không có thì trả 404 | [ ] |
| 162 | Claude Opus 5.5 |  | `backend/dashboard/catalog_views.py` | `books` | 44 | Trang danh sách sách: lọc theo tên, tác giả, thể loại, trạng thái, phân trang, cảnh báo tồn kho thấp | [ ] |
| 163 | Claude Opus 5.5 |  | `backend/dashboard/catalog_views.py` | `book_create` | 75 | Trang thêm sách: form thông tin, tồn kho ban đầu, ảnh bìa; lỗi service gắn vào đúng ô | [ ] |
| 164 | Claude Opus 5.5 |  | `backend/dashboard/catalog_views.py` | `book_edit` | 97 | Trang sửa sách: form thông tin và ảnh, kèm khung tồn kho, trạng thái và nút xóa | [ ] |
| 165 | Claude Opus 5.5 |  | `backend/dashboard/catalog_views.py` | `_change_stock` | 130 | Xử lý chung form nhập kho/giảm kho: kiểm tra số lượng, gọi service, báo kết quả rồi quay lại trang sửa | [ ] |
| 166 | Claude Opus 5.5 |  | `backend/dashboard/catalog_views.py` | `book_restock` | 147 | Nhập thêm hàng cho một sách (POST) | [ ] |
| 167 | Claude Opus 5.5 |  | `backend/dashboard/catalog_views.py` | `book_reduce` | 155 | Giảm kho ngoại lệ cho một sách (POST) | [ ] |
| 168 | Claude Opus 5.5 |  | `backend/dashboard/catalog_views.py` | `book_toggle` | 163 | Ẩn hoặc hiện sách theo trạng thái gửi lên rõ ràng, không đảo trạng thái mù | [ ] |
| 169 | Claude Opus 5.5 |  | `backend/dashboard/catalog_views.py` | `book_delete` | 182 | Xóa hẳn sách: cần xác thực lại, có trang xác nhận, chỉ xóa sách đang ẩn | [ ] |
| 170 | Claude Opus 5.5 |  | `backend/dashboard/catalog_views.py` | `categories` | 203 | Trang thể loại: danh sách kèm số sách, form thêm, form sửa tên từng dòng | [ ] |
| 171 | Claude Opus 5.5 |  | `backend/dashboard/catalog_views.py` | `category_rename` | 222 | Sửa tên thể loại (POST), báo lỗi trùng tên hoặc không tồn tại | [ ] |
| 172 | Claude Opus 5.5 |  | `backend/dashboard/catalog_views.py` | `category_delete` | 240 | Xóa thể loại: cần xác thực lại, có trang xác nhận, chỉ xóa thể loại không còn sách | [ ] |
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
| 231 | Claude Opus 5.5 |  | `backend/orders/forms.py` | `CartAddForm` | 6 | Form thêm vào giỏ: chỉ id sách và số lượng 1–5, không có giá hay user | [ ] |
| 232 | Claude Opus 5.5 |  | `backend/orders/views.py` | `_safe_back_url` | 94 | Chỉ quay lại địa chỉ nội bộ an toàn sau khi thêm vào giỏ, chặn open redirect | [ ] |
| 233 | Claude Opus 5.5 |  | `backend/orders/views.py` | `cart_add` | 105 | Nhận form thêm vào giỏ (chỉ POST, CSRF): ẩn danh đi đăng nhập, nhân viên bị từ chối, xong thì ở lại trang đang xem kèm thông báo | [ ] |
| 234 | Claude Opus 5.5 |  | `frontend/templates/shop/book_detail.html` | `{% if book.in_stock and not user.is_staff %}` | 48 | Form thêm vào giỏ cạnh nút đặt hàng: ô số lượng 1–5, khóa khi hết hàng | [ ] |
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
| 248 | Claude Opus 5.5 |  | `backend/orders/forms.py` | `CartQuantityForm` | 12 | Form đổi số lượng trong giỏ: id sách và số lượng cuối cùng 1–5 | [ ] |
| 249 | Claude Opus 5.5 |  | `backend/orders/forms.py` | `CartRemoveForm` | 18 | Form gỡ sách khỏi giỏ: chỉ id sách | [ ] |
| 250 | Claude Opus 5.5 |  | `backend/orders/views.py` | `cart` | 20 | Trang giỏ hàng của khách: đọc bằng sp_cart_list, không lưu cache; nhân viên không có giỏ | [ ] |
| 251 | Claude Opus 5.5 |  | `backend/orders/views.py` | `_cart_page_guard` | 36 | Kiểm tra chung cho form trên trang giỏ: ẩn danh đi đăng nhập rồi quay lại giỏ, nhân viên bị từ chối | [ ] |
| 252 | Claude Opus 5.5 |  | `backend/orders/views.py` | `cart_update` | 47 | Nhận nút tăng/giảm trên trang giỏ (chỉ POST, CSRF): gửi số lượng cuối cùng, xong quay về giỏ | [ ] |
| 253 | Claude Opus 5.5 |  | `backend/orders/views.py` | `cart_remove` | 66 | Nhận nút gỡ sách trên trang giỏ (chỉ POST, CSRF), không hỏi xác nhận, xong quay về giỏ | [ ] |
| 254 | Claude Opus 5.5 |  | `frontend/templates/shop/cart.html` | `<div class="cart">` | 11 | Danh sách sách trong giỏ: nút −/+ gửi số lượng cuối cùng, nút Gỡ, sách ngừng bán/hết hàng hiện mờ chỉ gỡ được, tạm tính và nút đặt hàng mờ | [ ] |
| 255 | Claude Opus 5.5 |  | `frontend/static/css/account-area.css` | `.cart { display: grid; grid-template-columns: minmax(0, 1fr)` | 48 | Kiểu trang giỏ hàng: danh sách sách bên trái, ô tạm tính bên phải, sách không bán được hiện mờ, xếp dọc trên màn hình hẹp | [ ] |
| 256 | Claude Opus 5.5 |  | `backend/orders/tests/test_cart_page.py` | `CartDataTests` | 30 | Test dữ liệu giỏ: tạm tính chỉ tính sách còn bán, nút tăng/giảm khóa đúng lúc, nhãn ngừng bán/hết hàng | [ ] |
| 257 | Claude Opus 5.5 |  | `backend/orders/tests/test_cart_page.py` | `CartPageServiceTests` | 53 | Test service trang giỏ bằng cursor giả: user lấy từ phiên, id/số lượng kiểm tra trước khi xuống CSDL, giới hạn tần suất, đổi lỗi SIGNAL | [ ] |
| 258 | Claude Opus 5.5 |  | `backend/orders/tests/test_cart_page.py` | `CartPageViewTests` | 131 | Test view trang giỏ: hiển thị dòng, nút khóa, không cache; form chỉ POST + CSRF, ẩn danh đi đăng nhập, nhân viên bị từ chối, luôn quay về giỏ | [ ] |
