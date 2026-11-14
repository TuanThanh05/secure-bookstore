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
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "axes.middleware.AxesMiddleware", 
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
}

DATABASE_ROUTERS = ["core.db_routers.MigrateOnDefaultRouter"]

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

LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "catalog:home"
LOGOUT_REDIRECT_URL = "catalog:home"

REAUTH_MAX_AGE = 2 * 60

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator","OPTIONS": {"min_length": 12},},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
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