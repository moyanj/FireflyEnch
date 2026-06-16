<script setup lang="ts">
import { ref, onMounted } from 'vue'

const version = ref('')
const buildTime = ref('')

onMounted(() => {
  // 从 meta 标签读取版本信息（如果有）
  const versionMeta = document.querySelector('meta[name="version"]')
  const buildMeta = document.querySelector('meta[name="build"]')

  if (versionMeta) version.value = versionMeta.getAttribute('content') || ''
  if (buildMeta) buildTime.value = buildMeta.getAttribute('content') || ''
})
</script>

<template>
  <div class="about">
    <div class="about__card">
      <div class="about__logo">
        <img src="/favicon.png" alt="FireflyEnch Logo" class="about__logo-img">
        <p class="about__logo-note">若此图作者看到请与我联系</p>
      </div>

      <h1 class="about__title">FireflyEnch</h1>
      <p class="about__version">
        {{ version ? `V ${version}` : 'V 2.4.6' }}
      </p>

      <p class="about__slogan">点亮你的幻想，每次闪烁新发现。</p>

      <div class="about__links">
        <a href="/docs" class="about__link">API 文档</a>
        <a href="https://github.com/moyanj" class="about__link">作者：莫颜JDC</a>
      </div>

      <div class="about__meta">
        <p v-if="buildTime">构建时间：{{ buildTime }}</p>
        <p class="about__copyright">
          © 2018-2025 <a href="https://github.com/moyanj">MoYanJDC</a>. All rights reserved.
        </p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.about {
  min-height: 60vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-lg);
}

.about__card {
  text-align: center;
  max-width: 400px;
  background-color: var(--color-surface);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-lg);
  padding: var(--space-2xl);
}

.about__logo {
  margin-bottom: var(--space-lg);
}

.about__logo-img {
  width: 120px;
  height: auto;
  margin-bottom: var(--space-sm);
}

.about__logo-note {
  font-size: 0.6rem;
  color: var(--color-text-muted);
}

.about__title {
  font-family: var(--font-display);
  font-size: 1.5rem;
  margin-bottom: var(--space-xs);
  color: var(--color-text);
}

.about__version {
  font-size: 0.9rem;
  color: var(--color-text-secondary);
  margin-bottom: var(--space-lg);
}

.about__slogan {
  font-family: var(--font-display);
  font-size: 1rem;
  color: var(--color-text);
  margin-bottom: var(--space-lg);
}

.about__links {
  display: flex;
  justify-content: center;
  gap: var(--space-lg);
  margin-bottom: var(--space-lg);
}

.about__link {
  color: var(--color-accent);
  font-size: 0.9rem;
  transition: color var(--transition-fast);
}

.about__link:hover {
  color: var(--color-accent-hover);
}

.about__meta {
  color: var(--color-text-muted);
  font-size: 0.75rem;
}

.about__meta p {
  margin-bottom: var(--space-xs);
}

.about__copyright a {
  color: var(--color-text-muted);
}
</style>