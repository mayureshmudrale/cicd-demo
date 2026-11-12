"""Every fault-injection mode the canary track can run, in one place.

Importing this module has no side effects. Routes call `maybe_inject()` near
the top of the handler (and, for the listing endpoint, `simulate_n_plus_one`
afterward); the active mode comes from `config.settings.fault_mode`, which
only the canary's Helm values ever set to something other than "none" — the
stable track always runs clean.
"""
import random
import time

from fastapi import HTTPException

from config import settings

_leaked_chunks: list[bytes] = []


def _fault_none() -> None:
    """No-op: the stable track's default."""


def _fault_panic() -> None:
    """Raise an unhandled exception, simulating a crash."""
    raise RuntimeError("simulated panic (FAULT_MODE=panic)")


def _fault_error500() -> None:
    """Return a 500 for a fraction of requests, simulating a broken deploy."""
    if random.random() < settings.fault_rate:
        raise HTTPException(
            status_code=500, detail="simulated error (FAULT_MODE=error500)"
        )


def _fault_slow() -> None:
    """Add latency to a fraction of requests, simulating a degraded dependency."""
    if random.random() < settings.fault_rate:
        time.sleep(settings.fault_latency_ms / 1000)


def _fault_leak() -> None:
    """Leak memory on every request, simulating an unbounded cache/buffer."""
    _leaked_chunks.append(bytes(1_000_000))


def _fault_cpu_burn() -> None:
    """Spin the CPU for a fixed window, simulating a hot loop/regression."""
    deadline = time.monotonic() + settings.fault_cpu_burn_ms / 1000
    while time.monotonic() < deadline:
        pass


_HANDLERS = {
    "none": _fault_none,
    "panic": _fault_panic,
    "error500": _fault_error500,
    "slow": _fault_slow,
    "leak": _fault_leak,
    "cpu_burn": _fault_cpu_burn,
}


def maybe_inject() -> None:
    """Run the handler named by FAULT_MODE, if any is configured.

    "n_plus_one" is handled separately by `simulate_n_plus_one`, since that
    one needs the DB session rather than just sleeping or raising.
    """
    handler = _HANDLERS.get(settings.fault_mode, _fault_none)
    handler()


def simulate_n_plus_one(db, idea_ids: list[int]) -> None:
    """When FAULT_MODE=n_plus_one, issue one extra query per id.

    Called from the ideas-list route after the real query already ran, so
    it adds the extra round trips without changing the response shape.
    """
    if settings.fault_mode != "n_plus_one":
        return

    from models import Idea  # local import: avoids a models/db import cycle

    for idea_id in idea_ids:
        db.query(Idea).filter(Idea.id == idea_id).first()
