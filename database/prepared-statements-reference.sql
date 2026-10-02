USE BOOKSTORE_GROUP5_DB;

-- khu vực ví dụ prepared statement công khai

-- ví dụ tìm sách theo tên
SET @book_keyword = '%clean%';
PREPARE stmt_search_books FROM '
SELECT book_id, book_name, price, category_name, publisher_name, primary_author_name, stock_status
FROM v_public_books
WHERE book_name LIKE ?
ORDER BY book_name
LIMIT 50';
EXECUTE stmt_search_books USING @book_keyword;
DEALLOCATE PREPARE stmt_search_books;

-- ví dụ tìm sách theo tác giả
SET @author_keyword = '%martin%';
PREPARE stmt_search_books_by_author FROM '
SELECT DISTINCT pb.book_id, pb.book_name, pb.price, pb.primary_author_name
FROM v_public_books pb
INNER JOIN v_public_book_authors pba ON pba.book_id = pb.book_id
WHERE pba.author_name LIKE ?
ORDER BY pb.book_name
LIMIT 50';
EXECUTE stmt_search_books_by_author USING @author_keyword;
DEALLOCATE PREPARE stmt_search_books_by_author;

-- khu vực ví dụ prepared statement xác thực

-- ví dụ lấy tài khoản để backend xác minh mật khẩu
SET @login_identifier = 'example';
PREPARE stmt_auth_user FROM '
SELECT user_id, username, email, email_verified_at, password_hash, status, locked_until
FROM v_auth_users
WHERE username = ? OR email = ?
LIMIT 1';
EXECUTE stmt_auth_user USING @login_identifier, @login_identifier;
DEALLOCATE PREPARE stmt_auth_user;

-- ví dụ lấy năm mật khẩu gần nhất để backend dùng argon2 kiểm tra
SET @password_user_id = 1;
PREPARE stmt_recent_passwords FROM '
SELECT password_hash
FROM v_auth_password_history
WHERE user_id = ?
ORDER BY created_at DESC, id DESC
LIMIT 5';
EXECUTE stmt_recent_passwords USING @password_user_id;
DEALLOCATE PREPARE stmt_recent_passwords;

-- ví dụ kiểm tra phiên đăng nhập bằng hàm băm token
SET @session_token_hash = '0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef';
PREPARE stmt_auth_session FROM '
SELECT session_id, user_id, expires_at, revoked_at
FROM v_auth_sessions
WHERE token_hash = ?
LIMIT 1';
EXECUTE stmt_auth_session USING @session_token_hash;
DEALLOCATE PREPARE stmt_auth_session;

-- khu vực ví dụ gọi thủ tục bằng tham số

-- ví dụ gọi thủ tục xem đơn hàng của khách hàng
SET @current_user_id = 1;
PREPARE stmt_customer_orders FROM 'CALL sp_customer_get_orders(?)';
EXECUTE stmt_customer_orders USING @current_user_id;
DEALLOCATE PREPARE stmt_customer_orders;
