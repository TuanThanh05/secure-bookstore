import secrets

from django.contrib.auth.hashers import make_password
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import connection
from django.test import TestCase
from django.urls import reverse

from accounts.models import PasswordHistory, User
from accounts.validators import PasswordHistoryValidator


def new_secret(tag):
    return f"{secrets.token_urlsafe(12)}-{tag}-Aa9"


class PasswordHistoryTests(TestCase):
    def setUp(self):
        cache.clear()
        self.validator = PasswordHistoryValidator(history_count=5)
        self.secrets = [new_secret(i) for i in range(7)]
        self.user = User.objects.create_user(username="an_nguyen", email="an@example.test",
                                             password=self.secrets[0], email_verified=True)

    def put_history(self, raw_list):
        PasswordHistory.objects.filter(user_id=self.user.pk).delete()
        encoded = [make_password(raw) for raw in raw_list]
        with connection.cursor() as cur:
            for value in encoded:
                cur.execute("INSERT INTO accounts_passwordhistory (user_id, password_hash) VALUES (%s, %s)",
                            [self.user.pk, value])
        self.user.password = encoded[-1]
        User.objects.filter(pk=self.user.pk).update(password=encoded[-1])

    def rejected(self, raw):
        try:
            self.validator.validate(raw, self.user)
        except ValidationError as exc:
            return exc.error_list[0].code == "password_reused"
        return False

    def test_current_password_is_rejected_without_history_rows(self):
        PasswordHistory.objects.filter(user_id=self.user.pk).delete()
        self.assertTrue(self.rejected(self.secrets[0]))

    def test_five_most_recent_are_rejected_older_ones_allowed(self):
        self.put_history(self.secrets)
        for raw in self.secrets[2:]:
            self.assertTrue(self.rejected(raw))
        for raw in self.secrets[:2]:
            self.assertFalse(self.rejected(raw))

    def test_brand_new_password_is_allowed(self):
        self.put_history(self.secrets[:3])
        self.assertFalse(self.rejected(new_secret("moi")))

    def test_unsaved_user_is_skipped(self):
        self.validator.validate(self.secrets[0], User(username="chua_luu"))

    def test_unusable_hashes_are_ignored(self):
        PasswordHistory.objects.filter(user_id=self.user.pk).delete()
        self.user.set_unusable_password()
        self.assertFalse(self.rejected(self.secrets[0]))

    def test_validator_is_enabled_in_settings(self):
        from django.contrib.auth.password_validation import get_default_password_validators
        found = [v for v in get_default_password_validators() if isinstance(v, PasswordHistoryValidator)]
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0].history_count, 5)

    def test_change_password_page_rejects_recent_password(self):
        self.put_history(self.secrets[:4])
        current = self.secrets[3]
        self.client.force_login(self.user)
        response = self.client.post(reverse("accounts:password_change"), {
            "old_password": current, "new_password1": self.secrets[1], "new_password2": self.secrets[1],
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "5 mật khẩu gần nhất")
        self.assertTrue(User.objects.get(pk=self.user.pk).check_password(current))
