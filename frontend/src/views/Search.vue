<script setup lang="ts">
import { ref, watch, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import ImageGallery from '@/components/ImageGallery.vue'
import { searchByTag } from '@/api'
import type { Image } from '@/api/types'

const route = useRoute()
const router = useRouter()

const searchQuery = ref('')
const images = ref<Image[]>([])
const isLoading = ref(false)
const errorMsg = ref('')
const hasSearched = ref(false)
const resultCount = ref(0)

type SearchState = 'initial' | 'loading' | 'results' | 'empty' | 'error'
const searchState = computed<SearchState>(() => {
  if (!hasSearched.value) return 'initial'
  if (isLoading.value) return 'loading'
  if (errorMsg.value) return 'error'
  if (images.value.length === 0) return 'empty'
  return 'results'
})

async function doSearch() {
  if (!searchQuery.value.trim()) return

  isLoading.value = true
  errorMsg.value = ''
  hasSearched.value = true

  try {
    const res = await searchByTag(searchQuery.value.trim())
    if (res.code !== 200) {
      errorMsg.value = res.message
      images.value = []
      return
    }

    images.value = res.data.images
    resultCount.value = res.data.total

    if (images.value.length === 0) {
      errorMsg.value = ''
    }

    // 更新 URL query
    router.replace({ path: '/search', query: { tag: searchQuery.value.trim() } })
  } catch {
    errorMsg.value = '搜索失败，请稍后再试'
    images.value = []
  } finally {
    isLoading.value = false
  }
}

function handleSubmit(e: Event) {
  e.preventDefault()
  doSearch()
}

// 监听路由参数变化
watch(() => route.query.tag, (tag) => {
  if (tag && typeof tag === 'string') {
    searchQuery.value = tag
    doSearch()
  }
}, { immediate: true })

onMounted(() => {
  if (route.query.tag && typeof route.query.tag === 'string') {
    searchQuery.value = route.query.tag
  }
})
</script>

<template>
  <div class="search">
    <form class="search__form" @submit="handleSubmit">
      <input
        v-model="searchQuery"
        type="search"
        class="search__input"
        placeholder="搜索标签..."
        aria-label="搜索标签"
      >
      <button type="submit" class="search__btn" :disabled="isLoading">
        <span class="search__btn-icon">✦</span>
        <span v-if="!isLoading">搜索</span>
        <span v-else>...</span>
      </button>
    </form>

    <!-- 初始态 -->
    <div v-if="searchState === 'initial'" class="search__state search__state--initial">
      <span class="search__state-icon">✦</span>
      <p>输入标签搜索图片</p>
      <p class="search__state-hint">支持中文标签，如「白发」「双马尾」</p>
    </div>

    <!-- 搜索中 -->
    <div v-if="searchState === 'loading'" class="search__state search__state--loading">
      <div class="search__spinner"></div>
      <span>搜索中...</span>
    </div>

    <!-- 当前搜索标签回显 + 结果数量 -->
    <div v-if="searchState === 'results'" class="search__result-info">
      <span class="search__result-tag">#{{ searchQuery }}</span>
      <span class="search__result-count">找到 {{ resultCount }} 张图片</span>
    </div>

    <!-- 搜索结果 -->
    <ImageGallery
      v-if="searchState === 'results'"
      :images="images"
      :loading="false"
      :has-more="false"
    />

    <!-- 无结果 -->
    <div v-if="searchState === 'empty'" class="search__state search__state--empty">
      <span class="search__state-icon">∅</span>
      <p>没有找到标签为「{{ searchQuery }}」的图片</p>
    </div>

    <!-- 请求错误 -->
    <div v-if="searchState === 'error'" class="search__state search__state--error">
      <span class="search__state-icon">!</span>
      <p>{{ errorMsg }}</p>
      <button class="search__retry-btn" @click="doSearch">重试</button>
    </div>
  </div>
</template>

<style scoped>
.search {
  padding: var(--space-sm) 0;
}

.search__form {
  display: flex;
  gap: var(--space-sm);
  max-width: 500px;
  margin-bottom: var(--space-lg);
}

.search__input {
  flex: 1;
  padding: var(--space-sm) var(--space-md);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background-color: var(--color-surface);
  color: var(--color-text);
  font-size: 1rem;
  outline: none;
  transition:
    border-color var(--transition-fast),
    box-shadow var(--transition-fast);
}

.search__input:focus {
  border-color: var(--color-accent);
  box-shadow: 0 0 0 2px var(--color-accent-glow);
}

.search__input::placeholder {
  color: var(--color-text-muted);
}

.search__btn {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  padding: var(--space-sm) var(--space-lg);
  background-color: var(--color-accent);
  color: var(--color-bg);
  border: none;
  border-radius: var(--radius-sm);
  font-size: 1rem;
  cursor: pointer;
  transition:
    background-color var(--transition-fast),
    transform var(--transition-fast);
}

.search__btn:hover:not(:disabled) {
  background-color: var(--color-accent-hover);
}

.search__btn:active:not(:disabled) {
  transform: scale(0.98);
}

.search__btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.search__btn-icon {
  font-size: 1.1rem;
}

/* ── 状态展示 ── */
.search__state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-2xl);
  gap: var(--space-sm);
}

.search__state-icon {
  font-size: 2.5rem;
  margin-bottom: var(--space-sm);
}

.search__state--initial {
  color: var(--color-text-muted);
  min-height: 40vh;
}

.search__state--initial .search__state-icon {
  color: var(--color-accent);
  text-shadow: var(--shadow-glow);
  animation: pulse-glow 3s ease-in-out infinite;
}

@keyframes pulse-glow {
  0%, 100% { opacity: 0.6; }
  50% { opacity: 1; }
}

.search__state-hint {
  font-size: 0.85rem;
  color: var(--color-text-muted);
  opacity: 0.7;
}

.search__state--loading {
  color: var(--color-text-muted);
  font-size: 0.9rem;
}

.search__spinner {
  width: 24px;
  height: 24px;
  border: 2px solid var(--color-border);
  border-top-color: var(--color-accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-bottom: var(--space-sm);
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.search__state--empty {
  color: var(--color-text-muted);
  min-height: 30vh;
}

.search__state--empty .search__state-icon {
  color: var(--color-border);
}

.search__state--error {
  color: var(--color-text-muted);
}

.search__state--error .search__state-icon {
  color: #e54545;
}

.search__retry-btn {
  margin-top: var(--space-sm);
  padding: var(--space-sm) var(--space-lg);
  background: transparent;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  color: var(--color-text-secondary);
  cursor: pointer;
  font-size: 0.85rem;
  transition: all var(--transition-fast);
}

.search__retry-btn:hover {
  border-color: var(--color-accent);
  color: var(--color-accent);
}

/* ── 结果信息 ── */
.search__result-info {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  margin-bottom: var(--space-md);
}

.search__result-tag {
  display: inline-flex;
  padding: 4px var(--space-md);
  border-radius: var(--radius-sm);
  background-color: var(--color-accent-glow);
  color: var(--color-accent);
  font-size: 0.9rem;
  font-weight: 500;
}

.search__result-count {
  font-size: 0.85rem;
  color: var(--color-text-muted);
}
</style>
