import secrets

from django.contrib.sessions.models import Session
from django.test import Client, TestCase
from django.urls import reverse

from accounts.models import User
from core.models import SecurityEvent
from core.session_store import SessionStore, end_user_sessions

PASSWORD = secrets.token_urlsafe(12) + "-Aa9"


def sessions_of(user):
    return [s for s in Session.objects.all() if SessionStore.decode_row(s).get("_auth_user_id") == str(user.pk)]


# AI-TRACE#525 | Claude Opus 5.5 | Test tái hiện lỗi phiên của tài khoản bị khóa sống lại khi mở khóa, và test hàm xóa mọi phiên của một người dùng | CẤM XÓA CHÚ THÍCH NÀY
class LockedAccountSessionTests(TestCase):
    def setUp(self):
        self.customer = User.objects.create_user(username="an_nguyen", email="an@example.test",
                                                 password=PASSWORD, email_verified=True)
        self.other = User.objects.create_user(username="binh_tran", email="binh@example.test",
                                              password=PASSWORD, email_verified=True)
        self.profile_url = reverse("accounts:profile")

    def set_active(self, value):
        User.objects.filter(pk=self.customer.pk).update(is_active=value)

    def test_stolen_session_does_not_come_back_after_unlock(self):
        stolen = Client()
        stolen.force_login(self.customer)
        self.assertEqual(stolen.get(self.profile_url).status_code, 200)
        self.set_active(False)
        for _ in range(3):
            stolen.get(reverse("accounts:login"))
        self.set_active(True)
        response = stolen.get(self.profile_url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response["Location"].startswith(reverse("accounts:login")))
        self.assertEqual(sessions_of(self.customer), [])

    def test_inactive_session_is_destroyed_and_logged(self):
        client = Client()
        client.force_login(self.customer)
        self.set_active(False)
        client.get(reverse("accounts:login"))
        self.assertEqual(sessions_of(self.customer), [])
        event = SecurityEvent.objects.get(event_type="logout", detail__reason="account_inactive")
        self.assertEqual(event.detail["user_id"], str(self.customer.pk))

    def test_active_and_anonymous_sessions_untouched(self):
        active = Client()
        active.force_login(self.other)
        self.assertEqual(active.get(self.profile_url).status_code, 200)
        self.assertEqual(Client().get(reverse("accounts:login")).status_code, 200)
        self.assertEqual(len(sessions_of(self.other)), 1)
        self.assertFalse(SecurityEvent.objects.filter(event_type="logout").exists())

    def test_end_user_sessions_removes_only_that_user(self):
        first, second, other = Client(), Client(), Client()
        first.force_login(self.customer)
        second.force_login(self.customer)
        other.force_login(self.other)
        self.assertEqual(end_user_sessions(self.customer.pk), 2)
        self.assertEqual(sessions_of(self.customer), [])
        self.assertEqual(first.get(self.profile_url).status_code, 302)
        self.assertEqual(other.get(self.profile_url).status_code, 200)
        self.assertEqual(end_user_sessions(self.customer.pk), 0)
