def build_nested(comment_list):
    """Convert a flat list of CTE results into a nested tree.

    Each input comment must expose id and parent_id attributes.
    Returns a list of root nodes, each shaped like {"comment": <original>, "children": [...]},
    with children ordered by their appearance in comment_list.
    Pure Python, O(n), with no extra queries.
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
