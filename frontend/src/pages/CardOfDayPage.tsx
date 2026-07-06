import { motion } from 'framer-motion'
import { useQuery } from '@tanstack/react-query'
import { api, getAccessToken } from '@/api/client'
import { useAppStore } from '@/store/appStore'
import { useAppNavigation } from '@/hooks/useAppNavigation'
import { Button, GlassCard, Skeleton } from '@/components/ui'
import { TarotCardVisual } from '@/components/tarot/TarotCardVisual'
import { haptic } from '@/lib/telegram'

const SECTIONS = [
  { key: 'meaning', title: 'Послание дня', icon: '🌙' },
  { key: 'advice', title: 'Совет карты', icon: '💫' },
  { key: 'conclusion', title: 'Главная мысль', icon: '✨' },
] as const

export function CardOfDayPage() {
  const { goTo } = useAppNavigation()
  const isAuthenticated = useAppStore((s) => s.isAuthenticated)
  const { data, isLoading, error, refetch, isFetching } = useQuery({
    queryKey: ['card-of-day'],
    queryFn: api.getCardOfDay,
    enabled: isAuthenticated && Boolean(getAccessToken()),
    retry: 2,
  })

  if (!isAuthenticated || !getAccessToken()) {
    return (
      <div className="min-h-screen gradient-bg flex flex-col items-center justify-center px-6 text-center">
        <div className="text-5xl mb-4">🔮</div>
        <p className="text-white/70 mb-6">
          Откройте карту дня через бота @best1tarolog_bot — команда /card или кнопка «Открыть карту» в
          сообщении.
        </p>
        <Button onClick={() => window.location.reload()}>Попробовать снова</Button>
      </div>
    )
  }

  if (isLoading || isFetching) {
    return (
      <div className="min-h-screen gradient-bg px-4 pt-20 pb-8">
        <Skeleton className="h-64 w-full mb-6" />
        <Skeleton className="h-24 w-full mb-3" />
        <Skeleton className="h-24 w-full" />
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className="min-h-screen gradient-bg flex flex-col items-center justify-center px-6 text-center">
        <div className="text-5xl mb-4">🌫️</div>
        <p className="text-white/70 mb-2">Не удалось загрузить карту дня</p>
        {error instanceof Error && error.message && (
          <p className="text-white/40 text-sm mb-6">{error.message}</p>
        )}
        <div className="flex flex-col gap-3 w-full max-w-xs">
          <Button onClick={() => refetch()}>Повторить</Button>
          <Button variant="secondary" onClick={() => goTo('welcome')}>
            На главную
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen gradient-bg px-4 pt-20 pb-8">
      <motion.div
        initial={{ opacity: 0, y: -12 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center mb-8"
      >
        <p className="text-tarot-gold text-sm mb-2">Карта дня</p>
        <h1 className="text-2xl font-display font-bold text-white">
          {new Date(data.date).toLocaleDateString('ru-RU', {
            day: 'numeric',
            month: 'long',
          })}
        </h1>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="flex justify-center mb-8"
      >
        <TarotCardVisual
          slug={data.card.slug}
          name={data.card.name}
          imageUrl={data.card.image_url}
          isReversed={data.card.is_reversed}
          size="lg"
          showName
        />
      </motion.div>

      <div className="max-w-md mx-auto space-y-4">
        {SECTIONS.map((section, i) => {
          const text = data[section.key]
          if (!text) return null
          return (
            <motion.div
              key={section.key}
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1 }}
            >
              <GlassCard>
                <h3 className="text-tarot-gold font-semibold mb-2">
                  {section.icon} {section.title}
                </h3>
                <p className="text-white/80 leading-relaxed">{text}</p>
              </GlassCard>
            </motion.div>
          )
        })}
      </div>

      <div className="max-w-md mx-auto mt-8 space-y-3">
        <Button
          onClick={() => {
            haptic('light')
            goTo('welcome')
          }}
        >
          Новый расклад 🔮
        </Button>
        <Button
          variant="secondary"
          onClick={() => {
            haptic('light')
            goTo('portrait')
          }}
        >
          Мой портрет ✨
        </Button>
      </div>
    </div>
  )
}
