from types import SimpleNamespace
from unittest import mock

from django.core.management import CommandError, call_command
from django.db import OperationalError
from django.test import SimpleTestCase

from catalog import staff_services
from catalog.staff_services import (
    CATEGORY_ERROR_MESSAGES,
    CategoryError,
    StaffCategory,
    clean_name,
    create_category,
    delete_category,
    list_categories,
    make_slug,
    rename_category,
)


class SlugAndNameTests(SimpleTestCase):
    def test_vietnamese_names_become_ascii_slugs(self):
        cases = {
            "Văn học": "van-hoc",
            "Địa lý & Lịch sử": "dia-ly-lich-su",
            "  Khoa   học viễn tưởng ": "khoa-hoc-vien-tuong",
            "Kinh tế 4.0": "kinh-te-4-0",
            "ĐỜI SỐNG": "doi-song",
        }
        for name, slug in cases.items():
            with self.subTest(name=name):
                self.assertEqual(make_slug(name), slug)

    def test_name_without_letters_or_digits_is_rejected(self):
        with self.assertRaises(CategoryError) as ctx:
            make_slug("!!! ???")
        self.assertEqual(ctx.exception.code, "INVALID_INPUT")

    def test_clean_name_collapses_spaces_and_checks_length(self):
        self.assertEqual(clean_name("  Văn    học "), "Văn học")
        for bad in ("", "   ", None, "a" * 101):
            with self.subTest(bad=bad), self.assertRaises(CategoryError):
                clean_name(bad)


class CategoryProcedureTests(SimpleTestCase):
    def setUp(self):
        self.actor = SimpleNamespace(pk=7)
        self.cursor = mock.MagicMock()
        self.cursor.nextset.return_value = None
        self.cursor.fetchone.return_value = (15,)
        self.conn = mock.MagicMock()
        self.conn.in_atomic_block = False
        self.conn.cursor.return_value.__enter__.return_value = self.cursor
        patcher = mock.patch.object(staff_services, "connections", {"staff": self.conn})
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_create_passes_actor_clean_name_and_slug(self):
        self.assertEqual(create_category(self.actor, "  Văn   học "), 15)
        self.cursor.callproc.assert_called_once_with("sp_category_create", [7, "Văn học", "van-hoc", None])
        self.cursor.execute.assert_called_once_with("SELECT @_sp_category_create_3")

    def test_rename_sends_new_slug(self):
        rename_category(self.actor, "3", "Địa lý thế giới")
        self.cursor.callproc.assert_called_once_with("sp_category_rename", [7, 3, "Địa lý thế giới", "dia-ly-the-gioi"])

    def test_delete_passes_ids(self):
        delete_category(self.actor, 3)
        self.cursor.callproc.assert_called_once_with("sp_category_delete", [7, 3])

    def test_non_numeric_id_is_not_found_without_calling_database(self):
        with self.assertRaises(CategoryError) as ctx:
            delete_category(self.actor, "1 OR 1=1")
        self.assertEqual(ctx.exception.code, "CATEGORY_NOT_FOUND")
        self.cursor.callproc.assert_not_called()

    def test_each_signal_code_becomes_category_error(self):
        for code, message in CATEGORY_ERROR_MESSAGES.items():
            with self.subTest(code=code):
                self.cursor.callproc.side_effect = OperationalError(1644, code)
                with self.assertRaises(CategoryError) as ctx:
                    create_category(self.actor, "Văn học")
                self.assertEqual((ctx.exception.code, ctx.exception.message), (code, message))

    def test_permission_error_is_not_swallowed(self):
        self.cursor.callproc.side_effect = OperationalError(1370, "execute command denied")
        with self.assertRaises(OperationalError):
            delete_category(self.actor, 3)

    def test_refuses_inside_atomic_block(self):
        self.conn.in_atomic_block = True
        with self.assertRaises(RuntimeError):
            create_category(self.actor, "Văn học")
        self.cursor.callproc.assert_not_called()


class CategoryListTests(SimpleTestCase):
    def setUp(self):
        self.cursor = mock.MagicMock()
        self.cursor.nextset.return_value = None
        self.cursor.fetchall.return_value = [(1, "Văn học", "van-hoc", 3, 2, None), (2, "Địa lý", "dia-ly", 0, 0, None)]
        self.conn = mock.MagicMock()
        self.conn.in_atomic_block = False
        self.conn.cursor.return_value.__enter__.return_value = self.cursor
        patcher = mock.patch.object(staff_services, "connections", {"staff": self.conn})
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_list_calls_procedure_and_maps_rows(self):
        rows = list_categories()
        self.cursor.callproc.assert_called_once_with("sp_category_list", [])
        self.assertEqual([(c.id, c.name, c.book_count, c.active_book_count) for c in rows],
                         [(1, "Văn học", 3, 2), (2, "Địa lý", 0, 0)])
        self.assertEqual([c.can_delete for c in rows], [False, True])

    def test_list_refuses_inside_atomic_block(self):
        self.conn.in_atomic_block = True
        with self.assertRaises(RuntimeError):
            list_categories()

    def test_row_is_read_only(self):
        row = StaffCategory(1, "Văn học", "van-hoc", 0, 0, None)
        with self.assertRaises(AttributeError):
            row.name = "Khác"

    def test_grant_check_refuses_same_account_for_both_connections(self):
        with self.assertRaises(CommandError):
            call_command("db_check_grants")
