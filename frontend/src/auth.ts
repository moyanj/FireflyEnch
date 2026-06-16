const ADMIN_TOKEN_KEY = 'fireflyench.admin.token'

export function getAdminToken(): string {
  if (typeof window === 'undefined') {
    return ''
  }

  return window.localStorage.getItem(ADMIN_TOKEN_KEY) ?? ''
}

export function setAdminToken(token: string) {
  if (typeof window === 'undefined') {
    return
  }

  window.localStorage.setItem(ADMIN_TOKEN_KEY, token)
}

export function clearAdminToken() {
  if (typeof window === 'undefined') {
    return
  }

  window.localStorage.removeItem(ADMIN_TOKEN_KEY)
}

export function isAdminLoggedIn(): boolean {
  return getAdminToken().trim().length > 0
}
