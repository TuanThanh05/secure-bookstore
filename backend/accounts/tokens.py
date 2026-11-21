from typing import NamedTuple

from django.conf import settings
from django.core import signing

SIGNUP_SIGNING_SALT = "accounts.signup-link"


class SignupTokenResult(NamedTuple):
    status: str
    email: str | None = None


def make_signup_token(email):
    return signing.dumps({"e": email}, salt=SIGNUP_SIGNING_SALT)


def read_signup_token(token):
    try:
        data = signing.loads(token, salt=SIGNUP_SIGNING_SALT, max_age=settings.SIGNUP_LINK_MAX_AGE)
    except signing.SignatureExpired:
        return SignupTokenResult("expired")
    except signing.BadSignature:
        return SignupTokenResult("invalid")
    if not isinstance(data, dict) or set(data) != {"e"}:
        return SignupTokenResult("invalid")
    email = data["e"]
    if not isinstance(email, str) or not email or len(email) > 254:
        return SignupTokenResult("invalid")
    return SignupTokenResult("valid", email)
