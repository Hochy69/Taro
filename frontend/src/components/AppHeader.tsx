import { useEffect, useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { useLocation, useNavigate } from 'react-router-dom'
import { PATH_TO_SCREEN } from '@/lib/routes'
import { type AppScreen } from '@/store/appStore'
import { useAppNavigation } from '@/hooks/useAppNavigation'
import { useQuestionnaireRefill } from '@/hooks/useQuestionnaireRefill'
import { haptic } from '@/lib/telegram'

const TITLES: Record<AppScreen, string> = {
  welcome: 'Мир Таро',
  returning: 'С возвращением',
  questionnaire: 'Анкета',
  deck: 'Колода',
  reading: 'Ваш расклад',
  result: 'Ваш расклад',
  history: 'История',
  subscription: 'Premium',
  cardOfDay: 'Карта дня',
  portrait: 'Мой портрет',
  natalChart: 'Натальная карта',
  compatibility: 'Что между вами',
}

const MENU_ITEMS: { id: string; screen: AppScreen; label: string; icon: string }[] = [
  { id: 'compat', screen: 'compatibility', label: 'Что между вами — 79 ⭐', icon: '💕' },
  { id: 'spread', screen: 'welcome', label: 'Новый расклад', icon: '🔮' },
  { id: 'cardday', screen: 'cardOfDay', label: 'Карта дня', icon: '🃏' },
  { id: 'portrait', screen: 'portrait', label: 'Мой портрет', icon: '✨' },
  { id: 'natal', screen: 'natalChart', label: 'Натальная карта', icon: '🌌' },
  { id: 'returning', screen: 'returning', label: 'Меню возвращения', icon: '✨' },
  { id: 'history', screen: 'history', label: 'История раскладов', icon: '📜' },
  { id: 'referral', screen: 'subscription', label: 'Пригласить друга', icon: '🎁' },
  { id: 'premium', screen: 'subscription', label: 'Premium подписка', icon: '⭐️' },
]

export function AppHeader() {
  const [open, setOpen] = useState(false)
  const location = useLocation()
  const navigate = useNavigate()
  const { goTo } = useAppNavigation()
  const refillQuestionnaire = useQuestionnaireRefill()

  const screen: AppScreen = PATH_TO_SCREEN[location.pathname] ?? 'welcome'
  const isReferralScreen = screen === 'subscription' && location.hash === '#referral'
  const isEntry = screen === 'welcome' || screen === 'returning'

  const goBack = () => {
    haptic('light')
    if (window.history.length > 1) {
      navigate(-1)
    } else {
      goTo('welcome')
    }
  }

  // Wire Telegram's native BackButton (top-left in the Telegram header).
  useEffect(() => {
    const bb = window.Telegram?.WebApp?.BackButton
    if (!bb) return
    if (!isEntry) {
      bb.show()
      bb.onClick(goBack)
    } else {
      bb.hide()
    }
    return () => {
      try {
        bb.offClick(goBack)
      } catch {
        /* noop */
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isEntry, location.pathname])

  const navigateTo = (target: AppScreen, hash?: string) => {
    haptic('light')
    setOpen(false)
    goTo(target, hash ? { hash } : undefined)
  }

  const handleQuestionnaireRefill = () => {
    setOpen(false)
    refillQuestionnaire()
  }

  return (
    <>
      <header className="app-header fixed top-0 inset-x-0 z-40 flex items-center justify-between px-2 max-w-full
                         bg-tarot-dark/70 backdrop-blur-md border-b border-white/5">
        <div className="flex items-center gap-1 min-w-0 shrink">
          <button
            onClick={() => {
              haptic('light')
              setOpen(true)
            }}
            aria-label="Меню"
            className="p-2 rounded-xl text-white/90 hover:bg-white/10 active:scale-95 transition"
          >
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
              <line x1="3" y1="6" x2="21" y2="6" />
              <line x1="3" y1="12" x2="21" y2="12" />
              <line x1="3" y1="18" x2="21" y2="18" />
            </svg>
          </button>
          {!isEntry && (
            <button
              onClick={goBack}
              aria-label="Назад"
              className="p-2 rounded-xl text-white/90 hover:bg-white/10 active:scale-95 transition flex items-center gap-1"
            >
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M15 18l-6-6 6-6" />
              </svg>
              <span className="text-sm">Назад</span>
            </button>
          )}
        </div>

        <span className="text-sm font-medium text-white/70 pr-2 truncate shrink min-w-0 max-w-[45%] text-right">
          {isReferralScreen ? 'Пригласи друга' : TITLES[screen]}
        </span>
      </header>

      <AnimatePresence>
        {open && (
          <>
            <motion.div
              className="fixed inset-0 z-50 bg-black/60"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setOpen(false)}
            />
            <motion.aside
              className="fixed top-0 left-0 z-50 h-full w-72 max-w-[80%] bg-tarot-dark
                         border-r border-white/10 p-6 flex flex-col overflow-hidden"
              initial={{ x: '-100%' }}
              animate={{ x: 0 }}
              exit={{ x: '-100%' }}
              transition={{ type: 'tween', duration: 0.25 }}
            >
              <div className="flex items-center justify-between mb-8">
                <span className="text-xl font-display font-bold text-tarot-gold">🔮 Мир Таро</span>
                <button
                  onClick={() => setOpen(false)}
                  aria-label="Закрыть"
                  className="p-2 text-white/60 hover:text-white"
                >
                  ✕
                </button>
              </div>

              <nav className="space-y-1 flex-1 min-h-0 overflow-y-auto -mx-1 px-1">
                {MENU_ITEMS.map((item) => (
                  <button
                    key={item.id}
                    onClick={() => navigateTo(item.screen, item.id === 'referral' ? 'referral' : undefined)}
                    className={`w-full flex items-center gap-3 px-4 py-3 rounded-2xl text-left
                                transition active:scale-[0.98] ${
                                  (item.id === 'referral' && isReferralScreen) ||
                                  (item.id === 'premium' && screen === 'subscription' && !isReferralScreen) ||
                                  (item.id !== 'referral' && item.id !== 'premium' && screen === item.screen)
                                    ? 'bg-tarot-gold/15 text-tarot-gold'
                                    : 'text-white/90 hover:bg-white/10'
                                }`}
                  >
                    <span className="text-xl">{item.icon}</span>
                    <span className="font-medium truncate">{item.label}</span>
                  </button>
                ))}
              </nav>

              <button
                type="button"
                onClick={handleQuestionnaireRefill}
                className="mt-3 shrink-0 w-full flex items-center gap-3 px-4 py-3 rounded-2xl text-left
                           bg-tarot-gold/10 border border-tarot-gold/30 text-tarot-gold
                           hover:bg-tarot-gold/20 transition active:scale-[0.98]"
              >
                <span className="text-xl">📝</span>
                <span className="font-medium">Заполнить анкету заново</span>
              </button>

              <p className="mt-3 shrink-0 text-xs text-white/30">Мир Таро • v1.0</p>
            </motion.aside>
          </>
        )}
      </AnimatePresence>
    </>
  )
}
