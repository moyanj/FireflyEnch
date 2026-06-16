<script setup lang="ts">
import type { Image } from '@/api/types'
import ImageCard from './ImageCard.vue'

defineProps<{
  images: Image[]
  loading?: boolean
  hasMore?: boolean
}>()

defineEmits<{
  loadMore: []
}>()
</script>

<template>
  <div class="gallery">
    <TransitionGroup name="gallery-item" tag="div" class="gallery__grid">
      <div
        v-for="(image, index) in images"
        :key="image.id"
        class="gallery__item"
        :style="{ animationDelay: `${Math.min(index % 20, 10) * 50}ms` }"
      >
        <ImageCard :image="image" />
      </div>
    </TransitionGroup>

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
  column-width: 260px;
  gap: var(--space-md);
}

.gallery__item {
  break-inside: avoid;
  margin-bottom: var(--space-md);
  animation: fade-up 0.4s ease both;
}

.gallery__item:last-child {
  margin-bottom: 0;
}

@media (max-width: 1024px) {
  .gallery__grid {
    column-width: 230px;
  }
}

@media (max-width: 768px) {
  .gallery__grid {
    column-width: 200px;
  }
}

@media (max-width: 480px) {
  .gallery__grid {
    column-width: 100%;
  }
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

/* Transition group animations */
.gallery-item-enter-active {
  transition: all 0.4s ease;
}

.gallery-item-leave-active {
  transition: all 0.3s ease;
}

.gallery-item-enter-from {
  opacity: 0;
  transform: translateY(20px);
}

.gallery-item-leave-to {
  opacity: 0;
  transform: scale(0.95);
}

/* Loading spinner */
.gallery__loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-sm);
  padding: var(--space-xl);
  color: var(--color-text-muted);
  font-size: 0.9rem;
}

.gallery__spinner {
  width: 20px;
  height: 20px;
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
  font-size: 0.85rem;
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
  font-size: 0.85rem;
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
  font-size: 3rem;
  color: var(--color-accent);
  text-shadow: var(--shadow-glow);
  margin-bottom: var(--space-md);
}
</style>
