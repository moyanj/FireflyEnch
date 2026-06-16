from io import BytesIO
from pathlib import Path
from typing import Any, Optional, Tuple
import hashlib
import os
import time

import imagehash
from PIL import Image as PILImage
from PIL import ImageOps


def compute_quick_hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def compute_perceptual_hash(content: bytes) -> imagehash.ImageHash:
    with PILImage.open(BytesIO(content)) as image:
        image = ImageOps.exif_transpose(image)

    return imagehash.phash(image)


def compute_hash(content: bytes) -> Tuple[str, str]:
    return (
        compute_quick_hash(content),
        str(compute_perceptual_hash(content)),
    )


def phash_distance(a: imagehash.ImageHash, b: imagehash.ImageHash) -> int:
    return int(a - b)


def get_safe_path(base_dir: str, user_path: str) -> Optional[str]:
    safe_path = (Path(base_dir) / user_path).resolve()
    base_path = Path(base_dir).resolve()
    if not str(safe_path).startswith(str(base_path)):
        return None
    return str(safe_path)


def normalize_tags(tags: list[str]) -> list[str]:
    seen: set[str] = set()
    normalized: list[str] = []

    for raw_tag in tags:
        tag = raw_tag.strip()
        if not tag:
            continue
        if len(tag) > 32:
            tag = tag[:32]
        tag_key = tag.casefold()
        if tag_key in seen:
            continue
        seen.add(tag_key)
        normalized.append(tag)

    return normalized


def parse_tags(tags: str) -> list[str]:
    return normalize_tags(tags.split(",")) if tags else []


def cleanup_expired_prepared_uploads(
    prepared_uploads: dict[str, Any],
    temp_upload_folder: str,
    expire_seconds: int,
) -> None:
    now = time.time()
    expired_tokens = [
        token
        for token, prepared in prepared_uploads.items()
        if prepared["created_at"] + expire_seconds < now
    ]

    for token in expired_tokens:
        prepared = prepared_uploads.pop(token, None)
        if not prepared:
            continue
        temp_path = os.path.join(temp_upload_folder, prepared["temp_filename"])
        if os.path.exists(temp_path):
            os.remove(temp_path)


def build_public_image_url(base_url: str, image_id: int) -> str:
    return f"{base_url}api/images/{image_id}/file"
