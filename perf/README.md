# Performance Harness

Measures performance and diagnoses bottlenecks for the CTE tree-comment queries of django-tree-comments.

**Core value**: quantifies system behavior into structured metrics and produces reports that an LLM can consume, for AI-assisted bottleneck analysis and optimization decisions. The goal is not to produce faster code, but an honest health-check report.

Supported scope: CTE query performance is observable at the **10k-comment scale, depths up to 32 levels**.

---

## Quick Start

### 1. Start the database containers (only needed for PG/MySQL)

```bash
docker compose -f perf/docker-compose.yml up -d
```

SQLite uses an in-memory database; no container is needed.

### 2. Run the benchmark

```bash
# SQLite (default; no environment variable required)
uv run pytest tests/perf/

# PostgreSQL
TREE_COMMENTS_DB_BACKEND=postgres uv run pytest tests/perf/

# MySQL
TREE_COMMENTS_DB_BACKEND=mysql uv run pytest tests/perf/

# Run only a single scenario (-k matches the scenario id by substring)
TREE_COMMENTS_DB_BACKEND=sqlite uv run pytest tests/perf/ -k "balanced_1000_sqlite"
```

### 3. View the report

Reports are generated automatically under `perf/reports/<git-commit>-<timestamp>/`:

- `report.json` —— full raw data (machine-readable, includes the complete EXPLAIN text)
- `report.md` —— LLM-readable (red flags highlighted + cross-scenario comparison + an empty decision-table skeleton)

### 4. LLM offline analysis

Paste the entire `report.md` to an LLM (or have a tool read it). The report opens with a complete Context block (CTE SQL semantics + red-flag definitions + known characteristics), so the LLM can diagnose without looking at the codebase. Based on the red flags and cross-scenario comparison it pinpoints the bottleneck and proposes optimizations, filling the decision table at the end of the report.

### 5. Performance regression assertions (pytest-benchmark)

Leverage pytest-benchmark's native baseline save-and-compare to detect performance regressions after refactoring/optimization:

```bash
# 1. Establish a baseline (before optimization)
TREE_COMMENTS_DB_BACKEND=sqlite uv run pytest tests/perf/ \
  --benchmark-save=baseline

# 2. Compare after refactoring/optimization (fails if regression exceeds the threshold)
TREE_COMMENTS_DB_BACKEND=sqlite uv run pytest tests/perf/ \
  --benchmark-compare --benchmark-compare-fail=mean:10%
```

Baseline files are archived under `perf/.benchmarks/<machine>/` (gitignored).

---

## Notes

- **A plain `pytest` run does not execute perf**: the benchmark is too slow and is skipped by default. Only an explicit `pytest tests/perf/` runs it.
- **MySQL data generation is slow**: MySQL 8.0 (not MariaDB) `bulk_create` does not backfill PKs (source: `mysql/features.py`: `can_return_columns_from_insert` is only true for MariaDB), so MySQL falls back to one-by-one `save()`. 10k nodes take about 51 seconds, versus 1-2 seconds on the other backends.
- **tracemalloc slows queries by 3.3x**: memory collection is decoupled from timing collection, so the benchmark timing is unaffected.

---

## Scenario Matrix

10 scenarios per backend x 2 queries (`cte_for_instance` / `threaded_for_instance`) = 20 benchmarks per backend.

### Four tree shapes

| Shape | Structure | Benchmarking focus |
|------|------|---------|
| `chain` | Deep single chain (fanout=1) | Upper bound of CTE recursion depth |
| `balanced` | Balanced depth and width (fanout~1.3, depth<=32) | **Core target scenario**, closest to real discussion forums |
| `wide` | Wide shallow tree (depth<=3, fanout~100) | Large result set from a single-level JOIN |
| `forest` | Multi-root forest (fixed 50 roots) | Multi-root sorting and parallel recursion |

### Scale tiers

1k / 5k / 10k nodes.

### Backend constraints

- **MySQL chain is clipped to total<=1000**: `cte_max_recursion_depth=1000` (measured boundary, source `basic_row_iterators.cc:461`); chain depth = total-1, exceeding it raises error `(3636)`.
- SQLite/PostgreSQL have no hard recursion-depth limit.

See `perf/scenarios.py` for the full scenario definitions.

---

## Four Red-Flag Categories

Structured performance signals extracted from the execution plan, ready for an LLM to consume directly:

| Type | Meaning | Trigger criteria |
|------|------|---------|
| `seq_scan_large_table` | Full table scan on a large table | PG: Seq Scan + Actual Rows>1000; MySQL: type=ALL + rows>1000; SQLite: starts with SCAN and no USING |
| `estimation_off` | Severe row-count estimation deviation | PG: \|Plan Rows-Actual Rows\|/Actual Rows>0.5 (deduplicated by NodeType); MySQL/SQLite: not applicable |
| `spilled_to_disk` | Sort/intermediate result spilled to disk | PG: external merge/Disk/Temp Blocks; MySQL: Using filesort; SQLite: USE TEMP B-TREE |
| `recursive_bulk` | Large recursive intermediate result | PG: Recursive Union loops>10 or WorkTable rows>1000; MySQL: Materialize CTE loops/rows; SQLite: presence of RECURSIVE STEP |

Thresholds are tunable at the top of `perf/metrics/redflags.py` (`SEQ_SCAN_MIN_ROWS` / `ESTIMATION_RATIO`, etc.).

---

## Reading the report

### report.md structure

1. **Context block** (top) —— the real CTE SQL + known design characteristics + red-flag definitions. **Must-read before LLM diagnosis**; provides all the context needed to understand the system.
2. **Per-scenario details** —— one section per scenario: parameters -> timing (ms) -> query count -> red flags (highlighted red/yellow) -> PG depth metrics -> memory.
3. **Cross-scenario comparison** —— tables for same-shape scaling growth, cross-backend comparison, and per-scenario red-flag totals.
4. **Empty optimization decision table** —— to be filled in by LLM analysis (bottleneck / current state / hypothesis / expected gain / verification scenario / status).

### Key metrics

- **Timing**: milliseconds (pytest-benchmark warm multi-round measurements, median primary, p95 supplementary).
- **Memory**: KB (tracemalloc Python-object peak; excludes DB-process memory).
- **Buffer hit ratio**: percentage (PG only; computed from Shared Hit/Read Blocks of EXPLAIN BUFFERS).
- **Recursive iterations**: PG only (Actual Loops of the Recursive Union).

---

## SQLite diagnostic limitations

Because CPython does not expose the `sqlite3*` C handle (ctypes memory-offset access causes a segfault, exit code 139), SQLite cannot collect `sqlite3_db_status` cache-hit ratio or spill byte counts.

Still-effective SQLite diagnostics: EXPLAIN QUERY PLAN (SCAN/SEARCH/USE TEMP B-TREE) + three red-flag categories (presence of seq_scan/spilled/recursive) + timing + N+1 detection + memory. Less deep than PG/MySQL, but the core measurements are complete.

---

## Architecture and dependencies

```
perf/
├── factories.py            Data generator (topology + three-DB persistence)
├── scenarios.py            Scenario matrix (shape x scale x backend + constraints)
├── metrics/
│   ├── query_counter.py    Query count + N+1 detection (connection.queries)
│   ├── explain.py          Three-DB EXPLAIN collection (dialect dispatch)
│   ├── redflags.py         Four red-flag extraction
│   ├── memory.py           tracemalloc memory peak
│   └── collector.py        Collection orchestration (combines all metrics + PG extras)
├── reporting/
│   ├── json_reporter.py    report.json (full raw)
│   └── markdown_reporter.py report.md (LLM-readable + decision table)
├── reports/                Archive directory (.gitignore, generated per run)
├── docker-compose.yml      PG 16 + MySQL 8.0 (local; run from repo root with -f perf/)
├── docker/mysql-init.sql   MySQL first-start grants (Django tests need a test_ DB)
└── .benchmarks/            pytest-benchmark baseline archive (.gitignore, --benchmark-save)

tests/perf/
├── conftest.py             Scenario parameterization + data generation + sessionfinish report
├── test_cte_query.py       benchmark cte_for_instance
└── test_threaded_query.py  benchmark threaded_for_instance
```

### Data flow

```
Scenario(shape x scale x backend)
    |
build_comment_tree -> comment tree (bulk_create, or per-row save() on MySQL)
    |
benchmark(queryset)  -> timing (median/p95, warm multi-round)
    | + separate `with` block (tracemalloc slows 3.3x, so kept separate)
capture_queries      -> query count + N+1
explain              -> execution plan (three-DB dialect)
extract_red_flags    -> four red flags
measure_memory       -> peak memory
    |
collect_scenario_metrics -> unified metrics dict
    |
pytest_sessionfinish -> report.json + report.md
    |
LLM offline analysis -> fill decision table -> next-phase optimization
```

---

## Known design characteristics (current state of the system under test, not harness bugs)

These are problems the harness measured; they will be handled in the optimization phase:

1. **parent_id has no index on PG/SQLite** (FK does not auto-create an index); MySQL InnoDB auto-creates one.
2. **No (content_type, object_pk) composite index**; only a single-column object_pk index exists.
3. **The recursive branch does not filter visibility**: when an intermediate node is is_removed, its subtree is still fetched.
4. **Sorting is a flat time order**; the depth annotation is computed but does not participate in sorting.
5. **bulk_create does not call save()**: submit_date is auto-populated in save(), so batch inserts must set it explicitly.

All of these are stated in the Context block of report.md for the LLM to reference during analysis.

---

## Full design document

For the detailed design, source-verified facts, and decision process, see [`docs/plans/2026-07-03-perf-harness-design.md`](../docs/plans/2026-07-03-perf-harness-design.md).
