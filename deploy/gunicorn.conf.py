"""Cấu hình Gunicorn cho secure-bookstore (xem docs/trien-khai-nginx.md).

Chạy từ thư mục backend/:
    gunicorn -c ../deploy/gunicorn.conf.py
"""
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bookstore.settings.prod")

wsgi_app = "bookstore.wsgi:application"

# Chỉ nghe trên 127.0.0.1: từ ngoài không vào thẳng Gunicorn được, mọi request phải qua Nginx.
bind = "127.0.0.1:8000"

# 1 tiến trình nhiều luồng: các bộ đếm giới hạn tần suất (cache bộ nhớ của Django) dùng
# chung một chỗ, không bị chia theo tiến trình. Muốn nhiều tiến trình thì phải đổi sang
# cache chung (Redis...) trước.
workers = 1
worker_class = "gthread"
threads = 4

# Chỉ tin X-Forwarded-Proto từ Nginx trên cùng máy.
forwarded_allow_ips = "127.0.0.1"

timeout = 30
graceful_timeout = 30
limit_request_line = 4094
limit_request_fields = 100

# Không ghi access log ở Gunicorn: Nginx đã ghi (IP thật), và đường dẫn có thể chứa mã
# một lần (link đăng ký, đặt lại mật khẩu).
accesslog = None
errorlog = "-"
