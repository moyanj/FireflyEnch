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
from fastapi.responses import JSONResponse, FileResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, Dict, Any, TypedDict
from contextlib import asynccontextmanager
import aiofiles
import hashlib
import multiprocessing
import os
import random
import re
import time
import uuid

import httpx
import uvicorn
from captcha.image import ImageCaptcha
from tortoise.contrib.fastapi import RegisterTortoise

# 导入tortoise-orm
import config as app_config
from models import Image
from utils import (
    build_public_image_url,
    cleanup_expired_prepared_uploads,
    compute_hash,
    compute_perceptual_hash,
    compute_quick_hash,
    get_safe_path,
    normalize_tags,
    parse_tags,
    phash_distance,
)

# 配置常量
UPLOAD_FOLDER = os.path.abspath(
    os.environ.get("UPLOAD_FOLDER", app_config.UPLOAD_DIR) or app_config.UPLOAD_DIR
)
SECRET_KEY = app_config.APP_KEY
PAGE_SIZE = 20
THUMBNAIL_SIZE = (640, 640)
THUMBNAIL_FOLDER = os.path.join(UPLOAD_FOLDER, ".thumbs")
TEMP_UPLOAD_FOLDER = os.path.join(UPLOAD_FOLDER, ".prepared")
PREPARED_UPLOAD_EXPIRE_SECONDS = 1800
PHASH_DUPLICATE_THRESHOLD = 6

AI_CONFIG = {
    "enabled": app_config.AI_ENABLED,
    "base_url": app_config.AI_BASE_URL,
    "api_key": app_config.AI_API_KEY,
    "model": app_config.AI_MODEL,
    "timeout_seconds": app_config.AI_TIMEOUT_SECONDS,
    "max_tags": app_config.AI_MAX_TAGS,
    "prompt": app_config.AI_PROMPT,
}
AI_TIMEOUT_SECONDS = app_config.AI_TIMEOUT_SECONDS
AI_MAX_TAGS = app_config.AI_MAX_TAGS
AI_DEFAULT_PROMPT = app_config.AI_PROMPT

CAPTCHA_LENGTH = 4
CAPTCHA_EXPIRE_SECONDS = 300
# 验证码配置
captcha_store: Dict[str, Dict[str, Any]] = {}


class PreparedUpload(TypedDict):
    token: str
    temp_filename: str
    original_filename: str
    created_at: float
    suggested_tags: list[str]


prepared_uploads: Dict[str, PreparedUpload] = {}

# Tortoise-ORM配置
TORTOISE_ORM = {
    "connections": {"default": "sqlite://db/images.db"},
    "apps": {
        "models": {
            "models": ["models", "aerich.models"],
            "default_connection": "default",
        }
    },
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(THUMBNAIL_FOLDER, exist_ok=True)
    os.makedirs(TEMP_UPLOAD_FOLDER, exist_ok=True)
    async with RegisterTortoise(
        app,
        config=TORTOISE_ORM,
        generate_schemas=True,
    ):
        yield


# 创建FastAPI应用
app = FastAPI(
    title=app_config.APP_NAME,
    version="2.5.0",
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


def jsonify(
    data: Optional[Dict[str, Any]] = None, msg: str = "OK", status: int = 200
) -> JSONResponse:
    """统一JSON响应格式"""
    return JSONResponse(
        content={"code": status, "message": msg, "data": data}, status_code=status
    )


def generate_captcha_code(length: int = CAPTCHA_LENGTH) -> str:
    """生成随机验证码"""
    chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "".join(random.choices(chars, k=length))


def generate_captcha_image(code: str) -> bytes:
    """使用 captcha 库生成验证码图片"""
    image_captcha = ImageCaptcha(width=120, height=40)
    return image_captcha.generate(code).getvalue()


async def save_file(
    content: bytes, filename: str, base_dir: Optional[str] = None
) -> str:
    """异步保存文件"""
    target_dir = base_dir or UPLOAD_FOLDER
    os.makedirs(target_dir, exist_ok=True)
    filepath = os.path.join(target_dir, filename)
    async with aiofiles.open(filepath, "wb") as out_file:
        await out_file.write(content)
    return filepath


def get_thumbnail_path(filename: str) -> str:
    stem, _ = os.path.splitext(filename)
    return os.path.join(THUMBNAIL_FOLDER, f"{stem}.webp")


def ensure_thumbnail(filename: str) -> str:
    source_path = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(source_path):
        raise HTTPException(status_code=404, detail="图片文件不存在")

    thumbnail_path = get_thumbnail_path(filename)
    if os.path.exists(thumbnail_path) and os.path.getmtime(
        thumbnail_path
    ) >= os.path.getmtime(source_path):
        return thumbnail_path

    try:
        from PIL import Image as PILImage

        with PILImage.open(source_path) as image:
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


def is_image_file(filename: str) -> bool:
    source_path = os.path.join(UPLOAD_FOLDER, filename)
    try:
        from PIL import Image as PILImage

        with PILImage.open(source_path):
            return True
    except OSError:
        return False


async def generate_ai_tags(content: bytes, filename: str) -> list[str]:
    if not AI_CONFIG.get("enabled"):
        return []

    api_key = AI_CONFIG.get("api_key")
    model = AI_CONFIG.get("model")
    base_url = AI_CONFIG.get("base_url")
    if not api_key or not model or not base_url:
        raise HTTPException(status_code=500, detail="AI 配置不完整")

    prompt = AI_CONFIG.get("prompt") or AI_DEFAULT_PROMPT
    data_url = "data:image/png;base64," + __import__("base64").b64encode(
        content
    ).decode("ascii")

    payload = {
        "model": model,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": prompt},
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
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=AI_TIMEOUT_SECONDS) as client:
        response = await client.post(
            f"{base_url.rstrip('/')}/chat/completions",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()

    body = response.json()
    content_text = body.get("choices", [{}])[0].get("message", {}).get("content", "")
    return extract_ai_tags(content_text)[:AI_MAX_TAGS]


def extract_ai_tags(content_text: str) -> list[str]:
    try:
        parsed = json.loads(content_text)
    except json.JSONDecodeError:
        parsed = None

    if isinstance(parsed, dict):
        tags = parsed.get("tags", [])
        if isinstance(tags, list):
            return normalize_tags([str(tag) for tag in tags])

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


async def verify_appkey(
    x_api_key: Optional[str] = Header(None),
    appkey: Optional[str] = Query(None),
) -> bool:
    """API密钥验证"""
    candidate = x_api_key or appkey
    if candidate != SECRET_KEY:
        raise HTTPException(status_code=401, detail="无权限")
    return True


async def finalize_upload(
    request: Request,
    content: bytes,
    original_filename: str,
    tags: list[str],
) -> JSONResponse:
    base, ext = os.path.splitext(original_filename)
    if not ext:
        ext = ".png"

    img_hash = compute_hash(content)
    duplicate = await Image.check_duplicate(*img_hash)
    if duplicate:
        raise HTTPException(status_code=409, detail=f"疑似重复图片: {duplicate}")

    filename = f"{hashlib.md5(content).hexdigest()}{ext.lower()}"
    await save_file(content, filename)
    new_image = await Image.create_image(filename, normalize_tags(tags), img_hash)

    result = {
        "id": new_image.id,
        "url": build_public_image_url(str(request.base_url), new_image.id),
        "tags": new_image.tags,
    }
    return jsonify(result, "上传成功", 201)


# ========== API 路由 ==========


@app.get("/api/captcha")
async def get_captcha() -> Response:
    """获取验证码图片"""
    captcha_id = hashlib.md5(f"{time.time()}{random.random()}".encode()).hexdigest()
    code = generate_captcha_code()

    captcha_store[captcha_id] = {
        "code": code.upper(),
        "expire": time.time() + CAPTCHA_EXPIRE_SECONDS,
    }

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
    """登录验证"""
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

    if appkey != SECRET_KEY:
        raise HTTPException(status_code=401, detail="密码错误")

    token = hashlib.sha256(f"{appkey}{time.time()}".encode()).hexdigest()
    return jsonify({"token": token}, "登录成功")


@app.post("/api/images/prepare")
async def prepare_image_upload(
    image: UploadFile = File(...),
    _: bool = Depends(verify_appkey),
) -> JSONResponse:
    if not image.filename:
        raise HTTPException(status_code=400, detail="没有选择文件")

    cleanup_expired_prepared_uploads(
        prepared_uploads,
        TEMP_UPLOAD_FOLDER,
        PREPARED_UPLOAD_EXPIRE_SECONDS,
    )

    content = await image.read()
    if not content:
        raise HTTPException(status_code=400, detail="图片内容为空")

    _, ext = os.path.splitext(image.filename)
    if not ext:
        ext = ".png"

    token = uuid.uuid4().hex
    temp_filename = f"{token}{ext.lower()}"
    await save_file(content, temp_filename, TEMP_UPLOAD_FOLDER)

    suggested_tags: list[str] = []
    if AI_CONFIG.get("enabled"):
        try:
            suggested_tags = await generate_ai_tags(content, image.filename)
        except (httpx.HTTPError, HTTPException, ValueError):
            suggested_tags = []

    prepared_uploads[token] = {
        "token": token,
        "temp_filename": temp_filename,
        "original_filename": image.filename,
        "created_at": time.time(),
        "suggested_tags": suggested_tags,
    }

    return jsonify(
        {
            "upload_token": token,
            "suggested_tags": suggested_tags,
        }
    )


@app.post("/api/images/commit")
async def commit_prepared_upload(
    request: Request,
    upload_token: str = Form(...),
    tags: str = Form(""),
    _: bool = Depends(verify_appkey),
) -> JSONResponse:
    cleanup_expired_prepared_uploads(
        prepared_uploads,
        TEMP_UPLOAD_FOLDER,
        PREPARED_UPLOAD_EXPIRE_SECONDS,
    )

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
    if not image.filename:
        raise HTTPException(status_code=400, detail="没有选择文件")

    content = await image.read()
    return await finalize_upload(request, content, image.filename, parse_tags(tags))


@app.get("/api/images")
async def get_images(
    page: int = Query(1, ge=1),
    tag: Optional[str] = Query(None, description="标签列表，逗号分隔"),
) -> JSONResponse:
    if tag:
        tag_list = parse_tags(tag)
        images = await Image.get_by_tags(tag_list)
        images = [img for img in images if is_image_file(img.filename)]
        return jsonify(
            {"total": len(images), "images": [img.to_dict() for img in images]}
        )

    result = await Image.get_all(page=page, page_size=PAGE_SIZE)
    if result["images"]:
        result["images"] = [img for img in result["images"] if is_image_file(img["filename"])]
        random.shuffle(result["images"])
    return jsonify(result)


@app.get("/api/images/random")
async def random_image():
    image = await Image.get_random()
    if not image:
        raise HTTPException(status_code=404, detail="没有图片")
    return jsonify(image.to_dict())


@app.get("/api/images/{image_id}")
async def get_image(image_id: int):
    image = await Image.get_by_id(image_id)
    if not image:
        raise HTTPException(status_code=404, detail="图片未找到")
    return jsonify(image.to_dict())


@app.get("/api/images/{image_id}/file")
async def get_image_file(image_id: int):
    image = await Image.get_by_id(image_id)
    if not image:
        raise HTTPException(status_code=404, detail="图片未找到")

    filepath = os.path.join(UPLOAD_FOLDER, image.filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="图片文件不存在")
    return FileResponse(filepath)


@app.get("/api/images/{image_id}/thumbnail")
async def get_image_thumbnail(image_id: int):
    image = await Image.get_by_id(image_id)
    if not image:
        raise HTTPException(status_code=404, detail="图片未找到")
    if not is_image_file(image.filename):
        raise HTTPException(status_code=404, detail="图片文件不存在")

    thumbnail_path = ensure_thumbnail(image.filename)
    return FileResponse(thumbnail_path, media_type="image/webp")


@app.delete("/api/images/{image_id}")
async def delete_image(
    image_id: int,
    _: bool = Depends(verify_appkey),
) -> JSONResponse:
    image = await Image.get_by_id(image_id)
    if not image:
        raise HTTPException(status_code=404, detail="图片未找到")

    filepath = os.path.join(UPLOAD_FOLDER, image.filename)
    if os.path.exists(filepath):
        os.remove(filepath)
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
    success = await Image.update_tags(image_id, parse_tags(tags))
    if success:
        return jsonify(msg="完成")
    raise HTTPException(status_code=404, detail="图片未找到")


@app.delete("/api/cache")
async def clear_cache(_: bool = Depends(verify_appkey)) -> JSONResponse:
    return jsonify()


# ========== 静态文件（放在最后） ==========


@app.get("/{path:path}")
async def static_file(path: str) -> FileResponse:
    file_path = get_safe_path("files", path)
    if not file_path or not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="文件不存在")
    return FileResponse(file_path)


def main():
    """启动应用"""
    multiprocessing.cpu_count()
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=app_config.APP_PORT,
        reload=False,
    )


if __name__ == "__main__":
    main()
