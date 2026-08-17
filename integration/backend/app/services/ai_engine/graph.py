from __future__ import annotations

from collections import defaultdict, deque
from typing import Any, Iterable

from app.services.ai_engine.models import GraphRelationship, NodeKey, NodeRef


def node_key(node_type: str, node_id: str) -> NodeKey:
    return (str(node_type), str(node_id))


def endpoint_key(endpoint: dict[str, Any]) -> NodeKey:
    return node_key(str(endpoint["type"]), str(endpoint["id"]))


class InMemoryGraph:
    """Small graph facade used by the AI engine and tests.

    Relationships are traversed as undirected for evidence discovery because
    analysts usually care that two entities are connected, while the original
    relationship direction is preserved in the edge payload.
    """

    def __init__(
        self,
        nodes: Iterable[dict[str, Any]] | None = None,
        relationships: Iterable[dict[str, Any] | GraphRelationship] | None = None,
    ) -> None:
        self.nodes: dict[NodeKey, dict[str, Any]] = {}
        self.relationships: dict[str, dict[str, Any]] = {}
        self.outgoing: dict[NodeKey, list[str]] = defaultdict(list)
        self.incoming: dict[NodeKey, list[str]] = defaultdict(list)

        for node in nodes or []:
            self.add_node(node)
        for relationship in relationships or []:
            self.add_relationship(relationship)

    @classmethod
    def from_payload(
        cls,
        nodes: Iterable[dict[str, Any]],
        relationships: Iterable[dict[str, Any] | GraphRelationship],
    ) -> "InMemoryGraph":
        return cls(nodes=nodes, relationships=relationships)

    def add_node(self, node: dict[str, Any]) -> None:
        if "type" not in node or "id" not in node:
            raise ValueError("Node must contain type and id.")
        self.nodes[node_key(node["type"], node["id"])] = dict(node)

    def add_relationship(self, relationship: dict[str, Any] | GraphRelationship) -> None:
        payload = relationship.as_dict() if isinstance(relationship, GraphRelationship) else dict(relationship)
        rel_id = str(payload["id"])
        from_key = endpoint_key(payload["from"])
        to_key = endpoint_key(payload["to"])
        self.relationships[rel_id] = payload
        self.outgoing[from_key].append(rel_id)
        self.incoming[to_key].append(rel_id)

    def get_node(self, key: NodeKey) -> dict[str, Any] | None:
        return self.nodes.get(key)

    def get_relationship(self, relationship_id: str) -> dict[str, Any] | None:
        return self.relationships.get(relationship_id)

    def has_node(self, key: NodeKey) -> bool:
        return key in self.nodes

    def incident_relationship_ids(self, key: NodeKey) -> list[str]:
        return list(dict.fromkeys(self.outgoing.get(key, []) + self.incoming.get(key, [])))

    def neighbor_keys(self, key: NodeKey) -> list[tuple[NodeKey, str]]:
        neighbors: list[tuple[NodeKey, str]] = []
        for rel_id in self.incident_relationship_ids(key):
            relationship = self.relationships[rel_id]
            from_key = endpoint_key(relationship["from"])
            to_key = endpoint_key(relationship["to"])
            if from_key == key:
                neighbors.append((to_key, rel_id))
            elif to_key == key:
                neighbors.append((from_key, rel_id))
        return neighbors

    def degree(self, key: NodeKey) -> int:
        return len(self.incident_relationship_ids(key))

    def relationship_between(self, left: NodeKey, right: NodeKey) -> dict[str, Any] | None:
        for rel_id in self.incident_relationship_ids(left):
            relationship = self.relationships[rel_id]
            endpoints = {endpoint_key(relationship["from"]), endpoint_key(relationship["to"])}
            if endpoints == {left, right}:
                return relationship
        return None

    def neighborhood_keys(self, start: NodeKey, max_depth: int = 3, limit: int = 200) -> set[NodeKey]:
        if start not in self.nodes:
            return set()
        visited: set[NodeKey] = {start}
        queue: deque[tuple[NodeKey, int]] = deque([(start, 0)])
        while queue and len(visited) < limit:
            current, depth = queue.popleft()
            if depth >= max_depth:
                continue
            for neighbor, _ in self.neighbor_keys(current):
                if neighbor not in visited and neighbor in self.nodes:
                    visited.add(neighbor)
                    queue.append((neighbor, depth + 1))
                    if len(visited) >= limit:
                        break
        return visited

    def subgraph(self, keys: Iterable[NodeKey]) -> dict[str, list[dict[str, Any]]]:
        key_set = set(keys)
        nodes = [self.nodes[key] for key in key_set if key in self.nodes]
        relationships = [
            relationship
            for relationship in self.relationships.values()
            if endpoint_key(relationship["from"]) in key_set
            and endpoint_key(relationship["to"]) in key_set
        ]
        return {"nodes": nodes, "relationships": relationships}

    def keys_by_type(self, node_type: str) -> list[NodeKey]:
        return [key for key in self.nodes if key[0] == node_type]

    def all_entity_keys(self) -> list[NodeKey]:
        excluded = {
            "AuditLog",
            "BlacklistDecision",
            "BlacklistEntity",
            "Recommendation",
            "RiskAssessment",
            "VerificationCase",
        }
        return [key for key in self.nodes if key[0] not in excluded]

    def as_dict(self) -> dict[str, list[dict[str, Any]]]:
        return {
            "nodes": list(self.nodes.values()),
            "relationships": list(self.relationships.values()),
        }


def flatten_dataset_nodes(nodes_container: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    nodes: list[dict[str, Any]] = []
    for values in nodes_container.values():
        if isinstance(values, list):
            nodes.extend(dict(item) for item in values)
    return nodes


def graph_from_dataset(dataset: dict[str, Any]) -> InMemoryGraph:
    nodes = flatten_dataset_nodes(dataset.get("nodes", {}))
    relationships = dataset.get("relationships", [])
    return InMemoryGraph(nodes=nodes, relationships=relationships)


def node_ref_for(key: NodeKey) -> NodeRef:
    return NodeRef(type=key[0], id=key[1])

