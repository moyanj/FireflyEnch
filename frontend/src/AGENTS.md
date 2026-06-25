# FRONTEND SRC KNOWLEDGE BASE

**Parent:** `../AGENTS.md`

## OVERVIEW

Vue 3 Composition API 源码，所有组件使用 `<script setup>`，TypeScript 严格模式。

## STRUCTURE

```
frontend/src/
├── api/              # API 请求层（无状态）
│   ├── index.ts      # 请求封装 + 所有 API 函数
│   └── types.ts      # 纯类型定义
├── composables/      # 可复用逻辑
│   ├── useTheme.ts   # 主题（固定 dark）
│   └── useInfiniteScroll.ts # 滚动加载
├── views/            # 页面级组件
│   └── backend/      # 管理后台（嵌套路由）
├── components/       # 公共组件
├── router/           # 路由配置
└── styles/           # 全局样式
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| 添加新 API | `api/index.ts` | 用 `request<T>()` 封装 |
| 添加类型 | `api/types.ts` | 纯 interface/type |
| 添加组合式函数 | `composables/` | 返回 `ref()` |
| 添加页面 | `views/` | 懒加载 |
| 添加后台页面 | `views/backend/` | 嵌套在 BackendLayout |
| 添加组件 | `components/` | 保持通用性 |

## CONVENTIONS

### API 函数模式
```typescript
// 公开接口（无需认证）
export async function getXxx(): Promise<ApiResponse<XxxData>> {
  return request<XxxData>('/xxx')
}

// 管理接口（需要认证）
export async function adminGetXxx(): Promise<ApiResponse<XxxData>> {
  return request<XxxData>('/admin/xxx', withAdminAuth())
}
```

### 组件模式
```vue
<script setup lang="ts">
// 1. 导入
import { ref } from 'vue'
import { xxx } from '@/api'

// 2. Props/Emits
const props = defineProps<{ ... }>()
const emit = defineEmits<{ ... }>()

// 3. 状态
const data = ref(...)

// 4. 方法
async function handleXxx() { ... }
</script>

<template>
  <div class="xxx"> ... </div>
</template>

<style scoped>
.xxx { ... }
</style>
```

### CSS 命名规则
- **组件前缀**: `{component-name}-` (kebab-case)
- **状态类**: `{prefix}--{state}` (BEM modifier)
- **元素类**: `{prefix}__{element}` (BEM element)

### 路由约定
- **懒加载**: `() => import('@/views/Xxx.vue')`
- **嵌套路由**: `/backend/*` 使用 `BackendLayout` 包裹
- **路由守卫**: 无（前端无路由守卫，认证在组件内处理）

## ANTI-PATTERNS

- **禁止 `any`**: TypeScript 严格模式
- **禁止 `as any`**: 类型断言需有依据
- **禁止内联样式**: 使用 CSS 变量 + scoped 样式
- **禁止直接操作 DOM**: 使用 Vue ref

## PERFORMANCE

- **图片懒加载**: `loading="lazy"` + IntersectionObserver
- **路由懒加载**: 所有页面组件动态导入
- **无限滚动**: `useInfiniteScroll` 组合式函数
- **骨架屏**: 图片加载前显示 shimmer 动画
