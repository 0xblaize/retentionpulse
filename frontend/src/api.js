const djangoBase = import.meta.env.VITE_DJANGO_URL || ''

export const authRoutes = {
  login: `${djangoBase}/login/`,
  dashboard: `${djangoBase}/dashboard/`
}

export function djangoUrl(path) {
  return `${djangoBase}${path}`
}
