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
import { LoveOfferHero } from '@/components/LoveOfferHero'

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
    enabled: isAuthenticated,
  })

  const compatPrice = pricing?.compatibility ?? 99
  const promoPercent = getStoredPromoPercent()
  const compatDisplayPrice = applyDiscount(compatPrice, promoPercent)
  const compatCredits = limits?.compatibility_credits ?? 0
  const isPremium = Boolean(limits?.is_premium || limits?.is_admin)
  const hasCompatAccess = isPremium || compatCredits > 0
  const lastTopic = lastCategory ? CATEGORY_NAMES[lastCategory] || lastCategory : null

  const loveCategory = categories?.find((c) => c.slug === 'love')
  const otherCategories = categories?.filter((c) => c.slug !== 'love')

  const handleSelect = (category: NonNullable<typeof categories>[0]) => {
    haptic('medium')
    setCategory(category)
    if (limits && !limits.can_spread && !limits.is_admin) {
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

  const handleLoveBundle = async () => {
    if (buyingCompat) return
    haptic('medium')
    setBuyingCompat(true)
    try {
      const result = await openStarsPayment('love_bundle')
      if (result === 'paid' || result === 'free') {
        queryClient.invalidateQueries({ queryKey: ['limits'] })
        goTo('compatibility')
      }
    } finally {
      setBuyingCompat(false)
    }
  }

  const compatSublabel =
    compatCredits > 0 ? `${compatCredits} проверок` : `${compatDisplayPrice} ⭐`

  const spreadPrice = pricing?.single_spread ?? 69
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
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        className="max-w-md mx-auto mb-6"
      >
        <LoveOfferHero
          compatLabel={compatSublabel}
          compatPrice={compatDisplayPrice}
          spreadPrice={spreadPrice}
          bundleOriginal={pricing?.love_bundle?.original_stars}
          bundleStars={pricing?.love_bundle?.stars}
          bundleSavings={pricing?.love_bundle?.savings_percent}
          showBundle={!isPremium && Boolean(pricing?.love_bundle)}
          onCompat={handleCompatibility}
          onBundle={handleLoveBundle}
        />
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

      <div className="grid grid-cols-2 gap-3 max-w-md mx-auto w-full min-w-0">
        <GlassCard onClick={() => goTo('portrait')} delay={0.02}>
          <div className="text-center py-2 min-w-0">
            <span className="text-3xl block mb-2">✨</span>
            <span className="font-semibold text-white text-sm break-words">Мой портрет</span>
          </div>
        </GlassCard>

        <GlassCard onClick={() => goTo('cardOfDay')} delay={0.04}>
          {cardOfDay ? (
            <div className="flex items-center gap-3 min-w-0 py-1">
              <TarotCardVisual
                slug={cardOfDay.card.slug}
                name={cardOfDay.card.name}
                imageUrl={cardOfDay.card.image_url}
                isReversed={cardOfDay.card.is_reversed}
                size="sm"
              />
              <div className="flex-1 min-w-0 text-left">
                <p className="text-tarot-gold text-xs font-semibold mb-0.5">Карта дня</p>
                <p className="text-white text-sm font-medium truncate">{cardOfDay.card.name}</p>
              </div>
            </div>
          ) : (
            <div className="text-center py-2 min-w-0">
              <span className="text-3xl block mb-2">🃏</span>
              <span className="font-semibold text-white text-sm break-words">Карта дня</span>
            </div>
          )}
        </GlassCard>

        {loveCategory && (
          <GlassCard
            onClick={() => handleSelect(loveCategory)}
            delay={0.06}
            className="col-span-2 border-pink-400/35 bg-gradient-to-r from-pink-500/10 to-transparent"
          >
            <div className="flex items-center justify-center gap-4 py-3 min-w-0">
              <span className="text-4xl sm:text-5xl shrink-0">{loveCategory.emoji}</span>
              <div className="text-left min-w-0">
                <span className="font-semibold text-white text-base sm:text-lg break-words leading-tight block">
                  Любовь
                </span>
                <span className="block text-pink-200/80 text-sm mt-1">
                  Расклад на отношения, чувства и пару
                </span>
              </div>
            </div>
          </GlassCard>
        )}

        <GlassCard onClick={() => goTo('natalChart')} delay={0.08}>
          <div className="text-center py-2 min-w-0">
            <span className="text-3xl block mb-2">🌌</span>
            <span className="font-semibold text-white text-sm break-words">Натальная карта</span>
          </div>
        </GlassCard>

        {isLoading
          ? Array.from({ length: 4 }).map((_, i) => (
              <div key={`sk-${i}`} className="col-span-2 h-28 skeleton rounded-2xl" />
            ))
          : otherCategories?.map((cat, i) => (
                <GlassCard key={cat.slug} onClick={() => handleSelect(cat)} delay={0.12 + i * 0.04}>
                  <div className="text-center py-2 min-w-0">
                    <span className="text-3xl sm:text-4xl block mb-2">{cat.emoji}</span>
                    <span className="font-semibold text-white text-sm break-words leading-tight">
                      {cat.name}
                    </span>
                  </div>
                </GlassCard>
              ))}
      </div>
    </div>
  )
}
