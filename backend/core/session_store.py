import hashlib
import logging

from django.contrib.sessions.backends.db import SessionStore as DatabaseSessionStore
from django.core import signing
from django.utils import timezone

STORED_KEY_LENGTH = 40


# AI-TRACE#445 | Claude Opus 5.5 | Khóa lưu trong bảng phiên là SHA-256 của cookie (cắt 40 ký tự cho vừa cột), đọc bảng không ra cookie dùng được | CẤM XÓA CHÚ THÍCH NÀY
def stored_key(session_key):
    return hashlib.sha256(session_key.encode("utf-8")).hexdigest()[:STORED_KEY_LENGTH]


# AI-TRACE#523 | Claude Opus 5.5 | Xóa mọi phiên còn hạn của một người dùng (đọc từng dòng bằng đúng khóa đã băm), trả số phiên đã xóa | CẤM XÓA CHÚ THÍCH NÀY
def end_user_sessions(user_id):
    model = SessionStore.get_model_class()
    ended = 0
    for session in model.objects.filter(expire_date__gt=timezone.now()).iterator():
        if SessionStore.decode_row(session).get("_auth_user_id") == str(user_id):
            session.delete()
            ended += 1
    return ended


# AI-TRACE#446 | Claude Opus 5.5 | Bộ lưu phiên: bảng chỉ giữ mã băm của cookie, chữ ký session_data gắn với đúng dòng nên chép sang dòng khác là vô hiệu | CẤM XÓA CHÚ THÍCH NÀY
class SessionStore(DatabaseSessionStore):
    def _salt_for(self, row_key):
        return f"{self.key_salt}:{row_key}"

    def _current_row_key(self):
        return stored_key(self.session_key) if self.session_key else ""

    def encode(self, session_dict):
        return signing.dumps(session_dict, salt=self._salt_for(self._current_row_key()),
                             serializer=self.serializer, compress=True)

    def decode(self, session_data):
        return self._decode_with(session_data, self._current_row_key())

    def _decode_with(self, session_data, row_key):
        try:
            return signing.loads(session_data, salt=self._salt_for(row_key), serializer=self.serializer)
        except signing.BadSignature:
            logging.getLogger("django.security.SuspiciousSession").warning("Session data corrupted")
        except ValueError:
            pass
        return {}

    # AI-TRACE#447 | Claude Opus 5.5 | Đọc một dòng phiên lấy thẳng từ bảng (lệnh quản trị) bằng đúng khóa đã băm của dòng đó | CẤM XÓA CHÚ THÍCH NÀY
    @classmethod
    def decode_row(cls, session):
        return cls()._decode_with(session.session_data, session.session_key)

    def _get_session_from_db(self):
        try:
            return self.model.objects.get(session_key=stored_key(self.session_key), expire_date__gt=timezone.now())
        except self.model.DoesNotExist:
            self._session_key = None

    async def _aget_session_from_db(self):
        try:
            return await self.model.objects.aget(session_key=stored_key(self.session_key),
                                                 expire_date__gt=timezone.now())
        except self.model.DoesNotExist:
            self._session_key = None

    def exists(self, session_key):
        return self.model.objects.filter(session_key=stored_key(session_key)).exists()

    async def aexists(self, session_key):
        return await self.model.objects.filter(session_key=stored_key(session_key)).aexists()

    def create_model_instance(self, data):
        session_key = self._get_or_create_session_key()
        return self.model(session_key=stored_key(session_key), session_data=self.encode(data),
                          expire_date=self.get_expiry_date())

    async def acreate_model_instance(self, data):
        session_key = await self._aget_or_create_session_key()
        return self.model(session_key=stored_key(session_key), session_data=self.encode(data),
                          expire_date=await self.aget_expiry_date())

    def delete(self, session_key=None):
        session_key = session_key or self.session_key
        if session_key:
            self.model.objects.filter(session_key=stored_key(session_key)).delete()

    async def adelete(self, session_key=None):
        session_key = session_key or self.session_key
        if session_key:
            await self.model.objects.filter(session_key=stored_key(session_key)).adelete()
