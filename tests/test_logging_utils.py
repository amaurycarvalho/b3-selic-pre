import logging
import sys
import threading
import unittest
import urllib.error
from unittest import mock

from b3_selic_pre.application.errors import CommunicationError
from b3_selic_pre.presentation.logging_utils import (
    install_exception_hooks,
    install_tk_exception_hook,
    is_communication_error,
    log_exception,
)


def _with_cause(error, cause):
    error.__cause__ = cause
    return error


class CommunicationClassificationTest(unittest.TestCase):
    def test_direct_communication_error(self):
        self.assertTrue(is_communication_error(CommunicationError("boom")))

    def test_non_communication_error(self):
        self.assertFalse(is_communication_error(ValueError("boom")))

    def test_cause_chain(self):
        outer = _with_cause(RuntimeError("wrapper"), CommunicationError("boom"))
        self.assertTrue(is_communication_error(outer))

    def test_context_chain(self):
        outer = RuntimeError("wrapper")
        outer.__context__ = CommunicationError("boom")
        self.assertTrue(is_communication_error(outer))

    def test_cycle_with_communication_error_terminates(self):
        communication = CommunicationError("boom")
        outer = RuntimeError("wrapper")
        communication.__cause__ = outer
        outer.__cause__ = communication
        self.assertTrue(is_communication_error(outer))

    def test_cycle_without_communication_error_terminates(self):
        first = RuntimeError("first")
        second = RuntimeError("second")
        first.__cause__ = second
        second.__cause__ = first
        self.assertFalse(is_communication_error(first))


class LogExceptionTest(unittest.TestCase):
    def test_communication_error_is_single_line(self):
        logger = logging.getLogger("test_log_direct")
        with self.assertLogs(logger, level="ERROR") as captured:
            log_exception(logger, CommunicationError("boom"), "context")
        record = captured.records[0]
        self.assertIsNone(record.exc_info)
        self.assertIn("CommunicationError: boom", record.getMessage())
        self.assertNotIn("\n", record.getMessage())

    def test_communication_cause_reports_network_type(self):
        logger = logging.getLogger("test_log_cause")
        error = _with_cause(
            CommunicationError("offline"),
            urllib.error.URLError("offline"),
        )
        with self.assertLogs(logger, level="ERROR") as captured:
            log_exception(logger, error, "context")
        message = captured.records[0].getMessage()
        self.assertIn("URLError: <urlopen error offline>", message)
        self.assertIsNone(captured.records[0].exc_info)

    def test_communication_message_newlines_are_normalized(self):
        logger = logging.getLogger("test_log_newlines")
        error = _with_cause(
            CommunicationError("offline"),
            urllib.error.URLError("line one\nline two"),
        )
        with self.assertLogs(logger, level="ERROR") as captured:
            log_exception(logger, error, "context")
        message = captured.records[0].getMessage()
        self.assertNotIn("\n", message)
        self.assertIn("line one line two", message)

    def test_non_communication_error_keeps_traceback(self):
        logger = logging.getLogger("test_log_traceback")
        error = ValueError("bad value")
        with self.assertLogs(logger, level="ERROR") as captured:
            log_exception(logger, error, "context")
        record = captured.records[0]
        self.assertIsNotNone(record.exc_info)
        self.assertEqual(record.getMessage(), "context")
        self.assertIn("ValueError: bad value", captured.output[0])

    def test_logged_exception_is_marked(self):
        logger = logging.getLogger("test_log_marker")
        error = ValueError("bad value")
        with self.assertLogs(logger, level="ERROR"):
            log_exception(logger, error, "context")
        self.assertTrue(getattr(error, "_b3_selic_logged", False))


class ExceptionHooksTest(unittest.TestCase):
    def test_sys_hook_logs_and_calls_previous(self):
        logger = logging.getLogger("test_sys_hook")
        error = ValueError("boom")
        with mock.patch.object(sys, "excepthook") as previous, mock.patch.object(
            threading, "excepthook"
        ):
            install_exception_hooks(logger)
            hook = sys.excepthook
            with self.assertLogs(logger, level="ERROR") as captured:
                hook(ValueError, error, error.__traceback__)
        self.assertIsNotNone(captured.records[0].exc_info)
        previous.assert_called_once_with(ValueError, error, error.__traceback__)

    def test_thread_hook_logs_and_calls_previous(self):
        logger = logging.getLogger("test_thread_hook")
        error = ValueError("boom")
        args = mock.Mock(exc_value=error, exc_traceback=error.__traceback__)
        with mock.patch.object(sys, "excepthook"), mock.patch.object(
            threading, "excepthook"
        ) as previous:
            install_exception_hooks(logger)
            hook = threading.excepthook
            with self.assertLogs(logger, level="ERROR") as captured:
                hook(args)
        self.assertIsNotNone(captured.records[0].exc_info)
        previous.assert_called_once_with(args)

    def test_already_logged_exception_is_not_logged_again(self):
        logger = logging.getLogger("test_hook_marker")
        error = ValueError("boom")
        with self.assertLogs(logger, level="ERROR") as captured:
            log_exception(logger, error, "context")
            with mock.patch.object(sys, "excepthook") as previous, mock.patch.object(
                threading, "excepthook"
            ):
                install_exception_hooks(logger)
                sys.excepthook(ValueError, error, error.__traceback__)
        self.assertEqual(len(captured.records), 1)
        previous.assert_called_once_with(ValueError, error, error.__traceback__)

    def test_tk_hook_logs_and_calls_previous(self):
        logger = logging.getLogger("test_tk_hook")
        error = ValueError("boom")
        root = mock.Mock()
        previous = root.report_callback_exception
        install_tk_exception_hook(root, logger)
        hook = root.report_callback_exception
        with self.assertLogs(logger, level="ERROR") as captured:
            hook(ValueError, error, error.__traceback__)
        self.assertIsNotNone(captured.records[0].exc_info)
        previous.assert_called_once_with(ValueError, error, error.__traceback__)

    def test_tk_hook_skips_previous_without_stderr(self):
        logger = logging.getLogger("test_tk_no_stderr")
        error = ValueError("boom")
        root = mock.Mock()
        previous = root.report_callback_exception
        install_tk_exception_hook(root, logger)
        hook = root.report_callback_exception
        with mock.patch.object(sys, "stderr", None):
            with self.assertLogs(logger, level="ERROR"):
                hook(ValueError, error, error.__traceback__)
        previous.assert_not_called()


if __name__ == "__main__":
    unittest.main()
