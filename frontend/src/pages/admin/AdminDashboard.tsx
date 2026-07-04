import { useCallback, useEffect, useState } from 'react'

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
  is_blocked: boolean
  created_at: string
}

interface FinanceData {
  revenue_day: number
  revenue_week: number
  revenue_month: number
  currency: string
}

type Tab = 'overview' | 'users' | 'finance'

const API = import.meta.env.VITE_API_URL || '/api/v1'

function initialToken(): string {
  if (typeof window === 'undefined') return ''
  const fromUrl = new URLSearchParams(window.location.search).get('token')
  if (fromUrl) {
    localStorage.setItem('tarot_admin_token', fromUrl)
    window.history.replaceState({}, '', '/admin')
    return fromUrl
  }
  return localStorage.getItem('tarot_admin_token') || ''
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
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

export default function AdminDashboard() {
  const [tab, setTab] = useState<Tab>('overview')
  const [token, setToken] = useState(initialToken)
  const [data, setData] = useState<DashboardData | null>(null)
  const [users, setUsers] = useState<AdminUser[]>([])
  const [finance, setFinance] = useState<FinanceData | null>(null)
  const [search, setSearch] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

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

  const refresh = useCallback(async () => {
    if (!token) {
      setError('Нет токена. Отправьте боту: /admin TaroVlad')
      return
    }
    setLoading(true)
    setError('')
    try {
      if (tab === 'overview') await loadOverview()
      if (tab === 'users') await loadUsers()
      if (tab === 'finance') await loadFinance()
    } catch (e) {
      setError(String(e))
    } finally {
      setLoading(false)
    }
  }, [token, tab, loadOverview, loadUsers, loadFinance])

  useEffect(() => {
    refresh()
  }, [refresh])

  const toggleBlock = async (user: AdminUser) => {
    if (!token) return
    const action = user.is_blocked ? 'unblock' : 'block'
    await adminFetch(`/users/${user.id}/${action}`, token, { method: 'POST' })
    await loadUsers()
  }

  const metrics = data
    ? [
        { label: 'Пользователей', value: data.total_users },
        { label: 'DAU', value: data.dau },
        { label: 'MAU', value: data.mau },
        { label: 'Новых сегодня', value: data.new_registrations_today },
        { label: 'Активных подписок', value: data.active_subscriptions },
        { label: 'Premium', value: data.premium_users },
        { label: 'Платящих', value: data.paying_users },
        { label: 'Доход (⭐)', value: data.total_revenue_stars },
        { label: 'ARPU', value: data.arpu },
        { label: 'Конверсия %', value: data.conversion_percent },
        { label: 'Раскладов', value: data.total_spreads },
        { label: 'Завершённых', value: data.completed_spreads },
        { label: 'AI генераций', value: data.ai_generations },
        { label: 'Ср. AI (мс)', value: data.avg_ai_response_ms },
      ]
    : []

  return (
    <div className="min-h-screen bg-[#0f0a1a] text-white">
      <div className="max-w-6xl mx-auto px-4 py-8">
        <div className="flex flex-wrap items-center justify-between gap-4 mb-8">
          <div>
            <h1 className="text-2xl font-bold">🔐 Админ-панель</h1>
            <p className="text-white/40 text-sm mt-1">Мир Таро · скрытый доступ</p>
          </div>
          <button
            type="button"
            onClick={refresh}
            disabled={loading || !token}
            className="px-4 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 disabled:opacity-50 text-sm"
          >
            {loading ? 'Загрузка…' : 'Обновить'}
          </button>
        </div>

        {!token && (
          <div className="rounded-2xl border border-amber-500/30 bg-amber-500/10 p-4 mb-6 text-amber-100 text-sm">
            Отправьте боту команду <code className="bg-black/30 px-1 rounded">/admin TaroVlad</code> —
            бот выдаст кнопку для входа в панель.
          </div>
        )}

        <div className="flex gap-2 mb-6">
          {(['overview', 'users', 'finance'] as Tab[]).map((t) => (
            <button
              key={t}
              type="button"
              onClick={() => setTab(t)}
              className={`px-4 py-2 rounded-xl text-sm font-medium transition ${
                tab === t
                  ? 'bg-tarot-gold text-tarot-dark'
                  : 'bg-white/10 text-white/70 hover:bg-white/15'
              }`}
            >
              {t === 'overview' ? 'Обзор' : t === 'users' ? 'Пользователи' : 'Финансы'}
            </button>
          ))}
        </div>

        {error && <p className="text-red-400 mb-4 text-sm">{error}</p>}

        {tab === 'overview' && (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
            {metrics.map((m) => (
              <div key={m.label} className="rounded-2xl bg-white/5 border border-white/10 p-4">
                <p className="text-white/50 text-xs">{m.label}</p>
                <p className="text-xl font-bold mt-1">{m.value}</p>
              </div>
            ))}
          </div>
        )}

        {tab === 'users' && (
          <div>
            <div className="flex gap-2 mb-4">
              <input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Поиск по имени или @username"
                className="flex-1 px-4 py-2 rounded-xl bg-white/5 border border-white/10 text-sm outline-none focus:border-purple-500/50"
              />
              <button
                type="button"
                onClick={loadUsers}
                className="px-4 py-2 rounded-xl bg-white/10 text-sm"
              >
                Найти
              </button>
            </div>
            <div className="rounded-2xl border border-white/10 overflow-hidden">
              <table className="w-full text-sm">
                <thead className="bg-white/5 text-white/50">
                  <tr>
                    <th className="text-left p-3">ID</th>
                    <th className="text-left p-3">Имя</th>
                    <th className="text-left p-3">Telegram</th>
                    <th className="text-left p-3">Premium</th>
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
                      <td className="p-3">{u.is_premium ? '✅' : '—'}</td>
                      <td className="p-3">
                        {u.is_blocked ? (
                          <span className="text-red-400">Заблокирован</span>
                        ) : (
                          <span className="text-emerald-400">Активен</span>
                        )}
                      </td>
                      <td className="p-3 text-right">
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
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {users.length === 0 && (
                <p className="p-6 text-center text-white/40 text-sm">Пользователи не найдены</p>
              )}
            </div>
          </div>
        )}

        {tab === 'finance' && finance && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {[
              { label: 'За 24 часа', value: finance.revenue_day },
              { label: 'За 7 дней', value: finance.revenue_week },
              { label: 'За 30 дней', value: finance.revenue_month },
            ].map((item) => (
              <div key={item.label} className="rounded-2xl bg-white/5 border border-white/10 p-6">
                <p className="text-white/50 text-sm">{item.label}</p>
                <p className="text-3xl font-bold mt-2 text-tarot-gold">
                  {item.value} ⭐
                </p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
