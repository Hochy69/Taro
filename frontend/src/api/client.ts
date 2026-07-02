const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'
const TOKEN_KEY = 'tarot_access_token'
const AUTH_KEY = 'tarot_auth_meta'

let accessToken: string | null = null

interface AuthMeta {
  is_premium: boolean
  is_returning: boolean
  last_category: string | null
  terms_accepted?: boolean
  profile?: {
    name?: string | null
    birth_date?: string | null
    zodiac_sign?: string | null
  } | null
}

export function setAccessToken(token: string) {
  accessToken = token
  sessionStorage.setItem(TOKEN_KEY, token)
}

export function setAuthMeta(meta: AuthMeta) {
  sessionStorage.setItem(AUTH_KEY, JSON.stringify(meta))
}

export function loadAuthMeta(): AuthMeta | null {
  const raw = sessionStorage.getItem(AUTH_KEY)
  if (!raw) return null
  try {
    return JSON.parse(raw) as AuthMeta
  } catch {
    return null
  }
}

export function loadAccessToken(): string | null {
  if (!accessToken) {
    accessToken = sessionStorage.getItem(TOKEN_KEY)
  }
  return accessToken
}

export function clearAccessToken() {
  accessToken = null
  sessionStorage.removeItem(TOKEN_KEY)
  sessionStorage.removeItem(AUTH_KEY)
}

export function getAccessToken() {
  return accessToken ?? loadAccessToken()
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  }
  if (accessToken) {
    headers['Authorization'] = `Bearer ${accessToken}`
  }

  const response = await fetch(`${API_URL}${path}`, { ...options, headers })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Request failed' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
  return response.json()
}

export interface Category {
  id: number
  slug: string
  name: string
  emoji: string
}

export interface UserProfile {
  name?: string
  birth_date?: string
  zodiac_sign?: string
}

export interface AuthResponse {
  access_token: string
  user: {
    id: number
    telegram_id: number
    first_name: string | null
    is_premium: boolean
    terms_accepted: boolean
    profile: UserProfile | null
  }
  is_returning: boolean
  last_category: string | null
}

export interface SpreadCard {
  id: number
  slug: string
  name: string
  position: string
  is_reversed: boolean
  image_url: string | null
}

export interface Spread {
  id: number
  category_slug: string
  category_name: string
  situation: string | null
  emotion: string | null
  status: string
  cards: SpreadCard[]
  created_at: string
}

export interface AIResult {
  response_text: string
  past: string | null
  present: string | null
  future: string | null
  advice: string | null
  conclusion: string | null
  generation_time_ms: number
}

export interface Limits {
  can_spread: boolean
  used_today: number
  daily_limit: number
  is_premium: boolean
  bonus_spreads: number
  period_days: number
  next_available_at: string | null
}

export interface ReferralInfo {
  code: string
  link: string
  invites_count: number
  bonus_earned: number
}

export const api = {
  auth: (initData: string) =>
    request<AuthResponse>('/auth/telegram', {
      method: 'POST',
      body: JSON.stringify({ init_data: initData }),
    }),

  authDev: () =>
    request<AuthResponse>('/auth/dev', {
      method: 'POST',
    }),

  getMe: () =>
    request<AuthResponse['user']>('/me'),

  getCategories: () => request<Category[]>('/categories'),

  getLimits: () => request<Limits>('/limits'),

  getReferral: () => request<ReferralInfo>('/referral'),

  createSpread: (data: {
    category_slug: string
    situation: string
    emotion: string
    profile?: UserProfile
  }) =>
    request<Spread>('/spreads', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  interpretSpread: (spreadId: number) =>
    request<AIResult>(`/spreads/${spreadId}/interpret`, { method: 'POST' }),

  prepareSpreadShare: (spreadId: number) =>
    request<{ share_message_id: string }>(`/spreads/${spreadId}/share`, { method: 'POST' }),

  getSpread: (spreadId: number) =>
    request<Spread & { ai_result: AIResult | null }>(`/spreads/${spreadId}`),

  getHistory: () =>
    request<
      Array<{
        id: number
        category_name: string
        category_emoji: string
        cards: string[]
        situation: string | null
        conclusion: string | null
        created_at: string
        is_favorite: boolean
      }>
    >('/history'),

  getPricing: () => request<{
    single_spread: number
    plans: Array<{
      plan: string
      stars: number
      duration_days: number
      daily_spreads: number
      features: string[]
    }>
  }>('/pricing'),

  createPayment: (payment_type: string, plan?: string) =>
    request<{
      id: number
      stars_amount: number
      status: string
      plan: string | null
      invoice_link: string | null
    }>('/payments', {
      method: 'POST',
      body: JSON.stringify({ payment_type, plan }),
    }),

  acceptTerms: () =>
    request<{ terms_accepted: boolean; accepted_at: string }>('/me/accept-terms', {
      method: 'POST',
    }),
}
