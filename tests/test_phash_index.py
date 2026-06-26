from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from phash_index import PhashBKTree, PhashRecord, hamming_distance, phash_hex_to_int


def make_record(image_id: int, phash: str) -> PhashRecord:
    return PhashRecord(
        id=image_id,
        hash_value=phash_hex_to_int(phash),
    )


def test_hamming_distance_uses_64bit_xor_popcount() -> None:
    assert hamming_distance(0b1010, 0b0011) == 2


def test_phash_record_only_stores_id_and_hash_value() -> None:
    record = make_record(7, "000000000000000f")

    assert record.id == 7
    assert record.hash_value == 15
    assert set(record.__dataclass_fields__) == {"id", "hash_value"}


def test_bktree_returns_nearest_matches_sorted_by_distance() -> None:
    tree = PhashBKTree(
        [
            make_record(1, "0000000000000000"),
            make_record(2, "0000000000000001"),
            make_record(3, "0000000000000003"),
        ]
    )

    matches = tree.search(phash_hex_to_int("0000000000000000"), max_distance=2)

    assert [match.record.id for match in matches] == [1, 2, 3]
    assert [match.distance for match in matches] == [0, 1, 2]


def test_bktree_limit_applies_after_distance_sort() -> None:
    tree = PhashBKTree(
        [
            make_record(10, "ffffffffffffffff"),
            make_record(11, "fffffffffffffffe"),
            make_record(12, "fffffffffffffffc"),
        ]
    )

    matches = tree.search(
        phash_hex_to_int("ffffffffffffffff"),
        max_distance=3,
        limit=2,
    )

    assert [match.record.id for match in matches] == [10, 11]


def test_update_image_route_clears_phash_cache_when_metadata_changes() -> None:
    app_source = Path(__file__).resolve().parents[1] / "app.py"
    source = app_source.read_text(encoding="utf-8")
    route_start = source.index('@app.patch("/api/images/{image_id}")')
    route_end = source.index('@app.delete("/api/cache")')
    route_block = source[route_start:route_end]

    assert "clear_phash_index_cache()" in route_block
