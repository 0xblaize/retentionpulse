const djangoBase = import.meta.env.VITE_DJANGO_URL || ''
let csrfTokenValue = ''

export const authRoutes = {
  login: '/login/',
  dashboard: '/dashboard/'
}

export function djangoUrl(path) {
  return `${djangoBase}${path}`
}

function csrfToken() {
  return document.cookie.split('; ').find((cookie) => cookie.startsWith('csrftoken='))?.split('=')[1] || ''
}

async function request(path, options = {}) {
  const response = await fetch(djangoUrl(path), {
    credentials: djangoBase ? 'include' : 'same-origin',
    ...options,
    headers: {
      ...(options.body instanceof FormData ? {} : { 'Content-Type': 'application/json' }),
      ...(options.method && options.method !== 'GET' ? { 'X-CSRFToken': decodeURIComponent(csrfTokenValue || csrfToken()) } : {}),
      ...(options.headers || {})
    }
  })
  const body = await response.text()
  let payload = null
  try {
    payload = body ? JSON.parse(body) : null
  } catch {
    const error = new Error(`Request returned an invalid response (${response.status})`)
    error.status = response.status
    throw error
  }
  if (!response.ok) {
    const error = new Error(payload?.detail || payload?.error || `Request failed (${response.status})`)
    error.status = response.status
    throw error
  }
  return payload
}

export async function bootstrapCsrf() {
  const payload = await request('/api/auth/csrf/')
  csrfTokenValue = payload?.csrfToken || ''
  return payload
}

export async function getSession() {
  return request('/api/auth/session/')
}

export async function logout() {
  return request('/api/auth/logout/', { method: 'POST' })
}

export async function analyzeVideo(file, signal, mode = 'auto') {
  const body = new FormData()
  body.append('video', file)
  body.append('mode', mode)
  return request('/api/analyze/', { method: 'POST', body, signal })
}
