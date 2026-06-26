<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import ImageGallery from '@/components/ImageGallery.vue'
import { getRandomImageInfo, searchImages } from '@/api'
import type { Image } from '@/api/types'

const route = useRoute()
const router = useRouter()

const inputQuery = ref('')
const activeQuery = ref('')
const images = ref<Image[]>([])
const resultCount = ref(0)
const currentPage = ref(1)
const hasMore = ref(false)
const isLoading = ref(false)
const isLoadingMore = ref(false)
const errorMsg = ref('')
const hasSearched = ref(false)
const randomPending = ref(false)

type SearchState = 'initial' | 'loading' | 'results' | 'empty' | 'error'

const searchState = computed<SearchState>(() => {
  if (!hasSearched.value) return 'initial'
  if (isLoading.value && images.value.length === 0) return 'loading'
  if (errorMsg.value) return 'error'
  if (images.value.length === 0) return 'empty'
  return 'results'
})

const syntaxExamples = [
  '白发 女仆 = OR',
  '+白发 +女仆 = AND',
  '白发 -r18 = 排除',
  '白色 可匹配 白色衣服',
]

function normalizeQuery(value: unknown): string {
  return typeof value === 'string' ? value.trim() : ''
}

function normalizePage(value: unknown): number {
  const raw = typeof value === 'string' ? Number.parseInt(value, 10) : Number.NaN
  return Number.isFinite(raw) && raw > 1 ? raw : 1
}

function resetSearchState(nextInput: string) {
  inputQuery.value = nextInput
  activeQuery.value = ''
  images.value = []
  resultCount.value = 0
  currentPage.value = 1
  hasMore.value = false
  isLoading.value = false
  isLoadingMore.value = false
  errorMsg.value = ''
  hasSearched.value = false
}

async function fetchSearch(query: string, page: number) {
  const append = query === activeQuery.value && page > 1

  errorMsg.value = ''
  hasSearched.value = true
  if (append) {
    isLoadingMore.value = true
  } else {
    isLoading.value = true
  }

  try {
    const res = await searchImages({ q: query, page })
    if (res.code !== 200) {
      errorMsg.value = res.message
      if (!append) {
        images.value = []
      }
      return
    }

    activeQuery.value = query
    currentPage.value = res.data.page
    resultCount.value = res.data.total
    hasMore.value = !res.data.last
    images.value = append
      ? [...images.value, ...res.data.images]
      : res.data.images
  } catch {
    errorMsg.value = '搜索失败，请稍后再试'
    if (!append) {
      images.value = []
    }
  } finally {
    isLoading.value = false
    isLoadingMore.value = false
  }
}

async function syncFromRoute() {
  const q = normalizeQuery(route.query.q)
  const page = normalizePage(route.query.page)
  inputQuery.value = q

  if (!q) {
    resetSearchState('')
    return
  }

  await fetchSearch(q, page)
}

async function submitSearch() {
  const q = inputQuery.value.trim()
  if (!q) {
    await router.push({ path: '/search' })
    return
  }

  await router.push({
    path: '/search',
    query: { q },
  })
}

async function clearSearch() {
  await router.push({ path: '/search' })
}

async function loadMore() {
  if (!hasMore.value || isLoading.value || isLoadingMore.value || !activeQuery.value) {
    return
  }

  await router.replace({
    path: '/search',
    query: {
      q: activeQuery.value,
      page: String(currentPage.value + 1),
    },
  })
}

async function jumpToRandomImage() {
  randomPending.value = true
  try {
    const res = await getRandomImageInfo()
    if (res.code === 200 && res.data) {
      await router.push(`/image/${res.data.id}`)
    }
  } finally {
    randomPending.value = false
  }
}

watch(
  () => [route.query.q, route.query.page],
  () => {
    void syncFromRoute()
  },
  { immediate: true }
)

onMounted(() => {
  inputQuery.value = normalizeQuery(route.query.q)
})
</script>

<template>
  <div class="search">
    <section class="search__hero">
      <div class="search__hero-copy">
        <p class="search__eyebrow">Tag Explorer</p>
        <h1 class="search__title">溯流而上，掘尽万象。</h1>
      </div>

      <button class="search__random" type="button" :disabled="randomPending" @click="jumpToRandomImage">
        <span class="search__random-icon">↗</span>
        <span>{{ randomPending ? '跳转中...' : '随机看看' }}</span>
      </button>
    </section>

    <form class="search__form" @submit.prevent="submitSearch">
      <input v-model="inputQuery" type="search" class="search__input" placeholder="例如：白发 +女仆 -r18" aria-label="搜索标签">
      <button type="submit" class="search__btn" :disabled="isLoading || isLoadingMore">
        <span class="search__btn-icon">✦</span>
        <span>搜索</span>
      </button>
      <button v-if="inputQuery || hasSearched" type="button" class="search__ghost-btn"
        :disabled="isLoading || isLoadingMore" @click="clearSearch">
        清空
      </button>
    </form>

    <section class="search__syntax">
      <span v-for="example in syntaxExamples" :key="example" class="search__syntax-chip">
        {{ example }}
      </span>
    </section>

    <section v-if="searchState === 'results'" class="search__summary">
      <div>
        <p class="search__summary-label">当前查询</p>
        <div class="search__summary-row">
          <span class="search__result-query">{{ activeQuery }}</span>
          <span class="search__result-count">共 {{ resultCount }} 张，第 {{ currentPage }} 页</span>
        </div>
      </div>
    </section>

    <div v-if="searchState === 'initial'" class="search__state search__state--initial">
      <span class="search__state-icon">✦</span>
      <p>输入一条标签查询开始搜索</p>
      <p class="search__state-hint">支持组合、排除和子串匹配，不支持自然语言联想。</p>
    </div>

    <div v-if="searchState === 'loading'" class="search__state search__state--loading">
      <div class="search__spinner"></div>
      <span>搜索中...</span>
    </div>

    <ImageGallery v-if="searchState === 'results'" :images="images" :loading="isLoadingMore" :has-more="hasMore"
      @load-more="loadMore" />

    <div v-if="searchState === 'empty'" class="search__state search__state--empty">
      <span class="search__state-icon">∅</span>
      <p>没有找到符合「{{ inputQuery }}」的图片</p>
      <p class="search__state-hint">试试更短的词，或减少 `+` 条件、增加空格 OR 条件。</p>
    </div>

    <div v-if="searchState === 'error'" class="search__state search__state--error">
      <span class="search__state-icon">!</span>
      <p>{{ errorMsg }}</p>
      <button class="search__ghost-btn" type="button" @click="submitSearch">重试</button>
    </div>
  </div>
</template>

<style scoped>
.search {
  padding: var(--space-sm) 0 var(--space-2xl);
}

.search__hero {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: var(--space-lg);
  align-items: end;
  padding: var(--space-xl);
  margin-bottom: var(--space-lg);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-xl);
  background:
    radial-gradient(circle at top left, rgba(168, 230, 0, 0.18), transparent 32%),
    linear-gradient(135deg, rgba(255, 255, 255, 0.02), transparent 55%),
    var(--color-surface);
  box-shadow: var(--shadow-md);
}

.search__eyebrow {
  margin-bottom: var(--space-sm);
  color: var(--color-accent);
  letter-spacing: 0.12em;
  text-transform: uppercase;
  font-size: 0.62rem;
}

.search__title {
  max-width: 18ch;
  font-size: clamp(1.6rem, 4vw, 2.72rem);
  line-height: 1.05;
}

.search__desc {
  max-width: 58ch;
  margin-top: var(--space-md);
  color: var(--color-text-secondary);
  font-size: 0.86rem;
}

.search__desc code {
  font-family: 'JetBrains Mono', monospace;
}

.search__random {
  display: inline-flex;
  align-items: center;
  gap: var(--space-sm);
  min-height: 40px;
  padding: 0 var(--space-lg);
  border: 1px solid rgba(168, 230, 0, 0.25);
  border-radius: var(--radius-full);
  background: rgba(168, 230, 0, 0.08);
  color: var(--color-accent);
  cursor: pointer;
  transition:
    transform var(--transition-fast),
    border-color var(--transition-fast),
    background-color var(--transition-fast);
}

.search__random:hover:not(:disabled) {
  transform: translateY(-1px);
  border-color: rgba(168, 230, 0, 0.45);
  background: rgba(168, 230, 0, 0.14);
}

.search__random:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.search__random-icon {
  font-size: 0.8rem;
}

.search__form {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto auto;
  gap: var(--space-sm);
  margin-bottom: var(--space-md);
}

.search__input {
  min-height: 42px;
  padding: var(--space-sm) var(--space-md);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background-color: var(--color-surface);
  color: var(--color-text);
  font-size: 0.86rem;
  outline: none;
  transition:
    border-color var(--transition-fast),
    box-shadow var(--transition-fast);
}

.search__input:focus {
  border-color: var(--color-accent);
  box-shadow: 0 0 0 2px var(--color-accent-glow);
}

.search__btn,
.search__ghost-btn {
  min-height: 42px;
  padding: 0 var(--space-lg);
  border-radius: var(--radius-md);
  font-size: 0.8rem;
  cursor: pointer;
  transition:
    transform var(--transition-fast),
    border-color var(--transition-fast),
    background-color var(--transition-fast),
    color var(--transition-fast);
}

.search__btn {
  display: inline-flex;
  align-items: center;
  gap: var(--space-xs);
  border: none;
  background-color: var(--color-accent);
  color: var(--color-bg);
}

.search__btn:hover:not(:disabled),
.search__ghost-btn:hover:not(:disabled) {
  transform: translateY(-1px);
}

.search__ghost-btn {
  border: 1px solid var(--color-border);
  background: transparent;
  color: var(--color-text-secondary);
}

.search__btn:disabled,
.search__ghost-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.search__syntax {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm);
  margin-bottom: var(--space-lg);
}

.search__syntax-chip {
  padding: 0.38rem 0.72rem;
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-full);
  background: rgba(255, 255, 255, 0.03);
  color: var(--color-text-secondary);
  font-size: 0.72rem;
}

.search__summary {
  padding: var(--space-lg);
  margin-bottom: var(--space-lg);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
}

.search__summary-label {
  margin-bottom: var(--space-xs);
  color: var(--color-text-muted);
  font-size: 0.68rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.search__summary-row {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm);
  align-items: center;
}

.search__result-query {
  font-family: 'JetBrains Mono', monospace;
  color: var(--color-accent);
}

.search__result-count {
  color: var(--color-text-secondary);
  font-size: 0.82rem;
}

.search__state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-sm);
  padding: var(--space-2xl);
  text-align: center;
  color: var(--color-text-muted);
}

.search__state-icon {
  font-size: 2.2rem;
  color: var(--color-accent);
}

.search__state-hint {
  max-width: 36ch;
  font-size: 0.82rem;
}

.search__spinner {
  width: 20px;
  height: 20px;
  border: 2px solid var(--color-border);
  border-top-color: var(--color-accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 768px) {
  .search__hero {
    grid-template-columns: 1fr;
    align-items: stretch;
  }

  .search__form {
    grid-template-columns: 1fr;
  }

  .search__btn,
  .search__ghost-btn,
  .search__random {
    width: 100%;
    justify-content: center;
  }
}
</style>
