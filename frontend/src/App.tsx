import { useEffect, useRef, useState } from 'react'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { useAppStore } from '@/store/appStore'
import {
  api,
  clearAccessToken,
  getAccessToken,
  loadAccessToken,
  loadAuthMeta,
  setAccessToken,
  setAuthMeta,
} from '@/api/client'
import { useAppNavigation, useSyncRouteToStore } from '@/hooks/useAppNavigation'
import { ROUTES } from '@/lib/routes'
import { tryApplyPromoFromUrl } from '@/lib/applyPromoFromUrl'
import { initTelegramWebApp, unlockPageScroll } from '@/lib/telegram'
import { AppHeader } from '@/components/AppHeader'
import { TermsGate } from '@/components/TermsGate'
import AdminDashboard from '@/pages/admin/AdminDashboard'
import { WelcomePage } from '@/pages/WelcomePage'
import { ReturningPage } from '@/pages/ReturningPage'
import { QuestionnairePage } from '@/pages/QuestionnairePage'
import { DeckPage } from '@/pages/DeckPage'
import { ReadingPage } from '@/pages/ReadingPage'
import { HistoryPage } from '@/pages/HistoryPage'
import { SubscriptionPage } from '@/pages/SubscriptionPage'
import { CardOfDayPage } from '@/pages/CardOfDayPage'
import { PortraitPage } from '@/pages/PortraitPage'
import { NatalChartPage } from '@/pages/NatalChartPage'
import { CompatibilityPage } from '@/pages/CompatibilityPage'

function AppRoutes() {
  useSyncRouteToStore()
  return (
    <div className="w-full max-w-full min-h-0">
      <AppHeader />
      <Routes>
        <Route path={ROUTES.welcome} element={<WelcomePage />} />
        <Route path={ROUTES.returning} element={<ReturningPage />} />
        <Route path={ROUTES.questionnaire} element={<QuestionnairePage />} />
        <Route path={ROUTES.deck} element={<DeckPage />} />
        <Route path={ROUTES.reading} element={<ReadingPage />} />
        <Route path={ROUTES.history} element={<HistoryPage />} />
        <Route path={ROUTES.subscription} element={<SubscriptionPage />} />
        <Route path={ROUTES.cardOfDay} element={<CardOfDayPage />} />
        <Route path={ROUTES.portrait} element={<PortraitPage />} />
        <Route path={ROUTES.natalChart} element={<NatalChartPage />} />
        <Route path={ROUTES.compatibility} element={<CompatibilityPage />} />
        <Route path="*" element={<Navigate to={ROUTES.welcome} replace />} />
      </Routes>
    </div>
  )
}

type ProfileMeta = {
  name?: string | null
  birth_date?: string | null
  birth_time?: string | null
  birth_city?: string | null
  gender?: string | null
  zodiac_sign?: string | null
} | null

function applyAuth(
  setAuth: ReturnType<typeof useAppStore.getState>['setAuth'],
  updateQuestionnaire: ReturnType<typeof useAppStore.getState>['updateQuestionnaire'],
  setTermsAccepted: ReturnType<typeof useAppStore.getState>['setTermsAccepted'],
  isPremium: boolean,
  isReturning: boolean,
  lastCategory: string | null,
  profile: ProfileMeta,
  termsAccepted: boolean,
) {
  setAuthMeta({
    is_premium: isPremium,
    is_returning: isReturning,
    last_category: lastCategory,
    terms_accepted: termsAccepted,
    profile,
  })
  setAuth(isPremium, isReturning, lastCategory)
  setTermsAccepted(termsAccepted)

  // Remember the user's earlier answers so returning users don't re-enter them.
  if (profile) {
    const prefill: Partial<{
      name: string
      birthDate: string
      birthTime: string
      birthCity: string
      gender: string
      zodiacSign: string
    }> = {}
    if (profile.name) prefill.name = profile.name
    if (profile.birth_date) prefill.birthDate = profile.birth_date
    if (profile.birth_time) prefill.birthTime = profile.birth_time
    if (profile.birth_city) prefill.birthCity = profile.birth_city
    if (profile.gender) prefill.gender = profile.gender
    if (profile.zodiac_sign) prefill.zodiacSign = profile.zodiac_sign
    if (Object.keys(prefill).length > 0) {
      updateQuestionnaire(prefill)
    }
  }
}

function SessionBootstrap() {
  const { setAuth, updateQuestionnaire, setTermsAccepted } = useAppStore()
  const termsAccepted = useAppStore((s) => s.termsAccepted)
  const isAuthenticated = useAppStore((s) => s.isAuthenticated)
  const { goTo } = useAppNavigation()
  const [loading, setLoading] = useState(true)
  const [bootError, setBootError] = useState<string | null>(null)
  const didRun = useRef(false)

  useEffect(() => {
    if (didRun.current) return
    didRun.current = true

    const tg = window.Telegram?.WebApp
    if (tg) {
      initTelegramWebApp()
    } else {
      unlockPageScroll()
    }

    // Only redirect to the landing screen if the user has not navigated away
    // during the async bootstrap (prevents a late auth response from kicking
    // the user back to the main menu).
    const landing = () => {
      const path = window.location.pathname
      if (path === ROUTES.welcome || path === '/' || path === ROUTES.returning) {
        goTo('welcome', true)
      }
    }

    const afterAuth = async (termsAccepted: boolean) => {
      if (termsAccepted) {
        await tryApplyPromoFromUrl()
      }
    }

    const bootstrap = async () => {
      try {
        setBootError(null)
        loadAccessToken()
        const initData = tg?.initData

        if (initData) {
          const auth = await api.auth(initData)
          setAccessToken(auth.access_token)
          applyAuth(
            setAuth,
            updateQuestionnaire,
            setTermsAccepted,
            auth.user.is_premium,
            auth.is_returning,
            auth.last_category,
            auth.user.profile ?? null,
            auth.user.terms_accepted,
          )
          await afterAuth(auth.user.terms_accepted)
          landing()
          return
        }

        if (getAccessToken()) {
          try {
            const me = await api.getMe()
            const meta = loadAuthMeta()
            applyAuth(
              setAuth,
              updateQuestionnaire,
              setTermsAccepted,
              me.is_premium,
              meta?.is_returning ?? false,
              meta?.last_category ?? null,
              me.profile ?? meta?.profile ?? null,
              me.terms_accepted,
            )
            await afterAuth(me.terms_accepted)
            return
          } catch {
            clearAccessToken()
          }
        }

        const auth = await api.authDev()
        setAccessToken(auth.access_token)
        applyAuth(
          setAuth,
          updateQuestionnaire,
          setTermsAccepted,
          auth.user.is_premium,
          auth.is_returning,
          auth.last_category,
          auth.user.profile ?? null,
          auth.user.terms_accepted,
        )
        await afterAuth(auth.user.terms_accepted)
        landing()
      } catch (e) {
        console.warn('Session bootstrap failed:', e)
        if (tg?.initData) {
          setBootError(
            'Не удалось подключиться к серверу. Закройте мини-приложение, отправьте боту /start и нажмите кнопку снова.',
          )
        } else if (window.location.pathname !== ROUTES.welcome && window.location.pathname !== '/') {
          setBootError(
            'Откройте приложение через бота @best1tarolog_bot (команда /card или кнопка в сообщении), а не по обычной ссылке в браузере.',
          )
        } else {
          landing()
        }
      } finally {
        setLoading(false)
      }
    }

    bootstrap()
  }, [goTo, setAuth, updateQuestionnaire, setTermsAccepted])

  if (loading) {
    return (
      <div className="min-h-screen gradient-bg flex items-center justify-center">
        <div className="text-center">
          <div className="text-5xl animate-pulse mb-4">🔮</div>
          <p className="text-white/50">Открываем карты...</p>
        </div>
      </div>
    )
  }

  if (bootError) {
    return (
      <div className="min-h-screen gradient-bg flex items-center justify-center px-6 text-center">
        <div className="max-w-sm">
          <div className="text-5xl mb-4">⚠️</div>
          <p className="text-white/80 mb-4">{bootError}</p>
          <button
            type="button"
            onClick={() => window.location.reload()}
            className="w-full py-3 rounded-2xl bg-gradient-to-r from-tarot-gold to-yellow-400 text-tarot-dark font-semibold"
          >
            Попробовать снова
          </button>
        </div>
      </div>
    )
  }

  // Gate the whole app behind a one-time acceptance of the offer/terms.
  if (isAuthenticated && !termsAccepted) {
    return <TermsGate />
  }

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen gradient-bg flex items-center justify-center px-6 text-center">
        <div className="max-w-sm">
          <div className="text-5xl mb-4">🔮</div>
          <p className="text-white/80 mb-4">
            Откройте Мир Таро через бота @best1tarolog_bot — отправьте /start и нажмите кнопку
            «Открыть расклад».
          </p>
          <button
            type="button"
            onClick={() => window.location.reload()}
            className="w-full py-3 rounded-2xl bg-gradient-to-r from-tarot-gold to-yellow-400 text-tarot-dark font-semibold"
          >
            Попробовать снова
          </button>
        </div>
      </div>
    )
  }

  return <AppRoutes />
}

export default function App() {
  // The admin dashboard is a completely separate surface: it must bypass the
  // Telegram auth flow and the terms gate, and is only reachable by someone who
  // was given the direct /admin link (with a token) via the hidden bot command.
  if (typeof window !== 'undefined' && window.location.pathname.startsWith('/admin')) {
    return <AdminDashboard />
  }

  return (
    <BrowserRouter>
      <SessionBootstrap />
    </BrowserRouter>
  )
}
