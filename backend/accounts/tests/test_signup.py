import re
import secrets
import time
from unittest import mock

from django.core import mail, signing
from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from accounts.models import User
from core.captcha import NO_CAPTCHA
from accounts.services import SIGNUP_SESSION_KEY
from accounts.tokens import make_signup_token
from core.models import SecurityEvent

PASSWORD = secrets.token_urlsafe(12) + "-Aa9"
ATTACKER_PASSWORD = secrets.token_urlsafe(12) + "-Hk7"
WEAK = "1234" * 2
LINK_RE = re.compile(r"https?://[^\s]+(/account/dang-ky/xac-nhan/[^/\s]+/)")


# AI-TRACE#431 | Claude Opus 5.5 | Test đăng ký bắt đầu bằng email: chống chiếm tài khoản trước, phiên, link, giới hạn | CẤM XÓA CHÚ THÍCH NÀY
@override_settings(**NO_CAPTCHA)
class SignupTests(TestCase):
    def setUp(self):
        cache.clear()
        self.register_url = reverse("accounts:register")
        self.complete_url = reverse("accounts:signup_complete")
        self.login_url = reverse("accounts:login")

    def start(self, email="an@example.test", client=None, follow=False):
        return (client or self.client).post(self.register_url, {"email": email}, follow=follow)

    def link_path(self, message=None):
        found = LINK_RE.search((message or mail.outbox[-1]).body)
        self.assertIsNotNone(found, (message or mail.outbox[-1]).body)
        return found.group(1)

    def complete(self, username="an_nguyen", password=PASSWORD, client=None, **extra):
        data = {"username": username, "password1": password, "password2": password, **extra}
        return (client or self.client).post(self.complete_url, data)

    def signup(self, email="an@example.test", username="an_nguyen", password=PASSWORD, client=None):
        client = client or self.client
        self.start(email, client)
        client.get(self.link_path())
        return self.complete(username, password, client)

    def can_log_in(self, login, password):
        return Client().post(self.login_url, {"username": login, "password": password}).status_code == 302

    def test_step_one_sends_link_and_writes_no_account(self):
        response = self.start()
        self.assertRedirects(response, reverse("accounts:check_email"))
        self.assertEqual(User.objects.count(), 0)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["an@example.test"])
        self.link_path()
        self.assertTrue(SecurityEvent.objects.filter(event_type="email_sent", detail__kind="signup").exists())

    def test_attacker_cannot_pre_register_victim_email(self):
        attacker = Client()
        self.start("nannhan@example.test", attacker)
        self.assertEqual(User.objects.count(), 0)
        self.assertEqual(attacker.get(self.complete_url).status_code, 400)
        self.assertEqual(self.complete("hacker", ATTACKER_PASSWORD, attacker).status_code, 400)
        cache.clear()
        victim = Client()
        self.start("nannhan@example.test", victim)
        victim.get(self.link_path())
        self.assertRedirects(self.complete("nannhan", PASSWORD, victim), self.login_url)
        self.assertEqual(list(User.objects.values_list("username", "email")), [("nannhan", "nannhan@example.test")])
        self.assertFalse(self.can_log_in("nannhan@example.test", ATTACKER_PASSWORD))
        self.assertTrue(self.can_log_in("nannhan@example.test", PASSWORD))

    def test_attacker_link_cannot_be_redirected_to_victim_email(self):
        attacker = Client()
        self.start("hacker@example.test", attacker)
        attacker.get(self.link_path())
        self.complete("hacker", ATTACKER_PASSWORD, attacker, email="nannhan@example.test")
        user = User.objects.get(username="hacker")
        self.assertEqual(user.email, "hacker@example.test")
        self.assertFalse(User.objects.filter(email="nannhan@example.test").exists())

    def test_existing_email_looks_identical_and_gets_notice_without_link(self):
        User.objects.create_user(username="chu_cu", email="an@example.test", password=PASSWORD, email_verified=True)
        first = self.start("AN@Example.test", follow=True)
        second = self.start("khac@example.test", follow=True)
        self.assertEqual(first.redirect_chain, second.redirect_chain)
        self.assertEqual(first.content, second.content)
        notice = mail.outbox[0]
        self.assertEqual(notice.to, ["an@example.test"])
        self.assertIsNone(LINK_RE.search(notice.body))
        self.assertIn("chu_cu", notice.body)
        self.assertIn(reverse("accounts:password_reset"), notice.body)
        self.assertTrue(SecurityEvent.objects.filter(event_type="register_existing_email").exists())

    def test_link_moves_email_into_new_session_and_drops_token_from_url(self):
        self.start()
        session = self.client.session
        session["truoc_khi_bam_link"] = 1
        session.save()
        before = session.session_key
        response = self.client.get(self.link_path())
        self.assertRedirects(response, self.complete_url)
        self.assertNotEqual(self.client.session.session_key, before)
        self.assertEqual(self.client.session[SIGNUP_SESSION_KEY]["email"], "an@example.test")
        page = self.client.get(self.complete_url)
        self.assertContains(page, "an@example.test")
        self.assertNotContains(page, 'name="email"')
        self.assertEqual(User.objects.count(), 0)

    def test_complete_creates_verified_account_and_clears_session(self):
        response = self.signup()
        self.assertRedirects(response, self.login_url)
        user = User.objects.get(username="an_nguyen")
        self.assertEqual(user.email, "an@example.test")
        self.assertTrue(user.email_verified)
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertNotIn(SIGNUP_SESSION_KEY, self.client.session)
        self.assertTrue(SecurityEvent.objects.filter(event_type="register_success", username_attempted="an_nguyen").exists())
        self.assertTrue(self.can_log_in("an_nguyen", PASSWORD))

    def test_complete_page_needs_session_from_link(self):
        response = self.client.get(self.complete_url)
        self.assertEqual(response.status_code, 400)
        self.assertContains(response, "Phiên đăng ký đã hết hạn", status_code=400)
        self.assertTrue(SecurityEvent.objects.filter(event_type="register_link_invalid", detail__reason="session").exists())

    def test_session_expires_five_minutes_after_link_opened(self):
        self.start()
        self.client.get(self.link_path())
        with mock.patch("accounts.services.time.time", return_value=time.time() + 301):
            response = self.complete()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(User.objects.count(), 0)
        self.assertNotIn(SIGNUP_SESSION_KEY, self.client.session)

    def test_expired_link_is_rejected_and_logged(self):
        self.start()
        path = self.link_path()
        with mock.patch("django.core.signing.time.time", return_value=signing.time.time() + 301):
            response = self.client.get(path)
        self.assertEqual(response.status_code, 400)
        self.assertContains(response, "đã hết hạn", status_code=400)
        self.assertContains(response, self.register_url, status_code=400)
        self.assertNotIn(SIGNUP_SESSION_KEY, self.client.session)
        event = SecurityEvent.objects.get(event_type="register_link_invalid", detail__reason="expired")
        self.assertEqual(event.path, "/account/dang-ky/xac-nhan/-/")
        self.assertNotIn(path.split("/")[-2], str(SecurityEvent.objects.values_list("path", "detail")))

    def test_tampered_link_is_rejected(self):
        token = make_signup_token("an@example.test")
        tampered = token[:-1] + ("A" if token[-1] != "A" else "B")
        response = self.client.get(reverse("accounts:signup_confirm", args=[tampered]))
        self.assertEqual(response.status_code, 400)
        self.assertNotIn(SIGNUP_SESSION_KEY, self.client.session)

    def test_link_stops_working_once_account_exists(self):
        self.start()
        path = self.link_path()
        self.client.get(path)
        self.complete()
        response = Client().get(path)
        self.assertEqual(response.status_code, 400)
        self.assertContains(response, "không còn hiệu lực", status_code=400)

    def test_second_tab_cannot_create_second_account(self):
        self.start()
        path = self.link_path()
        first, second = Client(), Client()
        first.get(path)
        second.get(path)
        self.assertRedirects(self.complete("an_nguyen", client=first), self.login_url)
        response = self.complete("an_nguyen_2", client=second)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(User.objects.count(), 1)

    def test_taken_username_and_weak_password_are_reported(self):
        User.objects.create_user(username="an_nguyen", email="cu@example.test", password=PASSWORD, email_verified=True)
        self.start("moi@example.test")
        self.client.get(self.link_path())
        response = self.complete("an_nguyen")
        self.assertContains(response, "Tên đăng nhập này đã được sử dụng.", status_code=400)
        response = self.complete("nguoi_moi", WEAK)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(User.objects.filter(email="moi@example.test").count(), 0)
        self.assertEqual(self.client.session[SIGNUP_SESSION_KEY]["email"], "moi@example.test")

    def test_password_similar_to_email_is_rejected(self):
        self.start("nguyenvanbinh2026@example.test")
        self.client.get(self.link_path())
        response = self.complete("binh", "nguyenvanbinh2026")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(User.objects.count(), 0)

    def test_complete_requires_csrf(self):
        client = Client(enforce_csrf_checks=True)
        self.start()
        client.get(self.link_path())
        response = self.complete(client=client)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(User.objects.count(), 0)

    def test_mail_to_one_address_is_limited_per_minute(self):
        self.start()
        self.start("AN@example.test")
        self.assertEqual(len(mail.outbox), 1)
        self.assertTrue(SecurityEvent.objects.filter(event_type="rate_limited", detail__kind="signup").exists())

    @override_settings(EMAIL_RESEND_INTERVAL=0)
    def test_mail_to_one_address_is_limited_per_hour(self):
        for number in range(6):
            self.start(client=Client(REMOTE_ADDR=f"10.0.0.{number}"))
        self.assertEqual(len(mail.outbox), 5)
        self.assertTrue(SecurityEvent.objects.filter(event_type="rate_limited", detail__kind="signup_email").exists())

    def test_each_ip_is_limited_on_both_steps(self):
        for number in range(5):
            self.assertEqual(self.start(f"user{number}@example.test").status_code, 302)
        response = self.start("user5@example.test")
        self.assertContains(response, "thao tác quá nhiều lần", status_code=429)
        self.assertEqual(len(mail.outbox), 5)
        self.assertTrue(SecurityEvent.objects.filter(event_type="rate_limited", detail__kind="signup_start").exists())
        cache.clear()
        self.start()
        self.client.get(self.link_path())
        for _ in range(5):
            self.complete("x", WEAK)
        response = self.complete()
        self.assertEqual(response.status_code, 429)
        self.assertEqual(User.objects.count(), 0)
        self.assertTrue(SecurityEvent.objects.filter(event_type="rate_limited", detail__kind="signup_complete").exists())

    def test_logged_in_user_is_sent_home(self):
        user = User.objects.create_user(username="da_co", email="co@example.test", password=PASSWORD, email_verified=True)
        self.client.force_login(user)
        for url in (self.register_url, self.complete_url, reverse("accounts:signup_confirm", args=["x"])):
            with self.subTest(url=url):
                self.assertRedirects(self.client.get(url), reverse("catalog:home"), fetch_redirect_response=False)

    def test_get_requests_send_no_mail_and_create_nothing(self):
        self.client.get(self.register_url)
        self.client.get(self.complete_url)
        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(User.objects.count(), 0)

    def test_smtp_failure_is_logged_not_shown(self):
        with mock.patch("accounts.emails.send_mail", side_effect=OSError("smtp down")):
            response = self.start(follow=True)
        self.assertEqual(response.redirect_chain, [(reverse("accounts:check_email"), 302)])
        self.assertTrue(SecurityEvent.objects.filter(event_type="email_send_failed", detail__kind="signup").exists())

    def test_forged_host_header_is_rejected(self):
        response = self.client.post(self.register_url, {"email": "an@example.test"}, HTTP_HOST="evil.example")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(len(mail.outbox), 0)

    def test_old_verification_urls_are_gone(self):
        for path in ("/account/xac-nhan-email/abc/", "/account/gui-lai-xac-nhan/"):
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 404)
