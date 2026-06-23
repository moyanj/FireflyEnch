import imagehash
from tortoise.models import Model
from tortoise import fields
from typing import List, Optional, Dict, Any, Tuple

import config
from utils import compute_perceptual_hash, compute_quick_hash, phash_distance


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

        # SQLite 的 JSONField __contains 不可用，使用 Python 端过滤
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
        page_images = matched[offset : offset + page_size]

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "images": [img.to_dict() for img in page_images],
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
        return await cls.create(
            filename=filename,
            tags=tags,
            sha256=img_hash[0],
            phash=img_hash[1],
            nsfw=nsfw,
            nsfw_score=nsfw_score,
        )

    @classmethod
    async def update_tags(cls, image_id: int, tags: List[str]) -> bool:
        """更新图片标签"""
        image = await cls.get_or_none(id=image_id)
        if image:
            image.tags = tags
            await image.save()
            return True
        return False

    @classmethod
    async def delete_image(cls, image_id: int) -> bool:
        """删除图片记录"""
        image = await cls.get_or_none(id=image_id)
        if image:
            await image.delete()
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
        for img in await cls.all():
            if img.phash:
                b = imagehash.hex_to_hash(img.phash)
                if (
                    phash_distance(perceptual_hash, b)
                    <= config.PHASH_DUPLICATE_THRESHOLD
                ):
                    return True
        return False
