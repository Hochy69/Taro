import type { ReactNode } from 'react'
import type { LoveBundle } from '@/api/client'
import { Button, GlassCard } from '@/components/ui'
import { applyDiscount, getStoredPromoPercent } from '@/lib/promo'

type Props = {
  compatBase: number
  loveBundle: LoveBundle
  compatCredits: number
  isPremium: boolean
  busy: string | null
  onBuyCompatibility: () => void
  onBuyLoveBundle: () => void
  renderPrice: (base: number, extraDiscount?: number) => ReactNode
}

export function RelationshipsPremiumHero({
  compatBase,
  loveBundle,
  compatCredits,
  isPremium,
  busy,
  onBuyCompatibility,
  onBuyLoveBundle,
  renderPrice,
}: Props) {
  const promoPercent = getStoredPromoPercent()
  const compatDisplayPrice = applyDiscount(compatBase, promoPercent)

  return (
    <GlassCard className="border-pink-400/35 shadow-lg shadow-pink-500/10 !p-0 overflow-hidden">
      <div className="bg-gradient-to-b from-pink-500/15 to-transparent px-5 pt-6 pb-5 space-y-4">
        <div className="text-center">
          <div className="text-5xl mb-3">💕</div>
          <h2 className="text-xl sm:text-2xl font-display font-bold text-white mb-2">
            Что между вами
          </h2>
          <p className="text-white/65 text-sm leading-relaxed">
            Совместимость по Солнцу и Луне — главная функция для пары
          </p>
        </div>

        <div className="text-center">
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

        <Button
          onClick={onBuyCompatibility}
          disabled={!!busy}
        >
          {busy === 'compatibility' ? 'Оплата...' : 'Купить проверку пары'}
        </Button>

        <GlassCard className="!p-4 border-pink-400/25 bg-pink-500/5">
          <div className="flex items-center justify-between gap-3 min-w-0">
            <div className="min-w-0 flex-1">
              <p className="font-semibold text-white">💞 Пакет «Любовь»</p>
              <p className="text-white/55 text-sm mt-1 break-words">
                {loveBundle.description} • −{loveBundle.savings_percent}%
              </p>
            </div>
            {renderPrice(
              loveBundle.original_stars,
              Math.max(promoPercent, loveBundle.savings_percent),
            )}
          </div>
          <Button
            className="mt-3"
            variant="secondary"
            onClick={onBuyLoveBundle}
            disabled={!!busy}
          >
            {busy === 'love_bundle' ? 'Оплата...' : 'Купить пакет «Любовь»'}
          </Button>
        </GlassCard>

        <p className="text-center text-white/40 text-xs">
          Оплата через Telegram Stars · {compatDisplayPrice} ⭐ за проверку
        </p>
      </div>
    </GlassCard>
  )
}
