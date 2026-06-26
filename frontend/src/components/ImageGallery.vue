<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import type { Image } from '@/api/types'
import ImageCard from './ImageCard.vue'

const props = defineProps<{
  images: Image[]
  loading?: boolean
  hasMore?: boolean
}>()

defineEmits<{
  loadMore: []
}>()

const galleryRef = ref<HTMLElement | null>(null)
const columnCount = ref(1)

let resizeObserver: ResizeObserver | null = null

function getMinColumnWidth(width: number): number {
  if (width <= 480) return width
  if (width <= 768) return 160
  if (width <= 1024) return 184
  return 208
}

function updateColumnCount(width: number) {
  const minColumnWidth = getMinColumnWidth(width)
  const nextCount = width <= 480
    ? 1
    : Math.max(1, Math.floor((width + 16) / (minColumnWidth + 16)))

  columnCount.value = nextCount
}

const imageColumns = computed(() => {
  const columns = Array.from({ length: columnCount.value }, () => [] as Image[])

  props.images.forEach((image, index) => {
    columns[index % columnCount.value].push(image)
  })

  return columns
})

onMounted(() => {
  if (!galleryRef.value) return

  updateColumnCount(galleryRef.value.clientWidth)

  resizeObserver = new ResizeObserver((entries) => {
    const entry = entries[0]
    if (!entry) return
    updateColumnCount(entry.contentRect.width)
  })

  resizeObserver.observe(galleryRef.value)
})

onBeforeUnmount(() => {
  resizeObserver?.disconnect()
  resizeObserver = null
})
</script>

<template>
  <div ref="galleryRef" class="gallery">
    <div
      class="gallery__grid"
      :style="{ '--gallery-columns': String(columnCount) }"
    >
      <div
        v-for="(column, columnIndex) in imageColumns"
        :key="`column-${columnIndex}`"
        class="gallery__column"
      >
        <div
          v-for="(image, index) in column"
          :key="image.id"
          class="gallery__item"
          :style="{ animationDelay: `${Math.min((columnIndex + index) % 20, 10) * 50}ms` }"
        >
          <ImageCard :image="image" />
        </div>
      </div>
    </div>

    <!-- Loading indicator -->
    <div v-if="loading" class="gallery__loading">
      <div class="gallery__spinner"></div>
      <span>加载中...</span>
    </div>

    <!-- Load more trigger -->
    <div
      v-if="hasMore && !loading"
      class="gallery__sentinel"
      aria-label="加载更多"
    >
      <button class="gallery__load-more" @click="$emit('loadMore')">
        加载更多
      </button>
    </div>

    <!-- No more content -->
    <div v-if="!hasMore && images.length > 0" class="gallery__end">
      <span>✦ 已展示全部内容 ✦</span>
    </div>

    <!-- Empty state -->
    <div v-if="!loading && images.length === 0" class="gallery__empty">
      <span class="gallery__empty-icon">✦</span>
      <p>暂无图片</p>
    </div>
  </div>
</template>

<style scoped>
.gallery__grid {
  display: grid;
  grid-template-columns: repeat(var(--gallery-columns), minmax(0, 1fr));
  gap: var(--space-md);
  align-items: start;
}

.gallery__column {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.gallery__item {
  animation: fade-up 0.4s ease both;
}

@keyframes fade-up {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Loading spinner */
.gallery__loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-sm);
  padding: var(--space-xl);
  color: var(--color-text-muted);
  font-size: 0.72rem;
}

.gallery__spinner {
  width: 16px;
  height: 16px;
  border: 2px solid var(--color-border);
  border-top-color: var(--color-accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Load more */
.gallery__sentinel {
  display: flex;
  justify-content: center;
  padding: var(--space-xl);
}

.gallery__load-more {
  padding: var(--space-sm) var(--space-xl);
  background: none;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-full);
  color: var(--color-text-secondary);
  font-size: 0.68rem;
  cursor: pointer;
  transition:
    color var(--transition-fast),
    border-color var(--transition-fast),
    background-color var(--transition-fast);
}

.gallery__load-more:hover {
  color: var(--color-accent);
  border-color: var(--color-accent);
  background-color: var(--color-accent-glow);
}

/* End state */
.gallery__end {
  text-align: center;
  padding: var(--space-xl);
  color: var(--color-text-muted);
  font-size: 0.68rem;
}

/* Empty state */
.gallery__empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-2xl);
  color: var(--color-text-muted);
}

.gallery__empty-icon {
  font-size: 2.4rem;
  color: var(--color-accent);
  text-shadow: var(--shadow-glow);
  margin-bottom: var(--space-md);
}
</style>
