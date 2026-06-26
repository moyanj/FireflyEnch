"""FireflyEnch 应用配置"""

import os


def env_str(name: str, default: str) -> str:
    value = os.getenv(name)
    return value if value is not None else default


def env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return int(value)


def env_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return float(value)


def env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_optional_str(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name)
    if value is None:
        return default
    value = value.strip()
    return value or None


def env_size(name: str, default: tuple[int, int]) -> tuple[int, int]:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default

    normalized = value.lower().replace("x", ",")
    parts = [part.strip() for part in normalized.split(",") if part.strip()]
    if len(parts) != 2:
        raise ValueError(f"{name} must be in 'width,height' format")
    return int(parts[0]), int(parts[1])


# ==================== 基础配置 ====================

APP_NAME = env_str("APP_NAME", "FireflyEnch")
APP_PORT = env_int("APP_PORT", 8896)
MAX_TAGS = env_int("MAX_TAGS", 25)

# ==================== 存储配置 ====================

DATA_PATH = os.path.abspath(env_str("DATA_PATH", "./data"))
UPLOAD_FOLDER = env_str("UPLOAD_FOLDER", os.path.join(DATA_PATH, "uploads"))
DB_FILE = env_str("DB_FILE", os.path.join(DATA_PATH, "data.db"))
SECRET_KEY = env_str("SECRET_KEY", "12345678")

# ==================== 分页和缩略图 ====================

PAGE_SIZE = env_int("PAGE_SIZE", 20)
THUMBNAIL_SIZE = env_size("THUMBNAIL_SIZE", (640, 640))
THUMBNAIL_FOLDER = env_str("THUMBNAIL_FOLDER", os.path.join(DATA_PATH, "thumbs"))

# ==================== 临时上传配置 ====================

PREPARED_UPLOAD_EXPIRE_SECONDS = env_int("PREPARED_UPLOAD_EXPIRE_SECONDS", 180)
TEMP_UPLOAD_FOLDER = env_str("TEMP_UPLOAD_FOLDER", os.path.join(DATA_PATH, "temp"))

# ==================== 图片去重 ====================

PHASH_DUPLICATE_THRESHOLD = env_int("PHASH_DUPLICATE_THRESHOLD", 5)

# ==================== 验证码配置 ====================

CAPTCHA_LENGTH = env_int("CAPTCHA_LENGTH", 4)
CAPTCHA_EXPIRE_SECONDS = env_int("CAPTCHA_EXPIRE_SECONDS", 300)

# ==================== 登录态配置 ====================

LOGIN_TOKEN_EXPIRE_SECONDS = env_int("LOGIN_TOKEN_EXPIRE_SECONDS", 86400)
CLEANUP_INTERVAL_SECONDS = env_int("CLEANUP_INTERVAL_SECONDS", 300)

# ==================== NSFW 检测配置 ====================

NSFW_MODEL_PATH = env_optional_str("NSFW_MODEL_PATH")
NSFW_HENTAI_THRESHOLD = env_float("NSFW_HENTAI_THRESHOLD", 0.5)
NSFW_PORN_THRESHOLD = env_float("NSFW_PORN_THRESHOLD", 0.5)
NSFW_SEXY_THRESHOLD = env_float("NSFW_SEXY_THRESHOLD", 0.6)

# ==================== AI 自动标签 ====================

AI_ENABLED = env_bool("AI_ENABLED", True)
AI_BASE_URL = env_str("AI_BASE_URL", "http://127.0.0.1:8350/v1")
AI_API_KEY = env_str(
    "AI_API_KEY", "sk-ITfMuFSPqkIAV17fWK9cDdrFXjW0zd8B2ldtuWqbyRzCeXtd"
)
AI_MODEL = env_str("AI_MODEL", "qwen3.5-35b-a3b")
AI_TIMEOUT_SECONDS = env_int("AI_TIMEOUT_SECONDS", 30)
AI_MAX_TAGS = env_int("AI_MAX_TAGS", 12)
AI_PROMPT = env_str(
    "AI_PROMPT",
    "你是一个专为ACG图库（如Pixiv、Danbooru风格）服务的图片标签提取助手。"
    "请基于图片内容提取 8~14 个中文搜索关键词（标签）。"
    "输出规则："
    "1. 标签必须为单个中文词汇或极短词组（如'白发''双马尾'，避免'白色头发'这种长词）。"
    "2. 按搜索价值从高到低排序：角色名（如有）> 发型/发色/瞳色 > 服装/武器 > 姿势 > 场景 > 画风。"
    "3. 确保包含画面中最独特的 2~3 个视觉焦点（如'机械臂''狐耳''断剑'）。"
    "4. 尽量使用该特征最常用的中文搜索词（例如'异色瞳'而非'不同颜色眼睛'）。"
    "5. 禁止输出完整句子、编号、解释或额外说明。"
    '最终只返回一个JSON对象，格式为 {"tags": ["标签1", "标签2", ...]}。',
)

# ==================== 数据库配置 ====================

DB_TYPE = env_str("DB_TYPE", "mysql")
DB_HOST = env_str("DB_HOST", "localhost")
DB_PORT = env_int("DB_PORT", 3306)
DB_USER = env_str("DB_USER", "root")
DB_PASSWORD = env_str("DB_PASSWORD", "")
DB_NAME = env_str("DB_NAME", "fireflyench")

os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(THUMBNAIL_FOLDER, exist_ok=True)
os.makedirs(TEMP_UPLOAD_FOLDER, exist_ok=True)

if DB_TYPE == "mysql":
    DB_CONNECTION = f"mysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
else:
    DB_CONNECTION = f"sqlite://{DB_FILE}"

TORTOISE_ORM = {
    "connections": {"default": DB_CONNECTION},
    "apps": {
        "models": {
            "models": ["models", "aerich.models"],
            "default_connection": "default",
        }
    },
}
