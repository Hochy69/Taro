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

// Relative path works via Vite proxy (localhost + Tuna tunnel).
const API = import.meta.env.VITE_API_URL || '/api/v1'

function initialToken(): string {
  if (typeof window === 'undefined') return ''
  const fromUrl = new URLSearchParams(window.location.search).get('token')
  if (fromUrl) {
    localStorage.setItem('tarot_admin_token', fromUrl)
    return fromUrl
  }
  return localStorage.getItem('tarot_admin_token') || ''
}

export default function AdminDashboard() {
  const [data, setData] = useState<DashboardData | null>(null)
  const [token, setToken] = useState(initialToken)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const fetchDashboard = useCallback(async () => {
    if (!token) return
    setLoading(true)
    try {
      const res = await fetch(`${API}/admin/dashboard`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      setData(await res.json())
      setError('')
    } catch (e) {
      setError(String(e))
    } finally {
      setLoading(false)
    }
  }, [token])

  useEffect(() => {
    fetchDashboard()
  }, [fetchDashboard])

  const metrics = data
    ? [
        { label: 'Реальных пользователей', value: data.total_users },
        { label: 'DAU (сегодня UTC)', value: data.dau },
        { label: 'MAU (30 дней)', value: data.mau },
        { label: 'Новые сегодня', value: data.new_registrations_today },
        { label: 'Активные подписки', value: data.active_subscriptions },
        { label: 'Premium-пользователи', value: data.premium_users },
        { label: 'Платящие пользователи', value: data.paying_users },
        { label: 'Доход (Stars)', value: data.total_revenue_stars },
        { label: 'ARPU (Stars)', value: data.arpu },
        { label: 'Конверсия в оплату %', value: data.conversion_percent },
        { label: 'Всего раскладов', value: data.total_spreads },
        { label: 'Завершённых раскладов', value: data.completed_spreads },
        { label: 'AI генераций', value: data.ai_generations },
        { label: 'Ср. время AI (мс)', value: data.avg_ai_response_ms },
      ]
    : []

  return (
    <div className="min-h-screen bg-gray-900 text-white p-8">
      <h1 className="text-3xl font-bold mb-2">🔮 Admin Dashboard</h1>
      <p className="text-gray-500 text-sm mb-8">
        Тестовые аккаунты (dev, QA) исключены из статистики
      </p>

      <div className="mb-6 flex gap-4">
        <input
          type="password"
          value={token}
          onChange={(e) => setToken(e.target.value)}
          placeholder="Admin JWT Token"
          className="px-4 py-2 bg-gray-800 rounded-lg flex-1 max-w-md"
        />
        <button
          onClick={fetchDashboard}
          disabled={loading || !token}
          className="px-6 py-2 bg-purple-600 rounded-lg hover:bg-purple-500 disabled:opacity-50"
        >
          {loading ? 'Загрузка…' : 'Обновить'}
        </button>
      </div>

      {error && <p className="text-red-400 mb-4">{error}</p>}

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
        {metrics.map((m) => (
          <div key={m.label} className="bg-gray-800 rounded-xl p-4">
            <p className="text-gray-400 text-sm">{m.label}</p>
            <p className="text-2xl font-bold mt-1">{m.value}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
