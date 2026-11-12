"""Lifecycle management for an optional worker hosted inside the API process."""
from __future__ import annotations

import logging
from threading import Event, Thread
from typing import Callable


log = logging.getLogger("case-worker.runtime")
WorkerTarget = Callable[[Event], None]


class InlineWorkerRuntime:
    """Run one durable queue worker in a supervised, stoppable daemon thread.

    This mode is intended for single-instance hosts that offer a free web
    service but no free background-worker service. The queue itself remains in
    PostgreSQL, so interrupted jobs can be reclaimed after their stale lease.
    """

    def __init__(self, target: WorkerTarget, restart_delay_seconds: float = 5.0):
        if restart_delay_seconds <= 0:
            raise ValueError("Worker restart delay must be positive")
        self._target = target
        self._restart_delay_seconds = restart_delay_seconds
        self._stop_event = Event()
        self._thread: Thread | None = None

    @property
    def is_alive(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self) -> None:
        if self.is_alive:
            return
        self._stop_event.clear()
        self._thread = Thread(
            target=self._run,
            name="rsiacdp-inline-worker",
            daemon=True,
        )
        self._thread.start()

    def _run(self) -> None:
        retry_delay = self._restart_delay_seconds
        while not self._stop_event.is_set():
            try:
                self._target(self._stop_event)
                if self._stop_event.is_set():
                    return
                log.error("Inline worker exited unexpectedly; it will be restarted")
            except Exception as exc:
                # Exception text and tracebacks can include connection URLs,
                # private object paths, or submitted material.
                log.error("Inline worker stopped unexpectedly (%s); it will be restarted", type(exc).__name__)
            if self._stop_event.wait(retry_delay):
                return
            retry_delay = min(retry_delay * 2, 60.0)

    def stop(self, timeout_seconds: float = 15.0) -> bool:
        """Ask the loop to stop and wait briefly for an in-flight task to finish."""
        self._stop_event.set()
        thread = self._thread
        if thread is None:
            return True
        thread.join(timeout=max(0.0, timeout_seconds))
        if thread.is_alive():
            log.warning("Inline worker did not stop before the shutdown timeout")
            return False
        return True
