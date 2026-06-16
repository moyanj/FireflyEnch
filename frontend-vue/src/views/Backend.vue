<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { uploadImage, deleteImage, clearCache, getCaptcha, login } from '@/api'

// 登录状态
const appkey = ref('')
const captchaCode = ref('')
const captchaId = ref('')
const captchaImageUrl = ref('')
const isLoggedIn = ref(false)
const loginError = ref('')
const isLoggingIn = ref(false)

// 上传状态
const fileInput = ref<HTMLInputElement | null>(null)
const selectedFile = ref<File | null>(null)
const tags = ref('')
const previewUrl = ref('')
const uploadSuccess = ref(false)
const uploadMessage = ref('')
const isLoading = ref(false)

// 删除状态
const imageId = ref('')
const deleteConfirm = ref(false)

// 缓存清除状态
const clearSuccess = ref(false)

const hasSelectedFile = computed(() => selectedFile.value !== null)

onMounted(() => {
  refreshCaptcha()
})

async function refreshCaptcha() {
  try {
    const { captchaId: id, imageUrl } = await getCaptcha()
    captchaId.value = id
    captchaImageUrl.value = imageUrl
    captchaCode.value = ''
  } catch {
    loginError.value = '获取验证码失败'
  }
}

async function handleLogin() {
  if (!appkey.value.trim()) {
    loginError.value = '请输入管理员密码'
    return
  }

  if (!captchaCode.value.trim()) {
    loginError.value = '请输入验证码'
    return
  }

  isLoggingIn.value = true
  loginError.value = ''

  try {
    const res = await login(appkey.value, captchaCode.value, captchaId.value)

    if (res.code === 200) {
      isLoggedIn.value = true
      loginError.value = ''
    } else {
      loginError.value = res.message || '登录失败'
      refreshCaptcha()
    }
  } catch {
    loginError.value = '连接服务器失败'
    refreshCaptcha()
  } finally {
    isLoggingIn.value = false
  }
}

function handleLogout() {
  isLoggedIn.value = false
  appkey.value = ''
  selectedFile.value = null
  previewUrl.value = ''
  uploadSuccess.value = false
  imageId.value = ''
  deleteConfirm.value = false
  clearSuccess.value = false
  refreshCaptcha()
}

function onFileChange(e: Event) {
  const input = e.target as HTMLInputElement
  if (input.files && input.files[0]) {
    selectedFile.value = input.files[0]
    previewUrl.value = URL.createObjectURL(input.files[0])
    uploadSuccess.value = false
    uploadMessage.value = ''
  }
}

function clearFileSelection() {
  selectedFile.value = null
  previewUrl.value = ''
  uploadSuccess.value = false
}

async function handleUpload() {
  if (!selectedFile.value) {
    alert('请选择图片')
    return
  }

  isLoading.value = true
  try {
    const tagsList = tags.value.split(',').map(t => t.trim()).filter(Boolean)
    const res = await uploadImage(selectedFile.value, tagsList, appkey.value)

    if (res.code === 201) {
      uploadSuccess.value = true
      uploadMessage.value = '上传成功！'
      previewUrl.value = res.data.url
      selectedFile.value = null
      tags.value = ''
    } else {
      alert(res.message)
    }
  } catch {
    alert('上传失败')
  } finally {
    isLoading.value = false
  }
}

async function handleDelete() {
  if (!imageId.value) {
    alert('请输入图片 ID')
    return
  }

  if (!deleteConfirm.value) {
    deleteConfirm.value = true
    return
  }

  isLoading.value = true
  try {
    const res = await deleteImage(parseInt(imageId.value), appkey.value, true)
    if (res.code === 204) {
      alert('删除成功')
      imageId.value = ''
      deleteConfirm.value = false
    } else {
      alert(res.message)
    }
  } catch {
    alert('删除失败')
  } finally {
    isLoading.value = false
  }
}

function cancelDelete() {
  deleteConfirm.value = false
}

async function handleClearCache() {
  isLoading.value = true
  clearSuccess.value = false
  try {
    const res = await clearCache(appkey.value)
    if (res.code === 200) {
      clearSuccess.value = true
      setTimeout(() => { clearSuccess.value = false }, 3000)
    } else {
      alert(res.message)
    }
  } catch {
    alert('清除失败')
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <div class="backend">
    <!-- 登录界面 -->
    <div v-if="!isLoggedIn" class="login">
      <div class="login__card">
        <div class="login__header">
          <div class="login__icon">✦</div>
          <h1 class="login__title">管理后台</h1>
          <p class="login__subtitle">FireflyEnch 管理系统</p>
        </div>

        <form class="login__form" @submit.prevent="handleLogin">
          <div class="login__field">
            <label for="login-password" class="login__label">管理员密码</label>
            <input id="login-password" v-model="appkey" type="password" class="login__input" placeholder="请输入管理员密码"
              :disabled="isLoggingIn" autofocus>
          </div>

          <div class="login__field">
            <label for="login-captcha" class="login__label">验证码</label>
            <div class="login__captcha-row">
              <input id="login-captcha" v-model="captchaCode" type="text" class="login__input login__captcha-input"
                placeholder="请输入验证码" :disabled="isLoggingIn" maxlength="4">
              <div class="login__captcha-image" @click="refreshCaptcha">
                <img v-if="captchaImageUrl" :src="captchaImageUrl" alt="验证码" class="login__captcha-img">
                <span v-else class="login__captcha-loading">加载中...</span>
              </div>
            </div>
            <span class="login__captcha-hint">点击图片刷新验证码</span>
          </div>

          <div v-if="loginError" class="login__error">
            <span class="login__error-icon">!</span>
            {{ loginError }}
          </div>

          <button type="submit" class="login__btn" :disabled="isLoggingIn">
            <span v-if="isLoggingIn" class="login__spinner"></span>
            <span v-else>登录</span>
          </button>
        </form>

        <div class="login__footer">
          <RouterLink to="/" class="login__link">← 返回画廊</RouterLink>
        </div>
      </div>
    </div>

    <!-- 管理面板 -->
    <div v-else class="admin">
      <div class="admin__header">
        <div class="admin__welcome">
          <h1 class="admin__title">管理后台</h1>
          <p class="admin__desc">FireflyEnch 图片管理系统</p>
        </div>
        <button class="admin__logout" @click="handleLogout">
          退出登录
        </button>
      </div>

      <div class="admin__grid">
        <!-- 上传卡片 -->
        <div class="admin__card">
          <div class="admin__card-header">
            <h2 class="admin__card-title">上传图片</h2>
          </div>

          <div class="admin__card-body">
            <div class="admin__upload-area" @click="fileInput?.click()">
              <input ref="fileInput" type="file" accept="image/*" class="admin__file-input-hidden"
                @change="onFileChange">
              <div v-if="!hasSelectedFile" class="admin__upload-placeholder">
                <span class="admin__upload-icon">+</span>
                <span class="admin__upload-text">点击选择图片</span>
                <span class="admin__upload-hint">支持 JPG、PNG、GIF 格式</span>
              </div>
              <div v-else class="admin__upload-preview">
                <img :src="previewUrl" alt="预览" class="admin__preview-img">
                <button class="admin__clear-btn" @click.stop="clearFileSelection">✕</button>
              </div>
            </div>

            <div class="admin__field">
              <label class="admin__label">标签</label>
              <input v-model="tags" type="text" class="admin__input" placeholder="输入标签，用逗号分隔">
            </div>

            <button class="admin__btn admin__btn--primary" :disabled="isLoading || !hasSelectedFile"
              @click="handleUpload">
              {{ isLoading ? '上传中...' : '上传图片' }}
            </button>

            <div v-if="uploadSuccess" class="admin__success">
              ✓ {{ uploadMessage }}
            </div>
          </div>
        </div>

        <!-- 删除卡片 -->
        <div class="admin__card">
          <div class="admin__card-header">
            <h2 class="admin__card-title">删除图片</h2>
          </div>

          <div class="admin__card-body">
            <div class="admin__field">
              <label class="admin__label">图片 ID</label>
              <input v-model="imageId" type="text" class="admin__input" placeholder="输入要删除的图片 ID">
            </div>

            <div v-if="deleteConfirm" class="admin__confirm">
              <p class="admin__confirm-text">确定要删除图片 #{{ imageId }} 吗？此操作不可撤销。</p>
              <div class="admin__confirm-actions">
                <button class="admin__btn admin__btn--danger" :disabled="isLoading" @click="handleDelete">
                  确认删除
                </button>
                <button class="admin__btn admin__btn--secondary" @click="cancelDelete">
                  取消
                </button>
              </div>
            </div>

            <button v-else class="admin__btn admin__btn--danger" :disabled="isLoading || !imageId"
              @click="handleDelete">
              删除图片
            </button>
          </div>
        </div>

        <!-- 系统操作卡片 -->
        <div class="admin__card">
          <div class="admin__card-header">
            <h2 class="admin__card-title">系统操作</h2>
          </div>

          <div class="admin__card-body">
            <button class="admin__btn admin__btn--secondary" :disabled="isLoading" @click="handleClearCache">
              清除缓存
            </button>

            <div v-if="clearSuccess" class="admin__success">
              ✓ 缓存已清除
            </div>

            <div class="admin__divider"></div>

            <a href="/docs" class="admin__link-btn">
              查看 API 文档
            </a>
          </div>
        </div>
      </div>

      <div class="admin__footer">
        <RouterLink to="/" class="admin__link">← 返回画廊</RouterLink>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* 登录界面 */
.login {
  min-height: 80vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-lg);
}

.login__card {
  width: 100%;
  max-width: 400px;
  background-color: var(--color-surface);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-lg);
  padding: var(--space-2xl);
}

.login__header {
  text-align: center;
  margin-bottom: var(--space-2xl);
}

.login__icon {
  font-size: 3rem;
  color: var(--color-accent);
  text-shadow: var(--shadow-glow);
  margin-bottom: var(--space-md);
  animation: pulse-glow 2s ease-in-out infinite;
}

@keyframes pulse-glow {

  0%,
  100% {
    opacity: 0.7;
    transform: scale(1);
  }

  50% {
    opacity: 1;
    transform: scale(1.05);
  }
}

.login__title {
  font-family: var(--font-display);
  font-size: 1.5rem;
  color: var(--color-text);
  margin-bottom: var(--space-xs);
}

.login__subtitle {
  color: var(--color-text-muted);
  font-size: 0.85rem;
}

.login__form {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.login__field {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.login__label {
  color: var(--color-text-secondary);
  font-size: 0.85rem;
}

.login__input {
  width: 100%;
  padding: var(--space-md);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background-color: var(--color-bg);
  color: var(--color-text);
  font-size: 1rem;
  outline: none;
  transition:
    border-color var(--transition-fast),
    box-shadow var(--transition-fast);
}

.login__input:focus {
  border-color: var(--color-accent);
  box-shadow: 0 0 0 3px var(--color-accent-glow);
}

.login__input:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.login__captcha-row {
  display: flex;
  gap: var(--space-sm);
}

.login__captcha-input {
  flex: 1;
}

.login__captcha-image {
  width: 120px;
  height: 40px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  overflow: hidden;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--color-bg);
  transition: border-color var(--transition-fast);
}

.login__captcha-image:hover {
  border-color: var(--color-accent);
}

.login__captcha-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.login__captcha-loading {
  font-size: 0.75rem;
  color: var(--color-text-muted);
}

.login__captcha-hint {
  font-size: 0.75rem;
  color: var(--color-text-muted);
}

.login__error {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-md);
  background-color: rgba(220, 53, 69, 0.1);
  border: 1px solid rgba(220, 53, 69, 0.3);
  border-radius: var(--radius-sm);
  color: #dc3545;
  font-size: 0.85rem;
}

.login__error-icon {
  width: 18px;
  height: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #dc3545;
  color: white;
  border-radius: 50%;
  font-size: 0.75rem;
  font-weight: bold;
}

.login__btn {
  width: 100%;
  padding: var(--space-md);
  border: none;
  border-radius: var(--radius-sm);
  background-color: var(--color-accent);
  color: var(--color-bg);
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition:
    background-color var(--transition-fast),
    opacity var(--transition-fast);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-sm);
}

.login__btn:hover:not(:disabled) {
  background-color: var(--color-accent-hover);
}

.login__btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.login__spinner {
  width: 18px;
  height: 18px;
  border: 2px solid var(--color-bg);
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.login__footer {
  margin-top: var(--space-xl);
  text-align: center;
}

.login__link {
  color: var(--color-text-muted);
  font-size: 0.85rem;
  transition: color var(--transition-fast);
}

.login__link:hover {
  color: var(--color-accent);
}

/* 管理面板 */
.admin {
  max-width: 1200px;
  margin: 0 auto;
  padding: var(--space-lg);
}

.admin__header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--space-2xl);
  padding-bottom: var(--space-lg);
  border-bottom: 1px solid var(--color-border-subtle);
}

.admin__title {
  font-family: var(--font-display);
  font-size: 1.75rem;
  color: var(--color-text);
  margin-bottom: var(--space-xs);
}

.admin__desc {
  color: var(--color-text-muted);
  font-size: 0.9rem;
}

.admin__logout {
  padding: var(--space-sm) var(--space-lg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background-color: transparent;
  color: var(--color-text-secondary);
  font-size: 0.85rem;
  cursor: pointer;
  transition:
    color var(--transition-fast),
    border-color var(--transition-fast),
    background-color var(--transition-fast);
}

.admin__logout:hover {
  color: var(--color-text);
  border-color: var(--color-text-secondary);
  background-color: var(--color-surface-hover);
}

.admin__grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: var(--space-lg);
  margin-bottom: var(--space-2xl);
}

.admin__card {
  background-color: var(--color-surface);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.admin__card-header {
  padding: var(--space-lg);
  border-bottom: 1px solid var(--color-border-subtle);
}

.admin__card-title {
  font-size: 1.1rem;
  color: var(--color-text);
}

.admin__card-body {
  padding: var(--space-lg);
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.admin__upload-area {
  position: relative;
  border: 2px dashed var(--color-border);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition:
    border-color var(--transition-fast),
    background-color var(--transition-fast);
  overflow: hidden;
}

.admin__upload-area:hover {
  border-color: var(--color-accent);
  background-color: var(--color-accent-glow);
}

.admin__file-input-hidden {
  display: none;
}

.admin__upload-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-sm);
  padding: var(--space-2xl);
  color: var(--color-text-muted);
}

.admin__upload-icon {
  font-size: 2.5rem;
  color: var(--color-accent);
  opacity: 0.7;
}

.admin__upload-text {
  font-size: 0.95rem;
}

.admin__upload-hint {
  font-size: 0.75rem;
  opacity: 0.7;
}

.admin__upload-preview {
  position: relative;
}

.admin__preview-img {
  width: 100%;
  height: 200px;
  object-fit: cover;
  display: block;
}

.admin__clear-btn {
  position: absolute;
  top: var(--space-sm);
  right: var(--space-sm);
  width: 28px;
  height: 28px;
  border: none;
  border-radius: 50%;
  background-color: rgba(0, 0, 0, 0.6);
  color: white;
  font-size: 0.85rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color var(--transition-fast);
}

.admin__clear-btn:hover {
  background-color: rgba(220, 53, 69, 0.8);
}

.admin__field {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.admin__label {
  color: var(--color-text-secondary);
  font-size: 0.85rem;
}

.admin__input {
  width: 100%;
  padding: var(--space-md);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background-color: var(--color-bg);
  color: var(--color-text);
  font-size: 0.95rem;
  outline: none;
  transition:
    border-color var(--transition-fast),
    box-shadow var(--transition-fast);
}

.admin__input:focus {
  border-color: var(--color-accent);
  box-shadow: 0 0 0 3px var(--color-accent-glow);
}

.admin__btn {
  width: 100%;
  padding: var(--space-md);
  border: none;
  border-radius: var(--radius-sm);
  font-size: 0.95rem;
  font-weight: 500;
  cursor: pointer;
  transition:
    background-color var(--transition-fast),
    opacity var(--transition-fast);
}

.admin__btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.admin__btn--primary {
  background-color: var(--color-accent);
  color: var(--color-bg);
}

.admin__btn--primary:hover:not(:disabled) {
  background-color: var(--color-accent-hover);
}

.admin__btn--danger {
  background-color: #dc3545;
  color: white;
}

.admin__btn--danger:hover:not(:disabled) {
  background-color: #c82333;
}

.admin__btn--secondary {
  background-color: var(--color-bg);
  color: var(--color-text);
  border: 1px solid var(--color-border);
}

.admin__btn--secondary:hover:not(:disabled) {
  background-color: var(--color-surface-hover);
  border-color: var(--color-text-secondary);
}

.admin__confirm {
  padding: var(--space-md);
  background-color: rgba(220, 53, 69, 0.1);
  border: 1px solid rgba(220, 53, 69, 0.3);
  border-radius: var(--radius-sm);
}

.admin__confirm-text {
  color: var(--color-text);
  font-size: 0.9rem;
  margin-bottom: var(--space-md);
}

.admin__confirm-actions {
  display: flex;
  gap: var(--space-sm);
}

.admin__confirm-actions .admin__btn {
  flex: 1;
}

.admin__success {
  padding: var(--space-md);
  background-color: rgba(200, 255, 0, 0.1);
  border: 1px solid rgba(200, 255, 0, 0.3);
  border-radius: var(--radius-sm);
  color: var(--color-accent);
  font-size: 0.9rem;
  text-align: center;
}

.admin__divider {
  height: 1px;
  background-color: var(--color-border-subtle);
  margin: var(--space-sm) 0;
}

.admin__link-btn {
  display: block;
  width: 100%;
  padding: var(--space-md);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background-color: transparent;
  color: var(--color-text-secondary);
  font-size: 0.95rem;
  text-align: center;
  text-decoration: none;
  transition:
    color var(--transition-fast),
    border-color var(--transition-fast),
    background-color var(--transition-fast);
}

.admin__link-btn:hover {
  color: var(--color-accent);
  border-color: var(--color-accent);
  background-color: var(--color-accent-glow);
}

.admin__footer {
  text-align: center;
  padding-top: var(--space-lg);
  border-top: 1px solid var(--color-border-subtle);
}

.admin__link {
  color: var(--color-text-muted);
  font-size: 0.85rem;
  transition: color var(--transition-fast);
}

.admin__link:hover {
  color: var(--color-accent);
}

/* 响应式 */
@media (max-width: 640px) {
  .admin__header {
    flex-direction: column;
    gap: var(--space-md);
  }

  .admin__logout {
    align-self: flex-start;
  }

  .admin__grid {
    grid-template-columns: 1fr;
  }
}
</style>
