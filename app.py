from sanic import Sanic, Request, response
from sanic_ext import openapi as doc
from urllib.parse import urljoin
from functools import wraps
from typing import Optional, Dict, Any, List
from pathlib import Path

import aiofiles
import os
import hashlib
import random
import multiprocessing
from sanic.log import logger
import json

# 导入tortoise-orm
from tortoise.contrib.sanic import register_tortoise
from models import Image

# 加载配置
with open("config.json") as f:
    config = json.load(f)

# 创建Sanic应用
Sanic.start_method = "fork"
app = Sanic(config["name"])

# 配置常量
UPLOAD_FOLDER = os.path.abspath(os.environ.get("UPLOAD_FOLDER", config["upload_dir"]))
SECRET_KEY = config["appkey"]
PAGE_SIZE = 20

# 应用配置
app.config.FORWARDED_FOR_HEADER = "X-FORWARDED-FOR"
app.config["OAS_UI_DEFAULT"] = "swagger"
app.config["OAS_UI_REDOC"] = False
app.config.HEALTH = True
app.config.HEALTH_ENDPOINT = True
app.config.CORS_ORIGINS = "*"

# OpenAPI描述
app.ext.openapi.describe(config["name"], "2.4.6")

# Tortoise-ORM配置
TORTOISE_ORM = {
    "connections": {
        "default": f"sqlite://db/images.db"
    },
    "apps": {
        "models": {
            "models": ["models", "aerich.models"],
            "default_connection": "default",
        }
    }
}


def jsonify(data: Optional[Dict[str, Any]] = None, msg: str = "OK", status: int = 200) -> response.HTTPResponse:
    """统一JSON响应格式"""
    res = {"code": status, "message": msg, "data": data}
    return response.json(res, status=status)


async def save_file(file: Any, filename: str) -> str:
    """异步保存文件"""
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    async with aiofiles.open(filepath, "wb") as out_file:
        await out_file.write(file.body)
    return filepath


def get_safe_path(base_dir: str, user_path: str) -> Optional[str]:
    """安全地处理用户提供的路径，防止路径遍历攻击"""
    # 规范化路径
    safe_path = Path(base_dir) / user_path
    safe_path = safe_path.resolve()
    
    # 确保路径在指定目录内
    base_path = Path(base_dir).resolve()
    if not str(safe_path).startswith(str(base_path)):
        return None
    
    return str(safe_path)


def appkey_required(view_func: Any) -> Any:
    """API密钥验证装饰器"""
    @wraps(view_func)
    async def wrapped_view(request: Request, *args: Any, **kwargs: Any) -> response.HTTPResponse:
        head_T = request.args.get("appkey", None)
        if not head_T == SECRET_KEY:
            return jsonify(None, "无权限", 401)
        else:
            return await view_func(request, *args, **kwargs)

    return wrapped_view


@app.exception(Exception)
async def exc(request: Request, exception: Exception) -> response.HTTPResponse:
    """全局异常处理"""
    logger.error(f"Exception: {exception}", exc_info=True)
    return jsonify(msg="服务器出错", status=500)


async def before_server_start(app: Sanic, loop):
    """服务器启动前初始化"""
    # 确保上传目录存在
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    
    # 注册Tortoise-ORM
    register_tortoise(
        app,
        config=TORTOISE_ORM,
        generate_schemas=True,
    )


app.register_listener(before_server_start, "main_process_start")


@app.post("/api/upload")
@doc.exclude(True)
@appkey_required
async def upload_image(request: Request) -> response.HTTPResponse:
    """上传图片"""
    if "image" not in request.files:
        return jsonify(msg="请求中没有文件部分", status=400)

    file = request.files["image"]
    file = file[0]
    if file.name == "":
        return jsonify(msg="没有选择文件", status=400)

    tags = request.form.get("tags", "").split(',')

    # 确保文件名是安全的
    filename = file.name
    base, ext = os.path.splitext(filename)
    
    # 计算文件哈希
    hashs = hashlib.md5()
    hashs.update(file.body)
    filename = f"{hashs.hexdigest()}{ext}"

    # 保存文件
    await save_file(file, filename)

    # 创建图片记录
    new_image = await Image.create_image(filename, tags)
    
    # 构建响应
    result = {
        "id": new_image.id,
        "url": urljoin(
            request.host, app.url_for("get_image", image_id=str(new_image.id))
        ),
        "tags": new_image.tags,
    }

    return jsonify(result, "上传成功", 201)


@app.get("/api/images")
async def get_images(request: Request) -> response.HTTPResponse:
    """获取图片列表（分页）"""
    page = int(request.args.get("page", 1))
    
    # 获取图片列表
    result = await Image.get_all(page=page, page_size=PAGE_SIZE)
    
    # 随机排序
    if result["images"]:
        random.shuffle(result["images"])
    
    return jsonify(result)


@app.get("/api/image/random")
async def random_image(request: Request) -> response.HTTPResponse:
    """获取随机图片"""
    image = await Image.get_random()
    
    if not image:
        return jsonify(None, "没有图片", 404)
    
    # 返回图片信息
    if request.args.get("info", "0") != "0":
        return jsonify(image.to_dict())
    
    # 返回图片文件
    filepath = os.path.join(UPLOAD_FOLDER, image.filename)
    if not os.path.exists(filepath):
        return jsonify(None, "图片文件不存在", 404)
    
    return await response.file_stream(filepath)


@app.get("/api/image/<image_id:int>")
async def get_image(request: Request, image_id: int) -> response.HTTPResponse:
    """根据ID获取图片"""
    image = await Image.get_by_id(image_id)
    
    if not image:
        return jsonify(None, "图片未找到", 404)
    
    # 返回图片信息
    if request.args.get("info"):
        return jsonify(image.to_dict())
    
    # 返回图片文件
    filepath = os.path.join(UPLOAD_FOLDER, image.filename)
    if not os.path.exists(filepath):
        return jsonify(None, "图片文件不存在", 404)
    
    return await response.file_stream(filepath)


@app.get("/api/image/tag")
async def get_image_by_tag(request: Request) -> response.HTTPResponse:
    """根据标签获取图片"""
    tags = request.args.get("tag")
    if not tags:
        return jsonify(None, "请提供标签", 400)
    
    tag_list = tags.split(",")
    images = await Image.get_by_tags(tag_list)
    
    return jsonify({
        "total": len(images),
        "images": [img.to_dict() for img in images],
    })


@app.delete("/api/image/<image_id:int>")
@doc.exclude(True)
@appkey_required
async def delete_image(request: Request, image_id: int) -> response.HTTPResponse:
    """删除图片"""
    image = await Image.get_by_id(image_id)
    
    if not image:
        return jsonify(None, "图片未找到", 404)
    
    # 删除文件
    if request.args.get("rmfile", "1") == "1":
        filepath = os.path.join(UPLOAD_FOLDER, image.filename)
        if os.path.exists(filepath):
            os.remove(filepath)
    
    # 删除数据库记录
    await Image.delete_image(image_id)
    return jsonify(None, "图片删除成功", 204)


@app.patch("/api/image/<image_id:int>")
@doc.exclude(True)
@appkey_required
async def update_image_tags(request: Request, image_id: int) -> response.HTTPResponse:
    """更新图片标签"""
    tags = request.args.get("tags", "").split(",")
    success = await Image.update_tags(image_id, tags)
    
    if success:
        return jsonify(msg="完成")
    else:
        return jsonify(None, "图片未找到", 404)


@app.delete("/api/clear")
@doc.exclude(True)
@appkey_required
async def clear_cache(request: Request) -> response.HTTPResponse:
    """清除数据库缓存"""
    # 这里可以添加缓存清理逻辑
    return jsonify()


@app.route("/<path:path>", name="files")
@app.route("/", name="index")
@doc.exclude(True)
async def static_file(request: Request, path: str = "/index.html") -> response.HTTPResponse:
    """静态文件服务"""
    # 安全地处理路径
    file_path = get_safe_path("files", path)
    
    if not file_path:
        return jsonify(msg="文件不存在", status=404)
    
    # 验证文件是否存在
    if os.path.isfile(file_path):
        return await response.file(file_path)
    else:
        return jsonify(msg="文件不存在", status=404)


if __name__ == "__main__":
    cpu_count = multiprocessing.cpu_count()
    app.run(host="0.0.0.0", port=config["port"], workers=cpu_count * 2 + 1)
