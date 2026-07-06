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

  const lastTopic = lastCategory ? CATEGORY_NAMES[lastCategory] || lastCategory : null

  const compatPrice = pricing?.compatibility ?? 99
  const promoPercent = getStoredPromoPercent()
  const compatDisplayPrice = applyDiscount(compatPrice, promoPercent)
  const compatCredits = limits?.compatibility_credits ?? 0
  const isPremium = Boolean(limits?.is_premium || limits?.is_admin)
  const hasCompatAccess = isPremium || compatCredits > 0

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
        await queryClient.refetchQueries({ queryKey: ['limits'] })
        goTo('compatibility')
      }
    } finally {
      setBuyingCompat(false)
    }
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
        <GlassCard className="border-pink-400/35 shadow-lg shadow-pink-500/10 !p-0 overflow-hidden">
          <div className="bg-gradient-to-b from-pink-500/15 to-transparent px-5 pt-6 pb-5">
            <div className="text-center mb-4">
              <motion.div
                animate={{ scale: [1, 1.06, 1] }}
                transition={{ duration: 2.5, repeat: Infinity }}
                className="text-6xl mb-3"
              >
                💕
              </motion.div>
              <h1 className="text-2xl sm:text-3xl font-display font-bold text-white mb-2">
                Что между вами
              </h1>
              <p className="text-white/65 text-sm leading-relaxed px-1">
                Совместимость по Солнцу и Луне — узнайте сильные стороны пары и зоны напряжения
              </p>
            </div>

            <div className="text-center mb-4">
              {isPremium ? (
                <p className="text-tarot-gold font-semibold text-lg">Бесплатно с Premium</p>
              ) : compatCredits > 0 ? (
                <p className="text-tarot-gold font-semibold text-lg">
                  Доступно проверок: {compatCredits}
                </p>
              ) : (
                <div className="inline-flex flex-col items-center">
                  <span className="text-white/50 text-xs uppercase tracking-wider mb-1">
                    Стоимость проверки
                  </span>
                  <span className="text-4xl font-bold text-tarot-gold leading-none">
                    {compatDisplayPrice}
                    <span className="text-2xl ml-1">⭐</span>
                  </span>
                </div>
              )}
            </div>

            <Button onClick={handleCompatibility} disabled={buyingCompat}>
              {buyingCompat ? 'Оплата...' : 'Проверить пару'}
            </Button>

            {!isPremium && compatCredits === 0 && (
              <p className="text-center text-white/40 text-xs mt-3">
                Оплата через Telegram Stars · {compatDisplayPrice} ⭐ за проверку
              </p>
            )}
          </div>
        </GlassCard>
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
