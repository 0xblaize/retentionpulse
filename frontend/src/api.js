const apiBase = import.meta.env.VITE_API_URL || ''
let csrfTokenValue = ''

function friendlyError(payload, status) {
  if (status === 413) return new Error(payload?.detail || 'This video is too large or longer than five minutes.')
  if (status === 422) return new Error(payload?.detail || 'This video could not be analyzed. Try another file or a shorter export.')
  if (status === 401) return new Error('Your workspace session has expired. Please sign in again.')
  if (status === 403) return new Error('This secure request could not be verified. Refresh the page and try again.')
  if (status === 504) return new Error('Analysis took too long. Try a shorter or smaller video.')
  return new Error(payload?.detail || payload?.error || 'The request could not be completed. Please try again.')
}

export const authRoutes = {
  login: '/login/',
  dashboard: '/dashboard/'
}

export function apiUrl(path) {
  return `${apiBase}${path}`
}

function csrfToken() {
  return document.cookie.split('; ').find((cookie) => cookie.startsWith('csrftoken='))?.split('=')[1] || ''
}

async function request(path, options = {}) {
  const method = options.method || 'GET'
  const isFormData = options.body instanceof FormData
  const token = decodeURIComponent(csrfTokenValue || csrfToken())
  if (isFormData && method !== 'GET' && token) options.body.append('csrfmiddlewaretoken', token)
  const response = await fetch(apiUrl(path), {
    credentials: apiBase ? 'include' : 'same-origin',
    ...options,
    headers: {
      ...(isFormData ? {} : { 'Content-Type': 'application/json' }),
      ...(method !== 'GET' && !isFormData ? { 'X-CSRFToken': token } : {}),
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
    const error = friendlyError(payload, response.status)
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

export async function analyzeVideo(file, signal, mode = 'fast_preview') {
  const body = new FormData()
  body.append('video', file)
  body.append('mode', mode)
  const controller = new AbortController()
  const timeout = window.setTimeout(() => controller.abort(), 240000)
  const cancel = () => controller.abort()
  signal?.addEventListener('abort', cancel, { once: true })
  try {
    return await request('/api/analyze/', { method: 'POST', body, signal: controller.signal })
  } catch (error) {
    if (error.name === 'AbortError' && !signal?.aborted) throw new Error('Analysis took too long. Try a shorter or smaller video.')
    throw error
  } finally {
    window.clearTimeout(timeout)
    signal?.removeEventListener('abort', cancel)
  }
}
