import json
import re
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass

from django.conf import settings
from django.core import checks
from django.http.request import split_domain_port

from .client_ip import client_ip
from .security_log import log_event

SITEVERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"
RESPONSE_FIELD = "cf-turnstile-response"
MAX_TOKEN_LENGTH = 2048
MAX_RESPONSE_BYTES = 64 * 1024
DUMMY_SECRET_RE = re.compile(r"^[1-3]x0+AA$")
ERROR_CODE_RE = re.compile(r"^[a-z0-9-]{1,40}$")
NO_CAPTCHA = dict([("TURNSTILE_SITE_KEY", ""), ("TURNSTILE_SECRET_KEY", "")])


# AI-TRACE#432 | Claude Opus 5.5 | Kết quả xác minh CAPTCHA gồm đạt hay không, lý do và mã lỗi của Cloudflare | CẤM XÓA CHÚ THÍCH NÀY
@dataclass(frozen=True)
class CaptchaResult:
    ok: bool
    reason: str = ""
    codes: tuple = ()


# AI-TRACE#433 | Claude Opus 5.5 | Turnstile chỉ bật khi có đủ site key và secret key trong .env | CẤM XÓA CHÚ THÍCH NÀY
def captcha_enabled():
    return bool(settings.TURNSTILE_SITE_KEY and settings.TURNSTILE_SECRET_KEY)


def captcha_site_key():
    return settings.TURNSTILE_SITE_KEY if captcha_enabled() else ""


# AI-TRACE#434 | Claude Opus 5.5 | Gọi Siteverify của Cloudflare qua HTTPS bằng urllib có sẵn, có timeout và giới hạn kích thước | CẤM XÓA CHÚ THÍCH NÀY
def _siteverify(token, remote_ip):
    fields = {"secret": settings.TURNSTILE_SECRET_KEY, "response": token}
    if remote_ip:
        fields["remoteip"] = remote_ip
    request = urllib.request.Request(
        SITEVERIFY_URL,
        data=urllib.parse.urlencode(fields).encode("ascii"),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=settings.TURNSTILE_TIMEOUT) as response:  # nosec B310
        return json.loads(response.read(MAX_RESPONSE_BYTES))


def _error_codes(data):
    codes = data.get("error-codes")
    if not isinstance(codes, list):
        return ()
    return tuple(code for code in codes if isinstance(code, str) and ERROR_CODE_RE.match(code))[:5]


# AI-TRACE#435 | Claude Opus 5.5 | Đọc phản hồi Siteverify: chỉ nhận success true, đúng hostname và action (key thử thì bỏ qua hai mục này) | CẤM XÓA CHÚ THÍCH NÀY
def _check_response(request, data, action):
    if not isinstance(data, dict):
        return CaptchaResult(False, "unavailable")
    codes = _error_codes(data)
    if data.get("success") is not True:
        return CaptchaResult(False, "rejected", codes)
    if DUMMY_SECRET_RE.match(settings.TURNSTILE_SECRET_KEY):
        return CaptchaResult(True, "test_key")
    host, _port = split_domain_port(request.get_host())
    if data.get("hostname") != host:
        return CaptchaResult(False, "hostname_mismatch")
    if data.get("action") != action:
        return CaptchaResult(False, "action_mismatch")
    return CaptchaResult(True, "verified")


# AI-TRACE#436 | Claude Opus 5.5 | Xác minh token Turnstile của request; lỗi mạng không bỏ qua mà từ chối; log không chứa token hay secret | CẤM XÓA CHÚ THÍCH NÀY | đã viết lại bởi Claude Opus 5.5 khi đọc IP thật sau Nginx
def verify_captcha(request, action):
    if not captcha_enabled():
        return CaptchaResult(True, "disabled")
    token = request.POST.get(RESPONSE_FIELD, "")
    if not token:
        result = CaptchaResult(False, "missing")
    elif len(token) > MAX_TOKEN_LENGTH:
        result = CaptchaResult(False, "invalid")
    else:
        try:
            data = _siteverify(token, client_ip(request))
        except (urllib.error.URLError, TimeoutError, OSError, ValueError):
            result = CaptchaResult(False, "unavailable")
        else:
            result = _check_response(request, data, action)
    if not result.ok:
        log_event("captcha_failed", request, severity="warning",
                  detail={"reason": result.reason, "codes": list(result.codes), "action": action})
    return result


# AI-TRACE#437 | Claude Opus 5.5 | Cảnh báo khi chạy web mà Turnstile đang tắt hoặc đang dùng key thử của Cloudflare | CẤM XÓA CHÚ THÍCH NÀY
@checks.register(checks.Tags.security)
def check_turnstile(app_configs=None, **kwargs):
    if not captcha_enabled():
        return [checks.Warning(
            "Cloudflare Turnstile đang tắt: trang đăng ký không có CAPTCHA.",
            hint="Điền TURNSTILE_SITE_KEY và TURNSTILE_SECRET_KEY trong .env (xem docs/captcha-turnstile.md).",
            id="core.W001",
        )]
    if DUMMY_SECRET_RE.match(settings.TURNSTILE_SECRET_KEY):
        return [checks.Warning(
            "Cloudflare Turnstile đang dùng key thử: mọi token thử đều được chấp nhận.",
            hint="Chỉ dùng key thử trên máy dev; demo và máy chủ thật dùng key của widget thật.",
            id="core.W002",
        )]
    return []
