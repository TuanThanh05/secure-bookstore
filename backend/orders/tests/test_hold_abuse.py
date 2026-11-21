import datetime
import secrets
from unittest import mock

from django.conf import settings
from django.contrib.sessions.models import Session
from django.core.cache import cache
from django.test import Client, SimpleTestCase, TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from core.models import SecurityEvent
from core.session_store import SessionStore
from dashboard.account_services import ACCOUNT_STATUS_LABELS, StaffAccount
from dashboard.forms import ACCOUNT_STATUS_FILTERS
from dashboard.log_services import EVENT_LABELS
from orders.cart_services import Cart, CartLine
from orders.services import ORDER_ERROR_MESSAGES

PASSWORD = secrets.token_urlsafe(12) + "-Aa9"
CODE = "a" * 32


def sessions_of(user):
    return [s for s in Session.objects.all() if SessionStore.decode_row(s).get("_auth_user_id") == str(user.pk)]


def line(book_id, quantity):
    return CartLine(book_id=book_id, title="Sách thử", author="Tác giả", cover_image=None, price=50000,
                    quantity=quantity, is_active=True, in_stock=True)


class HoldAbuseLockTests(TestCase):
    def setUp(self):
        cache.clear()
        self.customer = User.objects.create_user(username="an_nguyen", email="an@example.test", password=PASSWORD,
                                                 email_verified=True)

    def lock(self, hours=24):
        User.objects.filter(pk=self.customer.pk).update(
            auto_locked_until=timezone.now() + datetime.timedelta(hours=hours))

    def test_settings_match_decision(self):
        self.assertEqual(settings.ORDER_HOLD_MINUTES, 5)
        self.assertEqual(settings.ORDER_MAX_ITEMS, 20)

    def test_is_auto_locked_property(self):
        self.assertFalse(self.customer.is_auto_locked)
        self.customer.auto_locked_until = timezone.now() - datetime.timedelta(minutes=1)
        self.assertFalse(self.customer.is_auto_locked)
        self.customer.auto_locked_until = timezone.now() + datetime.timedelta(minutes=1)
        self.assertTrue(self.customer.is_auto_locked)

    def test_cancel_that_locks_logs_out_everywhere(self):
        other_device = Client()
        other_device.force_login(self.customer)
        self.client.force_login(self.customer)

        def cancel(request, code):
            self.lock()
            return True

        with mock.patch("orders.views.cancel_order", side_effect=cancel):
            response = self.client.post(reverse("orders:order_cancel", args=[CODE]), follow=True)
        self.assertEqual(response.redirect_chain[-1][0], reverse("accounts:login"))
        self.assertContains(response, "bị tạm khóa đến")
        self.assertEqual(sessions_of(self.customer), [])
        self.assertEqual(other_device.get(reverse("accounts:profile")).status_code, 302)
        event = SecurityEvent.objects.get(event_type="order_hold_abuse")
        self.assertEqual(event.detail["via"], "cancel")
        self.assertEqual(event.severity, "warning")

    def test_open_session_logged_out_when_locked(self):
        self.client.force_login(self.customer)
        self.assertEqual(self.client.get(reverse("accounts:profile")).status_code, 200)
        self.lock()
        response = self.client.get(reverse("accounts:profile"), follow=True)
        self.assertTrue(response.redirect_chain[-1][0].startswith(reverse("accounts:login")))
        self.assertContains(response, "bị tạm khóa đến")
        self.assertEqual(sessions_of(self.customer), [])
        self.assertTrue(SecurityEvent.objects.filter(event_type="logout", detail__reason="account_auto_locked").exists())

    def test_login_with_correct_password_refused_while_locked(self):
        self.lock()
        response = self.client.post(reverse("accounts:login"), {"username": "an_nguyen", "password": PASSWORD})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "bị tạm khóa đến")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_wrong_password_does_not_reveal_lock(self):
        self.lock()
        response = self.client.post(reverse("accounts:login"), {"username": "an_nguyen", "password": "sai-" + PASSWORD})
        self.assertNotContains(response, "bị tạm khóa")

    def test_login_works_after_lock_expired(self):
        self.lock(hours=-1)
        response = self.client.post(reverse("accounts:login"), {"username": "an_nguyen", "password": PASSWORD})
        self.assertEqual(response.status_code, 302)

    def test_checkout_refuses_cart_over_limit(self):
        self.client.force_login(self.customer)
        big = Cart(lines=tuple(line(i, 5) for i in range(1, 6)))
        with mock.patch("orders.views.get_cart", return_value=big), mock.patch("orders.views.place_order") as place:
            response = self.client.get(reverse("orders:checkout"), follow=True)
        self.assertEqual(response.redirect_chain[-1][0], reverse("orders:cart"))
        self.assertContains(response, "Mỗi đơn tối đa 20 cuốn")
        place.assert_not_called()

    def test_checkout_shows_hold_minutes(self):
        self.client.force_login(self.customer)
        with mock.patch("orders.views.get_cart", return_value=Cart(lines=(line(1, 2),))):
            response = self.client.get(reverse("orders:checkout"))
        self.assertContains(response, "bạn có 5 phút để thanh toán")


class HoldAbuseLabelTests(SimpleTestCase):
    def test_labels_and_messages(self):
        self.assertIn("order_hold_abuse", EVENT_LABELS)
        self.assertEqual(ACCOUNT_STATUS_LABELS["auto_locked"], "Khóa tự động (giữ kho)")
        self.assertEqual(ACCOUNT_STATUS_FILTERS["khoa-tu-dong"], "auto_locked")
        self.assertIn("ORDER_TOO_LARGE", ORDER_ERROR_MESSAGES)
        self.assertIn("ACCOUNT_LOCKED", ORDER_ERROR_MESSAGES)

    def test_auto_locked_account_can_be_unlocked_by_admin(self):
        now = timezone.now()
        row = StaffAccount(id=7, username="an_nguyen", email="an@example.test", phone=None, status="auto_locked",
                         date_joined=now, last_login=None)
        self.assertTrue(row.is_locked)
