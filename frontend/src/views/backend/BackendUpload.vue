<script setup lang="ts">
import { computed, ref } from 'vue'
import { suggestImageTags, uploadImage } from '@/api'
import { clearAdminToken } from '@/auth'

const fileInput = ref<HTMLInputElement | null>(null)
const selectedFile = ref<File | null>(null)
const tags = ref('')
const previewUrl = ref('')

// ── 上传状态 ──
const uploadSuccess = ref(false)
const uploadedImageUrl = ref('')
const uploadedImageId = ref<number | null>(null)
const uploadMessage = ref('')
const uploadError = ref('')
const isUploading = ref(false)

// ── AI 建议状态 ──
type SuggestedTagItem = {
  id: number
  value: string
  enabled: boolean
}

const suggestedTags = ref<SuggestedTagItem[]>([])
let suggestedTagId = 0
const isSuggesting = ref(false)
const suggestError = ref('')
const suggestStatus = ref<'idle' | 'loading' | 'empty' | 'error' | 'done'>('idle')

// ── 计算属性 ──
const hasSelectedFile = computed(() => selectedFile.value !== null)
const canSuggestTags = computed(() => hasSelectedFile.value && !isSuggesting.value && !isUploading.value)
const canCommitUpload = computed(() => hasSelectedFile.value && !isUploading.value && !isSuggesting.value)

// ── 工具函数 ──
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
  const enabledSuggested = suggestedTags.value
    .filter(tag => tag.enabled && tag.value.trim())
    .map(tag => tag.value)
  return uniqueTags([...manualTags, ...enabledSuggested])
})

const uploadButtonLabel = computed(() => {
  if (isUploading.value) return '上传中...'
  if (uploadSuccess.value) return '已上传'
  if (!hasSelectedFile.value) return '选择图片后上传'
  return '上传'
})

// ── 文件操作 ──
function onFileChange(e: Event) {
  const input = e.target as HTMLInputElement
  if (input.files && input.files[0]) {
    selectedFile.value = input.files[0]
    previewUrl.value = URL.createObjectURL(input.files[0])
    resetUploadState()
  }
}

function clearFileSelection() {
  selectedFile.value = null
  previewUrl.value = ''
  resetUploadState()
  if (fileInput.value) fileInput.value.value = ''
}

function resetUploadState() {
  uploadSuccess.value = false
  uploadedImageUrl.value = ''
  uploadedImageId.value = null
  uploadMessage.value = ''
  uploadError.value = ''
  suggestedTags.value = []
  suggestError.value = ''
  suggestStatus.value = 'idle'
}

function resetForNextUpload() {
  clearFileSelection()
  tags.value = ''
}

// ── AI 建议 ──
function normalizeSuggestedTag(item: SuggestedTagItem) {
  item.value = item.value.trim().slice(0, 32)
}

function addSuggestedTag() {
  suggestedTags.value = [
    ...suggestedTags.value,
    { id: ++suggestedTagId, value: '', enabled: true },
  ]
}

function removeSuggestedTag(id: number) {
  suggestedTags.value = suggestedTags.value.filter(tag => tag.id !== id)
}

async function handleSuggestTags() {
  if (!selectedFile.value) return

  isSuggesting.value = true
  suggestStatus.value = 'loading'
  suggestError.value = ''
  uploadError.value = ''

  try {
    const res = await suggestImageTags(selectedFile.value)
    if (res.code === 200) {
      suggestedTags.value = createSuggestedTagItems(res.data.suggested_tags)
      suggestStatus.value = res.data.suggested_tags.length === 0 ? 'empty' : 'done'
    } else if (res.code === 401) {
      clearAdminToken()
      suggestError.value = '登录已失效'
      suggestStatus.value = 'error'
    } else {
      suggestError.value = res.message
      suggestStatus.value = 'error'
    }
  } catch {
    suggestError.value = 'AI 标签建议失败'
    suggestStatus.value = 'error'
  } finally {
    isSuggesting.value = false
  }
}

// ── 上传 ──
async function handleUpload() {
  if (!selectedFile.value) return

  isUploading.value = true
  uploadError.value = ''
  uploadMessage.value = ''

  try {
    const res = await uploadImage(selectedFile.value, mergedTagsPreview.value)
    if (res.code === 201) {
      uploadSuccess.value = true
      uploadedImageUrl.value = res.data.url
      uploadedImageId.value = res.data.id
      uploadMessage.value = '上传成功'
      suggestStatus.value = 'idle'
      suggestedTags.value = []
    } else if (res.code === 401) {
      clearAdminToken()
      uploadError.value = '登录已失效'
    } else {
      uploadError.value = res.message
    }
  } catch {
    uploadError.value = '上传失败'
  } finally {
    isUploading.value = false
  }
}
</script>

<template>
  <div class="bu-page">
    <!-- 页面标题 -->
    <div class="bu-page__header">
      <h1 class="bu-page__title">上传图片</h1>
      <p class="bu-page__desc">选择图片，可选 AI 标签建议，然后上传至图库。</p>
    </div>

    <div class="bu-workbench">
      <!-- 左列：文件选择与预览 -->
      <div class="bu-workbench__left">
        <div class="bu-upload-area" @click="fileInput?.click()">
          <input
            ref="fileInput"
            type="file"
            accept="image/*"
            class="bu-upload__input-hidden"
            @change="onFileChange"
          >
          <div v-if="!hasSelectedFile" class="bu-upload__placeholder">
            <span class="bu-upload__icon">↑</span>
            <span class="bu-upload__text">点击选择图片</span>
            <span class="bu-upload__hint">支持 JPG、PNG、GIF 格式</span>
          </div>
          <div v-else class="bu-upload__preview">
            <img :src="previewUrl" alt="预览" class="bu-upload__preview-img">
            <button class="bu-upload__clear-btn" @click.stop="clearFileSelection">✕</button>
          </div>
        </div>
      </div>

      <!-- 右列：标签与上传 -->
      <div class="bu-workbench__right">
        <!-- 手动标签 -->
        <div class="bu-field">
          <label class="bu-label">手动标签</label>
          <input v-model="tags" type="text" class="bu-input" placeholder="输入标签，用逗号分隔">
        </div>

        <!-- AI 建议区 -->
        <div class="bu-field">
          <label class="bu-label">AI 建议标签</label>

          <!-- 状态层 -->
          <div class="bu-ai-status">
            <div v-if="suggestStatus === 'idle'" class="bu-ai-status__idle">
              <button
                class="bu-btn bu-btn--ghost"
                :disabled="!canSuggestTags"
                @click="handleSuggestTags"
              >
                {{ isSuggesting ? '生成中...' : '生成 AI 建议' }}
              </button>
            </div>
            <div v-else-if="suggestStatus === 'loading'" class="bu-ai-status__loading">
              <div class="bu-spinner"></div>
              <span>AI 正在分析图片...</span>
            </div>
            <div v-else-if="suggestStatus === 'empty'" class="bu-ai-status__empty">
              没有可用的 AI 建议标签
              <button class="bu-btn bu-btn--ghost bu-btn--compact" @click="handleSuggestTags">重试</button>
            </div>
            <div v-else-if="suggestStatus === 'error'" class="bu-ai-status__error">
              {{ suggestError }}
              <button class="bu-btn bu-btn--ghost bu-btn--compact" @click="handleSuggestTags">重试</button>
            </div>
          </div>

          <!-- 编辑层 -->
          <div v-if="suggestedTags.length > 0" class="bu-ai-tags">
            <div v-for="tag in suggestedTags" :key="tag.id" class="bu-ai-tag">
              <label class="bu-ai-tag__toggle">
                <input v-model="tag.enabled" type="checkbox">
              </label>
              <input
                v-model="tag.value"
                type="text"
                class="bu-ai-tag__input"
                placeholder="编辑 AI 标签"
                @blur="normalizeSuggestedTag(tag)"
              >
              <button type="button" class="bu-ai-tag__remove" @click="removeSuggestedTag(tag.id)">✕</button>
            </div>
            <button type="button" class="bu-btn bu-btn--ghost bu-btn--compact" @click="addSuggestedTag">
              + 新增标签
            </button>
          </div>
        </div>

        <!-- 结果层：最终标签汇总 -->
        <div class="bu-field">
          <label class="bu-label">最终上传标签</label>
          <div class="bu-tag-summary">
            <span v-if="mergedTagsPreview.length" class="bu-tag-summary__content">
              <span v-for="tag in mergedTagsPreview" :key="tag" class="bu-tag-chip">{{ tag }}</span>
            </span>
            <span v-else class="bu-tag-summary__empty">当前未选择任何标签</span>
          </div>
        </div>

        <!-- 主操作按钮 -->
        <button
          class="bu-btn bu-btn--primary"
          :disabled="!canCommitUpload"
          @click="handleUpload"
        >
          {{ uploadButtonLabel }}
        </button>

        <!-- 上传成功 & 继续上传 -->
        <div v-if="uploadSuccess" class="bu-result bu-result--success">
          <span class="bu-result__icon">✓</span>
          <span>{{ uploadMessage }}</span>
          <span v-if="uploadedImageId" class="bu-result__id">#{{ uploadedImageId }}</span>
          <button class="bu-btn bu-btn--ghost bu-btn--compact" @click="resetForNextUpload">
            继续上传下一张
          </button>
        </div>

        <div v-if="uploadError" class="bu-result bu-result--error">
          {{ uploadError }}
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.bu-page {
  max-width: 1100px;
}

.bu-page__header {
  margin-bottom: var(--space-xl);
}

.bu-page__title {
  font-family: var(--font-display);
  font-size: 1.35rem;
  color: var(--terminal-text-bright);
  margin-bottom: var(--space-xs);
}

.bu-page__desc {
  color: var(--terminal-text-dim);
  font-size: 0.85rem;
}

/* ── 工作台布局 ── */
.bu-workbench {
  display: grid;
  grid-template-columns: minmax(0, 1.2fr) minmax(0, 1fr);
  gap: var(--space-xl);
  align-items: start;
}

.bu-workbench__left,
.bu-workbench__right {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

/* ── 上传区域 ── */
.bu-upload-area {
  position: relative;
  border: 2px dashed var(--terminal-border);
  border-radius: var(--radius-md);
  cursor: pointer;
  min-height: 260px;
  transition: border-color var(--transition-fast);
  background-color: var(--terminal-surface);
}

.bu-upload-area:hover {
  border-color: var(--terminal-accent);
}

.bu-upload__input-hidden {
  display: none;
}

.bu-upload__placeholder,
.bu-upload__preview {
  min-height: 260px;
  display: grid;
  place-items: center;
}

.bu-upload__placeholder {
  text-align: center;
  color: var(--terminal-text-dim);
}

.bu-upload__icon {
  font-size: 2.5rem;
  color: var(--terminal-accent);
  display: block;
  margin-bottom: var(--space-sm);
}

.bu-upload__text {
  display: block;
  font-size: 1rem;
  color: var(--terminal-text);
}

.bu-upload__hint {
  display: block;
  font-size: 0.8rem;
  margin-top: var(--space-xs);
}

.bu-upload__preview-img {
  width: 100%;
  height: 260px;
  object-fit: contain;
}

.bu-upload__clear-btn {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 28px;
  height: 28px;
  display: grid;
  place-items: center;
  background: var(--terminal-bg);
  border: 1px solid var(--terminal-border);
  border-radius: var(--radius-sm);
  color: var(--terminal-text-dim);
  cursor: pointer;
  font-size: 0.75rem;
  transition: all var(--transition-fast);
}

.bu-upload__clear-btn:hover {
  color: var(--terminal-danger);
  border-color: var(--terminal-danger);
}

/* ── 表单字段 ── */
.bu-field {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.bu-label {
  font-size: 0.8rem;
  color: var(--terminal-text-dim);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.bu-input {
  width: 100%;
  padding: 0.75rem 1rem;
  border: 1px solid var(--terminal-border);
  border-radius: var(--radius-sm);
  background-color: var(--terminal-bg);
  color: var(--terminal-text-bright);
  font-family: var(--font-body);
  font-size: 0.9rem;
  transition: border-color var(--transition-fast);
}

.bu-input:focus {
  outline: none;
  border-color: var(--terminal-accent);
  box-shadow: 0 0 0 2px var(--terminal-accent-glow);
}

.bu-input::placeholder {
  color: var(--terminal-text-dim);
}

/* ── AI 建议状态 ── */
.bu-ai-status {
  min-height: 36px;
  display: flex;
  align-items: center;
}

.bu-ai-status__idle {
  width: 100%;
}

.bu-ai-status__loading {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  color: var(--terminal-text-dim);
  font-size: 0.85rem;
}

.bu-ai-status__empty,
.bu-ai-status__error {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  font-size: 0.85rem;
}

.bu-ai-status__empty {
  color: var(--terminal-text-dim);
}

.bu-ai-status__error {
  color: var(--terminal-danger);
}

/* ── AI 标签编辑 ── */
.bu-ai-tags {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  margin-top: var(--space-sm);
}

.bu-ai-tag {
  display: grid;
  grid-template-columns: auto 1fr auto;
  gap: var(--space-sm);
  align-items: center;
}

.bu-ai-tag__toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
}

.bu-ai-tag__input {
  width: 100%;
  padding: 0.55rem 0.75rem;
  border: 1px solid var(--terminal-border);
  border-radius: var(--radius-sm);
  background-color: var(--terminal-bg);
  color: var(--terminal-text-bright);
  font-size: 0.85rem;
}

.bu-ai-tag__input:focus {
  outline: none;
  border-color: var(--terminal-accent);
}

.bu-ai-tag__remove {
  width: 24px;
  height: 24px;
  display: grid;
  place-items: center;
  background: transparent;
  border: 1px solid var(--terminal-border);
  border-radius: var(--radius-sm);
  color: var(--terminal-text-dim);
  cursor: pointer;
  font-size: 0.7rem;
  transition: all var(--transition-fast);
}

.bu-ai-tag__remove:hover {
  color: var(--terminal-danger);
  border-color: var(--terminal-danger);
}

/* ── 标签汇总 ── */
.bu-tag-summary {
  padding: var(--space-sm) var(--space-md);
  border: 1px solid var(--terminal-border);
  border-radius: var(--radius-sm);
  background-color: var(--terminal-bg);
  min-height: 36px;
}

.bu-tag-summary__content {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-xs);
}

.bu-tag-chip {
  display: inline-flex;
  padding: 2px var(--space-sm);
  border-radius: var(--radius-sm);
  background-color: var(--terminal-accent-glow);
  color: var(--terminal-accent);
  font-size: 0.78rem;
}

.bu-tag-summary__empty {
  color: var(--terminal-text-dim);
  font-size: 0.85rem;
}

/* ── 按钮 ── */
.bu-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.7rem 1rem;
  border: 1px solid transparent;
  border-radius: var(--radius-sm);
  font-family: var(--font-body);
  font-size: 0.9rem;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.bu-btn--primary {
  background-color: var(--terminal-accent);
  color: var(--terminal-bg);
  font-weight: 500;
}

.bu-btn--primary:hover:not(:disabled) {
  box-shadow: 0 0 24px var(--terminal-accent-glow);
}

.bu-btn--primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.bu-btn--ghost {
  background: transparent;
  border-color: var(--terminal-border);
  color: var(--terminal-text);
}

.bu-btn--ghost:hover:not(:disabled) {
  border-color: var(--terminal-accent);
  color: var(--terminal-accent);
}

.bu-btn--ghost:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.bu-btn--compact {
  padding: 0.45rem 0.7rem;
  font-size: 0.8rem;
}

/* ── 结果提示 ── */
.bu-result {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-sm) var(--space-md);
  border-radius: var(--radius-sm);
  font-size: 0.85rem;
}

.bu-result--success {
  background-color: rgba(61, 214, 140, 0.1);
  color: var(--terminal-success);
  border: 1px solid rgba(61, 214, 140, 0.2);
}

.bu-result--error {
  background-color: var(--terminal-danger-dim);
  color: var(--terminal-danger);
  border: 1px solid rgba(229, 69, 69, 0.2);
}

.bu-result__icon {
  font-weight: 700;
}

.bu-result__id {
  color: var(--terminal-accent);
  font-family: var(--font-display);
}

/* ── 加载动画 ── */
.bu-spinner {
  width: 18px;
  height: 18px;
  border: 2px solid var(--terminal-border);
  border-top-color: var(--terminal-accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* ── 响应式 ── */
@media (max-width: 768px) {
  .bu-workbench {
    grid-template-columns: 1fr;
  }
}
</style>
