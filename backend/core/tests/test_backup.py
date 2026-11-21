import base64
import datetime
import io
import json
import secrets
import tarfile
import tempfile
from pathlib import Path
from unittest import mock

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase, override_settings

from core import backup
from core.backup import (BackupConfig, BackupError, EncryptingWriter, compare_counts, decrypt_file,
                         expired_backups, open_backup, parse_backup_time)

KEY = secrets.token_bytes(32)
OTHER_KEY = secrets.token_bytes(32)


def config(tmp, prefix=()):
    return BackupConfig(db_name="bookstore", backup_dir=Path(tmp), offsite_dir=None, export_dir=Path(tmp) / "plain",
                        retention_days=365, dump_prefix=tuple(prefix), backup_password=secrets.token_urlsafe(8),
                        key=KEY)


def encrypt_bytes(key, data, path):
    with path.open("wb") as raw:
        writer = EncryptingWriter(key, raw)
        for start in range(0, len(data), 7):
            writer.write(data[start:start + 7])
        writer.finish()


def make_archive(path, members, key=KEY):
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as tar:
        for name, data in members.items():
            info = tarfile.TarInfo(name)
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
    encrypt_bytes(key, buffer.getvalue(), path)


def manifest_for(sql):
    import hashlib
    return json.dumps({"format": 1, "sql_sha256": hashlib.sha256(sql).hexdigest(), "counts": {"t": 1}}).encode()


class BackupCryptoTests(SimpleTestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.data = secrets.token_bytes(5000)
        self.enc = self.tmp / "x.enc"
        encrypt_bytes(KEY, self.data, self.enc)

    def test_roundtrip_and_header(self):
        out = self.tmp / "out"
        decrypt_file(KEY, self.enc, out)
        self.assertEqual(out.read_bytes(), self.data)
        raw = self.enc.read_bytes()
        self.assertTrue(raw.startswith(backup.MAGIC + b"\x01"))
        self.assertNotIn(self.data[:64], raw)

    def test_wrong_key_rejected(self):
        with self.assertRaises(BackupError):
            decrypt_file(OTHER_KEY, self.enc, self.tmp / "out")

    def test_tampered_or_truncated_rejected(self):
        raw = bytearray(self.enc.read_bytes())
        for label, blob in (("flip", raw[:100] + bytes([raw[100] ^ 1]) + raw[101:]),
                            ("cut", raw[:-5]), ("magic", b"XXXX" + raw[4:]), ("short", raw[:10])):
            with self.subTest(label=label):
                bad = self.tmp / f"{label}.enc"
                bad.write_bytes(bytes(blob))
                with self.assertRaises(BackupError):
                    decrypt_file(KEY, bad, self.tmp / f"{label}.out")

    def test_key_must_be_32_bytes(self):
        self.assertEqual(backup.decode_key(base64.b64encode(KEY).decode()), KEY)
        for bad in ("", "abc", base64.b64encode(b"x" * 16).decode()):
            with self.subTest(bad=bad), self.assertRaises(BackupError):
                backup.decode_key(bad)


class OpenBackupTests(SimpleTestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.cfg = config(self.tmp)
        self.sql = b"CREATE TABLE t (id INT);\nINSERT INTO t VALUES (1);\n"

    def _open(self, members):
        path = self.tmp / "bookstore-20261116T000000Z.tar.gz.enc"
        make_archive(path, members)
        work = Path(tempfile.mkdtemp(dir=self.tmp))
        return path, lambda: open_backup(self.cfg, path, work)

    def test_valid_archive(self):
        cover = "ab" * 16 + ".webp"
        _, run = self._open({"manifest.json": manifest_for(self.sql), "bookstore.sql": self.sql,
                             "media/covers/" + cover: b"img"})
        opened = run()
        self.assertEqual(opened.sql_path.read_bytes(), self.sql)
        self.assertEqual([c.name for c in opened.covers], [cover])

    def test_bad_members_rejected(self):
        for name in ("../evil.sql", "/etc/passwd", "media/covers/evil.php", "media/covers/../../x.webp", "other.txt"):
            with self.subTest(name=name):
                _, run = self._open({"manifest.json": manifest_for(self.sql), "bookstore.sql": self.sql, name: b"x"})
                with self.assertRaises(BackupError):
                    run()

    def test_sql_must_match_manifest(self):
        _, run = self._open({"manifest.json": manifest_for(b"other"), "bookstore.sql": self.sql})
        with self.assertRaises(BackupError):
            run()

    def test_sha256_sidecar_checked(self):
        path, run = self._open({"manifest.json": manifest_for(self.sql), "bookstore.sql": self.sql})
        path.with_name(path.name + ".sha256").write_text("0" * 64 + "  x\n", encoding="ascii")
        with self.assertRaises(BackupError):
            run()


class BackupHelpersTests(SimpleTestCase):
    def test_retention_uses_name_and_ignores_unknown_files(self):
        tmp = Path(tempfile.mkdtemp())
        now = datetime.datetime(2026, 11, 16, tzinfo=datetime.UTC)
        names = ["bookstore-20251115T000000Z.tar.gz.enc", "bookstore-20251117T000000Z.tar.gz.enc",
                 "bookstore-20240101T000000Z.tar.gz.enc.sha256", "notes.txt", "bookstore-2024.tar.gz.enc"]
        for name in names:
            (tmp / name).write_text("x")
        self.assertEqual([p.name for p in expired_backups(tmp, now, 365)], [names[0]])
        self.assertIsNone(parse_backup_time("bookstore-20261340T000000Z.tar.gz.enc"))
        (tmp / "bookstore-20261340T000000Z.tar.gz.enc").write_text("x")
        self.assertEqual([p.name for p in expired_backups(tmp, now, 365)], [names[0]])

    def test_compare_counts(self):
        self.assertEqual(compare_counts({"a": 1, "b": 2}, {"a": 1, "b": 2}), [])
        self.assertEqual(compare_counts({"a": 1}, {"a": 2, "c": 0}), [("a", 1, 2), ("c", None, 0)])

    @override_settings(REPO_DIR=Path(tempfile.gettempdir()))
    def test_password_only_on_stdin(self):
        cfg = config(tempfile.mkdtemp(), prefix=["sudo", "docker", "compose", "exec", "-T", "db"])
        process = mock.MagicMock(returncode=0)
        process.communicate.return_value = (b"", b"")
        with mock.patch.object(backup.subprocess, "Popen", return_value=process) as popen:
            backup.run_client(cfg, "mysqldump", ["--single-transaction", "bookstore"], stdout=None)
        command = popen.call_args.args[0]
        self.assertEqual(command[:6], ["sudo", "docker", "compose", "exec", "-T", "db"])
        self.assertIn("mysqldump", command)
        self.assertIn("--user=bookstore_backup", command)
        self.assertNotIn(cfg.backup_password, " ".join(command))
        self.assertTrue(process.communicate.call_args.args[0].startswith(cfg.backup_password.encode() + b"\n"))
        self.assertEqual(popen.call_args.kwargs.get("shell", False), False)

    def test_client_error_raises(self):
        cfg = config(tempfile.mkdtemp())
        process = mock.MagicMock(returncode=2)
        process.communicate.return_value = (b"", b"mysqldump: Got error: 1045: Access denied")
        with mock.patch.object(backup.subprocess, "Popen", return_value=process), self.assertRaises(BackupError):
            backup.run_client(cfg, "mysqldump", [], stdout=None)


class BackupCommandTests(SimpleTestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.file = self.tmp / "bookstore-20261116T000000Z.tar.gz.enc"
        self.file.write_bytes(b"x")

    def test_export_requires_confirmation(self):
        with mock.patch("core.management.commands.db_backup_export.open_backup") as opener, \
                self.assertRaises(CommandError):
            call_command("db_backup_export", str(self.file), confirm="sai", stdout=io.StringIO())
        opener.assert_not_called()

    def test_restore_requires_database_name(self):
        with mock.patch("core.management.commands.db_restore.create_backup") as create, \
                mock.patch("core.management.commands.db_restore.connect_admin") as connect, \
                self.assertRaises(CommandError):
            call_command("db_restore", str(self.file), confirm="khac", stdout=io.StringIO())
        create.assert_not_called()
        connect.assert_not_called()

    def test_backup_failure_logged(self):
        with mock.patch("core.management.commands.db_backup.load_config", side_effect=BackupError("thiếu khóa")), \
                mock.patch("core.management.commands.db_backup.log_backup_event") as log, \
                self.assertRaises(CommandError):
            call_command("db_backup", stdout=io.StringIO())
        self.assertEqual(log.call_args.args[0], "backup_failed")
        self.assertEqual(log.call_args.kwargs["severity"], "critical")


class SessionAndLogTests(SimpleTestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.cfg = config(self.tmp / "backups")
        self.log_dir = self.tmp / "logs"
        self.log_dir.mkdir()
        (self.log_dir / "security.log").write_text("dong log moi\n", encoding="utf-8")
        (self.log_dir / "security.log.1").write_text("dong log cu\n", encoding="utf-8")
        (self.log_dir / "django.log").write_text("khong lay\n", encoding="utf-8")
        self.calls = []

    def fake_client(self, cfg, tool, args, stdout, stdin_extra=b""):
        self.calls.append((tool, list(args)))
        stdout.write(b"-- dump " + " ".join(args).encode() + b"\n")
        return b""

    def make_backup(self):
        counts = {"core_securityevent": 4, "django_session": 7, "#routines": 1}
        with override_settings(LOG_DIR=self.log_dir, MEDIA_ROOT=self.tmp / "media"), \
                mock.patch.object(backup, "snapshot_counts", return_value=dict(counts)), \
                mock.patch.object(backup, "run_client", side_effect=self.fake_client):
            return backup.create_backup(self.cfg)

    def test_session_rows_are_not_dumped(self):
        self.make_backup()
        (_, main), (_, session) = self.calls
        self.assertIn("--ignore-table=bookstore.django_session", main)
        self.assertIn("--routines", main)
        self.assertEqual(session[-2:], ["bookstore", "django_session"])
        self.assertIn("--no-data", session)
        self.assertNotIn("--routines", session)
        self.assertNotIn("--events", session)

    def test_manifest_and_logs(self):
        result = self.make_backup()
        self.assertEqual(result.logs, 2)
        opened = open_backup(self.cfg, result.path, Path(tempfile.mkdtemp(dir=self.tmp)))
        self.assertEqual(opened.manifest["counts"]["django_session"], 0)
        self.assertFalse(opened.manifest["session_data"])
        self.assertEqual(opened.manifest["logs"], ["security.log", "security.log.1"])
        self.assertEqual(sorted(p.name for p in opened.logs), ["security.log", "security.log.1"])
        self.assertIn(b"django_session", opened.sql_path.read_bytes())

    def test_restore_logs_go_to_separate_folder(self):
        result = self.make_backup()
        opened = open_backup(self.cfg, result.path, Path(tempfile.mkdtemp(dir=self.tmp)))
        (self.log_dir / "security.log").write_text("log sau khi sao luu\n", encoding="utf-8")
        folder = backup.restore_logs(self.cfg, opened.logs, result.path.name)
        self.assertEqual(folder, self.cfg.backup_dir / "restored-logs" / result.path.name.split(".", 1)[0])
        self.assertEqual((folder / "security.log").read_text(encoding="utf-8"), "dong log moi\n")
        self.assertEqual((self.log_dir / "security.log").read_text(encoding="utf-8"), "log sau khi sao luu\n")
        self.assertEqual(folder.stat().st_mode & 0o777, 0o700)
        self.assertIsNone(backup.restore_logs(self.cfg, (), result.path.name))

    def test_unknown_log_members_rejected(self):
        sql = b"SELECT 1;\n"
        for name in ("logs/django.log", "logs/../security.log", "logs/security.log.10", "logs/sub/security.log"):
            with self.subTest(name=name):
                path = self.tmp / "bookstore-20261121T000000Z.tar.gz.enc"
                make_archive(path, {"manifest.json": manifest_for(sql), "bookstore.sql": sql, name: b"x"})
                with self.assertRaises(BackupError):
                    open_backup(self.cfg, path, Path(tempfile.mkdtemp(dir=self.tmp)))
