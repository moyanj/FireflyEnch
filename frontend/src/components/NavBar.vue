<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { RouterLink, useRoute } from 'vue-router'

const route = useRoute()
const isScrolled = ref(false)
const isMobileMenuOpen = ref(false)

function handleScroll() {
  isScrolled.value = window.scrollY > 10
}

function toggleMobileMenu() {
  isMobileMenuOpen.value = !isMobileMenuOpen.value
}

function closeMobileMenu() {
  isMobileMenuOpen.value = false
}

onMounted(() => {
  window.addEventListener('scroll', handleScroll, { passive: true })
})

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll)
})
</script>

<template>
  <nav class="navbar" :class="{ 'navbar--scrolled': isScrolled }">
    <div class="navbar__inner">
      <RouterLink to="/" class="navbar__brand" @click="closeMobileMenu">
        <span class="navbar__logo">✦</span>
        <span class="navbar__title">FireflyEnch</span>
      </RouterLink>

      <button
        class="navbar__toggle"
        :aria-expanded="isMobileMenuOpen"
        aria-label="菜单"
        @click="toggleMobileMenu"
      >
        <span class="navbar__toggle-icon" :class="{ 'is-open': isMobileMenuOpen }">
          <span></span>
          <span></span>
          <span></span>
        </span>
      </button>

      <div class="navbar__actions"></div>

      <div class="navbar__links" :class="{ 'is-open': isMobileMenuOpen }">
        <RouterLink
          to="/"
          class="navbar__link"
          :class="{ 'navbar__link--active': route.path === '/' }"
          @click="closeMobileMenu"
        >
          画廊
        </RouterLink>
        <RouterLink
          to="/search"
          class="navbar__link"
          :class="{ 'navbar__link--active': route.path === '/search' }"
          @click="closeMobileMenu"
        >
          搜索
        </RouterLink>
        <RouterLink
          to="/backend"
          class="navbar__link"
          :class="{ 'navbar__link--active': route.path.startsWith('/backend') }"
          @click="closeMobileMenu"
        >
          管理
        </RouterLink>
        <RouterLink
          to="/about"
          class="navbar__link"
          :class="{ 'navbar__link--active': route.path === '/about' }"
          @click="closeMobileMenu"
        >
          关于
        </RouterLink>
      </div>
    </div>
  </nav>
</template>

<style scoped>
.navbar {
  position: sticky;
  top: 0;
  z-index: var(--z-elevated);
  background-color: var(--color-surface);
  border-bottom: 1px solid var(--color-border-subtle);
  transition:
    background-color var(--transition-base),
    box-shadow var(--transition-base),
    border-color var(--transition-base);
}

.navbar--scrolled {
  box-shadow: var(--shadow-sm);
  border-bottom-color: var(--color-border);
}

.navbar__inner {
  width: 100%;
  max-width: none;
  margin: 0;
  padding: var(--space-sm) clamp(18px, 3vw, 40px);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-md);
}

.navbar__brand {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  text-decoration: none;
  color: var(--color-text);
  transition: color var(--transition-fast);
}

.navbar__brand:hover {
  color: var(--color-accent);
}

.navbar__logo {
  font-size: 1.5rem;
  color: var(--color-accent);
  text-shadow: var(--shadow-glow);
  animation: pulse-glow 3s ease-in-out infinite;
}

@keyframes pulse-glow {
  0%, 100% { opacity: 0.8; }
  50% { opacity: 1; }
}

.navbar__title {
  font-family: var(--font-display);
  font-size: 1.25rem;
  letter-spacing: -0.02em;
}

.navbar__toggle {
  display: none;
  background: none;
  border: none;
  cursor: pointer;
  padding: var(--space-sm);
}

.navbar__toggle-icon {
  display: flex;
  flex-direction: column;
  gap: 5px;
  width: 24px;
}

.navbar__toggle-icon span {
  display: block;
  height: 2px;
  background-color: var(--color-text);
  border-radius: 2px;
  transition: transform var(--transition-fast), opacity var(--transition-fast);
}

.navbar__toggle-icon.is-open span:nth-child(1) {
  transform: translateY(7px) rotate(45deg);
}

.navbar__toggle-icon.is-open span:nth-child(2) {
  opacity: 0;
}

.navbar__toggle-icon.is-open span:nth-child(3) {
  transform: translateY(-7px) rotate(-45deg);
}

.navbar__actions {
  display: flex;
  align-items: center;
}

.navbar__links {
  display: flex;
  gap: var(--space-xs);
}

.navbar__link {
  padding: var(--space-sm) var(--space-md);
  border-radius: var(--radius-sm);
  font-size: 0.9rem;
  color: var(--color-text-secondary);
  text-decoration: none;
  transition:
    color var(--transition-fast),
    background-color var(--transition-fast);
}

.navbar__link:hover {
  color: var(--color-text);
  background-color: var(--color-surface-hover);
}

.navbar__link--active {
  color: var(--color-accent);
  background-color: var(--color-accent-glow);
}

@media (max-width: 640px) {
  .navbar__inner {
    padding: var(--space-sm) var(--space-md);
  }

  .navbar__toggle {
    display: block;
    margin-left: auto;
  }

  .navbar__actions {
    display: none;
  }

  .navbar__links {
    display: none;
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    flex-direction: column;
    background-color: var(--color-surface);
    border-bottom: 1px solid var(--color-border);
    padding: var(--space-sm);
    box-shadow: var(--shadow-md);
  }

  .navbar__links.is-open {
    display: flex;
  }

  .navbar__link {
    padding: var(--space-md);
    border-radius: var(--radius-sm);
  }
}
</style>
