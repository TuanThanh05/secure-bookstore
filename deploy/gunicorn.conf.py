import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bookstore.settings.prod")

wsgi_app = "bookstore.wsgi:application"

# Chỉ nghe trên 127.0.0.1: từ ngoài không vào thẳng Gunicorn được, mọi request phải qua Nginx.
bind = "127.0.0.1:8000"

workers = 1
worker_class = "gthread"
threads = 4

# Chỉ tin X-Forwarded-Proto từ Nginx trên cùng máy.
forwarded_allow_ips = "127.0.0.1"

timeout = 30
graceful_timeout = 30
limit_request_line = 4094
limit_request_fields = 100

accesslog = None
errorlog = "-"
