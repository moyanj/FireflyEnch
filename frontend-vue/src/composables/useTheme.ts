/** 强制深色主题 */
export function useTheme() {
  document.documentElement.classList.add('dark')
  return { theme: 'dark' as const }
}

/** 获取当前实际主题（始终深色） */
export function getResolvedTheme(): 'dark' {
  return 'dark'
}