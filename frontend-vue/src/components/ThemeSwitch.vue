<script setup lang="ts">
import { useTheme, type Theme } from '@/composables/useTheme'

const { theme } = useTheme()

const options: { value: Theme; label: string; icon: string }[] = [
  { value: 'light', label: '浅色', icon: '☀' },
  { value: 'dark', label: '深色', icon: '☾' },
  { value: 'system', label: '跟随系统', icon: '✦' },
]

function setTheme(value: Theme) {
  theme.value = value
}
</script>

<template>
  <div class="theme-switch" :title="`当前主题: ${theme}`">
    <button
      v-for="option in options"
      :key="option.value"
      class="theme-switch__btn"
      :class="{ 'theme-switch__btn--active': theme === option.value }"
      :aria-label="option.label"
      @click="setTheme(option.value)"
    >
      {{ option.icon }}
    </button>
  </div>
</template>

<style scoped>
.theme-switch {
  display: flex;
  gap: 2px;
  background-color: var(--color-bg-elevated);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-full);
  padding: 2px;
}

.theme-switch__btn {
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 50%;
  background: transparent;
  cursor: pointer;
  font-size: 0.85rem;
  display: flex;
  align-items: center;
  justify-content: center;
  transition:
    background-color var(--transition-fast),
    color var(--transition-fast);
  color: var(--color-text-muted);
}

.theme-switch__btn:hover {
  color: var(--color-text);
  background-color: var(--color-surface-hover);
}

.theme-switch__btn--active {
  background-color: var(--color-accent-glow);
  color: var(--color-accent);
}
</style>