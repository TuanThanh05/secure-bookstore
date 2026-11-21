import secrets

from django.core import mail
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from accounts.models import User
from core.models import SecurityEvent
from core.tests.session_helpers import open_extra_session

PASSWORD = secrets.token_urlsafe(12) + "-Aa9"
NEW_PASSWORD = secrets.token_urlsafe(12) + "-Bb8"


# AI-TRACE#063 | Claude Opus 5.5 | Test đổi mật khẩu: mật khẩu cũ, đăng xuất thiết bị khác, sai nhiều lần, chặn nhân viên | CẤM XÓA CHÚ THÍCH NÀY | đã viết lại bởi Claude Opus 5.5 khi thêm luật một tài khoản một phiên
class PasswordChangeTests(TestCase):
    def setUp(self):
        cache.clear()
        self.url = reverse("accounts:password_change")
        self.user = User.objects.create_user(username="an_nguyen", email="an@example.test",
                                             password=PASSWORD, email_verified=True)
        self.client.force_login(self.user)

    def change(self, old=PASSWORD, new1=NEW_PASSWORD, new2=NEW_PASSWORD, client=None):
        return (client or self.client).post(self.url, {"old_password": old, "new_password1": new1, "new_password2": new2})

    def fresh_user(self):
        return User.objects.get(pk=self.user.pk)

    def test_profile_has_change_password_button(self):
        self.assertContains(self.client.get(reverse("accounts:profile")), self.url)

    def test_anonymous_is_sent_to_login(self):
        response = Client().get(self.url)
        self.assertRedirects(response, f"{reverse('accounts:login')}?next={self.url}")

    def test_staff_is_redirected(self):
        staff = User.objects.create_user(username="quan_tri", email="admin@example.test", password=PASSWORD, is_staff=True)
        client = Client()
        client.force_login(staff)
        response = self.change(client=client)
        self.assertRedirects(response, reverse("dashboard:profile"))
        self.assertTrue(User.objects.get(pk=staff.pk).check_password(PASSWORD))

    def test_change_password_success(self):
        response = self.change()
        self.assertRedirects(response, reverse("accounts:profile"))
        self.assertTrue(self.fresh_user().check_password(NEW_PASSWORD))
        self.assertTrue(SecurityEvent.objects.filter(event_type="password_changed", detail__via="change").exists())
        self.assertEqual(mail.outbox[-1].to, ["an@example.test"])
        self.assertIn("vừa được thay đổi", mail.outbox[-1].body)

    def test_current_session_kept_and_other_sessions_logged_out(self):
        other = open_extra_session(Client(), self.user)
        old_key = self.client.session.session_key
        self.change()
        self.assertEqual(self.client.get(reverse("accounts:profile")).status_code, 200)
        self.assertNotEqual(self.client.session.session_key, old_key)
        self.assertEqual(other.get(reverse("accounts:profile")).status_code, 302)

    def test_wrong_old_password_is_rejected_and_logged(self):
        response = self.change(old=PASSWORD + "-sai")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Mật khẩu hiện tại không đúng.")
        self.assertTrue(self.fresh_user().check_password(PASSWORD))
        self.assertTrue(SecurityEvent.objects.filter(event_type="login_failed",
                                                     detail__kind="password_change_old_password").exists())

    def test_five_wrong_old_passwords_log_out(self):
        for _ in range(4):
            self.assertEqual(self.change(old=PASSWORD + "-sai").status_code, 200)
        response = self.change(old=PASSWORD + "-sai")
        self.assertRedirects(response, reverse("accounts:login"))
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertTrue(SecurityEvent.objects.filter(event_type="rate_limited", detail__kind="password_change").exists())
        self.assertTrue(self.fresh_user().check_password(PASSWORD))

    def test_success_resets_failure_counter(self):
        for _ in range(4):
            self.change(old=PASSWORD + "-sai")
        self.change()
        response = self.change(old=PASSWORD, new1=PASSWORD + "-x2", new2=PASSWORD + "-x2")
        self.assertEqual(response.status_code, 200)
        self.assertIn("_auth_user_id", self.client.session)

    def test_mismatched_new_passwords_rejected(self):
        response = self.change(new2=NEW_PASSWORD + "x")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.fresh_user().check_password(PASSWORD))

    def test_weak_new_password_rejected(self):
        weak = "1234" * 2
        response = self.change(new1=weak, new2=weak)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.fresh_user().check_password(PASSWORD))

    def test_requires_csrf(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        self.assertEqual(self.change(client=client).status_code, 403)
        self.assertTrue(self.fresh_user().check_password(PASSWORD))

    def test_page_is_not_cached(self):
        self.assertIn("no-store", self.client.get(self.url)["Cache-Control"])
