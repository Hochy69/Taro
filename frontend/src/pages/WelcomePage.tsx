import { useState } from 'react'
import { motion } from 'framer-motion'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '@/api/client'
import { useAppStore } from '@/store/appStore'
import { useAppNavigation } from '@/hooks/useAppNavigation'
import { GlassCard, Button } from '@/components/ui'
import { TarotCardVisual } from '@/components/tarot/TarotCardVisual'
import { haptic } from '@/lib/telegram'
import { applyDiscount, getStoredPromoPercent } from '@/lib/promo'
import { useQuestionnaireRefill } from '@/hooks/useQuestionnaireRefill'
import { openStarsPayment } from '@/lib/payments'

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
  const { setCategory, isReturning, lastCategory } = useAppStore()
  const queryClient = useQueryClient()
  const [buyingCompat, setBuyingCompat] = useState(false)
  const { data: categories, isLoading } = useQuery({
    queryKey: ['categories'],
    queryFn: api.getCategories,
  })
  const { data: limits } = useQuery({
    queryKey: ['limits'],
    queryFn: api.getLimits,
  })
  const { data: pricing } = useQuery({
    queryKey: ['pricing'],
    queryFn: api.getPricing,
  })
  const { data: cardOfDay } = useQuery({
    queryKey: ['card-of-day'],
    queryFn: api.getCardOfDay,
  })

  const compatPrice = pricing?.compatibility ?? 100
  const promoPercent = getStoredPromoPercent()
  const compatDisplayPrice = applyDiscount(compatPrice, promoPercent)
  const compatCredits = limits?.compatibility_credits ?? 0
  const isPremium = limits?.is_premium ?? false
  const hasCompatAccess = isPremium || compatCredits > 0
  const lastTopic = lastCategory ? CATEGORY_NAMES[lastCategory] || lastCategory : null

  const handleSelect = (category: NonNullable<typeof categories>[0]) => {
    haptic('medium')
    setCategory(category)
    if (limits && !limits.can_spread) {
      goTo('subscription')
      return
    }
    goTo('questionnaire')
  }

  const handleCompatibility = async () => {
    if (hasCompatAccess) {
      haptic('medium')
      goTo('compatibility')
      return
    }
    if (buyingCompat) return
    haptic('medium')
    setBuyingCompat(true)
    try {
      const result = await openStarsPayment('compatibility')
      if (result === 'paid' || result === 'free') {
        queryClient.invalidateQueries({ queryKey: ['limits'] })
        goTo('compatibility')
      }
    } finally {
      setBuyingCompat(false)
    }
  }

  const compatSublabel = isPremium
    ? 'Бесплатно'
    : compatCredits > 0
      ? `${compatCredits} проверок`
      : `${compatDisplayPrice} ⭐`

  const refillQuestionnaire = useQuestionnaireRefill()

  return (
    <div className="page-shell pb-24">
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center mb-8"
      >
        <motion.div
          animate={{ rotate: [0, 5, -5, 0] }}
          transition={{ duration: 4, repeat: Infinity }}
          className="text-6xl mb-4"
        >
          🔮
        </motion.div>
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
        <GlassCard onClick={handleCompatibility} delay={0.04}>
          <div className="text-center py-2 min-w-0">
            <span className="text-3xl block mb-2">💕</span>
            <span className="font-semibold text-white text-sm break-words">Совместимость</span>
            <span className="block text-tarot-gold text-xs mt-1 font-medium break-words">{compatSublabel}</span>
            {!hasCompatAccess && (
              <span className="block text-white/45 text-[11px] mt-1 leading-tight break-words">
                Узнайте, что карты говорят о вас двоих
              </span>
            )}
          </div>
        </GlassCard>
        <GlassCard onClick={() => goTo('cardOfDay')} delay={0.06}>
          <div className="text-center py-2 min-w-0">
            <span className="text-3xl block mb-2">🃏</span>
            <span className="font-semibold text-white text-sm break-words">Карта дня</span>
          </div>
        </GlassCard>
        <GlassCard onClick={() => goTo('natalChart')} delay={0.08}>
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
