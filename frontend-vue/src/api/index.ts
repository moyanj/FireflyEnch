import type { ApiResponse, ImagesListData, TagSearchData, UploadData, Image } from './types'

const API_BASE = '/api'

/** 统一请求封装 */
async function request<T>(
  path: string,
  options?: RequestInit
): Promise<ApiResponse<T>> {
  const res = await fetch(`${API_BASE}${path}`, options)
  return res.json()
}

/** 获取图片列表（分页） */
export async function getImages(page: number = 1): Promise<ApiResponse<ImagesListData>> {
  return request<ImagesListData>(`/images?page=${page}`)
}

/** 获取单个图片信息 */
export async function getImageInfo(id: number): Promise<ApiResponse<Image>> {
  return request<Image>(`/image/${id}?info=1`)
}

/** 获取随机图片信息 */
export async function getRandomImageInfo(): Promise<ApiResponse<Image>> {
  return request<Image>(`/image/random?info=1`)
}

/** 标签搜索 */
export async function searchByTag(tag: string): Promise<ApiResponse<TagSearchData>> {
  return request<TagSearchData>(`/image/tag?tag=${encodeURIComponent(tag)}`)
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

  return request<UploadData>(`/upload?appkey=${appkey}`, {
    method: 'POST',
    body: formData,
  })
}

/** 删除图片 */
export async function deleteImage(
  id: number,
  appkey: string,
  rmfile: boolean = true
): Promise<ApiResponse<null>> {
  return request<null>(`/image/${id}?appkey=${appkey}&rmfile=${rmfile ? '1' : '0'}`, {
    method: 'DELETE',
  })
}

/** 更新图片标签 */
export async function updateTags(
  id: number,
  tags: string[],
  appkey: string
): Promise<ApiResponse<null>> {
  return request<null>(`/image/${id}?appkey=${appkey}&tags=${tags.join(',')}`, {
    method: 'PATCH',
  })
}

/** 清除缓存 */
export async function clearCache(appkey: string): Promise<ApiResponse<null>> {
  return request<null>(`/clear?appkey=${appkey}`)
}

/** 获取图片 URL */
export function getImageUrl(id: number): string {
  return `${API_BASE}/image/${id}`
}