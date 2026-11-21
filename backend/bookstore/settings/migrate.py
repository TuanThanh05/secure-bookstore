import os

import environ
from django.core.exceptions import ImproperlyConfigured

from .dev import *  # noqa: F401,F403
from .dev import DATABASES, REPO_DIR

_admin_env = REPO_DIR / "database" / ".env.db"
if _admin_env.exists():
    environ.Env.read_env(_admin_env, overwrite=False)

if not os.environ.get("DB_MIGRATE_PASSWORD"):
    raise ImproperlyConfigured(
        "Thiếu DB_MIGRATE_PASSWORD: điền vào database/.env.db (xem database/.env.db.example)."
    )

_migrate_account = {
    "USER": os.environ.get("DB_MIGRATE_USER", "bookstore_migrate"),
    "PASSWORD": os.environ["DB_MIGRATE_PASSWORD"],
    "CONN_MAX_AGE": 0,
}
DATABASES["default"] = {**DATABASES["default"], **_migrate_account}
DATABASES["staff"] = {**DATABASES["staff"], **_migrate_account}
DATABASES["session"] = {**DATABASES["session"], **_migrate_account}
SESSION_DB_ALIAS = "default"
DATABASES["auth"] = {**DATABASES["auth"], **_migrate_account}
AUTH_DB_ALIAS = "default"
