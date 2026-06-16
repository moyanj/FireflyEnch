<script setup lang="ts">
import { computed, ref } from 'vue'
import { RouterLink } from 'vue-router'
import {
  deleteImage,
  clearCache,
  suggestImageTags,
  uploadImage,
} from '@/api'

const appkey = ref('')

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
const canSuggestTags = computed(() => hasSelectedFile.value && !isSuggesting.value && !isUploading.value)
const canCommitUpload = computed(() => hasSelectedFile.value && !isUploading.value && !isSuggesting.value)

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

function requireAppkey(): boolean {
  if (appkey.value.trim()) {
    return true
  }

  alert('请输入管理员密码')
  return false
}

function resetSuggestionState() {
  suggestedTags.value = []
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
  if (!requireAppkey()) return

  if (!selectedFile.value) {
    alert('请选择图片')
    return
  }

  isSuggesting.value = true
  uploadSuccess.value = false
  uploadMessage.value = ''
  uploadError.value = ''

  try {
    const res = await suggestImageTags(selectedFile.value, appkey.value.trim())
    if (res.code === 200) {
      suggestedTags.value = createSuggestedTagItems(res.data.suggested_tags)
      if (res.data.suggested_tags.length === 0) {
        uploadMessage.value = '当前没有可用的 AI 建议标签'
      } else {
        uploadMessage.value = 'AI 建议标签已生成，可直接上传或继续手动调整'
      }
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
  if (!requireAppkey()) return

  if (!selectedFile.value) {
    alert('请选择图片')
    return
  }

  isUploading.value = true
  uploadSuccess.value = false
  uploadMessage.value = ''
  uploadError.value = ''
  try {
    const res = await uploadImage(
      selectedFile.value,
      mergedTagsPreview.value,
      appkey.value.trim(),
    )

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
  if (!requireAppkey()) return

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
    const res = await deleteImage(parseInt(imageId.value, 10), appkey.value.trim())
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
    isUploading.value = false
  }
}

function cancelDelete() {
  deleteConfirm.value = false
}

async function handleClearCache() {
  if (!requireAppkey()) return

  isUploading.value = true
  clearSuccess.value = false
  try {
    const res = await clearCache(appkey.value.trim())
    if (res.code === 200) {
      clearSuccess.value = true
      setTimeout(() => {
        clearSuccess.value = false
      }, 3000)
    } else {
      alert(res.message)
    }
  } catch {
    alert('清除失败')
  } finally {
    isUploading.value = false
  }
}
</script>

<template>
  <div class="backend">
    <div class="admin">
      <div class="admin__header">
        <div class="admin__welcome">
          <h1 class="admin__title">管理后台</h1>
          <p class="admin__desc">图片可直接上传，AI 建议标签为独立可选能力</p>
        </div>
      </div>

      <div class="admin__credential-card">
        <div class="admin__field">
          <label for="admin-appkey" class="admin__label">管理员密码 / appkey</label>
          <input
            id="admin-appkey"
            v-model="appkey"
            type="password"
            class="admin__input"
            placeholder="请输入 appkey"
            autocomplete="current-password"
          >
        </div>
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

            <button
              class="admin__btn admin__btn--secondary"
              :disabled="!canSuggestTags"
              @click="handleSuggestTags"
            >
              {{ isSuggesting ? '生成建议中...' : 'AI 建议标签' }}
            </button>

            <div v-if="suggestedTags.length" class="admin__field">
              <label class="admin__label">AI 建议</label>
              <div class="admin__suggested-list">
                <div
                  v-for="tag in suggestedTags"
                  :key="tag.id"
                  class="admin__suggested-item"
                >
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
                  <button
                    type="button"
                    class="admin__tag-remove"
                    @click="removeSuggestedTag(tag.id)"
                  >
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

            <button
              class="admin__btn admin__btn--primary"
              :disabled="!canCommitUpload"
              @click="handleUpload"
            >
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

.admin__credential-card {
  margin-bottom: var(--space-xl);
  padding: var(--space-lg);
  background-color: var(--color-surface);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-md);
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

.admin__suggested-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.admin__suggested-item {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  gap: var(--space-sm);
  align-items: center;
}

.admin__suggested-toggle {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  color: var(--color-text-secondary);
  font-size: 0.85rem;
  white-space: nowrap;
}

.admin__suggested-input {
  min-width: 0;
}

.admin__tag-remove {
  border: 1px solid var(--color-border);
  background-color: var(--color-bg);
  color: var(--color-text-secondary);
  padding: 0.75rem 0.9rem;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition:
    border-color var(--transition-fast),
    color var(--transition-fast),
    background-color var(--transition-fast);
}

.admin__tag-remove:hover {
  border-color: #dc3545;
  color: #dc3545;
}

.admin__text-btn {
  align-self: flex-start;
  padding: 0;
  border: none;
  background: none;
  color: var(--color-accent);
  cursor: pointer;
  font-size: 0.9rem;
}

.admin__text-btn:hover {
  color: var(--color-accent-hover);
}

.admin__tag-summary {
  min-height: 44px;
  padding: var(--space-md);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background-color: var(--color-bg);
  color: var(--color-text-secondary);
  line-height: 1.5;
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

.admin__success {
  padding: var(--space-md);
  background-color: rgba(40, 167, 69, 0.1);
  border: 1px solid rgba(40, 167, 69, 0.3);
  border-radius: var(--radius-sm);
  color: #28a745;
  font-size: 0.9rem;
}

.admin__error {
  padding: var(--space-md);
  background-color: rgba(220, 53, 69, 0.1);
  border: 1px solid rgba(220, 53, 69, 0.3);
  border-radius: var(--radius-sm);
  color: #dc3545;
  font-size: 0.9rem;
}

.admin__divider {
  height: 1px;
  background-color: var(--color-border-subtle);
  margin: var(--space-sm) 0;
}

.admin__link-btn,
.admin__link {
  color: var(--color-accent);
  text-decoration: none;
  transition: color var(--transition-fast);
}

.admin__link-btn:hover,
.admin__link:hover {
  color: var(--color-accent-hover);
}

.admin__footer {
  text-align: center;
}

@media (max-width: 768px) {
  .admin {
    padding: var(--space-md);
  }

  .admin__grid {
    grid-template-columns: 1fr;
  }

  .admin__confirm-actions {
    flex-direction: column;
  }

  .admin__suggested-item {
    grid-template-columns: 1fr;
  }
}
</style>
