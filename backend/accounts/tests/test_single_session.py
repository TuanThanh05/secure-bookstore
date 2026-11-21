import secrets
import time

from django.contrib.messages import get_messages
from django.core import mail
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from accounts.models import User
from core.models import SecurityEvent
from core.session_store import REPLACED_SESSION_KEY, STAFF_LOGIN_AT_KEY, SessionStore, stored_key

PASSWORD = secrets.token_urlsafe(12) + "-Aa9"


def login(user, ip="198.51.100.10"):
    client = Client(REMOTE_ADDR=ip)
    if user.is_staff:
        client.force_login(user)
    else:
        response = client.post(reverse("accounts:login"), {"username": user.username, "password": PASSWORD})
        if response.status_code != 302:
            raise AssertionError(f"đăng nhập thất bại: {response.status_code}")
    return client


def session_row(client):
    model = SessionStore.get_model_class()
    return model.objects.filter(session_key=stored_key(client.session.session_key)).first()


class SingleSessionTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(username="khach_mp", email="mp@example.test", password=PASSWORD,
                                             email_verified=True)
        self.profile = reverse("accounts:profile")

    def test_new_login_pushes_old_session_out(self):
        old = login(self.user, "198.51.100.10")
        self.assertEqual(old.get(self.profile).status_code, 200)
        new = login(self.user, "203.0.113.20")
        response = old.get(self.profile, follow=True)
        self.assertRedirects(response, reverse("accounts:login") + "?next=" + self.profile)
        notices = [str(m) for m in get_messages(response.wsgi_request)]
        self.assertTrue(any("vừa đăng nhập ở nơi khác" in n for n in notices), notices)
        self.assertFalse(any("203.0.113.20" in n for n in notices))
        self.assertEqual(new.get(self.profile).status_code, 200)

    def test_old_session_row_keeps_only_the_notice(self):
        old = login(self.user)
        old_key = old.session.session_key
        login(self.user)
        row = SessionStore.get_model_class().objects.get(session_key=stored_key(old_key))
        data = SessionStore.decode_row(row)
        self.assertEqual(set(data), {REPLACED_SESSION_KEY})
        old.get(self.profile)
        self.assertFalse(SessionStore.get_model_class().objects.filter(session_key=stored_key(old_key)).exists())

    def test_log_and_email(self):
        login(self.user, "198.51.100.10")
        mail.outbox.clear()
        login(self.user, "203.0.113.20")
        event = SecurityEvent.objects.filter(event_type="logout", detail__reason="new_login_elsewhere").get()
        self.assertEqual(event.username_attempted, "khach_mp")
        self.assertEqual(event.detail["ended"], 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["mp@example.test"])
        self.assertIn("203.0.113.20", mail.outbox[0].body)
        self.assertIn("đặt lại mật khẩu", mail.outbox[0].body)

    def test_first_login_sends_nothing(self):
        mail.outbox.clear()
        login(self.user)
        self.assertEqual(mail.outbox, [])
        self.assertFalse(SecurityEvent.objects.filter(detail__reason="new_login_elsewhere").exists())

    def test_other_users_are_untouched(self):
        other = User.objects.create_user(username="khach_khac", email="kk@example.test", password=PASSWORD,
                                         email_verified=True)
        theirs = login(other)
        login(self.user)
        login(self.user)
        self.assertEqual(theirs.get(self.profile).status_code, 200)

    def test_staff_gets_cli_advice_without_reset_link(self):
        staff = User.objects.create_user(username="qtv_mp", email="qmp@example.test", password=PASSWORD,
                                         is_staff=True)
        login(staff)
        mail.outbox.clear()
        login(staff)
        body = mail.outbox[0].body
        self.assertIn("doi_mat_khau_admin", body)
        self.assertNotIn("http", body)

    def test_expired_staff_session_is_dropped_silently(self):
        staff = User.objects.create_user(username="qtv_cu", email="qcu@example.test", password=PASSWORD,
                                         is_staff=True)
        old = login(staff)
        row = session_row(old)
        data = SessionStore.decode_row(row)
        data[STAFF_LOGIN_AT_KEY] = int(time.time()) - 2 * 60 * 60
        row.session_data = SessionStore.encode_row(row.session_key, data)
        row.save()
        mail.outbox.clear()
        login(staff)
        self.assertEqual(mail.outbox, [])
        self.assertFalse(SessionStore.get_model_class().objects.filter(session_key=row.session_key).exists())

    def test_real_login_form_also_pushes_out(self):
        old = login(self.user)
        fresh = Client(REMOTE_ADDR="203.0.113.30")
        response = fresh.post(reverse("accounts:login"), {"username": "khach_mp", "password": PASSWORD})
        self.assertEqual(response.status_code, 302)
        self.assertNotEqual(old.get(self.profile).status_code, 200)
