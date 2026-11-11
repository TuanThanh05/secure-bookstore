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

THIRD_PARTY_APPS = [
    # Thêm ở các bước sau: "axes", "django_otp", ...
]

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
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
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

# ---------------------------------------------------------------------
# Cơ sở dữ liệu
# ---------------------------------------------------------------------
# Bước 5 mới cấu hình MySQL với 2 kết nối:
#   "default" → tài khoản app_customer
#   "staff"   → tài khoản app_staff
# Hiện để trống để chạy thử runserver.
DATABASES = {}

# Khóa chính BIGINT, khớp với lược đồ v1
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Bước 3 bật dòng này, PHẢI có trước lần migrate đầu tiên:
AUTH_USER_MODEL = "accounts.User"

# ---------------------------------------------------------------------
# Mật khẩu
# ---------------------------------------------------------------------
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",  # sau có thể đổi sang Argon2
]

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 10},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
    # Bước sau: thêm validator riêng trong core (chữ hoa, thường, số, ký tự đặc biệt)
]

# Link đặt lại mật khẩu hết hạn sau 30 phút
PASSWORD_RESET_TIMEOUT = 60 * 30

# ---------------------------------------------------------------------
# Phiên làm việc và cookie (mục A)
# ---------------------------------------------------------------------
SESSION_COOKIE_NAME = "bs_sid"            # không lộ tên mặc định "sessionid" của Django
SESSION_COOKIE_HTTPONLY = True            # JavaScript không đọc được session ID
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_AGE = 60 * 30              # 30 phút
SESSION_SAVE_EVERY_REQUEST = True         # ...tính từ lần thao tác cuối (hết hạn khi không hoạt động)
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

CSRF_COOKIE_NAME = "bs_csrftoken"
CSRF_COOKIE_HTTPONLY = True               # AJAX lấy token từ {% csrf_token %} trong trang, không đọc cookie
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_FAILURE_VIEW = "core.views.csrf_failure"

# ---------------------------------------------------------------------
# Header bảo mật (mục B)
# ---------------------------------------------------------------------
X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"

# Content Security Policy: chỉ tải tài nguyên từ chính site, không cho script inline
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