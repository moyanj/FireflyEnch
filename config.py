APP_NAME = "FireflyEnch"
APP_PORT = 8896
APP_KEY = "12345678"

UPLOAD_DIR = "./imgs"

AI_ENABLED = True
AI_BASE_URL = "http://127.0.0.1:8350/v1"
AI_API_KEY = "sk-ITfMuFSPqkIAV17fWK9cDdrFXjW0zd8B2ldtuWqbyRzCeXtd"
AI_MODEL = "Qwen/Qwen3.5-35B-A3B"
AI_TIMEOUT_SECONDS = 30
AI_MAX_TAGS = 12
AI_PROMPT = (
    "你是图片标签助手。"
    "请基于图片内容输出 6 到 12 个简短中文标签。"
    "标签应适合用于图片检索，避免句子、解释、编号和重复。"
    '只返回 JSON，格式为 {"tags":["标签1","标签2"]}。'
)
