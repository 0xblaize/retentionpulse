const djangoBase = import.meta.env.VITE_DJANGO_URL || ''

export const authRoutes = {
  login: `${djangoBase}/login/`,
  dashboard: `${djangoBase}/dashboard/`
}

export function djangoUrl(path) {
  return `${djangoBase}${path}`
}

function csrfToken() {
  return document.cookie.split('; ').find((cookie) => cookie.startsWith('csrftoken='))?.split('=')[1] || ''
}

async function request(path, options = {}) {
  const response = await fetch(djangoUrl(path), {
    credentials: 'same-origin',
    ...options,
    headers: {
      ...(options.body instanceof FormData ? {} : { 'Content-Type': 'application/json' }),
      ...(options.method && options.method !== 'GET' ? { 'X-CSRFToken': decodeURIComponent(csrfToken()) } : {}),
      ...(options.headers || {})
    }
  })
  const contentType = response.headers.get('content-type') || ''
  const payload = contentType.includes('application/json') ? await response.json() : null
  if (!response.ok) {
    const error = new Error(payload?.detail || payload?.error || `Request failed (${response.status})`)
    error.status = response.status
    throw error
  }
  return payload
}

export async function bootstrapCsrf() {
  return request('/api/auth/csrf/')
}

export async function getSession() {
  return request('/api/auth/session/')
}

export async function logout() {
  return request('/api/auth/logout/', { method: 'POST' })
}

export async function analyzeVideo(file, signal) {
  const body = new FormData()
  body.append('video', file)
  return request('/api/analyze/', { method: 'POST', body, signal })
}
