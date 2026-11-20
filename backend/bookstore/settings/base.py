from datetime import timedelta
from pathlib import Path

import environ
from django.utils.csp import CSP

BASE_DIR = Path(__file__).resolve().parent.parent.parent
REPO_DIR = BASE_DIR.parent                
FRONTEND_DIR = REPO_DIR / "frontend"

env = environ.Env()
environ.Env.read_env(REPO_DIR / ".env")

SECRET_KEY = env("DJANGO_SECRET_KEY")

DEBUG = False
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=[])

DJANGO_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [ "axes" ]

AUTHENTICATION_BACKENDS = ["axes.backends.AxesStandaloneBackend", "django.contrib.auth.backends.ModelBackend"]

LOCAL_APPS = [ "core", "accounts", "catalog", "orders", "payments", "dashboard", ]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.csp.ContentSecurityPolicyMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "core.middleware.StaffSessionLimitMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "axes.middleware.AxesMiddleware", 
    "core.middleware.DbPermissionDeniedMiddleware",
]

ROOT_URLCONF = "bookstore.urls"
WSGI_APPLICATION = "bookstore.wsgi.application"
ASGI_APPLICATION = "bookstore.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [FRONTEND_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.template.context_processors.csp",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

_DB_COMMON = {
    "ENGINE": "django.db.backends.mysql",
    "NAME": env("DB_NAME", default="bookstore"),
    "HOST": env("DB_HOST", default="127.0.0.1"),
    "PORT": env("DB_PORT", default="3306"),
    "CONN_MAX_AGE": 60,
    "CONN_HEALTH_CHECKS": True,
    "OPTIONS": {
        "charset": "utf8mb4",
        "ssl_mode": "REQUIRED",
        "init_command": "SET sql_mode = 'STRICT_ALL_TABLES,NO_ZERO_DATE,NO_ZERO_IN_DATE,ERROR_FOR_DIVISION_BY_ZERO,ONLY_FULL_GROUP_BY,NO_ENGINE_SUBSTITUTION'",
    },
}

DATABASES = {
    "default": {
        **_DB_COMMON,
        "USER": env("DB_CUSTOMER_USER", default="app_customer"),
        "PASSWORD": env("DB_CUSTOMER_PASSWORD"),
    },
    "staff": {
        **_DB_COMMON,
        "USER": env("DB_STAFF_USER", default="app_staff"),
        "PASSWORD": env("DB_STAFF_PASSWORD"),
        "TEST": {"MIRROR": "default"},
    },
    "session": {                          # chỉ bảng django_session (core.db_routers.SessionRouter)
        **_DB_COMMON,
        "USER": env("DB_SESSION_USER", default="app_session"),
        "PASSWORD": env("DB_SESSION_PASSWORD"),
        "TEST": {"MIRROR": "default"},
    },
    "auth": {                             # chỉ lệnh GHI bảng accounts_user (core.db_routers.AccountWriteRouter)
        **_DB_COMMON,
        "USER": env("DB_AUTH_USER", default="app_auth"),
        "PASSWORD": env("DB_AUTH_PASSWORD"),
        "TEST": {"MIRROR": "default"},
    },
}

SESSION_DB_ALIAS = "session"
AUTH_DB_ALIAS = "auth"
DATABASE_ROUTERS = [
    "core.db_routers.SessionRouter",
    "core.db_routers.TwoFactorRouter",
    "core.db_routers.AccountWriteRouter",
    "core.db_routers.MigrateOnDefaultRouter",
]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = "accounts.User"

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher"
]

AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = timedelta(minutes=15)
AXES_LOCKOUT_PARAMETERS = [["username", "ip_address"]]
AXES_RESET_ON_SUCCESS = True
AXES_CLIENT_IP_CALLABLE = "core.client_ip.client_ip"   # axes đếm theo IP thật, không theo IP của Nginx

# IP thật của client sau reverse proxy (core/client_ip.py). Chỉ tin header khi
# REMOTE_ADDR là một proxy trong danh sách này; trống (máy dev) = không tin header nào.
TRUSTED_PROXY_IPS = env.list("TRUSTED_PROXY_IPS", default=[])
CLIENT_IP_HEADER = "HTTP_X_REAL_IP"        # Nginx: proxy_set_header X-Real-IP $remote_addr;

# Đường dẫn chứa mã bí mật (core/security_log.py): nhóm "secret" được thay bằng "-"
# trước khi ghi file log và bảng core_securityevent. Thêm URL mới chứa mã thì thêm mẫu vào đây.
SECURITY_LOG_SECRET_PATHS = [
    r"^/account/dat-lai-mat-khau/[^/]+/(?!set-password(?:/|$))(?P<secret>[^/]+)",   # link đặt lại mật khẩu
    r"^/account/dang-ky/xac-nhan/(?P<secret>[^/]+)",                               # link đăng ký
]

LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "catalog:home"
LOGOUT_REDIRECT_URL = "catalog:home"

REAUTH_MAX_AGE = 2 * 60

SIGNUP_LINK_MAX_AGE = 5 * 60              # link đăng ký trong thư: bấm trong 5 phút
SIGNUP_SESSION_MAX_AGE = 5 * 60           # sau khi bấm link: nộp form hoàn tất trong 5 phút
SIGNUP_EMAIL_LIMIT = 5                    # mỗi email nhận tối đa 5 thư đăng ký (link hoặc thư báo trùng) trong SIGNUP_EMAIL_WINDOW
SIGNUP_EMAIL_WINDOW = 60 * 60
SIGNUP_RATE_LIMIT = 5                     # mỗi IP gửi form đăng ký tối đa 5 lần trong SIGNUP_RATE_WINDOW, đếm riêng từng bước
SIGNUP_RATE_WINDOW = 10 * 60
EMAIL_RESEND_INTERVAL = 60                # mỗi email nhận tối đa 1 thư mỗi loại trong 60 giây
TURNSTILE_SITE_KEY = env("TURNSTILE_SITE_KEY", default="")       # để trống cả hai thì Turnstile tắt (máy dev, CI)
TURNSTILE_SECRET_KEY = env("TURNSTILE_SECRET_KEY", default="")
TURNSTILE_ACTION = "signup"               # khớp data-action của widget, Siteverify trả lại để kiểm tra
TURNSTILE_TIMEOUT = 5                     # giây chờ Siteverify; quá hạn thì từ chối, không gửi thư
PASSWORD_CHANGE_MAX_FAILURES = 5

# Xác thực 2 bước bằng ứng dụng (TOTP, RFC 6238) – docs/xac-thuc-2-buoc.md
TWO_FACTOR_ISSUER = "Secure Bookstore"      # tên hiện trong Google Authenticator
TWO_FACTOR_VALID_WINDOW = 1                 # chấp nhận lệch ±1 bước (±30 giây) cho đồng hồ điện thoại
TWO_FACTOR_PENDING_MAX_AGE = 5 * 60         # sau khi đúng mật khẩu, có 5 phút để nhập mã
TWO_FACTOR_MAX_ATTEMPTS = 5                 # sai 5 lần trong một lượt: hủy lượt, nhập lại mật khẩu
TWO_FACTOR_USER_MAX_FAILURES = 10           # sai 10 lần/giờ trên một tài khoản: tạm khóa bước 2 của tài khoản đó
TWO_FACTOR_USER_FAILURE_WINDOW = 60 * 60
TWO_FACTOR_SETUP_MAX_AGE = 10 * 60          # mã QR khi cài chỉ dùng được trong 10 phút
RECOVERY_CODE_COUNT = 5
PASSWORD_CHANGE_FAILURE_WINDOW = 15 * 60

FIELD_ENCRYPTION_KEY = env("FIELD_ENCRYPTION_KEY", default="")

EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
if EMAIL_HOST_USER and EMAIL_HOST_PASSWORD:
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = env("EMAIL_HOST", default="smtp.gmail.com")
    EMAIL_PORT = env.int("EMAIL_PORT", default=587)
    EMAIL_USE_TLS = True
else:
    EMAIL_BACKEND = "core.mail_backends.ReadableConsoleEmailBackend"
EMAIL_TIMEOUT = 10
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="") or EMAIL_HOST_USER or "Secure Bookstore <no-reply@localhost>"

# Mọi ô mật khẩu (kể cả đăng nhập, xác thực lại) cũng bị chặn ở mức này trong form
# (accounts.forms.cap_password_fields) để không gọi Argon2 với chuỗi quá dài.
PASSWORD_MAX_LENGTH = 64

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator","OPTIONS": {"min_length": 12},},
    {"NAME": "accounts.validators.MaximumLengthValidator", "OPTIONS": {"max_length": PASSWORD_MAX_LENGTH}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
    {"NAME": "accounts.validators.PasswordHistoryValidator", "OPTIONS": {"history_count": 5}},
]

PASSWORD_RESET_TIMEOUT = 5 * 60

# ---------------------------------------------------------------------
# Phiên làm việc và cookie (mục A)
# ---------------------------------------------------------------------
SESSION_ENGINE = "core.session_store"       # bảng chỉ lưu mã băm của cookie, chữ ký gắn với dòng
SESSION_COOKIE_NAME = "bs_sid"            # không lộ tên mặc định "sessionid" của Django
SESSION_COOKIE_HTTPONLY = True            # JavaScript không đọc được session ID
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_AGE = 60 * 30              # 30 phút
SESSION_SAVE_EVERY_REQUEST = True         # ...tính từ lần thao tác cuối (hết hạn khi không hoạt động)
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
STAFF_SESSION_MAX_AGE = 60 * 60           # phiên nhân viên/admin tối đa 1 giờ kể từ lúc đăng nhập, dù vẫn thao tác

CSRF_COOKIE_NAME = "bs_csrftoken"
CSRF_COOKIE_HTTPONLY = True             
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_FAILURE_VIEW = "core.views.csrf_failure"

# ---------------------------------------------------------------------
# Header bảo mật (mục B)
# ---------------------------------------------------------------------
X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"

SECURE_CSP = {
    "default-src": [CSP.SELF],
    "script-src": [CSP.SELF],
    "style-src": [CSP.SELF],
    "img-src": [CSP.SELF, "data:"],
    "font-src": [CSP.SELF],
    "connect-src": [CSP.SELF],
    "object-src": [CSP.NONE],
    "base-uri": [CSP.SELF],
    "form-action": [CSP.SELF],
    "frame-ancestors": [CSP.NONE],
}

TURNSTILE_ORIGIN = "https://challenges.cloudflare.com"
SIGNUP_CSP = {                            # ngoại lệ duy nhất: chỉ trang đăng ký bước 1 được tải script + iframe Turnstile
    **SECURE_CSP,
    "script-src": [CSP.SELF, TURNSTILE_ORIGIN],
    "frame-src": [TURNSTILE_ORIGIN],
}

# ---------------------------------------------------------------------
# Giới hạn kích thước request (chống DoS cơ bản)
# ---------------------------------------------------------------------
DATA_UPLOAD_MAX_MEMORY_SIZE = 2_621_440   # 2.5 MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 2_621_440
DATA_UPLOAD_MAX_NUMBER_FIELDS = 200

# ---------------------------------------------------------------------
# Ngôn ngữ, múi giờ
# ---------------------------------------------------------------------
LANGUAGE_CODE = "vi"
TIME_ZONE = "Asia/Ho_Chi_Minh"   # hiển thị theo giờ VN
USE_I18N = True
USE_TZ = True                    # lưu trong CSDL theo UTC

# ---------------------------------------------------------------------
# File tĩnh và file upload
# ---------------------------------------------------------------------
STATIC_URL = "static/"
STATICFILES_DIRS = [FRONTEND_DIR / "static"]
STATIC_ROOT = REPO_DIR / "staticfiles"     # kết quả collectstatic, không commit

MEDIA_URL = "media/"
MEDIA_ROOT = REPO_DIR / "media"            # ảnh bìa upload, không commit, Nginx không cho thực thi
BOOK_DEFAULT_COVER = "img/book-cover-default.webp"   # ảnh bìa mặc định trong frontend/static, dùng khi sách chưa có ảnh
LOW_STOCK_THRESHOLD = 10                            # dashboard tô "Sắp hết" khi tồn kho từ 1 đến ngưỡng này
REVIEW_RATE_LIMIT = 5                               # mỗi khách gửi/sửa tối đa 5 đánh giá trong REVIEW_RATE_WINDOW
REVIEW_RATE_WINDOW = 60 * 60
CART_ADD_RATE_LIMIT = 20                            # mỗi khách thêm vào giỏ tối đa 20 lần trong CART_ADD_RATE_WINDOW
CART_ADD_RATE_WINDOW = 60
CART_UPDATE_RATE_LIMIT = 60                         # đổi số lượng / gỡ khỏi giỏ: tối đa 60 lần trong CART_UPDATE_RATE_WINDOW
CART_UPDATE_RATE_WINDOW = 60
ORDER_PLACE_RATE_LIMIT = 5                          # đặt hàng: tối đa 5 lần trong ORDER_PLACE_RATE_WINDOW
ORDER_PLACE_RATE_WINDOW = 600
ORDER_CANCEL_RATE_LIMIT = 10                        # hủy đơn: tối đa 10 lần trong ORDER_CANCEL_RATE_WINDOW
ORDER_CANCEL_RATE_WINDOW = 600
PAYMENT_SIMULATION = env.bool("PAYMENT_SIMULATION", default=False)   # nút "Thanh toán (mô phỏng)", tạm thời khi chưa có cổng thật
PAYMENT_SIMULATE_RATE_LIMIT = 10                    # bấm thanh toán mô phỏng: tối đa 10 lần trong PAYMENT_SIMULATE_RATE_WINDOW
PAYMENT_SIMULATE_RATE_WINDOW = 600

LOG_DIR = REPO_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "plain": {"format": "%(asctime)s %(levelname)s %(name)s %(message)s"},
    },
    "handlers": {
        "security_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOG_DIR / "security.log",
            "maxBytes": 5 * 1024 * 1024,
            "backupCount": 5,
            "encoding": "utf-8",
            "formatter": "plain",
        },
    },
    "loggers": {
        "security": {"handlers": ["security_file"], "level": "INFO", "propagate": False},
    },
}