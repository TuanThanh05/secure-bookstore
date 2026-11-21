import datetime
import hashlib
import logging
import time

from django.conf import settings
from django.contrib.sessions.backends.db import SessionStore as DatabaseSessionStore
from django.core import signing
from django.utils import timezone

STORED_KEY_LENGTH = 40
REPLACED_SESSION_KEY = "session_replaced"
REPLACED_NOTICE_SECONDS = 60 * 60
STAFF_LOGIN_AT_KEY = "staff_login_at"


def stored_key(session_key):
    return hashlib.sha256(session_key.encode("utf-8")).hexdigest()[:STORED_KEY_LENGTH]


def end_user_sessions(user_id):
    model = SessionStore.get_model_class()
    ended = 0
    for session in model.objects.filter(expire_date__gt=timezone.now()).iterator():
        if SessionStore.decode_row(session).get("_auth_user_id") == str(user_id):
            session.delete()
            ended += 1
    return ended


def replace_other_sessions(user_id, keep_session_key, notice):
    model = SessionStore.get_model_class()
    keep = stored_key(keep_session_key) if keep_session_key else None
    now = timezone.now()
    replaced = 0
    for session in model.objects.filter(expire_date__gt=now).iterator():
        if session.session_key == keep:
            continue
        data = SessionStore.decode_row(session)
        if data.get("_auth_user_id") != str(user_id):
            continue
        if _staff_session_over(data):
            session.delete()
            continue
        session.session_data = SessionStore.encode_row(session.session_key, {REPLACED_SESSION_KEY: notice})
        session.expire_date = min(session.expire_date, now + datetime.timedelta(seconds=REPLACED_NOTICE_SECONDS))
        session.save(update_fields=["session_data", "expire_date"])
        replaced += 1
    return replaced


def _staff_session_over(data):
    started = data.get(STAFF_LOGIN_AT_KEY)
    if not isinstance(started, int):
        return False
    return time.time() - started >= settings.STAFF_SESSION_MAX_AGE


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

    @classmethod
    def decode_row(cls, session):
        return cls()._decode_with(session.session_data, session.session_key)

    @classmethod
    def encode_row(cls, row_key, session_dict):
        store = cls()
        return signing.dumps(session_dict, salt=store._salt_for(row_key), serializer=store.serializer, compress=True)

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
