USE BOOKSTORE_GROUP5_DB;

-- khu vực dữ liệu vai trò ứng dụng
INSERT IGNORE INTO roles (code, name, description) VALUES
('CUSTOMER', 'Khách hàng', 'Khách hàng có tài khoản'),
('STAFF', 'Nhân viên', 'Nhân viên xử lý nghiệp vụ đơn hàng cơ bản'),
('BOOK_MANAGER', 'Quản lý cửa hàng sách', 'Quản lý danh mục sách, kho, đơn hàng và nhân viên'),
('SECURITY_ADMIN', 'Quản trị viên an ninh', 'Quản lý tài khoản, phiên đăng nhập và sự kiện bảo mật'),
('OPERATIONS_ADMIN', 'Quản trị viên vận hành', 'Theo dõi vận hành, tình trạng cơ sở dữ liệu và sao lưu'),
('SUPER_ADMIN', 'Quản trị viên toàn quyền', 'Quản trị toàn bộ chức năng quản trị của ứng dụng');