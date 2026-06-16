"""FireflyEnch 主应用模块"""

import asyncio
from io import BytesIO
import json
import os
import random
import re
import time
import uuid
import hashlib
import multiprocessing
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any, TypedDict

import aiofiles
import httpx
import uvicorn
from fastapi import (
    FastAPI,
    UploadFile,
    File,
    Form,
    HTTPException,
    Depends,
    Query,
    Request,
    Header,
)

from PIL import Image as PILImage
from fastapi.responses import JSONResponse, FileResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from captcha.image import ImageCaptcha
from tortoise.contrib.fastapi import RegisterTortoise

# 导入应用配置
from config import (
    AI_API_KEY,
    AI_BASE_URL,
    AI_ENABLED,
    AI_MAX_TAGS,
    AI_MODEL,
    AI_PROMPT,
    AI_TIMEOUT_SECONDS,
    APP_NAME,
    APP_PORT,
    CAPTCHA_EXPIRE_SECONDS,
    CAPTCHA_LENGTH,
    PAGE_SIZE,
    PREPARED_UPLOAD_EXPIRE_SECONDS,
    SECRET_KEY,
    THUMBNAIL_FOLDER,
    THUMBNAIL_SIZE,
    TORTOISE_ORM,
    UPLOAD_FOLDER,
    TEMP_UPLOAD_FOLDER,
)

# 导入数据模型和工具函数
from models import Image
from utils import (
    build_public_image_url,
    cleanup_expired_prepared_uploads,
    compute_hash,
    create_thumbnail_base64,
    get_safe_path,
    normalize_tags,
    parse_tags,
)

# ==================== 内存存储 ====================

# 验证码存储（captcha_id -> {code, expire}）
captcha_store: Dict[str, Dict[str, Any]] = {}


class PreparedUpload(TypedDict):
    """预上传文件信息"""

    token: str
    temp_filename: str
    original_filename: str
    created_at: float


# 预上传文件存储（token -> PreparedUpload）
prepared_uploads: Dict[str, PreparedUpload] = {}


# ==================== 应用生命周期 ====================


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理：启动时创建必要目录，初始化数据库"""
    asyncio.create_task(
        cleanup_expired_prepared_uploads(
            prepared_uploads, TEMP_UPLOAD_FOLDER, PREPARED_UPLOAD_EXPIRE_SECONDS
        )
    )
    async with RegisterTortoise(
        app,
        config=TORTOISE_ORM,
        generate_schemas=True,
    ):
        yield


# ==================== 创建 FastAPI 应用 ====================

app = FastAPI(
    title=APP_NAME,
    version="2.5.0",
    description="FireflyEnch - 简单的图片画廊系统",
    lifespan=lifespan,
)

# CORS 中间件：允许跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== 工具函数 ====================


def jsonify(
    data: Optional[Dict[str, Any]] = None, msg: str = "OK", status: int = 200
) -> JSONResponse:
    """统一 JSON 响应格式：{code, message, data}"""
    return JSONResponse(
        content={"code": status, "message": msg, "data": data}, status_code=status
    )


def generate_captcha_code(length: int = CAPTCHA_LENGTH) -> str:
    """生成随机验证码（排除易混淆字符 I/O/0/1）"""
    chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "".join(random.choices(chars, k=length))


def generate_captcha_image(code: str) -> bytes:
    """使用 captcha 库生成验证码图片"""
    image_captcha = ImageCaptcha(width=120, height=40)
    return image_captcha.generate(code).getvalue()


async def save_file(
    content: bytes, filename: str, base_dir: Optional[str] = None
) -> str:
    """异步保存文件到指定目录，返回文件完整路径"""
    target_dir = base_dir or UPLOAD_FOLDER
    os.makedirs(target_dir, exist_ok=True)
    filepath = os.path.join(target_dir, filename)
    async with aiofiles.open(filepath, "wb") as out_file:
        await out_file.write(content)
    return filepath


def get_thumbnail_path(filename: str) -> str:
    """获取缩略图路径（WebP 格式）"""
    stem, _ = os.path.splitext(filename)
    return os.path.join(THUMBNAIL_FOLDER, f"{stem}.webp")


async def ensure_thumbnail(filename: str) -> str:
    """确保缩略图存在且是最新的，不存在或过期则重新生成"""
    source_path = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(source_path):
        raise HTTPException(status_code=404, detail="图片文件不存在")

    thumbnail_path = get_thumbnail_path(filename)
    # 缩略图已存在且比原图新，直接返回
    if os.path.exists(thumbnail_path) and os.path.getmtime(
        thumbnail_path
    ) >= os.path.getmtime(source_path):
        return thumbnail_path

    # 生成缩略图
    try:
        async with aiofiles.open(source_path, "rb") as f:
            image = await f.read()
            image = PILImage.open(BytesIO(image))
            image = image.convert("RGB")
            image.thumbnail(THUMBNAIL_SIZE)

            thumbnail_dir = os.path.dirname(thumbnail_path)
            os.makedirs(thumbnail_dir, exist_ok=True)

            image.save(
                thumbnail_path,
                format="WEBP",
                quality=85,
                method=6,
            )
    except OSError as exc:
        raise HTTPException(status_code=400, detail="无法生成缩略图") from exc

    return thumbnail_path


async def is_image_file(filename: str) -> bool:
    """检查文件是否为有效的图片文件"""
    source_path = os.path.join(UPLOAD_FOLDER, filename)
    try:

        async with aiofiles.open(source_path, "rb") as f:
            image = await f.read()
            PILImage.open(BytesIO(image))
            return True
    except OSError:
        return False


# ==================== AI 自动标签 ====================


async def generate_ai_tags(content: bytes, filename: str) -> list[str]:
    """调用 AI 服务自动提取图片标签（传缩略图以减少数据量）"""
    if not AI_ENABLED:
        return []

    if not AI_API_KEY or not AI_MODEL or not AI_BASE_URL:
        raise HTTPException(status_code=500, detail="AI 配置不完整")

    # 生成缩略图的 base64
    data_url = create_thumbnail_base64(content)

    # 构建请求 payload
    payload = {
        "model": AI_MODEL,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": AI_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": f"文件名：{filename}"},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ],
            },
        ],
    }

    headers = {
        "Authorization": f"Bearer {AI_API_KEY}",
        "Content-Type": "application/json",
    }

    # 调用 AI API
    async with httpx.AsyncClient(timeout=AI_TIMEOUT_SECONDS) as client:
        response = await client.post(
            f"{AI_BASE_URL.rstrip('/')}/chat/completions",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()

    # 解析响应，提取标签
    body = response.json()
    content_text = body.get("choices", [{}])[0].get("message", {}).get("content", "")
    return extract_ai_tags(content_text)[:AI_MAX_TAGS]


def extract_ai_tags(content_text: str) -> list[str]:
    """从 AI 响应文本中提取标签列表"""
    # 尝试解析 JSON 格式
    try:
        parsed = json.loads(content_text)
    except json.JSONDecodeError:
        parsed = None

    # 如果是 JSON 对象且包含 tags 字段
    if isinstance(parsed, dict):
        tags = parsed.get("tags", [])
        if isinstance(tags, list):
            return normalize_tags([str(tag) for tag in tags])

    # 回退：按空白字符分割并过滤
    tokens = [
        part.strip("[](),:;，。！？")
        for part in re.split(r"\s+", content_text)
        if part.strip("[](),:;，。！？")
    ]
    tags = [
        token
        for token in tokens
        if len(token) <= 32 and re.search(r"[\u4e00-\u9fffA-Za-z]", token)
    ]
    return normalize_tags(tags)


# ==================== 认证依赖 ====================


async def verify_appkey(
    x_api_key: Optional[str] = Header(None),
    appkey: Optional[str] = Query(None),
) -> bool:
    """API 密钥验证（支持 Header 和 Query 两种方式）"""
    candidate = x_api_key or appkey
    if candidate != SECRET_KEY:
        raise HTTPException(status_code=401, detail="无权限")
    return True


# ==================== 上传处理 ====================


async def finalize_upload(
    request: Request,
    content: bytes,
    original_filename: str,
    tags: list[str],
) -> JSONResponse:
    """完成图片上传：检查重复、保存文件、创建数据库记录"""
    base, ext = os.path.splitext(original_filename)
    if not ext:
        ext = ".png"

    # 检查图片是否重复（基于感知哈希）
    img_hash = compute_hash(content)
    duplicate = await Image.check_duplicate(*img_hash)
    if duplicate:
        raise HTTPException(status_code=409, detail=f"疑似重复图片: {duplicate}")

    # 保存文件（以 MD5 哈希命名）
    filename = f"{hashlib.sha1(content).hexdigest()}{ext.lower()}"
    await save_file(content, filename)
    new_image = await Image.create_image(filename, normalize_tags(tags), img_hash)

    result = {
        "id": new_image.id,
        "url": build_public_image_url(str(request.base_url), new_image.id),
        "tags": new_image.tags,
    }
    return jsonify(result, "上传成功", 201)


# ==================== API 路由：认证 ====================


@app.get("/api/captcha")
async def get_captcha() -> Response:
    """获取验证码图片，返回图片二进制和 captcha_id（通过 X-Captcha-Id 头）"""
    captcha_id = hashlib.md5(f"{time.time()}{random.random()}".encode()).hexdigest()
    code = generate_captcha_code()

    # 存储验证码（带过期时间）
    captcha_store[captcha_id] = {
        "code": code.upper(),
        "expire": time.time() + CAPTCHA_EXPIRE_SECONDS,
    }

    # 清理过期验证码
    expired_ids = [k for k, v in captcha_store.items() if v["expire"] < time.time()]
    for cid in expired_ids:
        del captcha_store[cid]

    image_bytes = generate_captcha_image(code)

    return Response(
        content=image_bytes,
        media_type="image/png",
        headers={"X-Captcha-Id": captcha_id},
    )


@app.post("/api/login")
async def login(
    appkey: str = Form(...),
    captcha: str = Form(...),
    captcha_id: str = Form(...),
) -> JSONResponse:
    """登录验证：校验验证码和密钥，返回 token"""
    # 验证验证码
    if captcha_id not in captcha_store:
        raise HTTPException(status_code=400, detail="验证码已过期，请重新获取")

    stored_captcha = captcha_store[captcha_id]
    if stored_captcha["expire"] < time.time():
        del captcha_store[captcha_id]
        raise HTTPException(status_code=400, detail="验证码已过期，请重新获取")

    if stored_captcha["code"] != captcha.upper():
        del captcha_store[captcha_id]
        raise HTTPException(status_code=400, detail="验证码错误")

    del captcha_store[captcha_id]

    # 验证密钥
    if appkey != SECRET_KEY:
        raise HTTPException(status_code=401, detail="密码错误")

    # 生成 token
    token = hashlib.sha256(f"{appkey}{time.time()}".encode()).hexdigest()
    return jsonify({"token": token}, "登录成功")


# ==================== API 路由：图片上传 ====================


@app.post("/api/images/prepare")
async def prepare_image_upload(
    image: UploadFile = File(...),
    _: bool = Depends(verify_appkey),
) -> JSONResponse:
    """预上传图片：保存临时文件，供后续确认提交"""
    if not image.filename:
        raise HTTPException(status_code=400, detail="没有选择文件")

    content = await image.read()
    if not content:
        raise HTTPException(status_code=400, detail="图片内容为空")

    # 获取文件扩展名
    filename: str = image.filename or "unknown"
    _base, ext = os.path.splitext(filename)
    if not ext:
        ext = ".png"

    # 保存到临时目录
    token = uuid.uuid4().hex
    temp_filename = f"{token}{ext.lower()}"
    await save_file(content, temp_filename, TEMP_UPLOAD_FOLDER)

    # 记录预上传信息
    prepared_uploads[token] = {
        "token": token,
        "temp_filename": temp_filename,
        "original_filename": image.filename,
        "created_at": time.time(),
    }

    return jsonify({"upload_token": token})


@app.post("/api/images/suggest-tags")
async def suggest_image_tags(
    image: UploadFile = File(...),
    _: bool = Depends(verify_appkey),
) -> JSONResponse:
    """为图片生成 AI 建议标签，不参与上传流程"""
    if not image.filename:
        raise HTTPException(status_code=400, detail="没有选择文件")

    content = await image.read()
    if not content:
        raise HTTPException(status_code=400, detail="图片内容为空")

    suggested_tags: list[str] = []
    if AI_ENABLED:
        try:
            suggested_tags = await generate_ai_tags(content, image.filename)
        except (httpx.HTTPError, HTTPException, ValueError):
            suggested_tags = []

    return jsonify({"suggested_tags": suggested_tags})


@app.post("/api/images/commit")
async def commit_prepared_upload(
    request: Request,
    upload_token: str = Form(...),
    tags: str = Form(""),
    _: bool = Depends(verify_appkey),
) -> JSONResponse:
    """提交预上传：确认标签并完成图片入库"""

    prepared = prepared_uploads.pop(upload_token, None)
    if not prepared:
        raise HTTPException(status_code=404, detail="临时上传不存在或已过期")

    temp_path = os.path.join(TEMP_UPLOAD_FOLDER, prepared["temp_filename"])
    if not os.path.exists(temp_path):
        raise HTTPException(status_code=404, detail="临时图片文件不存在")

    async with aiofiles.open(temp_path, "rb") as file:
        content = await file.read()

    try:
        response = await finalize_upload(
            request,
            content,
            prepared["original_filename"],
            parse_tags(tags),
        )
    finally:
        # 清理临时文件
        if os.path.exists(temp_path):
            os.remove(temp_path)

    return response


@app.post("/api/images")
async def upload_image(
    request: Request,
    image: UploadFile = File(...),
    tags: str = Form(""),
    _: bool = Depends(verify_appkey),
) -> JSONResponse:
    """直接上传图片（跳过预上传流程）"""
    if not image.filename:
        raise HTTPException(status_code=400, detail="没有选择文件")

    content = await image.read()
    return await finalize_upload(request, content, image.filename, parse_tags(tags))


# ==================== API 路由：图片查询 ====================


@app.get("/api/images")
async def get_images(
    page: int = Query(1, ge=1),
    tag: Optional[str] = Query(None, description="标签列表，逗号分隔"),
) -> JSONResponse:
    """获取图片列表（支持标签筛选和分页）"""
    if tag:
        # 按标签筛选
        tag_list = parse_tags(tag)
        images = await Image.get_by_tags(tag_list)
        images = [img for img in images if is_image_file(img.filename)]
        return jsonify(
            {"total": len(images), "images": [img.to_dict() for img in images]}
        )

    # 分页查询
    result = await Image.get_all(page=page, page_size=PAGE_SIZE)
    if result["images"]:
        # 过滤无效文件并随机打乱
        result["images"] = [
            img for img in result["images"] if is_image_file(img["filename"])
        ]
        random.shuffle(result["images"])
    return jsonify(result)


@app.get("/api/images/random")
async def random_image():
    """获取随机一张图片"""
    image = await Image.get_random()
    if not image:
        raise HTTPException(status_code=404, detail="没有图片")
    return jsonify(image.to_dict())


@app.get("/api/images/{image_id}")
async def get_image(image_id: int):
    """获取图片详情"""
    image = await Image.get_by_id(image_id)
    if not image:
        raise HTTPException(status_code=404, detail="图片未找到")
    return jsonify(image.to_dict())


@app.get("/api/images/{image_id}/file")
async def get_image_file(image_id: int):
    """获取图片原图文件"""
    image = await Image.get_by_id(image_id)
    if not image:
        raise HTTPException(status_code=404, detail="图片未找到")

    filepath = os.path.join(UPLOAD_FOLDER, image.filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="图片文件不存在")
    return FileResponse(filepath)


@app.get("/api/images/{image_id}/thumbnail")
async def get_image_thumbnail(image_id: int):
    """获取图片缩略图（WebP 格式）"""
    image = await Image.get_by_id(image_id)
    if not image:
        raise HTTPException(status_code=404, detail="图片未找到")
    if not is_image_file(image.filename):
        raise HTTPException(status_code=404, detail="图片文件不存在")

    thumbnail_path = await ensure_thumbnail(image.filename)
    return FileResponse(thumbnail_path, media_type="image/webp")


# ==================== API 路由：图片管理 ====================


@app.delete("/api/images/{image_id}")
async def delete_image(
    image_id: int,
    _: bool = Depends(verify_appkey),
) -> JSONResponse:
    """删除图片（同时删除缩略图）"""
    image = await Image.get_by_id(image_id)
    if not image:
        raise HTTPException(status_code=404, detail="图片未找到")

    # 删除原图
    filepath = os.path.join(UPLOAD_FOLDER, image.filename)
    if os.path.exists(filepath):
        os.remove(filepath)
    # 删除缩略图
    thumbnail_path = get_thumbnail_path(image.filename)
    if os.path.exists(thumbnail_path):
        os.remove(thumbnail_path)

    await Image.delete_image(image_id)
    return jsonify(None, "图片删除成功", 204)


@app.patch("/api/images/{image_id}")
async def update_image_tags(
    image_id: int,
    tags: str = Query("", description="新标签列表，逗号分隔"),
    _: bool = Depends(verify_appkey),
) -> JSONResponse:
    """更新图片标签"""
    success = await Image.update_tags(image_id, parse_tags(tags))
    if success:
        return jsonify(msg="完成")
    raise HTTPException(status_code=404, detail="图片未找到")


@app.delete("/api/cache")
async def clear_cache(_: bool = Depends(verify_appkey)) -> JSONResponse:
    """清除缓存（预留接口）"""
    return jsonify()


# ==================== 静态文件（放在最后） ====================


@app.get("/{path:path}")
async def static_file(path: str) -> FileResponse:
    """静态文件服务（前端 SPA）"""
    file_path = get_safe_path("files", path)
    if not file_path or not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="文件不存在")
    return FileResponse(file_path)


# ==================== 启动入口 ====================


def main():
    """启动应用"""
    multiprocessing.cpu_count()
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=APP_PORT,
        reload=False,
    )


if __name__ == "__main__":
    main()
