"""FireflyEnch 应用配置"""

import os

# ==================== 基础配置 ====================

# 应用名称
APP_NAME = "FireflyEnch"

# 服务端口
APP_PORT = 8896

# 应用密钥（用于 API 认证）
APP_KEY = "12345678"

# ==================== 存储配置 ====================

DATA_PATH = os.path.abspath("./data")

# 图片上传目录
UPLOAD_FOLDER = os.path.join(DATA_PATH, "uploads")

# 数据库文件
DB_FILE = os.path.join(DATA_PATH, "data.db")

# API 密钥（与 APP_KEY 相同）
SECRET_KEY = APP_KEY

# ==================== 分页和缩略图 ====================

# 每页显示的图片数量
PAGE_SIZE = 20

# 缩略图尺寸（宽, 高）
THUMBNAIL_SIZE = (640, 640)

# 缩略图存储目录
THUMBNAIL_FOLDER = os.path.join(DATA_PATH, "thumbs")

# ==================== 临时上传配置 ====================

# 预上传文件过期时间（秒），默认 3 分钟
PREPARED_UPLOAD_EXPIRE_SECONDS = 180

# 临时上传目录
TEMP_UPLOAD_FOLDER = os.path.join(DATA_PATH, "temp")

# ==================== 图片去重 ====================

# 感知哈希相似度阈值，低于此值视为重复图片
PHASH_DUPLICATE_THRESHOLD = 5

# ==================== 验证码配置 ====================

# 验证码长度
CAPTCHA_LENGTH = 4

# 验证码过期时间（秒），默认 5 分钟
CAPTCHA_EXPIRE_SECONDS = 300

# ==================== NSFW 检测配置 ====================

# NSFW 检测模型路径（None 表示自动下载默认模型）
NSFW_MODEL_PATH = None

# NSFW 判定阈值
NSFW_HENTAI_THRESHOLD = 0.5  # 二次元 NSFW
NSFW_PORN_THRESHOLD = 0.5  # 真实 NSFW
NSFW_SEXY_THRESHOLD = 0.6  # 擦边球阈值

# ==================== AI 自动标签 ====================

# 是否启用 AI 自动标签功能
AI_ENABLED = True

# AI 服务地址（兼容 OpenAI API 格式）
AI_BASE_URL = "http://127.0.0.1:8350/v1"

# AI 服务 API 密钥
AI_API_KEY = "sk-ITfMuFSPqkIAV17fWK9cDdrFXjW0zd8B2ldtuWqbyRzCeXtd"

# AI 模型名称
AI_MODEL = "qwen3.5-35b-a3b"

# AI 请求超时时间（秒）
AI_TIMEOUT_SECONDS = 30

# AI 返回的最大标签数量
AI_MAX_TAGS = 12

# AI 标签提取提示词
AI_PROMPT = (
    "你是一个专为ACG图库（如Pixiv、Danbooru风格）服务的图片标签提取助手。"
    "请基于图片内容提取 8~14 个中文搜索关键词（标签）。"
    "输出规则："
    "1. 标签必须为单个中文词汇或极短词组（如'白发''双马尾'，避免'白色头发'这种长词）。"
    "2. 按搜索价值从高到低排序：角色名（如有）> 发型/发色/瞳色 > 服装/武器 > 姿势 > 场景 > 画风。"
    "3. 确保包含画面中最独特的 2~3 个视觉焦点（如'机械臂''狐耳''断剑'）。"
    "4. 尽量使用该特征最常用的中文搜索词（例如'异色瞳'而非'不同颜色眼睛'）。"
    "5. 禁止输出完整句子、编号、解释或额外说明。"
    '最终只返回一个JSON对象，格式为 {"tags": ["标签1", "标签2", ...]}。'
)

# ==================== 数据库配置 ====================

os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(THUMBNAIL_FOLDER, exist_ok=True)
os.makedirs(TEMP_UPLOAD_FOLDER, exist_ok=True)

# Tortoise-ORM 配置（SQLite）
TORTOISE_ORM = {
    "connections": {"default": f"sqlite://{DB_FILE}"},
    "apps": {
        "models": {
            "models": ["models", "aerich.models"],
            "default_connection": "default",
        }
    },
}
