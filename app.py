from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends, Query, Request
from fastapi.responses import JSONResponse, FileResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, Dict, Any, List, Union
from pathlib import Path
from contextlib import asynccontextmanager

import aiofiles
import os
import hashlib
import random
import multiprocessing
import json
import uvicorn

# 导入tortoise-orm
from tortoise.contrib.fastapi import RegisterTortoise
from models import Image

# 加载配置
with open("config.json") as f:
    config = json.load(f)

# 配置常量
UPLOAD_FOLDER = os.path.abspath(os.environ.get("UPLOAD_FOLDER", config["upload_dir"]) or config["upload_dir"])
SECRET_KEY = config["appkey"]
PAGE_SIZE = 20

# Tortoise-ORM配置
TORTOISE_ORM = {
    "connections": {
        "default": "sqlite://db/images.db"
    },
    "apps": {
        "models": {
            "models": ["models", "aerich.models"],
            "default_connection": "default",
        }
    }
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    async with RegisterTortoise(
        app,
        config=TORTOISE_ORM,
        generate_schemas=True,
    ):
        yield


# 创建FastAPI应用
app = FastAPI(
    title=config["name"],
    version="2.4.6",
    description="FireflyEnch - 简单的图片画廊系统",
    lifespan=lifespan,
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def jsonify(data: Optional[Dict[str, Any]] = None, msg: str = "OK", status: int = 200) -> JSONResponse:
    """统一JSON响应格式"""
    return JSONResponse(content={"code": status, "message": msg, "data": data}, status_code=status)


async def save_file(content: bytes, filename: str) -> str:
    """异步保存文件"""
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    async with aiofiles.open(filepath, "wb") as out_file:
        await out_file.write(content)
    return filepath


def get_safe_path(base_dir: str, user_path: str) -> Optional[str]:
    """安全地处理用户提供的路径，防止路径遍历攻击"""
    safe_path = (Path(base_dir) / user_path).resolve()
    base_path = Path(base_dir).resolve()
    if not str(safe_path).startswith(str(base_path)):
        return None
    return str(safe_path)


async def verify_appkey(appkey: Optional[str] = Query(None)) -> bool:
    """API密钥验证"""
    if appkey != SECRET_KEY:
        raise HTTPException(status_code=401, detail="无权限")
    return True


# ========== API 路由 ==========

@app.post("/api/upload")
async def upload_image(
    request: Request,
    image: UploadFile = File(...),
    tags: str = Form(""),
    appkey: str = Depends(verify_appkey),
) -> JSONResponse:
    """上传图片"""
    if not image.filename:
        raise HTTPException(status_code=400, detail="没有选择文件")

    tag_list = tags.split(",") if tags else []
    base, ext = os.path.splitext(image.filename)

    content = await image.read()
    filename = f"{hashlib.md5(content).hexdigest()}{ext}"

    await save_file(content, filename)
    new_image = await Image.create_image(filename, tag_list)

    result = {
        "id": new_image.id,
        "url": str(request.base_url) + f"api/image/{new_image.id}",
        "tags": new_image.tags,
    }
    return jsonify(result, "上传成功", 201)


@app.get("/api/images")
async def get_images(page: int = Query(1, ge=1)) -> JSONResponse:
    """获取图片列表（分页）"""
    result = await Image.get_all(page=page, page_size=PAGE_SIZE)
    if result["images"]:
        random.shuffle(result["images"])
    return jsonify(result)


# 注意：固定路由必须在参数化路由之前注册
@app.get("/api/image/random")
async def random_image(info: str = Query("0")) -> Union[JSONResponse, FileResponse]:
    """获取随机图片"""
    image = await Image.get_random()
    if not image:
        raise HTTPException(status_code=404, detail="没有图片")

    if info != "0":
        return jsonify(image.to_dict())

    filepath = os.path.join(UPLOAD_FOLDER, image.filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="图片文件不存在")
    return FileResponse(filepath)


@app.get("/api/image/tag")
async def get_image_by_tag(tag: str = Query(..., description="标签列表，逗号分隔")) -> JSONResponse:
    """根据标签获取图片"""
    if not tag:
        raise HTTPException(status_code=400, detail="请提供标签")

    tag_list = tag.split(",")
    images = await Image.get_by_tags(tag_list)
    return jsonify({"total": len(images), "images": [img.to_dict() for img in images]})


@app.get("/api/image/{image_id}")
async def get_image(image_id: int, info: Optional[str] = Query(None)) -> Union[JSONResponse, FileResponse]:
    """根据ID获取图片"""
    image = await Image.get_by_id(image_id)
    if not image:
        raise HTTPException(status_code=404, detail="图片未找到")

    if info:
        return jsonify(image.to_dict())

    filepath = os.path.join(UPLOAD_FOLDER, image.filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="图片文件不存在")
    return FileResponse(filepath)


@app.delete("/api/image/{image_id}")
async def delete_image(
    image_id: int,
    rmfile: str = Query("1", description="是否删除文件"),
    appkey: str = Depends(verify_appkey),
) -> JSONResponse:
    """删除图片"""
    image = await Image.get_by_id(image_id)
    if not image:
        raise HTTPException(status_code=404, detail="图片未找到")

    if rmfile == "1":
        filepath = os.path.join(UPLOAD_FOLDER, image.filename)
        if os.path.exists(filepath):
            os.remove(filepath)

    await Image.delete_image(image_id)
    return jsonify(None, "图片删除成功", 204)


@app.patch("/api/image/{image_id}")
async def update_image_tags(
    image_id: int,
    tags: str = Query("", description="新标签列表，逗号分隔"),
    appkey: str = Depends(verify_appkey),
) -> JSONResponse:
    """更新图片标签"""
    tag_list = tags.split(",") if tags else []
    success = await Image.update_tags(image_id, tag_list)
    if success:
        return jsonify(msg="完成")
    else:
        raise HTTPException(status_code=404, detail="图片未找到")


@app.delete("/api/clear")
async def clear_cache(appkey: str = Depends(verify_appkey)) -> JSONResponse:
    """清除数据库缓存"""
    return jsonify()


# ========== 静态文件（放在最后） ==========

@app.get("/{path:path}")
async def static_file(path: str) -> FileResponse:
    """静态文件服务"""
    file_path = get_safe_path("files", path)
    if not file_path or not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="文件不存在")
    return FileResponse(file_path)


def main():
    """启动应用"""
    cpu_count = multiprocessing.cpu_count()
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=config["port"],
        workers=cpu_count * 2 + 1,
        reload=False,
    )


if __name__ == "__main__":
    main()
