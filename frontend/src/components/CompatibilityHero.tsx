import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '@/api/client'
import { useAppNavigation } from '@/hooks/useAppNavigation'
import { Button, GlassCard } from '@/components/ui'
import { haptic } from '@/lib/telegram'
import { applyDiscount, getStoredPromoPercent } from '@/lib/promo'
import { openStarsPayment } from '@/lib/payments'

export function useCompatibilityPurchase() {
  const { goTo } = useAppNavigation()
  const queryClient = useQueryClient()
  const [buyingCompat, setBuyingCompat] = useState(false)

  const { data: limits } = useQuery({
    queryKey: ['limits'],
    queryFn: api.getLimits,
  })
  const { data: pricing } = useQuery({
    queryKey: ['pricing'],
    queryFn: api.getPricing,
  })

  const compatPrice = pricing?.compatibility ?? 99
  const promoPercent = getStoredPromoPercent()
  const compatDisplayPrice = applyDiscount(compatPrice, promoPercent)
  const compatCredits = limits?.compatibility_credits ?? 0
  const isPremium = Boolean(limits?.is_premium || limits?.is_admin)
  const hasCompatAccess = isPremium || compatCredits > 0

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

  return {
    buyingCompat,
    compatDisplayPrice,
    compatCredits,
    isPremium,
    hasCompatAccess,
    handleCompatibility,
  }
}

export function CompatibilityHero({ className = '' }: { className?: string }) {
  const {
    buyingCompat,
    compatDisplayPrice,
    compatCredits,
    isPremium,
    handleCompatibility,
  } = useCompatibilityPurchase()

  return (
    <GlassCard
      className={`border-pink-400/35 shadow-lg shadow-pink-500/10 !p-0 overflow-hidden ${className}`}
    >
      <div className="bg-gradient-to-b from-pink-500/15 to-transparent px-5 pt-6 pb-5">
        <div className="text-center mb-4">
          <div className="text-6xl mb-3">💕</div>
          <h1 className="text-2xl sm:text-3xl font-display font-bold text-white mb-2">
            Что между вами
          </h1>
          <p className="text-white/65 text-sm leading-relaxed px-1">
            Совместимость по Солнцу и Луне — узнайте сильные стороны пары и зоны напряжения
          </p>
        </div>

        <div className="text-center mb-4">
          <div className="inline-flex flex-col items-center">
            <span className="text-white/50 text-xs uppercase tracking-wider mb-1">
              Стоимость проверки
            </span>
            <span className="text-4xl font-bold text-tarot-gold leading-none">
              {compatDisplayPrice}
              <span className="text-2xl ml-1">⭐</span>
            </span>
            {isPremium ? (
              <span className="text-tarot-gold text-sm font-medium mt-2">бесплатно с Premium</span>
            ) : compatCredits > 0 ? (
              <span className="text-tarot-gold text-sm font-medium mt-2">
                У вас доступно: {compatCredits}
              </span>
            ) : null}
          </div>
        </div>

        <Button onClick={handleCompatibility} disabled={buyingCompat}>
          {buyingCompat ? 'Оплата...' : 'Проверить пару'}
        </Button>

        <p className="text-center text-white/40 text-xs mt-3">
          Оплата через Telegram Stars · {compatDisplayPrice} ⭐ за проверку
        </p>
      </div>
    </GlassCard>
  )
}
