/** API 响应格式 */
export interface ApiResponse<T = unknown> {
  code: number
  message: string
  data: T
}

/** 图片对象 */
export interface Image {
  id: number
  filename: string
  tags: string[]
  nsfw: boolean
  nsfw_score: number
  created_at: string | null
  updated_at: string | null
}

/** 图片列表响应（统一分页结构） */
export interface ImagesListData {
  total: number
  page: number
  page_size: number
  images: Image[]
  last: boolean
}

/** 管理端图片查询参数 */
export interface AdminImageQuery {
  page?: number
  page_size?: number
  id?: number
  tag?: string
  nsfw?: boolean
  sort?: 'id_desc' | 'id_asc' | 'created_at_desc' | 'created_at_asc'
}

/** 标签搜索响应 */
export interface TagSearchData {
  total: number
  images: Image[]
}

/** 上传响应 */
export interface UploadData {
  id: number
  url: string
  tags: string[]
}

/** AI 建议响应 */
export interface AiTagSuggestionData {
  suggested_tags: string[]
}

/** 登录响应 */
export interface LoginData {
  token: string
}
