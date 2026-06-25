<script setup lang="ts">
import { ref, watch } from 'vue'
import { getAdminImages, deleteImage, getImageUrl, updateImage } from '@/api'
import { clearAdminToken } from '@/auth'
import type { Image } from '@/api/types'

// ── 查询参数 ──
const searchId = ref('')
const searchTag = ref('')
const nsfwFilter = ref<'all' | 'true' | 'false'>('all')
const sortBy = ref<'id_desc' | 'id_asc' | 'created_at_desc' | 'created_at_asc'>('id_desc')
const currentPage = ref(1)
const pageSize = 20

// ── 列表数据 ──
const images = ref<Image[]>([])
const total = ref(0)
const lastPage = ref(false)
const isLoading = ref(false)
const errorMsg = ref('')

// ── 详情抽屉 ──
const drawerOpen = ref(false)
const drawerImage = ref<Image | null>(null)
const editTags = ref('')
const editNsfw = ref(false)
const isSaving = ref(false)
const saveMsg = ref('')

// ── 删除确认 ──
const deleteConfirmId = ref<number | null>(null)

// ── 查询 ──
async function fetchImages() {
  isLoading.value = true
  errorMsg.value = ''

  try {
    const idNum = searchId.value.trim() ? Number(searchId.value.trim()) : undefined
    const nsfw = nsfwFilter.value === 'all' ? undefined : nsfwFilter.value === 'true'

    const res = await getAdminImages({
      page: currentPage.value,
      page_size: pageSize,
      id: idNum && !Number.isNaN(idNum) ? idNum : undefined,
      tag: searchTag.value.trim() || undefined,
      nsfw,
      sort: sortBy.value,
    })

    if (res.code === 401) {
      clearAdminToken()
      errorMsg.value = '登录已失效'
      return
    }

    if (res.code !== 200) {
      errorMsg.value = res.message
      return
    }

    images.value = res.data.images
    total.value = res.data.total
    lastPage.value = res.data.last
  } catch {
    errorMsg.value = '查询失败'
  } finally {
    isLoading.value = false
  }
}

function handleSearch() {
  currentPage.value = 1
  fetchImages()
}

function resetSearch() {
  searchId.value = ''
  searchTag.value = ''
  nsfwFilter.value = 'all'
  sortBy.value = 'id_desc'
  currentPage.value = 1
  fetchImages()
}

function goToPage(page: number) {
  currentPage.value = Math.max(1, page)
  fetchImages()
}

// ── 详情抽屉 ──
function openDrawer(image: Image) {
  drawerImage.value = { ...image }
  editTags.value = image.tags.join(', ')
  editNsfw.value = image.nsfw
  drawerOpen.value = true
  saveMsg.value = ''
}

function closeDrawer() {
  drawerOpen.value = false
  drawerImage.value = null
}

async function saveImage() {
  if (!drawerImage.value) return
  isSaving.value = true
  saveMsg.value = ''

  try {
    const newTags = editTags.value.split(',').map(t => t.trim()).filter(Boolean)
    const nsfwChanged = editNsfw.value !== drawerImage.value.nsfw
    const tagsChanged = JSON.stringify(newTags) !== JSON.stringify(drawerImage.value.tags)

    if (!nsfwChanged && !tagsChanged) {
      saveMsg.value = '无变更'
      return
    }

    const res = await updateImage(drawerImage.value.id, {
      ...(tagsChanged ? { tags: newTags } : {}),
      ...(nsfwChanged ? { nsfw: editNsfw.value } : {}),
    })

    if (res.code === 401) {
      clearAdminToken()
      saveMsg.value = '登录已失效'
    } else {
      saveMsg.value = '已保存'
      if (drawerImage.value) {
        drawerImage.value.tags = newTags
        drawerImage.value.nsfw = editNsfw.value
      }
      // 同步更新列表
      const idx = images.value.findIndex(img => img.id === drawerImage.value?.id)
      if (idx !== -1) {
        images.value[idx] = { ...images.value[idx], tags: newTags, nsfw: editNsfw.value }
      }
    }
  } catch {
    saveMsg.value = '更新失败'
  } finally {
    isSaving.value = false
  }
}

// ── 删除 ──
function confirmDelete(id: number) {
  deleteConfirmId.value = id
}

function cancelDelete() {
  deleteConfirmId.value = null
}

async function executeDelete(id: number) {
  try {
    const res = await deleteImage(id)
    if (res.code === 204) {
      images.value = images.value.filter(img => img.id !== id)
      total.value = Math.max(0, total.value - 1)
      if (drawerImage.value?.id === id) closeDrawer()
    } else if (res.code === 401) {
      clearAdminToken()
    }
  } catch {
    // 静默失败
  } finally {
    deleteConfirmId.value = null
  }
}

function formatTime(val: string | null): string {
  if (!val) return '—'
  const d = new Date(val)
  if (Number.isNaN(d.getTime())) return val
  return new Intl.DateTimeFormat('zh-CN', { dateStyle: 'short', timeStyle: 'short' }).format(d)
}

// 初始化加载
fetchImages()

// 监听排序/过滤变化自动刷新
watch([nsfwFilter, sortBy], () => {
  currentPage.value = 1
  fetchImages()
})
</script>

<template>
  <div class="bi-page">
    <!-- 页面标题 -->
    <div class="bi-page__header">
      <h1 class="bi-page__title">图片管理</h1>
      <p class="bi-page__desc">查看、搜索、编辑和管理图库中的图片。</p>
    </div>

    <!-- 查询区 -->
    <div class="bi-query">
      <div class="bi-query__primary">
        <div class="bi-field">
          <label class="bi-label">ID 精确查找</label>
          <input
            v-model="searchId"
            type="number"
            class="bi-input"
            placeholder="输入图片 ID"
            @keyup.enter="handleSearch"
          >
        </div>
        <div class="bi-field">
          <label class="bi-label">标签搜索</label>
          <input
            v-model="searchTag"
            type="text"
            class="bi-input"
            placeholder="输入标签关键词"
            @keyup.enter="handleSearch"
          >
        </div>
      </div>

      <div class="bi-query__filters">
        <div class="bi-field">
          <label class="bi-label">NSFW</label>
          <select v-model="nsfwFilter" class="bi-select">
            <option value="all">全部</option>
            <option value="false">仅 SFW</option>
            <option value="true">仅 NSFW</option>
          </select>
        </div>
        <div class="bi-field">
          <label class="bi-label">排序</label>
          <select v-model="sortBy" class="bi-select">
            <option value="id_desc">ID 递减</option>
            <option value="id_asc">ID 递增</option>
            <option value="created_at_desc">时间最新</option>
            <option value="created_at_asc">时间最早</option>
          </select>
        </div>
        <div class="bi-query__actions">
          <button class="bi-btn bi-btn--primary" @click="handleSearch">搜索</button>
          <button class="bi-btn bi-btn--ghost" @click="resetSearch">重置</button>
        </div>
      </div>
    </div>

    <!-- 信息栏 -->
    <div class="bi-info">
      <span class="bi-info__count">共 {{ total }} 张</span>
      <span v-if="isLoading" class="bi-info__loading">
        <span class="bi-spinner"></span> 查询中...
      </span>
    </div>

    <!-- 错误提示 -->
    <div v-if="errorMsg" class="bi-error">{{ errorMsg }}</div>

    <!-- 表格 -->
    <div class="bi-table-wrap">
      <table v-if="images.length > 0" class="bi-table">
        <thead>
          <tr>
            <th class="bi-table__th--thumb"></th>
            <th>ID</th>
            <th>标签</th>
            <th>时间</th>
            <th>NSFW</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="img in images" :key="img.id">
            <td>
              <img :src="getImageUrl(img.id, true)" :alt="img.tags.join(', ')" class="bi-thumb" loading="lazy">
            </td>
            <td class="bi-table__id">#{{ img.id }}</td>
            <td>
              <div class="bi-table__tags">
                <span v-for="tag in img.tags.slice(0, 3)" :key="tag" class="bi-tag-chip">{{ tag }}</span>
                <span v-if="img.tags.length > 3" class="bi-tag-more">+{{ img.tags.length - 3 }}</span>
              </div>
            </td>
            <td class="bi-table__time">{{ formatTime(img.created_at) }}</td>
            <td>
              <span class="bi-nsfw-badge" :class="{ 'bi-nsfw-badge--active': img.nsfw }">
                {{ img.nsfw ? 'R18' : 'SFW' }}
              </span>
            </td>
            <td>
              <div class="bi-table__actions">
                <button class="bi-btn bi-btn--ghost bi-btn--compact" @click="openDrawer(img)">详情</button>
                <button class="bi-btn bi-btn--ghost bi-btn--compact" @click="openDrawer(img)">编辑</button>
                <button
                  v-if="deleteConfirmId !== img.id"
                  class="bi-btn bi-btn--danger bu-btn--compact"
                  @click="confirmDelete(img.id)"
                >删除</button>
                <template v-else>
                  <button class="bi-btn bi-btn--danger-fill bi-btn--compact" @click="executeDelete(img.id)">确认 #{{ img.id }}</button>
                  <button class="bi-btn bi-btn--ghost bi-btn--compact" @click="cancelDelete">取消</button>
                </template>
              </div>
            </td>
          </tr>
        </tbody>
      </table>

      <!-- 空状态 -->
      <div v-else-if="!isLoading" class="bi-empty">
        <span class="bi-empty__icon">∅</span>
        <p>没有找到图片</p>
      </div>
    </div>

    <!-- 分页 -->
    <div v-if="images.length > 0" class="bi-pagination">
      <button
        class="bi-btn bi-btn--ghost bi-btn--compact"
        :disabled="currentPage <= 1"
        @click="goToPage(currentPage - 1)"
      >上一页</button>
      <span class="bi-pagination__info">第 {{ currentPage }} 页</span>
      <button
        class="bi-btn bi-btn--ghost bi-btn--compact"
        :disabled="lastPage"
        @click="goToPage(currentPage + 1)"
      >下一页</button>
    </div>

    <!-- 右侧详情抽屉 -->
    <Teleport to="body">
      <div v-if="drawerOpen" class="bi-drawer-overlay" @click.self="closeDrawer"></div>
      <div class="bi-drawer" :class="{ 'bi-drawer--open': drawerOpen }">
        <div v-if="drawerImage" class="bi-drawer__content">
          <div class="bi-drawer__header">
            <h2 class="bi-drawer__title">图片 #{{ drawerImage.id }}</h2>
            <button class="bi-drawer__close" @click="closeDrawer">✕</button>
          </div>

          <!-- 大图 -->
          <div class="bi-drawer__image">
            <img :src="getImageUrl(drawerImage.id)" alt="预览" loading="lazy">
          </div>

          <!-- 元信息 -->
          <div class="bi-drawer__meta">
            <div class="bi-drawer__meta-row">
              <span>ID</span>
              <span>{{ drawerImage.id }}</span>
            </div>
            <div class="bi-drawer__meta-row">
              <span>创建时间</span>
              <span>{{ formatTime(drawerImage.created_at) }}</span>
            </div>
            <div class="bi-drawer__meta-row">
              <span>NSFW 状态</span>
              <label class="bi-toggle">
                <input v-model="editNsfw" type="checkbox" class="bi-toggle__input">
                <span class="bi-toggle__slider"></span>
                <span class="bi-toggle__label" :class="{ 'bi-toggle__label--nsfw': editNsfw }">
                  {{ editNsfw ? 'R18' : 'SFW' }}
                </span>
              </label>
            </div>
            <div v-if="drawerImage.nsfw_score > 0" class="bi-drawer__meta-row">
              <span>NSFW 评分</span>
              <span>{{ (drawerImage.nsfw_score * 100).toFixed(1) }}%</span>
            </div>
          </div>

          <!-- 标签编辑 -->
          <div class="bi-drawer__tags-section">
            <label class="bi-label">标签（逗号分隔）</label>
            <textarea v-model="editTags" class="bi-textarea" rows="3" placeholder="输入标签，用逗号分隔"></textarea>
            <div class="bi-drawer__tags-actions">
              <button class="bi-btn bi-btn--primary bi-btn--compact" :disabled="isSaving" @click="saveImage">
                {{ isSaving ? '保存中...' : '保存修改' }}
              </button>
              <span v-if="saveMsg" class="bi-drawer__save-msg">{{ saveMsg }}</span>
            </div>
          </div>

          <!-- 删除 -->
          <div class="bi-drawer__danger">
            <button
              v-if="deleteConfirmId !== drawerImage.id"
              class="bi-btn bi-btn--danger bi-btn--compact"
              @click="confirmDelete(drawerImage.id)"
            >删除此图片</button>
            <template v-else>
              <p class="bi-drawer__confirm-text">确定要删除图片 #{{ drawerImage.id }} 吗？此操作不可撤销。</p>
              <div class="bi-drawer__confirm-actions">
                <button class="bi-btn bi-btn--danger-fill bi-btn--compact" @click="executeDelete(drawerImage.id)">确认删除</button>
                <button class="bi-btn bi-btn--ghost bi-btn--compact" @click="cancelDelete">取消</button>
              </div>
            </template>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.bi-page {
  max-width: 1200px;
}

.bi-page__header {
  margin-bottom: var(--space-lg);
}

.bi-page__title {
  font-family: var(--font-display);
  font-size: 1.35rem;
  color: var(--terminal-text-bright);
  margin-bottom: var(--space-xs);
}

.bi-page__desc {
  color: var(--terminal-text-dim);
  font-size: 0.85rem;
}

/* ── 查询区 ── */
.bi-query {
  padding: var(--space-md);
  background-color: var(--terminal-surface);
  border: 1px solid var(--terminal-border);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-md);
}

.bi-query__primary {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-md);
  margin-bottom: var(--space-md);
}

.bi-query__filters {
  display: flex;
  gap: var(--space-md);
  align-items: flex-end;
  flex-wrap: wrap;
}

.bi-query__actions {
  display: flex;
  gap: var(--space-sm);
}

/* ── 表单 ── */
.bi-field {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.bi-label {
  font-size: 0.75rem;
  color: var(--terminal-text-dim);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.bi-input,
.bi-select {
  padding: 0.6rem 0.85rem;
  border: 1px solid var(--terminal-border);
  border-radius: var(--radius-sm);
  background-color: var(--terminal-bg);
  color: var(--terminal-text-bright);
  font-size: 0.85rem;
  transition: border-color var(--transition-fast);
}

.bi-input:focus,
.bi-select:focus {
  outline: none;
  border-color: var(--terminal-accent);
}

.bi-select {
  min-width: 120px;
  cursor: pointer;
}

.bi-textarea {
  width: 100%;
  padding: 0.6rem 0.85rem;
  border: 1px solid var(--terminal-border);
  border-radius: var(--radius-sm);
  background-color: var(--terminal-bg);
  color: var(--terminal-text-bright);
  font-family: var(--font-body);
  font-size: 0.85rem;
  resize: vertical;
}

.bi-textarea:focus {
  outline: none;
  border-color: var(--terminal-accent);
}

/* ── 信息栏 ── */
.bi-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-sm);
  font-size: 0.8rem;
  color: var(--terminal-text-dim);
}

.bi-info__loading {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
}

.bi-error {
  color: var(--terminal-danger);
  font-size: 0.85rem;
  padding: var(--space-sm) 0;
}

/* ── 表格 ── */
.bi-table-wrap {
  overflow-x: auto;
}

.bi-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.85rem;
}

.bi-table th {
  text-align: left;
  padding: var(--space-sm) var(--space-md);
  color: var(--terminal-text-dim);
  font-weight: 500;
  border-bottom: 1px solid var(--terminal-border);
  white-space: nowrap;
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.bi-table td {
  padding: var(--space-sm) var(--space-md);
  border-bottom: 1px solid var(--terminal-border);
  color: var(--terminal-text);
  vertical-align: middle;
}

.bi-table tr:hover td {
  background-color: var(--terminal-surface-hover);
}

.bi-table__th--thumb {
  width: 56px;
}

.bi-thumb {
  width: 48px;
  height: 48px;
  object-fit: cover;
  border-radius: var(--radius-sm);
  border: 1px solid var(--terminal-border);
}

.bi-table__id {
  color: var(--terminal-accent);
  font-family: var(--font-display);
  white-space: nowrap;
}

.bi-table__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.bi-tag-chip {
  display: inline-flex;
  padding: 1px 6px;
  border-radius: var(--radius-sm);
  background-color: var(--terminal-accent-glow);
  color: var(--terminal-accent);
  font-size: 0.72rem;
  white-space: nowrap;
}

.bi-tag-more {
  font-size: 0.72rem;
  color: var(--terminal-text-dim);
}

.bi-table__time {
  white-space: nowrap;
  color: var(--terminal-text-dim);
  font-size: 0.8rem;
}

.bi-table__actions {
  display: flex;
  gap: 4px;
  flex-wrap: nowrap;
}

.bi-nsfw-badge {
  display: inline-flex;
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  font-size: 0.72rem;
  background-color: var(--terminal-surface);
  border: 1px solid var(--terminal-border);
  color: var(--terminal-text-dim);
}

.bi-nsfw-badge--active {
  border-color: var(--terminal-danger);
  color: var(--terminal-danger);
  background-color: var(--terminal-danger-dim);
}

/* ── 按钮 ── */
.bi-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.55rem 0.85rem;
  border: 1px solid transparent;
  border-radius: var(--radius-sm);
  font-size: 0.85rem;
  cursor: pointer;
  font-family: var(--font-body);
  transition: all var(--transition-fast);
}

.bi-btn--primary {
  background-color: var(--terminal-accent);
  color: var(--terminal-bg);
}

.bi-btn--primary:hover:not(:disabled) {
  box-shadow: 0 0 16px var(--terminal-accent-glow);
}

.bi-btn--ghost {
  background: transparent;
  border-color: var(--terminal-border);
  color: var(--terminal-text);
}

.bi-btn--ghost:hover:not(:disabled) {
  border-color: var(--terminal-accent);
  color: var(--terminal-accent);
}

.bi-btn--ghost:disabled,
.bi-btn--primary:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.bi-btn--danger {
  background: transparent;
  border-color: var(--terminal-border);
  color: var(--terminal-text);
}

.bi-btn--danger:hover {
  border-color: var(--terminal-danger);
  color: var(--terminal-danger);
}

.bi-btn--danger-fill {
  background-color: var(--terminal-danger);
  border-color: var(--terminal-danger);
  color: #fff;
}

.bi-btn--compact {
  padding: 0.4rem 0.6rem;
  font-size: 0.78rem;
}

/* ── 空状态 ── */
.bi-empty {
  text-align: center;
  padding: var(--space-2xl);
  color: var(--terminal-text-dim);
}

.bi-empty__icon {
  font-size: 2rem;
  display: block;
  margin-bottom: var(--space-sm);
  color: var(--terminal-border-active);
}

/* ── 分页 ── */
.bi-pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: var(--space-md);
  padding: var(--space-lg) 0;
}

.bi-pagination__info {
  font-size: 0.85rem;
  color: var(--terminal-text-dim);
}

/* ── 加载动画 ── */
.bi-spinner {
  width: 14px;
  height: 14px;
  border: 2px solid var(--terminal-border);
  border-top-color: var(--terminal-accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  display: inline-block;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* ── 详情抽屉 ── */
.bi-drawer-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  z-index: var(--z-modal);
}

.bi-drawer {
  position: fixed;
  top: 0;
  right: 0;
  bottom: 0;
  width: min(480px, 90vw);
  background-color: var(--terminal-surface);
  border-left: 1px solid var(--terminal-border);
  z-index: calc(var(--z-modal) + 1);
  transform: translateX(100%);
  transition: transform var(--transition-base);
  overflow-y: auto;
}

.bi-drawer--open {
  transform: translateX(0);
}

.bi-drawer__content {
  padding: var(--space-lg);
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
}

.bi-drawer__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.bi-drawer__title {
  font-family: var(--font-display);
  font-size: 1.15rem;
  color: var(--terminal-text-bright);
}

.bi-drawer__close {
  width: 32px;
  height: 32px;
  display: grid;
  place-items: center;
  background: transparent;
  border: 1px solid var(--terminal-border);
  border-radius: var(--radius-sm);
  color: var(--terminal-text-dim);
  cursor: pointer;
  font-size: 0.85rem;
  transition: all var(--transition-fast);
}

.bi-drawer__close:hover {
  border-color: var(--terminal-accent);
  color: var(--terminal-accent);
}

.bi-drawer__image img {
  width: 100%;
  max-height: 50vh;
  object-fit: contain;
  border-radius: var(--radius-md);
  background-color: var(--terminal-bg);
}

.bi-drawer__meta {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.bi-drawer__meta-row {
  display: flex;
  justify-content: space-between;
  font-size: 0.85rem;
  color: var(--terminal-text);
}

.bi-drawer__meta-row > :first-child {
  color: var(--terminal-text-dim);
}

/* ── Toggle 开关 ── */
.bi-toggle {
  display: inline-flex;
  align-items: center;
  gap: var(--space-sm);
  cursor: pointer;
}

.bi-toggle__input {
  display: none;
}

.bi-toggle__slider {
  position: relative;
  width: 40px;
  height: 22px;
  background-color: var(--terminal-border);
  border-radius: 11px;
  transition: background-color var(--transition-fast);
}

.bi-toggle__slider::after {
  content: '';
  position: absolute;
  top: 3px;
  left: 3px;
  width: 16px;
  height: 16px;
  background-color: var(--terminal-text-bright);
  border-radius: 50%;
  transition: transform var(--transition-fast);
}

.bi-toggle__input:checked + .bi-toggle__slider {
  background-color: var(--terminal-danger);
}

.bi-toggle__input:checked + .bi-toggle__slider::after {
  transform: translateX(18px);
}

.bi-toggle__label {
  font-size: 0.78rem;
  font-family: var(--font-display);
  color: var(--terminal-text-dim);
  min-width: 28px;
}

.bi-toggle__label--nsfw {
  color: var(--terminal-danger);
}

.bi-drawer__tags-section {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.bi-drawer__tags-actions {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.bi-drawer__save-msg {
  font-size: 0.8rem;
  color: var(--terminal-success);
}

.bi-drawer__danger {
  padding-top: var(--space-md);
  border-top: 1px solid var(--terminal-border);
}

.bi-drawer__confirm-text {
  color: var(--terminal-danger);
  font-size: 0.85rem;
  margin-bottom: var(--space-sm);
}

.bi-drawer__confirm-actions {
  display: flex;
  gap: var(--space-sm);
}

/* ── 响应式 ── */
@media (max-width: 768px) {
  .bi-query__primary {
    grid-template-columns: 1fr;
  }

  .bi-query__filters {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
