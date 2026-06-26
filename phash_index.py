from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable


def phash_hex_to_int(phash: str) -> int:
    normalized = phash.strip().lower()
    if len(normalized) != 16:
        raise ValueError("phash must be a 16-character hex string")
    return int(normalized, 16)


def hamming_distance(a: int, b: int) -> int:
    return (a ^ b).bit_count()


@dataclass(slots=True)
class PhashRecord:
    id: int
    hash_value: int


@dataclass(slots=True)
class PhashMatch:
    record: PhashRecord
    distance: int


@dataclass(slots=True)
class _BKNode:
    key: int
    records: list[PhashRecord] = field(default_factory=list)
    children: dict[int, "_BKNode"] = field(default_factory=dict)


class PhashBKTree:
    def __init__(self, records: Iterable[PhashRecord] = ()) -> None:
        self.root: _BKNode | None = None
        for record in records:
            self.add(record)

    def add(self, record: PhashRecord) -> None:
        if self.root is None:
            self.root = _BKNode(key=record.hash_value, records=[record])
            return

        node = self.root
        while True:
            distance = hamming_distance(record.hash_value, node.key)
            if distance == 0:
                node.records.append(record)
                return

            child = node.children.get(distance)
            if child is None:
                node.children[distance] = _BKNode(key=record.hash_value, records=[record])
                return
            node = child

    def search(self, hash_value: int, max_distance: int, limit: int | None = None) -> list[PhashMatch]:
        if self.root is None:
            return []

        matches: list[PhashMatch] = []
        stack = [self.root]

        while stack:
            node = stack.pop()
            distance = hamming_distance(hash_value, node.key)

            if distance <= max_distance:
                for record in node.records:
                    matches.append(
                        PhashMatch(
                            record=record,
                            distance=hamming_distance(hash_value, record.hash_value),
                        )
                    )

            lower = distance - max_distance
            upper = distance + max_distance
            for edge_distance, child in node.children.items():
                if lower <= edge_distance <= upper:
                    stack.append(child)

        matches.sort(key=lambda item: (item.distance, item.record.id))
        if limit is not None:
            return matches[:limit]
        return matches
