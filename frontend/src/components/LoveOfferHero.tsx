import { GlassCard } from '@/components/ui'
import { applyDiscount } from '@/lib/promo'

type LoveOfferHeroProps = {
  compatLabel: string
  compatPrice: number
  spreadPrice: number
  bundleStars?: number
  bundleOriginal?: number
  bundleSavings?: number
  showBundle?: boolean
  onCompat: () => void
  onBundle?: () => void
  compact?: boolean
}

export function LoveOfferHero({
  compatLabel,
  compatPrice,
  spreadPrice,
  bundleStars,
  bundleOriginal,
  bundleSavings = 20,
  showBundle = false,
  onCompat,
  onBundle,
  compact = false,
}: LoveOfferHeroProps) {
  const bundleFinal =
    bundleStars ??
    (bundleOriginal ? applyDiscount(bundleOriginal, bundleSavings) : compatPrice + spreadPrice)

  return (
    <GlassCard
      onClick={onCompat}
      className={`border-pink-400/40 bg-gradient-to-br from-pink-500/15 via-transparent to-tarot-gold/5 ${
        compact ? 'py-3' : 'py-1'
      }`}
    >
      <div className={compact ? 'flex items-center gap-3' : 'text-center'}>
        <span className={compact ? 'text-3xl shrink-0' : 'text-4xl block'}>💕</span>
        <div className={compact ? 'min-w-0 flex-1 text-left' : ''}>
          <h2 className={`font-bold text-white ${compact ? 'text-base' : 'text-xl mt-2'}`}>
            Проверка пары
          </h2>
          <p className={`text-white/60 ${compact ? 'text-xs mt-0.5' : 'text-sm mt-2 px-1'}`}>
            Насколько вы подходите друг другу — сильные стороны союза и зоны риска до важного
            разговора
          </p>
          <div
            className={`flex flex-wrap gap-2 ${compact ? 'mt-2' : 'justify-center mt-4'}`}
            onClick={(e) => e.stopPropagation()}
          >
            <button
              type="button"
              onClick={onCompat}
              className="px-3 py-1.5 rounded-full bg-pink-500/25 border border-pink-400/30 text-pink-100 text-sm font-semibold active:scale-[0.98]"
            >
              {compatLabel}
            </button>
            <span className="px-3 py-1.5 rounded-full bg-white/10 text-white/70 text-sm">
              + расклад {spreadPrice} ⭐
            </span>
            {showBundle && onBundle && bundleOriginal && (
              <button
                type="button"
                onClick={onBundle}
                className="px-3 py-1.5 rounded-full bg-tarot-gold/15 border border-tarot-gold/30 text-tarot-gold text-sm font-semibold active:scale-[0.98]"
              >
                Пакет «Любовь» {bundleFinal} ⭐
              </button>
            )}
          </div>
        </div>
      </div>
    </GlassCard>
  )
}
