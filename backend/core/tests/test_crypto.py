import base64
import secrets

from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase, override_settings

from core.crypto import DecryptionError, decrypt_field, encrypt_field

TEST_KEY = base64.b64encode(secrets.token_bytes(32)).decode()
OTHER_KEY = base64.b64encode(secrets.token_bytes(32)).decode()


@override_settings(FIELD_ENCRYPTION_KEY=TEST_KEY)
class FieldCryptoTests(SimpleTestCase):
    def test_round_trip(self):
        token = encrypt_field("0912345678", "ctx:1")
        self.assertTrue(token.startswith("v1."))
        self.assertNotIn("0912345678", token)
        self.assertEqual(decrypt_field(token, "ctx:1"), "0912345678")

    def test_same_plaintext_gives_different_ciphertext(self):
        self.assertNotEqual(encrypt_field("0912345678", "ctx:1"), encrypt_field("0912345678", "ctx:1"))

    def test_wrong_context_is_rejected(self):
        token = encrypt_field("0912345678", "ctx:1")
        with self.assertRaises(DecryptionError):
            decrypt_field(token, "ctx:2")

    def test_tampered_ciphertext_is_rejected(self):
        token = encrypt_field("0912345678", "ctx:1")
        raw = bytearray(base64.b64decode(token[3:]))
        raw[-1] ^= 1
        with self.assertRaises(DecryptionError):
            decrypt_field("v1." + base64.b64encode(bytes(raw)).decode(), "ctx:1")

    def test_wrong_key_is_rejected(self):
        token = encrypt_field("0912345678", "ctx:1")
        with override_settings(FIELD_ENCRYPTION_KEY=OTHER_KEY), self.assertRaises(DecryptionError):
            decrypt_field(token, "ctx:1")

    def test_garbage_is_rejected(self):
        for value in ("", "0912345678", "v1.", "v1.!!!", "v1." + base64.b64encode(b"short").decode(), None):
            with self.subTest(value=value), self.assertRaises(DecryptionError):
                decrypt_field(value, "ctx:1")

    def test_missing_or_short_key_is_configuration_error(self):
        for key in ("", "khong-phai-base64", base64.b64encode(b"16-byte-key-only").decode()):
            with self.subTest(key=key), override_settings(FIELD_ENCRYPTION_KEY=key), self.assertRaises(ImproperlyConfigured):
                encrypt_field("0912345678", "ctx:1")
