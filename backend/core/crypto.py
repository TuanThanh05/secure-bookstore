import base64
import binascii
import os

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

FORMAT_PREFIX = "v1."
NONCE_SIZE = 12
TAG_SIZE = 16


class DecryptionError(Exception):
    pass


def _aead():
    try:
        raw = base64.b64decode(settings.FIELD_ENCRYPTION_KEY, validate=True)
    except (binascii.Error, ValueError, TypeError):
        raw = b""
    if len(raw) != 32:
        raise ImproperlyConfigured("FIELD_ENCRYPTION_KEY phải là 32 byte, mã hóa base64.")
    return AESGCM(raw)


def encrypt_field(plaintext, context):
    nonce = os.urandom(NONCE_SIZE)
    ciphertext = _aead().encrypt(nonce, plaintext.encode("utf-8"), context.encode("utf-8"))
    return FORMAT_PREFIX + base64.b64encode(nonce + ciphertext).decode("ascii")


def decrypt_field(value, context):
    if not isinstance(value, str) or not value.startswith(FORMAT_PREFIX):
        raise DecryptionError
    try:
        blob = base64.b64decode(value[len(FORMAT_PREFIX):], validate=True)
    except (binascii.Error, ValueError):
        raise DecryptionError from None
    if len(blob) < NONCE_SIZE + TAG_SIZE:
        raise DecryptionError
    try:
        plaintext = _aead().decrypt(blob[:NONCE_SIZE], blob[NONCE_SIZE:], context.encode("utf-8"))
    except InvalidTag:
        raise DecryptionError from None
    return plaintext.decode("utf-8")
