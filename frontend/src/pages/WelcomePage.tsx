import { motion } from 'framer-motion'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/api/client'
import { useAppStore } from '@/store/appStore'
import { useAppNavigation } from '@/hooks/useAppNavigation'
import { GlassCard, Button } from '@/components/ui'
import { TarotCardVisual } from '@/components/tarot/TarotCardVisual'
import { haptic } from '@/lib/telegram'
import { useQuestionnaireRefill } from '@/hooks/useQuestionnaireRefill'

const CATEGORY_NAMES: Record<string, string> = {
  love: 'Любовь',
  money: 'Деньги',
  career: 'Карьера',
  family: 'Семья',
  destiny: 'Предназначение',
  general: 'Общий расклад',
}

export function WelcomePage() {
  const { goTo } = useAppNavigation()
  const { setCategory, isReturning, lastCategory, isAuthenticated } = useAppStore()
  const { data: categories, isLoading } = useQuery({
    queryKey: ['categories'],
    queryFn: api.getCategories,
  })
  const { data: limits } = useQuery({
    queryKey: ['limits'],
    queryFn: api.getLimits,
  })
  const { data: cardOfDay } = useQuery({
    queryKey: ['card-of-day'],
    queryFn: api.getCardOfDay,
    enabled: isAuthenticated,
  })

  const lastTopic = lastCategory ? CATEGORY_NAMES[lastCategory] || lastCategory : null

  const handleSelect = (category: NonNullable<typeof categories>[0]) => {
    haptic('medium')
    setCategory(category)
    if (limits && !limits.can_spread && !limits.is_admin) {
      goTo('subscription')
      return
    }
    goTo('questionnaire')
  }

  const refillQuestionnaire = useQuestionnaireRefill()

  return (
    <div className="page-shell pb-24">
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center mb-8"
      >
        <div className="hero-star mb-4">
          <span className="hero-star-glow" aria-hidden />
          <motion.div
            animate={{ rotate: [0, 5, -5, 0] }}
            transition={{ duration: 4, repeat: Infinity }}
            className="relative text-6xl"
          >
            {isReturning ? '✨' : '🔮'}
          </motion.div>
        </div>
        <h1 className="text-2xl sm:text-3xl font-display font-bold text-white mb-3 px-2 break-words">
          {isReturning ? 'С возвращением!' : 'Добро пожаловать в Мир Таро'}
        </h1>
        <p className="text-white/60 text-base sm:text-lg px-2 break-words">
          {isReturning && lastTopic
            ? <>Последняя тема: <span className="text-tarot-gold">{lastTopic}</span></>
            : 'Выберите сферу жизни, которая волнует вас сейчас'}
        </p>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        className="max-w-md mx-auto mb-6"
      >
        <Button
          onClick={() => {
            haptic('medium')
            goTo('compatibility')
          }}
        >
          💕 Что между вами
        </Button>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        className="max-w-md mx-auto mb-6"
      >
        <Button variant="secondary" onClick={() => refillQuestionnaire(categories)}>
          📝 Заполнить анкету заново
        </Button>
      </motion.div>

      {cardOfDay && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          className="max-w-md mx-auto mb-6"
        >
          <GlassCard onClick={() => goTo('cardOfDay')}>
            <div className="flex items-center gap-4">
              <TarotCardVisual
                slug={cardOfDay.card.slug}
                name={cardOfDay.card.name}
                imageUrl={cardOfDay.card.image_url}
                isReversed={cardOfDay.card.is_reversed}
                size="sm"
              />
              <div className="flex-1 min-w-0">
                <p className="text-tarot-gold text-sm font-semibold mb-1">Карта дня</p>
                <p className="text-white font-medium truncate">{cardOfDay.card.name}</p>
                <p className="text-white/50 text-sm line-clamp-2 mt-1">{cardOfDay.meaning}</p>
              </div>
            </div>
          </GlassCard>
        </motion.div>
      )}

      <div className="grid grid-cols-2 gap-3 max-w-md mx-auto w-full min-w-0">
        <GlassCard onClick={() => goTo('portrait')} delay={0.02}>
          <div className="text-center py-2 min-w-0">
            <span className="text-3xl block mb-2">✨</span>
            <span className="font-semibold text-white text-sm break-words">Мой портрет</span>
          </div>
        </GlassCard>
        <GlassCard onClick={() => goTo('cardOfDay')} delay={0.04}>
          <div className="text-center py-2 min-w-0">
            <span className="text-3xl block mb-2">🃏</span>
            <span className="font-semibold text-white text-sm break-words">Карта дня</span>
          </div>
        </GlassCard>
        <GlassCard onClick={() => goTo('natalChart')} delay={0.06}>
          <div className="text-center py-2 min-w-0">
            <span className="text-3xl block mb-2">🌌</span>
            <span className="font-semibold text-white text-sm break-words">Натальная карта</span>
          </div>
        </GlassCard>

        {isLoading
          ? Array.from({ length: 6 }).map((_, i) => (
              <div key={`sk-${i}`} className="h-28 skeleton rounded-2xl" />
            ))
          : categories?.map((cat, i) => (
              <GlassCard key={cat.slug} onClick={() => handleSelect(cat)} delay={0.1 + i * 0.04}>
                <div className="text-center py-2 min-w-0">
                  <span className="text-3xl sm:text-4xl block mb-2">{cat.emoji}</span>
                  <span className="font-semibold text-white text-sm break-words leading-tight">{cat.name}</span>
                </div>
              </GlassCard>
            ))}
      </div>
    </div>
  )
}
