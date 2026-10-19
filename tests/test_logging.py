import logging
import os
import tempfile
import unittest
from datetime import date, datetime, time, timedelta
from pathlib import Path
from unittest import mock

from b3_selic_pre.infrastructure.logging_setup import (
    LOG_ACTIVE_NAME,
    LOG_DATE_FORMAT,
    LOG_FORMAT,
    _daily_namer,
    _make_handler,
    configure_logging,
    log_dir,
    purge_old_logs,
    rotate_stale_log,
)


class LoggingTestBase(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.log_directory = Path(self.tmpdir.name)
        self.today = date(2026, 10, 19)

    def tearDown(self):
        self.tmpdir.cleanup()

    def _active(self):
        return self.log_directory / LOG_ACTIVE_NAME

    def _backup(self, day):
        return self.log_directory / f"b3-selic-pre-{day.isoformat()}.log"

    def _set_mtime(self, path, day):
        timestamp = datetime.combine(day, time(12, 0)).timestamp()
        os.utime(path, (timestamp, timestamp))


class RotateStaleLogTest(LoggingTestBase):
    def test_missing_active_is_not_rotated(self):
        self.assertIsNone(rotate_stale_log(self._active(), today=self.today))
        self.assertEqual(list(self.log_directory.iterdir()), [])

    def test_active_from_today_is_not_rotated(self):
        active = self._active()
        active.write_text("today\n", encoding="utf-8")
        self._set_mtime(active, self.today)
        self.assertIsNone(rotate_stale_log(active, today=self.today))
        self.assertTrue(active.exists())
        self.assertFalse(self._backup(self.today).exists())

    def test_active_from_previous_day_is_rotated(self):
        yesterday = self.today - timedelta(days=1)
        active = self._active()
        active.write_text("old\n", encoding="utf-8")
        self._set_mtime(active, yesterday)
        result = rotate_stale_log(active, today=self.today)
        self.assertEqual(result, self._backup(yesterday))
        self.assertFalse(active.exists())
        self.assertEqual(self._backup(yesterday).read_text(encoding="utf-8"), "old\n")

    def test_collision_appends_and_removes_active(self):
        yesterday = self.today - timedelta(days=1)
        active = self._active()
        target = self._backup(yesterday)
        active.write_text("new\n", encoding="utf-8")
        target.write_text("existing", encoding="utf-8")
        self._set_mtime(active, yesterday)
        rotate_stale_log(active, today=self.today)
        self.assertFalse(active.exists())
        self.assertEqual(
            target.read_text(encoding="utf-8"), "existing\nnew\n"
        )

    def test_collision_does_not_double_separator(self):
        yesterday = self.today - timedelta(days=1)
        active = self._active()
        target = self._backup(yesterday)
        active.write_text("new\n", encoding="utf-8")
        target.write_text("existing\n", encoding="utf-8")
        self._set_mtime(active, yesterday)
        rotate_stale_log(active, today=self.today)
        self.assertEqual(
            target.read_text(encoding="utf-8"), "existing\nnew\n"
        )


class PurgeOldLogsTest(LoggingTestBase):
    def test_deletes_only_backups_older_than_cutoff(self):
        today_backup = self._backup(self.today)
        previous_backup = self._backup(self.today - timedelta(days=1))
        cutoff_backup = self._backup(self.today - timedelta(days=2))
        old_backup = self._backup(self.today - timedelta(days=3))
        active = self._active()
        non_matching = self.log_directory / "notes.txt"
        invalid_date = self.log_directory / "b3-selic-pre-2026-13-40.log"
        directory_match = self.log_directory / "b3-selic-pre-2026-10-10.log"
        for path in (
            today_backup,
            previous_backup,
            cutoff_backup,
            old_backup,
            active,
            non_matching,
            invalid_date,
        ):
            path.write_text("data\n", encoding="utf-8")
        directory_match.mkdir()

        removed = purge_old_logs(
            self.log_directory, retention_days=2, today=self.today
        )

        self.assertEqual(removed, [old_backup])
        self.assertTrue(today_backup.exists())
        self.assertTrue(previous_backup.exists())
        self.assertTrue(cutoff_backup.exists())
        self.assertFalse(old_backup.exists())
        self.assertTrue(active.exists())
        self.assertTrue(non_matching.exists())
        self.assertTrue(invalid_date.exists())
        self.assertTrue(directory_match.exists())

    def test_retention_of_one_keeps_today_and_yesterday(self):
        yesterday = self._backup(self.today - timedelta(days=1))
        two_days_ago = self._backup(self.today - timedelta(days=2))
        yesterday.write_text("data\n", encoding="utf-8")
        two_days_ago.write_text("data\n", encoding="utf-8")
        now = self._backup(self.today)
        now.write_text("data\n", encoding="utf-8")

        purge_old_logs(self.log_directory, retention_days=1, today=self.today)

        self.assertTrue(now.exists())
        self.assertTrue(yesterday.exists())
        self.assertFalse(two_days_ago.exists())

    def test_missing_directory_returns_empty_list(self):
        missing = self.log_directory / "missing"
        self.assertEqual(purge_old_logs(missing, retention_days=7), [])

    def test_huge_retention_keeps_all_backups(self):
        old_backup = self._backup(self.today - timedelta(days=100))
        old_backup.write_text("data\n", encoding="utf-8")
        removed = purge_old_logs(
            self.log_directory, retention_days=10**100, today=self.today
        )
        self.assertEqual(removed, [])
        self.assertTrue(old_backup.exists())

    def test_unlink_errors_are_tolerated(self):
        old_backup = self._backup(self.today - timedelta(days=100))
        old_backup.write_text("data\n", encoding="utf-8")
        with mock.patch.object(Path, "unlink", side_effect=OSError("denied")):
            removed = purge_old_logs(
                self.log_directory, retention_days=2, today=self.today
            )
        self.assertEqual(removed, [])


class DailyNamerTest(unittest.TestCase):
    def test_namer_uses_dated_backup_name(self):
        self.assertEqual(
            _daily_namer("/tmp/b3-selic-pre.log.2026-10-18"),
            "/tmp/b3-selic-pre-2026-10-18.log",
        )


class HandlerTest(LoggingTestBase):
    def test_handler_formats_record_with_local_timestamp(self):
        active = self._active()
        handler = _make_handler(active)
        handler.setFormatter(logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT))
        logger = logging.getLogger("test_timestamp")
        logger.setLevel(logging.INFO)
        logger.propagate = False
        logger.addHandler(handler)
        try:
            logger.info("hello")
            handler.flush()
        finally:
            logger.removeHandler(handler)
            handler.close()
        content = active.read_text(encoding="utf-8")
        self.assertRegex(
            content,
            r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} "
            r"\[INFO\] test_timestamp: hello\n$",
        )

    def test_handler_rotates_to_dated_backup(self):
        active = self._active()
        handler = _make_handler(active)
        handler.setFormatter(logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT))
        logger = logging.getLogger("test_rotation")
        logger.setLevel(logging.INFO)
        logger.propagate = False
        logger.addHandler(handler)
        try:
            logger.info("before")
            handler.flush()
            handler.rolloverAt = datetime.now().timestamp() - 1
            expected_day = datetime.fromtimestamp(
                handler.rolloverAt - handler.interval
            ).date()
            logger.info("after")
            handler.flush()
        finally:
            logger.removeHandler(handler)
            handler.close()
        backup = self._backup(expected_day)
        backup_content = backup.read_text(encoding="utf-8")
        active_content = active.read_text(encoding="utf-8")
        self.assertTrue(backup.exists())
        self.assertTrue(active.exists())
        self.assertIn("test_rotation: before", backup_content)
        self.assertNotIn("after", backup_content)
        self.assertIn("test_rotation: after", active_content)


class ConfigureLoggingTest(LoggingTestBase):
    def test_calls_basic_config_with_shared_format(self):
        with mock.patch(
            "b3_selic_pre.infrastructure.logging_setup.logging.basicConfig"
        ) as basic_config:
            active = configure_logging(self.log_directory, today=self.today)
        self.assertEqual(active, self._active())
        basic_config.assert_called_once()
        kwargs = basic_config.call_args.kwargs
        self.assertEqual(kwargs["level"], logging.INFO)
        self.assertEqual(kwargs["format"], LOG_FORMAT)
        self.assertEqual(kwargs["datefmt"], LOG_DATE_FORMAT)
        self.assertTrue(kwargs["force"])
        self.assertEqual(len(kwargs["handlers"]), 1)
        self.assertIsNone(kwargs["handlers"][0].formatter)
        kwargs["handlers"][0].close()

    def test_rotation_happens_before_retention(self):
        old_day = self.today - timedelta(days=10)
        active = self._active()
        active.write_text("old\n", encoding="utf-8")
        self._set_mtime(active, old_day)
        with mock.patch(
            "b3_selic_pre.infrastructure.logging_setup.logging.basicConfig"
        ) as basic_config:
            configure_logging(
                self.log_directory, retention_days=2, today=self.today
            )
        self.assertFalse(self._backup(old_day).exists())
        self.assertTrue(active.exists())
        basic_config.call_args.kwargs["handlers"][0].close()

    def test_retention_is_skipped_without_retention_days(self):
        old_day = self.today - timedelta(days=10)
        old_backup = self._backup(old_day)
        old_backup.write_text("old\n", encoding="utf-8")
        with mock.patch(
            "b3_selic_pre.infrastructure.logging_setup.logging.basicConfig"
        ) as basic_config:
            configure_logging(self.log_directory, today=self.today)
        self.assertTrue(old_backup.exists())
        basic_config.call_args.kwargs["handlers"][0].close()

    def test_returns_none_when_log_directory_is_a_file(self):
        bad_directory = self.log_directory / "not_a_directory"
        bad_directory.write_text("data\n", encoding="utf-8")
        with mock.patch(
            "b3_selic_pre.infrastructure.logging_setup.logging.basicConfig"
        ) as basic_config:
            self.assertIsNone(configure_logging(bad_directory))
        basic_config.assert_not_called()

    def test_returns_none_when_active_path_is_a_directory(self):
        self._active().mkdir()
        with mock.patch(
            "b3_selic_pre.infrastructure.logging_setup.logging.basicConfig"
        ) as basic_config:
            self.assertIsNone(configure_logging(self.log_directory))
        basic_config.assert_not_called()

    def test_log_dir_uses_cache_base(self):
        with mock.patch(
            "b3_selic_pre.infrastructure.logging_setup.cache_base",
            return_value=Path("/cache"),
        ):
            self.assertEqual(log_dir(), Path("/cache/b3-selic-pre/logs"))


if __name__ == "__main__":
    unittest.main()
