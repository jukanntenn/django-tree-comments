import random

from .sentences import SENTENCES

_THEME_BY_TOPOLOGY = {
    "wide_shallow": "announcement",
    "flat_replies": "ama",
    "wide_deep": "technical",
    "deep_chain": "debate",
}


def build_topology(topology, seed):
    """Return a list of comment-data dicts ready for persistence.

    Each dict has keys:
        parent_index: int | None   # index into the returned list of the parent
                                   # (None for roots); child must appear AFTER parent
        body: str                   # comment text (sourced from the theme pool)
        is_anon: bool               # True => use anonymous name/email
        user_index: int | None      # index into the precreated users list (None if anon)
        submit_offset: float        # seconds AFTER the post's base time

    The list is ordered parent-before-child so callers can persist in order
    and remap parent_index -> real pk via a position array.

    topology must be one of: wide_shallow, flat_replies, wide_deep, empty, deep_chain.
    """
    rng = random.Random(seed)
    if topology == "empty":
        return []
    theme = _THEME_BY_TOPOLOGY[topology]
    pool = SENTENCES[theme]

    nodes = []

    def add(parent_index, body, rng, anon_chance, user_count, base_offset, window):
        is_anon = rng.random() < anon_chance
        user_index = None if is_anon else rng.randrange(user_count)
        offset = base_offset + rng.uniform(0, window)
        nodes.append(
            {
                "parent_index": parent_index,
                "body": body,
                "is_anon": is_anon,
                "user_index": user_index,
                "submit_offset": offset,
            }
        )
        return len(nodes) - 1

    if topology == "wide_shallow":
        user_count = 15
        for r in range(60):
            root_idx = add(None, rng.choice(pool["roots"]), rng, 0.3, user_count, r * 60, 30)
            n_children = rng.randint(1, 3)
            for c in range(n_children):
                add(root_idx, rng.choice(pool["replies"]), rng, 0.3, user_count, root_idx * 60 + 30, 30)

    elif topology == "flat_replies":
        user_count = 15
        for r in range(10):
            root_idx = add(None, rng.choice(pool["roots"]), rng, 0.2, user_count, r * 600, 60)
            n_children = rng.randint(14, 16)
            for c in range(n_children):
                add(root_idx, rng.choice(pool["replies"]), rng, 0.2, user_count, root_idx * 600 + 60, 600)

    elif topology == "wide_deep":
        user_count = 15
        max_depth = 7
        total_cap = 200

        def grow(parent_index, depth, base_offset):
            if depth >= max_depth or len(nodes) >= total_cap:
                return
            roll = rng.random()
            if roll < 0.1:
                return
            n_children = 1 if roll < 0.7 else 2
            for _ in range(n_children):
                if len(nodes) >= total_cap:
                    return
                pool_key = "replies"
                child_idx = add(parent_index, rng.choice(pool[pool_key]), rng, 0.3, user_count, base_offset, 30)
                grow(child_idx, depth + 1, nodes[child_idx]["submit_offset"] + 1)

        for r in range(40):
            if len(nodes) >= total_cap:
                break
            root_idx = add(None, rng.choice(pool["roots"]), rng, 0.3, user_count, r * 100, 30)
            grow(root_idx, 1, nodes[root_idx]["submit_offset"] + 1)

    elif topology == "deep_chain":
        user_count = 15
        depth = rng.randint(9, 11)
        root_idx = add(None, rng.choice(pool["roots"]), rng, 0.0, user_count, 0, 30)
        parent = root_idx
        for d in range(depth):
            pool_key = "followups" if d % 2 == 0 else "replies"
            base = nodes[parent]["submit_offset"] + 60
            parent = add(parent, rng.choice(pool[pool_key]), rng, 0.2, user_count, base, 60)

    else:
        raise ValueError(f"unknown topology: {topology}")

    return nodes
