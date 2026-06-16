from pathlib import Path
import sys

from PIL import Image as PILImage

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app


def make_image(path: Path, size: tuple[int, int], color: tuple[int, int, int]) -> None:
    image = PILImage.new("RGB", size, color)
    image.save(path)


def test_fast_hash_matches_exact_duplicate():
    payload = b"exact-duplicate"
    assert app.compute_quick_hash(payload) == app.compute_quick_hash(payload)


def test_phash_detects_near_duplicate(tmp_path):
    original = tmp_path / "original.png"
    near_duplicate = tmp_path / "near_duplicate.png"
    make_image(original, (800, 600), (20, 120, 200))
    make_image(near_duplicate, (820, 620), (20, 120, 200))

    original_hash = app.compute_perceptual_hash(original.read_bytes())
    duplicate_hash = app.compute_perceptual_hash(near_duplicate.read_bytes())

    assert original_hash is not None
    assert duplicate_hash is not None
    assert app.phash_distance(original_hash, duplicate_hash) <= app.PHASH_DUPLICATE_THRESHOLD
