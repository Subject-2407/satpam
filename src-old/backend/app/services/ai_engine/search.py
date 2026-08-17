from __future__ import annotations

import heapq
from collections import deque
from typing import Callable

from app.services.ai_engine.graph import InMemoryGraph, endpoint_key, node_ref_for
from app.services.ai_engine.models import EvidencePath, NodeKey, NodeRef


TargetPredicate = Callable[[dict], bool]
Heuristic = Callable[[NodeKey, InMemoryGraph], float]


def _default_target(node: dict) -> bool:
    if node.get("type") in {"BlacklistEntity", "BlacklistCandidate"}:
        return True
    return int(node.get("riskScore") or 0) >= 60 or node.get("riskLevel") in {"high", "critical"}


def _edge_cost(relationship: dict) -> float:
    # Higher relationship weight means stronger evidence, so investigation cost
    # becomes lower but never zero.
    weight = float(relationship.get("weight") or 1.0)
    return max(0.1, 2.0 - min(weight, 1.9))


def _path_from_parent(
    parents: dict[NodeKey, tuple[NodeKey | None, str | None]],
    end: NodeKey,
    *,
    cost: float = 0.0,
    risk_score: int = 0,
    explanation: str = "",
) -> EvidencePath:
    nodes: list[NodeRef] = []
    relationships: list[str] = []
    current: NodeKey | None = end
    while current is not None:
        nodes.append(node_ref_for(current))
        parent, relationship_id = parents[current]
        if relationship_id:
            relationships.append(relationship_id)
        current = parent
    nodes.reverse()
    relationships.reverse()
    return EvidencePath(
        nodes=nodes,
        relationships=relationships,
        cost=cost,
        risk_score=risk_score,
        explanation=explanation,
    )


def bfs_neighborhood(
    graph: InMemoryGraph,
    start: NodeKey,
    *,
    max_depth: int = 3,
    limit: int = 100,
) -> dict:
    max_depth = max(0, min(max_depth, 5))
    limit = max(1, min(limit, 1000))
    keys = graph.neighborhood_keys(start, max_depth=max_depth, limit=limit)
    return {
        "root": {"type": start[0], "id": start[1]},
        "algorithm": "BFS",
        "maxDepth": max_depth,
        "nodeCount": len(keys),
        **graph.subgraph(keys),
    }


def bfs_evidence_path(
    graph: InMemoryGraph,
    start: NodeKey,
    *,
    target_predicate: TargetPredicate | None = None,
    max_depth: int = 3,
    limit: int = 500,
) -> EvidencePath | None:
    if start not in graph.nodes:
        return None
    predicate = target_predicate or _default_target
    max_depth = max(0, min(max_depth, 5))
    parents: dict[NodeKey, tuple[NodeKey | None, str | None]] = {start: (None, None)}
    depth_by_key: dict[NodeKey, int] = {start: 0}
    queue: deque[NodeKey] = deque([start])
    visited_count = 0

    while queue and visited_count < limit:
        current = queue.popleft()
        visited_count += 1
        node = graph.get_node(current)
        if current != start and node and predicate(node):
            return _path_from_parent(
                parents,
                current,
                cost=float(depth_by_key[current]),
                risk_score=int(node.get("riskScore") or 0),
                explanation="BFS menemukan jalur evidence terdekat ke entitas berisiko.",
            )
        if depth_by_key[current] >= max_depth:
            continue
        for neighbor, rel_id in graph.neighbor_keys(current):
            if neighbor in parents or neighbor not in graph.nodes:
                continue
            parents[neighbor] = (current, rel_id)
            depth_by_key[neighbor] = depth_by_key[current] + 1
            queue.append(neighbor)
    return None


def uniform_cost_search(
    graph: InMemoryGraph,
    start: NodeKey,
    *,
    target_predicate: TargetPredicate | None = None,
    max_depth: int = 5,
    limit: int = 1000,
) -> EvidencePath | None:
    if start not in graph.nodes:
        return None
    predicate = target_predicate or _default_target
    parents: dict[NodeKey, tuple[NodeKey | None, str | None]] = {start: (None, None)}
    depth_by_key: dict[NodeKey, int] = {start: 0}
    best_cost: dict[NodeKey, float] = {start: 0.0}
    heap: list[tuple[float, NodeKey]] = [(0.0, start)]
    visited_count = 0

    while heap and visited_count < limit:
        cost, current = heapq.heappop(heap)
        visited_count += 1
        if cost > best_cost.get(current, float("inf")):
            continue
        node = graph.get_node(current)
        if current != start and node and predicate(node):
            return _path_from_parent(
                parents,
                current,
                cost=cost,
                risk_score=int(node.get("riskScore") or 0),
                explanation="UCS memilih jalur dengan cost investigasi terendah.",
            )
        if depth_by_key[current] >= max_depth:
            continue
        for neighbor, rel_id in graph.neighbor_keys(current):
            relationship = graph.get_relationship(rel_id)
            if not relationship or neighbor not in graph.nodes:
                continue
            next_cost = cost + _edge_cost(relationship)
            if next_cost < best_cost.get(neighbor, float("inf")):
                best_cost[neighbor] = next_cost
                depth_by_key[neighbor] = depth_by_key[current] + 1
                parents[neighbor] = (current, rel_id)
                heapq.heappush(heap, (next_cost, neighbor))
    return None


def bidirectional_search(
    graph: InMemoryGraph,
    start: NodeKey,
    targets: set[NodeKey],
    *,
    max_depth: int = 5,
    limit: int = 1000,
) -> EvidencePath | None:
    if start not in graph.nodes or not targets:
        return None

    forward_parent: dict[NodeKey, tuple[NodeKey | None, str | None]] = {start: (None, None)}
    backward_parent: dict[NodeKey, tuple[NodeKey | None, str | None]] = {
        target: (None, None) for target in targets if target in graph.nodes
    }
    forward_queue: deque[tuple[NodeKey, int]] = deque([(start, 0)])
    backward_queue: deque[tuple[NodeKey, int]] = deque((target, 0) for target in backward_parent)
    visited_count = 0

    while forward_queue and backward_queue and visited_count < limit:
        current, depth = forward_queue.popleft()
        visited_count += 1
        if current in backward_parent:
            return _join_bidirectional_paths(current, forward_parent, backward_parent, graph)
        if depth < max_depth:
            for neighbor, rel_id in graph.neighbor_keys(current):
                if neighbor not in forward_parent:
                    forward_parent[neighbor] = (current, rel_id)
                    forward_queue.append((neighbor, depth + 1))

        current, depth = backward_queue.popleft()
        if current in forward_parent:
            return _join_bidirectional_paths(current, forward_parent, backward_parent, graph)
        if depth < max_depth:
            for neighbor, rel_id in graph.neighbor_keys(current):
                if neighbor not in backward_parent:
                    backward_parent[neighbor] = (current, rel_id)
                    backward_queue.append((neighbor, depth + 1))
    return None


def _join_bidirectional_paths(
    meeting: NodeKey,
    forward_parent: dict[NodeKey, tuple[NodeKey | None, str | None]],
    backward_parent: dict[NodeKey, tuple[NodeKey | None, str | None]],
    graph: InMemoryGraph,
) -> EvidencePath:
    left = _path_from_parent(forward_parent, meeting)
    right_nodes: list[NodeRef] = []
    right_relationships: list[str] = []
    current = meeting
    while True:
        parent, rel_id = backward_parent[current]
        if parent is None:
            break
        right_nodes.append(node_ref_for(parent))
        if rel_id:
            right_relationships.append(rel_id)
        current = parent
    nodes = left.nodes + right_nodes
    relationships = left.relationships + right_relationships
    risk_score = max(
        int((graph.get_node((node.type, node.id)) or {}).get("riskScore") or 0)
        for node in nodes
    )
    return EvidencePath(
        nodes=nodes,
        relationships=relationships,
        cost=float(len(relationships)),
        risk_score=risk_score,
        explanation="Bi-Directional Search menemukan titik temu dengan entitas target.",
    )


def default_risk_heuristic(key: NodeKey, graph: InMemoryGraph) -> float:
    node = graph.get_node(key) or {}
    risk_score = int(node.get("riskScore") or 0)
    return max(0.0, 1.0 - (risk_score / 100))


def a_star_search(
    graph: InMemoryGraph,
    start: NodeKey,
    *,
    target_predicate: TargetPredicate | None = None,
    heuristic: Heuristic | None = None,
    max_depth: int = 5,
    limit: int = 1000,
) -> EvidencePath | None:
    if start not in graph.nodes:
        return None
    predicate = target_predicate or _default_target
    h = heuristic or default_risk_heuristic
    parents: dict[NodeKey, tuple[NodeKey | None, str | None]] = {start: (None, None)}
    depth_by_key: dict[NodeKey, int] = {start: 0}
    g_cost: dict[NodeKey, float] = {start: 0.0}
    heap: list[tuple[float, NodeKey]] = [(h(start, graph), start)]
    visited_count = 0

    while heap and visited_count < limit:
        _, current = heapq.heappop(heap)
        visited_count += 1
        node = graph.get_node(current)
        if current != start and node and predicate(node):
            return _path_from_parent(
                parents,
                current,
                cost=g_cost[current],
                risk_score=int(node.get("riskScore") or 0),
                explanation=(
                    "A* memakai cost investigasi ditambah heuristic risiko; "
                    "jalur berisiko tinggi diberi prioritas eksplorasi."
                ),
            )
        if depth_by_key[current] >= max_depth:
            continue
        for neighbor, rel_id in graph.neighbor_keys(current):
            relationship = graph.get_relationship(rel_id)
            if not relationship or neighbor not in graph.nodes:
                continue
            tentative = g_cost[current] + _edge_cost(relationship)
            if tentative < g_cost.get(neighbor, float("inf")):
                g_cost[neighbor] = tentative
                depth_by_key[neighbor] = depth_by_key[current] + 1
                parents[neighbor] = (current, rel_id)
                heapq.heappush(heap, (tentative + h(neighbor, graph), neighbor))
    return None


def path_relationship_endpoints(graph: InMemoryGraph, path: EvidencePath) -> list[tuple[NodeKey, NodeKey]]:
    endpoints: list[tuple[NodeKey, NodeKey]] = []
    for rel_id in path.relationships:
        relationship = graph.get_relationship(rel_id)
        if relationship:
            endpoints.append((endpoint_key(relationship["from"]), endpoint_key(relationship["to"])))
    return endpoints

