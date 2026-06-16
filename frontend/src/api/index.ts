import type { ApiResponse, ImagesListData, TagSearchData, UploadData, Image, LoginData } from './types'

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

function withApiKey(appkey: string, options: RequestInit = {}): RequestInit {
  return {
    ...options,
    headers: {
      ...(options.headers ?? {}),
      'X-API-Key': appkey,
    },
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
  return res.json()
}

/** 获取图片列表（分页） */
export async function getImages(page: number = 1): Promise<ApiResponse<ImagesListData>> {
  return request<ImagesListData>(`/images?page=${page}`)
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

/** 上传图片 */
export async function uploadImage(
  file: File,
  tags: string[],
  appkey: string
): Promise<ApiResponse<UploadData>> {
  const formData = new FormData()
  formData.append('image', file)
  formData.append('tags', tags.join(','))

  return request<UploadData>('/images', withApiKey(appkey, {
    method: 'POST',
    body: formData,
  }))
}

/** 删除图片 */
export async function deleteImage(
  id: number,
  appkey: string
): Promise<ApiResponse<null>> {
  return request<null>(`/images/${id}`, withApiKey(appkey, {
    method: 'DELETE',
  }))
}

/** 更新图片标签 */
export async function updateTags(
  id: number,
  tags: string[],
  appkey: string
): Promise<ApiResponse<null>> {
  return request<null>(`/images/${id}?tags=${encodeURIComponent(tags.join(','))}`, withApiKey(appkey, {
    method: 'PATCH',
  }))
}

/** 清除缓存 */
export async function clearCache(appkey: string): Promise<ApiResponse<null>> {
  return request<null>('/cache', withApiKey(appkey, {
    method: 'DELETE',
  }))
}

/** 获取图片 URL */
export function getImageUrl(id: number, thumbnail: boolean = false): string {
  return thumbnail
    ? `${API_BASE}/images/${id}/thumbnail`
    : `${API_BASE}/images/${id}/file`
}
