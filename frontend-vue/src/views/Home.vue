<script setup lang="ts">
import { ref, onMounted } from 'vue'
import ImageGallery from '@/components/ImageGallery.vue'
import { getImages } from '@/api'
import { useInfiniteScroll } from '@/composables/useInfiniteScroll'
import type { Image } from '@/api/types'

const images = ref<Image[]>([])
const currentPage = ref(1)
const hasMore = ref(true)
const isInitialLoading = ref(true)
const errorMsg = ref('')

async function fetchImages() {
  if (!hasMore.value) return

  try {
    const res = await getImages(currentPage.value)
    if (res.code !== 200) {
      errorMsg.value = res.message
      return
    }

    const { data } = res
    if (data.images.length > 0) {
      // 随机排序新加载的图片
      const shuffled = [...data.images].sort(() => Math.random() - 0.5)
      images.value.push(...shuffled)
    }
    hasMore.value = !data.last
    currentPage.value = data.page + 1
  } catch (e) {
    errorMsg.value = '网络连接失败'
  }
}

async function loadMore() {
  await fetchImages()
}

// 无限滚动
const { isLoading } = useInfiniteScroll(loadMore)

onMounted(async () => {
  await fetchImages()
  isInitialLoading.value = false
})
</script>

<template>
  <div class="home">
    <div v-if="errorMsg" class="home__error">
      <span>✦</span>
      {{ errorMsg }}
    </div>

    <ImageGallery
      :images="images"
      :loading="isInitialLoading || isLoading"
      :has-more="hasMore"
      @load-more="loadMore"
    />
  </div>
</template>

<style scoped>
.home {
  padding: var(--space-md) var(--space-lg);
}

.home__error {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-sm);
  padding: var(--space-xl);
  color: var(--color-text-muted);
  font-size: 0.9rem;
}
</style>