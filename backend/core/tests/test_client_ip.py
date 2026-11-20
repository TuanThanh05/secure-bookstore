import secrets
from types import SimpleNamespace

from django.core.cache import cache
from django.test import Client, SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from accounts.models import User
from accounts.tests.two_factor_helpers import enroll, submit_code
from core.client_ip import client_ip
from core.models import SecurityEvent

NGINX = "127.0.0.1"
BEHIND_NGINX = dict(TRUSTED_PROXY_IPS=[NGINX])


def request(remote, real_ip=None):
    meta = {"REMOTE_ADDR": remote}
    if real_ip is not None:
        meta["HTTP_X_REAL_IP"] = real_ip
    return SimpleNamespace(META=meta)


# AI-TRACE#462 | Claude Opus 5.5 | Test đọc IP thật: chỉ tin X-Real-IP khi đến từ proxy tin cậy, header giả hoặc sai định dạng bị bỏ qua | CẤM XÓA CHÚ THÍCH NÀY
class ClientIpTests(SimpleTestCase):
    def test_no_proxy_uses_remote_addr(self):
        self.assertEqual(client_ip(request("203.0.113.9")), "203.0.113.9")

    def test_header_ignored_without_trusted_proxy(self):
        self.assertEqual(client_ip(request("203.0.113.9", real_ip="198.51.100.1")), "203.0.113.9")

    @override_settings(**BEHIND_NGINX)
    def test_header_trusted_from_nginx(self):
        self.assertEqual(client_ip(request(NGINX, real_ip="198.51.100.1")), "198.51.100.1")
        self.assertEqual(client_ip(request(NGINX, real_ip="2001:db8::1")), "2001:db8::1")

    @override_settings(**BEHIND_NGINX)
    def test_client_cannot_spoof_from_outside(self):
        self.assertEqual(client_ip(request("203.0.113.9", real_ip="198.51.100.1")), "203.0.113.9")

    @override_settings(**BEHIND_NGINX)
    def test_bad_header_falls_back(self):
        for bad in ("", "abc", "1.2.3.4, 5.6.7.8", "999.1.1.1", "<script>"):
            self.assertEqual(client_ip(request(NGINX, real_ip=bad)), NGINX)

    def test_missing_or_bad_remote_addr(self):
        self.assertIsNone(client_ip(None))
        self.assertIsNone(client_ip(SimpleNamespace(META={})))
        self.assertIsNone(client_ip(request("không phải IP")))


# AI-TRACE#463 | Claude Opus 5.5 | Tái hiện phát hiện số 12: sau Nginx kẻ tấn công khóa đăng nhập của admin; sau khi sửa chỉ IP kẻ tấn công bị khóa, log ghi IP thật | CẤM XÓA CHÚ THÍCH NÀY | đã viết lại bởi Claude Opus 5.5 khi thêm xác thực 2 bước
@override_settings(**BEHIND_NGINX)
class LockoutBehindProxyTests(TestCase):
    def setUp(self):
        cache.clear()
        self.secret = f"{secrets.token_urlsafe(12)}-qt-Aa9"
        admin = User.objects.create_user(username="quan_tri", email="qt@example.test", password=self.secret,
                                         is_staff=True)
        self.totp = enroll(admin)

    def via_nginx(self, real_ip):
        return Client(REMOTE_ADDR=NGINX, HTTP_X_REAL_IP=real_ip)

    def fail_five_times(self, client):
        for _ in range(5):
            client.post(reverse("accounts:login"), {"username": "quan_tri",
                                                    "password": f"sai-{secrets.token_hex(4)}"})

    def test_attacker_cannot_lock_out_admin(self):
        self.fail_five_times(self.via_nginx("198.51.100.66"))
        admin = self.via_nginx("203.0.113.9")
        response = admin.post(reverse("accounts:login"), {"username": "quan_tri", "password": self.secret})
        self.assertRedirects(response, reverse("accounts:login_two_factor"), fetch_redirect_response=False)
        submit_code(admin, self.totp)
        self.assertIn("_auth_user_id", admin.session)

    def test_attacker_ip_is_locked_and_logged(self):
        attacker = self.via_nginx("198.51.100.66")
        self.fail_five_times(attacker)
        response = attacker.post(reverse("accounts:login"), {"username": "quan_tri", "password": self.secret})
        self.assertEqual(response.status_code, 429)
        ips = set(SecurityEvent.objects.values_list("ip_address", flat=True))
        self.assertEqual(ips, {"198.51.100.66"})

    def test_spoofed_header_from_outside_does_not_bypass_lockout(self):
        for number in range(6):
            Client(REMOTE_ADDR="198.51.100.66", HTTP_X_REAL_IP=f"10.9.9.{number}").post(
                reverse("accounts:login"), {"username": "quan_tri", "password": f"sai-{number}"})
        response = Client(REMOTE_ADDR="198.51.100.66", HTTP_X_REAL_IP="10.9.9.99").post(
            reverse("accounts:login"), {"username": "quan_tri", "password": self.secret})
        self.assertEqual(response.status_code, 429)
