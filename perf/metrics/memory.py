"""Peak memory collector (tracemalloc).

Measures the peak Python memory allocation during a query execution. Works across all
three backends; standard-library implementation.

Fact basis (measured):
  - tracemalloc.get_traced_memory() returns (current, peak) in bytes; reset to 0 after start().
  - tracemalloc slows queries by roughly 3.3x (measured 0.264s -> 0.867s).
    Memory collection must therefore be decoupled from timing collection (pytest-benchmark) --
    the benchmark's timing data must be collected without tracemalloc enabled, otherwise it is distorted.
    This is exactly why the benchmark driver is designed so that "benchmark is invoked once for timing,
    while the other metrics are collected in separate `with` blocks".
"""

from __future__ import annotations

import tracemalloc
from contextlib import contextmanager
from dataclasses import dataclass


@dataclass
class MemoryStats:
    """Memory collection result."""

    peak_bytes: int = 0
    current_bytes: int = 0

    @property
    def peak_kb(self) -> float:
        return self.peak_bytes / 1024

    def to_dict(self) -> dict:
        return {
            "peak_bytes": self.peak_bytes,
            "peak_kb": round(self.peak_kb, 1),
            "current_bytes": self.current_bytes,
        }


@contextmanager
def measure_memory():
    """Context manager: measures the peak Python memory allocation of the code within its block.

    Usage:
        with measure_memory() as cap:
            list(Comment.objects.cte_for_instance(post))
        stats = cap["stats"]  # MemoryStats

    Note: tracemalloc slows queries by roughly 3.3x, so do not use this function inside the
    pytest-benchmark timing loop -- the timing would be distorted. Collect memory in a separate `with` block.
    """
    # Ensure a clean starting point: if tracing is already on, record the state first; otherwise just start
    was_tracing = tracemalloc.is_tracing()
    if was_tracing:
        tracemalloc.stop()
    tracemalloc.start()

    holder = {"stats": None}
    try:
        yield holder
        current, peak = tracemalloc.get_traced_memory()
        holder["stats"] = MemoryStats(peak_bytes=peak, current_bytes=current)
    finally:
        tracemalloc.stop()
        # Restore the previous tracing state (though the caller usually has not enabled it)
        if was_tracing:
            tracemalloc.start()
