import re

from django.core.exceptions import ImproperlyConfigured

from .base import *

DEBUG = False

ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS")
CSRF_TRUSTED_ORIGINS = env.list("DJANGO_CSRF_TRUSTED_ORIGINS", default=[])

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 7_776_000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = False 

SILENCED_SYSTEM_CHECKS = ["security.W021"]

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

if not (TURNSTILE_SITE_KEY and TURNSTILE_SECRET_KEY):
    raise ImproperlyConfigured("Máy chủ thật phải có TURNSTILE_SITE_KEY và TURNSTILE_SECRET_KEY.")
if re.match(r"^[1-3]x0+AA$", TURNSTILE_SECRET_KEY):
    raise ImproperlyConfigured("Không dùng secret key thử của Cloudflare trên máy chủ thật.")
