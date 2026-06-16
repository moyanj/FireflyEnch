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
  created_at: string | null
  updated_at: string | null
}

/** 图片列表响应 */
export interface ImagesListData {
  total: number
  page: number
  page_size: number
  images: Image[]
  last: boolean
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
