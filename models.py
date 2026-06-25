import imagehash
import time
from tortoise.models import Model
from tortoise import fields, connections
from typing import List, Optional, Dict, Any, Tuple

import config
from utils import compute_perceptual_hash, compute_quick_hash, phash_distance


def _is_json_filter_supported() -> bool:
    """检查当前数据库是否支持 JSON 字段过滤（PostgreSQL/MySQL）"""
    try:
        conn = connections.get("default")
        # 检查 capabilities 中的 support_json_attributes
        return getattr(conn.capabilities, "support_json_attributes", False)
    except Exception:
        return False


# ==================== 标签缓存 ====================

# 标签缓存：存储 (tags_list, expire_time)
_tag_cache: Optional[Tuple[List[str], float]] = None
TAG_CACHE_TTL = 300  # 缓存 5 分钟


def clear_tag_cache() -> None:
    """清除标签缓存"""
    global _tag_cache
    _tag_cache = None


class Image(Model):
    """图片模型"""

    id = fields.IntField(pk=True)
    filename = fields.CharField(max_length=255)
    tags = fields.JSONField(default=list)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    phash = fields.CharField(max_length=64)
    sha256 = fields.CharField(max_length=64)
    nsfw = fields.BooleanField(default=False)
    nsfw_score = fields.FloatField(default=0.0)

    class Meta:  # type: ignore
        table = "images"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "id": self.id,
            "filename": self.filename,
            "tags": self.tags,
            "nsfw": self.nsfw,
            "nsfw_score": self.nsfw_score,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    async def get_by_id(cls, image_id: int) -> Optional["Image"]:
        """根据ID获取图片"""
        return await cls.get_or_none(id=image_id)

    @classmethod
    def _resolve_sort(cls, sort: str) -> str:
        """将排序别名映射为 Tortoise ORM 排序字段"""
        sort_map = {
            "id_desc": "-id",
            "id_asc": "id",
            "created_at_desc": "-created_at",
            "created_at_asc": "created_at",
        }
        return sort_map.get(sort, "-id")

    @classmethod
    async def get_all(
        cls,
        page: int = 1,
        page_size: int = 20,
        sort: str = "id_desc",
        nsfw: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """分页获取所有图片，支持排序和NSFW过滤"""
        offset = (page - 1) * page_size
        order_field = cls._resolve_sort(sort)

        queryset = cls.all()
        if nsfw is not None:
            queryset = queryset.filter(nsfw=nsfw)

        images = await queryset.order_by(order_field).offset(offset).limit(page_size)
        total = await queryset.count() if nsfw is not None else await cls.all().count()

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "images": [img.to_dict() for img in images],
            "last": offset + page_size >= total,
        }

    @classmethod
    async def get_random(cls) -> Optional["Image"]:
        """获取随机图片"""
        count = await cls.all().count()
        if count == 0:
            return None

        import random

        random_id = random.randint(1, count)
        return await cls.get_or_none(id=random_id)

    @classmethod
    async def get_all_tags(cls) -> List[str]:
        """获取图库中去重后的全部标签列表（带缓存）"""
        global _tag_cache

        # 检查缓存是否有效
        if _tag_cache is not None:
            tags, expire_time = _tag_cache
            if time.time() < expire_time:
                return tags

        # 缓存失效，重新查询
        tag_set: set[str] = set()

        for image in await cls.all():
            if image.tags:
                tag_set.update(tag for tag in image.tags if tag)

        tags = sorted(tag_set)

        # 更新缓存
        _tag_cache = (tags, time.time() + TAG_CACHE_TTL)

        return tags

    @classmethod
    async def get_by_tags(
        cls,
        tags: List[str],
        page: int = 1,
        page_size: int = 20,
        sort: str = "id_desc",
        nsfw: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """根据标签获取图片，支持分页、排序和NSFW过滤"""
        if not tags:
            return {
                "total": 0,
                "page": page,
                "page_size": page_size,
                "images": [],
                "last": True,
            }

        # 根据数据库类型选择过滤策略
        if _is_json_filter_supported():
            # PostgreSQL/MySQL：使用 ORM 原生的 __contains 在数据库端过滤
            queryset = cls.filter(tags__contains=tags)
            if nsfw is not None:
                queryset = queryset.filter(nsfw=nsfw)

            total = await queryset.count()
            order_field = cls._resolve_sort(sort)
            offset = (page - 1) * page_size
            images = (
                await queryset.order_by(order_field).offset(offset).limit(page_size)
            )
        else:
            # SQLite：回退到 Python 端过滤
            queryset = cls.all()
            if nsfw is not None:
                queryset = queryset.filter(nsfw=nsfw)

            all_images = await queryset
            matched = []
            for image in all_images:
                if image.tags and any(tag in image.tags for tag in tags):
                    matched.append(image)

            # 排序
            order_field = cls._resolve_sort(sort)
            reverse = order_field.startswith("-")
            field_name = order_field.lstrip("-")

            def sort_key(img: "Image"):
                val = getattr(img, field_name, None)
                if val is None:
                    return (1, "")  # null 排到最后
                return (0, val)

            matched.sort(key=sort_key, reverse=reverse)

            # 分页
            total = len(matched)
            offset = (page - 1) * page_size
            images = matched[offset : offset + page_size]

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "images": [img.to_dict() for img in images],
            "last": offset + page_size >= total,
        }

    @classmethod
    async def create_image(
        cls,
        filename: str,
        tags: List[str],
        img_hash: Tuple[str, str],
        nsfw: bool = False,
        nsfw_score: float = 0.0,
    ) -> "Image":
        """创建新图片记录"""
        image = await cls.create(
            filename=filename,
            tags=tags,
            sha256=img_hash[0],
            phash=img_hash[1],
            nsfw=nsfw,
            nsfw_score=nsfw_score,
        )
        clear_tag_cache()
        return image

    @classmethod
    async def update_tags(cls, image_id: int, tags: List[str]) -> bool:
        """更新图片标签"""
        image = await cls.get_or_none(id=image_id)
        if image:
            image.tags = tags
            await image.save()
            clear_tag_cache()
            return True
        return False

    @classmethod
    async def delete_image(cls, image_id: int) -> bool:
        """删除图片记录"""
        image = await cls.get_or_none(id=image_id)
        if image:
            await image.delete()
            clear_tag_cache()
            return True
        return False

    @classmethod
    async def get_all_phash(cls) -> List[Dict[str, Any]]:
        """获取所有图片的感知哈希值"""
        images = await cls.all()
        return [{"id": img.id, "phash": img.phash} for img in images if img.phash]

    @classmethod
    async def check_duplicate(cls, sha256: str, phash: str) -> bool:
        """检查图片是否重复"""
        image = await cls.get_or_none(sha256=sha256)
        if image:
            return True
        perceptual_hash = imagehash.hex_to_hash(phash)
        for phash in await cls.all().values_list("phash", flat=True):  # type: ignore
            if phash:
                b = imagehash.hex_to_hash(phash)
                if (
                    phash_distance(perceptual_hash, b)
                    <= config.PHASH_DUPLICATE_THRESHOLD
                ):
                    return True
        return False

    @classmethod
    async def find_similar_images(
        cls, phash: str, threshold: int = 10, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """根据感知哈希查找相似图片

        Args:
            phash: 用户提交的感知哈希值（十六进制字符串）
            threshold: 汉明距离阈值，越小越严格（默认10）
            limit: 返回结果数量限制（默认20）

        Returns:
            相似图片列表，包含图片信息和相似度距离
        """
        try:
            target_hash = imagehash.hex_to_hash(phash)
        except ValueError:
            return []

        # 获取所有图片的phash
        all_images = await cls.all().values(
            "id", "phash", "filename", "tags", "nsfw", "created_at"
        )

        similar_images = []
        for img_data in all_images:
            img_phash = img_data.get("phash")
            if not img_phash:
                continue
            try:
                img_hash = imagehash.hex_to_hash(img_phash)
                distance = phash_distance(target_hash, img_hash)
                if distance <= threshold:
                    similar_images.append(
                        {
                            "id": img_data["id"],
                            "filename": img_data["filename"],
                            "tags": img_data["tags"],
                            "nsfw": img_data["nsfw"],
                            "created_at": (
                                img_data["created_at"].isoformat()
                                if img_data["created_at"]
                                else None
                            ),
                            "distance": distance,
                        }
                    )
            except ValueError:
                continue

        # 按距离排序（越小越相似），然后限制数量
        similar_images.sort(key=lambda x: x["distance"])
        return similar_images[:limit]
