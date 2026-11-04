import type { IUser } from '@/types'

// apps/api. Set VITE_API_URL at build time to point at a deployed API.
export const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:3000/api'

const TOKEN_KEY = 'token'

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
  ) {
    super(message)
  }
}

export async function getToken(): Promise<string | null> {
  const stored = await browser.storage.local.get(TOKEN_KEY)
  return (stored[TOKEN_KEY] as string | undefined) ?? null
}

const setToken = (token: string) => browser.storage.local.set({ [TOKEN_KEY]: token })
export const clearToken = () => browser.storage.local.remove(TOKEN_KEY)

/** fetch against the API with the session token; a 401 signs the user out. */
export async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = await getToken()
  const headers = new Headers(init.headers)
  if (init.body) headers.set('Content-Type', 'application/json')
  if (token) headers.set('Authorization', `Bearer ${token}`)

  const response = await fetch(`${API_URL}${path}`, { ...init, headers })
  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    if (response.status === 401) await clearToken()
    throw new ApiError(body.error ?? body.message ?? response.statusText, response.status)
  }
  return response.json()
}

export async function signIn(email: string, password: string): Promise<IUser> {
  const { user, token } = await apiFetch<{ user: IUser; token: string }>('/auth/signin/email', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  })
  await setToken(token)
  return user
}

export async function signUp(name: string, email: string, password: string): Promise<IUser> {
  const { user, token } = await apiFetch<{ user: IUser; token: string | null }>(
    '/auth/signup/email',
    { method: 'POST', body: JSON.stringify({ name, email, password }) },
  )
  if (token) await setToken(token)
  else await signIn(email, password)
  return user
}

export async function currentUser(): Promise<IUser> {
  return (await apiFetch<{ user: IUser }>('/auth/me')).user
}

export async function signOut(): Promise<void> {
  await apiFetch('/auth/signout', { method: 'POST' }).catch(() => undefined)
  await clearToken()
}
