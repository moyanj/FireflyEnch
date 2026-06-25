# FRONTEND KNOWLEDGE BASE

**Parent:** `../AGENTS.md`

## OVERVIEW

Vue 3 + TypeScript + Vite 前端，暗夜萤火主题，管理后台使用黑曜石终端主题。

## STRUCTURE

```
frontend/src/
├── api/              # API 请求层
│   ├── index.ts      # 统一请求封装 + 所有 API 函数
│   └── types.ts      # TypeScript 类型定义
├── composables/      # Vue 组合式函数
│   ├── useTheme.ts   # 主题管理（强制深色）
│   └── useInfiniteScroll.ts # 无限滚动
├── views/            # 页面组件
│   ├── Home.vue      # 首页
│   ├── Search.vue    # 搜索页
│   ├── ImageDetail.vue # 图片详情
│   ├── About.vue     # 关于页
│   └── backend/      # 管理后台（全屏模式）
│       ├── BackendLayout.vue  # 布局 + 登录/登出
│       ├── BackendUpload.vue  # 上传工作台
│       ├── BackendImages.vue  # 图片管理
│       └── BackendSystem.vue  # 系统管理
├── components/       # 公共组件
│   ├── NavBar.vue    # 导航栏
│   ├── ImageGallery.vue # 图片网格
│   └── ImageCard.vue # 图片卡片（含 NSFW 模糊）
├── router/           # 路由配置
├── styles/           # 全局样式
│   └── variables.css # 设计系统 + 双主题变量
├── assets/           # 静态资源
├── auth.ts           # Token 管理
├── main.ts           # 入口文件
└── App.vue           # 根组件
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| 添加新页面 | `views/` | 使用 `<script setup>` |
| 添加 API 函数 | `api/index.ts` | 统一 `request<T>()` 封装 |
| 修改类型定义 | `api/types.ts` | 所有 API 类型在此 |
| 添加组合式函数 | `composables/` | 返回响应式状态 |
| 修改主题变量 | `styles/variables.css` | 双主题系统 |
| 添加公共组件 | `components/` | 保持组件单一职责 |
| 修改路由 | `router/index.ts` | 懒加载路由组件 |

## CONVENTIONS

### 组件规范
- **单文件组件**: 使用 `<script setup lang="ts">`
- **路由隐藏**: `/backend` 路径自动隐藏 NavBar

### API 层约定
- **请求封装**: `request<T>(path, options)` 统一处理响应
- **认证注入**: `withAdminAuth()` 自动添加 Bearer Token
- **响应格式**: `{code, message, data}` 与后端一致

### 状态管理
- **无集中状态**: 不使用 Pinia/Vuex
- **Token**: `localStorage` key 为 `fireflyench.admin.token`
- **缓存**: 组件内 `ref()` 管理局部状态

## ANTI-PATTERNS

- **无 ESLint/Prettier**: 前端缺少代码格式化工具
- **无测试框架**: vitest/jest 未安装
- **强制深色模式**: `useTheme.ts` 硬编码返回 `'dark'`

## DESIGN SYSTEM

### 变量前缀
- `--color-*`: 主站主题色（暗夜萤火）
- `--terminal-*`: 管理后台主题色（黑曜石终端）
- `--space-*`: 间距 (xs=4, sm=8, md=16, lg=24, xl=32, 2xl=48, 3xl=64)
- `--radius-*`: 圆角 (sm=6, md=12, lg=16, xl=20, full=9999)
- `--shadow-*`: 阴影 (sm, md, lg, glow)
- `--transition-*`: 过渡 (fast=150ms, base=250ms, slow=400ms)
- `--z-*`: 层级 (base=0, elevated=10, modal=100, toast=200)

### 字体
- **展示字体**: `'StarRail'` (from `@/assets/fonts/starrail.woff`)
- **正文字体**: `'MiSans'` (from `@/assets/fonts/MiSans.ttf`)

### 主色
- **萤火虫绿**: `#a8e600` (accent)
- **背景**: `#0f1419` (bg)
- **表面**: `#1a1f26` (surface)
