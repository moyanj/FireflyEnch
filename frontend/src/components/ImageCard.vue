<script setup lang="ts">
import type { Image } from '@/api/types'
import { getImageUrl } from '@/api'
import { computed, ref } from 'vue'
import { RouterLink } from 'vue-router'

const props = defineProps<{
  image: Image
}>()

const emit = defineEmits<{
  aspectRatio: [payload: { id: number; aspectRatio: number }]
}>()

const isLoaded = ref(false)
const isError = ref(false)
const imageAspectRatio = ref(1)
const revealed = ref(false)

const MAX_TAGS = 6
const displayTags = computed(() => props.image.tags.slice(0, MAX_TAGS))
const remainingCount = computed(() => Math.max(0, props.image.tags.length - MAX_TAGS))
const imageAspectRatioStyle = computed(() => String(imageAspectRatio.value))

function onLoaded(event: Event) {
  const target = event.target
  if (target instanceof HTMLImageElement && target.naturalWidth && target.naturalHeight) {
    imageAspectRatio.value = target.naturalWidth / target.naturalHeight
    emit('aspectRatio', {
      id: props.image.id,
      aspectRatio: imageAspectRatio.value,
    })
  }
  isLoaded.value = true
}

function onError() {
  isError.value = true
}

function handleReveal() {
  if (props.image.nsfw) {
    revealed.value = true
  }
}
</script>

<template>
  <div class="card" :class="{ 'card--nsfw': image.nsfw }">
    <RouterLink :to="`/image/${image.id}`" class="card__link">
      <div class="card__image-wrapper" :class="{ 'card__image-wrapper--blurred': image.nsfw && !revealed }"
        :style="{ aspectRatio: imageAspectRatioStyle }" @click="handleReveal">
        <img v-if="!isError" :src="getImageUrl(image.id, true)" :alt="image.tags.join(', ')" class="card__image"
          :class="{ 'card__image--loaded': isLoaded }" loading="lazy" @load="onLoaded" @error="onError">
        <img v-else src="@/assets/images/error.webp" alt="加载失败" class="card__image card__image--loaded">
        <!-- Loading placeholder -->
        <div v-if="!isLoaded && !isError" class="card__placeholder">
          <div class="card__shimmer"></div>
        </div>

        <!-- NSFW 模糊覆盖层 -->
        <div v-if="image.nsfw && !revealed" class="card__nsfw-overlay">
          <span class="card__nsfw-badge">R18</span>
          <span class="card__nsfw-hint">点击显示</span>
        </div>
      </div>
    </RouterLink>
    <div class="card__body">
      <div class="card__tags">
        <RouterLink v-for="tag in displayTags" :key="tag" :to="`/search?tag=${encodeURIComponent(tag)}`"
          class="card__tag">
          #{{ tag }}
        </RouterLink>
        <RouterLink v-if="remainingCount > 0" :to="`/image/${image.id}`" class="card__tag-more">
          +{{ remainingCount }}
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

.card--nsfw {
  border-color: rgba(220, 38, 38, 0.3);
}

.card--nsfw:hover {
  border-color: rgba(220, 38, 38, 0.6);
}

.card__link {
  display: block;
  text-decoration: none;
}

.card__image-wrapper {
  position: relative;
  width: 100%;
  min-height: 144px;
  max-height: min(72vh, 560px);
  background-color: var(--color-bg-elevated);
  overflow: hidden;
}

.card__image-wrapper--blurred img {
  filter: blur(32px) saturate(0.3);
  transform: scale(1.1);
  pointer-events: none;
  cursor: pointer;
}

.card__image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
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
  height: 3px;
  border-radius: 2px;
  background: linear-gradient(90deg,
      var(--color-border) 25%,
      var(--color-surface-hover) 50%,
      var(--color-border) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s ease-in-out infinite;
}

@keyframes shimmer {
  0% {
    background-position: 200% 0;
  }

  100% {
    background-position: -200% 0;
  }
}

/* NSFW 模糊覆盖层 */
.card__nsfw-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-sm);
  background: rgba(0, 0, 0, 0.45);
  cursor: pointer;
  z-index: 1;
}

.card__nsfw-badge {
  display: inline-flex;
  align-items: center;
  padding: 3px 11px;
  border: 2px solid #dc2626;
  border-radius: var(--radius-full);
  color: #ef4444;
  font-family: var(--font-display);
  font-size: 0.88rem;
  font-weight: 700;
  letter-spacing: 0.05em;
  background: rgba(220, 38, 38, 0.15);
  backdrop-filter: blur(4px);
}

.card__nsfw-hint {
  font-size: 0.6rem;
  color: rgba(255, 255, 255, 0.6);
  letter-spacing: 0.08em;
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
  font-size: 0.7rem;
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

.card__tag-more {
  font-size: 0.6rem;
  color: var(--color-text-muted);
  padding: 2px var(--space-xs);
  border-radius: var(--radius-sm);
  background-color: var(--color-bg-elevated);
  border: 1px dashed var(--color-border);
  text-decoration: none;
  cursor: pointer;
  transition:
    color var(--transition-fast),
    background-color var(--transition-fast),
    border-color var(--transition-fast);
}

.card__tag-more:hover {
  color: var(--color-accent);
  background-color: var(--color-accent-glow);
  border-color: var(--color-accent);
}
</style>
