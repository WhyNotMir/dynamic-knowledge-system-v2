const API_BASE =
  typeof window === 'undefined'
    ? process.env.API_INTERNAL_URL ?? process.env.NEXT_PUBLIC_API_URL ?? ''
    : process.env.NEXT_PUBLIC_API_URL ?? ''

export function apiUrl(path: string): string {
  return `${API_BASE}${path}`
}

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public code?: string,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

function formatErrorBody(body: unknown, fallback: string): string {
  if (!body || typeof body !== 'object') return fallback

  const record = body as Record<string, unknown>
  const rawMessage = record.message ?? record.detail

  if (typeof rawMessage === 'string') return rawMessage
  if (Array.isArray(rawMessage)) {
    return rawMessage
      .map(item => {
        if (item && typeof item === 'object') {
          const detail = item as Record<string, unknown>
          const location = Array.isArray(detail.loc) ? detail.loc.join('.') : undefined
          const message = typeof detail.msg === 'string' ? detail.msg : JSON.stringify(detail)
          return location ? `${location}: ${message}` : message
        }
        return String(item)
      })
      .join('; ')
  }
  if (rawMessage && typeof rawMessage === 'object') return JSON.stringify(rawMessage)

  return fallback
}

async function readError(res: Response): Promise<ApiError> {
  let message = `HTTP ${res.status}`
  try {
    message = formatErrorBody(await res.json(), message)
  } catch { /* ignore */ }

  const error = new ApiError(message, res.status)
  console.error('[api]', res.status, res.url, message)
  return error
}

export async function apiFetch<T>(
  path: string,
  options?: RequestInit,
): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    cache: 'no-store',
    ...options,
  })
  if (!res.ok) {
    throw await readError(res)
  }
  if (res.status === 204) {
    return undefined as T
  }
  return res.json() as Promise<T>
}

export async function apiUpload<T>(path: string, formData: FormData): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    body: formData,
  })
  if (!res.ok) {
    throw await readError(res)
  }
  return res.json() as Promise<T>
}
