"""Tests for supervised inline-worker startup, stop, and restart behavior."""
import logging
import threading
import unittest

from app.worker_runtime import InlineWorkerRuntime


class InlineWorkerRuntimeTests(unittest.TestCase):
    def test_stop_signals_worker_and_waits_for_exit(self):
        started = threading.Event()
        stopped = threading.Event()

        def target(stop_event):
            started.set()
            stop_event.wait()
            stopped.set()

        runtime = InlineWorkerRuntime(target, restart_delay_seconds=0.01)
        runtime.start()
        self.assertTrue(started.wait(1))
        self.assertTrue(runtime.is_alive)
        self.assertTrue(runtime.stop(timeout_seconds=1))
        self.assertTrue(stopped.is_set())
        self.assertFalse(runtime.is_alive)

    def test_unexpected_worker_exit_is_restarted_without_logging_error_text(self):
        started_after_restart = threading.Event()
        attempts = 0

        def target(stop_event):
            nonlocal attempts
            attempts += 1
            if attempts == 1:
                raise RuntimeError("database password must not be logged")
            started_after_restart.set()
            stop_event.wait()

        runtime = InlineWorkerRuntime(target, restart_delay_seconds=0.01)
        with self.assertLogs("case-worker.runtime", level=logging.ERROR) as captured:
            runtime.start()
            self.assertTrue(started_after_restart.wait(1))
            self.assertTrue(runtime.stop(timeout_seconds=1))
        self.assertGreaterEqual(attempts, 2)
        self.assertTrue(any("RuntimeError" in record for record in captured.output))
        self.assertFalse(any("database password" in record for record in captured.output))

    def test_non_positive_restart_delay_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "restart delay"):
            InlineWorkerRuntime(lambda _stop: None, restart_delay_seconds=0)


if __name__ == "__main__":
    unittest.main()
