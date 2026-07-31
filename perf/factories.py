"""Parameterized comment-tree data generator.

Generates comment trees of different shapes/scales for performance benchmarks.
Key design points (all verified by measurement/source code):

- Required fields content_type/object_pk/site/comment/submit_date must be set explicitly;
  in particular submit_date -- bulk_create does not call Model.save(), and the
  auto-population logic for submit_date lives in models.py:save(), so a bare
  bulk_create would trigger a NOT NULL constraint failure.
- PK backfill differs by backend:
    * SQLite / PostgreSQL -- bulk_create backfills PKs (Django ORM support);
    * MySQL 8.0 (not MariaDB) -- bulk_create does not backfill PKs (source:
      db/backends/mysql/features.py: can_return_columns_from_insert is true only for MariaDB).
  Persistence therefore splits into two paths by connection.vendor: MySQL falls back
  to one-by-one save(), the others use batched bulk_create.
- Only visible nodes are generated (is_public=True, is_removed=False).
- A fixed random.Random(seed) makes the topology reproducible.

Four tree shapes:
    chain     -- deep single chain, fanout=1, stresses the recursion-depth upper bound
    balanced  -- balanced depth and width, fanout~1.3, closest to real discussion forums,
                 the core target scenario
    wide      -- wide shallow tree, depth<=3, ~100 children per root, stresses large
                 result sets from a single-level JOIN
    forest    -- multi-root forest, roots>=50, stresses multi-root sorting and parallel recursion
"""

from __future__ import annotations

import random
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.db import connection
from django.utils import timezone

from tree_comments.models import Comment

User = get_user_model()

# Batch size for bulk_create. The per-batch upper limit for batched INSERTs on SQLite/PG.
# 500 is an empirical value: a trade-off between memory footprint and INSERT round trips.
BATCH_SIZE = 500

# Comment.comment is a TextField(max_length=COMMENT_MAX_LENGTH=3000).
# A fixed short text is used to keep data size from becoming a confounding variable
# (we are measuring query performance, not I/O volume).
COMMENT_TEXT = "perf benchmark comment"


def _build_topology(shape: str, depth: int, fanout: float, total: int, seed: int) -> list[tuple[int, int | None]]:
    """Build a tree topology (pure algorithm, does not touch the database).

    Returns [(node_id, parent_node_id), ...], with node_id incrementing from 0.
    A parent_node_id of None indicates a root node. The result guarantees:
      - the total number of nodes == total
      - the maximum nesting depth is bounded by depth (except for chain, where depth equals the chain length = total)
    """
    rng = random.Random(seed)
    nodes: list[tuple[int, int | None]] = []
    # Queue of "active" nodes to expand: (node_id, current_depth); FIFO ensures breadth-first.
    active: list[tuple[int, int]] = []

    if shape == "chain":
        # Deep single chain: 0->1->2->...->(total-1), depth=total.
        for i in range(total):
            parent = i - 1 if i > 0 else None
            nodes.append((i, parent))
        return nodes

    # Non-chain shapes: breadth-first expansion until total nodes are filled.
    # First create the root node.
    nodes.append((0, None))
    active.append((0, 0))
    next_id = 1

    if shape == "wide":
        # Wide shallow tree: strictly control depth (default <=3), each node spawns as many
        # children as possible (fanout~100). Fill each level breadth-first; stop when depth
        # or total is reached.
        while next_id < total and active:
            parent_id, parent_depth = active.pop(0)
            if parent_depth >= depth:
                continue  # Exceeded depth limit; this node has no more children
            # Wide tree: each parent spawns fanout children, but no more than total
            n_children = min(int(fanout), total - next_id)
            for _ in range(n_children):
                nodes.append((next_id, parent_id))
                active.append((next_id, parent_depth + 1))
                next_id += 1
        return nodes

    if shape in ("balanced", "forest"):
        # balanced: each node's child count follows a random distribution with mean ~fanout,
        # so the tree has both depth and width.
        # forest: a fixed number of roots (50); each root then expands a subtree in balanced fashion.
        #   The plan requires roots>=50; fixing 50 rather than growing with total keeps the
        #   "multi-root" semantics stable, and each root's subtree growing with total is what
        #   truly stresses "multi-root sorting + parallel recursion".
        if shape == "forest":
            n_roots = min(50, total)  # Fixed 50 roots; when total<50 each node becomes its own root
        else:
            n_roots = 1

        nodes = []
        active = []
        next_id = 0
        for _ in range(n_roots):
            nodes.append((next_id, None))
            active.append((next_id, 0))
            next_id += 1

        # Breadth-first expansion; random sampling decides each node's child count
        while next_id < total:
            if not active:
                # All active nodes hit the depth limit but total is not yet filled.
                # Break the depth limit and keep filling: reactivate from the already-generated
                # non-root nodes. This guarantees node count == total (data volume is the
                # benchmark's core control variable).
                if len(nodes) > n_roots:
                    # Reactivate the last 1/4 of nodes and give them children (breaking depth)
                    reactivate_from = max(n_roots, len(nodes) * 3 // 4)
                    for nid in range(reactivate_from, len(nodes)):
                        active.append((nid, depth))  # Marked as already at depth; below will +1 and continue
                else:
                    break  # Cannot expand further
            if not active:
                break
            parent_id, parent_depth = active.pop(0)
            # Child-count sampling: Poisson-like approximation, mean ~fanout.
            # Using rng.random() against the cumulative distribution, so that with fanout=1.3
            # most nodes get 1-2 children.
            r = rng.random()
            # Simplified Poisson: P(k) weights; the probability of k children decreases as k grows
            if r < 0.3:
                n_children = 0
            elif r < 0.6:
                n_children = 1
            elif r < 0.85:
                n_children = 2
            else:
                n_children = 3
            # Mean correction: raise the upper bound when fanout>2
            if fanout > 2:
                n_children = min(int(fanout) + rng.randint(0, 2), total - next_id)
            n_children = max(0, min(n_children, total - next_id))
            # balanced shape: ensure at least 1 child until 90% filled, to avoid insufficient depth.
            if shape == "balanced" and next_id < total * 0.9 and n_children == 0:
                n_children = 1
            for _ in range(n_children):
                nodes.append((next_id, parent_id))
                active.append((next_id, parent_depth + 1))
                next_id += 1
        return nodes

    raise ValueError(f"unknown shape: {shape!r} (expected chain/balanced/wide/forest)")


def _persist(
    target,
    content_type: ContentType,
    site: Site,
    user,
    object_pk: str,
    topology: list[tuple[int, int | None]],
    base_time,
):
    """Persist the topology as Comment rows.

    Splits into two paths by connection.vendor:
      - sqlite/postgresql: batched bulk_create; after the parent batch backfills PKs, build the children.
      - mysql: one-by-one save() (bulk_create does not backfill PKs; verified from source).

    Returns the list of created Comment objects (in node_id order; index is the node_id).
    """
    vendor = connection.vendor
    # node_id -> Comment object
    created: list[Comment | None] = [None] * len(topology)

    def make_comment(node_id: int, parent_obj: Comment | None, ordinal: int) -> Comment:
        # submit_date must be set explicitly: bulk_create does not call save() (constraint failure verified).
        # base_time + ordinal ensures strict monotonicity, avoiding unstable sorting when submit_date ties.
        return Comment(
            content_type=content_type,
            object_pk=object_pk,
            site=site,
            user=user,
            user_name=user.username if user else "anonymous",
            comment=COMMENT_TEXT,
            submit_date=base_time + timedelta(seconds=ordinal),
            parent=parent_obj,
            is_public=True,
            is_removed=False,
        )

    if vendor in ("sqlite", "postgresql"):
        # Batch in topology order: within one batch, no child may depend on a parent in the same batch.
        # Since node_id increases breadth-first (the parent always appears before the child),
        # a naive split would put the child in the batch after the parent, with the parent's PK
        # already backfilled -- safe.
        # But if a batch contains both parent and child, the parent's PK is not yet backfilled and
        # the child's parent dangles --
        # therefore batch by "level": first persist all roots, get their PKs, then persist depth-1 nodes, ...
        # A more robust approach: batch in node_id order; after each batch the PKs are backfilled,
        # and children in the next batch reference the backfilled parent PKs of the previous batch.
        # Must ensure no parent-child dependency within a batch.
        # Breadth-first order naturally satisfies "parent first"; splitting by BATCH_SIZE works,
        # but we must prevent the parent landing at the tail of the child's batch with the child at the head.
        # Since parent id < child id, within the same batch the parent always appears before the child --
        # after the parent's bulk_create backfills its PK, when the child in the same batch references
        # the parent object, Django bulk_create would raise "unsaved related object".
        # So we must strictly follow "process the parent batch before the children", i.e. batch by level.
        # Implementation: split the topology into "safely bulk-create-able" batches --
        # every node's parent within a batch must already be persisted in an earlier batch.
        i = 0
        ordinal = 0
        while i < len(topology):
            # Current batch: starting at i, collect a batch requiring the parent already be in created
            batch = []
            batch_start = i
            while i < len(topology) and len(batch) < BATCH_SIZE:
                node_id, parent_id = topology[i]
                parent_obj = created[parent_id] if parent_id is not None else None
                # Parent must already be persisted (parent_id < node_id is guaranteed by breadth-first)
                if parent_id is not None and created[parent_id] is None:
                    break  # Parent not yet persisted; end this batch here
                c = make_comment(node_id, parent_obj, ordinal)
                ordinal += 1
                batch.append((i, node_id, c))
                i += 1
            if not batch:
                # Edge case: nothing to process; force progress to avoid an infinite loop
                i = batch_start + 1
                continue
            objs = [item[2] for item in batch]
            Comment.objects.bulk_create(objs)
            # bulk_create backfills PKs onto objs on sqlite/pg
            for idx, node_id, c in batch:
                created[idx] = c
    else:
        # mysql (and any backend that does not backfill PKs via bulk_create): one-by-one save().
        ordinal = 0
        for idx, (node_id, parent_id) in enumerate(topology):
            parent_obj = created[parent_id] if parent_id is not None else None
            c = make_comment(node_id, parent_obj, ordinal)
            ordinal += 1
            c.save()
            created[idx] = c

    return [c for c in created if c is not None]


def build_comment_tree(
    target,
    *,
    shape: str,
    depth: int,
    fanout: float,
    total: int,
    seed: int = 42,
):
    """Generate and persist a comment tree.

    Args:
        target:     the object the comments attach to (e.g. a Post instance); its content_type + pk are used.
        shape:      "chain" | "balanced" | "wide" | "forest"
        depth:      maximum nesting depth (ignored for the chain shape, where chain length = total)
        fanout:     target branching factor (hard upper bound on children per root for the wide shape)
        total:      total node count
        seed:       random seed (reproducible)

    Returns: (target, the actual number of comments generated)
    """
    content_type = ContentType.objects.get_for_model(target)
    site = Site.objects.get_current()
    # Reuse an existing user to avoid creating a new user per tree (user is not the measurement focus).
    user = User.objects.first()
    object_pk = str(target.pk)

    topology = _build_topology(shape, depth, fanout, total, seed)
    base_time = timezone.now()

    created = _persist(target, content_type, site, user, object_pk, topology, base_time)
    return target, len(created)
