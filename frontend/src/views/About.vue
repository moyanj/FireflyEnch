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
  min-height: 70vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-2xl);
  position: relative;
  overflow: hidden;
}

/* 萤火虫装饰背景 */
.about::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: 
    radial-gradient(2px 2px at 20% 30%, var(--color-accent-glow), transparent),
    radial-gradient(2px 2px at 80% 70%, var(--color-accent-glow), transparent),
    radial-gradient(1px 1px at 40% 80%, var(--color-accent-glow), transparent),
    radial-gradient(1px 1px at 60% 20%, var(--color-accent-glow), transparent);
  opacity: 0.4;
  animation: twinkle 4s ease-in-out infinite alternate;
  pointer-events: none;
}

@keyframes twinkle {
  0% { opacity: 0.3; }
  100% { opacity: 0.6; }
}

.about__card {
  text-align: center;
  max-width: 600px;
  width: 100%;
  background-color: var(--color-surface);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-xl);
  padding: var(--space-3xl);
  position: relative;
  z-index: 1;
  box-shadow: var(--shadow-lg);
  backdrop-filter: blur(10px);
}

.about__logo {
  margin-bottom: var(--space-xl);
  position: relative;
}

.about__logo-img {
  width: 160px;
  height: auto;
  margin-bottom: var(--space-md);
  filter: drop-shadow(0 0 20px var(--color-accent-glow));
  transition: transform var(--transition-base);
}

.about__logo-img:hover {
  transform: scale(1.05);
}

.about__logo-note {
  font-size: 0.7rem;
  color: var(--color-text-muted);
  font-style: italic;
}

.about__title {
  font-family: var(--font-display);
  font-size: 2.5rem;
  margin-bottom: var(--space-sm);
  color: var(--color-text);
  letter-spacing: -0.02em;
  text-shadow: 0 0 30px var(--color-accent-glow);
}

.about__version {
  font-size: 1rem;
  color: var(--color-accent);
  margin-bottom: var(--space-xl);
  font-weight: 500;
}

.about__slogan {
  font-family: var(--font-display);
  font-size: 1.2rem;
  color: var(--color-text-secondary);
  margin-bottom: var(--space-2xl);
  line-height: 1.6;
}

.about__links {
  display: flex;
  justify-content: center;
  gap: var(--space-xl);
  margin-bottom: var(--space-2xl);
}

.about__link {
  color: var(--color-accent);
  font-size: 1rem;
  font-weight: 500;
  padding: var(--space-sm) var(--space-lg);
  border: 1px solid var(--color-accent);
  border-radius: var(--radius-full);
  transition: all var(--transition-fast);
  text-decoration: none;
}

.about__link:hover {
  background-color: var(--color-accent);
  color: var(--color-bg);
  box-shadow: 0 0 20px var(--color-accent-glow);
}

.about__meta {
  color: var(--color-text-muted);
  font-size: 0.85rem;
  padding-top: var(--space-lg);
  border-top: 1px solid var(--color-border-subtle);
}

.about__meta p {
  margin-bottom: var(--space-sm);
}

.about__copyright a {
  color: var(--color-text-muted);
  transition: color var(--transition-fast);
}

.about__copyright a:hover {
  color: var(--color-accent);
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .about {
    padding: var(--space-xl);
  }
  
  .about__card {
    max-width: 500px;
    padding: var(--space-2xl);
  }
  
  .about__title {
    font-size: 2rem;
  }
  
  .about__logo-img {
    width: 140px;
  }
}

@media (max-width: 768px) {
  .about {
    padding: var(--space-lg);
    min-height: 60vh;
  }
  
  .about__card {
    max-width: 450px;
    padding: var(--space-xl);
  }
  
  .about__title {
    font-size: 1.8rem;
  }
  
  .about__slogan {
    font-size: 1rem;
  }
  
  .about__links {
    flex-direction: column;
    gap: var(--space-md);
  }
  
  .about__link {
    width: 100%;
  }
}

@media (max-width: 480px) {
  .about {
    padding: var(--space-md);
    min-height: 50vh;
  }
  
  .about__card {
    padding: var(--space-lg);
    border-radius: var(--radius-lg);
  }
  
  .about__title {
    font-size: 1.5rem;
  }
  
  .about__logo-img {
    width: 120px;
  }
  
  .about__slogan {
    font-size: 0.9rem;
  }
  
  .about__meta {
    font-size: 0.75rem;
  }
}
</style>