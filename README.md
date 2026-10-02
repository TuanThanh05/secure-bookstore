# Secure Bookstore

## Nhóm 5

**Đề tài:** Xây dựng trang web bán sách đảm bảo an toàn bảo mật

## Giới thiệu

Secure Bookstore là đồ án xây dựng một trang web bán sách với các chức năng cơ bản của một hệ thống bán hàng trực tuyến.

Bên cạnh việc đáp ứng các nghiệp vụ bán sách, đồ án tập trung vào việc áp dụng các biện pháp bảo vệ ứng dụng web và cơ sở dữ liệu, đặc biệt ở các khu vực như xác thực người dùng, phân quyền, phiên đăng nhập, xử lý dữ liệu đầu vào, đơn hàng, thanh toán và truy cập cơ sở dữ liệu.

Mục tiêu của dự án là xây dựng một hệ thống có chức năng hợp lý, dễ phát triển theo từng module và có các lớp bảo vệ.

---

## Nghiệp vụ chính

Hệ thống dự kiến hỗ trợ các nghiệp vụ chính:

- xem và tìm kiếm sách;
- xem thông tin chi tiết sách;
- đăng ký và đăng nhập tài khoản;
- đăng nhập bằng Google;
- quản lý thông tin cá nhân;
- quản lý giỏ hàng;
- đặt hàng;
- thanh toán khi nhận hàng hoặc thanh toán trực tuyến;
- theo dõi trạng thái đơn hàng;
- đánh giá sách;
- quản lý sách, tác giả, thể loại và nhà xuất bản;
- quản lý nhà cung cấp và tồn kho;
- quản lý đơn hàng;
- quản lý người dùng và phân quyền;
- theo dõi các sự kiện và hoạt động liên quan đến bảo mật.

---

## Nhóm người dùng

Hệ thống được phân chia thành các nhóm người dùng chính:

- khách vãng lai;
- khách hàng;
- nhân viên;
- quản lý cửa hàng sách;
- quản trị viên an ninh;
- quản trị viên vận hành;
- quản trị viên toàn quyền.

Mỗi nhóm chỉ được sử dụng các chức năng và truy cập dữ liệu phù hợp với nhiệm vụ của mình.

---

## Công nghệ dự kiến

### Giao diện

- React;
- TypeScript;
- Vite.

### Máy chủ ứng dụng

- Node.js;
- NestJS;
- TypeScript.

### Cơ sở dữ liệu

- MySQL;
- InnoDB;
- Docker cho môi trường phát triển cơ sở dữ liệu.

### Triển khai và quản lý mã nguồn

- Caddy;
- HTTPS;
- Git;
- GitHub.

### Dịch vụ hỗ trợ

- Google Login;
- MoMo Sandbox;
- dịch vụ gửi email.

---

## Một số thư viện và công cụ dự kiến

- Argon2 để bảo vệ mật khẩu;
- `class-validator` để kiểm tra dữ liệu;
- `mysql2` để kết nối MySQL;
- thư viện giới hạn số lượng yêu cầu;
- thư viện hỗ trợ chống XSS và CSRF khi cần;
- Jest hoặc Vitest để kiểm thử;
- Supertest để kiểm thử API;
- Playwright để kiểm thử giao diện;
- OWASP ZAP để hỗ trợ kiểm tra bảo mật.

Việc lựa chọn thư viện có thể tiếp tục thay đổi trong quá trình phát triển.

---

## Các khu vực tập trung bảo vệ

Đồ án tập trung bảo vệ các khu vực chính sau:

- tài khoản và mật khẩu;
- đăng nhập và xác thực;
- phân quyền người dùng;
- phiên đăng nhập và cookie;
- dữ liệu đầu vào;
- thông tin cá nhân;
- giỏ hàng và đơn hàng;
- giá sản phẩm và tổng tiền;
- thanh toán;
- tồn kho;
- cơ sở dữ liệu;
- nhật ký hoạt động và sự kiện bảo mật;
- dữ liệu truyền giữa trình duyệt và máy chủ.

---

## Các rủi ro được xem xét

Một số dạng tấn công và rủi ro được xem xét trong đồ án:

- SQL Injection;
- XSS;
- CSRF;
- tấn công vào chức năng đăng nhập;
- dò mật khẩu;
- chiếm hoặc sử dụng lại phiên đăng nhập;
- truy cập dữ liệu không đúng quyền;
- thay đổi tham số trái phép;
- sửa giá hoặc thông tin thanh toán;
- lạm dụng luồng xử lý nghiệp vụ;
- truy cập cơ sở dữ liệu vượt quá quyền được cấp;
- làm lộ thông tin nhạy cảm.

---

## Phương pháp bảo vệ

Một số phương pháp dự kiến áp dụng:

- sử dụng HTTPS;
- kiểm tra dữ liệu đầu vào;
- sử dụng Prepared Statement;
- sử dụng Stored Procedure cho các nghiệp vụ phù hợp;
- sử dụng View để giới hạn dữ liệu được truy cập;
- phân quyền cơ sở dữ liệu theo nguyên tắc quyền tối thiểu;
- sử dụng Transaction cho các nghiệp vụ quan trọng;
- băm mật khẩu bằng thuật toán phù hợp;
- quản lý phiên đăng nhập an toàn;
- giới hạn số lần gửi yêu cầu;
- sử dụng CAPTCHA khi cần;
- bảo vệ chống XSS và CSRF;
- ghi nhật ký các hoạt động quan trọng;
- sao lưu và hỗ trợ phục hồi dữ liệu.

---

## Trạng thái dự án

Dự án hiện đang trong quá trình phát triển.

Các nội dung có thể tiếp tục được bổ sung, thay đổi hoặc điều chỉnh trong quá trình thiết kế, lập trình và kiểm thử.

---

## Ghi chú

Phạm vi dự án tập trung vào một website bán sách có nghiệp vụ cơ bản, đồng thời thể hiện việc áp dụng các biện pháp bảo vệ ứng dụng web và cơ sở dữ liệu ở mức độ cơ bản.