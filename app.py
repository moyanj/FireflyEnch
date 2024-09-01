from sanic import Sanic, Request, response
from sanic_cors import CORS
import os
import hashlib
from urllib.parse import urljoin
import random
import aiofiles
import math
import multiprocessing
from functools import wraps

from db import db

Sanic.start_method = 'fork'

app = Sanic('FireflyEnch')
CORS(app)
UPLOAD_FOLDER = os.path.abspath(os.environ.get("UPLOAD_FOLDER", "/mnt/data"))
SECRET_KEY = "ce4d82a91eeb6e2af36cd291d48f1de15d424417d2a6eb0778be51b9acf1f77eee3adc4df2d44555bfd79187c18daa4187ecd0c1477d2474da42be3ebc8c74e4"

app.config.FORWARDED_FOR_HEADER = 'X-FORWARDED-FOR'

def jsonify(data, status=200):
    return response.json(data, status=status)

async def save_file(file, filename):
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    async with aiofiles.open(filepath, 'wb') as out_file:
        await out_file.write(file.body)
    return filepath
    
def appkey_required(view_func):
    @wraps(view_func)
    def wrapped_view(request:Request, *args, **kwargs):

        head_T = request.args.get("appkey", None)
        if not head_T == SECRET_KEY:
            return jsonify({'code':403}, 403)
        else:
            return view_func(request, *args, **kwargs)

    return wrapped_view
        

@app.post('/api/upload')
@appkey_required
async def upload_image(request: Request):
    if "image" not in request.files:
        return jsonify({"error": "请求中没有文件部分"}, 400)

    file = request.files["image"]
    file = file[0]
    if file.name == "":
        return jsonify({"error": "没有选择文件"}, 400)

    tags = request.form.get("tags", "")  # 获取标签数据

    # 确保上传目录存在
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

    # 确保文件名是安全的
    filename = file.name

    # 如果文件名已经存在，添加哈希值
    base, ext = os.path.splitext(filename)
    hashs = hashlib.sha1()
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

    return jsonify({"message": "图片上传成功", "image": new_image}, 201)

@app.get("/api/images")
async def get_images(request: Request):
    page = int(request.args.get("page", 1))
    per_page = 20

    # 计算偏移量和限制数量
    offset = (page - 1) * per_page

    # 连接数据库
    all_data = db.db.all()
    last = False
    
    if math.ceil(len(all_data) / 20) <= page:
        last = True
        
    data = all_data[offset : offset + per_page]
    random.shuffle(data)
    image_list = []
    for item in data:
        items = {"id": item["id"], "tags": item["tags"]}
        image_list.append(items)
    # 返回分页结果
    return jsonify(
        {
            "total": len(image_list),
            "page": page,
            "per_page": per_page,
            "images": image_list,
            'last':last
        }
    )

@app.get("/api/image/<image_id:int>")
async def get_image(request: Request, image_id: int):
    # 根据ID从数据库中获取图片信息#
    image = db.get(image_id)
    if len(image) >= 1:
        filepath = os.path.join(UPLOAD_FOLDER, image[0]["path"])
        return await response.file(filepath)  # 使用文件路径发送图片
    else:
        return jsonify({"error": "图片未找到"}, 404)
       
@app.get("/api/image/tag")
async def get_image_by_tag(request: Request):
    tags = request.args.get("tag")
    tags = tags.split(',')
    ret = []
    for tag in tags:
        for item in db.get_by_tag(tag):
            items = {"id": item["id"], "tags": item["tags"]}
            ret.append(items)
    ret = list(set(ret))
    return jsonify(
        {
            "total": len(ret),
            "images": ret,
        }
    )

# 删除指定ID图片的路由
@app.delete("/api/image/<image_id:int>",)
@appkey_required
async def delete_image(request: Request, image_id):
    image = db.get(image_id)
    if len(image) >= 1:
        # 删除文件
        filepath = os.path.join(UPLOAD_FOLDER, image[0]["path"])

        if os.path.exists(filepath):
            if request.args.get('rmfile', '1') == '1':
                os.remove(filepath)
            try:
                os.remove(filepath + ".s")
            except:
                pass

        # 删除数据库记录
        db.delete(image_id)
        return jsonify({"message": "图片删除成功"})
    else:
        return jsonify({"error": "图片未找到"}, 404)

@app.route("/<path:path>")
@app.route('/', name='index')
async def static_file(request: Request, path="/index.html"):
   
    # 构建请求的文件路径
    file_path = 'files/' + path
    if ".." in file_path:
        return jsonify({'code':403})

    # 验证请求的文件路径确实是文件且存在
    if os.path.isfile(file_path):
        return await response.file(file_path)   
    else:
        # 如果文件不存在，返回 404 错误
        return jsonify({'code':404})

if __name__ == '__main__':
    cpu_count = multiprocessing.cpu_count()

    app.run(
        host='0.0.0.0',
        port=8896,
        workers=cpu_count*2+1
    )