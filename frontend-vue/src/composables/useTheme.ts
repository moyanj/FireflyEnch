import { ref, watch } from 'vue'

export type Theme = 'light' | 'dark' | 'system'

const STORAGE_KEY = 'firefly-theme'

const theme = ref<Theme>(
  (localStorage.getItem(STORAGE_KEY) as Theme) || 'system'
)

function applyTheme(newTheme: Theme) {
  const root = document.documentElement

  root.classList.remove('light', 'dark')

  if (newTheme === 'system') {
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
    if (prefersDark) {
      root.classList.add('dark')
    }
  } else {
    root.classList.add(newTheme)
  }
}

/** 初始化：应用主题并监听系统变化 */
export function useTheme() {
  applyTheme(theme.value)

  // 监听系统主题变化
  const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
  const handleChange = () => {
    if (theme.value === 'system') {
      applyTheme('system')
    }
  }
  mediaQuery.addEventListener('change', handleChange)

  // 监听手动切换
  watch(theme, (newVal) => {
    localStorage.setItem(STORAGE_KEY, newVal)
    applyTheme(newVal)
  })

  return { theme }
}

/** 获取当前实际主题（解析 system） */
export function getResolvedTheme(): 'light' | 'dark' {
  if (theme.value !== 'system') return theme.value
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}