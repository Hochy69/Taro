import { motion } from 'framer-motion'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/api/client'
import { useAppNavigation } from '@/hooks/useAppNavigation'
import { Button, GlassCard, Skeleton } from '@/components/ui'
import { haptic } from '@/lib/telegram'

const SECTIONS = [
  { key: 'essence', title: 'Суть знака', icon: '☉' },
  { key: 'strengths', title: 'Сильные стороны', icon: '💪' },
  { key: 'shadow', title: 'Тень знака', icon: '🌑' },
  { key: 'love', title: 'Любовь', icon: '❤️' },
  { key: 'career', title: 'Реализация', icon: '💼' },
  { key: 'advice', title: 'Совет звёзд', icon: '✨' },
] as const

export function PortraitPage() {
  const { goTo } = useAppNavigation()
  const { data, isLoading, error } = useQuery({
    queryKey: ['portrait'],
    queryFn: api.getPortrait,
    retry: false,
  })

  if (isLoading) {
    return (
      <div className="min-h-screen gradient-bg px-4 pt-20 pb-8 space-y-4">
        <Skeleton className="h-20 w-full" />
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-32 w-full" />
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className="min-h-screen gradient-bg flex flex-col items-center justify-center px-6 text-center">
        <div className="text-5xl mb-4">🌙</div>
        <p className="text-white/70 mb-2">Портрет пока недоступен</p>
        <p className="text-white/50 text-sm mb-6">
          Заполните дату рождения в анкете при следующем раскладе
        </p>
        <Button onClick={() => goTo('welcome')}>Сделать расклад</Button>
      </div>
    )
  }

  return (
    <div className="page-shell">
      <motion.div
        initial={{ opacity: 0, y: -12 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center mb-8"
      >
        <div className="text-5xl mb-3">{data.emoji}</div>
        <h1 className="text-3xl font-display font-bold text-white mb-2">
          {data.zodiac_sign}
        </h1>
        <p className="text-white/60 break-words px-2">{data.summary}</p>
      </motion.div>

      <div className="max-w-md mx-auto space-y-4">
        {data.lunar && (
          <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}>
            <GlassCard>
              <h3 className="text-tarot-gold font-semibold mb-2">🌙 Лунный день рождения</h3>
              <p className="text-white/50 text-sm mb-2 capitalize">{data.lunar.title}</p>
              <p className="text-white/80 leading-relaxed mb-3">{data.lunar.meaning}</p>
              <p className="text-white/60 text-sm">{data.lunar.advice}</p>
            </GlassCard>
          </motion.div>
        )}

        {SECTIONS.map((section, i) => {
          const text = data[section.key]
          if (!text) return null
          return (
            <motion.div
              key={section.key}
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.08 * (i + 1) }}
            >
              <GlassCard>
                <h3 className="text-tarot-gold font-semibold mb-2">
                  {section.icon} {section.title}
                </h3>
                <p className="text-white/80 leading-relaxed break-words">{text}</p>
              </GlassCard>
            </motion.div>
          )
        })}
      </div>

      <div className="max-w-md mx-auto mt-8 space-y-3">
        <Button
          onClick={() => {
            haptic('light')
            goTo('cardOfDay')
          }}
        >
          Карта дня 🃏
        </Button>
        <Button
          onClick={() => {
            haptic('light')
            goTo('natalChart')
          }}
        >
          Натальная карта 🌌
        </Button>
        <Button
          variant="secondary"
          onClick={() => {
            haptic('light')
            goTo('welcome')
          }}
        >
          Новый расклад
        </Button>
      </div>
    </div>
  )
}
