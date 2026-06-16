<script setup lang="ts">
import { ref } from 'vue'
import { uploadImage, deleteImage, clearCache } from '@/api'

const appkey = ref('')
const selectedFile = ref<File | null>(null)
const tags = ref('')
const imageId = ref('')
const previewUrl = ref('')
const uploadSuccess = ref(false)
const uploadMessage = ref('')
const isLoading = ref(false)

function onFileChange(e: Event) {
  const input = e.target as HTMLInputElement
  if (input.files && input.files[0]) {
    selectedFile.value = input.files[0]
    previewUrl.value = URL.createObjectURL(input.files[0])
    uploadSuccess.value = false
    uploadMessage.value = ''
  }
}

async function handleUpload() {
  if (!appkey.value) {
    alert('请输入管理员密码')
    return
  }
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
    } else if (res.code === 401) {
      alert('密码错误，无权限')
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
  if (!appkey.value) {
    alert('请输入管理员密码')
    return
  }
  if (!imageId.value) {
    alert('请输入图片 ID')
    return
  }

  const rmfile = confirm('是否删除文件？')

  isLoading.value = true
  try {
    const res = await deleteImage(parseInt(imageId.value), appkey.value, rmfile)
    if (res.code === 204) {
      alert('删除成功')
      imageId.value = ''
    } else if (res.code === 401) {
      alert('密码错误，无权限')
    } else {
      alert(res.message)
    }
  } catch {
    alert('删除失败')
  } finally {
    isLoading.value = false
  }
}

async function handleClearCache() {
  if (!appkey.value) {
    alert('请输入管理员密码')
    return
  }

  isLoading.value = true
  try {
    const res = await clearCache(appkey.value)
    if (res.code === 200) {
      alert('缓存已清除')
    } else if (res.code === 401) {
      alert('密码错误，无权限')
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
    <div class="backend__card">
      <h2 class="backend__title">图片上传</h2>

      <div class="backend__field">
        <label for="appkey">管理员密码</label>
        <input
          id="appkey"
          v-model="appkey"
          type="password"
          class="backend__input"
          placeholder="输入密码..."
        >
      </div>

      <div class="backend__field">
        <label for="file">选择图片</label>
        <input
          id="file"
          type="file"
          accept="image/*"
          class="backend__file-input"
          @change="onFileChange"
        >
      </div>

      <div class="backend__field">
        <label for="tags">标签（逗号分隔）</label>
        <input
          id="tags"
          v-model="tags"
          type="text"
          class="backend__input"
          placeholder="风景, 自然, 美丽..."
        >
      </div>

      <div v-if="previewUrl" class="backend__preview">
        <img :src="previewUrl" alt="预览" class="backend__preview-img">
      </div>

      <button
        class="backend__btn backend__btn--primary"
        :disabled="isLoading"
        @click="handleUpload"
      >
        {{ isLoading ? '上传中...' : '上传' }}
      </button>

      <div v-if="uploadSuccess" class="backend__success">
        ✦ {{ uploadMessage }}
      </div>
    </div>

    <div class="backend__card">
      <h2 class="backend__title">管理操作</h2>

      <div class="backend__field">
        <label for="imageId">图片 ID</label>
        <input
          id="imageId"
          v-model="imageId"
          type="text"
          class="backend__input"
          placeholder="输入要删除的图片 ID..."
        >
      </div>

      <button
        class="backend__btn backend__btn--danger"
        :disabled="isLoading"
        @click="handleDelete"
      >
        删除图片
      </button>

      <hr class="backend__divider">

      <button
        class="backend__btn backend__btn--secondary"
        :disabled="isLoading"
        @click="handleClearCache"
      >
        清除缓存
      </button>
    </div>

    <div class="backend__links">
      <RouterLink to="/" class="backend__link">← 返回画廊</RouterLink>
      <a href="/docs" class="backend__link">API 文档</a>
    </div>
  </div>
</template>

<style scoped>
.backend {
  max-width: 600px;
  margin: 0 auto;
  padding: var(--space-md) var(--space-lg);
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
}

.backend__card {
  background-color: var(--color-surface);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-md);
  padding: var(--space-lg);
}

.backend__title {
  margin-bottom: var(--space-lg);
  color: var(--color-text);
  font-size: 1.25rem;
}

.backend__field {
  margin-bottom: var(--space-md);
}

.backend__field label {
  display: block;
  margin-bottom: var(--space-xs);
  color: var(--color-text-secondary);
  font-size: 0.85rem;
}

.backend__input {
  width: 100%;
  padding: var(--space-sm) var(--space-md);
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

.backend__input:focus {
  border-color: var(--color-accent);
  box-shadow: 0 0 0 2px var(--color-accent-glow);
}

.backend__file-input {
  width: 100%;
  padding: var(--space-sm);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background-color: var(--color-bg);
  color: var(--color-text);
}

.backend__preview {
  margin-bottom: var(--space-md);
  border-radius: var(--radius-sm);
  overflow: hidden;
}

.backend__preview-img {
  max-width: 100%;
  height: auto;
  display: block;
}

.backend__btn {
  width: 100%;
  padding: var(--space-sm) var(--space-md);
  border: none;
  border-radius: var(--radius-sm);
  font-size: 1rem;
  cursor: pointer;
  transition:
    background-color var(--transition-fast),
    opacity var(--transition-fast);
}

.backend__btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.backend__btn--primary {
  background-color: var(--color-accent);
  color: var(--color-bg);
}

.backend__btn--primary:hover:not(:disabled) {
  background-color: var(--color-accent-hover);
}

.backend__btn--danger {
  background-color: #dc3545;
  color: #fff;
}

.backend__btn--danger:hover:not(:disabled) {
  background-color: #c82333;
}

.backend__btn--secondary {
  background-color: var(--color-bg);
  color: var(--color-text);
  border: 1px solid var(--color-border);
}

.backend__btn--secondary:hover:not(:disabled) {
  background-color: var(--color-surface-hover);
}

.backend__success {
  margin-top: var(--space-md);
  padding: var(--space-sm) var(--space-md);
  background-color: var(--color-accent-glow);
  border-radius: var(--radius-sm);
  color: var(--color-accent);
  text-align: center;
}

.backend__divider {
  margin: var(--space-lg) 0;
  border: none;
  border-top: 1px solid var(--color-border-subtle);
}

.backend__links {
  display: flex;
  justify-content: space-between;
}

.backend__link {
  color: var(--color-text-secondary);
  font-size: 0.9rem;
  transition: color var(--transition-fast);
}

.backend__link:hover {
  color: var(--color-accent);
}
</style>