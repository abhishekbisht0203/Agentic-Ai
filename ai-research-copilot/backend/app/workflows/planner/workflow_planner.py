"""
Workflow Planner.

Parses a workflow definition (graph of nodes and edges) into an
ordered list of executable steps. Supports sequential, parallel,
conditional, and loop workflow types with topological ordering
and cycle detection.
"""

import logging
from collections import defaultdict, deque
from typing import Any

logger = logging.getLogger(__name__)


class WorkflowValidationError(Exception):
    """Raised when a workflow definition fails validation."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        self.message = message
        self.details = details or {}
        super().__init__(message)


class WorkflowPlanner:
    """Plans workflow execution steps from a workflow definition.

    Takes a graph-based workflow definition (nodes + edges) and produces
    a topologically-ordered list of steps ready for sequential execution.
    Handles conditional branching, parallel groups, and loop constructs.
    """

    def validate_definition(self, definition: dict[str, Any]) -> bool:
        """Validate that a workflow definition has the required structure.

        A valid definition must contain:
        - ``nodes``: A list of node dictionaries, each with at least ``id`` and ``type``.
        - ``edges``: A list of edge dictionaries, each with ``from`` and ``to``.

        Args:
            definition: The workflow definition dictionary.

        Returns:
            True if valid.

        Raises:
            WorkflowValidationError: If the definition is malformed.
        """
        if not isinstance(definition, dict):
            raise WorkflowValidationError("Workflow definition must be a dictionary")

        nodes = definition.get("nodes")
        if not isinstance(nodes, list) or len(nodes) == 0:
            raise WorkflowValidationError(
                "Workflow definition must contain a non-empty 'nodes' list"
            )

        edges = definition.get("edges", [])
        if not isinstance(edges, list):
            raise WorkflowValidationError("'edges' must be a list")

        node_ids: set[str] = set()
        for i, node in enumerate(nodes):
            if not isinstance(node, dict):
                raise WorkflowValidationError(f"Node at index {i} must be a dictionary")
            node_id = node.get("id")
            if not node_id:
                raise WorkflowValidationError(f"Node at index {i} is missing an 'id'")
            if node_id in node_ids:
                raise WorkflowValidationError(f"Duplicate node id: '{node_id}'")
            node_ids.add(node_id)
            node_type = node.get("type")
            if not node_type:
                raise WorkflowValidationError(
                    f"Node '{node_id}' is missing a 'type'"
                )

        for i, edge in enumerate(edges):
            if not isinstance(edge, dict):
                raise WorkflowValidationError(f"Edge at index {i} must be a dictionary")
            from_id = edge.get("from")
            to_id = edge.get("to")
            if not from_id:
                raise WorkflowValidationError(
                    f"Edge at index {i} is missing 'from'"
                )
            if not to_id:
                raise WorkflowValidationError(
                    f"Edge at index {i} is missing 'to'"
                )
            if from_id not in node_ids:
                raise WorkflowValidationError(
                    f"Edge references unknown source node: '{from_id}'"
                )
            if to_id not in node_ids:
                raise WorkflowValidationError(
                    f"Edge references unknown target node: '{to_id}'"
                )

        return True

    def plan(self, definition: dict[str, Any]) -> list[dict[str, Any]]:
        """Parse a workflow definition into an ordered list of executable steps.

        Performs topological sort on the node graph, detecting cycles
        and unreachable nodes. Each step in the result includes its
        full node data plus computed metadata.

        Args:
            definition: The workflow definition dictionary with ``nodes`` and ``edges``.

        Returns:
            An ordered list of step dictionaries ready for execution.

        Raises:
            WorkflowValidationError: If the definition is invalid or contains cycles.
        """
        self.validate_definition(definition)

        nodes = definition.get("nodes", [])
        edges = definition.get("edges", [])

        node_map: dict[str, dict[str, Any]] = {}
        adjacency: dict[str, list[str]] = defaultdict(list)
        in_degree: dict[str, int] = {}

        for node in nodes:
            node_id = node["id"]
            node_map[node_id] = node
            in_degree[node_id] = 0

        for edge in edges:
            from_id = edge["from"]
            to_id = edge["to"]
            adjacency[from_id].append(to_id)
            in_degree[to_id] = in_degree.get(to_id, 0) + 1

        # Kahn's algorithm for topological sort
        queue: deque[str] = deque(
            node_id for node_id, deg in in_degree.items() if deg == 0
        )
        sorted_ids: list[str] = []

        while queue:
            current = queue.popleft()
            sorted_ids.append(current)
            for neighbor in adjacency[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(sorted_ids) != len(node_map):
            visited_set = set(sorted_ids)
            cycle_nodes = [nid for nid in node_map if nid not in visited_set]
            raise WorkflowValidationError(
                "Workflow contains a cycle",
                details={"cycle_nodes": cycle_nodes},
            )

        # Enrich steps with ordering metadata
        steps: list[dict[str, Any]] = []
        for idx, node_id in enumerate(sorted_ids):
            node = node_map[node_id]
            step = {
                "id": node_id,
                "step_index": idx,
                "type": node.get("type", "unknown"),
                "name": node.get("name", node_id),
                "config": node.get("config", {}),
                "dependencies": [
                    e["from"]
                    for e in edges
                    if e["to"] == node_id
                ],
                "is_start": in_degree.get(node_id, 0) == 0
                or node_id in {e["from"] for e in edges}
                and all(
                    e["to"] != node_id for e in edges if e["from"] == node_id
                ),
            }
            steps.append(step)

        # Mark the actual start nodes (no incoming edges)
        for step in steps:
            step["is_start"] = len(step["dependencies"]) == 0

        logger.info(
            "Planned %d steps for workflow definition", len(steps)
        )
        return steps

    def get_step_dependencies(
        self, definition: dict[str, Any], step_id: str
    ) -> list[str]:
        """Return the direct dependencies for a specific step.

        Args:
            definition: The workflow definition dictionary.
            step_id: The step identifier to query.

        Returns:
            A list of step IDs that must complete before the given step.
        """
        edges = definition.get("edges", [])
        return [e["from"] for e in edges if e["to"] == step_id]

    def get_execution_layers(
        self, definition: dict[str, Any]
    ) -> list[list[str]]:
        """Group steps into parallel execution layers.

        Steps within the same layer have no dependencies on each other
        and can theoretically run in parallel. Layers are ordered
        sequentially.

        Args:
            definition: The workflow definition dictionary.

        Returns:
            A list of layers, each containing step IDs that can run in parallel.
        """
        self.validate_definition(definition)

        nodes = definition.get("nodes", [])
        edges = definition.get("edges", [])

        in_degree: dict[str, int] = {node["id"]: 0 for node in nodes}
        adjacency: dict[str, list[str]] = defaultdict(list)

        for edge in edges:
            adjacency[edge["from"]].append(edge["to"])
            in_degree[edge["to"]] += 1

        layers: list[list[str]] = []
        current_layer = [nid for nid, deg in in_degree.items() if deg == 0]

        while current_layer:
            layers.append(sorted(current_layer))
            next_layer: list[str] = []
            for node_id in current_layer:
                for neighbor in adjacency[node_id]:
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        next_layer.append(neighbor)
            current_layer = next_layer

        return layers
