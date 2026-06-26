<script setup lang="ts">
import { computed, onMounted, provide, ref } from 'vue'
import { RouterLink, RouterView, useRoute, useRouter } from 'vue-router'
import { getCaptcha, login } from '@/api'
import { clearAdminToken, getAdminToken, isAdminLoggedIn, setAdminToken } from '@/auth'

const route = useRoute()
const router = useRouter()

// ── 登录状态 ──
const isAuthed = ref(isAdminLoggedIn())
const appkey = ref('')
const captcha = ref('')
const captchaId = ref('')
const captchaUrl = ref('')
const loginError = ref('')
const loginMessage = ref('')
const isLoggingIn = ref(false)

// 向子组件提供登录状态，用于 401 时通知父层登出
provide('isAuthed', isAuthed)
provide('forceLogout', forceLogout)

// ── 侧边栏 ──
const isMobileDrawerOpen = ref(false)

const navItems = computed(() => [
  { path: '/backend/upload', label: '上传', icon: '↑' },
  { path: '/backend/images', label: '图片管理', icon: '⊞' },
  { path: '/backend/system', label: '系统', icon: '⚙' },
])

function isActive(path: string): boolean {
  return route.path === path
}

function closeDrawer() {
  isMobileDrawerOpen.value = false
}

// ── 登录逻辑 ──
function setLoggedOut() {
  clearAdminToken()
  isAuthed.value = false
  appkey.value = ''
  captcha.value = ''
  captchaId.value = ''
  captchaUrl.value = ''
  loginError.value = ''
  loginMessage.value = ''
}

// 子组件 401 时调用此函数强制登出
async function forceLogout() {
  setLoggedOut()
  await refreshCaptcha()
}

async function refreshCaptcha() {
  const res = await getCaptcha()
  captchaId.value = res.captchaId
  captchaUrl.value = res.imageUrl
}

async function handleLogin() {
  if (!appkey.value.trim()) {
    loginError.value = '请输入管理员密码'
    return
  }
  if (!captcha.value.trim() || !captchaId.value) {
    loginError.value = '请先完成验证码'
    return
  }

  isLoggingIn.value = true
  loginError.value = ''
  loginMessage.value = ''

  try {
    const res = await login(appkey.value.trim(), captcha.value.trim(), captchaId.value)
    if (res.code === 200) {
      setAdminToken(res.data.token)
      isAuthed.value = true
      loginMessage.value = '登录成功'
      await router.replace('/backend/upload')
    } else {
      loginError.value = res.message
      await refreshCaptcha()
      captcha.value = ''
    }
  } catch {
    loginError.value = '登录失败'
    await refreshCaptcha()
    captcha.value = ''
  } finally {
    isLoggingIn.value = false
  }
}

function handleLogout() {
  setLoggedOut()
  refreshCaptcha()
  router.replace('/backend')
}

onMounted(async () => {
  if (!getAdminToken()) {
    await refreshCaptcha()
    return
  }
  isAuthed.value = true
})
</script>

<template>
  <!-- 未登录：登录表单 -->
  <div v-if="!isAuthed" class="bl-login">
    <div class="bl-login__card">
      <div class="bl-login__header">
        <span class="bl-login__icon">✦</span>
        <h1 class="bl-login__title">FireflyEnch</h1>
        <p class="bl-login__subtitle">管理后台 · 身份验证</p>
      </div>

      <div class="bl-login__field">
        <label class="bl-login__label">管理员密码</label>
        <input
          v-model="appkey"
          type="password"
          class="bl-login__input"
          placeholder="请输入密码"
          autocomplete="current-password"
          @keyup.enter="handleLogin"
        >
      </div>

      <div class="bl-login__captcha-row">
        <img v-if="captchaUrl" :src="captchaUrl" alt="验证码" class="bl-login__captcha-img">
        <button class="bl-login__btn bl-login__btn--ghost" @click="refreshCaptcha">刷新</button>
      </div>

      <div class="bl-login__field">
        <label class="bl-login__label">验证码</label>
        <input
          v-model="captcha"
          type="text"
          class="bl-login__input"
          placeholder="请输入验证码"
          @keyup.enter="handleLogin"
        >
      </div>

      <button class="bl-login__btn bl-login__btn--primary" :disabled="isLoggingIn" @click="handleLogin">
        {{ isLoggingIn ? '验证中...' : '登录' }}
      </button>

      <div v-if="loginMessage" class="bl-login__msg bl-login__msg--success">✓ {{ loginMessage }}</div>
      <div v-if="loginError" class="bl-login__msg bl-login__msg--error">{{ loginError }}</div>

      <RouterLink to="/" class="bl-login__back">← 返回画廊</RouterLink>
    </div>
  </div>

  <!-- 已登录：后台壳层 -->
  <div v-else class="bl-shell">
    <!-- 顶部栏 -->
    <header class="bl-header">
      <button class="bl-header__hamburger" @click="isMobileDrawerOpen = !isMobileDrawerOpen">
        <span></span><span></span><span></span>
      </button>
      <div class="bl-header__brand">
        <span class="bl-header__icon">✦</span>
        <span class="bl-header__title">管理后台</span>
      </div>
      <button class="bl-header__logout" @click="handleLogout">退出</button>
    </header>

    <div class="bl-body">
      <!-- 侧边栏遮罩（移动端） -->
      <div
        v-if="isMobileDrawerOpen"
        class="bl-sidebar__overlay"
        @click="closeDrawer"
      ></div>

      <!-- 侧边栏 -->
      <aside class="bl-sidebar" :class="{ 'bl-sidebar--open': isMobileDrawerOpen }">
        <nav class="bl-sidebar__nav">
          <RouterLink
            v-for="item in navItems"
            :key="item.path"
            :to="item.path"
            class="bl-sidebar__item"
            :class="{ 'bl-sidebar__item--active': isActive(item.path) }"
            @click="closeDrawer"
          >
            <span class="bl-sidebar__icon">{{ item.icon }}</span>
            <span class="bl-sidebar__label">{{ item.label }}</span>
          </RouterLink>
        </nav>

        <div class="bl-sidebar__footer">
          <RouterLink to="/" class="bl-sidebar__link">← 返回画廊</RouterLink>
        </div>
      </aside>

      <!-- 工作区 -->
      <main class="bl-workspace">
        <RouterView />
      </main>
    </div>
  </div>
</template>

<style scoped>
/* ── 登录表单 ── */
.bl-login {
  height: 100vh;
  display: grid;
  place-items: center;
  padding: var(--space-xl) var(--space-lg);
  background-color: var(--terminal-bg);
}

.bl-login__card {
  width: min(420px, 100%);
  padding: var(--space-2xl);
  background-color: var(--terminal-surface);
  border: 1px solid var(--terminal-border);
  border-radius: var(--radius-md);
  box-shadow: 0 0 60px rgba(168, 230, 0, 0.04);
}

.bl-login__header {
  text-align: center;
  margin-bottom: var(--space-xl);
}

.bl-login__icon {
  display: block;
  font-size: 1.60rem;
  color: var(--terminal-accent);
  text-shadow: var(--shadow-glow);
  margin-bottom: var(--space-sm);
}

.bl-login__title {
  font-family: var(--font-display);
  font-size: 1.42rem;
  color: var(--terminal-text-bright);
  letter-spacing: -0.02em;
}

.bl-login__subtitle {
  color: var(--terminal-text-dim);
  font-size: 0.86rem;
  margin-top: var(--space-xs);
}

.bl-login__field {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  margin-bottom: var(--space-md);
}

.bl-login__label {
  font-size: 0.76rem;
  color: var(--terminal-text-dim);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.bl-login__input {
  width: 100%;
  padding: 0.82rem 1rem;
  border: 1px solid var(--terminal-border);
  border-radius: var(--radius-sm);
  background-color: var(--terminal-bg);
  color: var(--terminal-text-bright);
  font-family: var(--font-body);
  font-size: 0.94rem;
  transition: border-color var(--transition-fast);
}

.bl-login__input:focus {
  outline: none;
  border-color: var(--terminal-accent);
  box-shadow: 0 0 0 2px var(--terminal-accent-glow);
}

.bl-login__captcha-row {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  margin-bottom: var(--space-md);
}

.bl-login__captcha-img {
  height: 35px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--terminal-border);
  background: #fff;
}

.bl-login__btn {
  width: 100%;
  padding: 0.84rem 1rem;
  border: 1px solid transparent;
  border-radius: var(--radius-sm);
  font-family: var(--font-body);
  font-size: 0.94rem;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.bl-login__btn--primary {
  background-color: var(--terminal-accent);
  color: var(--terminal-bg);
  font-weight: 500;
}

.bl-login__btn--primary:hover:not(:disabled) {
  box-shadow: 0 0 20px var(--terminal-accent-glow);
}

.bl-login__btn--primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.bl-login__btn--ghost {
  background: transparent;
  border-color: var(--terminal-border);
  color: var(--terminal-text);
  width: auto;
  padding: 0.54rem 0.86rem;
  font-size: 0.82rem;
}

.bl-login__btn--ghost:hover {
  border-color: var(--terminal-accent);
  color: var(--terminal-accent);
}

.bl-login__msg {
  margin-top: var(--space-md);
  font-size: 0.84rem;
  text-align: center;
}

.bl-login__msg--success {
  color: var(--terminal-success);
}

.bl-login__msg--error {
  color: var(--terminal-danger);
}

.bl-login__back {
  display: block;
  margin-top: var(--space-lg);
  text-align: center;
  font-size: 0.84rem;
  color: var(--terminal-text-dim);
  text-decoration: none;
}

.bl-login__back:hover {
  color: var(--terminal-accent);
}

/* ── 后台壳层 ── */
.bl-shell {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: var(--terminal-bg);
}

/* ── 顶部栏 ── */
.bl-header {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  height: var(--terminal-header-height);
  padding: 0 clamp(18px, 2.8vw, 36px);
  background-color: var(--terminal-surface);
  border-bottom: 1px solid var(--terminal-border);
  flex-shrink: 0;
}

.bl-header__hamburger {
  display: none;
  flex-direction: column;
  gap: 3px;
  background: none;
  border: none;
  padding: var(--space-sm);
  cursor: pointer;
}

.bl-header__hamburger span {
  display: block;
  width: 14px;
  height: 2px;
  background-color: var(--terminal-text);
  border-radius: 2px;
}

.bl-header__brand {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  flex: 1;
}

.bl-header__icon {
  font-size: 1.12rem;
  color: var(--terminal-accent);
  text-shadow: 0 0 12px var(--terminal-accent-glow);
}

.bl-header__title {
  font-family: var(--font-display);
  font-size: 1.06rem;
  color: var(--terminal-text-bright);
}

.bl-header__logout {
  padding: 0.52rem 0.9rem;
  background: transparent;
  border: 1px solid var(--terminal-border);
  border-radius: var(--radius-sm);
  color: var(--terminal-text-dim);
  font-size: 0.8rem;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.bl-header__logout:hover {
  border-color: var(--terminal-danger);
  color: var(--terminal-danger);
}

/* ── 主体 ── */
.bl-body {
  display: flex;
  flex: 1;
  overflow: hidden;
}

/* ── 侧边栏 ── */
.bl-sidebar {
  width: var(--terminal-sidebar-width);
  background-color: var(--terminal-surface);
  border-right: 1px solid var(--terminal-border);
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: var(--space-lg) 0;
  flex-shrink: 0;
}

.bl-sidebar__nav {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 0 var(--space-sm);
}

.bl-sidebar__item {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: 0.78rem var(--space-md);
  border-radius: var(--radius-sm);
  color: var(--terminal-text-dim);
  text-decoration: none;
  font-size: 0.92rem;
  transition: all var(--transition-fast);
}

.bl-sidebar__item:hover {
  color: var(--terminal-text);
  background-color: var(--terminal-surface-hover);
}

.bl-sidebar__item--active {
  color: var(--terminal-accent);
  background-color: var(--terminal-accent-glow);
}

.bl-sidebar__icon {
  width: 18px;
  text-align: center;
  font-size: 0.94rem;
}

.bl-sidebar__footer {
  padding: var(--space-md) var(--space-md) 0;
  border-top: 1px solid var(--terminal-border);
  padding-top: var(--space-md);
  margin: 0 var(--space-sm);
}

.bl-sidebar__link {
  display: block;
  font-size: 0.82rem;
  color: var(--terminal-text-dim);
  text-decoration: none;
  padding: 0.56rem var(--space-md);
  border-radius: var(--radius-sm);
  transition: color var(--transition-fast);
}

.bl-sidebar__link:hover {
  color: var(--terminal-accent);
}

/* ── 移动端遮罩 ── */
.bl-sidebar__overlay {
  display: none;
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  z-index: var(--z-modal);
}

/* ── 工作区 ── */
.bl-workspace {
  flex: 1;
  overflow-y: auto;
  padding: clamp(18px, 2.8vw, 36px);
}

/* ── 响应式 ── */
@media (max-width: 768px) {
  .bl-login {
    padding: var(--space-lg);
  }

  .bl-login__card {
    padding: var(--space-xl);
  }

  .bl-header__hamburger {
    display: flex;
  }

  .bl-header {
    padding: 0 var(--space-md);
  }

  .bl-header__title {
    font-size: 1rem;
  }

  .bl-header__logout {
    padding: 0.48rem 0.76rem;
    font-size: 0.76rem;
  }

  .bl-sidebar {
    position: fixed;
    top: 0;
    left: 0;
    bottom: 0;
    z-index: calc(var(--z-modal) + 1);
    transform: translateX(-100%);
    transition: transform var(--transition-base);
  }

  .bl-sidebar--open {
    transform: translateX(0);
  }

  .bl-sidebar__overlay {
    display: block;
  }

  .bl-workspace {
    padding: var(--space-md);
  }
}

@media (max-width: 480px) {
  .bl-login__title {
    font-size: 1.28rem;
  }

  .bl-login__subtitle,
  .bl-login__label,
  .bl-login__msg,
  .bl-login__back {
    font-size: 0.78rem;
  }

  .bl-login__input,
  .bl-login__btn {
    font-size: 0.9rem;
  }
}
</style>
