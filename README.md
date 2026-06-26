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
docker compose up -d --build
```

默认 Docker 部署使用 MySQL，数据库数据保存在 `mysql_data` volume 中。
当前 Docker 部署只挂载 `./rdata/data` 到容器内的数据目录。应用配置优先走环境变量，不再依赖把 `config.py` 挂进容器。

常用环境变量包括 `APP_PORT`、`SECRET_KEY`、`DB_TYPE`、`DB_HOST`、`DB_PORT`、`DB_USER`、`DB_PASSWORD`、`DB_NAME`、`AI_ENABLED`、`AI_BASE_URL`、`AI_API_KEY`、`AI_MODEL`、`DATA_PATH`、`UPLOAD_FOLDER`、`THUMBNAIL_FOLDER`、`TEMP_UPLOAD_FOLDER`、`LOG_LEVEL`、`LOG_PATH`、`LOG_ROTATION`、`LOG_RETENTION`。

单独构建镜像：

```bash
make docker
docker run -d --name fireflyench -p 8896:8896 -v $(pwd)/data:/moyan/data fireflyench:$(cat VERSION)
```

## 配置

应用配置优先由环境变量驱动，`config.py` 只负责读取默认值。主要配置项：

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `APP_PORT` | 8896 | 服务端口 |
| `SECRET_KEY` | 12345678 | API 密钥 |
| `PAGE_SIZE` | 20 | 每页显示数量 |
| `AI_ENABLED` | True | 是否启用 AI 自动标签 |
| `AI_BASE_URL` | http://127.0.0.1:8350/v1 | AI 服务地址 |
| `LOG_LEVEL` | INFO | 日志级别 |
| `LOG_PATH` | `./data/logs/app.log` | 应用日志文件路径 |

## 技术栈

- **后端**: FastAPI + Uvicorn
- **数据库**: Tortoise ORM (SQLite)
- **前端**: Vue 3 + TypeScript
- **依赖**: aiofiles, Pillow, httpx
