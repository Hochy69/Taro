import { useCallback, useEffect, useState } from 'react'
import { initTelegramWebApp } from '@/lib/telegram'

interface DashboardData {
  total_users: number
  dau: number
  mau: number
  new_registrations_today: number
  active_subscriptions: number
  premium_users: number
  paying_users: number
  total_revenue_stars: number
  arpu: number
  conversion_percent: number
  total_spreads: number
  completed_spreads: number
  ai_generations: number
  avg_ai_response_ms: number
}

interface AdminUser {
  id: number
  telegram_id: number
  username: string | null
  first_name: string | null
  is_premium: boolean
  is_admin: boolean
  is_blocked: boolean
  acquisition_source?: string | null
  created_at: string
}

interface FinanceData {
  revenue_day: number
  revenue_week: number
  revenue_month: number
  currency: string
}

interface PartnerStat {
  source: string
  link: string
  users_count: number
  pending_starts: number
  paying_users: number
  revenue_stars: number
  partner_share_35pct: number
}

type Tab = 'overview' | 'users' | 'finance' | 'partners'

const API = import.meta.env.VITE_API_URL || '/api/v1'
const TOKEN_KEY = 'tarot_admin_token'

function readTokenFromUrl(): string {
  if (typeof window === 'undefined') return ''
  const query = new URLSearchParams(window.location.search)
  const hash = new URLSearchParams(window.location.hash.replace(/^#/, ''))
  return query.get('token') || hash.get('token') || hash.get('t') || ''
}

function persistToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token)
  sessionStorage.setItem(TOKEN_KEY, token)
}

function clearStoredToken(): void {
  localStorage.removeItem(TOKEN_KEY)
  sessionStorage.removeItem(TOKEN_KEY)
}

function initialToken(): string {
  const fromUrl = readTokenFromUrl()
  if (fromUrl) {
    persistToken(fromUrl)
    window.history.replaceState({}, '', '/admin')
    return fromUrl
  }
  return sessionStorage.getItem(TOKEN_KEY) || localStorage.getItem(TOKEN_KEY) || ''
}

function formatNum(value: number): string {
  return new Intl.NumberFormat('ru-RU').format(value)
}

async function adminFetch<T>(path: string, token: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API}/admin${path}`, {
    ...init,
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
      ...(init?.headers as Record<string, string>),
    },
  })
  if (res.status === 401 || res.status === 403) {
    throw new Error('Сессия истекла. Отправьте боту /admin TaroVlad и откройте панель снова.')
  }
  if (!res.ok) {
    const text = await res.text().catch(() => '')
    throw new Error(text || `HTTP ${res.status}`)
  }
  return res.json()
}

export default function AdminDashboard() {
  const [tab, setTab] = useState<Tab>('overview')
  const [token, setToken] = useState(initialToken)
  const [tokenInput, setTokenInput] = useState('')
  const [data, setData] = useState<DashboardData | null>(null)
  const [users, setUsers] = useState<AdminUser[]>([])
  const [finance, setFinance] = useState<FinanceData | null>(null)
  const [partners, setPartners] = useState<PartnerStat[]>([])
  const [search, setSearch] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [authOk, setAuthOk] = useState<boolean | null>(null)

  useEffect(() => {
    initTelegramWebApp()
  }, [])

  const loadOverview = useCallback(async () => {
    if (!token) return
    setData(await adminFetch<DashboardData>('/dashboard', token))
  }, [token])

  const loadUsers = useCallback(async () => {
    if (!token) return
    const q = search.trim() ? `?search=${encodeURIComponent(search.trim())}` : ''
    setUsers(await adminFetch<AdminUser[]>(`/users${q}`, token))
  }, [token, search])

  const loadFinance = useCallback(async () => {
    if (!token) return
    setFinance(await adminFetch<FinanceData>('/finance', token))
  }, [token])

  const loadPartners = useCallback(async () => {
    if (!token) return
    setPartners(await adminFetch<PartnerStat[]>('/partners', token))
  }, [token])

  const refresh = useCallback(async () => {
    if (!token) {
      setError('Нет токена. Отправьте боту: /admin TaroVlad')
      setAuthOk(false)
      return
    }
    setLoading(true)
    setError('')
    try {
      await adminFetch('/ping', token)
      setAuthOk(true)
      if (tab === 'overview') await loadOverview()
      if (tab === 'users') await loadUsers()
      if (tab === 'finance') await loadFinance()
      if (tab === 'partners') await loadPartners()
    } catch (e) {
      setAuthOk(false)
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setLoading(false)
    }
  }, [token, tab, loadOverview, loadUsers, loadFinance, loadPartners])

  useEffect(() => {
    refresh()
  }, [refresh])

  const applyManualToken = () => {
    const trimmed = tokenInput.trim()
    if (!trimmed) return
    persistToken(trimmed)
    setToken(trimmed)
    setTokenInput('')
    setError('')
  }

  const logout = () => {
    clearStoredToken()
    setToken('')
    setAuthOk(false)
    setData(null)
    setUsers([])
    setFinance(null)
    setPartners([])
    setError('Вы вышли. Отправьте боту /admin TaroVlad для нового входа.')
  }

  const toggleBlock = async (user: AdminUser) => {
    if (!token || user.is_admin) return
    const action = user.is_blocked ? 'unblock' : 'block'
    await adminFetch(`/users/${user.id}/${action}`, token, { method: 'POST' })
    await loadUsers()
  }

  const metrics = data
    ? [
        { label: 'Пользователей (без админов/тестов)', value: formatNum(data.total_users) },
        { label: 'DAU (сегодня МСК)', value: formatNum(data.dau) },
        { label: 'MAU (30 дней)', value: formatNum(data.mau) },
        { label: 'Новых сегодня (МСК)', value: formatNum(data.new_registrations_today) },
        { label: 'Активный Premium', value: formatNum(data.active_subscriptions) },
        { label: 'Платящих (реальные Stars)', value: formatNum(data.paying_users) },
        { label: 'Доход (⭐, без promo/test)', value: formatNum(data.total_revenue_stars) },
        { label: 'ARPPU (⭐)', value: formatNum(data.arpu) },
        { label: 'Конверсия %', value: formatNum(data.conversion_percent) },
        { label: 'Раскладов', value: formatNum(data.total_spreads) },
        { label: 'Завершённых', value: formatNum(data.completed_spreads) },
        { label: 'AI генераций', value: formatNum(data.ai_generations) },
        { label: 'Ср. AI (мс)', value: formatNum(data.avg_ai_response_ms) },
      ]
    : []

  return (
    <div className="min-h-[100dvh] bg-[#0f0a1a] text-white">
      <div className="max-w-6xl mx-auto px-4 py-6 pb-10 pt-[max(1.5rem,env(safe-area-inset-top))]">
        <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
          <div>
            <h1 className="text-2xl font-bold">🔐 Админ-панель</h1>
            <p className="text-white/40 text-sm mt-1">
              Мир Таро · {authOk ? 'доступ подтверждён' : 'требуется вход'}
            </p>
          </div>
          <div className="flex gap-2">
            {token && (
              <button
                type="button"
                onClick={logout}
                className="px-4 py-2 rounded-xl bg-white/10 hover:bg-white/15 text-sm"
              >
                Выйти
              </button>
            )}
            <button
              type="button"
              onClick={refresh}
              disabled={loading || !token}
              className="px-4 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 disabled:opacity-50 text-sm"
            >
              {loading ? 'Загрузка…' : 'Обновить'}
            </button>
          </div>
        </div>

        {!token && (
          <div className="rounded-2xl border border-amber-500/30 bg-amber-500/10 p-4 mb-6 space-y-3">
            <p className="text-amber-100 text-sm">
              1. Отправьте боту <code className="bg-black/30 px-1 rounded">/admin TaroVlad</code>
            </p>
            <p className="text-amber-100/80 text-sm">
              2. Нажмите кнопку <b>🔐 Админ-панель</b> в ответе бота
            </p>
            <p className="text-amber-100/70 text-xs">
              Если кнопка открыла пустую панель — вставьте токен вручную ниже (бот может не передать
              параметры в WebApp).
            </p>
            <div className="flex gap-2">
              <input
                value={tokenInput}
                onChange={(e) => setTokenInput(e.target.value)}
                placeholder="Вставьте admin-токен"
                className="flex-1 min-w-0 px-3 py-2 rounded-xl bg-black/30 border border-white/10 text-sm outline-none focus:border-amber-400/50"
              />
              <button
                type="button"
                onClick={applyManualToken}
                className="px-4 py-2 rounded-xl bg-amber-500 text-black font-medium text-sm shrink-0"
              >
                Войти
              </button>
            </div>
          </div>
        )}

        <div className="flex gap-2 mb-6 overflow-x-auto pb-1">
          {(['overview', 'users', 'finance', 'partners'] as Tab[]).map((t) => (
            <button
              key={t}
              type="button"
              onClick={() => setTab(t)}
              className={`px-4 py-2 rounded-xl text-sm font-medium transition shrink-0 ${
                tab === t
                  ? 'bg-[#D4AF37] text-[#0F0A1A]'
                  : 'bg-white/10 text-white/70 hover:bg-white/15'
              }`}
            >
              {t === 'overview'
                ? 'Обзор'
                : t === 'users'
                  ? 'Пользователи'
                  : t === 'finance'
                    ? 'Финансы'
                    : 'Партнёры'}
            </button>
          ))}
        </div>

        {error && (
          <p className="text-red-400 mb-4 text-sm rounded-xl bg-red-500/10 border border-red-500/20 px-4 py-3">
            {error}
          </p>
        )}

        {tab === 'overview' && (
          <div>
            {loading && !data && (
              <p className="text-white/40 text-sm mb-4">Загружаем метрики…</p>
            )}
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
              {metrics.map((m) => (
                <div key={m.label} className="rounded-2xl bg-white/5 border border-white/10 p-4">
                  <p className="text-white/50 text-xs">{m.label}</p>
                  <p className="text-xl font-bold mt-1 break-words">{m.value}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {tab === 'users' && (
          <div>
            <div className="flex gap-2 mb-4">
              <input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && loadUsers()}
                placeholder="Поиск по имени или @username"
                className="flex-1 min-w-0 px-4 py-2 rounded-xl bg-white/5 border border-white/10 text-sm outline-none focus:border-purple-500/50"
              />
              <button
                type="button"
                onClick={loadUsers}
                disabled={loading || !token}
                className="px-4 py-2 rounded-xl bg-white/10 text-sm shrink-0"
              >
                Найти
              </button>
            </div>
            <div className="rounded-2xl border border-white/10 overflow-x-auto">
              <table className="w-full text-sm min-w-[640px]">
                <thead className="bg-white/5 text-white/50">
                  <tr>
                    <th className="text-left p-3">ID</th>
                    <th className="text-left p-3">Имя</th>
                    <th className="text-left p-3">Telegram</th>
                    <th className="text-left p-3">Роль</th>
                    <th className="text-left p-3">Источник</th>
                    <th className="text-left p-3">Статус</th>
                    <th className="text-right p-3">Действие</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((u) => (
                    <tr key={u.id} className="border-t border-white/5">
                      <td className="p-3 text-white/60">{u.id}</td>
                      <td className="p-3">{u.first_name || '—'}</td>
                      <td className="p-3 text-white/70">
                        {u.username ? `@${u.username}` : u.telegram_id}
                      </td>
                      <td className="p-3 text-xs">
                        {u.is_admin ? (
                          <span className="text-amber-300">👑 admin</span>
                        ) : u.is_premium ? (
                          <span className="text-emerald-300">⭐ premium</span>
                        ) : (
                          <span className="text-white/40">free</span>
                        )}
                      </td>
                      <td className="p-3 text-xs text-white/50">
                        {u.acquisition_source || '—'}
                      </td>
                      <td className="p-3">
                        {u.is_blocked ? (
                          <span className="text-red-400">Заблокирован</span>
                        ) : (
                          <span className="text-emerald-400">Активен</span>
                        )}
                      </td>
                      <td className="p-3 text-right">
                        {u.is_admin ? (
                          <span className="text-white/30 text-xs">—</span>
                        ) : (
                          <button
                            type="button"
                            onClick={() => toggleBlock(u)}
                            className={`px-3 py-1 rounded-lg text-xs ${
                              u.is_blocked
                                ? 'bg-emerald-500/20 text-emerald-300'
                                : 'bg-red-500/20 text-red-300'
                            }`}
                          >
                            {u.is_blocked ? 'Разблокировать' : 'Заблокировать'}
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {!loading && users.length === 0 && (
                <p className="p-6 text-center text-white/40 text-sm">Пользователи не найдены</p>
              )}
            </div>
          </div>
        )}

        {tab === 'finance' && (
          <div>
            {loading && !finance && (
              <p className="text-white/40 text-sm mb-4">Загружаем финансы…</p>
            )}
            {finance ? (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {[
                  { label: 'За 24 часа', value: finance.revenue_day },
                  { label: 'За 7 дней', value: finance.revenue_week },
                  { label: 'За 30 дней', value: finance.revenue_month },
                ].map((item) => (
                  <div
                    key={item.label}
                    className="rounded-2xl bg-white/5 border border-white/10 p-6"
                  >
                    <p className="text-white/50 text-sm">{item.label}</p>
                    <p className="text-3xl font-bold mt-2 text-[#D4AF37]">
                      {formatNum(item.value)} ⭐
                    </p>
                  </div>
                ))}
              </div>
            ) : (
              !loading && (
                <p className="text-white/40 text-sm">Нет данных. Нажмите «Обновить».</p>
              )
            )}
          </div>
        )}

        {tab === 'partners' && (
          <div>
            <p className="text-white/50 text-sm mb-4">
              Метки из ссылок вида{' '}
              <code className="bg-black/30 px-1 rounded">?start=p_канал</code> или{' '}
              <code className="bg-black/30 px-1 rounded">?start=ads_love</code>. Доля 35% —
              ориентир для выплат партнёрам.
            </p>
            {loading && partners.length === 0 && (
              <p className="text-white/40 text-sm mb-4">Загружаем партнёров…</p>
            )}
            <div className="rounded-2xl border border-white/10 overflow-x-auto">
              <table className="w-full text-sm min-w-[720px]">
                <thead className="bg-white/5 text-white/50">
                  <tr>
                    <th className="text-left p-3">Метка</th>
                    <th className="text-right p-3">Пользователи</th>
                    <th className="text-right p-3">Ожидают WebApp</th>
                    <th className="text-right p-3">Платящие</th>
                    <th className="text-right p-3">Доход ⭐</th>
                    <th className="text-right p-3">35%</th>
                  </tr>
                </thead>
                <tbody>
                  {partners.map((p) => (
                    <tr key={p.source} className="border-t border-white/5">
                      <td className="p-3">
                        <div className="font-medium">{p.source}</div>
                        <div className="text-white/40 text-xs break-all">{p.link}</div>
                      </td>
                      <td className="p-3 text-right">{formatNum(p.users_count)}</td>
                      <td className="p-3 text-right text-white/60">
                        {formatNum(p.pending_starts)}
                      </td>
                      <td className="p-3 text-right">{formatNum(p.paying_users)}</td>
                      <td className="p-3 text-right text-[#D4AF37]">
                        {formatNum(p.revenue_stars)}
                      </td>
                      <td className="p-3 text-right text-emerald-300">
                        {formatNum(p.partner_share_35pct)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {!loading && partners.length === 0 && (
                <p className="p-6 text-center text-white/40 text-sm">
                  Пока нет переходов по партнёрским ссылкам
                </p>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
