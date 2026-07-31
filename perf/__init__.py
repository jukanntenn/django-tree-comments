"""Performance harness library.

The query-count / EXPLAIN / memory modules do not depend on pytest-benchmark and
can be invoked independently; timing collection is driven by pytest-benchmark
(benchmark fixture + extract_timing).
"""
