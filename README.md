# FireflyEnch

FireflyEnch 是一个简单的图片画廊系统，功能简洁但实用，满足日常图片管理需求。

## 功能

- 图片浏览与搜索
- 图片上传与删除
- 标签管理与筛选
- 缩略图自动生成（WebP 格式）
- 图片去重（基于感知哈希）
- AI 自动标签（兼容 OpenAI API）
- 验证码登录

## 环境要求

- Python >= 3.13

## 安装

### 本地运行

```bash
git clone https://github.com/moyanj/FireflyEnch
cd FireflyEnch
make run
```

### Docker 运行

```bash
git clone https://github.com/moyanj/FireflyEnch
cd FireflyEnch
make docker
docker run -p 8896:8896 -v /path/to/data:/moyan/data fireflyench:2.5.0
```

## 配置

应用配置位于 `config.py`，主要配置项：

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `APP_PORT` | 8896 | 服务端口 |
| `APP_KEY` | 12345678 | API 密钥 |
| `PAGE_SIZE` | 20 | 每页显示数量 |
| `AI_ENABLED` | True | 是否启用 AI 自动标签 |
| `AI_BASE_URL` | http://127.0.0.1:8350/v1 | AI 服务地址 |

## 技术栈

- **后端**: FastAPI + Uvicorn
- **数据库**: Tortoise ORM (SQLite)
- **前端**: Vue 3 + TypeScript
- **依赖**: aiofiles, Pillow, httpx
