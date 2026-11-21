import secrets
from unittest import mock

from django.conf import settings
from django.contrib.sessions.models import Session
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import User
from accounts.tests.two_factor_helpers import enroll, submit_code
from core.db_routers import SessionRouter
from core.models import SecurityEvent
from core.session_store import SessionStore, stored_key

TIME = "core.middleware.time.time"


def new_secret(tag):
    return f"{secrets.token_urlsafe(12)}-{tag}-Aa9"


class HashedSessionStoreTests(TestCase):
    def setUp(self):
        cache.clear()
        self.secret = new_secret("phien")
        self.user = User.objects.create_user(username="an_nguyen", email="an@example.test",
                                             password=self.secret, email_verified=True)

    def login_cookie(self):
        response = self.client.post(reverse("accounts:login"), {"username": "an_nguyen", "password": self.secret})
        self.assertEqual(response.status_code, 302)
        return self.client.cookies[settings.SESSION_COOKIE_NAME].value

    def test_table_holds_hash_not_cookie(self):
        cookie = self.login_cookie()
        keys = list(Session.objects.values_list("session_key", flat=True))
        self.assertNotIn(cookie, keys)
        self.assertIn(stored_key(cookie), keys)

    def test_stolen_row_key_is_not_a_cookie(self):
        self.login_cookie()
        row_key = Session.objects.get().session_key
        self.client.cookies[settings.SESSION_COOKIE_NAME] = row_key
        response = self.client.get(reverse("accounts:profile"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response["Location"])

    def test_copied_session_data_is_rejected(self):
        self.login_cookie()
        victim = Session.objects.get()
        attacker = SessionStore()
        attacker["gio_hang"] = 1
        attacker.save()
        Session.objects.filter(session_key=stored_key(attacker.session_key)).update(session_data=victim.session_data)
        stolen = SessionStore(attacker.session_key)
        self.assertNotIn("_auth_user_id", stolen.load())

    def test_decode_row_reads_own_data(self):
        self.login_cookie()
        row = Session.objects.get()
        self.assertEqual(SessionStore.decode_row(row).get("_auth_user_id"), str(self.user.pk))

    def test_exists_and_delete_use_hash(self):
        store = SessionStore()
        store["x"] = 1
        store.save()
        key = store.session_key
        self.assertTrue(store.exists(key))
        self.assertFalse(store.exists(stored_key(key)))
        store.delete(key)
        self.assertFalse(Session.objects.exists())

    def test_logout_removes_row(self):
        self.login_cookie()
        self.client.post(reverse("accounts:logout"))
        self.assertFalse(Session.objects.exists())


class SessionRouterTests(TestCase):
    def test_sessions_use_session_alias(self):
        router = SessionRouter()
        with override_settings(SESSION_DB_ALIAS="session"):
            self.assertEqual(router.db_for_read(Session), "session")
            self.assertEqual(router.db_for_write(Session), "session")

    def test_other_models_untouched(self):
        router = SessionRouter()
        self.assertIsNone(router.db_for_read(SecurityEvent))
        self.assertIsNone(router.db_for_write(User))


class StaffSessionLimitTests(TestCase):
    def setUp(self):
        cache.clear()
        self.secret = new_secret("qt")
        self.staff = User.objects.create_user(username="quan_tri", email="admin@example.test",
                                              password=self.secret, is_staff=True)
        self.totp = enroll(self.staff)
        self.customer = User.objects.create_user(username="an_nguyen", email="an@example.test",
                                                 password=self.secret, email_verified=True)
        self.now = 1_800_000_000

    def login_at(self, username, at):
        with mock.patch(TIME, return_value=at):
            response = self.client.post(reverse("accounts:login"), {"username": username, "password": self.secret})
            if username == self.staff.username:
                response = submit_code(self.client, self.totp)
        self.assertEqual(response.status_code, 302)
        self.assertIn("_auth_user_id", self.client.session)

    def get_at(self, url, at):
        with mock.patch(TIME, return_value=at):
            return self.client.get(url)

    def test_staff_within_hour_allowed(self):
        self.login_at("quan_tri", self.now)
        response = self.get_at(reverse("accounts:profile"), self.now + settings.STAFF_SESSION_MAX_AGE - 1)
        self.assertNotEqual(response.get("Location"), reverse("accounts:login"))
        self.assertEqual(self.client.session["_auth_user_id"], str(self.staff.pk))

    def test_staff_after_hour_logged_out(self):
        self.login_at("quan_tri", self.now)
        response = self.get_at(reverse("accounts:profile"), self.now + settings.STAFF_SESSION_MAX_AGE)
        self.assertRedirects(response, reverse("accounts:login"), fetch_redirect_response=False)
        self.assertNotIn("_auth_user_id", self.client.session)
        event = SecurityEvent.objects.filter(event_type="logout").latest("id")
        self.assertEqual(event.detail["reason"], "absolute_timeout")
        self.assertEqual(event.user_id, self.staff.pk)

    def test_staff_without_login_time_logged_out(self):
        self.login_at("quan_tri", self.now)
        session = self.client.session
        del session["staff_login_at"]
        session.save()
        response = self.get_at(reverse("accounts:profile"), self.now + 5)
        self.assertRedirects(response, reverse("accounts:login"), fetch_redirect_response=False)

    def test_login_time_from_future_rejected(self):
        self.login_at("quan_tri", self.now + 600)
        response = self.get_at(reverse("accounts:profile"), self.now)
        self.assertRedirects(response, reverse("accounts:login"), fetch_redirect_response=False)

    def test_customer_has_no_hour_limit(self):
        self.login_at("an_nguyen", self.now)
        response = self.get_at(reverse("accounts:profile"), self.now + 3 * settings.STAFF_SESSION_MAX_AGE)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("staff_login_at", self.client.session)
