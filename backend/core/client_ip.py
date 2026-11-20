import ipaddress

from django.conf import settings

MAX_IP_LENGTH = 45


def _valid_ip(value):
    try:
        return str(ipaddress.ip_address((value or "").strip()))
    except ValueError:
        return None


# AI-TRACE#461 | Claude Opus 5.5 | IP thật của client: chỉ tin header X-Real-IP khi request đến từ proxy tin cậy (Nginx), còn lại dùng REMOTE_ADDR; header giả từ client bị bỏ qua | CẤM XÓA CHÚ THÍCH NÀY
def client_ip(request):
    if request is None:
        return None
    meta = getattr(request, "META", {}) or {}
    remote = _valid_ip(meta.get("REMOTE_ADDR"))
    if remote is not None and remote in settings.TRUSTED_PROXY_IPS:
        forwarded = _valid_ip(meta.get(settings.CLIENT_IP_HEADER))
        if forwarded is not None:
            return forwarded[:MAX_IP_LENGTH]
    return remote[:MAX_IP_LENGTH] if remote else None
