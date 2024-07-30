from flask import Flask, jsonify, request, send_file, url_for, abort, redirect
from flask_cors import CORS
from flask_caching import Cache
import os
from db import db
import hashlib
import time
from urllib.parse import urljoin
from functools import wraps
from base64 import b64encode, b64decode
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)

DATABASE = 'db.json'
UPLOAD_FOLDER = os.path.abspath(os.environ.get('UPLOAD_FLODER','uploads('))
SECRET_KEY = 'ce4d82a91eeb6e2af36cd291d48f1de15d424417d2a6eb0778be51b9acf1f77eee3adc4df2d44555bfd79187c18daa4187ecd0c1477d2474da42be3ebc8c74e4'
config = {
    "CACHE_TYPE": "FileSystemCache",  # Flask-Caching related configs
    "CACHE_DEFAULT_TIMEOUT": 172800,
    "CACHE_DIR": "./cache",
}
app.config.from_mapping(config)
cache = Cache(app)


def gen_key(route, sk):
    salt = str(int(time.time()))
    data = salt + route + salt
    data += sk

    hashed = hashlib.sha256(data.encode('utf-8')).hexdigest()
    encoded_t = b64encode(salt.encode()).decode('utf-8')

    return hashed + '.' + encoded_t

def verify(key, route, sk):
    o_hashed, t = key.split('.')
    
    t = b64decode(t).decode('utf-8')
    salt = t
    
    data = salt + route + salt
    data += sk

    hashed = hashlib.sha256(data.encode('utf-8')).hexdigest()
    
    return hashed == o_hashed

def appkey_required(view_func):
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):

        head_T = request.args.get("appkey", None)
        if verify(head_T, request.path, SECRET_KEY):
            return abort(403)
        else:
            return view_func(*args, **kwargs)

    return wrapped_view

# 上传图片的路由
@app.route('/api/upload', methods=['POST'])
@appkey_required
def upload_image():
    if 'image' not in request.files:
        return jsonify({'error': '请求中没有文件部分'}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400
    
    tags = request.form.get('tags', '')  # 获取标签数据

    # 确保上传目录存在
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

    # 确保文件名是安全的
    filename = secure_filename(file.filename)
    
    # 如果文件名已经存在，添加哈希值
    base, ext = os.path.splitext(filename)
    hashs = hashlib.sha1()
    hashs.update(file.read())
    filename = f'{hashs.hexdigest()}{ext}'
    
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.seek(0)
    file.save(filepath)
    
    # 插入图片信息到数据库
    new_image = db.add(filepath, tags)
    new_image = {
        'id': new_image['id'],
        'url': urljoin(request.host_url,url_for('get_image', image_id=new_image['id'])),
        'tags': new_image['tags']
    }
    
    return jsonify({'message': '图片上传成功', 'image': new_image}), 201

# 获取图片的路由（带分页）
@app.route('/api/images', methods=['GET'])
@cache.cached(timeout=3600)
def get_images():
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per', 10))
    
    # 计算偏移量和限制数量
    offset = (page - 1) * per_page
    
    # 连接数据库
    
    all_data = db.db.all()
    data = all_data[offset:offset + per_page]
    image_list = []
    for item in data:
        items = {
            'url':urljoin(request.host_url, url_for('get_image',image_id=item['id'])),
            'id':item['id'],
            'tags':item['tags']
        }
        image_list.append(items)
    # 返回分页结果
    return jsonify({
        'total': len(image_list),
        'page': page,
        'per_page': per_page,
        'images': image_list
    })

# 获取指定ID图片的路由
@app.route('/api/image/<int:image_id>', methods=['GET'])
def get_image(image_id):
    # 根据ID从数据库中获取图片信息
    image = db.get(image_id)
    
    if len(image) >= 1:
        filepath = os.path.join(UPLOAD_FOLDER, image[0]['path'])
        return send_file(filepath)  # 使用文件路径发送图片
    else:
        return jsonify({'error': '图片未找到'}), 404

@app.route('/api/image/tag')
@cache.cached(timeout=3600)
def get_image_by_tag():
    tag = request.args.get('tag')
    ret = []
    for item in db.get_by_tag(tag):
        items = {
            'url':urljoin(request.host_url, url_for('get_image',image_id=item['id'])),
            'id':item['id'],
            'tags':item['tags']
        }
        ret.append(items)
    return jsonify(ret)
    
# 删除指定ID图片的路由
@app.route('/api/image/<int:image_id>', methods=['DELETE'])
@appkey_required
def delete_image(image_id):
    image = db.get(image_id)
    if len(image) >= 1:
        # 删除文件
        filepath = os.path.join(UPLOAD_FOLDER, image[0]['path'])
        if os.path.exists(filepath):
            os.remove(filepath)
        
        # 删除数据库记录
        db.delete(image_id)
        return jsonify({'message': '图片删除成功'}), 200
    else:
        return jsonify({'error': '图片未找到'}), 404

@app.route('/api/clear')
@appkey_required
def clear():
    cache.clear()
    return jsonify({'message':'清空完毕'})

@app.route('/')
def index():
    return redirect(url_for('static_file',filename='index.html'))

@app.route('/<path:filename>')
def static_file(filename):
    path = filename
    # 构建请求的文件路径
    file_path = os.path.join(app.root_path, 'files',path)
    if '..' in file_path:
        return abort(403)
        
    # 验证请求的文件路径确实是文件且存在
    if os.path.isfile(file_path):
        # 使用 Flask 的 send_file 函数安全地发送文件
        return send_file(file_path)
    else:
        # 如果文件不存在，返回 404 错误
        abort(404)
        
if __name__ == '__main__':
    app.run(debug=True)