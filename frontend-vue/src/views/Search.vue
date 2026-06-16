<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
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

async function doSearch() {
  if (!searchQuery.value.trim()) return

  isLoading.value = true
  errorMsg.value = ''
  hasSearched.value = true

  try {
    const res = await searchByTag(searchQuery.value.trim())
    if (res.code !== 200) {
      errorMsg.value = res.message
      return
    }

    images.value = res.data.images
    if (images.value.length === 0) {
      errorMsg.value = '没有找到相关图片'
    }

    // 更新 URL query
    router.replace({ path: '/search', query: { tag: searchQuery.value.trim() } })
  } catch {
    errorMsg.value = '搜索失败，请稍后再试'
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

    <div v-if="errorMsg && hasSearched" class="search__error">
      <span>✦</span>
      {{ errorMsg }}
    </div>

    <ImageGallery
      v-if="hasSearched && images.length > 0"
      :images="images"
      :loading="isLoading"
      :has-more="false"
    />
  </div>
</template>

<style scoped>
.search {
  padding: var(--space-md) var(--space-lg);
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

.search__error {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-sm);
  padding: var(--space-xl);
  color: var(--color-text-muted);
  font-size: 0.9rem;
}
</style>