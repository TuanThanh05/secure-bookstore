from django.contrib.sessions.models import Session
from django.test import SimpleTestCase, override_settings

from accounts.models import PasswordHistory, User
from core.db_routers import AccountWriteRouter
from core.models import SecurityEvent


def on(alias, model=User):
    obj = model()
    obj._state.db = alias
    return obj


@override_settings(AUTH_DB_ALIAS="auth")
class AccountWriteRouterTests(SimpleTestCase):
    def setUp(self):
        self.router = AccountWriteRouter()

    def test_user_writes_go_to_auth(self):
        self.assertEqual(self.router.db_for_write(User), "auth")
        self.assertEqual(self.router.db_for_write(User, instance=on("default")), "auth")

    def test_user_reads_stay_default(self):
        self.assertIsNone(self.router.db_for_read(User))
        self.assertEqual(self.router.db_for_read(User, instance=on("auth")), "default")

    def test_related_rows_of_saved_user_use_default(self):
        user = on("auth")
        self.assertEqual(self.router.db_for_read(PasswordHistory, instance=user), "default")
        self.assertEqual(self.router.db_for_write(SecurityEvent, instance=user), "default")

    def test_other_models_untouched(self):
        self.assertIsNone(self.router.db_for_write(SecurityEvent))
        self.assertIsNone(self.router.db_for_write(Session))
        self.assertIsNone(self.router.db_for_read(PasswordHistory, instance=on("staff")))

    def test_relation_between_default_and_auth_allowed(self):
        self.assertTrue(self.router.allow_relation(on("auth"), on("default", SecurityEvent)))
        self.assertIsNone(self.router.allow_relation(on("staff"), on("default", SecurityEvent)))

    @override_settings(AUTH_DB_ALIAS="default")
    def test_migrate_settings_keep_default(self):
        self.assertEqual(self.router.db_for_write(User), "default")
        self.assertIsNone(self.router.db_for_read(User, instance=on("default")))
