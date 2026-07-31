def build_nested(comment_list):
    """Convert a flat CTE result list into a nested tree of dicts.

    Each input comment must expose attributes: id, parent_id.
    Output: list of {"comment": <original>, "children": [...]}, root-first,
    children ordered by their position in comment_list (which is already
    submit_date-ordered within a root by the CTE).
    """
    nodes = {}
    roots = []
    for c in comment_list:
        nodes[c.id] = {"comment": c, "children": []}
    for c in comment_list:
        node = nodes[c.id]
        parent_id = getattr(c, "parent_id", None)
        if parent_id and parent_id in nodes:
            nodes[parent_id]["children"].append(node)
        else:
            roots.append(node)
    return roots
