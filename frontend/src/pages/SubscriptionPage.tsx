import { useState } from 'react'
import { motion } from 'framer-motion'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '@/api/client'
import { useAppStore } from '@/store/appStore'
import { GlassCard, Skeleton } from '@/components/ui'
import { haptic, shareText } from '@/lib/telegram'

const PLAN_LABELS: Record<string, string> = {
  month_1: '1 месяц',
  month_3: '3 месяца',
  month_6: '6 месяцев',
}

type Feedback = { kind: 'success' | 'error' | 'info'; text: string } | null

function formatNextDate(iso: string | null): string | null {
  if (!iso) return null
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return null
  return d.toLocaleDateString('ru-RU', { day: 'numeric', month: 'long' })
}

export function SubscriptionPage() {
  const { isReturning, lastCategory, setAuth } = useAppStore()
  const queryClient = useQueryClient()
  const [busy, setBusy] = useState<string | null>(null)
  const [feedback, setFeedback] = useState<Feedback>(null)
  const { data: pricing, isLoading } = useQuery({
    queryKey: ['pricing'],
    queryFn: api.getPricing,
  })
  const { data: limits } = useQuery({
    queryKey: ['limits'],
    queryFn: api.getLimits,
  })
  const { data: referral } = useQuery({
    queryKey: ['referral'],
    queryFn: api.getReferral,
  })

  const limitReached = !!limits && !limits.can_spread && !limits.is_premium
  const nextDate = formatNextDate(limits?.next_available_at ?? null)

  const copyReferralLink = async () => {
    if (!referral?.link) return
    haptic('light')
    try {
      await navigator.clipboard.writeText(referral.link)
      haptic('success')
      setFeedback({ kind: 'success', text: 'Ссылка скопирована! Отправьте её другу.' })
    } catch {
      setFeedback({ kind: 'error', text: 'Не удалось скопировать ссылку.' })
    }
  }

  const shareReferralLink = async () => {
    if (!referral?.link) return
    haptic('medium')
    const text = `🔮 Присоединяйся к Миру Таро!\n\n${referral.link}\n\nЗарегистрируйся по ссылке — и мы оба получим бесплатный расклад в подарок.`
    const copied = await shareText(text)
    if (copied === 'copied') haptic('success')
    else setFeedback({ kind: 'error', text: 'Не удалось скопировать ссылку.' })
  }

  const handlePurchase = async (type: string, plan?: string) => {
    if (busy) return
    haptic('medium')
    setFeedback(null)
    const key = plan || type
    setBusy(key)
    try {
      const payment = await api.createPayment(type, plan)
      const tg = window.Telegram?.WebApp

      if (!tg?.openInvoice || !payment.invoice_link) {
        setFeedback({
          kind: 'info',
          text: 'Оплата звёздами доступна только внутри Telegram. Откройте приложение через бота.',
        })
        return
      }

      tg.openInvoice(payment.invoice_link, (status: string) => {
        if (status === 'paid') {
          haptic('success')
          if (type === 'subscription') {
            setAuth(true, isReturning, lastCategory)
          }
          queryClient.invalidateQueries({ queryKey: ['limits'] })
          setFeedback({
            kind: 'success',
            text:
              type === 'subscription'
                ? '✅ Подписка активирована! Открыт полный доступ.'
                : '✅ Оплата прошла! Дополнительный расклад добавлен. Можно вернуться назад и сделать расклад.',
          })
        } else if (status === 'failed') {
          haptic('error')
          setFeedback({ kind: 'error', text: 'Оплата не прошла. Попробуйте ещё раз.' })
        } else if (status === 'cancelled') {
          setFeedback({ kind: 'info', text: 'Оплата отменена.' })
        }
      })
    } catch (e) {
      haptic('error')
      console.error(e)
      setFeedback({
        kind: 'error',
        text: 'Не удалось создать счёт. Проверьте связь и попробуйте снова.',
      })
    } finally {
      setBusy(null)
    }
  }

  return (
    <div className="min-h-screen gradient-bg px-4 pt-20 pb-8">
      <h1 className="text-2xl font-display font-bold mb-6 max-w-lg mx-auto">Premium</h1>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="max-w-lg mx-auto space-y-4"
      >
        {limitReached && (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            className="rounded-2xl px-4 py-4 border border-tarot-gold/40 bg-tarot-gold/10 text-white"
          >
            <p className="font-semibold mb-1">✨ Бесплатный расклад уже использован</p>
            <p className="text-sm text-white/70">
              Бесплатный расклад доступен раз в {limits?.period_days ?? 3} дня.
              {nextDate ? ` Следующий бесплатный — ${nextDate}.` : ''} Чтобы сделать
              расклад прямо сейчас, оформите подписку или купите разовый расклад за звёзды.
            </p>
          </motion.div>
        )}

        <GlassCard className="border-emerald-400/30">
          <div className="flex items-start gap-3">
            <span className="text-3xl">🎁</span>
            <div className="flex-1 min-w-0">
              <h2 className="text-lg font-bold">Пригласи друга</h2>
              <p className="text-white/60 text-sm mt-1">
                За каждого друга — бесплатный расклад вам обоим. Друг должен перейти по
                ссылке и впервые открыть приложение.
              </p>
              {referral && (
                <p className="text-emerald-300/90 text-sm mt-2">
                  Приглашено: {referral.invites_count} • Бонусных раскладов: {referral.bonus_earned}
                  {(limits?.bonus_spreads ?? 0) > 0
                    ? ` • Доступно сейчас: ${limits?.bonus_spreads}`
                    : ''}
                </p>
              )}
              <div className="flex flex-wrap gap-2 mt-4">
                <button
                  type="button"
                  onClick={shareReferralLink}
                  disabled={!referral?.link}
                  className="px-4 py-2 rounded-xl bg-emerald-500/20 border border-emerald-400/30
                             text-emerald-200 text-sm font-medium active:scale-95 transition"
                >
                  Поделиться
                </button>
                <button
                  type="button"
                  onClick={copyReferralLink}
                  disabled={!referral?.link}
                  className="px-4 py-2 rounded-xl bg-white/10 border border-white/15
                             text-white/90 text-sm font-medium active:scale-95 transition"
                >
                  Копировать ссылку
                </button>
              </div>
            </div>
          </div>
        </GlassCard>

        {feedback && (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            className={`rounded-2xl px-4 py-3 text-sm border ${
              feedback.kind === 'success'
                ? 'border-emerald-400/30 bg-emerald-500/10 text-emerald-200'
                : feedback.kind === 'error'
                  ? 'border-red-400/30 bg-red-500/10 text-red-200'
                  : 'border-white/20 bg-white/5 text-white/70'
            }`}
          >
            {feedback.text}
          </motion.div>
        )}

        <GlassCard className="text-center border-tarot-gold/30">
          <span className="text-4xl">⭐️</span>
          <h2 className="text-xl font-bold mt-2">Полный доступ</h2>
          <p className="text-white/60 text-sm mt-1">15 раскладов в сутки • Вся история</p>
        </GlassCard>

        {isLoading
          ? Array.from({ length: 3 }).map((_, i) => (
              <Skeleton key={i} className="h-20 w-full rounded-2xl" />
            ))
          : pricing?.plans.map((plan, i) => (
              <motion.div
                key={plan.plan}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.1 }}
              >
                <GlassCard
                  onClick={() => handlePurchase('subscription', plan.plan)}
                  className="flex items-center justify-between"
                >
                  <div>
                    <p className="font-semibold text-lg">{PLAN_LABELS[plan.plan]}</p>
                    <p className="text-white/50 text-sm">
                      {plan.features.join(' • ')}
                    </p>
                  </div>
                  <span className="text-tarot-gold font-bold text-xl">
                    {plan.stars} ⭐️
                  </span>
                </GlassCard>
              </motion.div>
            ))}

        <GlassCard
          onClick={() => handlePurchase('single_spread')}
          className="flex items-center justify-between"
        >
          <div>
            <p className="font-semibold">Разовый расклад</p>
            <p className="text-white/50 text-sm">+1 расклад к лимиту</p>
          </div>
          <span className="text-tarot-gold font-bold">
            {pricing?.single_spread ?? 150} ⭐️
          </span>
        </GlassCard>
      </motion.div>
    </div>
  )
}
