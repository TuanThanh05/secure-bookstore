import base64
import binascii
import datetime
import hashlib
import io
import json
import os
import re
import shlex
import shutil
import subprocess  # nosec B404
import tarfile
import tempfile
from dataclasses import dataclass
from pathlib import Path

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from django.conf import settings

from core.dbadmin import ADMIN_ENV_FILE, load_admin_env

BACKUP_USER = "bookstore_backup"
MAGIC = b"SBBK"
VERSION = 1
NONCE_SIZE = 12
TAG_SIZE = 16
HEADER_SIZE = len(MAGIC) + 1 + NONCE_SIZE
CHUNK = 1024 * 1024

FILE_RE = re.compile(r"^bookstore-(\d{8}T\d{6}Z)\.tar\.gz\.enc$")
COVER_RE = re.compile(r"^[0-9a-f]{32}\.webp$")
SQL_MEMBER = "bookstore.sql"
MANIFEST_MEMBER = "manifest.json"
COVERS_PREFIX = "media/covers/"
LOGS_PREFIX = "logs/"
LOG_RE = re.compile(r"^security\.log(\.[1-9])?$")
SESSION_TABLE = "django_session"
DUMP_SCRIPT = 'IFS= read -r MYSQL_PWD; export MYSQL_PWD; exec "$@"'
DUMP_OPTIONS = (
    "--single-transaction", "--quick", "--routines", "--triggers", "--events", "--no-tablespaces",
    "--set-gtid-purged=OFF", "--hex-blob", "--skip-add-locks", "--default-character-set=utf8mb4",
)
SESSION_DUMP_OPTIONS = (
    "--single-transaction", "--no-data", "--skip-triggers", "--no-tablespaces", "--set-gtid-purged=OFF", "--skip-add-locks",
    "--default-character-set=utf8mb4",
)


class BackupError(Exception):
    pass


@dataclass(frozen=True)
class BackupConfig:
    db_name: str
    backup_dir: Path
    offsite_dir: Path | None
    export_dir: Path
    retention_days: int
    dump_prefix: tuple
    backup_password: str
    key: bytes


def load_config(require_password=True):
    load_admin_env()
    key = decode_key(os.environ.get("BACKUP_ENCRYPTION_KEY", ""))
    password = os.environ.get("DB_BACKUP_PASSWORD", "")
    if require_password and not password:
        raise BackupError(f"Thiếu DB_BACKUP_PASSWORD trong {ADMIN_ENV_FILE}.")
    offsite = settings.BACKUP_OFFSITE_DIR
    return BackupConfig(
        db_name=settings.DATABASES["default"]["NAME"],
        backup_dir=Path(settings.BACKUP_DIR),
        offsite_dir=Path(offsite) if offsite else None,
        export_dir=Path(settings.BACKUP_EXPORT_DIR),
        retention_days=int(settings.BACKUP_RETENTION_DAYS),
        dump_prefix=tuple(shlex.split(settings.BACKUP_DUMP_PREFIX or "")),
        backup_password=password,
        key=key,
    )


def decode_key(value):
    try:
        raw = base64.b64decode(value, validate=True)
    except (binascii.Error, ValueError, TypeError):
        raw = b""
    if len(raw) != 32:
        raise BackupError(f"BACKUP_ENCRYPTION_KEY trong {ADMIN_ENV_FILE} phải là 32 byte mã hóa base64.")
    return raw


class EncryptingWriter(io.RawIOBase):
    def __init__(self, key, raw):
        nonce = os.urandom(NONCE_SIZE)
        header = MAGIC + bytes([VERSION]) + nonce
        self._raw = raw
        self._enc = Cipher(algorithms.AES(key), modes.GCM(nonce)).encryptor()
        self._enc.authenticate_additional_data(header)
        self._raw.write(header)

    def writable(self):
        return True

    def write(self, data):
        self._raw.write(self._enc.update(bytes(data)))
        return len(data)

    def finish(self):
        self._raw.write(self._enc.finalize())
        self._raw.write(self._enc.tag)


def decrypt_file(key, src, dst):
    size = src.stat().st_size
    if size < HEADER_SIZE + TAG_SIZE:
        raise BackupError("File sao lưu quá ngắn hoặc không đúng định dạng.")
    with src.open("rb") as fin:
        header = fin.read(HEADER_SIZE)
        if header[:4] != MAGIC or header[4] != VERSION:
            raise BackupError("File không phải bản sao lưu của hệ thống (sai mã nhận dạng).")
        fin.seek(size - TAG_SIZE)
        tag = fin.read(TAG_SIZE)
        fin.seek(HEADER_SIZE)
        dec = Cipher(algorithms.AES(key), modes.GCM(header[5:], tag)).decryptor()
        dec.authenticate_additional_data(header)
        remaining = size - HEADER_SIZE - TAG_SIZE
        with dst.open("wb") as fout:
            while remaining:
                chunk = fin.read(min(CHUNK, remaining))
                if not chunk:
                    raise BackupError("File sao lưu bị cắt cụt.")
                remaining -= len(chunk)
                fout.write(dec.update(chunk))
            try:
                fout.write(dec.finalize())
            except Exception as exc:
                raise BackupError("Giải mã thất bại: sai BACKUP_ENCRYPTION_KEY hoặc file đã bị sửa.") from exc


def sha256_of(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(CHUNK), b""):
            digest.update(chunk)
    return digest.hexdigest()


def backup_name(now):
    return f"bookstore-{now.astimezone(datetime.UTC):%Y%m%dT%H%M%SZ}.tar.gz.enc"


def parse_backup_time(name):
    match = FILE_RE.match(name)
    if not match:
        return None
    try:
        return datetime.datetime.strptime(match.group(1), "%Y%m%dT%H%M%SZ").replace(tzinfo=datetime.UTC)
    except ValueError:
        return None


def expired_backups(folder, now, days):
    if not folder.is_dir():
        return []
    limit = now - datetime.timedelta(days=days)
    old = []
    for path in sorted(folder.iterdir()):
        stamp = parse_backup_time(path.name)
        if stamp is not None and path.is_file() and stamp < limit:
            old.append(path)
    return old


def latest_backup(folder):
    if not folder.is_dir():
        return None
    found = sorted((p for p in folder.iterdir() if parse_backup_time(p.name)), key=lambda p: p.name)
    return found[-1] if found else None


def secure_dir(path):
    path.mkdir(parents=True, exist_ok=True)
    path.chmod(0o700)
    return path


def client_command(config, tool, args):
    return [*config.dump_prefix, "sh", "-c", DUMP_SCRIPT, "sh", tool, f"--user={BACKUP_USER}", *args]


def run_client(config, tool, args, stdout, stdin_extra=b""):
    command = client_command(config, tool, args)
    try:
        process = subprocess.Popen(  # nosec B603
            command, stdin=subprocess.PIPE, stdout=stdout, stderr=subprocess.PIPE, cwd=settings.REPO_DIR,
        )
    except OSError as exc:
        raise BackupError(f"Không chạy được {command[0]}: {exc}") from exc
    _, err = process.communicate(config.backup_password.encode("utf-8") + b"\n" + stdin_extra)
    if process.returncode != 0:
        message = err.decode("utf-8", "replace").strip().splitlines()
        message = [line for line in message if "password on the command line" not in line.lower()]
        raise BackupError(f"{tool} lỗi (mã {process.returncode}): {' | '.join(message)[-400:]}")
    return err


def snapshot_counts(config):
    tables_sql = ("SELECT table_name FROM information_schema.tables WHERE table_schema = DATABASE() "
                  "AND table_type = 'BASE TABLE' ORDER BY table_name")
    out = io.BytesIO()
    _capture(config, ["--batch", "--skip-column-names", f"--database={config.db_name}", "-e", tables_sql], out)
    tables = [t for t in out.getvalue().decode("utf-8").split() if re.fullmatch(r"[A-Za-z0-9_]{1,64}", t)]
    parts = [f"SELECT '{t}', COUNT(*) FROM `{t}`" for t in tables]  # nosec B608
    parts += [
        "SELECT '#routines', COUNT(*) FROM information_schema.routines WHERE routine_schema = DATABASE()",
        "SELECT '#triggers', COUNT(*) FROM information_schema.triggers WHERE trigger_schema = DATABASE()",
        "SELECT '#events', COUNT(*) FROM information_schema.events WHERE event_schema = DATABASE()",
    ]
    out = io.BytesIO()
    _capture(config, ["--batch", "--skip-column-names", f"--database={config.db_name}", "-e",
                      " UNION ALL ".join(parts)], out)
    counts = {}
    for line in out.getvalue().decode("utf-8").splitlines():
        name, _, value = line.partition("\t")
        if value.isdigit():
            counts[name] = int(value)
    return counts


def _capture(config, args, out):
    with tempfile.TemporaryFile() as handle:
        run_client(config, "mysql", args, handle)
        handle.seek(0)
        out.write(handle.read())


@dataclass(frozen=True)
class BackupResult:
    path: Path
    size: int
    sha256: str
    tables: int
    covers: int
    logs: int
    offsite: Path | None
    deleted: tuple


def create_backup(config, now=None):
    now = now or datetime.datetime.now(datetime.UTC)
    old_umask = os.umask(0o077)
    try:
        secure_dir(config.backup_dir)
        counts = snapshot_counts(config)
        session_rows = counts.get(SESSION_TABLE)
        if session_rows is not None:
            counts[SESSION_TABLE] = 0
        with tempfile.TemporaryDirectory(dir=config.backup_dir, prefix=".tmp-") as tmp:
            sql_path = Path(tmp) / SQL_MEMBER
            with sql_path.open("wb") as handle:
                run_client(config, "mysqldump",
                           [*DUMP_OPTIONS, f"--ignore-table={config.db_name}.{SESSION_TABLE}", config.db_name], handle)
            if sql_path.stat().st_size == 0:
                raise BackupError("mysqldump không trả về dữ liệu.")
            if session_rows is not None:
                with sql_path.open("ab") as handle:
                    run_client(config, "mysqldump", [*SESSION_DUMP_OPTIONS, config.db_name, SESSION_TABLE], handle)
            covers = _cover_files()
            logs = _log_files()
            manifest = {
                "format": 1, "created_at": now.isoformat(), "database": config.db_name,
                "sql_sha256": sha256_of(sql_path), "sql_size": sql_path.stat().st_size,
                "counts": counts, "covers": len(covers), "logs": [log.name for log in logs],
                "session_data": False,
            }
            final = config.backup_dir / backup_name(now)
            partial = final.with_name(final.name + ".part")
            with partial.open("wb") as raw:
                writer = EncryptingWriter(config.key, raw)
                with tarfile.open(fileobj=writer, mode="w|gz") as tar:
                    _add_bytes(tar, MANIFEST_MEMBER, json.dumps(manifest, ensure_ascii=False, indent=2).encode())
                    tar.add(sql_path, arcname=SQL_MEMBER, recursive=False)
                    for cover in covers:
                        tar.add(cover, arcname=COVERS_PREFIX + cover.name, recursive=False)
                    for log in logs:
                        tar.add(log, arcname=LOGS_PREFIX + log.name, recursive=False)
                writer.finish()
            partial.replace(final)
        digest = sha256_of(final)
        final.with_name(final.name + ".sha256").write_text(f"{digest}  {final.name}\n", encoding="ascii")
        offsite = _copy_offsite(config, final)
        deleted = tuple(_prune(config, now))
    finally:
        os.umask(old_umask)
    return BackupResult(path=final, size=final.stat().st_size, sha256=digest,
                        tables=sum(1 for k in counts if not k.startswith("#")), covers=len(covers),
                        logs=len(logs), offsite=offsite, deleted=deleted)


def _cover_files():
    folder = Path(settings.MEDIA_ROOT) / "covers"
    if not folder.is_dir():
        return []
    return [p for p in sorted(folder.iterdir()) if p.is_file() and not p.is_symlink() and COVER_RE.match(p.name)]


def _log_files():
    folder = Path(settings.LOG_DIR)
    if not folder.is_dir():
        return []
    return [p for p in sorted(folder.iterdir()) if p.is_file() and not p.is_symlink() and LOG_RE.match(p.name)]


def _add_bytes(tar, name, data):
    info = tarfile.TarInfo(name)
    info.size = len(data)
    info.mode = 0o600
    tar.addfile(info, io.BytesIO(data))


def _copy_offsite(config, final):
    if config.offsite_dir is None:
        return None
    secure_dir(config.offsite_dir)
    target = config.offsite_dir / final.name
    shutil.copy2(final, target)
    shutil.copy2(final.with_name(final.name + ".sha256"), config.offsite_dir / (final.name + ".sha256"))
    if sha256_of(target) != sha256_of(final):
        raise BackupError("Bản chép off-site không khớp SHA-256.")
    return target


def _prune(config, now):
    removed = []
    for folder in filter(None, (config.backup_dir, config.offsite_dir)):
        for path in expired_backups(folder, now, config.retention_days):
            path.unlink()
            sidecar = path.with_name(path.name + ".sha256")
            if sidecar.exists():
                sidecar.unlink()
            removed.append(path.name)
    return removed


@dataclass(frozen=True)
class OpenedBackup:
    manifest: dict
    sql_path: Path
    covers: tuple
    logs: tuple = ()


def open_backup(config, path, workdir):
    sidecar = path.with_name(path.name + ".sha256")
    if sidecar.exists():
        expected = sidecar.read_text(encoding="ascii").split()[0]
        if sha256_of(path) != expected:
            raise BackupError("SHA-256 của file sao lưu không khớp file .sha256 đi kèm (file hỏng hoặc bị sửa).")
    archive = workdir / "archive.tar.gz"
    decrypt_file(config.key, path, archive)
    covers_dir = workdir / "covers"
    covers_dir.mkdir()
    logs_dir = workdir / "logs"
    logs_dir.mkdir()
    manifest = None
    sql_path = workdir / SQL_MEMBER
    covers = []
    logs = []
    with tarfile.open(archive, mode="r:gz") as tar:
        for member in tar:
            name = member.name
            if not member.isfile():
                raise BackupError(f"Gói sao lưu có thành phần lạ: {name!r}")
            if name == MANIFEST_MEMBER:
                manifest = json.loads(tar.extractfile(member).read().decode("utf-8"))
            elif name == SQL_MEMBER:
                _extract_to(tar, member, sql_path)
            elif name.startswith(COVERS_PREFIX) and COVER_RE.match(name[len(COVERS_PREFIX):]):
                target = covers_dir / name[len(COVERS_PREFIX):]
                _extract_to(tar, member, target)
                covers.append(target)
            elif name.startswith(LOGS_PREFIX) and LOG_RE.match(name[len(LOGS_PREFIX):]):
                target = logs_dir / name[len(LOGS_PREFIX):]
                _extract_to(tar, member, target)
                logs.append(target)
            else:
                raise BackupError(f"Gói sao lưu có thành phần lạ: {name!r}")
    archive.unlink()
    if manifest is None or not sql_path.exists():
        raise BackupError("Gói sao lưu thiếu manifest hoặc file SQL.")
    if sha256_of(sql_path) != manifest.get("sql_sha256"):
        raise BackupError("File SQL trong gói không khớp mã băm ghi trong manifest.")
    return OpenedBackup(manifest=manifest, sql_path=sql_path, covers=tuple(covers), logs=tuple(logs))


def _extract_to(tar, member, target):
    with tar.extractfile(member) as src, target.open("wb") as dst:
        shutil.copyfileobj(src, dst)


def restore_covers(covers):
    folder = Path(settings.MEDIA_ROOT) / "covers"
    folder.mkdir(parents=True, exist_ok=True)
    for cover in covers:
        shutil.copyfile(cover, folder / cover.name)
    return len(covers)


def restore_logs(config, logs, source_name):
    if not logs:
        return None
    stem = source_name.split(".", 1)[0]
    folder = secure_dir(secure_dir(config.backup_dir / "restored-logs") / stem)
    old_umask = os.umask(0o077)
    try:
        for log in logs:
            shutil.copyfile(log, folder / log.name)
    finally:
        os.umask(old_umask)
    return folder


def execute_sql_file(conn, sql_path):
    from core.dbadmin import split_sql

    text = sql_path.read_text(encoding="utf-8")
    statements = split_sql(text)
    with conn.cursor() as cur:
        for number, statement in enumerate(statements, start=1):
            try:
                cur.execute(statement)
                while cur.nextset():
                    pass
            except Exception as exc:
                raise BackupError(f"Câu lệnh SQL thứ {number} lỗi: {exc}") from exc
    return len(statements)


def table_counts(conn, database):
    with conn.cursor() as cur:
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = %s "
                    "AND table_type = 'BASE TABLE' ORDER BY table_name", (database,))
        tables = [row[0] for row in cur.fetchall() if re.fullmatch(r"[A-Za-z0-9_]{1,64}", row[0])]
        counts = {}
        for table in tables:
            cur.execute(f"SELECT COUNT(*) FROM `{database}`.`{table}`")  # nosec B608
            counts[table] = int(cur.fetchone()[0])
        for key, sql in (("#routines", "SELECT COUNT(*) FROM information_schema.routines WHERE routine_schema = %s"),
                         ("#triggers", "SELECT COUNT(*) FROM information_schema.triggers WHERE trigger_schema = %s"),
                         ("#events", "SELECT COUNT(*) FROM information_schema.events WHERE event_schema = %s")):
            cur.execute(sql, (database,))
            counts[key] = int(cur.fetchone()[0])
    return counts


def compare_counts(expected, actual):
    keys = sorted(set(expected) | set(actual))
    return [(k, expected.get(k), actual.get(k)) for k in keys if expected.get(k) != actual.get(k)]


def log_backup_event(event_type, severity="info", **detail):
    from core.security_log import log_event

    log_event(event_type, severity=severity, username="cli", ip_address="cli", detail=detail)


def ask_confirmation(prompt, expected, given=None):
    answer = given if given is not None else input(prompt)
    if answer.strip() != expected:
        raise BackupError("Chưa xác nhận đúng, đã hủy (không thay đổi gì).")
