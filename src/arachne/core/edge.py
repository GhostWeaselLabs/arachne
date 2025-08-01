from __future__ import annotations

from dataclasses import dataclass

from .ports import Port


@dataclass(frozen=True, slots=True)
class Edge:
    source_node: str
    source_port: Port
    target_node: str
    target_port: Port

    def is_self_loop(self) -> bool:
        return self.source_node == self.target_node
