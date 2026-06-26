<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import ImageGallery from '@/components/ImageGallery.vue'
import { getAllTags, getRandomImageInfo, searchByTag } from '@/api'
import type { Image } from '@/api/types'

const route = useRoute()
const router = useRouter()

const searchQuery = ref('')
const images = ref<Image[]>([])
const isLoading = ref(false)
const errorMsg = ref('')
const hasSearched = ref(false)
const resultCount = ref(0)
const randomPending = ref(false)
const allTags = ref<string[]>([])

type SearchState = 'initial' | 'loading' | 'results' | 'empty' | 'error'
const searchState = computed<SearchState>(() => {
  if (!hasSearched.value) return 'initial'
  if (isLoading.value) return 'loading'
  if (errorMsg.value) return 'error'
  if (images.value.length === 0) return 'empty'
  return 'results'
})

const trimmedQuery = computed(() => searchQuery.value.trim())

const relatedTags = computed(() => {
  return allTags.value
    .filter(tag => tag !== trimmedQuery.value)
    .map(tag => ({ tag, sortKey: Math.random() }))
    .sort((a, b) => a.sortKey - b.sortKey)
    .slice(0, 8)
    .map(item => item.tag)
})

async function doSearch() {
  if (!trimmedQuery.value) return

  isLoading.value = true
  errorMsg.value = ''
  hasSearched.value = true

  try {
    const res = await searchByTag(trimmedQuery.value)
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

    router.replace({ path: '/search', query: { tag: trimmedQuery.value } })
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

function openSuggestedTag(tag: string) {
  searchQuery.value = tag
  doSearch()
}

async function loadAllTags() {
  try {
    const res = await getAllTags()
    if (res.code === 200 && res.data?.tags) {
      allTags.value = res.data.tags
    }
  } catch {
    allTags.value = []
  }
}

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
  loadAllTags()
})
</script>

<template>
  <div class="search">
    <section class="search__hero">
      <div class="search__hero-copy">
        <p class="search__eyebrow">Tag Explorer</p>
        <h1 class="search__title">溯流而上，掘尽万象。</h1>
      </div>

      <div class="search__hero-side">
        <button class="search__random" type="button" :disabled="randomPending" @click="jumpToRandomImage">
          <span class="search__random-icon">↗</span>
          <span>{{ randomPending ? '跳转中...' : '随机看看' }}</span>
        </button>
      </div>
    </section>

    <form class="search__form" @submit="handleSubmit">
      <input v-model="searchQuery" type="search" class="search__input" placeholder="搜索标签..." aria-label="搜索标签">
      <button type="submit" class="search__btn" :disabled="isLoading">
        <span class="search__btn-icon">✦</span>
        <span v-if="!isLoading">搜索</span>
        <span v-else>...</span>
      </button>
    </form>

    <section v-if="searchState === 'results'" class="search__summary">
      <div class="search__summary-main">
        <p class="search__summary-label">当前探索</p>
        <div class="search__summary-row">
          <span class="search__result-tag">#{{ trimmedQuery }}</span>
          <span class="search__result-count">找到 {{ resultCount }} 张图片</span>
        </div>
      </div>

      <div class="search__summary-meta">
        <p class="search__summary-label">继续延展</p>
        <div v-if="relatedTags.length > 0" class="search__related-tags">
          <button v-for="tag in relatedTags" :key="tag" type="button" class="search__related-tag"
            @click="openSuggestedTag(tag)">
            <span>#{{ tag }}</span>
          </button>
        </div>
        <p v-else class="search__summary-empty">当前结果里没有足够多的其他标签，试试换个更宽一点的关键词。</p>
      </div>
    </section>

    <div v-if="searchState === 'initial'" class="search__state search__state--initial">
      <span class="search__state-icon">✦</span>
      <p>输入标签搜索图片</p>
      <p class="search__state-hint">支持中文标签，如「白发」「双马尾」</p>
    </div>

    <div v-if="searchState === 'loading'" class="search__state search__state--loading">
      <div class="search__spinner"></div>
      <span>搜索中...</span>
    </div>

    <ImageGallery v-if="searchState === 'results'" :images="images" :loading="false" :has-more="false" />

    <div v-if="searchState === 'empty'" class="search__state search__state--empty">
      <span class="search__state-icon">∅</span>
      <p>没有找到标签为「{{ searchQuery }}」的图片</p>
      <p class="search__state-hint">可以尝试更短的标签，或者直接随机看看。</p>
      <button class="search__retry-btn" type="button" :disabled="randomPending" @click="jumpToRandomImage">
        {{ randomPending ? '跳转中...' : '换个方向，随机看看' }}
      </button>
    </div>

    <div v-if="searchState === 'error'" class="search__state search__state--error">
      <span class="search__state-icon">!</span>
      <p>{{ errorMsg }}</p>
      <button class="search__retry-btn" type="button" @click="doSearch">重试</button>
    </div>
  </div>
</template>

<style scoped>
.search {
  padding: var(--space-sm) 0 var(--space-2xl);
}

.search__hero {
  display: grid;
  grid-template-columns: minmax(0, 1.4fr) minmax(192px, 0.6fr);
  gap: var(--space-lg);
  padding: var(--space-xl);
  margin-bottom: var(--space-lg);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-xl);
  background:
    radial-gradient(circle at top left, rgba(168, 230, 0, 0.18), transparent 30%),
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
  max-width: 16ch;
  font-size: clamp(1.6rem, 4vw, 2.72rem);
  line-height: 1.05;
}

.search__desc {
  max-width: 56ch;
  margin-top: var(--space-md);
  color: var(--color-text-secondary);
}

.search__hero-side {
  display: flex;
  align-items: flex-end;
  justify-content: flex-end;
}

.search__random {
  display: inline-flex;
  align-items: center;
  gap: var(--space-sm);
  min-height: 38px;
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
  display: flex;
  gap: var(--space-sm);
  max-width: 512px;
  margin-bottom: var(--space-lg);
}

.search__input {
  flex: 1;
  min-height: 40px;
  padding: var(--space-sm) var(--space-md);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background-color: var(--color-surface);
  color: var(--color-text);
  font-size: 0.8rem;
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
  justify-content: center;
  min-width: 96px;
  min-height: 40px;
  padding: var(--space-sm) var(--space-lg);
  background-color: var(--color-accent);
  color: var(--color-bg);
  border: none;
  border-radius: var(--radius-md);
  font-size: 0.8rem;
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
  font-size: 0.88rem;
}

.search__summary {
  display: grid;
  grid-template-columns: minmax(0, 0.7fr) minmax(0, 1.3fr);
  gap: var(--space-lg);
  padding: var(--space-lg);
  margin-bottom: var(--space-lg);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-lg);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.02), transparent 50%),
    var(--color-surface);
}

.search__summary-label {
  margin-bottom: var(--space-sm);
  color: var(--color-text-muted);
  font-size: 0.64rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.search__summary-row {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  flex-wrap: wrap;
}

.search__result-tag {
  display: inline-flex;
  align-items: center;
  min-height: 32px;
  padding: 0 var(--space-md);
  border-radius: var(--radius-full);
  background: rgba(168, 230, 0, 0.12);
  color: var(--color-accent);
  font-family: var(--font-display);
}

.search__result-count {
  color: var(--color-text-secondary);
}

.search__related-tags {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm);
}

.search__related-tag {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.44rem 0.68rem;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-full);
  background: var(--color-bg-elevated);
  color: var(--color-text);
  cursor: pointer;
  transition:
    border-color var(--transition-fast),
    color var(--transition-fast),
    transform var(--transition-fast);
}

.search__related-tag:hover {
  transform: translateY(-1px);
  border-color: var(--color-accent);
  color: var(--color-accent);
}

.search__summary-empty {
  color: var(--color-text-secondary);
  font-size: 0.74rem;
}

.search__state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-2xl);
  gap: var(--space-sm);
}

.search__state-icon {
  font-size: 2rem;
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

  0%,
  100% {
    opacity: 0.6;
  }

  50% {
    opacity: 1;
  }
}

.search__state-hint {
  color: var(--color-text-muted);
  opacity: 0.7;
  font-size: 0.68rem;
  text-align: center;
}

.search__state--loading {
  color: var(--color-text-muted);
  font-size: 0.72rem;
}

.search__spinner {
  width: 19px;
  height: 19px;
  border: 2px solid var(--color-border);
  border-top-color: var(--color-accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-bottom: var(--space-sm);
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
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
  min-height: 35px;
  margin-top: var(--space-sm);
  padding: 0 var(--space-lg);
  background: transparent;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-full);
  color: var(--color-text-secondary);
  cursor: pointer;
  font-size: 0.72rem;
  transition:
    border-color var(--transition-fast),
    color var(--transition-fast),
    background-color var(--transition-fast);
}

.search__retry-btn:hover {
  border-color: var(--color-accent);
  color: var(--color-accent);
  background: var(--color-accent-glow);
}

@media (max-width: 960px) {

  .search__hero,
  .search__summary {
    grid-template-columns: 1fr;
  }

  .search__hero-side {
    justify-content: flex-start;
  }
}

@media (max-width: 640px) {
  .search__form {
    flex-direction: column;
    max-width: none;
  }

  .search__btn {
    width: 100%;
  }
}
</style>
