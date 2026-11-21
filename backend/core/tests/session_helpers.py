from django.conf import settings
from django.contrib.auth import BACKEND_SESSION_KEY, HASH_SESSION_KEY, SESSION_KEY

from core.session_store import SessionStore


# AI-TRACE#589 | Claude Opus 5.5 | Test: tạo thẳng một phiên thứ hai cho người dùng (không qua login, nên không bị luật một phiên đẩy ra) để thử các hàm xóa phiên | CẤM XÓA CHÚ THÍCH NÀY
def open_extra_session(client, user):
    store = SessionStore()
    store[SESSION_KEY] = str(user.pk)
    store[BACKEND_SESSION_KEY] = "django.contrib.auth.backends.ModelBackend"
    store[HASH_SESSION_KEY] = user.get_session_auth_hash()
    store.create()
    client.cookies[settings.SESSION_COOKIE_NAME] = store.session_key
    return client
