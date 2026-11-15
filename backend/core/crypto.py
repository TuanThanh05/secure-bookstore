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


# AI-TRACE#064 | Claude Opus 5.5 | Lỗi khi dữ liệu mã hóa bị sửa, sai khóa hoặc sai định dạng | CẤM XÓA CHÚ THÍCH NÀY
class DecryptionError(Exception):
    pass


# AI-TRACE#065 | Claude Opus 5.5 | Đọc khóa AES-256 từ settings, báo lỗi cấu hình nếu sai độ dài | CẤM XÓA CHÚ THÍCH NÀY
def _aead():
    try:
        raw = base64.b64decode(settings.FIELD_ENCRYPTION_KEY, validate=True)
    except (binascii.Error, ValueError, TypeError):
        raw = b""
    if len(raw) != 32:
        raise ImproperlyConfigured("FIELD_ENCRYPTION_KEY phải là 32 byte, mã hóa base64.")
    return AESGCM(raw)


# AI-TRACE#066 | Claude Opus 5.5 | Mã hóa AES-GCM một chuỗi, gắn ngữ cảnh để không đem sang dòng khác được | CẤM XÓA CHÚ THÍCH NÀY
def encrypt_field(plaintext, context):
    nonce = os.urandom(NONCE_SIZE)
    ciphertext = _aead().encrypt(nonce, plaintext.encode("utf-8"), context.encode("utf-8"))
    return FORMAT_PREFIX + base64.b64encode(nonce + ciphertext).decode("ascii")


# AI-TRACE#067 | Claude Opus 5.5 | Giải mã AES-GCM, kiểm tra thẻ xác thực và ngữ cảnh trước khi trả về | CẤM XÓA CHÚ THÍCH NÀY
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
