"""Temporary diagnostic instrumentation for measuring login/logout/resume-import
latency (see the timing investigation task). Not permanent production logging —
safe to delete once the investigation is done, unless kept on purpose."""

import logging
import pathlib
import time
from contextlib import contextmanager, nullcontext

# Handlers are attached directly to this logger (propagate=False) rather than
# relying on root/basicConfig, so timing output doesn't depend on how the host
# process (e.g. uvicorn --reload, which configures its own loggers) wires up
# stdout/stderr — it always lands in timing_debug.log next to backend/.
_LOG_FILE = pathlib.Path(__file__).resolve().parents[2] / "timing_debug.log"

logger = logging.getLogger("app.timing")
logger.setLevel(logging.INFO)
logger.propagate = False
if not logger.handlers:
    _formatter = logging.Formatter("%(asctime)s %(message)s")
    for _handler in (logging.StreamHandler(), logging.FileHandler(_LOG_FILE)):
        _handler.setFormatter(_formatter)
        logger.addHandler(_handler)


class RequestTimer:
    """Tracks total wall time for one request and logs each named step as it
    completes, plus a final total when `finish()` is called."""

    def __init__(self, endpoint: str):
        self.endpoint = endpoint
        self._start = time.perf_counter()

    @contextmanager
    def step(self, name: str):
        step_start = time.perf_counter()
        try:
            yield
        finally:
            self._log(name, time.perf_counter() - step_start)

    def finish(self) -> None:
        self._log("total", time.perf_counter() - self._start)

    def _log(self, step_name: str, duration_s: float) -> None:
        logger.info(
            "[TIMING] endpoint=%s step=%s duration_ms=%.1f",
            self.endpoint, step_name, duration_s * 1000,
        )


def step(timer: "RequestTimer | None", name: str):
    """Wraps timer.step(name); no-ops when no timer is passed, so instrumented
    service functions stay callable without one (e.g. from unit tests)."""
    if timer is None:
        return nullcontext()
    return timer.step(name)
