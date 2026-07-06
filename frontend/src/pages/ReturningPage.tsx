import { useState } from 'react'
import { motion } from 'framer-motion'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '@/api/client'
import { useAppStore } from '@/store/appStore'
import { useAppNavigation } from '@/hooks/useAppNavigation'
import { Button, GlassCard } from '@/components/ui'
import { useQuestionnaireRefill } from '@/hooks/useQuestionnaireRefill'
import { haptic } from '@/lib/telegram'
import { applyDiscount, getStoredPromoPercent } from '@/lib/promo'
import { openStarsPayment } from '@/lib/payments'

const CATEGORY_NAMES: Record<string, string> = {
  love: 'Любовь',
  money: 'Деньги',
  career: 'Карьера',
  family: 'Семья',
  destiny: 'Предназначение',
  general: 'Общий расклад',
}

export function ReturningPage() {
  const { lastCategory, setCategory } = useAppStore()
  const { goTo } = useAppNavigation()
  const queryClient = useQueryClient()
  const [buyingCompat, setBuyingCompat] = useState(false)
  const refillQuestionnaire = useQuestionnaireRefill()
  const { data: categories } = useQuery({ queryKey: ['categories'], queryFn: api.getCategories })
  const { data: limits } = useQuery({ queryKey: ['limits'], queryFn: api.getLimits })
  const { data: pricing } = useQuery({ queryKey: ['pricing'], queryFn: api.getPricing })
  const categoryName = lastCategory ? CATEGORY_NAMES[lastCategory] || lastCategory : 'Общий расклад'

  const compatPrice = pricing?.compatibility ?? 99
  const promoPercent = getStoredPromoPercent()
  const compatDisplayPrice = applyDiscount(compatPrice, promoPercent)
  const compatCredits = limits?.compatibility_credits ?? 0
  const isPremium = Boolean(limits?.is_premium || limits?.is_admin)
  const hasCompatAccess = isPremium || compatCredits > 0

  const continueTopic = () => {
    haptic('medium')
    if (lastCategory) {
      const found = categories?.find((c) => c.slug === lastCategory)
      setCategory(
        found ?? { id: 0, slug: lastCategory, name: categoryName, emoji: '🔮' },
      )
      goTo('questionnaire')
    } else {
      goTo('welcome')
    }
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

  return (
    <div className="page-shell flex flex-col items-center pb-8">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="w-full max-w-md"
      >
        <div className="text-center mb-5">
          <p className="text-white/50 text-sm mb-1">С возвращением!</p>
          <p className="text-white/60 text-sm">
            Последняя тема: <span className="text-tarot-gold">{categoryName}</span>
          </p>
        </div>

        <GlassCard className="mb-4 border-pink-400/35 !p-0 overflow-hidden">
          <div className="bg-gradient-to-b from-pink-500/15 to-transparent px-5 pt-5 pb-4">
            <div className="text-center mb-3">
              <div className="text-5xl mb-2">💕</div>
              <h1 className="text-xl font-display font-bold text-white">Что между вами</h1>
              <p className="text-white/60 text-sm mt-1">Проверьте совместимость пары</p>
            </div>
            {!isPremium && compatCredits === 0 && (
              <p className="text-center text-3xl font-bold text-tarot-gold mb-3">
                {compatDisplayPrice} ⭐
              </p>
            )}
            <Button onClick={handleCompatibility} disabled={buyingCompat}>
              {buyingCompat ? 'Оплата...' : 'Проверить пару'}
            </Button>
          </div>
        </GlassCard>

        <GlassCard className="mb-4">
          <p className="text-center text-white/80 mb-4">Расклады Таро</p>
          <div className="space-y-3">
            <Button onClick={continueTopic}>Продолжить эту тему</Button>
            <Button
              variant="secondary"
              onClick={() => {
                haptic('light')
                goTo('welcome')
              }}
            >
              Новая категория
            </Button>
            <Button
              variant="secondary"
              onClick={() => {
                haptic('light')
                goTo('cardOfDay')
              }}
            >
              Карта дня 🃏
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
            <Button
              variant="secondary"
              onClick={() => {
                haptic('light')
                goTo('natalChart')
              }}
            >
              Натальная карта 🌌
            </Button>
            <Button variant="secondary" onClick={() => refillQuestionnaire(categories)}>
              Заполнить анкету заново
            </Button>
          </div>
        </GlassCard>
      </motion.div>
    </div>
  )
}
