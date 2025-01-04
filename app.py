from sanic import Sanic, Request, response
from sanic_ext import openapi as doc
from urllib.parse import urljoin
from functools import wraps
from db import db

import aiofiles
import os
import hashlib
import random
import math
import multiprocessing
from sanic.log import logger
import mjson
import json

config = json.load(open("config.json"))
Sanic.start_method = "fork"

app = Sanic(config["name"])

UPLOAD_FOLDER = os.path.abspath(os.environ.get("UPLOAD_FOLDER", config["upload_dir"]))
SECRET_KEY = config["appkey"]

app.config.FORWARDED_FOR_HEADER = "X-FORWARDED-FOR"
app.config["OAS_UI_DEFAULT"] = "swagger"
app.config["OAS_UI_REDOC"] = False
app.config.HEALTH = True
app.config.HEALTH_ENDPOINT = True
app.config.CORS_ORIGINS = "*"

app.ext.openapi.describe(config["name"], "2.4.6")


def jsonify(data=None, msg="OK", status=200):
    res = {"code": status, "message": msg, "data": data}
    return response.text(mjson.dumps(res), status=status)


async def save_file(file, filename):
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    async with aiofiles.open(filepath, "wb") as out_file:
        await out_file.write(file.body)
    return filepath


def appkey_required(view_func):
    @wraps(view_func)
    async def wrapped_view(request: Request, *args, **kwargs):

        head_T = request.args.get("appkey", None)
        if not head_T == SECRET_KEY:
            return jsonify(None, "无权限", 401)
        else:
            return await view_func(request, *args, **kwargs)

    return wrapped_view


@app.exception(Exception)
async def exc(request, exception):
    logger.error(f"Exception: {exception}", exc_info=True)
    return jsonify(msg="服务器出错", status=500)


@app.post("/api/upload")
@doc.exclude(True)
@appkey_required
async def upload_image(request: Request):
    if "image" not in request.files:
        return jsonify(msg="请求中没有文件部分", status=400)

    file = request.files["image"]
    file = file[0]
    if file.name == "":
        return jsonify(msg="没有选择文件", status=400)

    tags = request.form.get("tags", "")  # 获取标签数据

    # 确保上传目录存在
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

    # 确保文件名是安全的
    filename = file.name

    # 如果文件名已经存在，添加哈希值
    base, ext = os.path.splitext(filename)
    hashs = hashlib.md5()
    hashs.update(file.body)  # Read file content asynchronously
    filename = f"{hashs.hexdigest()}{ext}"

    filepath = await save_file(file, filename)

    # 插入图片信息到数据库
    new_image = db.add(filepath, tags)
    new_image = {
        "id": new_image["id"],
        "url": urljoin(
            request.host, app.url_for("get_image", image_id=str(new_image["id"]))
        ),
        "tags": new_image["tags"],
    }

    return jsonify(new_image, "上传成功", 201)


@app.get("/api/images")
async def get_images(request: Request):
    """
    带分页的图片获取
    openapi:
    ---
    parameters:
      - name: page
        in: query
        description: 页码
        required: true
        type: integer
      - name: all
        in: query
        description: 是否返回全部

    """
    page = int(request.args.get("page", 1))

    # 计算偏移量和限制数量
    offset = (page - 1) * 20

    # 连接数据库
    all_data = db.db.all()
    last = False

    # 判断是否为最后一页
    if math.ceil(len(all_data) / 20) <= page:
        last = True

    if request.args.get("all", None):
        all = all_data
        last = True
    else:
        data = all_data[offset : offset + 20]

    random.shuffle(data)
    image_list = [{"id": item["id"], "tags": item["tags"]} for item in data]

    # 返回分页结果
    return jsonify(
        {"total": len(image_list), "page": page, "images": image_list, "last": last}
    )


@app.get("/api/image/random")
async def random_image(request: Request):
    """
    获取随机图片
    openapi:
    ---
    parameters:
      - name: info
        in: query
        description: 是否只获取图片信息
        required: false

    """
    max_length = db.db.__len__()  # 获取最大id
    idx = random.randint(1, max_length)  # 随机选择
    image = db.get(idx)

    if request.args.get("info", "0") != 0:
        return jsonify({"id": image[0]["id"], "tags": image[0]["tags"]})

    filepath = os.path.join(UPLOAD_FOLDER, image[0]["path"])
    return await response.file_stream(filepath)  # 使用文件路径发送图片


@app.get("/api/image/<image_id:int>")
async def get_image(request: Request, image_id: int):
    """
    根据ID从数据库中获取图片（信息）
    openapi:
    ---
    parameters:
      - name: info
        in: query
        description: 是否只获取图片信息
        required: false
      - name: image_id
        in: path
        description: 图片id
        required: true
        type: integer

    """
    image = db.get(image_id)

    if len(image) >= 1:
        if request.args.get("info", "0") != "0":
            return jsonify({"id": image[0]["id"], "tags": image[0]["tags"]})

        filepath = os.path.join(UPLOAD_FOLDER, image[0]["path"])
        return await response.file_stream(filepath)  # 使用文件路径发送图片
    else:
        return jsonify(None, "图片未找到", 404)


@app.get("/api/image/tag")
async def get_image_by_tag(request: Request):
    """
    根据Tag获取图片
    openapi:
    ---
    parameters:
      - name: tag
        in: query
        description: 图片tag，以英文逗号分割
        required: false

    """
    tags = request.args.get("tag")
    tags = tags.split(",")
    ret = []
    for tag in tags:
        data = db.get_by_tag(tag)
        ret += [{"id": item["id"], "tags": item["tags"]} for item in data]
    return jsonify(
        {
            "total": len(ret),
            "images": ret,
        }
    )


# 删除指定ID图片的路由
@app.delete(
    "/api/image/<image_id:int>",
)
@doc.exclude(True)
@appkey_required
async def delete_image(request: Request, image_id):
    """
    删除指定图片
    """
    image = db.get(image_id)
    if len(image) >= 1:
        # 删除文件
        filepath = os.path.join(UPLOAD_FOLDER, image[0]["path"])

        if os.path.exists(filepath):
            if request.args.get("rmfile", "1") == "1":
                os.remove(filepath)
        # 删除数据库记录
        db.delete(image_id)
        return jsonify(None, "图片删除成功", 204)
    else:
        return jsonify(None, "图片未找到", 404)


@app.patch("/api/image/<img_id:int>")
@doc.exclude(True)
@appkey_required
def update_img(request: Request, img_id):
    """
    修改一张图片的tag
    """
    tags = request.args.get("tags", "").split(",")
    db.modify(img_id, tags)
    return jsonify(msg="完成")


@app.delete("/api/clear")
@doc.exclude(True)
@appkey_required
async def clear_cache(request: Request):
    """
    清除数据库缓存
    """
    db.db.clear_cache()
    return jsonify()


@app.route("/<path:path>", name="files")
@app.route("/", name="index")
@doc.exclude(True)
async def static_file(request: Request, path="/index.html"):
    # 构建请求的文件路径
    file_path = "files/" + path
    if ".." in file_path:
        return jsonify(msg="文件不存在", status=404)

    # 验证请求的文件路径确实是文件且存在
    if os.path.isfile(file_path):
        return await response.file(file_path)
    else:
        # 如果文件不存在，返回 404 错误
        return jsonify(msg="文件不存在", status=404)


if __name__ == "__main__":
    cpu_count = multiprocessing.cpu_count()

    app.run(host="0.0.0.0", port=config["port"], workers=cpu_count * 2 + 1)
