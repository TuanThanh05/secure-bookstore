# AI_TRACE – code do AI viết và giải thích code

Trước đây mỗi hàm do AI viết có một dòng `AI-TRACE` ngay trong code, và nhiều chỗ có khối chú thích dài. Từ ngày 21/11/2026 các dòng đó và các khối chú thích nhiều dòng đã được bỏ khỏi code và chuyển hết vào file này; trong code chỉ còn chú thích một dòng. Cách ghi mục mới: `docs/ai-trace.md`.

Mỗi mục có dạng:

```
<loại> <tên> | <file> | <AI viết>
<giải thích>
```

- Sắp theo thư mục, rồi theo file, rồi theo thứ tự xuất hiện trong file.
- `#NNN` là số ID cũ của dòng AI-TRACE, giữ lại để đối chiếu với lịch sử PR.
- "chưa đánh dấu": chỗ đó có khối chú thích giải thích nhưng không có dòng AI-TRACE (phần lớn là bộ khung viết trước khi có quy định AI-TRACE ngày 14/11).
- Đoạn giải thích dưới dòng mô tả là nội dung khối chú thích cũ, giữ nguyên ý, chỉ nối dòng.


## Backend (Python, Django)

### `backend/accounts/admin.py`

**cả file | backend/accounts/admin.py | chưa đánh dấu**  
Nhóm KHÔNG dùng trang /admin/ mặc định của Django cho bảng nghiệp vụ (django.contrib.admin chưa được bật). Trang quản trị tự viết nằm ở app dashboard.

### `backend/accounts/decorators.py`

**hàm `customer_required` | backend/accounts/decorators.py | Claude Opus 5.5**  
#071 – Chỉ cho khách đã đăng nhập, nhân viên bị chuyển sang trang quản trị.

**hàm `customer_recent_auth_required` | backend/accounts/decorators.py | Claude Opus 5.5**  
#072 – Bắt khách xác thực lại trong vài phút gần đây, chuyển tới trang xác thực riêng của khách.

### `backend/accounts/emails.py`

**hàm `_allow_send` | backend/accounts/emails.py | Claude Opus 5.5**  
#016 – Giới hạn mỗi địa chỉ email chỉ nhận một thư mỗi loại trong một khoảng thời gian.

**hàm `_send` | backend/accounts/emails.py | Claude Opus 5.5**  
#017 – Gửi một thư văn bản thuần, lỗi SMTP chỉ ghi log không lộ ra ngoài.

**hàm `send_signup_link_email` | backend/accounts/emails.py | Claude Opus 5.5**  
#414 – Gửi thư chứa link tiếp tục đăng ký có hạn dùng tới đúng email vừa nhập.

**hàm `send_existing_account_email` | backend/accounts/emails.py | Claude Opus 5.5**  
#019 – Báo cho chủ email biết có người dùng email này để đăng ký lại.

**hàm `send_password_reset_email` | backend/accounts/emails.py | Claude Opus 5.5**  
#047 – Gửi thư chứa link đặt lại mật khẩu có hạn dùng.

**hàm `send_password_changed_email` | backend/accounts/emails.py | Claude Opus 5.5**  
#048 – Báo cho chủ tài khoản biết mật khẩu vừa được đổi.

**hàm `send_staff_password_changed_email` | backend/accounts/emails.py | Claude Opus 5.5**  
#092 – Báo cho nhân viên biết mật khẩu vừa được đổi bằng lệnh trên máy chủ, không kèm link.

**hàm `send_two_factor_email` | backend/accounts/emails.py | Claude Opus 5.5**  
#498 – Báo cho chủ tài khoản mỗi lần bật/tắt 2 bước hoặc dùng mã dự phòng, kèm link đổi mật khẩu.

**hàm `send_new_login_email` | backend/accounts/emails.py | Claude Opus 5.5**  
#587 – Báo cho chủ tài khoản mỗi lần một phiên cũ bị kết thúc vì tài khoản vừa đăng nhập ở nơi khác, kèm giờ và IP của lần đăng nhập mới.

### `backend/accounts/forms.py`

**hàm `cap_password_fields` | backend/accounts/forms.py | Claude Opus 5.5**  
#465 – Chặn độ dài ô mật khẩu ngay ở form: quá dài thì form báo lỗi, không gọi authenticate hay validator (không băm Argon2).

**class `SignupEmailForm` | backend/accounts/forms.py | Claude Opus 5.5**  
#412 – Bước 1 đăng ký: chỉ một ô email, chuẩn hóa về chữ thường.

**class `SignupCompleteForm` | backend/accounts/forms.py | Claude Opus 5.5**  
#413 – Bước 2 đăng ký: tên đăng nhập và mật khẩu, email lấy từ phiên chứ không từ form. Đã viết lại bởi Claude Opus 5.5 khi giới hạn độ dài mật khẩu.

**class `LoginForm` | backend/accounts/forms.py | Claude Opus 5.5**  
#543 – Form đăng nhập chỉ nhận tên đăng nhập (không nhận email): chặn dò email ↔ tên đăng nhập qua trạng thái khóa.  
#540 – Đúng mật khẩu nhưng tài khoản đang bị khóa tự động vì giữ kho: không cho đăng nhập, báo giờ mở khóa.

**class `CustomerPasswordResetForm` | backend/accounts/forms.py | Claude Opus 5.5**  
#049 – Form quên mật khẩu chỉ gửi cho khách, dùng thư và giới hạn của nhóm.

**class `CustomerPasswordChangeForm` | backend/accounts/forms.py | Claude Opus 5.5**  
#057 – Form đổi mật khẩu: mật khẩu hiện tại và hai ô mật khẩu mới. Đã viết lại bởi Claude Opus 5.5 khi giới hạn độ dài mật khẩu.

**class `CustomerSetPasswordForm` | backend/accounts/forms.py | Claude Opus 5.5**  
#466 – Form đặt mật khẩu mới từ link quên mật khẩu, có chặn độ dài ô mật khẩu.

**class `CurrentUserPasswordForm` | backend/accounts/forms.py | Claude Opus 5.5**  
#550 – Form xác nhận bằng mật khẩu của chính người đang đăng nhập (T2.2): không có ô tên đăng nhập, tên lấy từ request.user nên không thử được mật khẩu tài khoản khác.

**class `CustomerReauthForm` | backend/accounts/forms.py | Claude Opus 5.5**  
#073 – Form xác thực lại của khách, nhận tên đăng nhập hoặc email và mật khẩu. Đã viết lại bởi Claude Opus 5.5 khi giới hạn độ dài mật khẩu.

**class `ProfileUpdateForm` | backend/accounts/forms.py | Claude Opus 5.5**  
#074 – Form cập nhật họ, tên, SĐT của khách; không có ô username hay email.

**class `TwoFactorCodeForm` | backend/accounts/forms.py | Claude Opus 5.5**  
#491 – Ô nhập mã 6 số (hoặc mã dự phòng) của bước 2 khi đăng nhập và khi cài.

**class `TwoFactorDisableForm` | backend/accounts/forms.py | Claude Opus 5.5**  
#492 – Form tắt 2 bước: mật khẩu hiện tại và mã 6 số (hoặc mã dự phòng).

### `backend/accounts/management/commands/_two_factor_cli.py`

**hàm `check_connection` | backend/accounts/management/commands/_two_factor_cli.py | Claude Opus 5.5**  
#504 – Lệnh 2 bước của admin chỉ chạy bằng tài khoản migrate, không bằng tài khoản web.

**hàm `enroll_in_terminal` | backend/accounts/management/commands/_two_factor_cli.py | Claude Opus 5.5**  
#505 – In mã QR ra terminal, hỏi mã 6 số để chắc admin đã quét đúng; sai 3 lần thì hủy (giao dịch quay lui).

### `backend/accounts/management/commands/dat_lai_2fa_admin.py`

**class `Command` | backend/accounts/management/commands/dat_lai_2fa_admin.py | Claude Opus 5.5**  
#507 – Lệnh máy chủ cài lại 2 bước cho admin mất điện thoại: gõ xác nhận, gỡ thiết bị cũ, quét QR mới, đăng xuất mọi phiên, ghi log. Đã viết lại bởi Claude Opus 5.5 khi dùng chung end_user_sessions.

### `backend/accounts/management/commands/doi_mat_khau_admin.py`

**class `Command` | backend/accounts/management/commands/doi_mat_khau_admin.py | Claude Opus 5.5**  
#091 – Lệnh máy chủ đổi mật khẩu nhân viên: kiểm tra quy tắc mật khẩu, đăng xuất mọi phiên, ghi log, gửi thư báo. Đã viết lại bởi Claude Opus 5.5 khi băm khóa phiên.

### `backend/accounts/management/commands/tao_admin.py`

**class `Command` | backend/accounts/management/commands/tao_admin.py | Claude Opus 5.5**  
#506 – Lệnh máy chủ tạo admin duy nhất: kiểm tra quy tắc mật khẩu, bắt buộc cài 2 bước ngay, lỗi ở bất kỳ bước nào thì không tạo gì.

### `backend/accounts/models.py`

**class `User` | backend/accounts/models.py | Claude Opus 5.5**  
#538 – Tài khoản đang bị khóa tự động vì giữ kho (auto_locked_until còn hạn).

**class `PasswordHistory` | backend/accounts/models.py | Claude Opus 5.5**  
#088 – Model chỉ đọc cho bảng lịch sử mã băm mật khẩu do trigger ghi.

**class `TotpDevice` | backend/accounts/models.py | Claude Opus 5.5**  
#477 – Model thiết bị TOTP (bảng do schema/10 tạo): chuỗi bí mật mã hóa, lúc xác nhận, bước đã dùng.

**class `RecoveryCode` | backend/accounts/models.py | Claude Opus 5.5**  
#478 – Model mã dự phòng (bảng do schema/10 tạo): chỉ mã băm, lúc đã dùng.

### `backend/accounts/profile.py`

**class `ProfileView` | backend/accounts/profile.py | Claude Opus 5.5**  
#034 – Dữ liệu trang thông tin tài khoản, email và SĐT có thể bị giấu.

**hàm `phone_context` | backend/accounts/profile.py | Claude Opus 5.5**  
#068 – Ngữ cảnh mã hóa SĐT gắn với id người dùng, chống tráo bản mã giữa các dòng.

**hàm `encrypt_phone` | backend/accounts/profile.py | Claude Opus 5.5**  
#069 – Mã hóa SĐT trước khi lưu, chuỗi rỗng thì lưu NULL.

**hàm `decrypt_phone` | backend/accounts/profile.py | Claude Opus 5.5**  
#070 – Giải mã SĐT để hiển thị, lỗi giải mã thì trả câu báo thay vì làm hỏng trang.

**hàm `build_profile` | backend/accounts/profile.py | Claude Opus 5.5**  
#035 – Tạo dữ liệu trang thông tin, chỉ đưa email và SĐT khi được phép.

### `backend/accounts/services.py`

**hàm `allow_signup_step` | backend/accounts/services.py | Claude Opus 5.5**  
#415 – Giới hạn số lần gửi form đăng ký của mỗi IP, đếm riêng từng bước. Đã viết lại bởi Claude Opus 5.5 khi đọc IP thật sau Nginx.

**hàm `_allow_signup_mail` | backend/accounts/services.py | Claude Opus 5.5**  
#416 – Giới hạn số thư đăng ký gửi tới một email trong một giờ, tính cả thư báo trùng.

**hàm `start_signup` | backend/accounts/services.py | Claude Opus 5.5**  
#417 – Bước 1 đăng ký: không ghi CSDL, email mới nhận link, email đã có nhận thư báo.

**hàm `email_has_account` | backend/accounts/services.py | Claude Opus 5.5**  
#418 – Email đã có tài khoản chưa (link đăng ký chỉ dùng được khi chưa có).

**hàm `remember_signup_email` | backend/accounts/services.py | Claude Opus 5.5**  
#419 – Cất email đã chứng minh vào phiên mới (đổi session ID) kèm thời điểm bấm link.

**hàm `pending_signup_email` | backend/accounts/services.py | Claude Opus 5.5**  
#420 – Lấy email đăng ký đang chờ trong phiên, quá hạn hoặc sai dạng thì xóa và trả None.

**hàm `complete_signup` | backend/accounts/services.py | Claude Opus 5.5**  
#421 – Bước 2 đăng ký: tạo tài khoản đã xác nhận email, chặn trùng bằng UNIQUE khi nộp cùng lúc. Đã viết lại bởi Claude Opus 5.5 khi tách app_auth.

**hàm `record_password_change_failure` | backend/accounts/services.py | Claude Opus 5.5**  
#058 – Đếm số lần nhập sai mật khẩu hiện tại khi đổi mật khẩu, trả về tổng số lần.

**hàm `clear_password_change_failures` | backend/accounts/services.py | Claude Opus 5.5**  
#059 – Xóa bộ đếm nhập sai sau khi đổi mật khẩu thành công.

**hàm `update_profile` | backend/accounts/services.py | Claude Opus 5.5**  
#075 – Lưu họ, tên, SĐT đã mã hóa; chỉ ghi cột thay đổi và log tên cột, không log giá trị.

**hàm `login_ip_blocked` | backend/accounts/services.py | Claude Opus 5.5**  
#546 – IP đã đăng nhập sai quá ngưỡng (gộp mọi tài khoản) trong cửa sổ gần nhất thì chặn: đếm bằng sp_login_ip_failures trên bảng nhật ký.

### `backend/accounts/tests/test_admin_password_command.py`

**class `AdminPasswordCommandTests` | backend/accounts/tests/test_admin_password_command.py | Claude Opus 5.5**  
#093 – Test lệnh đổi mật khẩu admin: chỉ nhân viên, quy tắc mật khẩu, đăng xuất phiên, log, thư báo, chặn kết nối web.

### `backend/accounts/tests/test_login_username_only.py`

**class `UsernameOnlyLoginTests` | backend/accounts/tests/test_login_username_only.py | Claude Opus 5.5**  
#548 – Test T3.2: đăng nhập/xác thực lại chỉ nhận tên đăng nhập, email đúng + mật khẩu đúng vẫn bị từ chối như sai; thư quên mật khẩu kèm tên đăng nhập. Đã viết lại bởi Claude Opus 5.5 khi bỏ ô tên đăng nhập ở xác thực lại (T2.2).

**class `LoginIpGuardTests` | backend/accounts/tests/test_login_username_only.py | Claude Opus 5.5**  
#549 – Test T3.2: IP đăng nhập sai quá ngưỡng bị 429 trước khi kiểm mật khẩu (không authenticate, không thêm login_failed), có log rate_limited.

### `backend/accounts/tests/test_password_change.py`

**class `PasswordChangeTests` | backend/accounts/tests/test_password_change.py | Claude Opus 5.5**  
#063 – Test đổi mật khẩu: mật khẩu cũ, đăng xuất thiết bị khác, sai nhiều lần, chặn nhân viên. Đã viết lại bởi Claude Opus 5.5 khi thêm luật một tài khoản một phiên.

### `backend/accounts/tests/test_password_history.py`

**class `PasswordHistoryTests` | backend/accounts/tests/test_password_history.py | Claude Opus 5.5**  
#090 – Test chặn dùng lại 5 mật khẩu gần nhất, tính cả mật khẩu hiện tại, qua validator và trang đổi mật khẩu.

### `backend/accounts/tests/test_password_max_length.py`

**class `MaximumLengthValidatorTests` | backend/accounts/tests/test_password_max_length.py | Claude Opus 5.5**  
#467 – Test giới hạn 64 ký tự: validator, mọi form có ô mật khẩu, quá dài thì không gọi authenticate hay validator (không băm). Đã viết lại bởi Claude Opus 5.5 khi bỏ ô tên đăng nhập ở xác thực lại (T2.2).

### `backend/accounts/tests/test_password_reset.py`

**class `PasswordResetTests` | backend/accounts/tests/test_password_reset.py | Claude Opus 5.5**  
#056 – Test luồng quên mật khẩu: gửi link, đặt lại, link hết hạn, chặn nhân viên.

**class `ResetLinkLoggingTests` | backend/accounts/tests/test_password_reset.py | Claude Opus 5.5**  
#521 – Test tái hiện lỗi lộ mã đặt lại mật khẩu trong nhật ký: link đúng không ghi invalid_input, không đường dẫn log nào chứa mã.

### `backend/accounts/tests/test_profile.py`

**class `CustomerProfileTests` | backend/accounts/tests/test_profile.py | Claude Opus 5.5**  
#045 – Test trang thông tin của khách: hiện email, chặn nhân viên, không lưu cache.

### `backend/accounts/tests/test_profile_update.py`

**class `ProfileUpdateTests` | backend/accounts/tests/test_profile_update.py | Claude Opus 5.5**  
#083 – Test xác thực lại của khách và cập nhật họ, tên, SĐT mã hóa. Đã viết lại bởi Claude Opus 5.5 khi bỏ đăng nhập bằng email (T3.2).

### `backend/accounts/tests/test_reauth_password_only.py`

**class `PasswordOnlyReauthTests` | backend/accounts/tests/test_reauth_password_only.py | Claude Opus 5.5**  
#554 – Test T2.2: 3 form xác thực lại chỉ còn ô mật khẩu, tên lấy từ phiên (gửi kèm username của người khác bị bỏ qua), trang hiện tên dạng chữ và không có ô username gửi lên server.

### `backend/accounts/tests/test_signup.py`

**class `SignupTests` | backend/accounts/tests/test_signup.py | Claude Opus 5.5**  
#431 – Test đăng ký bắt đầu bằng email: chống chiếm tài khoản trước, phiên, link, giới hạn. Đã viết lại bởi Claude Opus 5.5 khi bỏ đăng nhập bằng email (T3.2).

### `backend/accounts/tests/test_signup_captcha.py`

**class `SignupCaptchaTests` | backend/accounts/tests/test_signup_captcha.py | Claude Opus 5.5**  
#444 – Test trang đăng ký có Turnstile: CSP riêng trang, thiếu token, Cloudflare lỗi, vẫn giữ giới hạn tần suất.

### `backend/accounts/tests/test_signup_token.py`

**class `SignupTokenTests` | backend/accounts/tests/test_signup_token.py | Claude Opus 5.5**  
#430 – Test mã link đăng ký: hợp lệ, hết hạn, bị sửa, ký sai mục đích, sai dạng.

### `backend/accounts/tests/test_single_session.py`

**class `SingleSessionTests` | backend/accounts/tests/test_single_session.py | Claude Opus 5.5**  
#588 – Test một tài khoản một phiên: đăng nhập mới đẩy phiên cũ ra (phiên cũ thấy thông báo, không lộ IP), ghi log, gửi thư kèm IP cho chủ tài khoản; phiên người khác và phiên admin đã quá 1 giờ không tính.

### `backend/accounts/tests/test_two_factor.py`

**class `TwoFactorServiceTests` | backend/accounts/tests/test_two_factor.py | Claude Opus 5.5**  
#509 – Test service TOTP: mã đúng/sai, lệch giờ, không dùng lại mã, chuỗi bí mật mã hóa gắn user, mã dự phòng một lần.

**class `TwoFactorLoginTests` | backend/accounts/tests/test_two_factor.py | Claude Opus 5.5**  
#510 – Test đăng nhập 2 bước: đúng mật khẩu chưa đăng nhập, mã đúng mới vào, sai 5 lần hủy lượt, hết hạn, mã dự phòng, admin bắt buộc.

**class `TwoFactorSetupTests` | backend/accounts/tests/test_two_factor.py | Claude Opus 5.5**  
#511 – Test bật/tắt 2 bước của khách: cần xác thực lại, QR không cache, mã sai không bật, mã dự phòng hiện một lần, thư báo.

**class `AdminCommandTests` | backend/accounts/tests/test_two_factor.py | Claude Opus 5.5**  
#512 – Test lệnh tao_admin/dat_lai_2fa_admin: bắt cài 2 bước ngay, chỉ một admin, sai mã thì không tạo gì.

### `backend/accounts/tests/two_factor_helpers.py`

**hàm `enroll` | backend/accounts/tests/two_factor_helpers.py | Claude Opus 5.5**  
#508 – Hàm hỗ trợ test: gắn sẵn thiết bị 2 bước đã xác nhận, nhập mã 6 số ở bước 2.

### `backend/accounts/tokens.py`

**class `SignupTokenResult` | backend/accounts/tokens.py | Claude Opus 5.5**  
#409 – Kết quả đọc mã trong link đăng ký gồm trạng thái và email.

**hàm `make_signup_token` | backend/accounts/tokens.py | Claude Opus 5.5**  
#410 – Tạo mã link đăng ký chỉ chứa email, ký bằng SECRET_KEY kèm salt riêng.

**hàm `read_signup_token` | backend/accounts/tokens.py | Claude Opus 5.5**  
#411 – Kiểm tra chữ ký, hạn dùng và dạng dữ liệu của mã link đăng ký.

### `backend/accounts/two_factor.py`

**hàm `_context` | backend/accounts/two_factor.py | Claude Opus 5.5**  
#480 – Ngữ cảnh mã hóa chuỗi bí mật gắn với user_id: chép bản mã sang dòng khác thì không giải mã được.

**hàm `requires_two_factor` | backend/accounts/two_factor.py | Claude Opus 5.5**  
#481 – Nhân viên luôn phải qua bước 2; khách chỉ khi đã bật và xác nhận thiết bị.

**hàm `start_setup` | backend/accounts/two_factor.py | Claude Opus 5.5**  
#482 – Bắt đầu cài 2 bước: tạo chuỗi bí mật 160 bit mới (mã hóa), xóa lượt cài dở trước đó.

**hàm `pending_setup` | backend/accounts/two_factor.py | Claude Opus 5.5**  
#483 – Lấy lượt cài đang dở (chưa xác nhận, chưa quá hạn) của đúng người dùng.

**hàm `qr_svg` | backend/accounts/two_factor.py | Claude Opus 5.5**  
#484 – Vẽ mã QR thành SVG (phục vụ như ảnh từ URL riêng, không nhúng vào HTML).

**hàm `verify_code` | backend/accounts/two_factor.py | Claude Opus 5.5**  
#485 – Kiểm mã 6 số: lệch ±30 giây, so sánh hằng thời gian, mỗi bước thời gian chỉ dùng một lần (UPDATE có điều kiện nên 2 request cùng lúc chỉ một cái qua).

**hàm `confirm_setup` | backend/accounts/two_factor.py | Claude Opus 5.5**  
#486 – Xác nhận lượt cài: mã đúng thì bật 2 bước và tạo mã dự phòng (khách), trả mã dự phòng dạng chữ một lần.

**hàm `replace_recovery_codes` | backend/accounts/two_factor.py | Claude Opus 5.5**  
#487 – Tạo 5 mã dự phòng mới (50 bit mỗi mã), chỉ lưu mã băm, xóa bộ cũ.

**hàm `use_recovery_code` | backend/accounts/two_factor.py | Claude Opus 5.5**  
#488 – Dùng một mã dự phòng: đúng thì đánh dấu đã dùng (UPDATE có điều kiện), trả số mã còn lại.

**hàm `disable` | backend/accounts/two_factor.py | Claude Opus 5.5**  
#489 – Tắt 2 bước của khách: xóa thiết bị và mọi mã dự phòng.

**hàm `record_failure` | backend/accounts/two_factor.py | Claude Opus 5.5**  
#490 – Đếm số lần nhập sai bước 2 của mỗi tài khoản trong 1 giờ (chặn dò mã qua nhiều lượt đăng nhập).

### `backend/accounts/validators.py`

**class `PasswordHistoryValidator` | backend/accounts/validators.py | Claude Opus 5.5**  
#089 – Chặn mật khẩu mới trùng một trong N mật khẩu gần nhất, tính cả mật khẩu đang dùng.

**class `MaximumLengthValidator` | backend/accounts/validators.py | Claude Opus 5.5**  
#464 – Mật khẩu dài tối đa N ký tự (64, theo mức tối thiểu NIST SP 800-63B) để không ai bắt máy chủ băm Argon2 chuỗi khổng lồ.

### `backend/accounts/views.py`

**hàm `register` | backend/accounts/views.py | Claude Opus 5.5**  
#422 – Đăng ký bước 1: chỉ nhận email, mọi trường hợp đều chuyển tới trang kiểm tra hộp thư. Đã viết lại bởi Claude Opus 5.5 khi thêm Cloudflare Turnstile.

**hàm `check_email` | backend/accounts/views.py | Claude Opus 5.5**  
#024 – Trang báo kiểm tra hộp thư, giống nhau cho mọi trường hợp.

**hàm `signup_confirm` | backend/accounts/views.py | Claude Opus 5.5**  
#423 – Mở link đăng ký: kiểm tra mã, cất email vào phiên rồi chuyển sang địa chỉ không chứa mã.

**hàm `signup_complete` | backend/accounts/views.py | Claude Opus 5.5**  
#424 – Đăng ký bước 2: đặt tên đăng nhập, mật khẩu cho email trong phiên, xong thì về đăng nhập.

**class `CustomerPasswordResetView` | backend/accounts/views.py | Claude Opus 5.5**  
#050 – Trang quên mật khẩu: nhập email, ghi log, trả lời giống nhau cho mọi email.

**hàm `password_reset_done` | backend/accounts/views.py | Claude Opus 5.5**  
#051 – Trang báo đã gửi thư đặt lại mật khẩu kèm thời hạn link.

**class `CustomerPasswordResetConfirmView` | backend/accounts/views.py | Claude Opus 5.5**  
#052 – Đặt mật khẩu mới từ link: chặn nhân viên, xác nhận email, mở khóa axes, báo thư. Đã viết lại bởi Claude Opus 5.5 khi đổi sang đăng ký bằng email.  
#520 – Chỉ ghi invalid_input khi link đặt lại mật khẩu thật sự sai (link đúng bị Django chuyển hướng 302 trước khi có validlink), đường dẫn trong log không chứa mã.

**hàm `profile` | backend/accounts/views.py | Claude Opus 5.5**  
#036 – Trang thông tin của khách, nhân viên bị chuyển sang trang quản trị. Đã viết lại bởi Claude Opus 5.5 khi thêm xác thực 2 bước.

**hàm `password_change` | backend/accounts/views.py | Claude Opus 5.5**  
#060 – Đổi mật khẩu cho khách: giữ phiên hiện tại, đăng xuất thiết bị khác, sai nhiều lần thì đăng xuất.

**hàm `reauth` | backend/accounts/views.py | Claude Opus 5.5**  
#076 – Trang xác thực lại riêng cho khách, có link quên mật khẩu, next chỉ trỏ trong site. Đã viết lại bởi Claude Opus 5.5 khi bỏ ô tên đăng nhập (T2.2).

**hàm `profile_update` | backend/accounts/views.py | Claude Opus 5.5**  
#077 – Cập nhật họ, tên, SĐT của khách sau khi xác thực lại.

**class `SecureLoginView` | backend/accounts/views.py | Claude Opus 5.5**  
#493 – Đăng nhập bước 1: đúng mật khẩu mà cần 2 bước thì CHƯA đăng nhập, chỉ ghi trạng thái chờ (đổi session ID) rồi chuyển sang bước 2.  
#547 – IP đã đăng nhập sai quá ngưỡng (mọi tài khoản) thì trả 429 trước khi kiểm mật khẩu, không gọi authenticate, ghi log.

**hàm `login_two_factor` | backend/accounts/views.py | Claude Opus 5.5**  
#494 – Đăng nhập bước 2: mã 6 số (hoặc mã dự phòng của khách) đúng mới login(); sai 5 lần hủy lượt, sai nhiều lần/giờ chặn tài khoản.

**hàm `two_factor_setup` | backend/accounts/views.py | Claude Opus 5.5**  
#495 – Cài 2 bước cho khách: trang QR cần xác thực lại; mã đúng thì bật, hiện 5 mã dự phòng đúng một lần, gửi thư báo.

**hàm `two_factor_qr` | backend/accounts/views.py | Claude Opus 5.5**  
#496 – Ảnh QR của lượt cài đang dở: chỉ chủ tài khoản, không cache, hết lượt cài thì 404.

**hàm `two_factor_disable` | backend/accounts/views.py | Claude Opus 5.5**  
#497 – Tắt 2 bước: cần mật khẩu và mã hiện tại (hoặc mã dự phòng), sai nhiều lần thì đăng xuất, gửi thư báo.

### `backend/bookstore/settings/base.py`

**biến `TRUSTED_PROXY_IPS` | backend/bookstore/settings/base.py | chưa đánh dấu**  
IP thật của client sau reverse proxy (core/client_ip.py). Chỉ tin header khi REMOTE_ADDR là một proxy trong danh sách này; trống (máy dev) = không tin header nào.

**biến `SECURITY_LOG_SECRET_PATHS` | backend/bookstore/settings/base.py | chưa đánh dấu**  
Đường dẫn chứa mã bí mật (core/security_log.py): nhóm "secret" được thay bằng "-" trước khi ghi file log và bảng core_securityevent. Thêm URL mới chứa mã thì thêm mẫu vào đây.

**biến `PASSWORD_MAX_LENGTH` | backend/bookstore/settings/base.py | chưa đánh dấu**  
Mọi ô mật khẩu (kể cả đăng nhập, xác thực lại) cũng bị chặn ở mức này trong form (accounts.forms.cap_password_fields) để không gọi Argon2 với chuỗi quá dài.

**biến `BACKUP_DIR` | backend/bookstore/settings/base.py | chưa đánh dấu**  
Sao lưu CSDL (lệnh db_backup, db_backup_export, db_restore, db_backup_verify – chỉ chạy trên máy chủ). Khóa mã hóa BACKUP_ENCRYPTION_KEY và mật khẩu DB_BACKUP_PASSWORD nằm trong database/.env.db (web không đọc).

### `backend/bookstore/settings/migrate.py`

**cả file | backend/bookstore/settings/migrate.py | chưa đánh dấu**  
Cấu hình CHỈ dùng cho lệnh cần quyền tạo/sửa bảng.

Đổi tài khoản của cả 2 kết nối sang bookstore_migrate. Mật khẩu lấy từ biến môi trường DB_MIGRATE_PASSWORD hoặc file database/.env.db (không nằm trong .env, nên web lúc chạy không biết mật khẩu này).

python manage.py migrate --settings=bookstore.settings.migrate python manage.py createsuperuser --settings=bookstore.settings.migrate python manage.py test --settings=bookstore.settings.migrate

Không bao giờ chạy runserver/gunicorn bằng file này.

"staff" cũng dùng tài khoản migrate: khi chạy test, "staff" trỏ vào CSDL tạm test_bookstore (TEST MIRROR) mà app_staff không có quyền vào.

**biến `SESSION_DB_ALIAS` | backend/bookstore/settings/migrate.py | chưa đánh dấu**  
Lệnh quản trị và test đọc/ghi bảng phiên bằng kết nối "default" (tài khoản migrate); chỉ web lúc chạy mới dùng kết nối "session" (app_session).

**biến `AUTH_DB_ALIAS` | backend/bookstore/settings/migrate.py | chưa đánh dấu**  
Tương tự: lệnh quản trị (createsuperuser, doi_mat_khau_admin) và test ghi bảng tài khoản bằng "default"; chỉ web lúc chạy mới dùng kết nối "auth" (app_auth).

### `backend/bookstore/settings/prod.py`

**cả file | backend/bookstore/settings/prod.py | chưa đánh dấu**  
Máy chủ thật luôn chạy sau Nginx (deploy/nginx/secure-bookstore.conf). Thiếu danh sách proxy tin cậy thì mọi người dùng mang chung IP của Nginx: khóa đăng nhập lẫn nhau.

### `backend/catalog/admin.py`

**cả file | backend/catalog/admin.py | chưa đánh dấu**  
Nhóm KHÔNG dùng trang /admin/ mặc định của Django cho bảng nghiệp vụ (django.contrib.admin chưa được bật). Trang quản trị tự viết nằm ở app dashboard.

### `backend/catalog/book_services.py`

**class `BookError` | backend/catalog/book_services.py | Claude Opus 5.5**  
#129 – Lỗi nghiệp vụ khi quản lý sách, mang mã lỗi và câu tiếng Việt.

**hàm `clean_isbn` | backend/catalog/book_services.py | Claude Opus 5.5**  
#130 – Chuẩn hóa ISBN (bỏ gạch, khoảng trắng) và kiểm tra chữ số kiểm tra ISBN-10/ISBN-13.

**hàm `_int_in_range` | backend/catalog/book_services.py | Claude Opus 5.5**  
#131 – Đổi giá trị từ form thành số nguyên trong khoảng cho phép, sai thì báo mã lỗi.

**hàm `clean_book_fields` | backend/catalog/book_services.py | Claude Opus 5.5**  
#132 – Chuẩn hóa và kiểm tra các trường thông tin sách trước khi gọi thủ tục.

**hàm `_book_id` | backend/catalog/book_services.py | Claude Opus 5.5**  
#133 – Đổi id sách nhận từ request thành số nguyên, sai kiểu thì coi như không tìm thấy.

**hàm `_call_book` | backend/catalog/book_services.py | Claude Opus 5.5**  
#134 – Gọi thủ tục sách với bảng mã lỗi của sách.

**hàm `list_books` | backend/catalog/book_services.py | Claude Opus 5.5**  
#135 – Danh sách sách cho nhân viên, lọc theo thể loại, tác giả, tên sách, trạng thái bằng ORM.

**hàm `get_book` | backend/catalog/book_services.py | Claude Opus 5.5**  
#136 – Lấy một sách theo id cho form sửa, không có thì báo BOOK_NOT_FOUND.

**hàm `create_book` | backend/catalog/book_services.py | Claude Opus 5.5**  
#137 – Thêm sách bằng sp_book_create kèm tồn kho ban đầu và ảnh bìa tùy chọn; lỗi thì xóa ảnh vừa lưu.

**hàm `update_book` | backend/catalog/book_services.py | Claude Opus 5.5**  
#138 – Sửa thông tin sách bằng sp_book_update: giữ ảnh cũ, thay ảnh mới hoặc bỏ ảnh; chỉ xóa file cũ khi CSDL đã lưu xong.

**hàm `set_book_active` | backend/catalog/book_services.py | Claude Opus 5.5**  
#139 – Ẩn hoặc hiện sách bằng sp_book_set_active.

**hàm `restock_book` | backend/catalog/book_services.py | Claude Opus 5.5**  
#140 – Nhập thêm hàng bằng sp_book_restock, trả tồn kho mới.

**hàm `reduce_book_stock` | backend/catalog/book_services.py | Claude Opus 5.5**  
#141 – Giảm kho ngoại lệ bằng sp_book_reduce_stock, trả tồn kho mới.

**hàm `delete_book` | backend/catalog/book_services.py | Claude Opus 5.5**  
#142 – Xóa hẳn sách bằng sp_book_delete (đang ẩn, chưa có đơn), xong thì xóa file ảnh bìa.

### `backend/catalog/covers.py`

**class `CoverError` | backend/catalog/covers.py | Claude Opus 5.5**  
#146 – Lỗi khi xử lý ảnh bìa upload, mang mã lỗi và câu tiếng Việt.

**hàm `_read_limited` | backend/catalog/covers.py | Claude Opus 5.5**  
#147 – Đọc file upload có giới hạn dung lượng, không tin kích thước client gửi.

**hàm `sanitize_cover` | backend/catalog/covers.py | Claude Opus 5.5**  
#148 – Xác nhận đúng là ảnh JPEG/PNG/WebP thật, chặn ảnh bom giải nén, rồi lưu lại thành WebP sạch metadata.

**hàm `_cover_file` | backend/catalog/covers.py | Claude Opus 5.5**  
#149 – Đường dẫn tuyệt đối của ảnh bìa, chỉ nhận đúng mẫu covers/<uuid>.<đuôi> và phải nằm trong MEDIA_ROOT/covers.

**hàm `save_cover` | backend/catalog/covers.py | Claude Opus 5.5**  
#150 – Kiểm tra và lưu ảnh bìa mới vào MEDIA_ROOT/covers với tên UUID, trả đường dẫn để ghi vào CSDL.

**hàm `delete_cover` | backend/catalog/covers.py | Claude Opus 5.5**  
#151 – Xóa file ảnh bìa đã upload; bỏ qua mọi đường dẫn không đúng mẫu nên không xóa được file khác.

### `backend/catalog/forms.py`

**class `ReviewForm` | backend/catalog/forms.py | Claude Opus 5.5**  
#208 – Form đánh giá sách: chọn 1–5 sao và nội dung tối đa 2000 ký tự; không có ô user hay sách.

### `backend/catalog/models.py`

**cả file | backend/catalog/models.py | chưa đánh dấu**  
Model của app catalog.

Bảng nghiệp vụ truy cập 100% gián tiếp: model ở đây chỉ để ĐỌC qua view MySQL (Meta: managed = False, db_table = "v_..."). Ghi dữ liệu qua services.py → stored procedure. Lược đồ gốc: database/scripts-secure-bookstore.sql

**class `StaffConnectionManager` | backend/catalog/models.py | Claude Opus 5.5**  
#127 – Manager luôn đọc qua kết nối staff, vì chỉ app_staff có quyền SELECT view của nhân viên.

**class `StaffBook` | backend/catalog/models.py | Claude Opus 5.5**  
#128 – Model chỉ đọc view một bảng v_staff_books, trả đường dẫn ảnh bìa hoặc ảnh mặc định.

### `backend/catalog/review_services.py`

**class `ReviewError` | backend/catalog/review_services.py | Claude Opus 5.5**  
#200 – Lỗi nghiệp vụ khi gửi đánh giá, mang mã lỗi và câu tiếng Việt.

**class `MyReview` | backend/catalog/review_services.py | Claude Opus 5.5**  
#201 – Đánh giá của chính khách cho một sách, dùng để điền sẵn form sửa.

**class `PublicReview` | backend/catalog/review_services.py | Claude Opus 5.5**  
#215 – Một đánh giá hiển thị công khai: tên đã che, số sao, nội dung, thời gian, cờ đã sửa.

**hàm `clean_content` | backend/catalog/review_services.py | Claude Opus 5.5**  
#202 – Chuẩn hóa nội dung đánh giá: thống nhất xuống dòng, bỏ ký tự điều khiển và ký tự đảo chiều văn bản, kiểm tra độ dài.

**hàm `_int_in_range` | backend/catalog/review_services.py | Claude Opus 5.5**  
#203 – Đổi điểm và id sách nhận từ request thành số nguyên trong khoảng cho phép.

**hàm `_allow_review` | backend/catalog/review_services.py | Claude Opus 5.5**  
#205 – Giới hạn mỗi khách gửi/sửa tối đa REVIEW_RATE_LIMIT đánh giá trong REVIEW_RATE_WINDOW giây.

**hàm `save_review` | backend/catalog/review_services.py | Claude Opus 5.5**  
#206 – Gửi hoặc sửa đánh giá bằng sp_review_save; user lấy từ phiên đăng nhập, có giới hạn tần suất; trả True nếu là đánh giá mới.

**hàm `get_my_review` | backend/catalog/review_services.py | Claude Opus 5.5**  
#207 – Lấy đánh giá của chính khách cho một sách bằng sp_review_get_mine, chưa có thì trả None.

**hàm `can_write_review` | backend/catalog/review_services.py | Claude Opus 5.5**  
#517 – Hỏi CSDL khách đã nhận cuốn sách này chưa (sp_review_can_write) để quyết định hiện form đánh giá.

**hàm `list_reviews` | backend/catalog/review_services.py | Claude Opus 5.5**  
#216 – Danh sách đánh giá đang hiện của một sách bằng sp_review_list, tên đã được che trong CSDL.

### `backend/catalog/services.py`

**class `Category` | backend/catalog/services.py | Claude Opus 5.5**  
#191 – Một thể loại hiển thị trên bộ lọc của cửa hàng.

**class `BookCard` | backend/catalog/services.py | Claude Opus 5.5**  
#192 – Một thẻ sách cho khách, đúng cột hợp đồng của sp_public_book_list, kèm đường dẫn ảnh bìa hoặc ảnh mặc định.

**hàm `_read` | backend/catalog/services.py | Claude Opus 5.5**  
#193 – Gọi thủ tục đọc của cửa hàng bằng kết nối app_customer, trả mọi dòng của kết quả đầu tiên.

**hàm `list_categories` | backend/catalog/services.py | Claude Opus 5.5**  
#194 – Danh sách thể loại cho bộ lọc, gọi sp_public_category_list.

**hàm `_book_from_row` | backend/catalog/services.py | Claude Opus 5.5**  
#213 – Đổi một dòng của thủ tục đọc sách thành BookCard, thêm tên thể loại nếu có.

**hàm `list_public_books` | backend/catalog/services.py | Claude Opus 5.5**  
#195 – Sách đang bán cho khách, lọc thể loại và từ khóa, gọi sp_public_book_list với tham số truyền riêng.

**hàm `get_public_book` | backend/catalog/services.py | Claude Opus 5.5**  
#214 – Một sách đang bán cho trang chi tiết bằng sp_public_book_get; id sai hoặc sách ẩn trả None.

### `backend/catalog/staff_services.py`

**class `StaffCategory` | backend/catalog/staff_services.py | Claude Opus 5.5**  
#106 – Một dòng thể loại trả về từ sp_category_list, kèm số sách và cờ xóa được.

**class `CategoryError` | backend/catalog/staff_services.py | Claude Opus 5.5**  
#107 – Lỗi nghiệp vụ khi quản lý thể loại, mang mã lỗi và câu tiếng Việt.

**hàm `clean_name` | backend/catalog/staff_services.py | Claude Opus 5.5**  
#108 – Chuẩn hóa tên thể loại: bỏ khoảng trắng thừa, kiểm tra độ dài.

**hàm `make_slug` | backend/catalog/staff_services.py | Claude Opus 5.5**  
#109 – Tạo slug không dấu từ tên tiếng Việt, xử lý riêng chữ đ.

**hàm `_call` | backend/catalog/staff_services.py | Claude Opus 5.5**  
#110 – Gọi một thủ tục qua kết nối staff, đổi lỗi SIGNAL thành exception nghiệp vụ tương ứng.

**hàm `_category_id` | backend/catalog/staff_services.py | Claude Opus 5.5**  
#115 – Đổi id thể loại nhận từ request thành số nguyên, sai kiểu thì coi như không tìm thấy.

**hàm `list_categories` | backend/catalog/staff_services.py | Claude Opus 5.5**  
#111 – Danh sách thể loại cho nhân viên, gọi sp_category_list qua kết nối staff.

**hàm `create_category` | backend/catalog/staff_services.py | Claude Opus 5.5**  
#112 – Thêm thể loại bằng sp_category_create, trả id mới.

**hàm `rename_category` | backend/catalog/staff_services.py | Claude Opus 5.5**  
#113 – Sửa tên thể loại bằng sp_category_rename, slug đổi theo tên.

**hàm `delete_category` | backend/catalog/staff_services.py | Claude Opus 5.5**  
#114 – Xóa thể loại bằng sp_category_delete.

### `backend/catalog/tests/test_book_detail.py`

**class `BookDetailViewTests` | backend/catalog/tests/test_book_detail.py | Claude Opus 5.5**  
#223 – Test trang chi tiết sách và gửi đánh giá: 404 sách ẩn, form theo loại người xem, CSRF, chỉ POST, escape nội dung. Đã viết lại bởi Claude Opus 5.5 khi chỉ cho khách đã nhận sách đánh giá.

**class `ReviewPurchasedOnlyTests` | backend/catalog/tests/test_book_detail.py | Claude Opus 5.5**  
#518 – Test chỉ khách đã nhận sách mới thấy form và gửi được đánh giá; gửi lén bị chặn ở CSDL thì báo lỗi và ghi log.

### `backend/catalog/tests/test_covers.py`

**class `SanitizeCoverTests` | backend/catalog/tests/test_covers.py | Claude Opus 5.5**  
#152 – Test kiểm tra ảnh bìa: nhận ảnh thật, chặn file giả, ảnh bom, file quá lớn, xóa metadata và nội dung cài kèm.

**class `CoverStorageTests` | backend/catalog/tests/test_covers.py | Claude Opus 5.5**  
#153 – Test lưu và xóa file ảnh bìa: tên UUID trong media/covers, không xóa được file ngoài thư mục.

**class `BookCoverFlowTests` | backend/catalog/tests/test_covers.py | Claude Opus 5.5**  
#154 – Test ảnh bìa trong luồng thêm/sửa/xóa sách: dọn file khi CSDL báo lỗi, xóa ảnh cũ khi thay hoặc bỏ.

### `backend/catalog/tests/test_home.py`

**class `HomePageTests` | backend/catalog/tests/test_home.py | Claude Opus 5.5**  
#196 – Test trang chủ: hiển thị sách thật qua service, lọc thể loại, tìm kiếm, đầu vào độc hại, không script inline.

**class `HomePaginationTests` | backend/catalog/tests/test_home.py | Claude Opus 5.5**  
#408 – Test phân trang tủ sách: 12 cuốn mỗi trang, trang sai về trang hợp lệ, link giữ từ khóa và thể loại, dấu ba chấm, ô nhập số trang; danh sách số trang hiện ra.

### `backend/catalog/tests/test_public_catalog.py`

**class `PublicCatalogServiceTests` | backend/catalog/tests/test_public_catalog.py | Claude Opus 5.5**  
#197 – Test service danh mục cho khách: gọi đúng thủ tục bằng kết nối app_customer, tham số truyền riêng, đổi dòng thành BookCard.

**class `PublicBookDetailServiceTests` | backend/catalog/tests/test_public_catalog.py | Claude Opus 5.5**  
#224 – Test lấy một sách cho trang chi tiết: id sai không xuống CSDL, sách ẩn trả None, có tên thể loại.

### `backend/catalog/tests/test_reviews.py`

**class `ReviewInputTests` | backend/catalog/tests/test_reviews.py | Claude Opus 5.5**  
#209 – Test chuẩn hóa nội dung đánh giá, che username và form đánh giá. Đã viết lại bởi Claude Opus 5.5 khi bỏ hàm che username không còn dùng.

**class `SaveReviewTests` | backend/catalog/tests/test_reviews.py | Claude Opus 5.5**  
#210 – Test gửi đánh giá bằng cursor giả: user lấy từ phiên, chặn nhân viên, giới hạn tần suất, đổi lỗi SIGNAL.

### `backend/catalog/tests/test_staff_books.py`

**class `BookFieldTests` | backend/catalog/tests/test_staff_books.py | Claude Opus 5.5**  
#143 – Test chuẩn hóa ISBN, kiểm tra chữ số kiểm tra và các giới hạn thông tin sách.

**class `BookProcedureTests` | backend/catalog/tests/test_staff_books.py | Claude Opus 5.5**  
#144 – Test gọi sáu thủ tục sách bằng cursor giả qua kết nối staff, đổi lỗi SIGNAL thành BookError.

**class `StaffBookReadTests` | backend/catalog/tests/test_staff_books.py | Claude Opus 5.5**  
#145 – Test model sách đọc qua kết nối staff, lọc theo thể loại/tác giả/tên và đường dẫn ảnh bìa.

### `backend/catalog/tests/test_staff_categories.py`

**class `SlugAndNameTests` | backend/catalog/tests/test_staff_categories.py | Claude Opus 5.5**  
#117 – Test tạo slug và chuẩn hóa tên thể loại tiếng Việt.

**class `CategoryProcedureTests` | backend/catalog/tests/test_staff_categories.py | Claude Opus 5.5**  
#118 – Test gọi thủ tục thể loại bằng cursor giả qua kết nối staff, đổi lỗi SIGNAL.

**class `CategoryListTests` | backend/catalog/tests/test_staff_categories.py | Claude Opus 5.5**  
#119 – Test đọc danh sách thể loại qua sp_category_list và lệnh kiểm tra quyền từ chối settings.migrate.

### `backend/catalog/views.py`

**hàm `page_items` | backend/catalog/views.py | Claude Opus 5.5**  
#404 – Danh sách số trang để hiện: trang đầu, trang cuối, trang hiện tại và hai trang kề, chỗ bị bỏ qua thay bằng dấu ba chấm (None).

**hàm `home` | backend/catalog/views.py | Claude Opus 5.5**  
#405 – Trang chủ: tủ sách 12 cuốn mỗi trang (3 hàng x 4 cột trên màn hình ngang), giữ từ khóa và thể loại khi chuyển trang, trang sai về trang gần nhất hợp lệ.

**hàm `_render_detail` | backend/catalog/views.py | Claude Opus 5.5**  
#217 – Dựng trang chi tiết sách: thông tin sách, danh sách đánh giá, form đánh giá theo từng loại người xem. Đã viết lại bởi Claude Opus 5.5 khi chỉ cho khách đã nhận sách đánh giá.

**hàm `book_detail` | backend/catalog/views.py | Claude Opus 5.5**  
#218 – Trang chi tiết sách cho mọi người xem; sách ẩn hoặc không tồn tại trả 404.

**hàm `review_submit` | backend/catalog/views.py | Claude Opus 5.5**  
#219 – Nhận form gửi/sửa đánh giá (chỉ POST, CSRF, khách đã đăng nhập); lỗi thì hiện lại form, thành công thì quay về trang sách. Đã viết lại bởi Claude Opus 5.5 khi chỉ cho khách đã nhận sách đánh giá.

### `backend/core/admin.py`

**cả file | backend/core/admin.py | chưa đánh dấu**  
Nhóm KHÔNG dùng trang /admin/ mặc định của Django cho bảng nghiệp vụ (django.contrib.admin chưa được bật). Trang quản trị tự viết nằm ở app dashboard.

### `backend/core/backup.py`

**class `BackupError` | backend/core/backup.py | Claude Opus 5.5**  
#557 – Lỗi khi sao lưu/khôi phục: sai khóa, file hỏng hoặc bị sửa, mysqldump lỗi, cấu hình thiếu.

**hàm `load_config` | backend/core/backup.py | Claude Opus 5.5**  
#558 – Đọc cấu hình sao lưu: khóa và mật khẩu tài khoản sao lưu chỉ lấy từ database/.env.db (web không đọc file này), thư mục và tiền tố lệnh từ settings.

**class `EncryptingWriter` | backend/core/backup.py | Claude Opus 5.5**  
#559 – Ghi luồng đã mã hóa AES-256-GCM: tiêu đề (mã nhận dạng, phiên bản, nonce ngẫu nhiên) làm dữ liệu xác thực kèm, thẻ xác thực 16 byte ở cuối file.

**hàm `decrypt_file` | backend/core/backup.py | Claude Opus 5.5**  
#560 – Giải mã file sao lưu ra file tạm; chỉ coi là hợp lệ khi thẻ GCM khớp (sai khóa, bị sửa, bị cắt đều bị từ chối), dữ liệu giải mã dở không bao giờ được dùng.

**hàm `expired_backups` | backend/core/backup.py | Claude Opus 5.5**  
#561 – Chọn bản sao lưu cũ hơn số ngày giữ lại theo thời điểm ghi trong tên file (không theo mtime dễ bị đổi); file lạ trong thư mục không bao giờ bị đụng tới.

**hàm `client_command` | backend/core/backup.py | Claude Opus 5.5**  
#562 – Dựng lệnh chạy công cụ MySQL (mysqldump/mysql) qua tiền tố cấu hình (ví dụ docker compose exec): mật khẩu đi qua stdin, không bao giờ nằm trong tham số dòng lệnh.

**hàm `snapshot_counts` | backend/core/backup.py | Claude Opus 5.5**  
#563 – Đếm số dòng từng bảng và số thủ tục/trigger/Event ngay trước khi sao lưu bằng tài khoản sao lưu, ghi vào manifest để kiểm tra khôi phục so sánh.

**hàm `create_backup` | backend/core/backup.py | Claude Opus 5.5**  
#564 – Tạo một bản sao lưu: mysqldump (giao dịch nhất quán, có thủ tục/trigger/Event; bảng phiên chỉ lấy cấu trúc, không lấy dữ liệu) ra file tạm trong thư mục 0700, đóng gói cùng ảnh bìa, file logs/security.log và manifest, nén rồi mã hóa, ghi SHA-256, chép off-site, xóa bản quá hạn.

**class `OpenedBackup` | backend/core/backup.py | Claude Opus 5.5**  
#565 – Mở một bản sao lưu: kiểm tra SHA-256 nếu có, giải mã, đọc manifest, kiểm tra SQL khớp mã băm; chỉ nhận đúng tên thành viên đã biết (SQL, manifest, ảnh bìa, logs/security.log*), thành viên lạ (đường dẫn tuyệt đối, ../, link) bị từ chối.

**hàm `restore_logs` | backend/core/backup.py | Claude Opus 5.5**  
#581 – Khi khôi phục, chép file log bảo mật trong bản sao lưu ra thư mục riêng restored-logs/<tên bản> (0700) để đối chiếu, không bao giờ ghi đè logs/security.log đang chạy.

**hàm `execute_sql_file` | backend/core/backup.py | Claude Opus 5.5**  
#566 – Chạy file SQL của mysqldump trên một kết nối quản trị: tách câu theo DELIMITER như client mysql, mỗi câu chạy nguyên văn (không tham số), báo đúng câu lỗi.

**hàm `log_backup_event` | backend/core/backup.py | Claude Opus 5.5**  
#568 – Ghi nhật ký bảo mật cho lệnh sao lưu/khôi phục chạy trên máy chủ (ip_address = cli), detail chỉ chứa tên file, dung lượng, kết quả – không chứa khóa hay mật khẩu.

### `backend/core/captcha.py`

**class `CaptchaResult` | backend/core/captcha.py | Claude Opus 5.5**  
#432 – Kết quả xác minh CAPTCHA gồm đạt hay không, lý do và mã lỗi của Cloudflare.

**hàm `captcha_enabled` | backend/core/captcha.py | Claude Opus 5.5**  
#433 – Turnstile chỉ bật khi có đủ site key và secret key trong .env.

**hàm `_siteverify` | backend/core/captcha.py | Claude Opus 5.5**  
#434 – Gọi Siteverify của Cloudflare qua HTTPS bằng urllib có sẵn, có timeout và giới hạn kích thước.

**hàm `_check_response` | backend/core/captcha.py | Claude Opus 5.5**  
#435 – Đọc phản hồi Siteverify: chỉ nhận success true, đúng hostname và action (key thử thì bỏ qua hai mục này).

**hàm `verify_captcha` | backend/core/captcha.py | Claude Opus 5.5**  
#436 – Xác minh token Turnstile của request; lỗi mạng không bỏ qua mà từ chối; log không chứa token hay secret. Đã viết lại bởi Claude Opus 5.5 khi đọc IP thật sau Nginx.

**hàm `check_turnstile` | backend/core/captcha.py | Claude Opus 5.5**  
#437 – Cảnh báo khi chạy web mà Turnstile đang tắt hoặc đang dùng key thử của Cloudflare.

### `backend/core/client_ip.py`

**hàm `client_ip` | backend/core/client_ip.py | Claude Opus 5.5**  
#461 – IP thật của client: chỉ tin header X-Real-IP khi request đến từ proxy tin cậy (Nginx), còn lại dùng REMOTE_ADDR; header giả từ client bị bỏ qua.

### `backend/core/crypto.py`

**class `DecryptionError` | backend/core/crypto.py | Claude Opus 5.5**  
#064 – Lỗi khi dữ liệu mã hóa bị sửa, sai khóa hoặc sai định dạng.

**hàm `_aead` | backend/core/crypto.py | Claude Opus 5.5**  
#065 – Đọc khóa AES-256 từ settings, báo lỗi cấu hình nếu sai độ dài.

**hàm `encrypt_field` | backend/core/crypto.py | Claude Opus 5.5**  
#066 – Mã hóa AES-GCM một chuỗi, gắn ngữ cảnh để không đem sang dòng khác được.

**hàm `decrypt_field` | backend/core/crypto.py | Claude Opus 5.5**  
#067 – Giải mã AES-GCM, kiểm tra thẻ xác thực và ngữ cảnh trước khi trả về.

### `backend/core/db_routers.py`

**class `MigrateOnDefaultRouter` | backend/core/db_routers.py | chưa đánh dấu**  
Chỉ cho migrate chạy trên kết nối "default".

Kết nối "staff" trỏ cùng CSDL nhưng bằng tài khoản app_staff (không có quyền tạo bảng). Router này đảm bảo `migrate --database staff` không làm gì. Việc chọn kết nối khi đọc/ghi dữ liệu do code quyết định (.using("staff")).

**class `SessionRouter` | backend/core/db_routers.py | Claude Opus 5.5**  
#448 – Mọi đọc/ghi bảng phiên django_session đi qua kết nối riêng (app_session), app_customer không còn đụng vào phiên.

**class `AccountWriteRouter` | backend/core/db_routers.py | Claude Opus 5.5**  
#456 – Mọi lệnh ghi bảng tài khoản đi qua kết nối riêng (app_auth); app_customer chỉ còn đọc, SQL injection ở trang khác không tạo/sửa được tài khoản.

**class `TwoFactorRouter` | backend/core/db_routers.py | Claude Opus 5.5**  
#479 – Bảng xác thực 2 bước chỉ đọc/ghi qua kết nối "auth" (app_auth); app_customer không có quyền gì trên đó.

**class `LockoutRouter` | backend/core/db_routers.py | Claude Opus 5.5**  
#526 – Bảng khóa đăng nhập của django-axes chỉ đọc/ghi qua kết nối "auth" (app_auth); SQL injection qua app_customer không xóa được trạng thái khóa của ai.

### `backend/core/dbadmin.py`

**cả file | backend/core/dbadmin.py | chưa đánh dấu**  
Hàm dùng chung cho 2 lệnh quản trị CSDL: db_setup và db_apply.

Hai lệnh này đăng nhập MySQL bằng root (hoặc tài khoản quản trị khác) để tạo tài khoản, trigger, cấp quyền. Chúng chạy giống nhau trên Docker (Arch) lẫn MySQL cài thường (Windows), vì chỉ cần kết nối TCP tới DB_HOST:DB_PORT.

Mật khẩu quản trị lấy theo thứ tự: biến môi trường → database/.env.db → hỏi trực tiếp (không hiện ký tự). Không bao giờ in mật khẩu ra màn hình.

**hàm `split_sql` | backend/core/dbadmin.py | chưa đánh dấu**  
Tách file SQL thành từng câu lệnh, hiểu lệnh DELIMITER như client mysql.

Bỏ qua câu chỉ có chú thích. Dùng cho database/02_trigger_thu_tuc.sql và database/03_phan_quyen.sql.

### `backend/core/mail_backends.py`

**class `ReadableConsoleEmailBackend` | backend/core/mail_backends.py | Claude Opus 5.5**  
#033 – In thư ra terminal dạng chữ đọc được thay vì base64 khi chạy máy dev.

### `backend/core/management/commands/db_apply.py`

**cả file | backend/core/management/commands/db_apply.py | chưa đánh dấu**  
python manage.py db_apply – tạo trigger/view/thủ tục rồi cấp quyền.

Chạy bằng tài khoản quản trị (root), SAU khi `migrate` đã tạo bảng (MySQL không cho cấp quyền hay tạo trigger trên bảng chưa có). Chạy lại mỗi khi sửa database/02_trigger_thu_tuc.sql hoặc database/03_phan_quyen.sql.

Thứ tự: 02_trigger_thu_tuc.sql rồi 03_phan_quyen.sql. File được dùng DELIMITER. Mỗi đối tượng tự DROP ... IF EXISTS trước khi tạo, nên chạy lại không lỗi.

Vì sao root làm việc này mà không phải migrate: khi MySQL bật binlog, tạo trigger/thủ tục cần quyền SUPER (hoặc nới lỏng log_bin_trust_function_creators). Nhóm không cấp quyền đó cho tài khoản migrate.

**hàm `apply_payment_simulation` | backend/core/management/commands/db_apply.py | Claude Opus 5.5**  
#529 – Quyền gọi sp_payment_simulate của r_customer đi theo cờ PAYMENT_SIMULATION: bật thì cấp, tắt thì thu hồi, để MySQL cũng chặn khi Django tắt.

### `backend/core/management/commands/db_backup.py`

**class `Command` | backend/core/management/commands/db_backup.py | Claude Opus 5.5**  
#569 – Lệnh tạo bản sao lưu (CSDL trừ dữ liệu phiên, ảnh bìa, log bảo mật): chạy bằng tài khoản chỉ đọc bookstore_backup, in kết quả, ghi log backup_created hoặc backup_failed (nghiêm trọng).

### `backend/core/management/commands/db_backup_export.py`

**class `Command` | backend/core/management/commands/db_backup_export.py | Claude Opus 5.5**  
#570 – Lệnh demo giải mã bản sao lưu ra file .sql chạy được (như seed_data.sql): cảnh báo, bắt gõ xác nhận, file quyền 600 trong thư mục riêng 0700, ghi log mức cảnh báo.

### `backend/core/management/commands/db_backup_verify.py`

**class `Command` | backend/core/management/commands/db_backup_verify.py | Claude Opus 5.5**  
#572 – Lệnh kiểm tra khôi phục: giải mã bản mới nhất (hoặc file chỉ định), khôi phục vào CSDL tạm, tắt Event của bản tạm, so số dòng từng bảng và số thủ tục/trigger/Event với manifest, kiểm tra tài khoản sao lưu chỉ đọc, rồi xóa CSDL tạm.

### `backend/core/management/commands/db_check_grants.py`

**class `Command` | backend/core/management/commands/db_check_grants.py | Claude Opus 5.5**  
#116 – Lệnh kiểm tra phân quyền trên CSDL thật: chạy từng câu bằng app_customer/app_staff, so với kết quả mong đợi. Đã viết lại bởi Claude Opus 5.5 khi thêm app_session.

### `backend/core/management/commands/db_restore.py`

**class `Command` | backend/core/management/commands/db_restore.py | Claude Opus 5.5**  
#571 – Lệnh khôi phục đè lên CSDL: nhận file mã hóa hoặc .sql trần, bắt gõ lại tên CSDL, tự sao lưu bản hiện tại trước, chạy SQL bằng root (bảng phiên được tạo lại rỗng nên mọi người phải đăng nhập lại), trả ảnh bìa, chép log bảo mật trong bản sao lưu ra thư mục riêng, cấp lại quyền bằng db_apply, ghi log.

### `backend/core/management/commands/db_setup.py`

**cả file | backend/core/management/commands/db_setup.py | chưa đánh dấu**  
python manage.py db_setup – tạo CSDL, role và 4 tài khoản MySQL.

Chạy bằng tài khoản quản trị (root), MỘT LẦN khi dựng máy mới, và chạy lại mỗi khi đổi mật khẩu trong .env / database/.env.db (lệnh sẽ đồng bộ mật khẩu). Chạy lại nhiều lần không hỏng gì.

Việc nó làm:

1. Tạo CSDL (utf8mb4) nếu chưa có.
2. Cài component validate_password, đặt chính sách MEDIUM, tối thiểu 12 ký tự.
3. Tạo role r_customer, r_staff, r_session, r_auth (quyền cụ thể cấp sau, bằng db_apply).
4. Tạo/cập nhật app_customer, app_staff, app_session, app_auth, bookstore_migrate theo ĐỊA CHỈ MÀ MYSQL THẤY MÁY NÀY KẾT NỐI TỪ (Docker: 172.28.0.1, cài thường: 127.0.0.1 hoặc localhost), bookstore_definer (khóa đăng nhập) và bookstore_backup (chỉ đọc, chỉ đăng nhập tại chỗ, dùng cho lệnh sao lưu).

**hàm `Command.handle` | backend/core/management/commands/db_setup.py | Claude Opus 5.5**  
#567 – Tạo tài khoản sao lưu bookstore_backup chỉ đăng nhập tại chỗ (localhost, socket trong container), tối đa 2 kết nối; quyền chỉ đọc cấp bằng db_apply.

2. bookstore_definer trước: chủ sở hữu trigger/view/thủ tục, khóa đăng nhập. Mật khẩu ngẫu nhiên, không lưu ở đâu (không ai cần đăng nhập bằng nó).

**hàm `Command._upsert_user` | backend/core/management/commands/db_setup.py | chưa đánh dấu**  
Tạo tài khoản, hoặc đồng bộ lại mật khẩu nếu đã có.

Tên, host, mật khẩu đi qua tham số của MySQLdb (được escape), không nối chuỗi.

### `backend/core/middleware.py`

**class `DbPermissionDeniedMiddleware` | backend/core/middleware.py | Claude Opus 5.5**  
#329 – Middleware ghi db_permission_denied (mức critical) khi MySQL từ chối câu lệnh vì thiếu quyền – dấu hiệu tấn công hoặc lỗi phân quyền; lỗi vẫn đi tiếp thành trang 500.

**hàm `remember_staff_login` | backend/core/middleware.py | Claude Opus 5.5**  
#449 – Ghi giờ đăng nhập của nhân viên vào phiên (phần đã ký, không sửa được từ bảng) để giới hạn thời gian tuyệt đối.

**class `StaffSessionLimitMiddleware` | backend/core/middleware.py | Claude Opus 5.5**  
#450 – Phiên nhân viên quá 1 giờ kể từ lúc đăng nhập thì đăng xuất dù vẫn thao tác; thiếu giờ đăng nhập cũng coi là hết hạn.

**class `InactiveAccountSessionMiddleware` | backend/core/middleware.py | Claude Opus 5.5**  
#524 – Phiên còn ghi người dùng nhưng tài khoản đã bị khóa (hoặc không còn) thì hủy hẳn phiên, không để phiên được gia hạn rồi sống lại khi mở khóa. Đã viết lại bởi Claude Opus 5.5 khi thêm khóa tự động vì giữ kho.

**hàm `auto_lock_message` | backend/core/middleware.py | Claude Opus 5.5**  
#539 – Câu báo tài khoản bị khóa tự động vì giữ kho, kèm giờ mở (giờ Việt Nam).

**hàm `end_other_sessions` | backend/core/middleware.py | Claude Opus 5.5**  
#585 – Đăng nhập xong (sau bước 2 nếu có) thì đẩy mọi phiên khác của tài khoản ra: ghi log đăng xuất lý do new_login_elsewhere và gửi thư báo chủ tài khoản.

**class `ReplacedSessionMiddleware` | backend/core/middleware.py | Claude Opus 5.5**  
#586 – Phiên bị đẩy ra vì tài khoản đăng nhập ở nơi khác: hủy hẳn phiên và báo cho người đang dùng (chỉ giờ đăng nhập mới, không lộ IP).

### `backend/core/migrations/0001_business_schema.py`

**hàm `_statements` | backend/core/migrations/0001_business_schema.py | Claude Opus 5.5**  
#593 – Đọc file SQL gộp toàn bộ bảng nghiệp vụ, tách thành từng câu lệnh (bỏ chú thích, bỏ câu rỗng).

### `backend/core/security_log.py`

**hàm `redact_path` | backend/core/security_log.py | Claude Opus 5.5**  
#519 – Che mã bí mật trong đường dẫn trước khi ghi log (link đặt lại mật khẩu, link đăng ký): phần mã thay bằng "-".

### `backend/core/session_store.py`

**hàm `stored_key` | backend/core/session_store.py | Claude Opus 5.5**  
#445 – Khóa lưu trong bảng phiên là SHA-256 của cookie (cắt 40 ký tự cho vừa cột), đọc bảng không ra cookie dùng được.

**hàm `end_user_sessions` | backend/core/session_store.py | Claude Opus 5.5**  
#523 – Xóa mọi phiên còn hạn của một người dùng (đọc từng dòng bằng đúng khóa đã băm), trả số phiên đã xóa.

**hàm `replace_other_sessions` | backend/core/session_store.py | Claude Opus 5.5**  
#583 – Một tài khoản chỉ một phiên: khi đăng nhập, mọi phiên khác còn hạn của người đó bị thay bằng phiên rỗng chỉ chứa thông báo "đã đăng nhập ở nơi khác" (hết hạn sau 1 giờ); phiên admin đã quá giới hạn 1 giờ thì xóa luôn, không tính.

**class `SessionStore` | backend/core/session_store.py | Claude Opus 5.5**  
#446 – Bộ lưu phiên: bảng chỉ giữ mã băm của cookie, chữ ký session_data gắn với đúng dòng nên chép sang dòng khác là vô hiệu.  
#447 – Đọc một dòng phiên lấy thẳng từ bảng (lệnh quản trị) bằng đúng khóa đã băm của dòng đó.  
#584 – Ký lại dữ liệu cho một dòng phiên lấy thẳng từ bảng, chữ ký gắn đúng khóa đã băm của dòng đó.

### `backend/core/templatetags/bookstore.py`

**hàm `stars` | backend/core/templatetags/bookstore.py | chưa đánh dấu**  
Điểm 0–5 → danh sách 5 tên icon: "star" (đầy), "star-half", "star-empty".

Làm tròn tới 0,5. Ví dụ 4.3 → 4,5 sao → [star × 4, star-half].

### `backend/core/tests/session_helpers.py`

**hàm `open_extra_session` | backend/core/tests/session_helpers.py | Claude Opus 5.5**  
#589 – Test: tạo thẳng một phiên thứ hai cho người dùng (không qua login, nên không bị luật một phiên đẩy ra) để thử các hàm xóa phiên.

### `backend/core/tests/test_account_router.py`

**class `AccountWriteRouterTests` | backend/core/tests/test_account_router.py | Claude Opus 5.5**  
#460 – Test router ghi tài khoản: ghi User đi qua "auth", đọc vẫn "default", bảng khác không đổi kết nối.

### `backend/core/tests/test_backup.py`

**class `BackupCryptoTests` | backend/core/tests/test_backup.py | Claude Opus 5.5**  
#577 – Test mã hóa bản sao lưu: giải mã đúng khi đúng khóa; sai khóa, sửa 1 byte, cắt cụt, sai mã nhận dạng đều bị từ chối và không để lại dữ liệu dùng được.

**class `OpenBackupTests` | backend/core/tests/test_backup.py | Claude Opus 5.5**  
#578 – Test mở gói sao lưu: SHA-256 đi kèm phải khớp, SQL phải khớp manifest, thành phần lạ (../, đường dẫn tuyệt đối, tên ảnh không phải UUID) bị từ chối.

**class `BackupHelpersTests` | backend/core/tests/test_backup.py | Claude Opus 5.5**  
#579 – Test giữ lại 1 năm theo tên file, so số dòng, và lệnh gọi mysqldump: mật khẩu chỉ đi qua stdin, không nằm trong tham số, tiền tố docker được giữ nguyên.

**class `BackupCommandTests` | backend/core/tests/test_backup.py | Claude Opus 5.5**  
#580 – Test lệnh quản trị: xuất .sql và khôi phục đều hủy khi gõ xác nhận sai (không giải mã, không đụng CSDL); sao lưu lỗi ghi backup_failed mức nghiêm trọng.

**class `SessionAndLogTests` | backend/core/tests/test_backup.py | Claude Opus 5.5**  
#582 – Test bản sao lưu bỏ dữ liệu bảng phiên (chỉ lấy cấu trúc, manifest ghi 0 dòng) và kèm logs/security.log*; khôi phục chép log ra thư mục riêng, không ghi đè log đang chạy.

### `backend/core/tests/test_captcha.py`

**class `VerifyCaptchaTests` | backend/core/tests/test_captcha.py | Claude Opus 5.5**  
#442 – Test xác minh Turnstile với Siteverify giả: đạt, thiếu, bị từ chối, dùng lại, sai hostname/action, timeout.

**class `TurnstileCheckTests` | backend/core/tests/test_captcha.py | Claude Opus 5.5**  
#443 – Test cảnh báo khi chạy web với Turnstile tắt hoặc dùng key thử.

### `backend/core/tests/test_client_ip.py`

**class `ClientIpTests` | backend/core/tests/test_client_ip.py | Claude Opus 5.5**  
#462 – Test đọc IP thật: chỉ tin X-Real-IP khi đến từ proxy tin cậy, header giả hoặc sai định dạng bị bỏ qua.

**class `LockoutBehindProxyTests` | backend/core/tests/test_client_ip.py | Claude Opus 5.5**  
#463 – Tái hiện phát hiện số 12: sau Nginx kẻ tấn công khóa đăng nhập của admin; sau khi sửa chỉ IP kẻ tấn công bị khóa, log ghi IP thật. Đã viết lại bởi Claude Opus 5.5 khi thêm xác thực 2 bước.

### `backend/core/tests/test_crypto.py`

**class `FieldCryptoTests` | backend/core/tests/test_crypto.py | Claude Opus 5.5**  
#082 – Test mã hóa AES-GCM: giải mã đúng, nonce ngẫu nhiên, chặn sửa dữ liệu, sai khóa, sai ngữ cảnh.

### `backend/core/tests/test_inactive_session.py`

**class `LockedAccountSessionTests` | backend/core/tests/test_inactive_session.py | Claude Opus 5.5**  
#525 – Test tái hiện lỗi phiên của tài khoản bị khóa sống lại khi mở khóa, và test hàm xóa mọi phiên của một người dùng. Đã viết lại bởi Claude Opus 5.5 khi thêm luật một tài khoản một phiên.

### `backend/core/tests/test_lockout_router.py`

**class `LockoutRouterTests` | backend/core/tests/test_lockout_router.py | Claude Opus 5.5**  
#530 – Test bảng django-axes đi qua kết nối "auth" và quyền gọi sp_payment_simulate đi theo cờ PAYMENT_SIMULATION.

### `backend/core/tests/test_security_log.py`

**class `RedactPathTests` | backend/core/tests/test_security_log.py | Claude Opus 5.5**  
#522 – Test che mã bí mật trong đường dẫn của nhật ký (file log và core_securityevent), kể cả khi view quên truyền path.

### `backend/core/tests/test_session_store.py`

**class `HashedSessionStoreTests` | backend/core/tests/test_session_store.py | Claude Opus 5.5**  
#453 – Test bộ lưu phiên: bảng chỉ có mã băm cookie, chép session_data sang dòng khác bị từ chối, xóa/kiểm tra tồn tại theo mã băm.

**class `SessionRouterTests` | backend/core/tests/test_session_store.py | Claude Opus 5.5**  
#454 – Test router: bảng phiên đi theo SESSION_DB_ALIAS, bảng khác không bị đổi kết nối.

**class `StaffSessionLimitTests` | backend/core/tests/test_session_store.py | Claude Opus 5.5**  
#455 – Test giới hạn 1 giờ cho phiên nhân viên: quá giờ thì đăng xuất kèm log lý do, khách không bị giới hạn. Đã viết lại bởi Claude Opus 5.5 khi thêm xác thực 2 bước.

### `backend/core/validators.py`

**hàm `parse_positive_int` | backend/core/validators.py | chưa đánh dấu**  
Chuỗi chỉ gồm chữ số (tối đa max_digits ký tự) → số nguyên dương; còn lại → None.

Dùng cho tham số trên URL như ?category=, ?page=. Không dùng int() trần vì int(" 12 "), int("+12"), int("١٢") (chữ số Ả Rập) đều "thành công".

### `backend/core/views.py`

**cả file | backend/core/views.py | chưa đánh dấu**  
View dùng chung: trang lỗi tùy chỉnh và trang lỗi CSRF.

Các handler này chỉ có tác dụng khi DEBUG = False (môi trường prod). Khi DEBUG = True, Django hiện trang lỗi chi tiết để lập trình viên gỡ lỗi. Lỗi CSRF được ghi vào core_securityevent (csrf_failed) và security.log.

**hàm `server_error` | backend/core/views.py | chưa đánh dấu**  
Không dùng render(request, ...): lỗi 500 có thể do CSDL, context processor đụng tới user/session có thể gây lỗi tiếp. Render template không cần request.

**hàm `csrf_failure` | backend/core/views.py | Claude Opus 5.5**  
#326 – Trang lỗi CSRF ghi sự kiện csrf_failed (lý do của Django chỉ vào log, không hiện cho người dùng).

### `backend/dashboard/account_services.py`

**class `AccountError` | backend/dashboard/account_services.py | Claude Opus 5.5**  
#297 – Lỗi nghiệp vụ khi quản lý tài khoản khách, mang mã lỗi và câu tiếng Việt.

**hàm `mask_email` | backend/dashboard/account_services.py | Claude Opus 5.5**  
#298 – Che bớt email (giữ ký tự đầu, cuối của phần trước @ và tên miền) và SĐT (giữ 3 số đầu, 3 số cuối).

**class `StaffAccount` | backend/dashboard/account_services.py | Claude Opus 5.5**  
#299 – Một tài khoản khách cho trang admin: trạng thái, email/SĐT bản đầy đủ và bản che, ngày tạo, lần đăng nhập cuối. Đã viết lại bởi Claude Opus 5.5 khi khóa tự động vì giữ kho cũng tính là đang khóa (admin mở được).

**hàm `_call` | backend/dashboard/account_services.py | Claude Opus 5.5**  
#300 – Gọi thủ tục quản lý tài khoản qua kết nối staff, đổi lỗi SIGNAL thành AccountError, lỗi khác (thiếu quyền...) để nguyên.

**hàm `list_accounts` | backend/dashboard/account_services.py | Claude Opus 5.5**  
#301 – Danh sách tài khoản khách qua sp_staff_account_list, lọc trạng thái và username (kiểm tra trước khi xuống CSDL).

**hàm `get_account` | backend/dashboard/account_services.py | Claude Opus 5.5**  
#302 – Một tài khoản khách qua sp_staff_account_get cho trang xác nhận khóa/mở khóa.

**hàm `lock_account` | backend/dashboard/account_services.py | Claude Opus 5.5**  
#303 – Khóa và mở khóa tài khoản khách qua sp_staff_account_lock/unlock, kèm lý do ghi vào nhật ký. Đã viết lại bởi Claude Opus 5.5 khi đăng xuất mọi phiên của tài khoản bị khóa.

### `backend/dashboard/account_views.py`

**hàm `_account_page` | backend/dashboard/account_views.py | Claude Opus 5.5**  
#306 – Dữ liệu chung cho trang danh sách tài khoản: lọc từ GET, gọi thủ tục, phân trang.

**hàm `accounts` | backend/dashboard/account_views.py | Claude Opus 5.5**  
#307 – Trang quản lý tài khoản: danh sách khách, email và SĐT đã che, lọc theo trạng thái và username.

**hàm `accounts_full` | backend/dashboard/account_views.py | Claude Opus 5.5**  
#308 – Xem email và SĐT đầy đủ của khách: cần xác thực lại, ghi log sensitive_data_viewed kèm bộ lọc và số dòng.

**hàm `_account_action` | backend/dashboard/account_views.py | Claude Opus 5.5**  
#309 – Khóa/mở khóa tài khoản: mỗi lần đều nhập lý do và mật khẩu admin ngay trong form (xác thực một lần, không dựa vào xác thực trước đó), ghi log bước xác thực. Đã viết lại bởi Claude Opus 5.5 khi đăng xuất phiên của tài khoản bị khóa.

### `backend/dashboard/admin.py`

**cả file | backend/dashboard/admin.py | chưa đánh dấu**  
Nhóm KHÔNG dùng trang /admin/ mặc định của Django cho bảng nghiệp vụ (django.contrib.admin chưa được bật). Trang quản trị tự viết nằm ở app dashboard.

### `backend/dashboard/catalog_forms.py`

**hàm `attach_error` | backend/dashboard/catalog_forms.py | Claude Opus 5.5**  
#155 – Gắn lỗi nghiệp vụ từ service vào đúng ô của form, không có ô phù hợp thì thành lỗi chung.

**class `BookForm` | backend/dashboard/catalog_forms.py | Claude Opus 5.5**  
#156 – Form thông tin sách dùng chung cho thêm và sửa: kiểm tra độ dài, khoảng giá, ISBN, thể loại, dung lượng ảnh.

**class `BookCreateForm` | backend/dashboard/catalog_forms.py | Claude Opus 5.5**  
#157 – Form thêm sách: thêm ô tồn kho ban đầu 0 đến 10.000.

**class `BookEditForm` | backend/dashboard/catalog_forms.py | Claude Opus 5.5**  
#158 – Form sửa sách: thêm ô bỏ ảnh bìa, không cho vừa chọn ảnh mới vừa bỏ ảnh.

**class `StockForm` | backend/dashboard/catalog_forms.py | Claude Opus 5.5**  
#159 – Form số lượng nhập kho hoặc giảm kho, 1 đến 10.000 cuốn.

**class `CategoryForm` | backend/dashboard/catalog_forms.py | Claude Opus 5.5**  
#160 – Form tên thể loại dùng cho thêm và sửa tên.

### `backend/dashboard/catalog_views.py`

**hàm `_log_upload_rejected` | backend/dashboard/catalog_views.py | Claude Opus 5.5**  
#327 – Ghi sự kiện upload_rejected khi ảnh bìa bị từ chối (chỉ mã lỗi, không ghi tên hay nội dung file).

**hàm `_book_or_404` | backend/dashboard/catalog_views.py | Claude Opus 5.5**  
#161 – Lấy sách theo id trong URL, không có thì trả 404.

**hàm `books` | backend/dashboard/catalog_views.py | Claude Opus 5.5**  
#162 – Trang danh sách sách: lọc theo tên, tác giả, thể loại, trạng thái, phân trang, cảnh báo tồn kho thấp.

**hàm `book_create` | backend/dashboard/catalog_views.py | Claude Opus 5.5**  
#163 – Trang thêm sách: form thông tin, tồn kho ban đầu, ảnh bìa; lỗi service gắn vào đúng ô.

**hàm `book_edit` | backend/dashboard/catalog_views.py | Claude Opus 5.5**  
#164 – Trang sửa sách: form thông tin và ảnh, kèm khung tồn kho, trạng thái và nút xóa.

**hàm `_change_stock` | backend/dashboard/catalog_views.py | Claude Opus 5.5**  
#165 – Xử lý chung form nhập kho/giảm kho: kiểm tra số lượng, gọi service, báo kết quả rồi quay lại trang sửa.

**hàm `book_restock` | backend/dashboard/catalog_views.py | Claude Opus 5.5**  
#166 – Nhập thêm hàng cho một sách (POST).

**hàm `book_reduce` | backend/dashboard/catalog_views.py | Claude Opus 5.5**  
#167 – Giảm kho ngoại lệ cho một sách (POST).

**hàm `book_toggle` | backend/dashboard/catalog_views.py | Claude Opus 5.5**  
#168 – Ẩn hoặc hiện sách theo trạng thái gửi lên rõ ràng, không đảo trạng thái mù.

**hàm `book_delete` | backend/dashboard/catalog_views.py | Claude Opus 5.5**  
#169 – Xóa hẳn sách: cần xác thực lại, có trang xác nhận, chỉ xóa sách đang ẩn.

**hàm `categories` | backend/dashboard/catalog_views.py | Claude Opus 5.5**  
#170 – Trang thể loại: danh sách kèm số sách, form thêm, form sửa tên từng dòng.

**hàm `category_rename` | backend/dashboard/catalog_views.py | Claude Opus 5.5**  
#171 – Sửa tên thể loại (POST), báo lỗi trùng tên hoặc không tồn tại.

**hàm `category_delete` | backend/dashboard/catalog_views.py | Claude Opus 5.5**  
#172 – Xóa thể loại: cần xác thực lại, có trang xác nhận, chỉ xóa thể loại không còn sách.

### `backend/dashboard/forms.py`

**class `ReauthForm` | backend/dashboard/forms.py | Claude Opus 5.5**  
#551 – Form xác thực lại của admin: chỉ ô mật khẩu, kiểm với chính admin đang đăng nhập (T2.2).

**class `StaffProfileUpdateForm` | backend/dashboard/forms.py | Claude Opus 5.5**  
#094 – Form sửa họ, tên, SĐT của nhân viên; ô SĐT luôn trống, để trống là giữ số cũ.

**class `AccountFilterForm` | backend/dashboard/forms.py | Claude Opus 5.5**  
#304 – Bộ lọc danh sách tài khoản khách: trạng thái (giá trị cố định) và username (bỏ ký tự điều khiển, tối đa 150 ký tự). Đã viết lại bởi Claude Opus 5.5 khi thêm trạng thái khóa tự động vì giữ kho.

**class `AccountActionForm` | backend/dashboard/forms.py | Claude Opus 5.5**  
#305 – Form khóa/mở khóa: lý do 5–255 ký tự và nhập lại tài khoản + mật khẩu admin, kiểm tra riêng cho đúng lần gửi này (không dùng lại xác thực cũ). Đã viết lại bởi Claude Opus 5.5 khi bỏ ô tên đăng nhập (T2.2).

**class `_LogDateRangeForm` | backend/dashboard/forms.py | Claude Opus 5.5**  
#336 – Phần lọc ngày dùng chung cho hai tab nhật ký: từ ngày/đến ngày theo giờ Việt Nam, đổi thành khoảng [bắt đầu, kết thúc) có múi giờ, tối đa 400 ngày.

**class `SecurityLogFilterForm` | backend/dashboard/forms.py | Claude Opus 5.5**  
#337 – Bộ lọc tab nhật ký bảo mật: loại sự kiện, mức độ (danh sách cố định), khoảng ngày, username/IP.

**class `AuditLogFilterForm` | backend/dashboard/forms.py | Claude Opus 5.5**  
#338 – Bộ lọc tab nhật ký thay đổi dữ liệu: bảng, hành động (danh sách cố định), khoảng ngày, id bản ghi.

**class `OrderFilterForm` | backend/dashboard/forms.py | Claude Opus 5.5**  
#382 – Bộ lọc trang quản lý đơn: chỉ chọn trong danh sách trạng thái cố định (hoặc Cần xử lý).

### `backend/dashboard/log_services.py`

**class `LogError` | backend/dashboard/log_services.py | Claude Opus 5.5**  
#330 – Lỗi khi đọc nhật ký hệ thống, mang mã lỗi và câu tiếng Việt.

**class `SecurityEventRow` | backend/dashboard/log_services.py | Claude Opus 5.5**  
#331 – Một dòng nhật ký bảo mật cho template: nhãn tiếng Việt, mức độ, người dùng, IP, đường dẫn, chi tiết dạng cặp khóa–giá trị.

**class `AuditRow` | backend/dashboard/log_services.py | Claude Opus 5.5**  
#332 – Một dòng nhật ký thay đổi dữ liệu: bảng, hành động, danh sách thay đổi cũ → mới, nguồn (khách/hệ thống/quản trị), người thực hiện.

**hàm `_read` | backend/dashboard/log_services.py | Claude Opus 5.5**  
#333 – Gọi thủ tục đọc nhật ký qua kết nối staff: bộ kết quả 1 là tổng số dòng, bộ 2 là trang dữ liệu; đổi lỗi SIGNAL thành LogError.

**hàm `list_security_events` | backend/dashboard/log_services.py | Claude Opus 5.5**  
#334 – Đọc một trang nhật ký bảo mật qua sp_staff_security_events, thời gian lọc đổi về UTC.

**hàm `list_audit_log` | backend/dashboard/log_services.py | Claude Opus 5.5**  
#335 – Đọc một trang nhật ký thay đổi dữ liệu qua sp_staff_audit_log.

### `backend/dashboard/log_views.py`

**hàm `_pager` | backend/dashboard/log_views.py | Claude Opus 5.5**  
#339 – Dữ liệu phân trang cho trang nhật ký: dùng Paginator trên tổng số dòng thủ tục trả về, giữ bộ lọc trong link trang.

**hàm `logs` | backend/dashboard/log_views.py | Claude Opus 5.5**  
#340 – Tab nhật ký bảo mật: cần xác thực lại, lọc loại/mức độ/ngày/username-IP, mỗi lần xem ghi log.

**hàm `logs_audit` | backend/dashboard/log_views.py | Claude Opus 5.5**  
#341 – Tab nhật ký thay đổi dữ liệu: cần xác thực lại, lọc bảng/hành động/ngày/id bản ghi, mỗi lần xem ghi log.

### `backend/dashboard/models.py`

**cả file | backend/dashboard/models.py | chưa đánh dấu**  
Model của app dashboard.

Bảng nghiệp vụ truy cập 100% gián tiếp: model ở đây chỉ để ĐỌC qua view MySQL (Meta: managed = False, db_table = "v_..."). Ghi dữ liệu qua services.py → stored procedure. Lược đồ gốc: database/scripts-secure-bookstore.sql

### `backend/dashboard/order_services.py`

**class `OrderAdminError` | backend/dashboard/order_services.py | Claude Opus 5.5**  
#376 – Lỗi nghiệp vụ khi admin quản lý đơn hàng, mang mã lỗi và câu tiếng Việt.

**class `StaffOrderRow` | backend/dashboard/order_services.py | Claude Opus 5.5**  
#377 – Một dòng đơn trên trang quản lý đơn: mã, username, trạng thái, tổng tiền, ngày đặt, số cuốn và bước tiếp theo admin được bấm.

**class `StaffOrderDetail` | backend/dashboard/order_services.py | Claude Opus 5.5**  
#378 – Chi tiết một đơn cho admin: người đặt, tiền, thông tin giao hàng đã giải mã, giao dịch thanh toán, danh sách sách.

**hàm `list_orders` | backend/dashboard/order_services.py | Claude Opus 5.5**  
#379 – Đọc một trang đơn qua sp_staff_order_list (kết nối staff), bộ lọc sai bị chặn trước khi xuống CSDL, trả tổng số và danh sách.

**hàm `get_order` | backend/dashboard/order_services.py | Claude Opus 5.5**  
#380 – Đọc chi tiết một đơn qua sp_staff_order_get, giải mã SĐT/địa chỉ giao hàng bằng ngữ cảnh gắn chủ đơn; mã đơn sai mẫu không xuống CSDL.

**hàm `advance_order` | backend/dashboard/order_services.py | Claude Opus 5.5**  
#381 – Chuyển đơn đúng một bước bằng thủ tục riêng của từng bước (tiếp nhận/đóng gói/giao hàng/đã giao); tên bước và mã đơn kiểm tra trước khi xuống CSDL.

### `backend/dashboard/order_views.py`

**hàm `orders` | backend/dashboard/order_views.py | Claude Opus 5.5**  
#383 – Trang quản lý đơn hàng: lọc theo trạng thái, bảng đơn đơn giản (không có thông tin giao hàng), nút bước tiếp theo, phân trang.

**hàm `order_detail` | backend/dashboard/order_views.py | Claude Opus 5.5**  
#384 – Trang chi tiết đơn cho admin: cần xác thực lại, hiện SĐT/địa chỉ giao hàng, mỗi lần xem ghi log sensitive_data_viewed; mã sai hoặc không có trả 404.

**hàm `order_advance` | backend/dashboard/order_views.py | Claude Opus 5.5**  
#385 – Nhận nút chuyển trạng thái đơn (chỉ POST, CSRF, sau bước xác nhận bằng details): mỗi bước một URL, sai bước báo lỗi, mã không có trả 404, xong quay lại trang đang xem.

### `backend/dashboard/overview_services.py`

**class `OverviewError` | backend/dashboard/overview_services.py | Claude Opus 5.5**  
#395 – Lỗi nghiệp vụ khi đọc trang tổng quan, mang mã lỗi và câu tiếng Việt.

**class `BackupStatus` | backend/dashboard/overview_services.py | Claude Opus 5.5**  
#574 – Trạng thái sao lưu cho Tổng quan: lần thành công, lần lỗi, lần kiểm tra khôi phục gần nhất; cảnh báo khi lỗi mới hơn thành công, chưa từng sao lưu hoặc bản mới nhất cũ hơn 7 ngày. Đã viết lại bởi Claude Opus 5.5 khi bỏ thuộc tính không dùng.

**class `Overview` | backend/dashboard/overview_services.py | Claude Opus 5.5**  
#396 – Số liệu trang tổng quan: đơn cần xử lý theo bước, đơn mới/hủy hôm nay, doanh thu, kho, bảo mật.

**hàm `period_starts` | backend/dashboard/overview_services.py | Claude Opus 5.5**  
#397 – Tính mốc đầu ngày hôm nay, đầu 7 ngày gần nhất (gồm hôm nay) và đầu tháng theo giờ Việt Nam rồi đổi về UTC không múi giờ để truyền xuống thủ tục.

**hàm `get_overview` | backend/dashboard/overview_services.py | Claude Opus 5.5**  
#398 – Đọc số liệu tổng quan bằng 3 thủ tục (đơn và doanh thu, kho, bảo mật) qua kết nối staff, ngưỡng sắp hết lấy từ LOW_STOCK_THRESHOLD. Đã viết lại bởi Claude Opus 5.5 khi thêm thủ tục trạng thái sao lưu.

### `backend/dashboard/services.py`

**cả file | backend/dashboard/services.py | chưa đánh dấu**  
Logic nghiệp vụ của app dashboard.

Mọi thao tác GHI dữ liệu nghiệp vụ đi qua đây và gọi stored procedure, ví dụ:

from django.db import connection # kết nối "default" = app_customer # với dashboard: from django.db import connections; connections["staff"]

with connection.cursor() as cur: cur.callproc("sp_ten_thu_tuc", [tham_so_1, tham_so_2]) # tham số truyền riêng, KHÔNG nối chuỗi row = cur.fetchone()

**hàm `update_staff_profile` | backend/dashboard/services.py | Claude Opus 5.5**  
#095 – Lưu họ, tên, SĐT của nhân viên bằng kết nối staff, chỉ ghi cột thay đổi, log tên cột.

### `backend/dashboard/tests/test_accounts.py`

**class `MaskingTests` | backend/dashboard/tests/test_accounts.py | Claude Opus 5.5**  
#313 – Test che email/SĐT và nhãn trạng thái tài khoản.

**class `AccountServiceTests` | backend/dashboard/tests/test_accounts.py | Claude Opus 5.5**  
#314 – Test service tài khoản bằng cursor giả: tham số đúng thứ tự, ngưỡng axes từ settings, giải mã SĐT đúng ngữ cảnh, chặn đầu vào sai, đổi lỗi SIGNAL. Đã viết lại bởi Claude Opus 5.5 khi khóa tài khoản đăng xuất mọi phiên.

**class `AccountViewTests` | backend/dashboard/tests/test_accounts.py | Claude Opus 5.5**  
#315 – Test trang quản lý tài khoản: chỉ admin, email/SĐT che mặc định, bản đầy đủ cần xác thực lại và ghi log, khóa/mở khóa luôn đòi nhập mật khẩu dù vừa xác thực, CSRF. Đã viết lại bởi Claude Opus 5.5 khi khóa tài khoản đăng xuất mọi phiên.

### `backend/dashboard/tests/test_catalog_views.py`

**class `CatalogViewTestBase` | backend/dashboard/tests/test_catalog_views.py | Claude Opus 5.5**  
#182 – Khung test trang kho sách: tài khoản admin, giả lập service, đánh dấu đã xác thực lại.

**class `CatalogAccessTests` | backend/dashboard/tests/test_catalog_views.py | Claude Opus 5.5**  
#183 – Test phân quyền trang kho sách: ẩn danh phải đăng nhập, khách bị 403, POST thiếu CSRF bị chặn, GET không đổi dữ liệu.

**class `BookListViewTests` | backend/dashboard/tests/test_catalog_views.py | Claude Opus 5.5**  
#184 – Test trang danh sách sách: truyền bộ lọc, bỏ qua giá trị lạ, nhãn tồn kho, escape dữ liệu.

**class `BookFormViewTests` | backend/dashboard/tests/test_catalog_views.py | Claude Opus 5.5**  
#185 – Test thêm và sửa sách: gửi dữ liệu sạch, ảnh, gắn lỗi service vào đúng ô, 404 khi không có sách.

**class `BookStockAndStatusTests` | backend/dashboard/tests/test_catalog_views.py | Claude Opus 5.5**  
#186 – Test nhập kho, giảm kho, ẩn hiện: chỉ POST, kiểm tra số lượng, trạng thái rõ ràng, báo lỗi service.

**class `DeleteFlowTests` | backend/dashboard/tests/test_catalog_views.py | Claude Opus 5.5**  
#187 – Test xóa sách và xóa thể loại: bắt buộc xác thực lại, có trang xác nhận, chặn khi sách đang hiện hoặc thể loại còn sách.

**class `CategoryViewTests` | backend/dashboard/tests/test_catalog_views.py | Claude Opus 5.5**  
#188 – Test trang thể loại: thêm, báo trùng tên đúng ô, đổi tên.

### `backend/dashboard/tests/test_logs.py`

**class `LogRowTests` | backend/dashboard/tests/test_logs.py | Claude Opus 5.5**  
#344 – Test dữ liệu nhật ký: nhãn tiếng Việt, danh sách thay đổi cũ → mới, nguồn, đọc JSON lỗi không làm hỏng trang.

**class `LogServiceTests` | backend/dashboard/tests/test_logs.py | Claude Opus 5.5**  
#345 – Test service đọc nhật ký bằng cursor giả: tham số đúng thứ tự, thời gian đổi về UTC, phân trang có trần, đổi lỗi SIGNAL, lỗi quyền để nguyên.

**class `LogFilterFormTests` | backend/dashboard/tests/test_logs.py | Claude Opus 5.5**  
#346 – Test bộ lọc nhật ký: loại/mức độ chỉ nhận giá trị cố định, ngày theo giờ Việt Nam đổi thành khoảng có múi giờ, chặn khoảng ngược và quá 400 ngày.

**class `LogViewTests` | backend/dashboard/tests/test_logs.py | Claude Opus 5.5**  
#347 – Test trang nhật ký: chỉ admin, bắt buộc xác thực lại, mỗi lần xem ghi log, lọc chuyển đúng xuống service, bộ lọc sai không gọi CSDL.

**class `NewSecurityEventTests` | backend/dashboard/tests/test_logs.py | Claude Opus 5.5**  
#348 – Test 4 log bổ sung: CSRF, MySQL từ chối quyền (middleware), nghi IDOR khi mở đơn người khác, mã đơn rác không ghi.

### `backend/dashboard/tests/test_orders.py`

**class `OrderAdminServiceTests` | backend/dashboard/tests/test_orders.py | Claude Opus 5.5**  
#390 – Test service quản lý đơn bằng cursor giả: bộ lọc/mã đơn/tên bước sai không xuống CSDL, gọi đúng thủ tục từng bước qua kết nối staff, giải mã thông tin giao hàng, đổi lỗi SIGNAL, nút bước tiếp theo theo trạng thái.

**class `OrderAdminViewTests` | backend/dashboard/tests/test_orders.py | Claude Opus 5.5**  
#391 – Test view quản lý đơn: chỉ nhân viên, danh sách không có thông tin giao hàng, chi tiết cần xác thực lại và ghi log, nút chuyển bước chỉ POST + CSRF, sai bước báo lỗi, mã không có trả 404, chỉ quay lại trang trong mục đơn hàng.

### `backend/dashboard/tests/test_overview.py`

**class `OverviewServiceTests` | backend/dashboard/tests/test_overview.py | Claude Opus 5.5**  
#402 – Test service tổng quan: mốc ngày/7 ngày/tháng theo giờ Việt Nam đổi về UTC, gọi đúng 3 thủ tục qua kết nối staff với ngưỡng sắp hết từ settings, đọc nhiều bộ kết quả, đổi lỗi SIGNAL.

**class `OverviewViewTests` | backend/dashboard/tests/test_overview.py | Claude Opus 5.5**  
#403 – Test trang Tổng quan: chỉ nhân viên, hiện các nhóm số liệu và link lọc sẵn, thẻ nghiêm trọng tô đỏ khi có sự kiện, không lưu cache, lỗi nghiệp vụ hiện thông báo. Đã viết lại bởi Claude Opus 5.5 khi bỏ thuộc tính không dùng.

### `backend/dashboard/tests/test_profile.py`

**class `StaffProfileTests` | backend/dashboard/tests/test_profile.py | Claude Opus 5.5**  
#046 – Test trang thông tin nhân viên: giấu email, hiện sau xác thực lại, ghi log. Đã viết lại bởi Claude Opus 5.5 khi bỏ ô tên đăng nhập ở xác thực lại (T2.2).

### `backend/dashboard/tests/test_profile_update.py`

**class `StaffProfileUpdateTests` | backend/dashboard/tests/test_profile_update.py | Claude Opus 5.5**  
#100 – Test nhân viên cập nhật họ, tên, SĐT: xác thực lại, không lộ SĐT cũ, để trống giữ số, chặn mass assignment.

### `backend/dashboard/views.py`

**hàm `index` | backend/dashboard/views.py | Claude Opus 5.5**  
#399 – Trang Tổng quan: báo cáo cơ bản đọc bằng 3 thủ tục, không lưu cache, chỉ có con số nên không bắt xác thực lại.

**hàm `profile` | backend/dashboard/views.py | Claude Opus 5.5**  
#037 – Trang thông tin của nhân viên, mặc định không gửi email và SĐT.

**hàm `profile_contact` | backend/dashboard/views.py | Claude Opus 5.5**  
#038 – Hiện email và SĐT của chính nhân viên sau khi xác thực lại, có ghi log.

**hàm `profile_update` | backend/dashboard/views.py | Claude Opus 5.5**  
#096 – Nhân viên sửa họ, tên, SĐT của chính mình sau khi xác thực lại, không hiện SĐT cũ.

### `backend/orders/admin.py`

**cả file | backend/orders/admin.py | chưa đánh dấu**  
Nhóm KHÔNG dùng trang /admin/ mặc định của Django cho bảng nghiệp vụ (django.contrib.admin chưa được bật). Trang quản trị tự viết nằm ở app dashboard.

### `backend/orders/cart_services.py`

**class `CartError` | backend/orders/cart_services.py | Claude Opus 5.5**  
#227 – Lỗi nghiệp vụ khi thêm vào giỏ, mang mã lỗi và câu tiếng Việt.

**hàm `_int_in_range` | backend/orders/cart_services.py | Claude Opus 5.5**  
#228 – Đổi id sách và số lượng nhận từ request thành số nguyên trong khoảng cho phép.

**hàm `_allow_cart_action` | backend/orders/cart_services.py | Claude Opus 5.5**  
#229 – Giới hạn tần suất thao tác giỏ hàng theo từng khách: thêm vào giỏ (CART_ADD_RATE_*) và đổi số lượng/gỡ (CART_UPDATE_RATE_*).

**hàm `_guard_cart_write` | backend/orders/cart_services.py | Claude Opus 5.5**  
#241 – Kiểm tra chung trước khi gọi thủ tục giỏ hàng: chỉ khách, không trong transaction.atomic, giới hạn tần suất có ghi log.

**hàm `_call_cart_proc` | backend/orders/cart_services.py | Claude Opus 5.5**  
#242 – Gọi thủ tục giỏ hàng với tham số truyền riêng, đổi lỗi SIGNAL thành CartError; lỗi khác (thiếu quyền...) để nguyên.

**hàm `add_to_cart` | backend/orders/cart_services.py | Claude Opus 5.5**  
#230 – Thêm sách vào giỏ bằng sp_cart_add; user lấy từ phiên đăng nhập, có giới hạn tần suất; trả số cuốn của sách đó trong giỏ sau khi thêm.

**class `CartLine` | backend/orders/cart_services.py | Claude Opus 5.5**  
#243 – Một dòng trong giỏ cho template: giá hiện tại, thành tiền, tình trạng và nút nào được bấm (tăng/giảm/gỡ).

**class `Cart` | backend/orders/cart_services.py | Claude Opus 5.5**  
#244 – Cả giỏ hàng: các dòng, tạm tính và số cuốn chỉ tính sách còn bán và còn hàng.

**hàm `get_cart` | backend/orders/cart_services.py | Claude Opus 5.5**  
#245 – Đọc giỏ của khách đang đăng nhập bằng sp_cart_list.

**hàm `set_cart_quantity` | backend/orders/cart_services.py | Claude Opus 5.5**  
#246 – Đặt số lượng mới (1–5) cho sách trong giỏ bằng sp_cart_set_quantity, dùng cho nút tăng và giảm.

**hàm `remove_from_cart` | backend/orders/cart_services.py | Claude Opus 5.5**  
#247 – Gỡ một sách khỏi giỏ bằng sp_cart_remove.

### `backend/orders/forms.py`

**class `CartAddForm` | backend/orders/forms.py | Claude Opus 5.5**  
#231 – Form thêm vào giỏ: chỉ id sách và số lượng 1–5, không có giá hay user.

**class `CartQuantityForm` | backend/orders/forms.py | Claude Opus 5.5**  
#248 – Form đổi số lượng trong giỏ: id sách và số lượng cuối cùng 1–5.

**class `CartRemoveForm` | backend/orders/forms.py | Claude Opus 5.5**  
#249 – Form gỡ sách khỏi giỏ: chỉ id sách.

**class `CheckoutForm` | backend/orders/forms.py | Claude Opus 5.5**  
#271 – Form thông tin giao hàng: tên người nhận, SĐT Việt Nam, địa chỉ; bỏ ký tự điều khiển/vô hình, gom khoảng trắng.

### `backend/orders/models.py`

**cả file | backend/orders/models.py | chưa đánh dấu**  
Model của app orders.

Bảng nghiệp vụ truy cập 100% gián tiếp: model ở đây chỉ để ĐỌC qua view MySQL (Meta: managed = False, db_table = "v_..."). Ghi dữ liệu qua services.py → stored procedure. Lược đồ gốc: database/scripts-secure-bookstore.sql

### `backend/orders/services.py`

**class `OrderError` | backend/orders/services.py | Claude Opus 5.5**  
#002 – Lỗi nghiệp vụ khi đặt đơn, mang mã lỗi và câu tiếng Việt. Người dùng: TuanThanh.

**class `PlaceOrderResult` | backend/orders/services.py | Claude Opus 5.5**  
#003 – Kết quả đặt đơn gồm mã đơn và cờ đơn mới. Người dùng: TuanThanh.

**hàm `new_idempotency_key` | backend/orders/services.py | Claude Opus 5.5**  
#004 – Sinh mã yêu cầu chống bấm đặt hàng hai lần. Người dùng: TuanThanh.

**hàm `shipping_context` | backend/orders/services.py | Claude Opus 5.5**  
#266 – Ngữ cảnh mã hóa SĐT/địa chỉ giao hàng gắn với người đặt và mã chống trùng của đơn, bản mã chép sang đơn khác sẽ không giải mã được.

**hàm `_allow_place_order` | backend/orders/services.py | Claude Opus 5.5**  
#267 – Giới hạn số lần đặt hàng của mỗi khách theo ORDER_PLACE_RATE_*.

**hàm `place_order` | backend/orders/services.py | Claude Opus 5.5**  
#005 – Đặt đơn: user lấy từ phiên, mã hóa SĐT/địa chỉ, giới hạn tần suất rồi gọi sp_place_order và đổi lỗi SIGNAL thành OrderError. Đã viết lại bởi Claude Opus 5.5 khi truyền thời gian giữ kho và số cuốn tối đa. Người dùng: TuanThanh.

**hàm `_signal_code` | backend/orders/services.py | Claude Opus 5.5**  
#006 – Đọc mã lỗi nghiệp vụ từ lỗi MySQL 1644 do SIGNAL. Người dùng: TuanThanh.

**class `OrderLine` | backend/orders/services.py | Claude Opus 5.5**  
#268 – Một sách trong đơn: tên và giá chụp lúc đặt.

**class `Order` | backend/orders/services.py | Claude Opus 5.5**  
#269 – Đơn hàng cho template: trạng thái, tiền, thông tin giao hàng đã giải mã, hạn thanh toán; không chứa mã chống trùng.

**hàm `get_order` | backend/orders/services.py | Claude Opus 5.5**  
#270 – Đọc một đơn của chính khách bằng sp_order_get; mã đơn sai mẫu bị chặn trước khi xuống CSDL, đơn người khác báo không tìm thấy.

**hàm `_allow_cancel_order` | backend/orders/services.py | Claude Opus 5.5**  
#286 – Giới hạn số lần bấm hủy đơn của mỗi khách theo ORDER_CANCEL_RATE_*.

**hàm `cancel_order` | backend/orders/services.py | Claude Opus 5.5**  
#287 – Khách hủy đơn chờ thanh toán của chính mình bằng sp_order_cancel; mã đơn sai mẫu không xuống CSDL, kho được cộng lại trong thủ tục. Đã viết lại bởi Claude Opus 5.5 khi trả về cờ tài khoản vừa bị khóa vì giữ kho.

**class `OrderSummary` | backend/orders/services.py | Claude Opus 5.5**  
#365 – Một dòng trong danh sách đơn của khách: mã, trạng thái, tổng tiền, thời gian, số cuốn và tên cuốn đầu; không chứa thông tin giao hàng.

**hàm `list_my_orders` | backend/orders/services.py | Claude Opus 5.5**  
#366 – Đọc một trang đơn của chính khách theo nhóm Đang xử lý/Lịch sử bằng sp_order_list_mine; nhóm sai bị chặn trước khi xuống CSDL, trả tổng số và danh sách.

### `backend/orders/tests/test_cart_add.py`

**class `AddToCartServiceTests` | backend/orders/tests/test_cart_add.py | Claude Opus 5.5**  
#236 – Test service thêm vào giỏ bằng cursor giả: user lấy từ phiên, số lượng 1–5, chặn nhân viên, giới hạn tần suất, đổi lỗi SIGNAL.

**class `CartAddViewTests` | backend/orders/tests/test_cart_add.py | Claude Opus 5.5**  
#237 – Test view thêm vào giỏ: chỉ POST, CSRF, ẩn danh đi đăng nhập, nhân viên bị từ chối, chặn open redirect, ở lại trang đang xem.

### `backend/orders/tests/test_cart_page.py`

**class `CartDataTests` | backend/orders/tests/test_cart_page.py | Claude Opus 5.5**  
#256 – Test dữ liệu giỏ: tạm tính chỉ tính sách còn bán, nút tăng/giảm khóa đúng lúc, nhãn ngừng bán/hết hàng.

**class `CartPageServiceTests` | backend/orders/tests/test_cart_page.py | Claude Opus 5.5**  
#257 – Test service trang giỏ bằng cursor giả: user lấy từ phiên, id/số lượng kiểm tra trước khi xuống CSDL, giới hạn tần suất, đổi lỗi SIGNAL.

**class `CartPageViewTests` | backend/orders/tests/test_cart_page.py | Claude Opus 5.5**  
#258 – Test view trang giỏ: hiển thị dòng, nút khóa, không cache; form chỉ POST + CSRF, ẩn danh đi đăng nhập, nhân viên bị từ chối, luôn quay về giỏ.

### `backend/orders/tests/test_checkout.py`

**class `CheckoutFormTests` | backend/orders/tests/test_checkout.py | Claude Opus 5.5**  
#278 – Test form giao hàng: chuẩn hóa SĐT, chặn tên có thẻ HTML/ký tự lạ, địa chỉ quá ngắn, bỏ ký tự vô hình.

**class `GetOrderServiceTests` | backend/orders/tests/test_checkout.py | Claude Opus 5.5**  
#279 – Test get_order bằng cursor giả: mã đơn sai mẫu không xuống CSDL, giải mã đúng ngữ cảnh, đơn người khác báo không tìm thấy, hạn thanh toán.

**class `CheckoutViewTests` | backend/orders/tests/test_checkout.py | Claude Opus 5.5**  
#280 – Test view đặt hàng và xem đơn: giỏ phải sạch, mã chống trùng chỉ trong phiên, giá/user_id từ form bị bỏ qua, IDOR trả 404, CSRF, nhân viên bị từ chối.

**class `BuyNowButtonTests` | backend/orders/tests/test_checkout.py | Claude Opus 5.5**  
#281 – Test nút Đặt hàng ở trang chi tiết sách: thêm vào giỏ rồi chuyển sang giỏ.

### `backend/orders/tests/test_hold_abuse.py`

**class `HoldAbuseLockTests` | backend/orders/tests/test_hold_abuse.py | Claude Opus 5.5**  
#542 – Test chống giữ kho: hủy đơn làm khóa tài khoản thì đăng xuất mọi phiên và ghi log, đăng nhập/phiên đang mở bị chặn khi đang khóa, đơn quá 20 cuốn bị chặn, trạng thái admin.

### `backend/orders/tests/test_order_cancel.py`

**class `CancelOrderServiceTests` | backend/orders/tests/test_order_cancel.py | Claude Opus 5.5**  
#291 – Test service hủy đơn bằng cursor giả: mã đơn sai mẫu không xuống CSDL, chặn nhân viên/ẩn danh, giới hạn tần suất, đổi lỗi SIGNAL. Đã viết lại bởi Claude Opus 5.5 khi thủ tục hủy trả cờ khóa vì giữ kho.

**class `OrderCancelViewTests` | backend/orders/tests/test_order_cancel.py | Claude Opus 5.5**  
#292 – Test view hủy đơn: chỉ POST + CSRF, đơn người khác/mã sai trả 404, nhân viên/ẩn danh bị chặn, nút hủy hai bước chỉ hiện khi còn chờ thanh toán.

### `backend/orders/tests/test_order_list.py`

**class `ListMyOrdersServiceTests` | backend/orders/tests/test_order_list.py | Claude Opus 5.5**  
#370 – Test service danh sách đơn của khách bằng cursor giả: nhóm sai không xuống CSDL, chặn nhân viên/ẩn danh, tính offset theo trang, đọc 2 bộ kết quả, đổi lỗi SIGNAL, nhãn quá hạn.

**class `OrderListViewTests` | backend/orders/tests/test_order_list.py | Claude Opus 5.5**  
#371 – Test trang Đơn hàng của tôi: hai tab, tab sai về Đang xử lý, trang sai về 1, link sang chi tiết, trạng thái rỗng, nhân viên/ẩn danh bị chặn, không lưu cache.

### `backend/orders/tests/test_place_order.py`

**class `PlaceOrderTests` | backend/orders/tests/test_place_order.py | Claude Opus 5.5**  
#007 – Test place_order bằng cursor giả: user lấy từ phiên, SĐT/địa chỉ được mã hóa theo ngữ cảnh đơn, giới hạn tần suất, đổi lỗi SIGNAL. Đã viết lại bởi Claude Opus 5.5 khi truyền thời gian giữ kho và số cuốn tối đa. Người dùng: TuanThanh.

### `backend/orders/views.py`

**hàm `cart` | backend/orders/views.py | Claude Opus 5.5**  
#250 – Trang giỏ hàng của khách: đọc bằng sp_cart_list, không lưu cache; nhân viên không có giỏ. Đã viết lại bởi Claude Opus 5.5 khi hiện số cuốn tối đa mỗi đơn và thời gian giữ kho.

**hàm `_cart_page_guard` | backend/orders/views.py | Claude Opus 5.5**  
#251 – Kiểm tra chung cho form trên trang giỏ: ẩn danh đi đăng nhập rồi quay lại giỏ, nhân viên bị từ chối.

**hàm `cart_update` | backend/orders/views.py | Claude Opus 5.5**  
#252 – Nhận nút tăng/giảm trên trang giỏ (chỉ POST, CSRF): gửi số lượng cuối cùng, xong quay về giỏ.

**hàm `cart_remove` | backend/orders/views.py | Claude Opus 5.5**  
#253 – Nhận nút gỡ sách trên trang giỏ (chỉ POST, CSRF), không hỏi xác nhận, xong quay về giỏ.

**hàm `order_list` | backend/orders/views.py | Claude Opus 5.5**  
#367 – Trang Đơn hàng của tôi: hai tab Đang xử lý/Lịch sử đọc bằng sp_order_list_mine, phân trang, không lưu cache; nhân viên không có đơn.

**hàm `_safe_back_url` | backend/orders/views.py | Claude Opus 5.5**  
#232 – Chỉ quay lại địa chỉ nội bộ an toàn sau khi thêm vào giỏ, chặn open redirect.

**hàm `cart_add` | backend/orders/views.py | Claude Opus 5.5**  
#233 – Nhận form thêm vào giỏ (chỉ POST, CSRF): ẩn danh đi đăng nhập, nhân viên bị từ chối, xong thì ở lại trang đang xem kèm thông báo.

**hàm `_log_order_probe` | backend/orders/views.py | Claude Opus 5.5**  
#328 – Ghi idor_attempt khi khách mở/hủy đơn bằng mã đúng định dạng nhưng không phải đơn của mình (hoặc không có); người dùng vẫn chỉ thấy 404.

**hàm `_checkout_key` | backend/orders/views.py | Claude Opus 5.5**  
#272 – Mã chống bấm trùng của lần đặt hàng: sinh ở server, chỉ lưu trong phiên, không nhận từ form.

**hàm `checkout` | backend/orders/views.py | Claude Opus 5.5**  
#273 – Trang đặt hàng: kiểm tra giỏ (không rỗng, không có sách ngừng bán/hết hàng), form giao hàng điền sẵn từ hồ sơ, gọi sp_place_order, xong chuyển tới trang đơn. Đã viết lại bởi Claude Opus 5.5 khi giới hạn số cuốn mỗi đơn và đổi thời gian giữ kho.

**hàm `order_detail` | backend/orders/views.py | Claude Opus 5.5**  
#274 – Trang chi tiết đơn của chính khách theo mã đơn (kèm cờ bật thanh toán mô phỏng); mã sai hoặc đơn người khác đều trả 404 như nhau.

**hàm `order_cancel` | backend/orders/views.py | Claude Opus 5.5**  
#288 – Nhận nút hủy đơn (chỉ POST, CSRF, sau bước xác nhận trên trang đơn): đơn người khác/mã sai trả 404, xong quay về trang đơn. Đã viết lại bởi Claude Opus 5.5 khi hủy đơn có thể khóa tài khoản vì giữ kho.

**hàm `_logout_auto_locked` | backend/orders/views.py | Claude Opus 5.5**  
#541 – Hủy đơn làm tài khoản bị khóa tự động vì giữ kho: ghi log order_hold_abuse, xóa mọi phiên, đăng xuất, báo giờ mở khóa.

### `backend/payments/admin.py`

**cả file | backend/payments/admin.py | chưa đánh dấu**  
Nhóm KHÔNG dùng trang /admin/ mặc định của Django cho bảng nghiệp vụ (django.contrib.admin chưa được bật). Trang quản trị tự viết nằm ở app dashboard.

### `backend/payments/models.py`

**cả file | backend/payments/models.py | chưa đánh dấu**  
Model của app payments.

Bảng nghiệp vụ truy cập 100% gián tiếp: model ở đây chỉ để ĐỌC qua view MySQL (Meta: managed = False, db_table = "v_..."). Ghi dữ liệu qua services.py → stored procedure. Lược đồ gốc: database/scripts-secure-bookstore.sql

### `backend/payments/services.py`

**class `PaymentError` | backend/payments/services.py | Claude Opus 5.5**  
#353 – Lỗi nghiệp vụ khi thanh toán, mang mã lỗi và câu tiếng Việt.

**hàm `_allow_simulate` | backend/payments/services.py | Claude Opus 5.5**  
#354 – Giới hạn số lần bấm thanh toán mô phỏng của mỗi khách theo PAYMENT_SIMULATE_RATE_*.

**hàm `_signal_code` | backend/payments/services.py | Claude Opus 5.5**  
#355 – Đọc mã lỗi nghiệp vụ thanh toán từ lỗi MySQL 1644 do SIGNAL.

**hàm `simulate_payment` | backend/payments/services.py | Claude Opus 5.5**  
#356 – Thanh toán mô phỏng: chỉ khi PAYMENT_SIMULATION bật, user lấy từ phiên, mã đơn sai mẫu không xuống CSDL, giới hạn tần suất rồi gọi sp_payment_simulate, trả mã giao dịch.

### `backend/payments/tests/test_simulate.py`

**class `SimulatePaymentServiceTests` | backend/payments/tests/test_simulate.py | Claude Opus 5.5**  
#360 – Test service thanh toán mô phỏng bằng cursor giả: tắt cờ thì không xuống CSDL, mã đơn sai mẫu bị chặn, chặn nhân viên/ẩn danh, giới hạn tần suất, đổi lỗi SIGNAL, lấy mã giao dịch từ tham số OUT.

**class `SimulateViewTests` | backend/payments/tests/test_simulate.py | Claude Opus 5.5**  
#361 – Test view thanh toán mô phỏng: chỉ POST + CSRF, đơn người khác/mã sai trả 404 và ghi idor_attempt, nhân viên/ẩn danh bị chặn, nút chỉ hiện khi bật cờ và đơn còn chờ thanh toán.

### `backend/payments/views.py`

**hàm `simulate` | backend/payments/views.py | Claude Opus 5.5**  
#357 – Nhận nút thanh toán mô phỏng (chỉ POST, CSRF, sau bước xác nhận trên trang đơn): đơn người khác/mã sai trả 404 và ghi idor_attempt, xong quay về trang đơn.


## Frontend (template, CSS, JS)

### `frontend/static/css/account-area.css`

**khối CSS `.area-actions` | frontend/static/css/account-area.css | Claude Opus 5.5**  
#062 – Kiểu nút thao tác và form đổi mật khẩu trong khu vực tài khoản.

**khối CSS `.area-form--center` | frontend/static/css/account-area.css | Claude Opus 5.5**  
#084 – Căn giữa form xác thực lại và đổi mật khẩu theo chiều ngang vùng nội dung tài khoản.

**khối CSS `.cart` | frontend/static/css/account-area.css | Claude Opus 5.5**  
#255 – Kiểu trang giỏ hàng: danh sách sách bên trái, ô tạm tính bên phải, sách không bán được hiện mờ, xếp dọc trên màn hình hẹp.

**khối CSS `.checkout` | frontend/static/css/account-area.css | Claude Opus 5.5**  
#277 – Kiểu trang đặt hàng (form + tóm tắt) và trang chi tiết đơn (bảng sách, nhãn trạng thái).

**khối CSS `.order__status--cancelled, .order__status--expired` | frontend/static/css/account-area.css | Claude Opus 5.5**  
#290 – Kiểu khối hủy đơn hai bước và nhãn trạng thái đã hủy/quá hạn.

**khối CSS `.order__pay summary` | frontend/static/css/account-area.css | Claude Opus 5.5**  
#359 – Kiểu khối thanh toán mô phỏng hai bước trên trang đơn.

**khối CSS `.order__status--confirmed, .order__status--packed` | frontend/static/css/account-area.css | Claude Opus 5.5**  
#369 – Kiểu danh sách Đơn hàng của tôi (thẻ đơn bấm được, phân trang) và nhãn trạng thái Đã tiếp nhận/Đã đóng gói.

### `frontend/static/css/account.css`

**cả file | frontend/static/css/account.css | chưa đánh dấu**  
account.css – khu vực tài khoản: đăng ký, đăng nhập, quên mật khẩu. Nạp trong template bằng {% block extra_css %}. Chỉ dùng biến của base.css.

Khớp với HTML hiện có của account/register.html (vòng lặp {% for field in form %}),

không cần sửa template:

- `.auth-form`: form, dạng lưới tự chia 1 hoặc 2 cột theo bề rộng thẻ
- `.auth-form__field`: một ô: label + input + lỗi + gợi ý
- `.auth-form__errors`: lỗi của ô        .auth-form__help   gợi ý của ô
- `.auth-form__alert`: lỗi chung        .auth-form__submit nút gửi

**khối CSS `.auth__card:has(#id_password2)` | frontend/static/css/account.css | chưa đánh dấu**  
--- Thẻ đăng ký rộng hơn để chia 2 cột --- Nhận biết trang đăng ký bằng ô "nhập lại mật khẩu" (id_password2 do Django tạo). Trang đăng nhập không có ô này nên giữ bề rộng 440px của base.css.

**khối CSS `.auth__brand` | frontend/static/css/account.css | chưa đánh dấu**  
--- Tên thương hiệu căn giữa --- fit-content để vùng bấm chỉ bằng chữ, không kéo dài hết chiều ngang thẻ.

**khối CSS `.auth-form` | frontend/static/css/account.css | chưa đánh dấu**  
--- Lưới form --- Mỗi cột tối thiểu 240px: thẻ rộng thì 2 cột (email | mật khẩu...), thẻ hẹp (đăng nhập, điện thoại) thì tự về 1 cột.

**khối CSS `.auth-form__field input[name="username"]` | frontend/static/css/account.css | chưa đánh dấu**  
--- Biểu tượng trong ô nhập --- Ảnh SVG nhúng dạng data URI (CSP cho phép img-src data:). Ảnh nền không đọc được biến CSS, nên màu ghi thẳng: %238a7171 chính là --color-subtle (#8a7171). Biểu tượng: Material Icons, Apache License 2.0 (giống icons.svg).

**khối CSS `.auth-form__help--wide` | frontend/static/css/account.css | chưa đánh dấu**  
Khối yêu cầu mật khẩu: một khối liền dưới cả hai ô, kéo sát lên hàng ô nhập, căn giữa theo chiều ngang của thẻ (khối chỉ rộng bằng nội dung)

**khối CSS `.auth__notice` | frontend/static/css/account.css | Claude Opus 5.5**  
#030 – Khung thông báo trên các trang xác nhận email.

**khối CSS `.auth__lead` | frontend/static/css/account.css | Claude Opus 5.5**  
#427 – Dòng giới thiệu trang đăng ký và ô email chỉ hiển thị ở bước hoàn tất.

**khối CSS `.auth-form__captcha` | frontend/static/css/account.css | Claude Opus 5.5**  
#439 – Chỗ cho ô Cloudflare Turnstile trải hết bề ngang form, giữ chỗ để form không nhảy khi ô hiện ra.

### `frontend/static/css/base.css`

**cả file | frontend/static/css/base.css | chưa đánh dấu**  
base.css – style CHUNG cho toàn site (nhóm trưởng giữ, sửa phải qua review). Phong cách theo docs thiết kế (DESIGN.md của Stitch): nền giấy ngà, đỏ đô làm màu chính, vàng đồng điểm xuyết; tiêu đề Playfair Display, nội dung Plus Jakarta Sans (font tự host, xem fonts.css).

CSP chặn style inline: KHÔNG dùng thuộc tính style="..." trong HTML. CSS riêng từng khu vực: shop.css, account.css, dashboard.css. Màu, khoảng cách, bo góc: luôn dùng biến bên dưới, không gõ mã màu trực tiếp.

**khối CSS `@media (max-width: 479px)` | frontend/static/css/base.css | chưa đánh dấu**  
Điện thoại: chỉ giữ biểu tượng logo cho đủ chỗ 3 mục menu; chữ thương hiệu bị ẩn bằng mắt nhưng trình đọc màn hình vẫn đọc được

### `frontend/static/css/dashboard.css`

**khối CSS `.dash-info` | frontend/static/css/dashboard.css | Claude Opus 5.5**  
#041 – Kiểu bảng thông tin tài khoản và ô bị ẩn có nút con mắt.

**khối CSS `.dash-actions` | frontend/static/css/dashboard.css | Claude Opus 5.5**  
#098 – Kiểu form cập nhật thông tin nhân viên và hàng nút thao tác.

**khối CSS `.dash-header--row` | frontend/static/css/dashboard.css | Claude Opus 5.5**  
#181 – Kiểu trang kho sách: bộ lọc, bảng, nhãn trạng thái, khung, form, ảnh bìa, phân trang, xác nhận xóa.

**khối CSS `.dash-field input[type="file"]` | frontend/static/css/dashboard.css | Claude Opus 5.5**  
#225 – Kiểu ô chọn ảnh bìa dạng vùng viền đứt có nút viên thuốc và khung xem ảnh bìa hiện tại.

**khối CSS `.dash-note` | frontend/static/css/dashboard.css | Claude Opus 5.5**  
#312 – Kiểu trang quản lý tài khoản: ghi chú trạng thái xem dữ liệu nhạy cảm, nút nhỏ trong bảng, form xác nhận một cột.

**khối CSS `.btn--danger.btn--sm` | frontend/static/css/dashboard.css | Claude Opus 5.5**  
#316 – Nút khóa nhỏ trong bảng tài khoản dùng màu nút chính và căn giữa khung xác nhận trong vùng quản trị.

**khối CSS `.dash-confirm:has(> .dash-form)` | frontend/static/css/dashboard.css | Claude Opus 5.5**  
#317 – Khung xác nhận khóa tài khoản chia hai cột: thông tin bên trái, form bên phải, về một cột trên màn hình nhỏ.

**khối CSS `.dash-tabs` | frontend/static/css/dashboard.css | Claude Opus 5.5**  
#343 – Kiểu trang nhật ký hệ thống: tab, dòng cảnh báo/nghiêm trọng tô nền, chữ đơn cách cho IP và đường dẫn, chi tiết và danh sách thay đổi gọn.

**khối CSS `.dash-order__code` | frontend/static/css/dashboard.css | Claude Opus 5.5**  
#389 – Kiểu trang quản lý đơn: mã đơn chữ đơn cách, nút bước tiếp theo xác nhận bằng details, hai thẻ thông tin đơn/giao hàng.

**khối CSS `.dash-overview` | frontend/static/css/dashboard.css | Claude Opus 5.5**  
#401 – Kiểu trang Tổng quan: nhóm số liệu có tiêu đề, thẻ số bấm được, thẻ cảnh báo đỏ, dải 4 bước đơn hàng, lưới kho/bảo mật.

**khối CSS `.reauth__label, .dash-field__label` | frontend/static/css/dashboard.css | Claude Opus 5.5**  
#553 – Ô hiện tên tài khoản dạng chữ trong form xác thực lại và khóa/mở khóa (T2.2), không phải ô nhập.

**khối CSS `.dash-stat__value--text` | frontend/static/css/dashboard.css | Claude Opus 5.5**  
#576 – Kiểu ô trạng thái sao lưu: giá trị dạng chữ/ngày giờ nhỏ hơn số, dòng gợi ý dưới giá trị.

### `frontend/static/css/fonts.css`

**cả file | frontend/static/css/fonts.css | chưa đánh dấu**  
fonts.css – font tự host (KHÔNG tải từ Google Fonts: CSP chỉ cho font từ chính site). Playfair Display (tiêu đề) và Plus Jakarta Sans (nội dung), bản "variable" (một file chứa mọi độ đậm), chỉ giữ 3 bộ ký tự: latin, latin-ext, vietnamese. Giấy phép SIL Open Font License 1.1: xem static/fonts/OFL-*.txt

### `frontend/static/css/shop.css`

**cả file | frontend/static/css/shop.css | chưa đánh dấu**  
shop.css – khu vực khách hàng: trang chủ, danh sách sách (FE 1 giữ). Nạp trong template bằng {% block extra_css %}. Chỉ dùng biến của base.css.

**khối CSS `.error-page` | frontend/static/css/shop.css | chưa đánh dấu**  
--- Trang lỗi (errors/400, 403, 403_csrf, 404, 500) ---

Hai kiểu HTML đều dùng được:

404: .error-page > .icon, .error-page__code, .error-page__title, __text, __search, __actions còn lại: .error-page > h1 (mã lỗi), p (mô tả), .btn Ghi đè rule .error-page của base.css (h1 72px đỏ) cho hợp theme giấy ngà + đỏ đô + vàng đồng.

**khối CSS `.book-card__cover` | frontend/static/css/shop.css | Claude Opus 5.5**  
#222 – Kiểu trang chi tiết sách: ảnh lớn, thông tin, nút đặt hàng mờ, danh sách và form đánh giá.

**khối CSS `.cart-add` | frontend/static/css/shop.css | Claude Opus 5.5**  
#235 – Kiểu form thêm vào giỏ ở trang chi tiết: ô số lượng gọn cạnh nút.

**khối CSS `.catalog` | frontend/static/css/shop.css | Claude Opus 5.5**  
#407 – Kiểu thanh chuyển trang tủ sách: ô số tròn, trang hiện tại tô màu chính, dấu ba chấm, ô nhập số trang; xuống dòng gọn trên điện thoại.

### `frontend/static/js/account.js`

**cả file | frontend/static/js/account.js | chưa đánh dấu**  
account.js – trang đăng nhập / đăng ký. Nạp bằng {% block extra_js %} (defer). Nút "con mắt" hiện/ẩn mật khẩu: chỉ đổi type của <input> (password ↔ text). Quy tắc CSP: không JS inline, gắn sự kiện bằng addEventListener, không innerHTML.

### `frontend/static/js/base.js`

**cả file | frontend/static/js/base.js | chưa đánh dấu**  
base.js – JavaScript CHUNG (nhóm trưởng giữ). Nạp ở cuối base.html với defer. Quy tắc (CSP + chống DOM XSS):

- Không viết JS inline trong HTML, không dùng onclick="...".
- Gắn sự kiện bằng addEventListener.
- Hiển thị dữ liệu bằng textContent, KHÔNG dùng innerHTML.
- AJAX gửi CSRF token qua header X-CSRFToken, lấy từ {% csrf_token %} trong trang.

**hàm `getCsrfToken` | frontend/static/js/base.js | chưa đánh dấu**  
Lấy CSRF token từ ô ẩn mà {% csrf_token %} sinh ra trong trang. (Cookie CSRF đặt HttpOnly nên JS không đọc cookie.)

**hàm `postForm` | frontend/static/js/base.js | chưa đánh dấu**  
Gửi POST bằng fetch, kèm CSRF token. Trả về JSON. Dùng chung cho các AJAX nhỏ (cập nhật giỏ hàng...).

### `frontend/static/js/copy-codes.js`

**cả file | frontend/static/js/copy-codes.js | chưa đánh dấu**  
copy-codes.js – nút "Sao chép" ở trang mã dự phòng (account/two_factor_codes.html). Quy tắc CSP: không JS inline, không innerHTML; chỉ đọc textContent và ghi textContent. Clipboard API chỉ chạy trên HTTPS hoặc localhost; trình duyệt không hỗ trợ (hoặc tắt JS) thì nút vẫn ẩn, người dùng chép tay hay tải file.

### `frontend/templates/account/check_email.html`

**khối HTML `<h1 class="auth__title">Kiểm tra hộp thư</h1>` | frontend/templates/account/check_email.html | Claude Opus 5.5**  
#027 – Trang kiểm tra hộp thư dùng chung cho đăng ký và gửi lại thư. Đã viết lại bởi Claude Opus 5.5 khi đổi sang đăng ký bằng email.

### `frontend/templates/account/login_two_factor.html`

**khối HTML `<h1 class="auth__title">Xác thực 2 bước</h1>` | frontend/templates/account/login_two_factor.html | Claude Opus 5.5**  
#500 – Trang đăng nhập bước 2: nhập mã 6 số (khách được dùng mã dự phòng), có hạn 5 phút.

### `frontend/templates/account/orders.html`

**khối HTML `<header class="area-header">` | frontend/templates/account/orders.html | Claude Opus 5.5**  
#368 – Trang Đơn hàng của tôi: hai tab, mỗi đơn hiện mã, ngày đặt, sách, số cuốn, tổng tiền, trạng thái và link sang chi tiết; phân trang.

### `frontend/templates/account/password_change.html`

**khối HTML `<header class="area-header">` | frontend/templates/account/password_change.html | Claude Opus 5.5**  
#061 – Form đổi mật khẩu trong khu vực tài khoản khách, có nút hiện mật khẩu.

### `frontend/templates/account/password_reset.html`

**khối HTML `<h1 class="auth__title">Quên mật khẩu</h1>` | frontend/templates/account/password_reset.html | Claude Opus 5.5**  
#053 – Form nhập email để nhận link đặt lại mật khẩu.

### `frontend/templates/account/password_reset_confirm.html`

**khối HTML `<h1 class="auth__title">Đặt mật khẩu mới</h1>` | frontend/templates/account/password_reset_confirm.html | Claude Opus 5.5**  
#055 – Trang đặt mật khẩu mới từ link, báo lỗi khi link hết hạn hoặc đã dùng.

### `frontend/templates/account/password_reset_done.html`

**khối HTML `<h1 class="auth__title">Kiểm tra hộp thư</h1>` | frontend/templates/account/password_reset_done.html | Claude Opus 5.5**  
#054 – Trang báo đã gửi link đặt lại mật khẩu, giống nhau cho mọi email.

### `frontend/templates/account/profile.html`

**khối HTML `<header class="area-header">` | frontend/templates/account/profile.html | Claude Opus 5.5**  
#039 – Bảng thông tin tài khoản của khách, hiện đầy đủ email và SĐT.

**khối HTML `<section class="area-2fa">` | frontend/templates/account/profile.html | Claude Opus 5.5**  
#499 – Khối xác thực 2 bước ở trang thông tin: trạng thái, số mã dự phòng còn lại, nút bật/tắt.

### `frontend/templates/account/profile_update.html`

**khối HTML `<header class="area-header">` | frontend/templates/account/profile_update.html | Claude Opus 5.5**  
#081 – Form sửa họ, tên, SĐT; tên đăng nhập và email chỉ hiển thị, không sửa.

### `frontend/templates/account/reauth.html`

**khối HTML `<header class="area-header">` | frontend/templates/account/reauth.html | Claude Opus 5.5**  
#080 – Trang xác thực lại của khách: tên đăng nhập, mật khẩu, nút xác thực và link quên mật khẩu. Đã viết lại bởi Claude Opus 5.5 khi bỏ ô tên đăng nhập (T2.2).

### `frontend/templates/account/register.html`

**khối HTML `<h1 class="auth__title">Tạo tài khoản</h1>` | frontend/templates/account/register.html | Claude Opus 5.5**  
#425 – Trang đăng ký bước 1 chỉ có ô email, tên đăng nhập và mật khẩu đặt sau khi mở link trong thư.

**khối HTML `<div class="auth-form__captcha">` | frontend/templates/account/register.html | Claude Opus 5.5**  
#438 – Ô xác minh Cloudflare Turnstile tự hiện trong form, báo cần JavaScript khi bị tắt.

### `frontend/templates/account/signup_complete.html`

**khối HTML `<h1 class="auth__title">Hoàn tất đăng ký</h1>` | frontend/templates/account/signup_complete.html | Claude Opus 5.5**  
#426 – Trang đăng ký bước 2: email chỉ hiển thị, đặt tên đăng nhập và mật khẩu; báo lỗi khi link hoặc phiên hỏng.

### `frontend/templates/account/two_factor_codes.html`

**khối HTML `<header class="area-header">` | frontend/templates/account/two_factor_codes.html | Claude Opus 5.5**  
#502 – Trang hiện 5 mã dự phòng đúng một lần, nút sao chép (JS ngoài) và tải file .txt (không cần JS).

### `frontend/templates/account/two_factor_disable.html`

**khối HTML `<header class="area-header">` | frontend/templates/account/two_factor_disable.html | Claude Opus 5.5**  
#503 – Trang tắt 2 bước: mật khẩu hiện tại và mã 6 số hoặc mã dự phòng.

### `frontend/templates/account/two_factor_setup.html`

**khối HTML `<header class="area-header">` | frontend/templates/account/two_factor_setup.html | Claude Opus 5.5**  
#501 – Trang cài 2 bước: ảnh QR từ URL riêng, chuỗi bí mật để gõ tay, ô nhập mã xác nhận.

### `frontend/templates/components/book_card.html`

**khối HTML `<a class="book-card__cover" href="{% url 'catalog:book_detai` | frontend/templates/components/book_card.html | Claude Opus 5.5**  
#221 – Ảnh bìa và tên sách trong thẻ sách dẫn tới trang chi tiết.

### `frontend/templates/components/category_filter.html`

**cả file | frontend/templates/components/category_filter.html | chưa đánh dấu**  
Lọc theo thể loại: mỗi thể loại là một link GET ?category=<id>. Tham số: categories – danh sách thể loại (mỗi phần tử có .id, .name)

- `current`: – id thể loại đang chọn (None = tất cả)
- `q`: – từ khóa đang tìm, giữ lại khi đổi thể loại

View tự kiểm tra category là số nguyên và có thật; giá trị lạ bị bỏ qua.

### `frontend/templates/components/pagination.html`

**khối HTML `{% if page.has_other_pages %}` | frontend/templates/components/pagination.html | Claude Opus 5.5**  
#406 – Thanh chuyển trang không JS: trước/sau, số trang có dấu ba chấm, ô nhập số trang gửi bằng form GET giữ nguyên bộ lọc.

### `frontend/templates/components/search_bar.html`

**cả file | frontend/templates/components/search_bar.html | chưa đánh dấu**  
Ô tìm kiếm sách (GET, không đổi dữ liệu nên không cần CSRF). Tham số: action – URL nhận kết quả (bắt buộc)

- `q`: – từ khóa hiện tại, để giữ lại trong ô sau khi tìm

category – thể loại đang lọc (giữ lại khi tìm), có thể trống maxlength="100" chỉ là tiện ích giao diện; giới hạn THẬT nằm ở view (kẻ tấn công gửi thẳng request, không đi qua ô này).

### `frontend/templates/dashboard/account_action.html`

**khối HTML `<section class="dash-confirm">` | frontend/templates/dashboard/account_action.html | Claude Opus 5.5**  
#311 – Trang xác nhận khóa/mở khóa: thông tin tài khoản (đã che), lý do và nhập lại tài khoản + mật khẩu admin cho riêng lần này. Đã viết lại bởi Claude Opus 5.5 khi bỏ ô tên đăng nhập (T2.2).

### `frontend/templates/dashboard/accounts.html`

**khối HTML `<header class="dash-header dash-header--row">` | frontend/templates/dashboard/accounts.html | Claude Opus 5.5**  
#310 – Trang quản lý tài khoản: lọc theo trạng thái và username, bảng khách hàng với email/SĐT che bớt (bản đầy đủ cần xác thực lại), nút khóa/mở khóa.

### `frontend/templates/dashboard/book_create.html`

**khối HTML `<a class="dash-back" href="{% url 'dashboard:books' %}">{% i` | frontend/templates/dashboard/book_create.html | Claude Opus 5.5**  
#176 – Trang thêm sách: form multipart gồm thông tin, tồn kho ban đầu và ảnh bìa.

### `frontend/templates/dashboard/book_delete.html`

**khối HTML `<section class="dash-confirm">` | frontend/templates/dashboard/book_delete.html | Claude Opus 5.5**  
#178 – Trang xác nhận xóa sách vĩnh viễn, nêu rõ hậu quả.

### `frontend/templates/dashboard/book_edit.html`

**khối HTML `<a class="dash-back" href="{% url 'dashboard:books' %}">{% i` | frontend/templates/dashboard/book_edit.html | Claude Opus 5.5**  
#177 – Trang sửa sách: khung thông tin và ảnh, khung tồn kho, khung trạng thái, vùng xóa.

### `frontend/templates/dashboard/books.html`

**khối HTML `<header class="dash-header dash-header--row">` | frontend/templates/dashboard/books.html | Claude Opus 5.5**  
#174 – Trang danh sách sách: bộ lọc GET, bảng sách có ảnh, giá nhập, tồn kho, trạng thái, phân trang.

### `frontend/templates/dashboard/categories.html`

**khối HTML `<header class="dash-header">` | frontend/templates/dashboard/categories.html | Claude Opus 5.5**  
#179 – Trang thể loại: form thêm, bảng thể loại có số sách, sửa tên từng dòng, liên kết xóa khi không còn sách.

### `frontend/templates/dashboard/category_delete.html`

**khối HTML `<section class="dash-confirm">` | frontend/templates/dashboard/category_delete.html | Claude Opus 5.5**  
#180 – Trang xác nhận xóa thể loại không còn sách.

### `frontend/templates/dashboard/index.html`

**khối HTML `<header class="dash-header">` | frontend/templates/dashboard/index.html | Claude Opus 5.5**  
#400 – Trang Tổng quan: đơn cần xử lý theo bước (bấm sang Quản lý đơn có lọc sẵn), đơn mới/hủy hôm nay, doanh thu, kho sắp hết/hết hàng và 5 cuốn còn ít nhất, bảo mật 24 giờ.

**khối HTML `{% with b=overview.backup %}` | frontend/templates/dashboard/index.html | Claude Opus 5.5**  
#575 – Ô trạng thái sao lưu trên Tổng quan: lần sao lưu thành công/lỗi, kiểm tra khôi phục gần nhất, tô đỏ khi cần chú ý; không có nút sao lưu (chỉ chạy bằng lệnh trên máy chủ).

### `frontend/templates/dashboard/logs.html`

**khối HTML `<header class="dash-header">` | frontend/templates/dashboard/logs.html | Claude Opus 5.5**  
#342 – Trang nhật ký hệ thống: hai tab bảo mật/thay đổi dữ liệu, bộ lọc GET, bảng mới nhất trước, mức độ tô màu, chi tiết mở bằng details, phân trang.

### `frontend/templates/dashboard/order_detail.html`

**khối HTML `<header class="dash-header dash-header--row">` | frontend/templates/dashboard/order_detail.html | Claude Opus 5.5**  
#388 – Trang chi tiết đơn cho admin: trạng thái, khách, các mốc thời gian, giao dịch thanh toán, thông tin giao hàng (đã ghi log khi xem), sách và tiền, nút bước tiếp theo.

### `frontend/templates/dashboard/orders.html`

**khối HTML `<header class="dash-header">` | frontend/templates/dashboard/orders.html | Claude Opus 5.5**  
#387 – Trang quản lý đơn hàng: lọc trạng thái, bảng mã đơn/khách/ngày đặt/số cuốn/tổng tiền/trạng thái, link chi tiết (cần xác thực lại), nút bước tiếp theo, phân trang.

### `frontend/templates/dashboard/partials/book_fields.html`

**khối HTML `<div class="dash-grid">` | frontend/templates/dashboard/partials/book_fields.html | Claude Opus 5.5**  
#175 – Nhóm ô thông tin sách dùng chung cho trang thêm và trang sửa.

### `frontend/templates/dashboard/partials/field.html`

**khối HTML `<div class="dash-field{% if field.errors %} has-error{% endi` | frontend/templates/dashboard/partials/field.html | Claude Opus 5.5**  
#173 – Hiển thị một ô form dashboard: nhãn, ô nhập, gợi ý, lỗi gắn aria-describedby.

### `frontend/templates/dashboard/partials/order_action.html`

**khối HTML `<details class="dash-step">` | frontend/templates/dashboard/partials/order_action.html | Claude Opus 5.5**  
#386 – Nút bước tiếp theo của đơn, xác nhận hai bước bằng details (không JS, không nhập mật khẩu), gửi POST tới URL riêng của bước đó.

### `frontend/templates/dashboard/profile.html`

**khối HTML `<header class="dash-header">` | frontend/templates/dashboard/profile.html | Claude Opus 5.5**  
#040 – Bảng thông tin nhân viên, email và SĐT ẩn sau nút con mắt cần xác thực lại.

### `frontend/templates/dashboard/profile_update.html`

**khối HTML `<header class="dash-header">` | frontend/templates/dashboard/profile_update.html | Claude Opus 5.5**  
#097 – Form sửa họ, tên, SĐT của nhân viên; không hiện email và SĐT hiện tại.

### `frontend/templates/dashboard/reauth.html`

**khối HTML `<section class="reauth">` | frontend/templates/dashboard/reauth.html | Claude Opus 5.5**  
#552 – Trang xác thực lại của admin: hiện tên tài khoản dạng chữ, chỉ nhập mật khẩu (T2.2).

### `frontend/templates/errors/500.html`

**block `title` | frontend/templates/errors/500.html | chưa đánh dấu**  
Trang 500 KHÔNG dùng layout có navbar/messages: lỗi có thể do CSDL, nên trang này không được phụ thuộc vào request, user hay session.

### `frontend/templates/layouts/admin.html`

**block `body` | frontend/templates/layouts/admin.html | chưa đánh dấu**  
Layout khu vực NHÂN VIÊN (dashboard): sidebar + nội dung. Chỉ dùng cho view đã kiểm tra quyền (@permission_required). Ẩn menu KHÔNG thay cho kiểm tra quyền. Trang con điền: title, content.

### `frontend/templates/shop/book_detail.html`

**khối HTML `<a class="detail-back" href="{% url 'catalog:home' %}">{% in` | frontend/templates/shop/book_detail.html | Claude Opus 5.5**  
#220 – Trang chi tiết sách: ảnh bìa lớn bên trái, thông tin theo hàng bên phải, nút đặt hàng mờ, danh sách và form đánh giá.

**khối HTML `{% if book.in_stock and not user.is_staff %}` | frontend/templates/shop/book_detail.html | Claude Opus 5.5**  
#234 – Form thêm vào giỏ cạnh nút đặt hàng: ô số lượng 1–5, khóa khi hết hàng; nút Đặt hàng gửi cùng form rồi chuyển sang giỏ.

### `frontend/templates/shop/cart.html`

**khối HTML `<div class="cart">` | frontend/templates/shop/cart.html | Claude Opus 5.5**  
#254 – Danh sách sách trong giỏ: nút −/+ gửi số lượng cuối cùng, nút Gỡ, sách ngừng bán/hết hàng hiện mờ chỉ gỡ được, tạm tính và nút đặt hàng (khóa khi còn sách không bán được).

### `frontend/templates/shop/checkout.html`

**khối HTML `<header class="area-header">` | frontend/templates/shop/checkout.html | Claude Opus 5.5**  
#275 – Trang đặt hàng: form giao hàng bên trái, tóm tắt giỏ, phí ship và tổng tiền bên phải; giá chỉ để xem, server tính lại.

### `frontend/templates/shop/order_detail.html`

**khối HTML `<header class="area-header">` | frontend/templates/shop/order_detail.html | Claude Opus 5.5**  
#276 – Trang chi tiết đơn: mã đơn, trạng thái, hạn thanh toán, sách và giá lúc đặt, thông tin giao hàng; nút thanh toán (mô phỏng khi bật trong .env), hủy đơn khi còn chờ thanh toán.

**khối HTML `<details class="order__pay">` | frontend/templates/shop/order_detail.html | Claude Opus 5.5**  
#358 – Thanh toán mô phỏng hai bước bằng details (không JS): bấm nút mới hiện số tiền và nút xác nhận gửi POST.

**khối HTML `<details class="order__cancel">` | frontend/templates/shop/order_detail.html | Claude Opus 5.5**  
#289 – Hủy đơn hai bước bằng details (không JS): bấm Hủy đơn mới hiện nút xác nhận gửi POST.


## Cơ sở dữ liệu (MySQL)

### `database/01_bang.sql`

**cả file | database/01_bang.sql | chưa đánh dấu**  
secure-bookstore – Bảng nghiệp vụ (lược đồ v1) Hệ quản trị: MySQL 8.4 LTS (Docker theo compose.yaml, hoặc cài thường)

File này KHÔNG chạy bằng tay. Nó được migration backend/core/migrations/0001_business_schema.py đọc và chạy khi gõ `python manage.py migrate`, ngay SAU migration tạo accounts_user. Thứ tự tạo bảng vì vậy luôn đúng: accounts_user (Django) → các bảng dưới đây.

Quy ước:

- Tên bảng, cột: tiếng Anh. Chú thích: tiếng Việt.
- Tên bảng theo quy ước của Django: <app>_<model>.
- Tiền tệ: VND, lưu số nguyên (INT UNSIGNED), không dùng số thực.
- Thời gian: DATETIME(6), lưu theo UTC (server đặt default-time-zone = '+00:00').
- Cột *_encrypted: dữ liệu đã mã hóa AES-GCM ở tầng ứng dụng, lưu dạng base64.
- Mọi bảng dùng InnoDB (cần cho transaction, khóa dòng, khóa ngoại).

Bảng accounts_user KHÔNG có ở đây: Django tạo nó từ accounts/models.py (migration accounts/0001_initial), cùng các cột và 2 CHECK như lược đồ v1. Các bảng Django khác cũng do migrate tạo: auth_*, accounts_user_groups, accounts_user_user_permissions, django_session, django_content_type, django_migrations (sau này thêm axes_*, otp_*).

Muốn sửa lược đồ: thường tạo file mới (02_..., 03_...) và một migration mới đọc file đó. Chỉ sửa thẳng file này khi cả nhóm đã thống nhất và mọi máy dựng lại CSDL từ đầu (xem database/README.md, mục "Làm lại sạch").

**bảng `accounts_passwordhistory` | database/01_bang.sql | Claude Opus 5.5**  
#085 – Bảng lưu 5 mã băm mật khẩu gần nhất của mỗi tài khoản.

Lịch sử mật khẩu: mã băm của tối đa 5 mật khẩu gần nhất (tính cả mật khẩu đang dùng) của mỗi tài khoản. Django dùng để chặn đặt lại mật khẩu cũ.

- GHI: chỉ trigger trg_pwhist_* (phần 11 của 02_trigger_thu_tuc.sql) ghi và xóa bớt, chạy bằng quyền bookstore_definer. Tài khoản ứng dụng chỉ có SELECT.
- SO SÁNH: chỉ làm được trong Django. Mã băm có muối ngẫu nhiên nên cùng một mật khẩu cho ra chuỗi khác nhau; phải gọi check_password(mật khẩu mới, mã băm cũ). CSDL không bao giờ thấy mật khẩu gốc.

**bảng `accounts_totpdevice` | database/01_bang.sql | Claude Opus 5.5**  
#468 – Bảng thiết bị TOTP: chuỗi bí mật mã hóa, lúc xác nhận, bước thời gian đã dùng gần nhất (chống dùng lại mã).

**bảng `accounts_recoverycode` | database/01_bang.sql | Claude Opus 5.5**  
#469 – Bảng mã dự phòng: chỉ mã băm, mỗi mã dùng một lần.

**bảng `orders_cartitem` | database/01_bang.sql | chưa đánh dấu**  
Dòng trong giỏ hàng. KHÔNG lưu giá: giá luôn lấy từ catalog_book tại thời điểm đặt đơn (chống sửa giá phía client).

**bảng `orders_order` | database/01_bang.sql | Claude Opus 5.5**  
#590 – Bảng đơn hàng gộp trạng thái cuối: thêm confirmed, packed, mọi trạng thái sau thanh toán bắt buộc có paid_at.

Đơn hàng. Chỉ được TẠO qua sp_place_order và chuyển sang 'paid' qua sp_confirm_payment. Thông tin giao hàng là bản chụp lúc đặt (không có bảng địa chỉ riêng).

**bảng `payments_payment` | database/01_bang.sql | Claude Opus 5.5**  
#591 – Bảng giao dịch thanh toán gộp trạng thái cuối: giới hạn tên cổng, giao dịch mô phỏng không cần chữ ký, mỗi đơn tối đa một giao dịch thành công.

Cột sinh tự động: chỉ có giá trị khi giao dịch thành công. Đặt UNIQUE trên cột này để một transaction_id chỉ được ghi nhận thành công MỘT lần (chống replay), nhưng vẫn lưu được nhiều lần thử bị từ chối dùng lại cùng mã.

**bảng `core_auditlog` | database/01_bang.sql | chưa đánh dấu**  
Nhật ký thay đổi dữ liệu. Do TRIGGER ghi (database/triggers/), ứng dụng không ghi trực tiếp. Không tài khoản ứng dụng nào có quyền UPDATE/DELETE trên bảng này. Không đặt khóa ngoại để log vẫn còn nguyên khi bản ghi gốc bị xóa.

**bảng `core_securityevent` | database/01_bang.sql | Claude Opus 5.5**  
#592 – Bảng nhật ký bảo mật gộp trạng thái cuối: danh sách loại sự kiện hiện hành và chỉ mục theo thời gian.

Nhật ký sự kiện bảo mật. Django ghi (app core), đồng thời ghi ra file security.log. Tài khoản ứng dụng chỉ có INSERT và SELECT, không có UPDATE/DELETE. Không đặt khóa ngoại tới accounts_user: log phải giữ nguyên kể cả khi user bị xóa, và có thể ghi sự kiện cho username không tồn tại (dò tài khoản).

### `database/02_trigger_thu_tuc.sql`

**phần "Trigger bảo vệ bảng tài khoản (chặn leo thang đặc quyền)" | database/02_trigger_thu_tuc.sql | chưa đánh dấu**  
Chặn leo thang đặc quyền ngay trong CSDL (lớp phòng thủ thứ 2).

Vấn đề: Django đăng nhập, đăng ký, đổi mật khẩu đều chạy bằng kết nối `default` (tài khoản app_customer) và lệnh user.save() của Django luôn ghi lại MỌI cột, kể cả is_staff, is_superuser. Vì vậy không thể chỉ cấp quyền UPDATE theo cột như kế hoạch ban đầu (save() sẽ bị MySQL từ chối).

Cách làm (cập nhật 2026-11-19): app_customer chỉ còn SELECT trên accounts_user. Mọi lệnh GHI của Django (đăng ký, last_login, hồ sơ, đổi/đặt lại mật khẩu) đi qua tài khoản riêng app_auth (core.db_routers.AccountWriteRouter). 2 trigger dưới đây từ chối mọi câu lệnh của app_auth (và app_customer, phòng khi cấp nhầm quyền)

có ý định:

- tạo user với is_staff = 1 hoặc is_superuser = 1;
- đổi giá trị is_staff, is_superuser của user đã có;
- sửa dòng của nhân viên/quản trị, trừ cột last_login (để nhân viên vẫn đăng nhập được qua trang đăng nhập chung). Chặn kiểu tấn công ghi đè mật khẩu/email của admin rồi chiếm tài khoản;
- sửa dòng của khách ở các cột web không bao giờ đổi: is_active (tự mở khóa), email, username (đổi email rồi "quên mật khẩu" để chiếm tài khoản), email_verified, date_joined. Khóa/mở khóa chỉ qua thủ tục của admin. Chỉ còn đổi được password, last_login, first_name, last_name, phone_encrypted.

Ghi lại đúng giá trị cũ (như user.save() bình thường) vẫn được phép.

Với app_staff (kết nối "staff" của dashboard): quyền theo cột chỉ cho sửa first_name, last_name, phone_encrypted; trigger chặn thêm việc sửa dòng của KHÁCH (is_staff = 0). Kết nối staff bị lạm dụng cũng không sửa được tên/SĐT của khách hàng. Ngoại lệ duy nhất (2026-11-16): cột is_active của khách, chỉ đổi được qua thủ tục khóa/mở khóa tài khoản.

Hệ quả cho code:

- Tạo tài khoản admin: chạy createsuperuser bằng settings.migrate.
- Đổi mật khẩu nhân viên: chỉ bằng lệnh trên máy chủ `python manage.py doi_mat_khau_admin <tên> --settings=bookstore.settings.migrate`. Trên web không có đường nào đổi được mật khẩu nhân viên.

Kể cả khi có lỗi SQL injection trên web, kẻ tấn công cũng không tự nâng mình lên nhân viên/quản trị được.

USER() trả về tài khoản MySQL đang kết nối (người gọi), không phải người tạo trigger, nên kiểm tra được ai đang chạy câu lệnh.

Root tạo trigger này bằng `python manage.py db_apply` (sau migrate). DEFINER là bookstore_definer (khóa đăng nhập), không phải root. Chạy lại nhiều lần được (DROP ... IF EXISTS rồi tạo lại).

**trigger `trg_user_guard_update` | database/02_trigger_thu_tuc.sql | chưa đánh dấu**  
Dòng của nhân viên: chỉ được đổi last_login. <=> là so sánh an toàn với NULL (NULL <=> NULL là đúng).

app_customer không có quyền UPDATE trên bảng này (chỉ SELECT), nên lệnh đổi cột này với USER() = app_customer chỉ có thể đến từ thủ tục DEFINER (33_order_cancel.sql).

app_staff: chỉ được sửa dòng của nhân viên (cột nào thì quyền theo cột đã giới hạn). Riêng dòng của khách: chỉ được đổi đúng cột is_active (khóa/mở khóa). app_staff không có quyền UPDATE(is_active) trực tiếp, nên thay đổi này chỉ có thể đến từ sp_staff_account_lock/unlock (42_account.sql, chạy bằng quyền definer, ghi nhật ký).

**trigger `trg_user_guard_update` (đoạn `IF OLD.is_staff = 0 AND NOT (`) | database/02_trigger_thu_tuc.sql | Claude Opus 5.5**  
#459 – Dòng của khách: cấm đổi is_active, email, username, email_verified, date_joined (chặn tự mở khóa và đổi email để chiếm tài khoản).

**trigger `trg_user_guard_update` (đoạn `-- app_customer không có quyền UPDATE trên bảng này (chỉ SEL`) | database/02_trigger_thu_tuc.sql | Claude Opus 5.5**  
#534 – app_auth không được đổi auto_locked_until (khóa tự động vì giữ kho): chỉ thủ tục DEFINER đặt/gỡ cột này.

**trigger `trg_user_guard_update` (đoạn `IF SUBSTRING_INDEX(USER(), '@', 1) = 'app_staff' AND OLD.is_`) | database/02_trigger_thu_tuc.sql | Claude Opus 5.5**  
#099 – Chặn app_staff sửa dòng của khách hàng, trừ cột is_active do thủ tục khóa/mở khóa đổi.

**phần "Trigger ghi lịch sử mật khẩu" | database/02_trigger_thu_tuc.sql | chưa đánh dấu**  
Ghi lịch sử mật khẩu (bảng accounts_passwordhistory, `database/01_bang.sql`).

Mỗi khi cột accounts_user.password có giá trị mới (tạo tài khoản, đổi mật khẩu, đặt lại mật khẩu, lệnh changepassword, kể cả ai đó sửa thẳng bằng SQL), trigger thêm mã băm mới vào lịch sử rồi xóa bớt, chỉ giữ 5 dòng mới nhất của tài khoản đó. Dòng mới nhất là mật khẩu đang dùng.

Vì sao dùng trigger cho phần GHI:

- không sót đường nào: mọi câu INSERT/UPDATE vào accounts_user đều đi qua;
- trigger chạy bằng quyền bookstore_definer, nên app_customer không cần quyền INSERT/DELETE trên bảng lịch sử (chỉ có SELECT để Django so sánh).

Phần SO SÁNH nằm ở Django (accounts/validators.py) vì mã băm có muối ngẫu nhiên: chỉ check_password() với mật khẩu gốc mới biết có trùng không.

Bỏ qua mật khẩu "không dùng được" của Django (bắt đầu bằng '!'). Số 5 phải khớp OPTIONS history_count của PasswordHistoryValidator trong bookstore/settings/base.py.

Root tạo bằng `python manage.py db_apply`. Chạy lại nhiều lần được.

**trigger `trg_pwhist_after_insert` | database/02_trigger_thu_tuc.sql | Claude Opus 5.5**  
#086 – Trigger lưu mật khẩu đầu tiên của tài khoản mới vào lịch sử.

**trigger `trg_pwhist_after_update` | database/02_trigger_thu_tuc.sql | Claude Opus 5.5**  
#087 – Trigger lưu mật khẩu mới vào lịch sử khi đổi và chỉ giữ 5 dòng mới nhất.

id của dòng mới thứ 5; mọi dòng cũ hơn dòng đó bị xóa. Chưa đủ 5 dòng thì SELECT không có kết quả, v_cut_id giữ NULL.

**phần "Trigger bảo vệ xác thực 2 bước của nhân viên" | database/02_trigger_thu_tuc.sql | chưa đánh dấu**  
Bảo vệ xác thực 2 bước của nhân viên (bảng ở `database/01_bang.sql`).

Chỉ app_auth có quyền trên accounts_totpdevice và accounts_recoverycode (khách bật/tắt 2 bước, ghi bước thời gian khi đăng nhập). Trigger dưới đây chặn app_auth (và app_customer, phòng khi cấp nhầm quyền) đụng vào 2 bước

của NHÂN VIÊN:

- không tạo, không xóa thiết bị TOTP của nhân viên: admin chỉ cài/cài lại bằng lệnh trên máy chủ (tao_admin, dat_lai_2fa_admin, tài khoản migrate);
- với thiết bị của nhân viên chỉ được tăng last_used_step (lúc admin đăng nhập), không đổi chuỗi bí mật, không đổi chủ, không lùi bước thời gian;
- không tạo/sửa/xóa mã dự phòng của nhân viên (admin không có mã dự phòng).

Nhờ vậy SQL injection ở trang tài khoản (kết nối app_auth) cũng không thay được Google Authenticator của admin bằng điện thoại của kẻ tấn công. Với khách: last_used_step cũng không được lùi (chống dùng lại mã cũ).

**trigger `trg_totp_guard_insert` | database/02_trigger_thu_tuc.sql | Claude Opus 5.5**  
#472 – Tài khoản ứng dụng không được tạo thiết bị TOTP cho nhân viên.

**trigger `trg_totp_guard_update` | database/02_trigger_thu_tuc.sql | Claude Opus 5.5**  
#473 – Thiết bị của nhân viên chỉ được tăng bước thời gian; mọi thiết bị không được lùi bước.

**trigger `trg_totp_guard_delete` | database/02_trigger_thu_tuc.sql | Claude Opus 5.5**  
#474 – Tài khoản ứng dụng không được xóa thiết bị TOTP của nhân viên.

**trigger `trg_recovery_guard_insert` | database/02_trigger_thu_tuc.sql | Claude Opus 5.5**  
#475 – Tài khoản ứng dụng không được tạo/sửa/xóa mã dự phòng của nhân viên.

**phần "Thủ tục đọc danh mục sách cho khách" | database/02_trigger_thu_tuc.sql | chưa đánh dấu**  
Đọc danh mục sách cho KHÁCH (mọi người xem, kể cả chưa đăng nhập).

- `sp_public_category_list`: thể loại để hiện bộ lọc: id, name, slug
- `sp_public_book_list`: sách đang bán, lọc theo thể loại và từ khóa
- `sp_public_book_get`: một cuốn sách đang bán (trang chi tiết), kèm tên thể loại

Ban đầu (issue #9) định làm view v_public_books / v_public_categories. Đổi sang THỦ TỤC ĐỌC vì MySQL 8.0/8.4 từ chối view SQL SECURITY DEFINER có WHERE/JOIN/GROUP BY khi phiên người gọi đang bật role (app_customer luôn bật r_customer) – lỗi 1143/1356. Thủ tục DEFINER không bị lỗi này.

Phân quyền: r_customer chỉ có EXECUTE hai thủ tục, KHÔNG có quyền nào trên catalog_book, catalog_category, catalog_review. Django luôn dùng kết nối app_customer cho trang cửa hàng, nên khách chưa đăng nhập cũng xem được.

Cột trả về của sp_public_book_list (hợp đồng, khớp issue #9, không thêm bớt): id, title, author, isbn, category_id, description, price, cover_image, created_at, in_stock (0/1 = stock > 0, không lộ số tồn kho), rating (ROUND(AVG, 1) của đánh giá is_visible = 1, NULL khi chưa có), review_count KHÔNG BAO GIỜ trả: cost_price, stock, is_active, updated_at. Chỉ sách is_active = 1. Sách ẩn không lộ qua bất kỳ tham số nào.

Tìm kiếm: từ khóa tối đa 100 ký tự, tìm trong tên sách hoặc tác giả bằng LIKE với tham số (không có SQL động). Ký tự đại diện % và _ trong từ khóa được thoát, nên chỉ tìm đúng chữ người dùng gõ. Kết quả tối đa 200 cuốn, mới nhất trước (chưa có phân trang).

Lỗi: SIGNAL SQLSTATE '45000' 'INVALID_INPUT' khi tham số sai. Root tạo bằng `python manage.py db_apply`. Chạy lại nhiều lần được.

**thủ tục `sp_public_category_list` | database/02_trigger_thu_tuc.sql | Claude Opus 5.5**  
#189 – Thủ tục trả thể loại cho bộ lọc của cửa hàng, chỉ id, tên, slug.

**thủ tục `sp_public_book_list` | database/02_trigger_thu_tuc.sql | Claude Opus 5.5**  
#190 – Thủ tục trả sách đang bán cho khách: lọc thể loại, tìm tên/tác giả, điểm đánh giá, không lộ giá nhập và tồn kho.

**thủ tục `sp_public_book_get` | database/02_trigger_thu_tuc.sql | Claude Opus 5.5**  
#211 – Thủ tục trả một sách đang bán cho trang chi tiết, kèm tên thể loại và điểm đánh giá; sách ẩn trả rỗng.

Cùng bộ cột với sp_public_book_list, thêm category_name ở cuối. Sách ẩn hoặc không tồn tại: 0 dòng như nhau, không phân biệt được.

**phần "Thủ tục đánh giá sách" | database/02_trigger_thu_tuc.sql | chưa đánh dấu**  
Đánh giá sách của khách (catalog_review).

- `sp_review_save`: gửi đánh giá; nếu đã có thì SỬA đánh giá cũ
- `sp_review_get_mine`: đánh giá của chính mình cho một sách (điền sẵn form sửa)
- `sp_review_can_write`: khách này đã được đánh giá sách này chưa (để hiện form)
- `sp_review_list`: đánh giá đang hiện của một sách, tên người viết đã che

Ai được đánh giá (siết lại 2026-11-20, cách a): khách đang hoạt động, đã xác nhận email, KHÔNG phải nhân viên, VÀ có ít nhất một đơn ở trạng thái 'delivered' (admin bấm "Đã giao") chứa đúng cuốn sách đó. Đơn chờ thanh toán, đã thanh toán, đang giao, đã hủy đều không tính. Trạng thái đơn chỉ đi tới (trigger 32), nên đã nhận sách thì luôn sửa được đánh giá của mình. Đánh giá cũ của khách chưa nhận sách đã bị xóa (trước khi gom SQL).

Bảo mật:

- p_user_id do Django lấy từ phiên đăng nhập (request.user.pk), không bao giờ lấy từ form; thủ tục vẫn tự kiểm tra lại người đó là khách hợp lệ.
- Chỉ sách đang hiện (is_active = 1); sách ẩn hay không tồn tại đều báo BOOK_NOT_FOUND như nhau.
- Điểm 1–5; nội dung 1–2000 ký tự sau khi bỏ khoảng trắng hai đầu (bảng còn có CHECK ck_review_rating, ck_review_content_not_blank).
- Mỗi khách một đánh giá cho mỗi sách (UNIQUE uq_review_user_book). Gửi lại là sửa; dùng INSERT ... ON DUPLICATE KEY UPDATE nên hai lần bấm cùng lúc không tạo hai dòng, không lỗi.
- Sửa không đổi is_visible: đánh giá admin đã ẩn thì vẫn ẩn.
- r_customer chỉ có EXECUTE; không có INSERT/UPDATE/DELETE trên bảng.
- Nội dung hiển thị luôn qua auto-escape của Django, không dùng |safe.

Lỗi (SIGNAL SQLSTATE '45000', MESSAGE_TEXT là đúng một mã):

- `INVALID_INPUT`: tham số sai
- `NOT_CUSTOMER`: tài khoản không phải khách hợp lệ (nhân viên, bị khóa, chưa xác nhận email, không tồn tại)
- `BOOK_NOT_FOUND`: sách không tồn tại hoặc đang ẩn
- `NOT_PURCHASED`: khách chưa có đơn "Đã giao" chứa cuốn sách này

Root tạo bằng `python manage.py db_apply`. Chạy lại nhiều lần được.

**thủ tục `sp_review_save` | database/02_trigger_thu_tuc.sql | Claude Opus 5.5**  
#198 – Thủ tục gửi hoặc sửa đánh giá: kiểm tra khách hợp lệ, sách đang hiện, điểm và nội dung, không tạo trùng.

**thủ tục `sp_review_save` (đoạn `IF NOT EXISTS (`) | database/02_trigger_thu_tuc.sql | Claude Opus 5.5**  
#513 – Chỉ khách có đơn "Đã giao" chứa đúng cuốn sách mới được gửi/sửa đánh giá.

**thủ tục `sp_review_get_mine` | database/02_trigger_thu_tuc.sql | Claude Opus 5.5**  
#199 – Thủ tục trả đánh giá của chính khách cho một sách để điền sẵn form sửa.

**thủ tục `sp_review_can_write` | database/02_trigger_thu_tuc.sql | Claude Opus 5.5**  
#514 – Thủ tục đọc: khách có được đánh giá sách này không (khách hợp lệ, sách đang hiện, đã nhận sách); trả đúng một dòng 0/1.

**thủ tục `sp_review_list` | database/02_trigger_thu_tuc.sql | Claude Opus 5.5**  
#212 – Thủ tục trả đánh giá đang hiện của một sách đang bán, che username ngay trong CSDL, mới nhất trước.

Username được che tại đây (ký tự đầu + dấu sao + ký tự cuối, chốt 2026-11-15), nên tên thật không rời khỏi CSDL. Không trả user_id, email. Chỉ đánh giá is_visible = 1 của sách đang hiện; tối đa 50 dòng.

**phần "Thủ tục đặt hàng sp_place_order" | database/02_trigger_thu_tuc.sql | chưa đánh dấu**  
sp_place_order: biến giỏ hàng của một người dùng thành đơn hàng.

Đây là NƠI DUY NHẤT được tạo đơn và trừ kho. app_customer chỉ có quyền EXECUTE trên thủ tục này, không có quyền nào trên các bảng nó đụng tới (quyền tối thiểu, chương 6.2). Thủ tục chạy bằng quyền của bookstore_definer (SQL SECURITY DEFINER, tài khoản khóa đăng nhập).

Chống race condition (SECURITY_CHECKLIST mục 6):

1. Khóa dòng giỏ của người dùng (FOR UPDATE): hai lần bấm của CÙNG một người phải xếp hàng, lần sau thấy đơn đã có thì trả lại mã cũ.
2. Khóa các dòng sách trong giỏ (FOR UPDATE): hai người KHÁC nhau cùng mua cuốn cuối thì người đến sau phải chờ, rồi nhận OUT_OF_STOCK. Thứ tự khóa sách: InnoDB khóa dòng theo thứ tự nó đọc. Câu khóa đi từ orders_cartitem theo chỉ mục UNIQUE (cart_id, book_id) nên đọc sách theo book_id tăng dần (STRAIGHT_JOIN giữ đúng thứ tự bảng). Mọi giao dịch khóa theo cùng một thứ tự → không có vòng chờ → không deadlock.

Tham số:

- `p_user_id`: id người dùng, Django lấy từ request.user (KHÔNG từ form)
- `p_idempotency_key`: 32 ký tự hex thường, Django sinh khi mở trang đặt hàng
- `p_shipping_name`: tên người nhận, 1–100 ký tự (tham số khai báo 255 để chuỗi dài quá vẫn vào được thủ tục và nhận INVALID_INPUT)
- `p_phone_encrypted`: SĐT đã mã hóa AES-GCM ở Django p_address_encrypted địa chỉ đã mã hóa AES-GCM ở Django
- `p_hold_minutes`: số phút giữ kho chờ thanh toán (settings ORDER_HOLD_MINUTES, 1–60)
- `p_max_items`: tổng số cuốn tối đa của một đơn (settings ORDER_MAX_ITEMS, 1–150) p_order_code (OUT) mã đơn (32 ký tự hex)
- `p_created`: (OUT)  1 = đơn mới tạo, 0 = bấm lại, trả mã đơn cũ

Lỗi (SIGNAL SQLSTATE '45000', MESSAGE_TEXT là đúng 1 trong 8 mã):

- `INVALID_INPUT`: tham số sai, hoặc mã yêu cầu đã thuộc người khác
- `NOT_CUSTOMER`: người gọi là nhân viên, bị khóa hoặc chưa xác nhận email
- `PENDING_EXISTS`: khách đang có 1 đơn chờ thanh toán còn hạn
- `CART_EMPTY`: giỏ rỗng hoặc chưa có giỏ
- `BOOK_INACTIVE`: có sách đã ngừng bán
- `OUT_OF_STOCK`: có sách không đủ số lượng ORDER_TOO_LARGE tổng số cuốn trong giỏ vượt p_max_items
- `ACCOUNT_LOCKED`: tài khoản đang bị khóa tự động vì giữ kho (auto_locked_until)

Bổ sung 2026-11-20 (báo cáo rà soát T3.4 – giữ kho không thanh toán): thời gian giữ kho rút còn 5 phút và truyền từ Django; mỗi đơn tối đa 20 cuốn; tài khoản bỏ 3 đơn chưa thanh toán trong 24 giờ bị khóa 24 giờ (33_order_cancel.sql).

Bổ sung 2026-11-16 (nhánh đặt hàng):

- Tự kiểm tra lại người gọi là khách hợp lệ (NOT_CUSTOMER), như các thủ tục giỏ hàng.
- Chống "giữ kho": kho bị trừ ngay khi tạo đơn, nên mỗi khách chỉ được có tối đa 1 đơn 'pending' còn hạn. Kiểm tra sau khi khóa giỏ nên hai lần đặt cùng lúc của cùng một người không lọt qua được.
- Đơn đã tạo không sửa được: trigger ở 32_trg_orders_guard.sql.

Lỗi ở bất kỳ bước nào: ROLLBACK, không có đơn dở dang, kho và giỏ giữ nguyên.

Root tạo thủ tục bằng `python manage.py db_apply`. Chạy lại nhiều lần được.

**thủ tục `sp_place_order` | database/02_trigger_thu_tuc.sql | Claude Opus 5.5**  
#001 – Thủ tục đặt đơn: khóa giỏ và sách, kiểm tra kho, tạo đơn, trừ kho. Đã viết lại bởi Claude Opus 5.5 khi thêm thời gian giữ kho, giới hạn số cuốn và khóa giữ kho. Người dùng: TuanThanh.

Bước 2: kiểm tra tham số trước khi đụng vào dữ liệu. REGEXP_LIKE(..., 'c') so khớp phân biệt hoa/thường (collation của CSDL không phân biệt, nên REGEXP thường sẽ nhận cả 'ABC...').

Bước 4: khóa giỏ của người dùng. Lần bấm thứ hai của cùng người này đứng chờ ở đây cho tới khi lần đầu COMMIT.

Bước 6: khóa các dòng sách trong giỏ và tính toán trong cùng một câu. Giá lấy từ catalog_book, không bao giờ từ phía người dùng.

Bước 8: tạo đơn. Mã đơn ngẫu nhiên mật mã (RANDOM_BYTES), không dùng UUID() vì UUID sinh theo thời gian nên đoán được.

**thủ tục `sp_place_order` (đoạn `SELECT COUNT(*) INTO v_customer`) | database/02_trigger_thu_tuc.sql | Claude Opus 5.5**  
#259 – sp_place_order tự kiểm tra lại người gọi là khách hợp lệ (đang hoạt động, không phải nhân viên, đã xác nhận email).

**thủ tục `sp_place_order` (đoạn `SELECT auto_locked_until INTO v_locked_until FROM accounts_u`) | database/02_trigger_thu_tuc.sql | Claude Opus 5.5**  
#533 – sp_place_order từ chối tài khoản đang bị khóa tự động vì giữ kho (lớp 2, kể cả khi gọi thẳng thủ tục).

**thủ tục `sp_place_order` (đoạn `SELECT COUNT(*) INTO v_pending_count`) | database/02_trigger_thu_tuc.sql | Claude Opus 5.5**  
#260 – Chống giữ kho: mỗi khách tối đa 1 đơn chờ thanh toán còn hạn, kiểm tra khi đang giữ khóa giỏ.

**thủ tục `sp_order_get` (đoạn `-- Trả 2 bộ kết quả:`) | database/02_trigger_thu_tuc.sql | Claude Opus 5.5**  
#261 – Thủ tục đọc một đơn của chính khách theo mã đơn: dòng đầu là đơn, bộ kết quả thứ hai là các sách; đơn của người khác báo như không tồn tại.

**thủ tục `sp_order_get` | database/02_trigger_thu_tuc.sql | chưa đánh dấu**  
Trả 2 bộ kết quả:

1. đơn: code, status, subtotal, shipping_fee, total, shipping_name, shipping_phone_encrypted, shipping_address_encrypted, idempotency_key (Django dùng làm ngữ cảnh giải mã, không đưa ra template), created_at, expires_at, paid_at, cancelled_at
2. sách: book_id, book_title, unit_price, quantity

Mã đơn sai mẫu, đơn không có hoặc đơn của người khác → ORDER_NOT_FOUND như nhau (chống IDOR: không dò được mã đơn của người khác).

**phần "Thủ tục giỏ hàng" | database/02_trigger_thu_tuc.sql | chưa đánh dấu**  
Giỏ hàng của khách (orders_cart, orders_cartitem).

- `sp_cart_add`: thêm sách vào giỏ; sách đã có thì cộng thêm số lượng
- `sp_cart_list`: đọc giỏ của khách (trang /orders/cart/)
- `sp_cart_set_quantity`: đặt số lượng mới cho một sách trong giỏ (nút + / −)
- `sp_cart_remove`: gỡ một sách khỏi giỏ

Chốt 2026-11-15:

- Mỗi đầu sách trong giỏ tối đa 5 cuốn (bảng còn CHECK 1..10 làm giới hạn ngoài cùng). Cộng dồn vượt 5 → CART_LIMIT, không tự đổi số lượng.
- Mỗi giỏ tối đa 30 đầu sách khác nhau → CART_FULL (chống lạm dụng).
- Chỉ khách đang hoạt động, đã xác nhận email, không phải nhân viên.
- Chỉ sách đang hiện và còn hàng (stock > 0). KHÔNG so số lượng với tồn kho thật ở bước này để khách không dò được số tồn kho; sp_place_order kiểm tra tồn kho chính xác (có khóa dòng) lúc đặt hàng.

Bảo mật / race condition:

- p_user_id do Django lấy từ phiên đăng nhập, thủ tục kiểm tra lại.
- Giỏ tạo bằng INSERT ... ON DUPLICATE KEY UPDATE trên UNIQUE(user_id), rồi khóa dòng giỏ FOR UPDATE, nên hai lần bấm cùng lúc xếp hàng, cộng đúng, không tạo hai giỏ hay hai dòng.
- Thứ tự khóa giống sp_place_order (giỏ trước, sách sau; ở đây sách chỉ khóa chia sẻ FOR SHARE) để hai thủ tục không chờ chéo nhau (deadlock).
- r_customer chỉ có EXECUTE; không có quyền nào trên orders_cart*.

Lỗi (SIGNAL SQLSTATE '45000', MESSAGE_TEXT là đúng một mã):

- `INVALID_INPUT`: tham số sai (số lượng ngoài 1–5)
- `NOT_CUSTOMER`: không phải khách hợp lệ
- `BOOK_NOT_FOUND`: sách không tồn tại hoặc đang ẩn
- `OUT_OF_STOCK`: sách hết hàng
- `CART_LIMIT`: tổng số cuốn của sách này trong giỏ sẽ vượt 5
- `CART_FULL`: giỏ đã có 30 đầu sách
- `NOT_IN_CART`: sách không có trong giỏ của khách này BOOK_UNAVAILABLE sách trong giỏ đã bị ẩn (ngừng bán) – chỉ còn gỡ được

Trang giỏ hàng (chốt 2026-11-15):

- Tăng/giảm dùng chung sp_cart_set_quantity nhận SỐ LƯỢNG CUỐI CÙNG (1–5), không nhận "+1": bấm đúp, hai tab, gửi lại form vẫn ra đúng con số đó.
- Đang 1 cuốn thì nút "−" bị khóa; bỏ sách phải bấm Gỡ (sp_cart_remove), không hỏi xác nhận.
- Sách bị ẩn: hiện mờ "Ngừng bán", chỉ gỡ được (BOOK_UNAVAILABLE). Sách hết hàng: hiện mờ "Hết hàng", không tăng được (OUT_OF_STOCK); giảm vẫn cho vì vô hại. Hai loại này không tính vào "Tạm tính".
- sp_cart_list trả in_stock (0/1), không trả số tồn kho.
- Sách không có trong giỏ → NOT_IN_CART dù sách có tồn tại hay không, nên không dò được sách ẩn qua các thủ tục này.

Root tạo bằng `python manage.py db_apply`. Chạy lại nhiều lần được.

**thủ tục `sp_cart_add` | database/02_trigger_thu_tuc.sql | Claude Opus 5.5**  
#226 – Thủ tục thêm sách vào giỏ: kiểm tra khách, sách còn hàng, cộng dồn tối đa 5 cuốn, tối đa 30 đầu sách, khóa giỏ chống bấm trùng.

**thủ tục `sp_cart_list` | database/02_trigger_thu_tuc.sql | Claude Opus 5.5**  
#238 – Thủ tục đọc giỏ của khách: sách, giá hiện tại, số lượng, tình trạng còn bán/còn hàng, không trả số tồn kho.

**thủ tục `sp_cart_set_quantity` | database/02_trigger_thu_tuc.sql | Claude Opus 5.5**  
#239 – Thủ tục đặt số lượng mới (1–5) cho sách trong giỏ: dùng cho cả tăng và giảm, khóa giỏ chống bấm trùng, sách ẩn không đổi được, hết hàng không tăng được.

**thủ tục `sp_cart_remove` | database/02_trigger_thu_tuc.sql | Claude Opus 5.5**  
#240 – Thủ tục gỡ một sách khỏi giỏ của khách; gỡ được cả sách đã ngừng bán hoặc hết hàng.

**phần "Trigger khóa đơn hàng đã tạo" | database/02_trigger_thu_tuc.sql | chưa đánh dấu**  
Đơn hàng đã tạo thì không sửa được (chốt 2026-11-16).

Yêu cầu: thanh toán xong không thể tự tăng số lượng sách hay thêm sách khác vào đơn. Lớp 1 là quyền: không tài khoản ứng dụng nào có quyền ghi orders_order/orders_orderitem, không có thủ tục nào sửa đơn. Lớp 2 là các trigger dưới đây, chặn ngay trong CSDL kể cả khi definer hoặc một thủ tục

sau này có lỗi:

orders_orderitem (chi tiết đơn)

- Chỉ thêm được khi đơn đang 'pending' và chưa thanh toán (đúng lúc sp_place_order tạo đơn). Đơn đã thanh toán/đang giao/đã hủy → chặn.
- Tổng tiền các dòng không bao giờ vượt subtotal đã chốt của đơn. sp_place_order chép giỏ sang đơn nên các dòng cộng lại vừa đúng bằng subtotal; sau đó chèn thêm bất kỳ dòng nào cũng vượt → chặn. Nhờ vậy đơn đang chờ thanh toán cũng không bị thêm sách sau khi tạo.
- Không bao giờ sửa (giá, số lượng, tên sách) và không bao giờ xóa. orders_order (đơn)
- Không bao giờ đổi: mã đơn, người đặt, tiền sách, phí ship, tổng tiền, thông tin giao hàng, mã chống trùng, ngày tạo, hạn thanh toán.
- Chỉ đổi trạng thái theo đúng chiều: pending → paid, pending → cancelled, paid → confirmed → packed → shipped → delivered (từng bước một, không nhảy cóc, không quay lại – chốt 2026-11-16) paid_at chỉ được ghi một lần lúc chuyển sang 'paid', cancelled_at chỉ được ghi một lần lúc chuyển sang 'cancelled'.
- Không bao giờ xóa đơn (giữ lịch sử).

Mã lỗi: ORDER_LOCKED. Chạy bằng quyền bookstore_definer (khóa đăng nhập). Root tạo trigger bằng `python manage.py db_apply`. Chạy lại nhiều lần được.

**trigger `trg_orderitem_guard_insert` | database/02_trigger_thu_tuc.sql | Claude Opus 5.5**  
#262 – Trigger chỉ cho thêm sách vào đơn đang chờ thanh toán lúc tạo đơn: tổng các dòng không vượt subtotal đã chốt, đơn đã thanh toán/giao/hủy bị chặn.

**trigger `trg_orderitem_guard_update` | database/02_trigger_thu_tuc.sql | Claude Opus 5.5**  
#263 – Trigger cấm sửa và xóa chi tiết đơn hàng (giá, số lượng, tên sách).

**trigger `trg_order_guard_update` | database/02_trigger_thu_tuc.sql | Claude Opus 5.5**  
#264 – Trigger cấm đổi tiền, thông tin giao hàng của đơn; trạng thái chỉ đi tới đúng một bước (đã thanh toán → tiếp nhận → đóng gói → đang giao → đã giao), không quay lại; mốc thanh toán/hủy ghi một lần.

**trigger `trg_order_guard_delete` | database/02_trigger_thu_tuc.sql | Claude Opus 5.5**  
#265 – Trigger cấm xóa đơn hàng để giữ lịch sử.

**phần "Thủ tục hủy đơn, hủy đơn quá hạn và Event" | database/02_trigger_thu_tuc.sql | chưa đánh dấu**  
Hậu xử lý đơn hàng (chốt 2026-11-16, nhánh A trước khung thanh toán):

- `sp_order_cancel`: khách tự hủy đơn chưa thanh toán của chính mình
- `sp_cancel_expired_orders`: hủy mọi đơn chờ thanh toán đã quá hạn (hạn do sp_place_order đặt, 5 phút)
- `sp_order_hold_check`: (nội bộ) đếm đơn bỏ không thanh toán, đủ ngưỡng thì khóa tài khoản 24 giờ
- `ev_cancel_expired_orders`: MySQL Event gọi thủ tục trên mỗi phút

Kho bị trừ ngay khi tạo đơn (sp_place_order), nên hủy đơn = cộng lại đúng số cuốn trong chi tiết đơn, cùng giao dịch với việc đổi trạng thái.

Quy tắc:

- Chỉ đơn 'pending' mới hủy được. Đơn đã thanh toán không hủy (không có hoàn tiền); trigger 32_trg_orders_guard.sql cũng chặn paid → cancelled.
- Khách hủy được cả đơn đã quá hạn mà Event chưa kịp xử lý.
- Mỗi đơn hủy trong một giao dịch riêng, khóa dòng đơn FOR UPDATE rồi mới kiểm tra lại trạng thái: khách bấm hủy đúng lúc Event chạy (hoặc bấm hai lần) thì chỉ một bên hủy được, kho chỉ được cộng một lần.
- Thứ tự khóa: đơn → sách. sp_place_order khóa giỏ → sách và không khóa dòng đơn cũ nào, nên không tạo vòng chờ (không deadlock).
- Sau này thủ tục ghi nhận thanh toán cũng khóa dòng đơn FOR UPDATE và chỉ nhận khi expires_at > lúc đó; Event chỉ hủy khi expires_at <= lúc đó. Hai bên xếp hàng trên cùng dòng đơn nên không có đơn vừa "đã thanh toán" vừa "đã hủy".

Chống giữ kho (báo cáo rà soát T3.4, chốt 2026-11-20): Mỗi lần một đơn 'pending' bị hủy (khách bấm) hoặc hết hạn (Event), trong CÙNG giao dịch gọi sp_order_hold_check: đếm số đơn của khách đó bị hủy mà chưa thanh toán, tính từ mốc muộn hơn giữa (24 giờ trước) và (lần hết khóa / admin mở khóa gần nhất = accounts_user.auto_locked_until cũ). Đủ 3 đơn thì đặt auto_locked_until = lúc đó + 24 giờ: Django coi tài khoản là bị khóa (đăng xuất mọi nơi, không đăng nhập được), sp_place_order cũng từ chối (ACCOUNT_LOCKED). Ngưỡng viết ở đây (không truyền từ Django) vì đường hết hạn do Event chạy, không có Django. Không dùng is_active: đó là khóa của admin (có lý do, nhật ký), và trigger 10 cấm app_customer đổi is_active. Admin mở khóa sớm được bằng sp_staff_account_unlock (42_account.sql). Đường hết hạn tự ghi core_securityevent 'order_hold_abuse' (ip 'system'); đường khách hủy trả p_account_locked = 1 để Django ghi log (có IP) và đăng xuất.

Mã lỗi:

INVALID_INPUT, NOT_CUSTOMER

- `ORDER_NOT_FOUND`: mã sai, không có, hoặc đơn của người khác (như nhau)
- `ORDER_NOT_CANCELLABLE`: đơn không còn ở trạng thái chờ thanh toán

Root tạo bằng `python manage.py db_apply`. Chạy lại nhiều lần được.

**thủ tục `sp_order_hold_check` | database/02_trigger_thu_tuc.sql | Claude Opus 5.5**  
#531 – Thủ tục nội bộ chống giữ kho: đếm đơn bị hủy chưa thanh toán trong 24 giờ (từ lần hết khóa gần nhất), đủ 3 đơn thì khóa tài khoản 24 giờ bằng auto_locked_until.

Chỉ được gọi bên trong giao dịch của sp_order_cancel / sp_order_expire_one, sau khi đã đổi đơn sang 'cancelled'. Không cấp EXECUTE cho tài khoản ứng dụng nào.

**thủ tục `sp_order_cancel` | database/02_trigger_thu_tuc.sql | Claude Opus 5.5**  
#282 – Thủ tục khách tự hủy đơn chờ thanh toán của chính mình: khóa đơn, kiểm tra lại trạng thái, cộng lại kho, đổi sang cancelled trong một giao dịch. Đã viết lại bởi Claude Opus 5.5 khi thêm chống giữ kho (OUT p_account_locked).

**thủ tục `sp_order_expire_one` | database/02_trigger_thu_tuc.sql | Claude Opus 5.5**  
#283 – Thủ tục nội bộ hủy một đơn quá hạn: khóa đơn, chỉ hủy nếu vẫn pending và đã hết hạn, cộng lại kho; lỗi thì rollback riêng đơn đó. Đã viết lại bởi Claude Opus 5.5 khi đơn hết hạn cũng tính là bỏ đơn (chống giữ kho).

**thủ tục `sp_order_expire_one` (đoạn `SELECT auto_locked_until INTO v_until FROM accounts_user WHE`) | database/02_trigger_thu_tuc.sql | Claude Opus 5.5**  
#532 – Đơn hết hạn cũng tính là bỏ đơn: gọi kiểm tra giữ kho, vừa khóa thì tự ghi log order_hold_abuse (Event không có Django).

**thủ tục `sp_cancel_expired_orders` | database/02_trigger_thu_tuc.sql | Claude Opus 5.5**  
#284 – Thủ tục hủy các đơn chờ thanh toán đã quá hạn (tối đa 200 đơn mỗi lần), mỗi đơn một giao dịch, một đơn lỗi không chặn các đơn khác.

**event `ev_cancel_expired_orders` | database/02_trigger_thu_tuc.sql | Claude Opus 5.5**  
#285 – MySQL Event mỗi phút gọi sp_cancel_expired_orders để trả kho cho đơn quá hạn thanh toán.

**phần "Trigger ghi nhật ký đơn hàng" | database/02_trigger_thu_tuc.sql | chưa đánh dấu**  
Nhật ký đơn hàng (chốt 2026-11-16): mọi lần tạo đơn và đổi trạng thái đơn đều ghi vào core_auditlog bằng trigger, nên thủ tục nào đổi đơn (đặt hàng, khách hủy, Event tự hủy, thanh toán sau này) cũng có dấu vết, không sót.

source (ai gây ra thay đổi) suy ra từ USER() – tài khoản MySQL đang chạy câu lệnh (người gọi thủ tục DEFINER, hoặc definer khi Event chạy):

- `app_customer`: → customer  (app_user_id = chủ đơn)
- `event_scheduler`: → system    (Event hủy đơn quá hạn: trong Event, USER() là event_scheduler@localhost – đã thử thật)
- `bookstore_definer`: → system
- `app_payment`: → payment   (nhánh thanh toán, sau này)
- `app_staff`: → staff     (quản lý đơn của admin; app_user_id = id admin do thủ tục 44_staff_orders.sql đặt vào biến phiên @bookstore_actor_id) khác (root...) → other

Thủ tục admin đổi trạng thái đơn KHÔNG tự ghi thêm core_auditlog cho việc đổi trạng thái (trigger đã ghi), chỉ ghi phần riêng như lý do.

Chạy bằng quyền bookstore_definer (đã có INSERT core_auditlog, TRIGGER trên orders_order). Root tạo bằng `python manage.py db_apply`. Chạy lại được.

**trigger `trg_order_audit_insert` | database/02_trigger_thu_tuc.sql | Claude Opus 5.5**  
#320 – Trigger ghi nhật ký khi tạo đơn: mã đơn, trạng thái, tổng tiền, nguồn gây ra (khách/hệ thống/...) suy từ tài khoản MySQL.

**trigger `trg_order_audit_update` | database/02_trigger_thu_tuc.sql | Claude Opus 5.5**  
#321 – Trigger ghi nhật ký khi đơn đổi trạng thái (chờ → đã thanh toán/đã hủy...), kèm nguồn gây ra và id người làm (khách là chủ đơn, admin lấy từ biến phiên do thủ tục đặt); không đổi trạng thái thì không ghi.

**phần "Thủ tục thanh toán mô phỏng" | database/02_trigger_thu_tuc.sql | chưa đánh dấu**  
Thanh toán mô phỏng (chốt 2026-11-16, tạm thời trước khi có cổng thật):

- `sp_payment_simulate`: khách bấm "Thanh toán (mô phỏng)" cho đơn của mình
- `trg_payment_guard_update`: giao dịch đã ghi không sửa được
- `trg_payment_guard_delete`: giao dịch đã ghi không xóa được

Django chỉ cho gọi khi PAYMENT_SIMULATION=True trong .env. Khi có cổng thật, thủ tục ghi nhận của cổng ghi vào cùng bảng payments_payment, đổi đơn sang 'paid' theo đúng cách dưới đây; thủ tục này và quyền EXECUTE của nó bỏ đi.

Quy tắc:

- Chỉ chủ đơn, là khách hợp lệ (NOT_CUSTOMER như các thủ tục khác).
- Khóa dòng đơn FOR UPDATE rồi mới kiểm tra lại trạng thái và hạn: khách bấm hai lần cùng lúc thì chỉ một lần thành công; khách bấm đúng lúc Event hủy đơn quá hạn thì hai bên xếp hàng trên cùng dòng đơn – thủ tục này chỉ nhận khi expires_at > lúc đó, Event chỉ hủy khi expires_at <= lúc đó, nên không có đơn vừa "đã thanh toán" vừa "đã hủy".
- Số tiền ghi vào giao dịch lấy từ total của đơn trong CSDL, không nhận từ ứng dụng. Mã giao dịch sinh ngẫu nhiên ngay trong CSDL.
- Ghi giao dịch và đổi đơn sang 'paid' trong cùng một giao dịch. Trigger 34_trg_orders_audit.sql tự ghi nhật ký đơn chuyển sang 'paid'.
- Lớp cuối: UNIQUE uq_payment_success_order (một đơn tối đa một giao dịch thành công) và trigger 32 (chỉ pending → paid, paid_at ghi một lần).

Mã lỗi:

INVALID_INPUT, NOT_CUSTOMER

- `ORDER_NOT_FOUND`: mã sai, không có, hoặc đơn của người khác (như nhau)
- `ORDER_ALREADY_PAID`: đơn đã thanh toán (hoặc đã tiếp nhận, đóng gói, đang giao, đã giao)
- `ORDER_NOT_PAYABLE`: đơn đã hủy
- `ORDER_EXPIRED`: đơn còn chờ nhưng đã quá hạn thanh toán
- `PAYMENT_LOCKED`: (trigger) sửa hoặc xóa giao dịch đã ghi

Root tạo bằng `python manage.py db_apply`. Chạy lại nhiều lần được.

**thủ tục `sp_payment_simulate` | database/02_trigger_thu_tuc.sql | Claude Opus 5.5**  
#351 – Thủ tục thanh toán mô phỏng: khóa đơn của chính khách, kiểm tra lại trạng thái và hạn, ghi giao dịch 'simulated' với số tiền lấy từ đơn rồi đổi đơn sang paid trong một giao dịch.

**trigger `trg_payment_guard_update` | database/02_trigger_thu_tuc.sql | Claude Opus 5.5**  
#352 – Trigger cấm sửa và xóa giao dịch thanh toán đã ghi, kể cả root và definer.

**phần "Thủ tục đọc đơn hàng của khách" | database/02_trigger_thu_tuc.sql | chưa đánh dấu**  
Trang "Đơn hàng của tôi" của khách (chốt 2026-11-16):

- `sp_order_list_mine`: danh sách đơn của CHÍNH khách đang đăng nhập, theo nhóm

Không dùng view: mọi khách vào CSDL bằng cùng một tài khoản app_customer, MySQL không biết người đang xem là khách nào, nên một view "đơn của khách" sẽ trả đơn của tất cả mọi người. Thủ tục nhận user_id do Django lấy từ phiên đăng nhập và lọc WHERE user_id ngay trong CSDL.

Nhóm:

- `'active'`: Đang xử lý: pending, paid, confirmed, packed, shipped
- `'history'`: Lịch sử (trạng thái cuối): delivered, cancelled

Trả 2 bộ kết quả (mẫu như trang nhật ký):

1. tổng số đơn của nhóm
2. một trang: code, status, total, created_at, expires_at, paid_at, cancelled_at, số cuốn, số đầu sách, tên cuốn đầu tiên

Không trả SĐT/địa chỉ (đã mã hóa) – xem ở trang chi tiết đơn (sp_order_get).

Mã lỗi: INVALID_INPUT, NOT_CUSTOMER. Root tạo bằng `python manage.py db_apply`. Chạy lại nhiều lần được.

**thủ tục `sp_order_list_mine` | database/02_trigger_thu_tuc.sql | Claude Opus 5.5**  
#364 – Thủ tục đọc danh sách đơn của chính khách theo nhóm Đang xử lý / Lịch sử, trả tổng số và một trang (mới nhất trước), không trả thông tin giao hàng.

**phần "Thủ tục quản lý thể loại" | database/02_trigger_thu_tuc.sql | chưa đánh dấu**  
Quản lý thể loại sách (catalog_category) – chỉ nhân viên.

- `sp_category_list`: danh sách thể loại kèm số sách, cho dashboard đọc
- `sp_category_create`: thêm thể loại
- `sp_category_rename`: sửa tên (slug đổi theo tên)
- `sp_category_delete`: xóa thể loại chưa có sách nào

Phân quyền (quyền tối thiểu, chương 6.2):

- Chỉ r_staff (app_staff) được EXECUTE bốn thủ tục. app_customer không có quyền nào ở đây, gọi là MySQL từ chối.
- Không tài khoản ứng dụng nào được INSERT/UPDATE/DELETE thẳng vào catalog_category; mọi thay đổi phải đi qua thủ tục.
- Thủ tục tự kiểm tra p_actor_id là nhân viên đang hoạt động (NOT_STAFF), phòng khi kết nối staff bị dùng sai.

Mỗi thay đổi ghi một dòng core_auditlog trong CÙNG giao dịch: giá trị cũ/mới, tài khoản MySQL gọi thủ tục (USER(), vì CURRENT_USER() trong thủ tục DEFINER luôn là bookstore_definer) và id nhân viên trên web.

Slug do Django tạo từ tên ("Văn học" → van-hoc); thủ tục chỉ kiểm tra định dạng.

Lỗi (SIGNAL SQLSTATE '45000', MESSAGE_TEXT là đúng một mã):

- `INVALID_INPUT`: tham số sai (tên rỗng/quá 100 ký tự, slug sai định dạng)
- `NOT_STAFF`: p_actor_id không phải nhân viên đang hoạt động
- `CATEGORY_EXISTS`: trùng tên hoặc slug (ràng buộc UNIQUE, lỗi 1062)
- `CATEGORY_NOT_FOUND`: không có thể loại với id này
- `CATEGORY_IN_USE`: thể loại còn sách (kể cả sách đang ẩn)

Lỗi ở bước nào cũng ROLLBACK: không có thay đổi dở dang, không có log lẻ.

Race condition:

- Hai lần thêm cùng tên: UNIQUE chặn lần sau → CATEGORY_EXISTS.
- Xóa đúng lúc có sách được thêm vào thể loại: thủ tục khóa dòng thể loại (FOR UPDATE) nên câu thêm sách phải chờ; nếu vẫn lọt, khóa ngoại ON DELETE RESTRICT chặn (lỗi 1451) → CATEGORY_IN_USE.

Vì sao danh sách là THỦ TỤC chứ không phải VIEW: trên MySQL 8.0 và 8.4, view SQL SECURITY DEFINER có JOIN/GROUP BY bị từ chối (lỗi 1143/1356) khi phiên người gọi đang bật role (app_staff luôn bật r_staff), dù definer đủ quyền. Đã thử và xác nhận trên cả hai bản (python manage.py db_check_grants). Thủ tục DEFINER không bị lỗi này. Dòng DROP VIEW bên dưới xóa view cũ.

Root tạo bằng `python manage.py db_apply`. Chạy lại nhiều lần được.

**thủ tục `sp_category_list` | database/02_trigger_thu_tuc.sql | Claude Opus 5.5**  
#101 – Thủ tục trả danh sách thể loại kèm tổng số sách và số sách đang hiện, chỉ cho nhân viên.

**thủ tục `sp_category_create` | database/02_trigger_thu_tuc.sql | Claude Opus 5.5**  
#102 – Thủ tục thêm thể loại: kiểm tra nhân viên và đầu vào, chặn trùng, ghi nhật ký.

**thủ tục `sp_category_rename` | database/02_trigger_thu_tuc.sql | Claude Opus 5.5**  
#103 – Thủ tục sửa tên thể loại: khóa dòng, đổi tên và slug, chặn trùng, ghi nhật ký.

**thủ tục `sp_category_delete` | database/02_trigger_thu_tuc.sql | Claude Opus 5.5**  
#104 – Thủ tục xóa thể loại: khóa dòng, từ chối nếu còn sách, ghi nhật ký.

**phần "Thủ tục quản lý sách" | database/02_trigger_thu_tuc.sql | chưa đánh dấu**  
Quản lý sách (catalog_book) – chỉ nhân viên.

- `v_staff_books`: mọi cột của catalog_book (kể cả giá nhập, tồn kho), view MỘT bảng nên đọc được khi có role
- `sp_book_create`: thêm sách, nhập luôn tồn kho ban đầu
- `sp_book_update`: sửa thông tin (không đụng tồn kho, không ẩn/hiện)
- `sp_book_set_active`: ẩn hoặc hiện sách
- `sp_book_restock`: nhập thêm hàng
- `sp_book_reduce_stock`: giảm kho ngoại lệ (hỏng, thất lạc...)
- `sp_book_delete`: xóa hẳn sách: phải ẩn trước và chưa từng có trong đơn

Phân quyền: chỉ r_staff được SELECT view và EXECUTE sáu thủ tục. Không tài khoản ứng dụng nào được INSERT/UPDATE/DELETE thẳng vào catalog_book. Thủ tục tự kiểm tra p_actor_id là nhân viên đang hoạt động (NOT_STAFF).

Giới hạn nghiệp vụ:

tên sách, tác giả 1–255 ký tự (sau khi bỏ khoảng trắng hai đầu)

- `ISBN`: ISBN-10 hoặc ISBN-13, không dấu gạch (Django kiểm tra thêm chữ số kiểm tra) mô tả NULL hoặc tối đa 5.000 ký tự giá bán 1 – 100.000.000 đ; giá nhập 0 – 100.000.000 đ tồn kho 0 – 10.000 cuốn cho MỖI đầu sách, mọi lúc ảnh bìa NULL (Django hiện ảnh mặc định) hoặc covers/<32 hex>.<jpg|png|webp>

Mỗi thay đổi ghi core_auditlog trong CÙNG giao dịch (old/new JSON, USER(), id nhân viên). Lỗi ở bước nào cũng ROLLBACK.

Lỗi (SIGNAL SQLSTATE '45000', MESSAGE_TEXT là đúng một mã):

- `INVALID_INPUT`: tham số sai
- `NOT_STAFF`: p_actor_id không phải nhân viên đang hoạt động
- `ISBN_EXISTS`: trùng ISBN (UNIQUE, lỗi 1062)
- `CATEGORY_NOT_FOUND`: thể loại không tồn tại
- `BOOK_NOT_FOUND`: không có sách với id này
- `INVALID_QUANTITY`: số lượng nhập/giảm ngoài 1–10.000
- `STOCK_LIMIT`: nhập thêm làm tồn kho vượt 10.000
- `INSUFFICIENT_STOCK`: giảm nhiều hơn số đang có
- `BOOK_ACTIVE`: sách đang hiện, phải ẩn trước khi xóa
- `BOOK_HAS_ORDERS`: sách đã có trong đơn hàng, chỉ được ẩn

Race condition: mọi thủ tục đổi tồn kho hoặc xóa đều khóa dòng sách (FOR UPDATE), giống sp_place_order, nên nhập kho, giảm kho, xóa và khách đặt hàng cùng lúc phải xếp hàng; không mất số, kho không âm (thêm CHECK ck_book_stock_non_neg). Xóa đúng lúc có đơn mới: khóa ngoại RESTRICT của orders_orderitem chặn (lỗi 1451) → BOOK_HAS_ORDERS.

Root tạo bằng `python manage.py db_apply`. Chạy lại nhiều lần được.

**view `v_staff_books` | database/02_trigger_thu_tuc.sql | Claude Opus 5.5**  
#120 – View một bảng cho nhân viên xem mọi cột của sách, kể cả giá nhập và tồn kho.

**thủ tục `sp_book_create` | database/02_trigger_thu_tuc.sql | Claude Opus 5.5**  
#121 – Thủ tục thêm sách: kiểm tra nhân viên, đầu vào, thể loại, chặn trùng ISBN, ghi nhật ký.

**thủ tục `sp_book_update` | database/02_trigger_thu_tuc.sql | Claude Opus 5.5**  
#122 – Thủ tục sửa thông tin sách (không đụng tồn kho và ẩn/hiện), khóa dòng, ghi giá trị cũ/mới.

**thủ tục `sp_book_set_active` | database/02_trigger_thu_tuc.sql | Claude Opus 5.5**  
#123 – Thủ tục ẩn hoặc hiện sách, khóa dòng, ghi nhật ký.

**thủ tục `sp_book_restock` | database/02_trigger_thu_tuc.sql | Claude Opus 5.5**  
#124 – Thủ tục nhập thêm hàng: khóa dòng sách, chặn vượt 10.000 cuốn, ghi tồn kho trước và sau.

**thủ tục `sp_book_reduce_stock` | database/02_trigger_thu_tuc.sql | Claude Opus 5.5**  
#125 – Thủ tục giảm kho ngoại lệ: khóa dòng sách, không cho âm, ghi tồn kho trước và sau.

**thủ tục `sp_book_delete` | database/02_trigger_thu_tuc.sql | Claude Opus 5.5**  
#126 – Thủ tục xóa hẳn sách: khóa dòng, chỉ xóa sách đã ẩn và chưa từng có trong đơn, ghi nhật ký.

**phần "Thủ tục quản lý tài khoản khách" | database/02_trigger_thu_tuc.sql | chưa đánh dấu**  
Quản lý tài khoản khách cho admin (chốt 2026-11-16).

- `sp_staff_account_list`: xem danh sách, lọc theo trạng thái và username (gộp 3 nhu cầu xem/lọc vào 1 thủ tục)
- `sp_staff_account_get`: xem một tài khoản (trang xác nhận khóa/mở khóa)
- `sp_staff_account_lock`: khóa tài khoản (is_active = 0), có lý do
- `sp_staff_account_unlock`: mở khóa (is_active = 1), có lý do; cũng gỡ khóa tự động vì giữ kho (chốt 2026-11-20, khi bắt nhầm khách thật)

Chỉ r_staff được EXECUTE. Mỗi thủ tục tự kiểm tra p_actor_id là nhân viên đang hoạt động (NOT_STAFF). Chỉ thao tác trên tài khoản KHÁCH (is_staff = 0): tài khoản nhân viên, kể cả chính admin, coi như không tồn tại (ACCOUNT_NOT_FOUND) nên admin không tự khóa mình được.

Trạng thái (ưu tiên từ trên xuống):

- `locked`: is_active = 0                       → "Đã khóa"
- `auto_locked`: auto_locked_until > lúc này: tự khóa 24 giờ vì bỏ 3 đơn chưa thanh toán (33_order_cancel.sql) → "Khóa tự động (giữ kho)"
- `temp_locked`: axes ghi ≥ p_failure_limit lần sai trong p_cooloff_minutes phút gần nhất → "Tạm khóa" (lý do xem log)
- `unverified`: chưa xác nhận email                  → "Chưa xác nhận email"
- `active`: còn lại                              → "Hoạt động"

Ngưỡng axes truyền từ Django (AXES_FAILURE_LIMIT, AXES_COOLOFF_TIME) để không ghi cứng hai chỗ.

SĐT trả về là bản mã AES-GCM (Django giải mã, che bớt khi hiển thị). Không trả password, is_superuser.

Khóa/mở khóa: khóa dòng user FOR UPDATE, ghi core_auditlog (cũ/mới + lý do) trong cùng giao dịch. Trigger trg_user_guard_update (10_...) cho app_staff đổi đúng cột is_active của khách, các cột khác vẫn bị chặn; app_staff không có quyền UPDATE(is_active) trực tiếp nên chỉ hai thủ tục này đổi được. Khóa xong, Django xóa mọi phiên của khách đó (dashboard.account_services.lock_account → core.session_store.end_user_sessions; bảng phiên thuộc app_session nên không xóa ở đây). Phòng hờ: core.middleware.InactiveAccountSessionMiddleware hủy phiên của tài khoản is_active = 0 ở request kế tiếp, nên phiên cũ không sống lại khi mở khóa.

Mã lỗi: INVALID_INPUT, NOT_STAFF, ACCOUNT_NOT_FOUND, ALREADY_LOCKED, NOT_LOCKED Root tạo bằng `python manage.py db_apply`. Chạy lại nhiều lần được.

**thủ tục `sp_staff_account_list` | database/02_trigger_thu_tuc.sql | Claude Opus 5.5**  
#293 – Thủ tục admin xem tài khoản khách, lọc theo trạng thái (hoạt động/đã khóa/tạm khóa/chưa xác nhận) và username, SĐT trả bản mã.

**thủ tục `sp_staff_account_get` | database/02_trigger_thu_tuc.sql | Claude Opus 5.5**  
#294 – Thủ tục admin xem một tài khoản khách theo id (cùng cột và trạng thái như danh sách), tài khoản nhân viên coi như không có.

**thủ tục `sp_staff_account_lock` | database/02_trigger_thu_tuc.sql | Claude Opus 5.5**  
#295 – Thủ tục admin khóa tài khoản khách: kiểm tra lý do, khóa dòng, đặt is_active = 0, ghi core_auditlog kèm lý do cùng giao dịch.

**thủ tục `sp_staff_account_unlock` | database/02_trigger_thu_tuc.sql | Claude Opus 5.5**  
#296 – Thủ tục admin mở khóa tài khoản khách: kiểm tra lý do, khóa dòng, đặt is_active = 1, ghi core_auditlog kèm lý do cùng giao dịch. Đã viết lại bởi Claude Opus 5.5 khi gỡ được cả khóa tự động vì giữ kho.

Gỡ khóa tự động: đặt auto_locked_until = lúc này (không để NULL) để sp_order_hold_check chỉ đếm đơn bỏ SAU lần mở khóa này, khách không bị khóa lại ngay ở lần hủy kế tiếp.

**phần "Thủ tục nhật ký hệ thống và Event xóa log cũ" | database/02_trigger_thu_tuc.sql | chưa đánh dấu**  
Nhật ký hệ thống cho admin (chốt 2026-11-16).

- `sp_staff_security_events`: đọc core_securityevent (nhật ký bảo mật)
- `sp_staff_audit_log`: đọc core_auditlog (nhật ký thay đổi dữ liệu)
- `sp_purge_old_logs`: xóa log cũ hơn 1 năm (chỉ Event gọi)
- `ev_purge_old_logs`: Event mỗi ngày gọi sp_purge_old_logs

Hai thủ tục đọc chỉ r_staff được EXECUTE, tự kiểm tra p_actor_id là nhân viên (NOT_STAFF). Trả 2 bộ kết quả: (1) tổng số dòng khớp bộ lọc, (2) một trang dữ liệu mới nhất trước. Mọi bộ lọc đều tùy chọn (NULL = không lọc). Giới hạn: mỗi trang 1–100 dòng, offset tối đa 100000, khoảng ngày tối đa 400 ngày; từ khóa tìm kiếm thoát \ % _ (LIKE).

Không khóa cứng log (chốt): tài khoản ứng dụng chỉ có INSERT trên 2 bảng log như trước; chỉ definer có DELETE, dùng trong sp_purge_old_logs. Xóa theo lô 5000 dòng để không giữ khóa lâu.

Mã lỗi: INVALID_INPUT, NOT_STAFF. Root tạo bằng `python manage.py db_apply`. Chạy lại nhiều lần được.

**thủ tục `sp_staff_security_events` | database/02_trigger_thu_tuc.sql | Claude Opus 5.5**  
#322 – Thủ tục admin đọc nhật ký bảo mật: lọc loại, mức độ, khoảng ngày, username/IP; trả tổng số và một trang mới nhất trước.

**thủ tục `sp_staff_audit_log` | database/02_trigger_thu_tuc.sql | Claude Opus 5.5**  
#323 – Thủ tục admin đọc nhật ký thay đổi dữ liệu: lọc bảng, hành động, khoảng ngày, id bản ghi; kèm username người thực hiện.

**thủ tục `sp_purge_old_logs` | database/02_trigger_thu_tuc.sql | Claude Opus 5.5**  
#324 – Thủ tục xóa nhật ký bảo mật và nhật ký thay đổi cũ hơn 1 năm, theo lô 5000 dòng, tối đa 40 lô mỗi lần chạy.

**event `ev_purge_old_logs` | database/02_trigger_thu_tuc.sql | Claude Opus 5.5**  
#325 – MySQL Event mỗi ngày (03:00 giờ Việt Nam) gọi sp_purge_old_logs để giữ nhật ký tối đa 1 năm.

**phần "Thủ tục quản lý đơn hàng của admin" | database/02_trigger_thu_tuc.sql | chưa đánh dấu**  
Quản lý đơn hàng của admin (chốt 2026-11-16):

- `sp_staff_order_list`: danh sách đơn đơn giản, lọc theo trạng thái
- `sp_staff_order_get`: chi tiết một đơn (sách, thông tin giao hàng bản mã, giao dịch thanh toán) – Django bắt xác thực lại + ghi log
- `sp_staff_order_confirm`: Đã thanh toán → Đã tiếp nhận
- `sp_staff_order_pack`: Đã tiếp nhận  → Đã đóng gói
- `sp_staff_order_ship`: Đã đóng gói   → Đang giao
- `sp_staff_order_deliver`: Đang giao     → Đã giao
- `sp_staff_order_advance`: thủ tục nội bộ dùng chung cho 4 thủ tục trên (không cấp cho tài khoản ứng dụng nào)

Chỉ r_staff được EXECUTE các thủ tục công khai. Mỗi thủ tục tự kiểm tra p_actor_id là nhân viên đang hoạt động (NOT_STAFF).

Chuyển trạng thái: buộc theo luồng, không có quay lại. Mỗi thủ tục chỉ nhận đúng MỘT trạng thái trước; khóa dòng đơn FOR UPDATE rồi mới kiểm tra, nên hai tab cùng bấm hoặc bấm hai lần thì lần sau báo ORDER_WRONG_STATUS, không nhảy cóc. Trigger 32_trg_orders_guard.sql là lớp cuối (chặn cả root). Nhật ký: trigger 34_trg_orders_audit.sql tự ghi (nguồn "Quản trị"); thủ tục đặt biến phiên @bookstore_actor_id để trigger ghi đúng id người bấm, rồi xóa ngay sau khi cập nhật.

Mã lỗi: INVALID_INPUT, NOT_STAFF, ORDER_NOT_FOUND, ORDER_WRONG_STATUS Root tạo bằng `python manage.py db_apply`. Chạy lại nhiều lần được.

**thủ tục `sp_staff_order_list` | database/02_trigger_thu_tuc.sql | Claude Opus 5.5**  
#372 – Thủ tục admin xem danh sách đơn (mã, username, trạng thái, tổng tiền, ngày đặt, số cuốn), lọc theo trạng thái hoặc nhóm Cần xử lý, trả tổng số và một trang; không trả thông tin giao hàng.

**thủ tục `sp_staff_order_get` | database/02_trigger_thu_tuc.sql | Claude Opus 5.5**  
#373 – Thủ tục admin đọc chi tiết một đơn: thông tin đơn, người đặt, SĐT/địa chỉ giao hàng bản mã (Django giải mã), giao dịch thanh toán thành công và danh sách sách.

**thủ tục `sp_staff_order_advance` | database/02_trigger_thu_tuc.sql | Claude Opus 5.5**  
#374 – Thủ tục nội bộ chuyển đơn đúng một bước: kiểm tra nhân viên, khóa dòng đơn, chỉ nhận đúng trạng thái trước, đặt id người bấm cho trigger nhật ký.

**thủ tục `sp_staff_order_confirm` | database/02_trigger_thu_tuc.sql | Claude Opus 5.5**  
#375 – Bốn thủ tục admin chuyển trạng thái đơn theo đúng luồng: tiếp nhận, đóng gói, giao hàng, đã giao; mỗi thủ tục cố định trạng thái trước và sau.

**phần "Thủ tục trang Tổng quan" | database/02_trigger_thu_tuc.sql | chưa đánh dấu**  
Trang Tổng quan của admin – báo cáo cơ bản (chốt 2026-11-16):

- `sp_staff_dashboard_orders`: đơn cần xử lý theo từng bước, đơn mới/hủy hôm nay, doanh thu hôm nay / 7 ngày / tháng này
- `sp_staff_dashboard_stock`: số sách sắp hết, hết hàng, 5 cuốn còn ít nhất
- `sp_staff_dashboard_security`: sự kiện cảnh báo/nghiêm trọng 24 giờ, đăng nhập sai hôm nay
- `sp_staff_dashboard_backup`: lần sao lưu thành công, lỗi, kiểm tra khôi phục gần nhất (đọc từ nhật ký do lệnh sao lưu ghi)

Không dùng view: cần COUNT/SUM/WHERE, mà MySQL từ chối view DEFINER có lọc hoặc gộp nhóm khi phiên đang bật role (lỗi 1143/1356). Chỉ r_staff được EXECUTE; mỗi thủ tục tự kiểm tra p_actor_id là nhân viên (NOT_STAFF).

Mốc thời gian (đầu ngày, đầu tháng theo giờ Việt Nam) do Django tính rồi truyền xuống dạng UTC; ngưỡng "sắp hết" lấy từ LOW_STOCK_THRESHOLD của Django (không ghi cứng hai nơi).

Doanh thu: tổng `total` của đơn từ "Đã thanh toán" trở đi, tính theo paid_at (đơn đã thanh toán không hủy được nên không bị trừ lại); gồm cả thanh toán mô phỏng.

Không trả dữ liệu cá nhân nào (chỉ con số, tên sách). Mã lỗi: INVALID_INPUT, NOT_STAFF. Root tạo bằng `python manage.py db_apply`.

**thủ tục `sp_staff_dashboard_orders` | database/02_trigger_thu_tuc.sql | Claude Opus 5.5**  
#392 – Thủ tục tổng quan đơn hàng: số đơn cần xử lý theo từng bước, đơn mới và đơn hủy hôm nay, doanh thu hôm nay/7 ngày/tháng này theo ngày thanh toán.

**thủ tục `sp_staff_dashboard_stock` | database/02_trigger_thu_tuc.sql | Claude Opus 5.5**  
#393 – Thủ tục tổng quan kho: số sách đang bán sắp hết (1 đến ngưỡng) và hết hàng, 5 cuốn đang bán còn ít nhất.

**thủ tục `sp_staff_dashboard_security` | database/02_trigger_thu_tuc.sql | Claude Opus 5.5**  
#394 – Thủ tục tổng quan bảo mật: số sự kiện mức cảnh báo/nghiêm trọng trong 24 giờ và số lần đăng nhập sai từ đầu ngày, chỉ trả con số.

**thủ tục `sp_staff_dashboard_backup` | database/02_trigger_thu_tuc.sql | Claude Opus 5.5**  
#573 – Thủ tục trạng thái sao lưu cho trang Tổng quan: bản ghi gần nhất của sao lưu thành công, sao lưu lỗi và kiểm tra khôi phục (thời điểm + chi tiết JSON không chứa bí mật).

**phần "Thủ tục đếm đăng nhập sai theo IP" | database/02_trigger_thu_tuc.sql | chưa đánh dấu**  
Chặn dò mật khẩu rải từ một IP (password spraying) – báo cáo rà soát T3.2, chốt 2026-11-20.

django-axes chỉ khóa theo cặp (tên đăng nhập, IP): một IP thử vài mật khẩu trên rất nhiều tài khoản thì không cặp nào chạm ngưỡng. Thủ tục này đếm số lần đăng nhập sai (core_securityevent 'login_failed') của MỘT IP, gộp mọi tài khoản, trong p_minutes phút gần nhất; Django so với ngưỡng (LOGIN_IP_FAILURE_LIMIT) và từ chối đăng nhập từ IP đó (429).

Đếm từ bảng nhật ký (bền, không mất khi khởi động lại) chứ không từ bảng axes (axes xóa bản ghi sau 15 phút, không đủ cửa sổ 60 phút) hay cache. r_customer chỉ có EXECUTE: thủ tục trả đúng một con số, tài khoản ứng dụng vẫn không đọc được nội dung nhật ký.

Mã lỗi: INVALID_INPUT Root tạo bằng `python manage.py db_apply`. Chạy lại nhiều lần được.

**thủ tục `sp_login_ip_failures` | database/02_trigger_thu_tuc.sql | Claude Opus 5.5**  
#544 – Thủ tục đọc đếm số lần đăng nhập sai của một IP (mọi tài khoản) trong N phút gần nhất, chỉ trả một con số.

### `database/03_phan_quyen.sql`

**cả file | database/03_phan_quyen.sql | Claude Opus 5.5**  
#457 – app_customer chỉ còn đọc bảng tài khoản, thu hồi INSERT/UPDATE cũ.  
#451 – Thu hồi mọi quyền của r_customer trên bảng phiên django_session.  
#527 – Thu hồi mọi quyền của r_customer trên 3 bảng khóa đăng nhập django-axes.  
#452 – Cấp cho r_session đúng 4 quyền trên bảng phiên, không quyền nào khác.  
#458 – Cấp cho r_auth đúng SELECT/INSERT/UPDATE trên bảng tài khoản.  
#476 – Cấp cho r_auth quyền trên 2 bảng xác thực 2 bước, không cấp cho role nào khác.  
#528 – Cấp cho r_auth đúng quyền django-axes cần trên 3 bảng khóa đăng nhập.  
#535 – Cấp cho definer quyền đổi đúng cột auto_locked_until và ghi log order_hold_abuse khi Event khóa tài khoản.  
#545 – Cấp quyền gọi thủ tục đếm lần đăng nhập sai theo IP cho r_customer.

Cấp quyền cho 4 vai trò r_customer, r_staff, r_session, r_auth và cho bookstore_definer (chương 6.2). Root chạy file này SAU khi `python manage.py migrate` đã tạo bảng (MySQL không cho cấp quyền trên bảng chưa tồn tại), bằng:

python manage.py db_apply

Chạy lại nhiều lần không sao (GRANT trùng không báo lỗi). Mỗi khi có bảng/view/thủ tục mới cần quyền: thêm vào file này rồi chạy lại.

Nguyên tắc:

- Bảng nghiệp vụ (catalog_*, orders_*, payments_*, core_auditlog): KHÔNG cấp gì. Sau này chỉ cấp SELECT trên view và EXECUTE trên thủ tục.
- Bảng nội bộ của Django: cấp đúng mức Django cần để chạy.
- Không cấp DELETE trên accounts_user, không cấp gì trên bảng log ngoài INSERT.

**nhóm quyền "bookstore_definer" | database/03_phan_quyen.sql | chưa đánh dấu**  
bookstore_definer: chủ sở hữu trigger/view/thủ tục (khóa đăng nhập) Trigger chạy bằng quyền của definer: cần TRIGGER để chạy và SELECT để đọc giá trị NEW./OLD. các cột.

**nhóm quyền "Trigger trg_pwhist_*" | database/03_phan_quyen.sql | chưa đánh dấu**  
Trigger trg_pwhist_* (phần 11 của 02_trigger_thu_tuc.sql): thêm mã băm mới, đọc để tìm dòng thứ 5, xóa các dòng cũ hơn. Chỉ definer có INSERT/DELETE trên bảng này.

**nhóm quyền "Tài khoản" | database/03_phan_quyen.sql | chưa đánh dấu**  
Tài khoản: r_customer CHỈ ĐỌC (đăng nhập, request.user, kiểm tra trùng email/tên). Mọi lệnh GHI (đăng ký, last_login, hồ sơ, đổi/đặt lại mật khẩu) đi qua r_auth (core.db_routers.AccountWriteRouter). Trước đây r_customer có INSERT, UPDATE nên SQL injection ở bất kỳ trang nào cũng tự mở khóa, đổi email/mật khẩu của khách khác, hoặc tạo tài khoản "đã xác nhận" mang email người khác. Câu REVOKE gỡ quyền cũ trên CSDL đã cài trước đó; IF EXISTS để chạy lại không báo lỗi.

**nhóm quyền "Lịch sử mật khẩu" | database/03_phan_quyen.sql | chưa đánh dấu**  
Lịch sử mật khẩu: chỉ ĐỌC để so sánh mật khẩu mới với 5 mã băm gần nhất. Không cấp INSERT/UPDATE/DELETE: việc ghi do trigger làm, nên dù có lỗi SQL injection, kẻ tấn công cũng không xóa được lịch sử để dùng lại mật khẩu cũ.

**nhóm quyền "Phiên đăng nhập" | database/03_phan_quyen.sql | chưa đánh dấu**  
Phiên đăng nhập: KHÔNG cấp cho r_customer nữa (chuyển sang r_session bên dưới). Trước đây r_customer có cả 4 quyền trên django_session, nên SQL injection qua app_customer đọc được cookie của admin (phát hiện số 13). Câu dưới gỡ quyền cũ trên CSDL đã cài trước đó; IF EXISTS để chạy lại không báo lỗi.

**nhóm quyền "Bảng khóa đăng nhập django-axes" | database/03_phan_quyen.sql | chưa đánh dấu**  
Bảng khóa đăng nhập django-axes: KHÔNG cấp cho r_customer nữa (chuyển sang r_auth bên dưới, core.db_routers.LockoutRouter). Trước đây r_customer có DELETE trên axes_accessattempt, nên SQL injection qua app_customer xóa được trạng thái khóa của mọi tài khoản, kể cả admin (báo cáo rà soát T3.3). Câu dưới gỡ quyền cũ.

**nhóm quyền "r_session" | database/03_phan_quyen.sql | chưa đánh dấu**  
r_session: kết nối "session" (app_session), chỉ bộ lưu phiên của Django dùng (core.session_store + core.db_routers.SessionRouter). Đúng một bảng, không gì khác: lộ app_session cũng không đụng được sách, đơn, tài khoản; còn bảng phiên chỉ chứa mã băm của cookie nên đọc được cũng không dùng làm cookie được.

**nhóm quyền "r_auth" | database/03_phan_quyen.sql | chưa đánh dấu**  
r_auth: kết nối "auth" (app_auth), chỉ lệnh ghi bảng tài khoản của Django dùng. Trigger trg_user_guard_* giới hạn thêm: không tạo/nâng nhân viên, dòng nhân viên chỉ đổi last_login, dòng khách không đổi is_active/email/username/email_verified/date_joined. Không quyền nào khác: lộ app_auth cũng không đụng được sách, đơn, phiên, nhật ký.

**nhóm quyền "Xác thực 2 bước" | database/03_phan_quyen.sql | chưa đánh dấu**  
Xác thực 2 bước: CHỈ r_auth đụng được 2 bảng này (chuỗi bí mật TOTP mã hóa, mã băm của mã dự phòng). r_customer, r_staff, r_session không có quyền gì. Trigger 12 chặn r_auth tạo/xóa/sửa 2 bước của nhân viên.

**nhóm quyền "Khóa đăng nhập django-axes" | database/03_phan_quyen.sql | chưa đánh dấu**  
Khóa đăng nhập django-axes (đếm sai, khóa 15 phút, xóa khi đăng nhập đúng / đặt lại mật khẩu / hết hạn): chỉ r_auth. Admin đọc "Tạm khóa" qua definer.

**nhóm quyền "r_staff" | database/03_phan_quyen.sql | chưa đánh dấu**  
r_staff: kết nối "staff" (app_staff), chỉ app dashboard dùng Phần lớn quyền (thủ tục sp_category_*, sp_book_*...) thêm ở các bước sau.

**nhóm quyền "Nhân viên sửa họ, tên, SĐT của chính mình" | database/03_phan_quyen.sql | chưa đánh dấu**  
Nhân viên sửa họ, tên, SĐT của chính mình (dashboard:profile_update). Quyền THEO CỘT: chỉ 3 cột được UPDATE, chỉ đọc được cột id (cho WHERE id = ...). app_staff không đụng được password, email, is_staff, is_superuser. Trigger trg_user_guard_update chặn thêm: app_staff chỉ sửa được dòng nhân viên.

**nhóm quyền "sp_place_order" | database/03_phan_quyen.sql | chưa đánh dấu**  
sp_place_order (phần 30 của `database/02_trigger_thu_tuc.sql`) Definer đọc/ghi đúng các bảng thủ tục cần. Từ MySQL 8.0.22, câu khóa dòng SELECT ... FOR UPDATE cần SELECT cộng thêm UPDATE hoặc DELETE trên bảng đó.

**nhóm quyền "Đặt hàng" | database/03_phan_quyen.sql | chưa đánh dấu**  
Đặt hàng (2026-11-16): đọc đơn của chính khách + trigger khóa đơn (phần 30 của `database/02_trigger_thu_tuc.sql`, 32_trg_orders_guard.sql). Definer: đọc chi tiết đơn cho sp_order_get; TRIGGER để chạy các trigger khóa đơn (trigger chạy bằng quyền definer).

**nhóm quyền "Hủy đơn và hủy đơn quá hạn" | database/03_phan_quyen.sql | chưa đánh dấu**  
Hủy đơn và hủy đơn quá hạn (phần 33 của `database/02_trigger_thu_tuc.sql`). Definer: đổi trạng thái đơn (trigger 32 vẫn chỉ cho pending → cancelled), cộng lại kho (đã có UPDATE catalog_book), gọi thủ tục nội bộ; EVENT để Event ev_cancel_expired_orders chạy bằng quyền definer. r_customer: chỉ sp_order_cancel. sp_cancel_expired_orders, sp_order_expire_one không cấp cho tài khoản ứng dụng nào (chỉ Event gọi).

**nhóm quyền "Thể loại sách" | database/03_phan_quyen.sql | chưa đánh dấu**  
Thể loại sách (phần 40 của `database/02_trigger_thu_tuc.sql`) Definer: đọc/khóa/ghi catalog_category, đếm sách, ghi nhật ký. r_staff: chỉ gọi bốn thủ tục; không có quyền nào trên bảng. r_customer: không có gì ở đây.

**nhóm quyền "Sách" | database/03_phan_quyen.sql | chưa đánh dấu**  
Sách (phần 41 của `database/02_trigger_thu_tuc.sql`) Definer: thêm/sửa/xóa catalog_book, đọc orders_orderitem để biết sách đã bán chưa. r_staff: chỉ đọc view một bảng v_staff_books và gọi sáu thủ tục. r_customer: không có gì ở đây (giá nhập, tồn kho chi tiết là của nhân viên).

**nhóm quyền "Danh mục sách cho khách" | database/03_phan_quyen.sql | chưa đánh dấu**  
Danh mục sách cho khách (phần 20 của `database/02_trigger_thu_tuc.sql`) Definer: đọc thêm catalog_review để tính điểm đánh giá. r_customer: chỉ gọi hai thủ tục đọc; không có quyền nào trên catalog_*.

**nhóm quyền "Đánh giá sách" | database/03_phan_quyen.sql | chưa đánh dấu**  
Đánh giá sách (phần 21 của `database/02_trigger_thu_tuc.sql`) Definer: thêm/sửa catalog_review (đã có SELECT ở phần danh mục cho khách), đọc accounts_user và catalog_book để kiểm tra (đã có). r_customer: chỉ gọi hai thủ tục; không có quyền ghi nào trên catalog_review.

**nhóm quyền "Trang chi tiết sách" | database/03_phan_quyen.sql | chưa đánh dấu**  
Trang chi tiết sách (sp_public_book_get trong phần 20 của 02_trigger_thu_tuc.sql, sp_review_list trong phần 21 của 02_trigger_thu_tuc.sql). Definer đã có SELECT trên các bảng cần đọc.

**nhóm quyền "Thêm vào giỏ hàng" | database/03_phan_quyen.sql | chưa đánh dấu**  
Thêm vào giỏ hàng (phần 31 của `database/02_trigger_thu_tuc.sql`) Definer: tạo giỏ, thêm/sửa dòng giỏ (đã có SELECT/UPDATE giỏ, SELECT/DELETE dòng giỏ cho sp_place_order). r_customer: chỉ gọi thủ tục; không có quyền nào trên orders_cart*.

**nhóm quyền "Trang giỏ hàng" | database/03_phan_quyen.sql | chưa đánh dấu**  
Trang giỏ hàng: đọc, đổi số lượng, gỡ (phần 31 của `database/02_trigger_thu_tuc.sql`) bookstore_definer đã có SELECT, UPDATE trên orders_cart và SELECT, INSERT, UPDATE, DELETE trên orders_cartitem (ở trên), không cần cấp thêm quyền bảng. r_customer: chỉ gọi thủ tục.

**nhóm quyền "Quản lý tài khoản khách" | database/03_phan_quyen.sql | chưa đánh dấu**  
Quản lý tài khoản khách (phần 42 của `database/02_trigger_thu_tuc.sql`) Definer: đổi is_active của khách (trigger chỉ cho đúng cột này), đọc bảng axes để biết tài khoản "Tạm khóa", ghi core_auditlog (đã có INSERT). r_staff: chỉ gọi bốn thủ tục; không có quyền UPDATE(is_active) trực tiếp.

**nhóm quyền "Nhật ký hệ thống" | database/03_phan_quyen.sql | chưa đánh dấu**  
Nhật ký hệ thống (phần 34 của `database/02_trigger_thu_tuc.sql`, 43_logs.sql) Definer: đọc 2 bảng log cho thủ tục đọc; xóa log cũ hơn 1 năm (chỉ trong sp_purge_old_logs do Event gọi). Tài khoản ứng dụng vẫn chỉ có INSERT. r_staff: chỉ gọi 2 thủ tục đọc. sp_purge_old_logs không cấp cho ai (chỉ Event).

**nhóm quyền "Thanh toán mô phỏng" | database/03_phan_quyen.sql | chưa đánh dấu**  
Thanh toán mô phỏng (phần 35 của `database/02_trigger_thu_tuc.sql`) Definer: ghi giao dịch vào payments_payment (trigger cấm sửa/xóa), đổi đơn sang 'paid' (đã có UPDATE orders_order, trigger 32 chỉ cho pending → paid). r_customer: chỉ gọi sp_payment_simulate; không có quyền nào trên payments_payment. Quyền EXECUTE của r_customer KHÔNG cấp ở file này: lệnh db_apply cấp khi PAYMENT_SIMULATION=True và thu hồi khi False (báo cáo rà soát T3.3 – trước đây tắt cờ chỉ chặn ở Django, MySQL vẫn cho gọi). Đổi cờ trong .env thì phải chạy lại db_apply. Khi lắp cổng thật thì bỏ thủ tục này.

**nhóm quyền "Đơn hàng của tôi" | database/03_phan_quyen.sql | chưa đánh dấu**  
Đơn hàng của tôi (phần 36 của `database/02_trigger_thu_tuc.sql`) Definer: đọc orders_order, orders_orderitem (đã có). r_customer: chỉ gọi sp_order_list_mine (thủ tục tự lọc theo user_id). r_staff: không có gì ở đây.

**nhóm quyền "Quản lý đơn hàng của admin" | database/03_phan_quyen.sql | chưa đánh dấu**  
Quản lý đơn hàng của admin (phần 44 của `database/02_trigger_thu_tuc.sql`) Definer: đọc orders_order, orders_orderitem, accounts_user, payments_payment, đổi trạng thái đơn (đã có cả; trigger 32 chỉ cho đi tới đúng một bước). r_staff: chỉ gọi 6 thủ tục công khai. sp_staff_order_advance là thủ tục nội bộ, không cấp cho tài khoản ứng dụng nào. r_customer: không có gì ở đây.

**nhóm quyền "Trang Tổng quan" | database/03_phan_quyen.sql | chưa đánh dấu**  
Trang Tổng quan (phần 45 của `database/02_trigger_thu_tuc.sql`) Definer: đọc orders_order, catalog_book, accounts_user, core_securityevent (đã có cả). r_staff: chỉ gọi 3 thủ tục đọc. r_customer: không có gì.

**nhóm quyền "Chặn dò mật khẩu rải từ một IP" | database/03_phan_quyen.sql | chưa đánh dấu**  
Chặn dò mật khẩu rải từ một IP (phần 46 của `database/02_trigger_thu_tuc.sql`). Definer đã có SELECT core_securityevent. r_customer: chỉ gọi thủ tục đếm (trang đăng nhập chạy trên kết nối default), không đọc được nhật ký.

**nhóm quyền "Tài khoản sao lưu bookstore_backup" | database/03_phan_quyen.sql | chưa đánh dấu**  
Tài khoản sao lưu bookstore_backup (db_setup tạo, chỉ @localhost: chỉ đăng nhập được bằng socket ngay trên máy/container MySQL, không qua mạng). CHỈ ĐỌC: đủ cho mysqldump --single-transaction --routines --triggers --events. Không INSERT/UPDATE/DELETE/DROP/ALTER, không FILE, không LOCK TABLES (giao dịch nhất quán thay cho khóa bảng), không PROCESS (--no-tablespaces). Lộ mật khẩu tài khoản này không phá được dữ liệu.

### `database/config/my.cnf`

**cả file | database/config/my.cnf | chưa đánh dấu**  
Cấu hình MySQL 8.4 cho secure-bookstore (mục D của checklist). compose.yaml gắn file này vào /etc/mysql/conf.d/bookstore.cnf (chỉ đọc). Sửa xong: docker compose restart db

Máy cài MySQL thường (Windows): KHÔNG bắt buộc. Muốn giống máy demo thì chép phần [mysqld] dưới đây vào my.ini (xem database/README.md), trừ skip-name-resolve và secure_file_priv (đường dẫn khác).

**mục `bind-address` | database/config/my.cnf | chưa đánh dấu**  
--- Mạng --- Trong container MySQL phải nghe trên mọi giao diện của container, nhưng compose.yaml chỉ mở cổng ra 127.0.0.1 của máy chủ: máy khác trong mạng LAN không kết nối được cổng 3306.

**mục `require_secure_transport` | database/config/my.cnf | chưa đánh dấu**  
--- Mã hóa kết nối (TLS) --- Từ chối kết nối TCP không mã hóa. Image mysql tự sinh chứng chỉ khi khởi tạo. Kết nối qua socket bên trong container (root, healthcheck) vẫn được phép.

**mục `local_infile` | database/config/my.cnf | chưa đánh dấu**  
--- Đọc/ghi file từ SQL --- Cấm LOAD DATA LOCAL INFILE (đọc file trên máy client)

**mục `secure_file_priv` | database/config/my.cnf | chưa đánh dấu**  
LOAD DATA / SELECT ... INTO OUTFILE chỉ trong thư mục này; thêm vào đó không tài khoản ứng dụng nào có quyền FILE.

**mục `event_scheduler` | database/config/my.cnf | chưa đánh dấu**  
Chính sách mật khẩu (validate_password) KHÔNG đặt ở đây: lệnh `python manage.py db_setup` cài component và lưu cấu hình bằng SET PERSIST, chạy giống nhau trên Docker lẫn Windows.


## Triển khai (Nginx, Gunicorn)

### `deploy/gunicorn.conf.py`

**cả file | deploy/gunicorn.conf.py | chưa đánh dấu**  
Cấu hình Gunicorn cho secure-bookstore (xem docs/trien-khai-nginx.md).

Chạy từ thư mục backend/:

gunicorn -c ../deploy/gunicorn.conf.py

**biến `workers` | deploy/gunicorn.conf.py | chưa đánh dấu**  
1 tiến trình nhiều luồng: các bộ đếm giới hạn tần suất (cache bộ nhớ của Django) dùng chung một chỗ, không bị chia theo tiến trình. Muốn nhiều tiến trình thì phải đổi sang cache chung (Redis...) trước.

**biến `accesslog` | deploy/gunicorn.conf.py | chưa đánh dấu**  
Không ghi access log ở Gunicorn: Nginx đã ghi (IP thật), và đường dẫn có thể chứa mã một lần (link đăng ký, đặt lại mật khẩu).

### `deploy/nginx/secure-bookstore.conf`

**cả file | deploy/nginx/secure-bookstore.conf | chưa đánh dấu**  
Nginx trước Gunicorn cho secure-bookstore (xem docs/trien-khai-nginx.md).

Trình duyệt ──HTTPS──> Nginx (:443) ──HTTP──> Gunicorn (127.0.0.1:8000) ──> Django

Trước khi dùng, sửa 3 chỗ có chữ ĐỔI:

- server_name: tên miền demo (phải có trong DJANGO_ALLOWED_HOSTS của .env);
- đường dẫn chứng chỉ TLS;
- /srv/secure-bookstore: thư mục repo trên máy chủ.

Phát hiện số 12: Django chỉ thấy IP của Nginx (127.0.0.1), nên mọi người dùng chung một IP và kẻ tấn công khóa được đăng nhập của admin. Nginx phải GHI ĐÈ X-Real-IP bằng $remote_addr (IP thật của kết nối); Django chỉ tin header này khi request đến từ TRUSTED_PROXY_IPS (core/client_ip.py). Không dùng $proxy_add_x_forwarded_for: biến đó NỐI THÊM vào giá trị client tự gửi.

**mục `map` | deploy/nginx/secure-bookstore.conf | chưa đánh dấu**  
Không ghi access log cho 2 đường dẫn chứa mã một lần (chốt 2026-11-20, T4.1): link đặt lại mật khẩu và link xác nhận đăng ký. Django vẫn tự ghi các lượt này vào nhật ký bảo mật nhưng đã che mã (SECURITY_LOG_SECRET_PATHS). Khối map phải nằm trong ngữ cảnh http: file này được include từ http { } (conf.d/sites-enabled).

**mục `location` | deploy/nginx/secure-bookstore.conf | chưa đánh dấu**  
Ảnh bìa người dùng tải lên: chỉ phục vụ file .webp, không thực thi gì (docs/quan-ly-kho-sach.md mục 5).


## GitHub (CI, mẫu PR)

### `.github/CODEOWNERS`

**cả file | .github/CODEOWNERS | chưa đánh dấu**  
Ai phải duyệt PR khi PR đụng tới file nào (GitHub tự gắn người duyệt). Dòng sau ghi đè dòng trước. Chỉ ghi tài khoản có quyền ghi vào repo. Thêm tài khoản GitHub của các bạn khác vào đây khi đã mời vào repo, ví dụ: /frontend/templates/shop/ @TuanThanh05 @ten-ban-fe1

### `.github/workflows/ci.yml`

**cả file | .github/workflows/ci.yml | chưa đánh dấu**  
Chạy tự động trên mỗi Pull Request và mỗi lần main thay đổi. Dựng một MySQL 8.4 tạm, rồi chạy đúng các lệnh mọi người chạy trên máy mình: db_setup → migrate → db_apply → db_check_grants → check → test, và quét lỗi bảo mật trong code. PR nào làm hỏng một bước là thấy dấu X đỏ ngay, trước khi merge vào main.
