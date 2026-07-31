"""Benchmark scenario matrix definition.

A scenario = a (shape, scale, backend) triple, accompanied by data-generation
parameters (depth/fanout/total).

Scenarios fall into two categories:
  - Category A core matrix: balanced / forest x three backends x three scales --
    closest to real workloads, run on every invocation.
  - Category B extreme specialties: chain (stresses the recursion-depth upper bound) /
    wide (stresses large single-level result sets).

Constraints (fact-based):
  - MySQL cte_max_recursion_depth=1000 (measured + source sys_vars.cc:1131-1137);
    for the chain shape depth = total-1, and exceeding 1000 raises error (3636).
    Therefore chain on MySQL clips total to min(total, 1000).
  - chain has no hard recursion-depth limit on SQLite/PostgreSQL and can run 1k/5k/10k.
"""

from __future__ import annotations

from dataclasses import dataclass

# MySQL recursive CTE depth limit (perf/docker-compose.yml sets --cte_max_recursion_depth=1000).
# For the chain shape depth = total - 1; MySQL raises an error when this value is exceeded.
# Used to clip chain scenarios.
MYSQL_RECURSION_LIMIT = 1000

# Scale tiers (total node counts).
SCALES = (1_000, 5_000, 10_000)

# Database backends.
BACKENDS = ("sqlite", "postgres", "mysql")


@dataclass(frozen=True)
class Scenario:
    """A single benchmark scenario.

    shape:   "chain" | "balanced" | "wide" | "forest"
    scale:   target total node count
    backend: database backend
    depth:   maximum tree depth (for the chain shape = scale-1)
    fanout:  target branching factor
    total:   actually generated node count (may be < scale after MySQL chain clipping)
    kind:    "A" (core matrix) or "B" (extreme specialty), used for grouping and filtering
    """

    shape: str
    scale: int
    backend: str
    depth: int
    fanout: float
    total: int
    kind: str = "A"

    @property
    def id(self) -> str:
        """Unique scenario identifier, used in reports and file names."""
        return f"{self.shape}_{self.scale}_{self.backend}"

    def __str__(self) -> str:
        return self.id


def _shape_params(shape: str, scale: int) -> dict:
    """depth/fanout parameters for each shape at a given scale."""
    if shape == "chain":
        # Chain depth = node count - 1 (fanout=1)
        return {"depth": scale - 1, "fanout": 1}
    if shape == "balanced":
        # Depth cap 32, fanout 1.3 (the plan's core target scenario)
        return {"depth": 32, "fanout": 1.3}
    if shape == "wide":
        # Depth <=3, at most 100 children per root (stresses large single-level result sets)
        return {"depth": 3, "fanout": 100}
    if shape == "forest":
        # Fixed 50 roots, fanout 1.5 (stresses multi-root sorting and parallel recursion)
        return {"depth": 10, "fanout": 1.5}
    raise ValueError(f"unknown shape: {shape!r}")


def _build_scenarios() -> list[Scenario]:
    """Build the complete scenario matrix."""
    scenarios: list[Scenario] = []

    # Category A core matrix: balanced + forest, all three backends, all three scales.
    for shape in ("balanced", "forest"):
        params = _shape_params(shape, SCALES[0])  # depth/fanout are independent of scale (except for chain)
        for scale in SCALES:
            for backend in BACKENDS:
                p = _shape_params(shape, scale)
                scenarios.append(
                    Scenario(
                        shape=shape,
                        scale=scale,
                        backend=backend,
                        depth=p["depth"],
                        fanout=p["fanout"],
                        total=scale,
                        kind="A",
                    )
                )

    # Category B extreme specialties: chain + wide.
    # chain: all three backends, clipped on MySQL.
    for scale in SCALES:
        for backend in BACKENDS:
            total = scale
            # MySQL chain clipping: measured with cte_max_recursion_depth=1000, the chain
            # node-count upper bound is 1000 (total<=1000 passes, >=1001 raises error 3636).
            # Source basic_row_iterators.cc:461: ++count > limit raises the error.
            if backend == "mysql" and total > MYSQL_RECURSION_LIMIT:
                total = MYSQL_RECURSION_LIMIT
            depth = total - 1  # chain shape: chain depth = node count - 1
            scenarios.append(
                Scenario(
                    shape="chain",
                    scale=scale,
                    backend=backend,
                    depth=depth,
                    fanout=1,
                    total=total,
                    kind="B",
                )
            )

    # wide: run only at 10k (per plan: small scales cannot expose the cost of large single-level
    # result sets), all three backends.
    for backend in BACKENDS:
        params = _shape_params("wide", 10_000)
        scenarios.append(
            Scenario(
                shape="wide",
                scale=10_000,
                backend=backend,
                depth=params["depth"],
                fanout=params["fanout"],
                total=10_000,
                kind="B",
            )
        )

    return scenarios


# The complete scenario list (module-level constant, imported by the benchmark driver).
ALL_SCENARIOS: list[Scenario] = _build_scenarios()


def scenarios_for_backend(backend: str) -> list[Scenario]:
    """Filter scenarios for a given backend."""
    return [s for s in ALL_SCENARIOS if s.backend == backend]


def scenarios_by_kind(kind: str) -> list[Scenario]:
    """Filter scenarios for a given category (A/B)."""
    return [s for s in ALL_SCENARIOS if s.kind == kind]
