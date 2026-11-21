"""Định tuyến CSDL (DATABASE_ROUTERS trong settings/base.py)."""
from django.conf import settings


class MigrateOnDefaultRouter:

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        return db == "default"


class SessionRouter:
    def _alias(self, model):
        return settings.SESSION_DB_ALIAS if model._meta.app_label == "sessions" else None

    def db_for_read(self, model, **hints):
        return self._alias(model)

    def db_for_write(self, model, **hints):
        return self._alias(model)


class AccountWriteRouter:
    def _is_account(self, model):
        return model._meta.label == settings.AUTH_USER_MODEL

    def _from_auth(self, hints):
        instance = hints.get("instance")
        return instance is not None and instance._state.db == settings.AUTH_DB_ALIAS

    def db_for_read(self, model, **hints):
        if settings.AUTH_DB_ALIAS != "default" and self._from_auth(hints):
            return "default"
        return None

    def db_for_write(self, model, **hints):
        if self._is_account(model):
            return settings.AUTH_DB_ALIAS
        if settings.AUTH_DB_ALIAS != "default" and self._from_auth(hints):
            return "default"
        return None

    def allow_relation(self, obj1, obj2, **hints):
        if {obj1._state.db, obj2._state.db} <= {"default", settings.AUTH_DB_ALIAS}:
            return True
        return None


class TwoFactorRouter:
    MODELS = {"accounts.TotpDevice", "accounts.RecoveryCode"}

    def _alias(self, model):
        return settings.AUTH_DB_ALIAS if model._meta.label in self.MODELS else None

    def db_for_read(self, model, **hints):
        return self._alias(model)

    def db_for_write(self, model, **hints):
        return self._alias(model)


class LockoutRouter:
    def _alias(self, model):
        return settings.AUTH_DB_ALIAS if model._meta.app_label == "axes" else None

    def db_for_read(self, model, **hints):
        return self._alias(model)

    def db_for_write(self, model, **hints):
        return self._alias(model)
