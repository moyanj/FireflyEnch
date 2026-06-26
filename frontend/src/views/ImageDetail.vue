<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import { getAllTags, getImageInfo, getImageUrl } from '@/api'
import type { Image } from '@/api/types'

const route = useRoute()

const image = ref<Image | null>(null)
const isLoading = ref(false)
const errorMsg = ref('')
const revealed = ref(false)
const linkCopied = ref(false)
const allTags = ref<string[]>([])

const imageId = computed(() => Number(route.params.id))
const imageUrl = computed(() => (
  image.value ? getImageUrl(image.value.id) : ''
))
const thumbnailUrl = computed(() => (
  image.value ? getImageUrl(image.value.id, true) : ''
))
const suggestedTags = computed(() => {
  return allTags.value
    .filter(tag => !image.value?.tags.includes(tag))
    .map(tag => ({ tag, sortKey: Math.random() }))
    .sort((a, b) => a.sortKey - b.sortKey)
    .slice(0, 6)
    .map(item => item.tag)
})

function formatLocalDateTime(value: string | null) {
  if (!value) return '未知'

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return value
  }

  return new Intl.DateTimeFormat('zh-CN', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(date)
}

async function loadImageDetail() {
  if (!Number.isInteger(imageId.value) || imageId.value <= 0) {
    image.value = null
    errorMsg.value = '无效的图片 ID'
    return
  }

  isLoading.value = true
  errorMsg.value = ''

  try {
    const res = await getImageInfo(imageId.value)
    if (res.code !== 200) {
      image.value = null
      errorMsg.value = res.message || '图片不存在'
      return
    }

    image.value = res.data
    revealed.value = false
  } catch {
    image.value = null
    errorMsg.value = '加载图片详情失败'
  } finally {
    isLoading.value = false
  }
}

async function copyImageLink() {
  try {
    await navigator.clipboard.writeText(window.location.href)
    linkCopied.value = true
    setTimeout(() => { linkCopied.value = false }, 2000)
  } catch {
    // 静默失败
  }
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

watch(() => route.params.id, loadImageDetail)

onMounted(loadImageDetail)
onMounted(loadAllTags)
</script>

<template>
  <div class="detail">
    <div class="detail__topbar">
      <RouterLink to="/" class="detail__back">← 返回画廊</RouterLink>
    </div>

    <div v-if="isLoading" class="detail__state">
      <span>图片详情加载中...</span>
    </div>

    <div v-else-if="errorMsg" class="detail__state detail__state--error">
      <span>{{ errorMsg }}</span>
    </div>

    <div v-else-if="image" class="detail__layout">
      <section class="detail__viewer">
        <div class="detail__image-wrapper" :class="{ 'detail__image-wrapper--blurred': image.nsfw && !revealed }"
          @click="revealed = image.nsfw">
          <img :src="thumbnailUrl" :alt="image.tags.join(', ')" class="detail__image">
          <div v-if="image.nsfw && !revealed" class="detail__nsfw-overlay">
            <span class="detail__nsfw-badge">R18</span>
            <span class="detail__nsfw-hint">点击显示图片内容</span>
          </div>
        </div>
      </section>

      <aside class="detail__panel">
        <div class="detail__card">
          <p class="detail__eyebrow">Image</p>
          <h1 class="detail__title">#{{ image.id }}</h1>
        </div>

        <div class="detail__card">
          <h2 class="detail__section-title">标签</h2>
          <div class="detail__tags">
            <RouterLink v-for="tag in image.tags" :key="tag" :to="`/search?tag=${encodeURIComponent(tag)}`"
              class="detail__tag">
              #{{ tag }}
            </RouterLink>
          </div>
        </div>

        <div v-if="suggestedTags.length > 0" class="detail__card">
          <h2 class="detail__section-title">继续探索</h2>
          <div class="detail__explore">
            <RouterLink v-for="tag in suggestedTags" :key="tag" :to="`/search?tag=${encodeURIComponent(tag)}`"
              class="detail__explore-tag">
              #{{ tag }}
            </RouterLink>
          </div>
        </div>

        <div class="detail__card">
          <h2 class="detail__section-title">信息</h2>
          <dl class="detail__meta">
            <div class="detail__meta-row">
              <dt>ID</dt>
              <dd>{{ image.id }}</dd>
            </div>
            <div class="detail__meta-row">
              <dt>创建时间</dt>
              <dd>{{ formatLocalDateTime(image.created_at) }}</dd>
            </div>
            <div class="detail__meta-row">
              <dt>更新时间</dt>
              <dd>{{ formatLocalDateTime(image.updated_at) }}</dd>
            </div>
            <div class="detail__meta-row">
              <dt>NSFW</dt>
              <dd>
                <span class="detail__nsfw-status" :class="{ 'detail__nsfw-status--active': image.nsfw }">
                  {{ image.nsfw ? 'R18' : 'SFW' }}
                </span>
              </dd>
            </div>
          </dl>
        </div>

        <div class="detail__actions">
          <a :href="thumbnailUrl" target="_blank" rel="noopener noreferrer"
            class="detail__action detail__action--primary">
            打开预览图
          </a>
          <a :href="imageUrl" download class="detail__action detail__action--secondary">
            下载图片
          </a>
          <button class="detail__action detail__action--secondary" @click="copyImageLink">
            {{ linkCopied ? '已复制链接' : '复制链接' }}
          </button>
        </div>
      </aside>
    </div>
  </div>
</template>

<style scoped>
.detail {
  padding: var(--space-sm) 0 var(--space-xl);
}

.detail__topbar {
  margin-bottom: var(--space-lg);
}

.detail__back {
  color: var(--color-text-muted);
  text-decoration: none;
  transition: color var(--transition-fast);
}

.detail__back:hover {
  color: var(--color-accent);
}

.detail__state {
  min-height: 50vh;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-muted);
}

.detail__state--error {
  color: #dc3545;
}

.detail__layout {
  display: grid;
  grid-template-columns: minmax(0, 1.7fr) minmax(256px, 0.9fr);
  gap: var(--space-xl);
  align-items: start;
}

.detail__viewer {
  padding: var(--space-md);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-lg);
  background:
    radial-gradient(circle at top, rgba(200, 255, 0, 0.08), transparent 45%),
    var(--color-surface);
}

.detail__image {
  display: block;
  width: 100%;
  max-height: 80vh;
  object-fit: contain;
  border-radius: var(--radius-md);
  background-color: var(--color-bg);
}

.detail__image-wrapper {
  position: relative;
}

.detail__image-wrapper--blurred {
  cursor: pointer;
}

.detail__image-wrapper--blurred img {
  filter: blur(48px) saturate(0.2);
  transform: scale(1.1);
  pointer-events: none;
}

.detail__nsfw-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-md);
  background: rgba(0, 0, 0, 0.5);
  border-radius: var(--radius-md);
  z-index: 1;
}

.detail__nsfw-badge {
  display: inline-flex;
  align-items: center;
  padding: 6px 22px;
  border: 3px solid #dc2626;
  border-radius: var(--radius-full);
  color: #ef4444;
  font-family: var(--font-display);
  font-size: 1.44rem;
  font-weight: 700;
  letter-spacing: 0.05em;
  background: rgba(220, 38, 38, 0.15);
  backdrop-filter: blur(4px);
}

.detail__nsfw-hint {
  font-size: 0.68rem;
  color: rgba(255, 255, 255, 0.6);
  letter-spacing: 0.08em;
  animation: pulse-hint 2s ease-in-out infinite;
}

@keyframes pulse-hint {

  0%,
  100% {
    opacity: 0.6;
  }

  50% {
    opacity: 1;
  }
}

.detail__panel {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.detail__card {
  padding: var(--space-lg);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-lg);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.02), transparent 60%),
    var(--color-surface);
}

.detail__eyebrow {
  margin-bottom: var(--space-xs);
  color: var(--color-accent);
  font-size: 0.64rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.detail__title {
  font-family: var(--font-display);
  font-size: 1.6rem;
}

.detail__section-title {
  margin-bottom: var(--space-sm);
  font-size: 0.8rem;
  color: var(--color-text);
}

.detail__tags,
.detail__explore {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm);
}

.detail__tag,
.detail__explore-tag {
  display: inline-flex;
  align-items: center;
  padding: 0.32rem 0.6rem;
  border-radius: var(--radius-full);
  border: 1px solid var(--color-border);
  background-color: var(--color-bg);
  color: var(--color-text-secondary);
  text-decoration: none;
  font-family: inherit;
  font-size: 0.75rem;
  cursor: pointer;
  transition:
    color var(--transition-fast),
    background-color var(--transition-fast),
    border-color var(--transition-fast),
    transform var(--transition-fast);
}

.detail__tag:hover,
.detail__explore-tag:hover {
  color: var(--color-accent);
  border-color: var(--color-accent);
  background-color: var(--color-accent-glow);
  transform: translateY(-1px);
}

.detail__meta {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.detail__meta-row {
  display: flex;
  justify-content: space-between;
  gap: var(--space-md);
  padding-bottom: var(--space-sm);
  border-bottom: 1px solid var(--color-border-subtle);
}

.detail__meta-row:last-child {
  padding-bottom: 0;
  border-bottom: none;
}

.detail__meta-row dt {
  color: var(--color-text-muted);
}

.detail__meta-row dd {
  text-align: right;
  word-break: break-word;
}

.detail__actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-sm);
}

.detail__nsfw-status {
  display: inline-flex;
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  font-size: 0.75rem;
  border: 1px solid var(--color-border);
  color: var(--color-text-muted);
}

.detail__nsfw-status--active {
  border-color: #dc2626;
  color: #ef4444;
  background: rgba(220, 38, 38, 0.1);
}

.detail__action {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 38px;
  border-radius: var(--radius-md);
  text-decoration: none;
  transition:
    background-color var(--transition-fast),
    border-color var(--transition-fast),
    color var(--transition-fast);
}

.detail__action--primary {
  background-color: var(--color-accent);
  color: var(--color-bg);
}

.detail__action--primary:hover {
  background-color: var(--color-accent-hover);
}

.detail__action--secondary {
  border: 1px solid var(--color-border);
  background-color: var(--color-surface);
  color: var(--color-text);
}

.detail__action--secondary:hover {
  border-color: var(--color-accent);
  color: var(--color-accent);
}

@media (max-width: 960px) {
  .detail__layout {
    grid-template-columns: 1fr;
  }

  .detail__image {
    max-height: none;
  }
}

@media (max-width: 640px) {
  .detail__actions {
    grid-template-columns: 1fr;
  }

  .detail__meta-row {
    flex-direction: column;
  }

  .detail__meta-row dd {
    text-align: left;
  }
}
</style>
