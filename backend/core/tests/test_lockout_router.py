from unittest import mock

from axes.models import AccessAttempt, AccessAttemptExpiration, AccessLog
from django.contrib.sessions.models import Session
from django.db import router
from django.test import SimpleTestCase, override_settings

from accounts.models import User
from core.models import SecurityEvent
from core.db_routers import LockoutRouter
from core.management.commands.db_apply import PAYMENT_GRANT, PAYMENT_REVOKE, apply_payment_simulation


@override_settings(AUTH_DB_ALIAS="auth", SESSION_DB_ALIAS="session")
class LockoutRouterTests(SimpleTestCase):
    def test_axes_tables_use_auth_connection(self):
        for model in (AccessAttempt, AccessAttemptExpiration, AccessLog):
            self.assertEqual(router.db_for_read(model), "auth")
            self.assertEqual(router.db_for_write(model), "auth")

    def test_other_models_not_routed_by_lockout_router(self):
        lockout = LockoutRouter()
        for model in (User, SecurityEvent, Session):
            self.assertIsNone(lockout.db_for_read(model))
            self.assertIsNone(lockout.db_for_write(model))

    def test_security_log_still_on_default(self):
        self.assertEqual(router.db_for_read(SecurityEvent), "default")


class PaymentSimulationGrantTests(SimpleTestCase):
    def test_flag_on_grants_execute(self):
        cursor = mock.Mock()
        self.assertEqual(apply_payment_simulation(cursor, True), "cấp")
        cursor.execute.assert_called_once_with(PAYMENT_GRANT)
        self.assertIn("GRANT EXECUTE ON PROCEDURE sp_payment_simulate TO 'r_customer'", PAYMENT_GRANT)

    def test_flag_off_revokes_execute(self):
        cursor = mock.Mock()
        self.assertEqual(apply_payment_simulation(cursor, False), "thu hồi")
        cursor.execute.assert_called_once_with(PAYMENT_REVOKE)
        self.assertIn("REVOKE IF EXISTS EXECUTE ON PROCEDURE sp_payment_simulate FROM 'r_customer'", PAYMENT_REVOKE)
