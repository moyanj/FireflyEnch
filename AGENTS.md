# PROJECT KNOWLEDGE BASE

**Generated:** 2025-06-25
**Commit:** a486ba0 feat: 增强图片管理与 NSFW 功能
**Branch:** master

## OVERVIEW

FireflyEnch 是一个图片画廊系统，FastAPI 后端 + Vue 3 前端，单仓库结构。核心功能包括图片管理、AI 自动标签、NSFW 检测、验证码登录。

## STRUCTURE

```
FireflyEnch/
├── app.py              # 主应用（839行单体，含所有路由）
├── config.py           # 配置中心（129行）
├── models.py           # Tortoise ORM 模型（329行）
├── utils.py            # 工具函数（110行）
├── nsfw_detector.py    # NSFW 检测器（114行，ONNX Runtime）
├── pyproject.toml      # Python 项目配置
├── Makefile            # 构建命令
├── Dockerfile          # Docker 构建
├── VERSION             # 版本文件（3.1.1）
├── data/               # 运行时数据目录
│   ├── uploads/
│   ├── thumbs/
│   └── temp/
└── frontend/           # Vue 3 前端
    └── src/
        ├── api/        # API 请求层
        ├── composables/# Vue 组合式函数
        ├── views/      # 页面组件
        │   └── backend/# 管理后台页面
        ├── components/ # 公共组件
        └── router/     # 路由配置
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| 添加新 API 路由 | `app.py` | 所有路由都在单文件中 |
| 修改数据模型 | `models.py` | 使用 Tortoise ORM |
| 修改配置 | `config.py` | 所有配置项集中管理 |
| 添加前端页面 | `frontend/src/views/` | Vue 3 + `<script setup>` |
| 添加 API 调用 | `frontend/src/api/index.ts` | 统一请求封装 |
| 修改样式主题 | `frontend/src/styles/variables.css` | 双主题系统 |
| NSFW 检测逻辑 | `nsfw_detector.py` | ONNX Runtime 单例 |

## CONVENTIONS

### 后端
- **API 响应格式**: `{code, message, data}`，通过 `jsonify()` 生成
- **认证方式**: 支持三种凭证：`X-Api-Key` header / `Authorization: Bearer` / `appkey` query param
- **文件命名**: 上传图片使用 `SHA1(内容) + 原始扩展名`
- **标签规范化**: `normalize_tags()` 执行 trim → 去重 → casefold → 截断(32字符)
- **验证码字符**: 排除易混淆字符 `I/O/0/1`

### 前端
- **版本注入**: `__APP_VERSION__` 全局常量通过 Vite define 注入
- **Token 存储**: `localStorage` key 为 `fireflyench.admin.token`

## ANTI-PATTERNS (THIS PROJECT)

- **无 CI/CD**: 完全依赖本地手动构建
- **版本不一致**: VERSION=3.1.1, pyproject.toml=0.1.0, package.json=2.5.0
- **缺失文件**: pyproject.toml 引用的 `mfb.py` 和 `db.py` 不存在
- **单体后端**: app.py 包含所有路由（839行），无路由器拆分
- **测试覆盖率为零**: pytest 声明但未安装，前端无测试框架

## UNIQUE STYLES

### 双主题系统
- **主站**: `--color-*` 变量（暗夜萤火主题，萤火虫绿 `#a8e600`）
- **管理后台**: `--terminal-*` 变量（黑曜石终端主题）

### NSFW 三级阈值
- Hentai（二次元）: 0.5
- Porn（真实）: 0.5
- Sexy（擦边球）: 0.6

### 两步上传模式
- 直接上传: `POST /api/images`
- 两步提交: `POST /api/images/prepare` → `POST /api/images/commit`

## COMMANDS

```bash
# 本地开发
make run              # 启动后端（uv run app.py）

# 构建
make init             # 安装依赖（uv sync + pnpm i）
make frontend         # 构建前端
make docker           # 构建 Docker 镜像
make all              # 构建前端 + Docker

# 清理
make clean            # 清理构建产物
```

## NOTES

- Python >= 3.13 要求
- 后端使用 Tortoise ORM + SQLite，支持 PostgreSQL/MySQL（JSON 过滤自动适配）
- NSFW 检测器首次运行会自动下载 ONNX 模型到 `.nsfw_cache/`
- 标签缓存 TTL 300 秒，任何增删改操作会主动清除缓存
- 前端强制深色模式，`useTheme.ts` 返回固定值 `'dark'`
- Git 提交使用 conventional commits 格式：`type(scope): message`
