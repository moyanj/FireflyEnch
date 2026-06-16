from tortoise.models import Model
from tortoise import fields
from typing import List, Optional, Dict, Any


class Image(Model):
    """图片模型"""
    id = fields.IntField(pk=True)
    filename = fields.CharField(max_length=255)
    tags = fields.JSONField(default=list)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "images"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "id": self.id,
            "filename": self.filename,
            "tags": self.tags,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    async def get_by_id(cls, image_id: int) -> Optional["Image"]:
        """根据ID获取图片"""
        return await cls.get_or_none(id=image_id)

    @classmethod
    async def get_all(cls, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """分页获取所有图片"""
        offset = (page - 1) * page_size
        images = await cls.all().offset(offset).limit(page_size)
        total = await cls.all().count()
        
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
    async def get_by_tags(cls, tags: List[str]) -> List["Image"]:
        """根据标签获取图片"""
        if not tags:
            return []
        
        # 构建查询条件：任一标签匹配
        from tortoise.expressions import Q
        query = Q()
        for tag in tags:
            query |= Q(tags__contains=tag)
        
        return await cls.filter(query)

    @classmethod
    async def create_image(cls, filename: str, tags: List[str]) -> "Image":
        """创建新图片记录"""
        return await cls.create(filename=filename, tags=tags)

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
