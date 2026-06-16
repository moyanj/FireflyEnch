<script setup lang="ts">
import type { Image } from '@/api/types'
import { getImageUrl } from '@/api'
import { ref } from 'vue'

const props = defineProps<{
  image: Image
}>()

const isLoaded = ref(false)
const isError = ref(false)

function onLoaded() {
  isLoaded.value = true
}

function onError() {
  isError.value = true
}
</script>

<template>
  <div class="card">
    <a :href="`/api/image/${image.id}`" class="card__link" target="_blank">
      <div class="card__image-wrapper">
        <img
          v-if="!isError"
          :src="getImageUrl(image.id)"
          :alt="image.tags.join(', ')"
          class="card__image"
          :class="{ 'card__image--loaded': isLoaded }"
          loading="lazy"
          @load="onLoaded"
          @error="onError"
        >
        <img
          v-else
          src="@/assets/images/error.webp"
          alt="加载失败"
          class="card__image card__image--loaded"
        >
        <!-- Loading placeholder -->
        <div v-if="!isLoaded && !isError" class="card__placeholder">
          <div class="card__shimmer"></div>
        </div>
      </div>
    </a>
    <div class="card__body">
      <div class="card__tags">
        <RouterLink
          v-for="tag in image.tags"
          :key="tag"
          :to="`/search?tag=${encodeURIComponent(tag)}`"
          class="card__tag"
        >
          #{{ tag }}
        </RouterLink>
      </div>
    </div>
  </div>
</template>

<style scoped>
.card {
  border-radius: var(--radius-md);
  overflow: hidden;
  background-color: var(--color-surface);
  border: 1px solid var(--color-border-subtle);
  transition:
    transform var(--transition-base),
    box-shadow var(--transition-base),
    border-color var(--transition-base);
}

.card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-lg);
  border-color: var(--color-accent-glow);
}

.card__link {
  display: block;
  text-decoration: none;
}

.card__image-wrapper {
  position: relative;
  width: 100%;
  aspect-ratio: 1 / 1;
  background-color: var(--color-bg-elevated);
  overflow: hidden;
}

.card__image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  opacity: 0;
  transition: opacity var(--transition-slow);
}

.card__image--loaded {
  opacity: 1;
}

.card__placeholder {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.card__shimmer {
  width: 60%;
  height: 4px;
  border-radius: 2px;
  background: linear-gradient(
    90deg,
    var(--color-border) 25%,
    var(--color-surface-hover) 50%,
    var(--color-border) 75%
  );
  background-size: 200% 100%;
  animation: shimmer 1.5s ease-in-out infinite;
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

.card__body {
  padding: var(--space-sm) var(--space-md);
}

.card__tags {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-xs);
}

.card__tag {
  font-size: 0.75rem;
  color: var(--color-text-muted);
  text-decoration: none;
  padding: 2px var(--space-xs);
  border-radius: var(--radius-sm);
  transition:
    color var(--transition-fast),
    background-color var(--transition-fast);
}

.card__tag:hover {
  color: var(--color-accent);
  background-color: var(--color-accent-glow);
}
</style>