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
  const response = await fetch(apiUrl(path), {
    credentials: apiBase ? 'include' : 'same-origin',
    ...options,
    headers: {
      ...(isFormData ? {} : { 'Content-Type': 'application/json' }),
      // Always send the CSRF token as a header for every mutating request.
      // Previously the !isFormData guard silently dropped it on file uploads → 403.
      ...(method !== 'GET' && token ? { 'X-CSRFToken': token } : {}),
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

/**
 * Upload a video file via XHR (for progress events) then poll for job completion.
 *
 * @param {File}     file        - The video file to upload.
 * @param {AbortSignal} signal   - Optional abort signal from the caller.
 * @param {string}   mode        - Analysis mode: 'fast_preview' | 'multimodal'.
 * @param {Function} onProgress  - Called with { phase: 'uploading'|'analyzing', percent: 0-100 }.
 */
export function analyzeVideo(file, signal, mode = 'fast_preview', onProgress) {
  // Separate timeouts: 5 min to upload + 5 min for analysis = 10 min total ceiling.
  const UPLOAD_TIMEOUT_MS = 5 * 60 * 1000
  const ANALYSIS_TIMEOUT_MS = 5 * 60 * 1000

  return new Promise((resolve, reject) => {
    const token = decodeURIComponent(csrfTokenValue || csrfToken())
    const body = new FormData()
    body.append('video', file)
    body.append('mode', mode)

    const xhr = new XMLHttpRequest()
    xhr.open('POST', apiUrl('/api/analyze/jobs/'))
    xhr.withCredentials = true
    if (token) xhr.setRequestHeader('X-CSRFToken', token)
    xhr.timeout = UPLOAD_TIMEOUT_MS

    // Report upload progress
    xhr.upload.addEventListener('progress', (event) => {
      if (event.lengthComputable) {
        onProgress?.({ phase: 'uploading', percent: Math.round((event.loaded / event.total) * 100) })
      }
    })

    // Abort from caller signal
    const abortXhr = () => xhr.abort()
    signal?.addEventListener('abort', abortXhr, { once: true })

    xhr.addEventListener('load', async () => {
      signal?.removeEventListener('abort', abortXhr)
      let payload = null
      try { payload = JSON.parse(xhr.responseText) } catch { /* ignore */ }
      if (xhr.status < 200 || xhr.status >= 300) {
        return reject(friendlyError(payload, xhr.status))
      }
      const jobId = payload?.jobId
      if (!jobId) return reject(new Error('The server did not return a job ID. Please try again.'))

      // Switch to polling phase
      onProgress?.({ phase: 'analyzing', percent: 0 })
      const deadline = Date.now() + ANALYSIS_TIMEOUT_MS
      let pollTick = 0
      const poll = async () => {
        try {
          if (signal?.aborted) return reject(new DOMException('Request aborted', 'AbortError'))
          if (Date.now() >= deadline) return reject(new Error('Analysis is taking too long. Try a shorter or smaller video.'))
          const status = await request(`/api/analyze/jobs/${jobId}`, { signal })
          if (status.status === 'complete') return resolve(status.result)
          // Pulse the progress indicator so the user sees activity
          pollTick++
          onProgress?.({ phase: 'analyzing', percent: Math.min(95, pollTick * 2) })
          window.setTimeout(poll, 1500)
        } catch (err) {
          reject(err)
        }
      }
      poll()
    })

    xhr.addEventListener('timeout', () => {
      signal?.removeEventListener('abort', abortXhr)
      reject(new Error('The upload timed out. Check your connection and try a smaller file.'))
    })

    xhr.addEventListener('error', () => {
      signal?.removeEventListener('abort', abortXhr)
      reject(new Error('The upload failed. Check your connection and try again.'))
    })

    xhr.addEventListener('abort', () => {
      signal?.removeEventListener('abort', abortXhr)
      if (signal?.aborted) {
        reject(new DOMException('Request aborted', 'AbortError'))
      } else {
        reject(new Error('The upload was cancelled.'))
      }
    })

    xhr.send(body)
  })
}

