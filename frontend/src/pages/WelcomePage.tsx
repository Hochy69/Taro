import { motion } from 'framer-motion'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/api/client'
import { useAppStore } from '@/store/appStore'
import { useAppNavigation } from '@/hooks/useAppNavigation'
import { GlassCard, Button } from '@/components/ui'
import { TarotCardVisual } from '@/components/tarot/TarotCardVisual'
import { CompatibilityHero } from '@/components/CompatibilityHero'
import { useQuestionnaireRefill } from '@/hooks/useQuestionnaireRefill'
import { haptic } from '@/lib/telegram'

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
      {isReturning && (
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-center text-white/50 text-sm mb-4 px-2"
        >
          С возвращением!
          {lastTopic && (
            <>
              {' '}
              Последняя тема: <span className="text-tarot-gold">{lastTopic}</span>
            </>
          )}
        </motion.p>
      )}

      <motion.div
        initial={{ opacity: 0, y: -16 }}
        animate={{ opacity: 1, y: 0 }}
        className="max-w-md mx-auto mb-6"
      >
        <CompatibilityHero />
      </motion.div>

      {cardOfDay && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          className="max-w-md mx-auto mb-8"
        >
          <GlassCard onClick={() => goTo('cardOfDay')} className="!p-5">
            <p className="text-tarot-gold text-sm font-semibold text-center mb-4">Карта дня</p>
            <div className="flex flex-col items-center text-center gap-4">
              <TarotCardVisual
                slug={cardOfDay.card.slug}
                name={cardOfDay.card.name}
                imageUrl={cardOfDay.card.image_url}
                isReversed={cardOfDay.card.is_reversed}
                size="lg"
              />
              <div className="min-w-0 w-full">
                <p className="text-white font-display font-semibold text-lg mb-2">
                  {cardOfDay.card.name}
                </p>
                <p className="text-white/55 text-sm leading-relaxed line-clamp-3">
                  {cardOfDay.meaning}
                </p>
                <p className="text-tarot-gold/80 text-xs mt-3">Нажмите, чтобы открыть полностью →</p>
              </div>
            </div>
          </GlassCard>
        </motion.div>
      )}

      <div className="max-w-md mx-auto mb-4 px-1">
        <h2 className="text-white/70 text-sm font-semibold uppercase tracking-wide text-center">
          Расклады Таро
        </h2>
        <p className="text-white/40 text-xs text-center mt-1 mb-3">
          Выберите сферу жизни для классического расклада
        </p>
      </div>

      <div className="grid grid-cols-2 gap-3 max-w-md mx-auto w-full min-w-0 mb-6">
        <GlassCard onClick={() => goTo('portrait')} delay={0.02}>
          <div className="text-center py-2 min-w-0">
            <span className="text-3xl block mb-2">✨</span>
            <span className="font-semibold text-white text-sm break-words">Мой портрет</span>
          </div>
        </GlassCard>
        <GlassCard onClick={() => goTo('natalChart')} delay={0.04}>
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
              <GlassCard key={cat.slug} onClick={() => handleSelect(cat)} delay={0.06 + i * 0.04}>
                <div className="text-center py-2 min-w-0">
                  <span className="text-3xl sm:text-4xl block mb-2">{cat.emoji}</span>
                  <span className="font-semibold text-white text-sm break-words leading-tight">
                    {cat.name}
                  </span>
                </div>
              </GlassCard>
            ))}
      </div>

      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        className="max-w-md mx-auto"
      >
        <Button variant="secondary" onClick={() => refillQuestionnaire(categories)}>
          📝 Заполнить анкету заново
        </Button>
      </motion.div>
    </div>
  )
}
