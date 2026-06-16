<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import {
  clearCache,
  deleteImage,
  getCaptcha,
  login,
  suggestImageTags,
  uploadImage,
} from '@/api'
import { clearAdminToken, getAdminToken, isAdminLoggedIn, setAdminToken } from '@/auth'

const router = useRouter()

const appkey = ref('')
const captcha = ref('')
const captchaId = ref('')
const captchaUrl = ref('')
const loginError = ref('')
const loginMessage = ref('')
const isLoggingIn = ref(false)

const isAuthed = ref(isAdminLoggedIn())

const fileInput = ref<HTMLInputElement | null>(null)
const selectedFile = ref<File | null>(null)
const tags = ref('')
const previewUrl = ref('')
const uploadSuccess = ref(false)
const uploadMessage = ref('')
const uploadError = ref('')
const isUploading = ref(false)
const isSuggesting = ref(false)

type SuggestedTagItem = {
  id: number
  value: string
  enabled: boolean
}

const suggestedTags = ref<SuggestedTagItem[]>([])
let suggestedTagId = 0

const imageId = ref('')
const deleteConfirm = ref(false)
const clearSuccess = ref(false)

const hasSelectedFile = computed(() => selectedFile.value !== null)
const canSuggestTags = computed(() => isAuthed.value && hasSelectedFile.value && !isSuggesting.value && !isUploading.value)
const canCommitUpload = computed(() => isAuthed.value && hasSelectedFile.value && !isUploading.value && !isSuggesting.value)

function uniqueTags(input: string[]): string[] {
  const seen = new Set<string>()
  const normalized: string[] = []

  for (const rawTag of input) {
    const tag = rawTag.trim()
    if (!tag) continue

    const key = tag.toLowerCase()
    if (seen.has(key)) continue
    seen.add(key)
    normalized.push(tag)
  }

  return normalized
}

function createSuggestedTagItems(input: string[]): SuggestedTagItem[] {
  return uniqueTags(input).map(tag => ({
    id: ++suggestedTagId,
    value: tag,
    enabled: true,
  }))
}

const mergedTagsPreview = computed(() => {
  const manualTags = tags.value.split(',').map(tag => tag.trim())
  const enabledSuggestedTags = suggestedTags.value
    .filter(tag => tag.enabled)
    .map(tag => tag.value)
  return uniqueTags([...manualTags, ...enabledSuggestedTags])
})

function resetSuggestionState() {
  suggestedTags.value = []
}

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
      await router.replace('/backend')
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

function onFileChange(e: Event) {
  const input = e.target as HTMLInputElement
  if (input.files && input.files[0]) {
    selectedFile.value = input.files[0]
    previewUrl.value = URL.createObjectURL(input.files[0])
    uploadSuccess.value = false
    uploadMessage.value = ''
    uploadError.value = ''
    resetSuggestionState()
  }
}

function clearFileSelection() {
  selectedFile.value = null
  previewUrl.value = ''
  uploadSuccess.value = false
  uploadError.value = ''
  resetSuggestionState()
  if (fileInput.value) {
    fileInput.value.value = ''
  }
}

function normalizeSuggestedTag(item: SuggestedTagItem) {
  item.value = item.value.trim().slice(0, 32)
}

function addSuggestedTag() {
  suggestedTags.value = [
    ...suggestedTags.value,
    {
      id: ++suggestedTagId,
      value: '',
      enabled: true,
    },
  ]
}

function removeSuggestedTag(id: number) {
  suggestedTags.value = suggestedTags.value.filter(tag => tag.id !== id)
}

async function handleSuggestTags() {
  if (!selectedFile.value) {
    alert('请选择图片')
    return
  }

  isSuggesting.value = true
  uploadSuccess.value = false
  uploadMessage.value = ''
  uploadError.value = ''

  try {
    const res = await suggestImageTags(selectedFile.value)
    if (res.code === 200) {
      suggestedTags.value = createSuggestedTagItems(res.data.suggested_tags)
      uploadMessage.value = res.data.suggested_tags.length === 0
        ? '当前没有可用的 AI 建议标签'
        : 'AI 建议标签已生成，可直接上传或继续手动调整'
    } else if (res.code === 401) {
      setLoggedOut()
      loginError.value = '登录已失效，请重新登录'
    } else {
      uploadError.value = res.message
    }
  } catch {
    uploadError.value = 'AI 标签建议失败'
  } finally {
    isSuggesting.value = false
  }
}

async function handleUpload() {
  if (!selectedFile.value) {
    alert('请选择图片')
    return
  }

  isUploading.value = true
  uploadSuccess.value = false
  uploadMessage.value = ''
  uploadError.value = ''
  try {
    const res = await uploadImage(selectedFile.value, mergedTagsPreview.value)

    if (res.code === 201) {
      uploadSuccess.value = true
      uploadMessage.value = '上传成功！'
      previewUrl.value = res.data.url
      selectedFile.value = null
      tags.value = ''
      resetSuggestionState()
      if (fileInput.value) {
        fileInput.value.value = ''
      }
    } else if (res.code === 401) {
      setLoggedOut()
      loginError.value = '登录已失效，请重新登录'
    } else {
      uploadError.value = res.message
    }
  } catch {
    uploadError.value = '上传失败'
  } finally {
    isUploading.value = false
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

  isUploading.value = true
  try {
    const res = await deleteImage(parseInt(imageId.value, 10))
    if (res.code === 204) {
      alert('删除成功')
      imageId.value = ''
      deleteConfirm.value = false
    } else if (res.code === 401) {
      setLoggedOut()
      loginError.value = '登录已失效，请重新登录'
    } else {
      alert(res.message)
    }
  } catch {
    alert('删除失败')
  } finally {
    isUploading.value = false
  }
}

function cancelDelete() {
  deleteConfirm.value = false
}

async function handleClearCache() {
  isUploading.value = true
  clearSuccess.value = false
  try {
    const res = await clearCache()
    if (res.code === 200) {
      clearSuccess.value = true
      setTimeout(() => {
        clearSuccess.value = false
      }, 3000)
    } else if (res.code === 401) {
      setLoggedOut()
      loginError.value = '登录已失效，请重新登录'
    } else {
      alert(res.message)
    }
  } catch {
    alert('清除失败')
  } finally {
    isUploading.value = false
  }
}

function handleLogout() {
  setLoggedOut()
  clearFileSelection()
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
  <div class="backend">
    <div v-if="!isAuthed" class="login-shell">
      <div class="login-card">
        <h1 class="admin__title">管理后台登录</h1>
        <p class="admin__desc">先登录，再进入上传与管理。</p>

        <div class="admin__field">
          <label for="admin-appkey" class="admin__label">管理员密码</label>
          <input
            id="admin-appkey"
            v-model="appkey"
            type="password"
            class="admin__input"
            placeholder="请输入密码"
            autocomplete="current-password"
          >
        </div>

        <div class="login-captcha">
          <img v-if="captchaUrl" :src="captchaUrl" alt="验证码" class="login-captcha__image">
          <button class="admin__btn admin__btn--secondary" @click="refreshCaptcha">刷新验证码</button>
        </div>

        <div class="admin__field">
          <label class="admin__label">验证码</label>
          <input v-model="captcha" type="text" class="admin__input" placeholder="请输入验证码">
        </div>

        <button class="admin__btn admin__btn--primary" :disabled="isLoggingIn" @click="handleLogin">
          {{ isLoggingIn ? '登录中...' : '登录' }}
        </button>

        <div v-if="loginMessage" class="admin__success">✓ {{ loginMessage }}</div>
        <div v-if="loginError" class="admin__error">{{ loginError }}</div>
      </div>
    </div>

    <div v-else class="admin">
      <div class="admin__header">
        <div class="admin__welcome">
          <h1 class="admin__title">管理后台</h1>
          <p class="admin__desc">已登录，管理请求会自动携带 token。</p>
        </div>
        <button class="admin__btn admin__btn--secondary" @click="handleLogout">退出登录</button>
      </div>

      <div class="admin__grid">
        <div class="admin__card">
          <div class="admin__card-header">
            <h2 class="admin__card-title">上传图片</h2>
          </div>

          <div class="admin__card-body">
            <div class="admin__upload-area" @click="fileInput?.click()">
              <input
                ref="fileInput"
                type="file"
                accept="image/*"
                class="admin__file-input-hidden"
                @change="onFileChange"
              >
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
              <label class="admin__label">手动标签</label>
              <input v-model="tags" type="text" class="admin__input" placeholder="输入标签，用逗号分隔">
            </div>

            <button class="admin__btn admin__btn--secondary" :disabled="!canSuggestTags" @click="handleSuggestTags">
              {{ isSuggesting ? '生成建议中...' : 'AI 建议标签' }}
            </button>

            <div v-if="suggestedTags.length" class="admin__field">
              <label class="admin__label">AI 建议</label>
              <div class="admin__suggested-list">
                <div v-for="tag in suggestedTags" :key="tag.id" class="admin__suggested-item">
                  <label class="admin__suggested-toggle">
                    <input v-model="tag.enabled" type="checkbox">
                    <span>上传</span>
                  </label>
                  <input
                    v-model="tag.value"
                    type="text"
                    class="admin__input admin__suggested-input"
                    placeholder="编辑 AI 标签"
                    @blur="normalizeSuggestedTag(tag)"
                  >
                  <button type="button" class="admin__tag-remove" @click="removeSuggestedTag(tag.id)">
                    删除
                  </button>
                </div>
              </div>
              <button type="button" class="admin__text-btn" @click="addSuggestedTag">
                + 新增建议标签
              </button>
            </div>

            <div class="admin__field">
              <label class="admin__label">最终上传标签</label>
              <div class="admin__tag-summary">
                <span v-if="mergedTagsPreview.length">
                  {{ mergedTagsPreview.join(', ') }}
                </span>
                <span v-else>当前未选择任何标签</span>
              </div>
            </div>

            <button class="admin__btn admin__btn--primary" :disabled="!canCommitUpload" @click="handleUpload">
              {{ isUploading ? '上传中...' : '直接上传' }}
            </button>

            <div v-if="uploadSuccess" class="admin__success">
              ✓ {{ uploadMessage }}
            </div>

            <div v-else-if="uploadMessage" class="admin__success">
              ✓ {{ uploadMessage }}
            </div>

            <div v-if="uploadError" class="admin__error">
              {{ uploadError }}
            </div>
          </div>
        </div>

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
                <button class="admin__btn admin__btn--danger" :disabled="isUploading || isSuggesting" @click="handleDelete">
                  确认删除
                </button>
                <button class="admin__btn admin__btn--secondary" @click="cancelDelete">
                  取消
                </button>
              </div>
            </div>

            <button
              v-else
              class="admin__btn admin__btn--danger"
              :disabled="isUploading || isSuggesting || !imageId"
              @click="handleDelete"
            >
              删除图片
            </button>
          </div>
        </div>

        <div class="admin__card">
          <div class="admin__card-header">
            <h2 class="admin__card-title">系统操作</h2>
          </div>

          <div class="admin__card-body">
            <button class="admin__btn admin__btn--secondary" :disabled="isUploading || isSuggesting" @click="handleClearCache">
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
.backend {
  min-height: 100%;
}

.login-shell {
  min-height: calc(100vh - 120px);
  display: grid;
  place-items: center;
  padding: var(--space-xl) var(--space-lg);
}

.login-card {
  width: min(520px, 100%);
  padding: var(--space-2xl);
  background-color: var(--color-surface);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
}

.login-captcha {
  display: flex;
  align-items: center;
  gap: var(--space-md);
}

.login-captcha__image {
  height: 52px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border);
  background: #fff;
}

.admin {
  max-width: 1200px;
  margin: 0 auto;
  padding: var(--space-lg);
}

.admin__header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--space-xl);
  padding-bottom: var(--space-lg);
  border-bottom: 1px solid var(--color-border-subtle);
  gap: var(--space-md);
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

.admin__field {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.admin__label {
  font-size: 0.85rem;
  color: var(--color-text-secondary);
}

.admin__input {
  width: 100%;
  padding: 0.85rem 1rem;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background-color: var(--color-bg);
  color: var(--color-text);
}

.admin__btn {
  padding: 0.85rem 1rem;
  border: 1px solid transparent;
  border-radius: var(--radius-sm);
  cursor: pointer;
}

.admin__btn--primary {
  background-color: var(--color-accent);
  color: #101418;
}

.admin__btn--secondary {
  background-color: transparent;
  border-color: var(--color-border);
  color: var(--color-text);
}

.admin__btn--danger {
  background-color: #b33a3a;
  color: #fff;
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
  min-height: 220px;
}

.admin__file-input-hidden {
  display: none;
}

.admin__upload-placeholder,
.admin__upload-preview {
  min-height: 220px;
  display: grid;
  place-items: center;
}

.admin__upload-placeholder {
  color: var(--color-text-muted);
  text-align: center;
}

.admin__preview-img {
  width: 100%;
  height: 220px;
  object-fit: contain;
}

.admin__clear-btn {
  position: absolute;
  top: 8px;
  right: 8px;
}

.admin__suggested-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.admin__suggested-item {
  display: grid;
  grid-template-columns: auto 1fr auto;
  gap: var(--space-sm);
  align-items: center;
}

.admin__suggested-toggle {
  display: flex;
  gap: var(--space-xs);
  align-items: center;
}

.admin__tag-summary {
  padding: var(--space-md);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  color: var(--color-text-secondary);
}

.admin__success {
  color: var(--color-accent);
}

.admin__error {
  color: #ff7a7a;
}

.admin__footer {
  padding-bottom: var(--space-xl);
}

.admin__link {
  color: var(--color-text-secondary);
}
</style>
