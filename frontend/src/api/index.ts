import type {
  ApiResponse,
  ImagesListData,
  TagSearchData,
  AllTagsData,
  UploadData,
  Image,
  LoginData,
  AiTagSuggestionData,
  AdminImageQuery,
} from './types'
import { getAdminToken } from '@/auth'

const API_BASE = '/api'

/** 统一请求封装 */
async function request<T>(
  path: string,
  options?: RequestInit
): Promise<ApiResponse<T>> {
  const res = await fetch(`${API_BASE}${path}`, options)
  const payload = await res.json()

  if ('code' in payload && 'message' in payload) {
    return payload as ApiResponse<T>
  }

  return {
    code: res.status,
    message: payload.detail || res.statusText || '请求失败',
    data: null as T,
  }
}

function withAdminAuth(options: RequestInit = {}): RequestInit {
  const headers = new Headers(options.headers ?? {})
  const token = getAdminToken()

  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }

  return {
    ...options,
    headers,
  }
}

/** 获取验证码图片 */
export async function getCaptcha(): Promise<{ captchaId: string; imageUrl: string }> {
  const res = await fetch(`${API_BASE}/captcha`)
  const captchaId = res.headers.get('X-Captcha-Id') || ''
  const blob = await res.blob()
  const imageUrl = URL.createObjectURL(blob)
  return { captchaId, imageUrl }
}

/** 登录验证 */
export async function login(
  appkey: string,
  captcha: string,
  captchaId: string
): Promise<ApiResponse<LoginData>> {
  const formData = new FormData()
  formData.append('appkey', appkey)
  formData.append('captcha', captcha)
  formData.append('captcha_id', captchaId)

  const res = await fetch(`${API_BASE}/login`, {
    method: 'POST',
    body: formData,
  })
  const payload = await res.json()

  // FastAPI HTTPException 格式：{detail: "..."}
  if ('detail' in payload) {
    return {
      code: res.status,
      message: payload.detail,
      data: null as unknown as LoginData,
    }
  }

  return payload as ApiResponse<LoginData>
}

/** 获取图片列表（分页） */
export async function getImages(page: number = 1): Promise<ApiResponse<ImagesListData>> {
  return request<ImagesListData>(`/images?page=${page}`)
}

/** 管理端图片列表查询（支持筛选/排序/分页） */
export async function getAdminImages(params: AdminImageQuery = {}): Promise<ApiResponse<ImagesListData>> {
  const query = new URLSearchParams()
  if (params.page) query.set('page', String(params.page))
  if (params.page_size) query.set('page_size', String(params.page_size))
  if (params.id !== undefined) query.set('id', String(params.id))
  if (params.tag) query.set('tag', params.tag)
  if (params.nsfw !== undefined) query.set('nsfw', String(params.nsfw))
  if (params.sort) query.set('sort', params.sort)

  const qs = query.toString()
  return request<ImagesListData>(`/images${qs ? `?${qs}` : ''}`)
}

/** 获取单个图片信息 */
export async function getImageInfo(id: number): Promise<ApiResponse<Image>> {
  return request<Image>(`/images/${id}`)
}

/** 获取随机图片信息 */
export async function getRandomImageInfo(): Promise<ApiResponse<Image>> {
  return request<Image>(`/images/random`)
}

/** 标签搜索 */
export async function searchByTag(tag: string): Promise<ApiResponse<TagSearchData>> {
  return request<TagSearchData>(`/images?tag=${encodeURIComponent(tag)}`)
}

/** 获取全部标签 */
export async function getAllTags(): Promise<ApiResponse<AllTagsData>> {
  return request<AllTagsData>('/tags')
}

/** 上传图片 */
export async function uploadImage(
  file: File,
  tags: string[]
): Promise<ApiResponse<UploadData>> {
  const formData = new FormData()
  formData.append('image', file)
  formData.append('tags', tags.join(','))

  return request<UploadData>('/images', withAdminAuth({
    method: 'POST',
    body: formData,
  }))
}

/** AI 预生成标签 */
export async function prepareImageUpload(
  file: File
): Promise<ApiResponse<AiTagSuggestionData>> {
  const formData = new FormData()
  formData.append('image', file)

  return request<AiTagSuggestionData>('/images/prepare', withAdminAuth({
    method: 'POST',
    body: formData,
  }))
}

/** AI 建议标签 */
export async function suggestImageTags(
  file: File,
  prompt: string = ''
): Promise<ApiResponse<AiTagSuggestionData>> {
  const formData = new FormData()
  formData.append('image', file)
  formData.append('prompt', prompt)

  return request<AiTagSuggestionData>('/images/suggest-tags', withAdminAuth({
    method: 'POST',
    body: formData,
  }))
}

/** 提交预生成上传 */
export async function commitImageUpload(
  uploadToken: string,
  tags: string[]
): Promise<ApiResponse<UploadData>> {
  const formData = new FormData()
  formData.append('upload_token', uploadToken)
  formData.append('tags', tags.join(','))

  return request<UploadData>('/images/commit', withAdminAuth({
    method: 'POST',
    body: formData,
  }))
}

/** 删除图片 */
export async function deleteImage(
  id: number
): Promise<ApiResponse<null>> {
  return request<null>(`/images/${id}`, withAdminAuth({
    method: 'DELETE',
  }))
}

/** 更新图片标签和NSFW状态（JSON body 方式） */
export async function updateImage(
  id: number,
  data: { tags?: string[]; nsfw?: boolean }
): Promise<ApiResponse<null>> {
  return request<null>(`/images/${id}`, withAdminAuth({
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  }))
}

/** @deprecated 使用 updateImage 替代 */
export const updateTags = (id: number, tags: string[]) => updateImage(id, { tags })

/** 清除缓存 */
export async function clearCache(): Promise<ApiResponse<null>> {
  return request<null>('/cache', withAdminAuth({
    method: 'DELETE',
  }))
}

/** 获取图片 URL */
export function getImageUrl(id: number, thumbnail: boolean = false): string {
  return thumbnail
    ? `${API_BASE}/images/${id}/thumbnail`
    : `${API_BASE}/images/${id}/file`
}
