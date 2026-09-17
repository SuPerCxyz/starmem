"""Small process-local metrics snapshot without adding an observability dependency."""

from __future__ import annotations

from collections import Counter
from threading import Lock

_counts: Counter[str] = Counter()
_latency_totals: Counter[str] = Counter()
_latency_samples: Counter[str] = Counter()
_lock = Lock()


def observe(name: str, *, latency_ms: int | float | None = None) -> None:
    with _lock:
        _counts[name] += 1
        if latency_ms is not None:
            _latency_totals[name] += int(latency_ms)
            _latency_samples[name] += 1


def snapshot() -> dict[str, dict[str, float | int]]:
    with _lock:
        names = set(_counts) | set(_latency_samples)
        return {
            name: {
                "count": _counts.get(name, 0),
                "latency_ms_total": _latency_totals.get(name, 0),
                "latency_ms_avg": round(_latency_totals.get(name, 0) / _latency_samples[name], 2)
                if _latency_samples.get(name)
                else 0,
            }
            for name in sorted(names)
        }
