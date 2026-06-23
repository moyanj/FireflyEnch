<script setup lang="ts">
import { ref } from 'vue'
import { clearCache } from '@/api'
import { clearAdminToken } from '@/auth'

const isClearing = ref(false)
const clearSuccess = ref(false)
const clearError = ref('')
const confirmLogout = ref(false)

async function handleClearCache() {
  isClearing.value = true
  clearSuccess.value = false
  clearError.value = ''

  try {
    const res = await clearCache()
    if (res.code === 200) {
      clearSuccess.value = true
      setTimeout(() => { clearSuccess.value = false }, 3000)
    } else if (res.code === 401) {
      clearAdminToken()
      clearError.value = '登录已失效'
    } else {
      clearError.value = res.message
    }
  } catch {
    clearError.value = '清除失败'
  } finally {
    isClearing.value = false
  }
}

function requestLogout() {
  confirmLogout.value = true
}

function cancelLogout() {
  confirmLogout.value = false
}

function executeLogout() {
  clearAdminToken()
  window.location.href = '/backend'
}
</script>

<template>
  <div class="bs-page">
    <div class="bs-page__header">
      <h1 class="bs-page__title">系统管理</h1>
      <p class="bs-page__desc">维护和管理系统级功能。</p>
    </div>

    <div class="bs-sections">
      <!-- 缓存清理 -->
      <div class="bs-card">
        <div class="bs-card__header">
          <h2 class="bs-card__title">缓存</h2>
          <p class="bs-card__desc">清理缩略图缓存等临时数据</p>
        </div>
        <div class="bs-card__body">
          <button
            class="bs-btn bs-btn--primary"
            :disabled="isClearing"
            @click="handleClearCache"
          >
            {{ isClearing ? '清除中...' : '清除缓存' }}
          </button>
          <div v-if="clearSuccess" class="bs-msg bs-msg--success">✓ 缓存已清除</div>
          <div v-if="clearError" class="bs-msg bs-msg--error">{{ clearError }}</div>
        </div>
      </div>

      <!-- API 文档 -->
      <div class="bs-card">
        <div class="bs-card__header">
          <h2 class="bs-card__title">API 文档</h2>
          <p class="bs-card__desc">查看后端接口文档</p>
        </div>
        <div class="bs-card__body">
          <a href="/docs" class="bs-btn bs-btn--ghost" target="_blank" rel="noopener noreferrer">
            打开 API 文档 →
          </a>
        </div>
      </div>

      <!-- 退出登录 -->
      <div class="bs-card">
        <div class="bs-card__header">
          <h2 class="bs-card__title">会话</h2>
          <p class="bs-card__desc">退出当前管理员会话</p>
        </div>
        <div class="bs-card__body">
          <button
            v-if="!confirmLogout"
            class="bs-btn bs-btn--danger"
            @click="requestLogout"
          >
            退出登录
          </button>
          <div v-else class="bs-confirm">
            <p class="bs-confirm__text">确定要退出登录吗？</p>
            <div class="bs-confirm__actions">
              <button class="bs-btn bs-btn--danger-fill" @click="executeLogout">确认退出</button>
              <button class="bs-btn bs-btn--ghost" @click="cancelLogout">取消</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.bs-page {
  max-width: 680px;
}

.bs-page__header {
  margin-bottom: var(--space-xl);
}

.bs-page__title {
  font-family: var(--font-display);
  font-size: 1.35rem;
  color: var(--terminal-text-bright);
  margin-bottom: var(--space-xs);
}

.bs-page__desc {
  color: var(--terminal-text-dim);
  font-size: 0.85rem;
}

.bs-sections {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.bs-card {
  background-color: var(--terminal-surface);
  border: 1px solid var(--terminal-border);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.bs-card__header {
  padding: var(--space-md) var(--space-lg);
  border-bottom: 1px solid var(--terminal-border);
}

.bs-card__title {
  font-size: 1rem;
  color: var(--terminal-text-bright);
  margin-bottom: 2px;
}

.bs-card__desc {
  font-size: 0.8rem;
  color: var(--terminal-text-dim);
}

.bs-card__body {
  padding: var(--space-md) var(--space-lg);
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

/* ── 按钮 ── */
.bs-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.6rem 1rem;
  border: 1px solid transparent;
  border-radius: var(--radius-sm);
  font-family: var(--font-body);
  font-size: 0.85rem;
  cursor: pointer;
  transition: all var(--transition-fast);
  text-decoration: none;
  width: fit-content;
}

.bs-btn--primary {
  background-color: var(--terminal-accent);
  color: var(--terminal-bg);
}

.bs-btn--primary:hover:not(:disabled) {
  box-shadow: 0 0 16px var(--terminal-accent-glow);
}

.bs-btn--primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.bs-btn--ghost {
  background: transparent;
  border-color: var(--terminal-border);
  color: var(--terminal-text);
}

.bs-btn--ghost:hover {
  border-color: var(--terminal-accent);
  color: var(--terminal-accent);
}

.bs-btn--danger {
  background: transparent;
  border-color: var(--terminal-border);
  color: var(--terminal-text);
}

.bs-btn--danger:hover {
  border-color: var(--terminal-danger);
  color: var(--terminal-danger);
}

.bs-btn--danger-fill {
  background-color: var(--terminal-danger);
  border-color: var(--terminal-danger);
  color: #fff;
}

/* ── 消息 ── */
.bs-msg {
  font-size: 0.8rem;
}

.bs-msg--success {
  color: var(--terminal-success);
}

.bs-msg--error {
  color: var(--terminal-danger);
}

/* ── 退出确认 ── */
.bs-confirm {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.bs-confirm__text {
  color: var(--terminal-danger);
  font-size: 0.85rem;
}

.bs-confirm__actions {
  display: flex;
  gap: var(--space-sm);
}
</style>
