import shutil
import tempfile
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, override_settings
from PIL import Image

from catalog import book_services, staff_services
from catalog.book_services import BookError, create_book, delete_book, update_book
from catalog.covers import COVER_PATH_RE, MAX_UPLOAD_BYTES, CoverError, delete_cover, sanitize_cover, save_cover

VALID = {"title": "Nhà Giả Kim", "author": "Paulo Coelho", "isbn": "9780306406157", "category_id": 4,
         "description": None, "price": 79000, "cost_price": 50000}


def image_bytes(fmt="JPEG", size=(300, 450), mode="RGB", **save_kwargs):
    buffer = BytesIO()
    color = {"RGBA": (200, 30, 30, 128), "L": 200}.get(mode, (200, 30, 30))
    Image.new(mode, size, color).save(buffer, format=fmt, **save_kwargs)
    return buffer.getvalue()


def upload(data, name="bia.jpg", content_type="image/jpeg"):
    return SimpleUploadedFile(name, data, content_type=content_type)


def jpeg_with_gps():
    exif = Image.Exif()
    exif[0x010F] = "MayAnhBiMat"
    exif[0x8825] = {2: (21.0, 1.0, 0.0), 4: (105.0, 50.0, 0.0)}
    return image_bytes("JPEG", exif=exif.tobytes())


# AI-TRACE#152 | Claude Opus 5.5 | Test kiểm tra ảnh bìa: nhận ảnh thật, chặn file giả, ảnh bom, file quá lớn, xóa metadata và nội dung cài kèm | CẤM XÓA CHÚ THÍCH NÀY
class SanitizeCoverTests(SimpleTestCase):
    def open_result(self, data):
        return Image.open(BytesIO(sanitize_cover(upload(data))))

    def test_jpeg_png_webp_become_webp(self):
        for fmt in ("JPEG", "PNG", "WEBP"):
            with self.subTest(fmt=fmt), self.open_result(image_bytes(fmt)) as result:
                self.assertEqual(result.format, "WEBP")
                self.assertEqual(result.size, (300, 450))

    def test_transparent_png_gets_white_background(self):
        with self.open_result(image_bytes("PNG", mode="RGBA")) as result:
            self.assertEqual(result.mode, "RGB")

    def test_large_image_is_shrunk(self):
        with self.open_result(image_bytes("JPEG", size=(2400, 3600))) as result:
            self.assertEqual(result.size, (1200, 1800))

    def test_exif_and_gps_are_removed(self):
        data = jpeg_with_gps()
        with Image.open(BytesIO(data)) as original:
            self.assertTrue(original.getexif())
        cleaned = sanitize_cover(upload(data))
        self.assertNotIn(b"MayAnhBiMat", cleaned)
        with Image.open(BytesIO(cleaned)) as result:
            self.assertFalse(result.getexif())

    def test_payload_appended_to_real_image_is_dropped(self):
        payload = b"<?php system($_GET['c']); ?><script>alert(1)</script>"
        cleaned = sanitize_cover(upload(image_bytes("JPEG") + payload, name="bia.php.jpg"))
        self.assertNotIn(b"<?php", cleaned)
        self.assertNotIn(b"<script>", cleaned)

    def test_fake_and_unsupported_files_are_rejected(self):
        cases = {
            "text renamed": (b"<?php echo 1; ?>", "bia.jpg"),
            "svg": (b'<svg xmlns="http://www.w3.org/2000/svg" onload="alert(1)"/>', "bia.svg"),
            "gif": (image_bytes("GIF"), "bia.gif"),
            "bmp": (image_bytes("BMP"), "bia.bmp"),
            "truncated jpeg": (image_bytes("JPEG")[:200], "bia.jpg"),
            "empty": (b"", "bia.jpg"),
        }
        for label, (data, name) in cases.items():
            with self.subTest(label), self.assertRaises(CoverError) as ctx:
                sanitize_cover(upload(data, name=name))
            self.assertEqual(ctx.exception.code, "COVER_INVALID")

    def test_too_many_bytes_is_rejected(self):
        big = upload(b"\xff\xd8" + b"0" * MAX_UPLOAD_BYTES)
        with self.assertRaises(CoverError) as ctx:
            sanitize_cover(big)
        self.assertEqual(ctx.exception.code, "COVER_TOO_LARGE")

    def test_lying_size_attribute_is_not_trusted(self):
        big = upload(b"\xff\xd8" + b"0" * MAX_UPLOAD_BYTES)
        big.size = 10
        with self.assertRaises(CoverError) as ctx:
            sanitize_cover(big)
        self.assertEqual(ctx.exception.code, "COVER_TOO_LARGE")

    def test_decompression_bomb_is_rejected_before_decoding(self):
        bomb = image_bytes("PNG", size=(8000, 8000), mode="L", optimize=True)
        self.assertLess(len(bomb), MAX_UPLOAD_BYTES)
        with self.assertRaises(CoverError) as ctx:
            sanitize_cover(upload(bomb, name="bom.png"))
        self.assertEqual(ctx.exception.code, "COVER_DIMENSIONS")


# AI-TRACE#153 | Claude Opus 5.5 | Test lưu và xóa file ảnh bìa: tên UUID trong media/covers, không xóa được file ngoài thư mục | CẤM XÓA CHÚ THÍCH NÀY
class CoverStorageTests(SimpleTestCase):
    def setUp(self):
        self.media = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.media, ignore_errors=True)
        override = override_settings(MEDIA_ROOT=self.media)
        override.enable()
        self.addCleanup(override.disable)

    def test_saved_file_has_uuid_name_and_is_not_executable(self):
        path = save_cover(upload(image_bytes(), name="../../evil.php"))
        self.assertRegex(path, COVER_PATH_RE)
        target = self.media / path
        self.assertTrue(target.is_file())
        self.assertEqual(target.stat().st_mode & 0o777, 0o644)
        self.assertNotIn("evil", path)

    def test_two_uploads_never_share_a_name(self):
        self.assertNotEqual(save_cover(upload(image_bytes())), save_cover(upload(image_bytes())))

    def test_delete_removes_only_cover_files(self):
        path = save_cover(upload(image_bytes()))
        secret = self.media / "secret.txt"
        secret.write_text("giu nguyen")
        for bad in ("../secret.txt", "covers/../secret.txt", "secret.txt", "/etc/passwd",
                    "covers/" + "a" * 32 + ".webp/../../secret.txt", "", None):
            with self.subTest(bad=bad):
                self.assertFalse(delete_cover(bad))
        self.assertTrue(secret.exists())
        self.assertTrue(delete_cover(path))
        self.assertFalse((self.media / path).exists())
        self.assertFalse(delete_cover(path))


# AI-TRACE#154 | Claude Opus 5.5 | Test ảnh bìa trong luồng thêm/sửa/xóa sách: dọn file khi CSDL báo lỗi, xóa ảnh cũ khi thay hoặc bỏ | CẤM XÓA CHÚ THÍCH NÀY
class BookCoverFlowTests(SimpleTestCase):
    def setUp(self):
        self.media = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.media, ignore_errors=True)
        override = override_settings(MEDIA_ROOT=self.media)
        override.enable()
        self.addCleanup(override.disable)
        self.actor = SimpleNamespace(pk=7)
        self.cursor = mock.MagicMock()
        self.cursor.nextset.return_value = None
        self.cursor.fetchone.return_value = (21,)
        conn = mock.MagicMock(in_atomic_block=False)
        conn.cursor.return_value.__enter__.return_value = self.cursor
        patcher = mock.patch.object(staff_services, "connections", {"staff": conn})
        patcher.start()
        self.addCleanup(patcher.stop)

    def covers(self):
        folder = self.media / "covers"
        return sorted(p.name for p in folder.iterdir()) if folder.exists() else []

    def existing_book(self, cover):
        return mock.patch.object(book_services, "get_book", return_value=SimpleNamespace(cover_image=cover))

    def test_create_with_cover_sends_saved_path(self):
        create_book(self.actor, stock=1, cover_file=upload(image_bytes()), **VALID)
        sent = self.cursor.callproc.call_args.args[1][6]
        self.assertRegex(sent, COVER_PATH_RE)
        self.assertEqual(self.covers(), [sent.split("/")[1]])

    def test_create_without_cover_sends_null(self):
        create_book(self.actor, stock=1, **VALID)
        self.assertIsNone(self.cursor.callproc.call_args.args[1][6])

    def test_database_error_removes_new_file(self):
        from django.db import OperationalError
        self.cursor.callproc.side_effect = OperationalError(1644, "ISBN_EXISTS")
        with self.assertRaises(BookError):
            create_book(self.actor, stock=1, cover_file=upload(image_bytes()), **VALID)
        self.assertEqual(self.covers(), [])

    def test_invalid_image_stops_before_database(self):
        with self.assertRaises(CoverError):
            create_book(self.actor, stock=1, cover_file=upload(b"not an image"), **VALID)
        self.cursor.callproc.assert_not_called()

    def test_update_without_file_keeps_cover(self):
        old = save_cover(upload(image_bytes()))
        with self.existing_book(old):
            update_book(self.actor, 9, **VALID)
        self.assertEqual(self.cursor.callproc.call_args.args[1][7], old)
        self.assertTrue((self.media / old).exists())

    def test_update_with_new_file_replaces_and_deletes_old(self):
        old = save_cover(upload(image_bytes()))
        with self.existing_book(old):
            update_book(self.actor, 9, cover_file=upload(image_bytes("PNG")), **VALID)
        new = self.cursor.callproc.call_args.args[1][7]
        self.assertNotEqual(new, old)
        self.assertFalse((self.media / old).exists())
        self.assertTrue((self.media / new).exists())

    def test_failed_update_keeps_old_and_drops_new(self):
        from django.db import OperationalError
        old = save_cover(upload(image_bytes()))
        self.cursor.callproc.side_effect = OperationalError(1644, "ISBN_EXISTS")
        with self.existing_book(old), self.assertRaises(BookError):
            update_book(self.actor, 9, cover_file=upload(image_bytes()), **VALID)
        self.assertEqual(self.covers(), [old.split("/")[1]])

    def test_remove_cover_sets_null_and_deletes_file(self):
        old = save_cover(upload(image_bytes()))
        with self.existing_book(old):
            update_book(self.actor, 9, remove_cover=True, **VALID)
        self.assertIsNone(self.cursor.callproc.call_args.args[1][7])
        self.assertEqual(self.covers(), [])

    def test_delete_book_removes_cover_after_database(self):
        old = save_cover(upload(image_bytes()))
        with self.existing_book(old):
            delete_book(self.actor, 9)
        self.assertEqual(self.covers(), [])

    def test_failed_delete_keeps_cover(self):
        from django.db import OperationalError
        old = save_cover(upload(image_bytes()))
        self.cursor.callproc.side_effect = OperationalError(1644, "BOOK_HAS_ORDERS")
        with self.existing_book(old), self.assertRaises(BookError):
            delete_book(self.actor, 9)
        self.assertTrue((self.media / old).exists())

    def test_delete_never_touches_default_cover(self):
        with self.existing_book(None):
            delete_book(self.actor, 9)
        self.cursor.callproc.assert_called_once()
