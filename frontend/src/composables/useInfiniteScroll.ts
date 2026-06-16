import { ref, onMounted, onUnmounted } from 'vue'

export function useInfiniteScroll(callback: () => Promise<void>, threshold: number = 200) {
  const isLoading = ref(false)

  async function handleScroll() {
    if (isLoading.value) return

    const { scrollTop, scrollHeight, clientHeight } = document.documentElement
    if (scrollTop + clientHeight >= scrollHeight - threshold) {
      isLoading.value = true
      try {
        await callback()
      } finally {
        isLoading.value = false
      }
    }
  }

  onMounted(() => {
    window.addEventListener('scroll', handleScroll, { passive: true })
  })

  onUnmounted(() => {
    window.removeEventListener('scroll', handleScroll)
  })

  return { isLoading }
}