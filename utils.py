import asyncio
import base64
from io import BytesIO
from pathlib import Path
from typing import Any, Optional, Tuple
import hashlib
import os
import time

import imagehash
from PIL import Image as PILImage
from PIL import ImageOps

from config import THUMBNAIL_SIZE


def compute_quick_hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def compute_perceptual_hash(content: bytes) -> imagehash.ImageHash:
    with PILImage.open(BytesIO(content)) as image:
        image = ImageOps.exif_transpose(image)

    return imagehash.phash(image)


def compute_hashes(content: bytes) -> Tuple[str, str]:
    """一次性计算 SHA256 和感知哈希，只打开图片一次。

    返回 (sha256_hex, phash_hex)。
    """
    sha256 = hashlib.sha256(content).hexdigest()
    with PILImage.open(BytesIO(content)) as image:
        image = ImageOps.exif_transpose(image)
        phash = str(imagehash.phash(image))
    return (sha256, phash)


def compute_hash(content: bytes) -> Tuple[str, str]:
    """兼容旧接口，委托给 compute_hashes。"""
    return compute_hashes(content)


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


def create_thumbnail_bytes(content: bytes) -> bytes:
    """将图片内容转换为 WebP 缩略图的原始字节（同步）"""
    with PILImage.open(BytesIO(content)) as img:
        img = img.convert("RGB")
        img.thumbnail(THUMBNAIL_SIZE)

        buffer = BytesIO()
        img.save(buffer, format="WEBP", quality=85, method=6)
        buffer.seek(0)
        return buffer.getvalue()


def create_thumbnail_base64(content: bytes) -> str:
    """将图片内容转换为缩略图的 base64 data URL"""
    webp_bytes = create_thumbnail_bytes(content)
    return "data:image/webp;base64," + base64.b64encode(webp_bytes).decode("ascii")


async def async_compute_hashes(content: bytes) -> Tuple[str, str]:
    """异步计算 SHA256 和感知哈希（在工作线程中执行）"""
    return await asyncio.to_thread(compute_hashes, content)


async def async_create_thumbnail_bytes(content: bytes) -> bytes:
    """异步生成 WebP 缩略图字节（在工作线程中执行）"""
    return await asyncio.to_thread(create_thumbnail_bytes, content)


def parse_tags(tags: str) -> list[str]:
    return normalize_tags(tags.split(",")) if tags else []


def parse_search_query(query: str) -> tuple[list[str], list[str], list[str]]:
    """将搜索串解析为 OR / AND / NOT 三组标签。"""
    or_tags: list[str] = []
    and_tags: list[str] = []
    not_tags: list[str] = []

    for raw_token in query.split():
        token = raw_token.strip()
        if not token:
            continue

        if token.startswith("+") and len(token) > 1:
            and_tags.append(token[1:])
            continue
        if token.startswith("-") and len(token) > 1:
            not_tags.append(token[1:])
            continue

        or_tags.append(token)

    return (
        normalize_tags(or_tags),
        normalize_tags(and_tags),
        normalize_tags(not_tags),
    )


async def cleanup_expired_prepared_uploads(
    prepared_uploads: dict[str, Any],
    temp_upload_folder: str,
    expire_seconds: int,
) -> None:
    while True:
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
        await asyncio.sleep(60)  # 每分钟检查一次


def build_public_image_url(base_url: str, image_id: int) -> str:
    return f"{base_url}api/images/{image_id}/file"
