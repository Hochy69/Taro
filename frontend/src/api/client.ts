const API_URL = import.meta.env.VITE_API_URL || '/api/v1'
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
    birth_time?: string | null
    birth_city?: string | null
    gender?: string | null
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
  const token = accessToken ?? loadAccessToken()
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
    accessToken = token
  }

  const response = await fetch(`${API_URL}${path}`, { ...options, headers })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Request failed' }))
    const detail = error.detail
    const message =
      typeof detail === 'string'
        ? detail
        : Array.isArray(detail)
          ? detail.map((d: { msg?: string }) => d.msg).filter(Boolean).join(', ')
          : 'Request failed'
    throw new Error(message || `HTTP ${response.status}`)
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
  birth_time?: string
  birth_city?: string
  gender?: string
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
  compatibility_credits: number
  period_days: number
  next_available_at: string | null
  completed_spreads: number
  first_paid_discount_eligible: boolean
  first_paid_discounted_price: number | null
  first_paid_discount_percent: number
}

export interface ReferralMilestone {
  invites_required: number
  reward: string
  reached: boolean
}

export interface ReferralInfo {
  code: string
  link: string
  invites_count: number
  bonus_earned: number
  milestones: ReferralMilestone[]
  next_milestone: ReferralMilestone | null
}

export interface SpreadPack {
  pack: string
  stars: number
  spreads: number
  savings_percent: number
  label: string
}

export interface LoveBundle {
  stars: number
  original_stars: number
  savings_percent: number
  description: string
}

export interface CardOfDay {
  date: string
  card: SpreadCard
  meaning: string
  advice: string
  conclusion: string
  text: string
}

export interface ZodiacPortrait {
  zodiac_sign: string
  emoji: string
  summary: string
  essence: string
  strengths: string
  shadow: string
  love: string
  career: string
  advice: string
  text: string
  lunar: {
    lunar_day: string
    title: string
    meaning: string
    advice: string
  } | null
}

export interface PlanetPosition {
  key: string
  name: string
  symbol: string
  sign: string
  sign_emoji: string
  degree: number
  longitude: number
  house: number | null
  interpretation: string
  wheel_angle: number
}

export interface NatalChart {
  birth_date: string
  birth_time: string | null
  birth_city: string | null
  time_unknown: boolean
  ascendant: string | null
  ascendant_emoji: string | null
  ascendant_degree: number | null
  ascendant_longitude: number | null
  summary: string
  planets: PlanetPosition[]
  houses: Array<{ house: number; sign: string; sign_emoji: string; degree: number }>
  aspects: Array<{
    planet_a: string
    planet_b: string
    aspect: string
    angle: number
    description: string
  }>
  text: string
}

export interface PartnerBirthData {
  name: string
  birth_date: string
  birth_time?: string
  birth_city?: string
  gender?: string
}

export interface CompatibilityResult {
  partner_name: string
  score: number
  summary: string
  user_sun_sign: string
  partner_sun_sign: string
  user_moon_sign: string
  partner_moon_sign: string
  sun_match: string
  moon_match: string | null
  love: string
  friendship: string
  challenges: string
  advice: string
  text: string
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
    compatibility: number
    first_paid_discount_percent: number
    subscription_per_day_stars: number | null
    spread_packs: SpreadPack[]
    love_bundle: LoveBundle | null
    plans: Array<{
      plan: string
      stars: number
      duration_days: number
      daily_spreads: number
      features: string[]
    }>
  }>('/pricing'),

  createPayment: (payment_type: string, plan?: string, promo_code?: string) =>
    request<{
      id: number
      stars_amount: number
      status: string
      plan: string | null
      invoice_link: string | null
      original_stars_amount: number | null
      discount_percent: number | null
      promo_code: string | null
      free: boolean
    }>('/payments', {
      method: 'POST',
      body: JSON.stringify({ payment_type, plan, promo_code }),
    }),

  validatePromo: (code: string) =>
    request<{ code: string; discount_percent: number; uses_left: number | null }>(
      '/promo/validate',
      {
        method: 'POST',
        body: JSON.stringify({ code }),
      },
    ),

  acceptTerms: () =>
    request<{ terms_accepted: boolean; accepted_at: string }>('/me/accept-terms', {
      method: 'POST',
    }),

  getCardOfDay: () => request<CardOfDay>('/card-of-day'),

  getPortrait: () => request<ZodiacPortrait>('/profile/portrait'),

  getNatalChart: () => request<NatalChart>('/profile/natal-chart'),

  getCompatibility: (data: PartnerBirthData) =>
    request<CompatibilityResult>('/astrology/compatibility', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  getPreferences: () => request<{ daily_card_push: boolean }>('/me/preferences'),

  updatePreferences: (data: { daily_card_push?: boolean }) =>
    request<{ daily_card_push: boolean }>('/me/preferences', {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),
}
