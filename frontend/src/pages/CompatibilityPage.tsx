import { useState } from 'react'
import { motion } from 'framer-motion'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api, type PartnerBirthData } from '@/api/client'
import { useAppNavigation } from '@/hooks/useAppNavigation'
import { Button, GlassCard } from '@/components/ui'
import { haptic } from '@/lib/telegram'
import { applyDiscount, getStoredPromoPercent } from '@/lib/promo'
import { openStarsPayment } from '@/lib/payments'

export function CompatibilityPage() {
  const { goTo } = useAppNavigation()
  const queryClient = useQueryClient()
  const [buying, setBuying] = useState(false)
  const { data: limits } = useQuery({
    queryKey: ['limits'],
    queryFn: api.getLimits,
  })
  const { data: pricing } = useQuery({
    queryKey: ['pricing'],
    queryFn: api.getPricing,
  })
  const [form, setForm] = useState<PartnerBirthData>({
    name: '',
    birth_date: '',
    birth_time: '',
    birth_city: '',
    gender: '',
  })
  const [buyingBundle, setBuyingBundle] = useState(false)

  const compatPrice = pricing?.compatibility ?? 99
  const promoPercent = getStoredPromoPercent()
  const compatDisplayPrice = applyDiscount(compatPrice, promoPercent)
  const compatCredits = limits?.compatibility_credits ?? 0
  const isPremium = Boolean(limits?.is_premium || limits?.is_admin)
  const hasCompatAccess = isPremium || compatCredits > 0

  const mutation = useMutation({
    mutationFn: api.getCompatibility,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['limits'] })
    },
  })

  const buyCredit = async () => {
    if (buying) return
    haptic('medium')
    setBuying(true)
    try {
      const result = await openStarsPayment('compatibility')
      if (result === 'paid' || result === 'free') {
        queryClient.invalidateQueries({ queryKey: ['limits'] })
      }
    } finally {
      setBuying(false)
    }
  }

  const buyLoveBundle = async () => {
    if (buyingBundle) return
    haptic('medium')
    setBuyingBundle(true)
    try {
      const result = await openStarsPayment('love_bundle')
      if (result === 'paid' || result === 'free') {
        queryClient.invalidateQueries({ queryKey: ['limits'] })
      }
    } finally {
      setBuyingBundle(false)
    }
  }

  const submit = () => {
    if (!form.name.trim() || !form.birth_date) return
    if (!hasCompatAccess) {
      buyCredit()
      return
    }
    haptic('medium')
    mutation.mutate({
      name: form.name.trim(),
      birth_date: form.birth_date,
      birth_time: form.birth_time || undefined,
      birth_city: form.birth_city || undefined,
      gender: form.gender || undefined,
    })
  }

  if (mutation.data) {
    const d = mutation.data
    return (
      <div className="page-shell">
        <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="text-center mb-8 px-2">
          <div className="text-5xl mb-2">💕</div>
          <h1 className="text-2xl font-display font-bold text-white mb-1 break-words">
            {d.partner_name}
          </h1>
          <p className="text-4xl font-bold text-tarot-gold">{d.score}%</p>
          <p className="text-white/50 text-sm mt-1">совместимость</p>
        </motion.div>

        <div className="max-w-md mx-auto space-y-4">
          <GlassCard>
            <p className="text-white/80 break-words">{d.summary}</p>
          </GlassCard>
          <GlassCard>
            <h3 className="text-tarot-gold font-semibold mb-2">☉ Солнце</h3>
            <p className="text-white/75 text-sm break-words">{d.sun_match}</p>
          </GlassCard>
          {d.moon_match && (
            <GlassCard>
              <h3 className="text-tarot-gold font-semibold mb-2">☽ Луна</h3>
              <p className="text-white/75 text-sm break-words">{d.moon_match}</p>
            </GlassCard>
          )}
          <GlassCard>
            <h3 className="text-tarot-gold font-semibold mb-2">❤️ Любовь</h3>
            <p className="text-white/75 text-sm break-words">{d.love}</p>
          </GlassCard>
          <GlassCard>
            <h3 className="text-tarot-gold font-semibold mb-2">🤝 Дружба</h3>
            <p className="text-white/75 text-sm break-words">{d.friendship}</p>
          </GlassCard>
          <GlassCard>
            <h3 className="text-tarot-gold font-semibold mb-2">⚡ Вызовы</h3>
            <p className="text-white/75 text-sm break-words">{d.challenges}</p>
          </GlassCard>
          <GlassCard>
            <h3 className="text-tarot-gold font-semibold mb-2">✨ Совет</h3>
            <p className="text-white/75 text-sm break-words">{d.advice}</p>
          </GlassCard>
        </div>

        <div className="max-w-md mx-auto mt-8 space-y-3">
          <Button onClick={() => mutation.reset()}>Проверить другого человека</Button>
          <Button variant="secondary" onClick={() => goTo('welcome')}>На главную</Button>
        </div>
      </div>
    )
  }

  return (
    <div className="page-shell">
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="text-center mb-8 px-2">
        <div className="text-5xl mb-3">💕</div>
        <h1 className="text-2xl sm:text-3xl font-display font-bold text-white mb-2">Проверка на пару</h1>
        <p className="text-white/60 text-sm break-words">Синастрия lite — Солнце и Луна двух карт</p>
        <p className="text-white/45 text-xs mt-2 px-4 break-words">
          Проверьте совместимость до важного разговора — карты покажут сильные стороны и зоны напряжения
        </p>
        {isPremium ? (
          <p className="text-tarot-gold text-sm mt-2">Бесплатно с Premium</p>
        ) : compatCredits > 0 ? (
          <p className="text-tarot-gold text-sm mt-2">Доступно проверок: {compatCredits}</p>
        ) : (
          <p className="text-tarot-gold text-sm mt-2">Стоимость проверки: {compatDisplayPrice} ⭐</p>
        )}
      </motion.div>

      <div className="max-w-md mx-auto space-y-4">
        {pricing?.love_bundle && !isPremium && (
          <GlassCard className="border-pink-400/25">
            <p className="text-tarot-gold font-semibold mb-1">💕 Пакет «Любовь»</p>
            <p className="text-white/70 text-sm mb-3 break-words">
              {pricing.love_bundle.description} + расклад на отношения со скидкой{' '}
              {pricing.love_bundle.savings_percent}%
            </p>
            <Button onClick={buyLoveBundle} disabled={buyingBundle}>
              {buyingBundle
                ? 'Оплата...'
                : `Купить за ${applyDiscount(pricing.love_bundle.original_stars, pricing.love_bundle.savings_percent)} ⭐`}
            </Button>
          </GlassCard>
        )}

        <GlassCard className="space-y-4 min-w-0">
          <div className="min-w-0">
            <label className="text-white/50 text-sm block mb-1">Имя партнёра</label>
            <input
              className="w-full min-w-0 bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white outline-none focus:border-tarot-gold/50"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              placeholder="Анна"
            />
          </div>
          <div className="min-w-0">
            <label className="text-white/50 text-sm block mb-1">Дата рождения</label>
            <input
              type="date"
              className="w-full min-w-0 bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white outline-none focus:border-tarot-gold/50"
              value={form.birth_date}
              onChange={(e) => setForm({ ...form, birth_date: e.target.value })}
            />
          </div>
          <div className="min-w-0">
            <label className="text-white/50 text-sm block mb-1">Время рождения (необязательно)</label>
            <input
              type="time"
              className="w-full min-w-0 bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white outline-none focus:border-tarot-gold/50"
              value={form.birth_time}
              onChange={(e) => setForm({ ...form, birth_time: e.target.value })}
            />
          </div>
          <div className="min-w-0">
            <label className="text-white/50 text-sm block mb-1">Город рождения</label>
            <input
              className="w-full min-w-0 bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white outline-none focus:border-tarot-gold/50"
              value={form.birth_city}
              onChange={(e) => setForm({ ...form, birth_city: e.target.value })}
              placeholder="Москва"
            />
          </div>
        </GlassCard>

        {mutation.isError && (
          <p className="text-red-300/80 text-sm text-center">
            {String(mutation.error?.message || 'Заполните анкету и данные партнёра')}
          </p>
        )}

        <Button
          onClick={submit}
          disabled={mutation.isPending || buying || !form.name || !form.birth_date}
        >
          {mutation.isPending
            ? 'Считаем...'
            : buying
              ? 'Оплата...'
              : hasCompatAccess
                ? 'Рассчитать пару'
                : `Купить за ${compatDisplayPrice} ⭐`}
        </Button>
      </div>
    </div>
  )
}
