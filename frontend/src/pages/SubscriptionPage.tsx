import { useEffect, useRef, useState, type ReactNode } from 'react'

import { motion } from 'framer-motion'

import { useQuery, useQueryClient } from '@tanstack/react-query'

import { useLocation } from 'react-router-dom'

import { api, type LoveBundle, type ReferralMilestone, type SpreadPack } from '@/api/client'

import { useAppStore } from '@/store/appStore'

import { GlassCard, Skeleton } from '@/components/ui'

import { PromoCodeField } from '@/components/PromoCodeField'

import { applyDiscount, getStoredPromoPercent } from '@/lib/promo'

import { openStarsPayment } from '@/lib/payments'

import { haptic, shareContent, shareText } from '@/lib/telegram'



const PLAN_LABELS: Record<string, string> = {

  month_1: '1 месяц',

  month_3: '3 месяца',

  month_6: '6 месяцев',

}



const DEFAULT_SPREAD_PACKS: SpreadPack[] = [

  { pack: 'spread_pack_3', stars: 249, spreads: 3, savings_percent: 45, label: '3 расклада' },

  { pack: 'spread_pack_5', stars: 399, spreads: 5, savings_percent: 47, label: '5 раскладов' },

]



const DEFAULT_LOVE_BUNDLE: LoveBundle = {

  stars: 134,

  original_stars: 168,

  savings_percent: 20,

  description: 'Совместимость + расклад на любовь',

}



const DEFAULT_MILESTONES: Omit<ReferralMilestone, 'reached'>[] = [

  { invites_required: 1, reward: '1 бесплатный расклад' },

  { invites_required: 3, reward: 'Проверка совместимости' },

  { invites_required: 5, reward: 'Premium на 3 дня' },

]



type Feedback = { kind: 'success' | 'error' | 'info'; text: string } | null



function SectionTitle({ children }: { children: ReactNode }) {

  return (

    <h2 className="text-sm font-semibold text-tarot-gold uppercase tracking-wide px-1 pt-2">

      {children}

    </h2>

  )

}



function formatNextDate(iso: string | null): string | null {

  if (!iso) return null

  const d = new Date(iso)

  if (Number.isNaN(d.getTime())) return null

  return d.toLocaleDateString('ru-RU', { day: 'numeric', month: 'long' })

}



export function SubscriptionPage() {

  const { isReturning, lastCategory, setAuth } = useAppStore()

  const location = useLocation()

  const referralSectionRef = useRef<HTMLElement>(null)

  const queryClient = useQueryClient()

  const [busy, setBusy] = useState<string | null>(null)

  const [feedback, setFeedback] = useState<Feedback>(null)

  const [promoPercent, setPromoPercent] = useState(getStoredPromoPercent())

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

  const { data: preferences } = useQuery({

    queryKey: ['preferences'],

    queryFn: api.getPreferences,

  })



  const toggleCardPush = async () => {

    if (!preferences) return

    haptic('light')

    const next = !preferences.daily_card_push

    await api.updatePreferences({ daily_card_push: next })

    queryClient.setQueryData(['preferences'], { daily_card_push: next })

    setFeedback({

      kind: 'success',

      text: next ? 'Карта дня будет приходить в 9:00' : 'Утренние уведомления отключены',

    })

  }



  const limitReached = !!limits && !limits.can_spread && !limits.is_premium

  const nextDate = formatNextDate(limits?.next_available_at ?? null)
  const premiumExpires = formatNextDate(limits?.subscription_expires_at ?? null)
  const premiumPlanLabel = limits?.subscription_plan
    ? PLAN_LABELS[limits.subscription_plan] ?? limits.subscription_plan
    : null



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
    const text =
      '🔮 Присоединяйся к Миру Таро!\n\nЗарегистрируйся по моей ссылке — мы оба получим бесплатный расклад в подарок.'
    const result = await shareContent(text, { url: referral.link })
    if (result === 'picker') {
      haptic('success')
      return
    }
    if (result === 'copied') {
      setFeedback({
        kind: 'info',
        text: 'Не удалось открыть выбор чата. Текст со ссылкой скопирован — вставьте вручную.',
      })
      return
    }
    setFeedback({ kind: 'error', text: 'Не удалось поделиться. Попробуйте ещё раз.' })
  }



  const handlePurchase = async (type: string, plan?: string) => {

    if (busy) return

    haptic('medium')

    setFeedback(null)

    const key = plan || type

    setBusy(key)

    try {

      const result = await openStarsPayment(type, {

        plan,

        onError: (text) => setFeedback({ kind: 'info', text }),

      })

      if (result === 'paid' || result === 'free') {

        if (type === 'subscription') {
          const me = await api.getMe()
          setAuth(me.is_premium, isReturning, lastCategory)
        }

        queryClient.invalidateQueries({ queryKey: ['limits'] })

        queryClient.invalidateQueries({ queryKey: ['referral'] })

        const successText: Record<string, string> = {

          subscription: '✅ Подписка активирована! Открыт полный доступ.',

          compatibility: '✅ Проверка на пару доступна на главном экране.',

          love_bundle: '✅ Пакет «Любовь» активирован!',

          spread_pack_3: '✅ Пакет из 3 раскладов добавлен.',

          spread_pack_5: '✅ Пакет из 5 раскладов добавлен.',

        }

        setFeedback({

          kind: 'success',

          text:

            result === 'free'

              ? '✅ Оплата прошла! Доступ активирован.'

              : successText[type] ?? '✅ Оплата прошла! Расклад добавлен.',

        })

      } else if (result === 'failed') {

        setFeedback({ kind: 'error', text: 'Оплата не прошла. Попробуйте ещё раз.' })

      } else if (result === 'cancelled') {

        setFeedback({ kind: 'info', text: 'Оплата отменена.' })

      }

    } catch (e) {

      haptic('error')

      console.error(e)

      setFeedback({

        kind: 'error',

        text: e instanceof Error ? e.message : 'Не удалось создать счёт.',

      })

    } finally {

      setBusy(null)

    }

  }



  const renderPrice = (base: number, extraDiscount = 0) => {

    const totalDiscount = Math.max(promoPercent, extraDiscount)

    const final = applyDiscount(base, totalDiscount)

    if (totalDiscount > 0 && final < base) {

      return (

        <span className="text-right shrink-0">

          <span className="block text-white/40 text-sm line-through">{base} ⭐</span>

          <span className="text-tarot-gold font-bold text-xl">{final} ⭐</span>

        </span>

      )

    }

    return <span className="text-tarot-gold font-bold text-xl shrink-0">{base} ⭐</span>

  }



  const singleBase = pricing?.single_spread ?? 69

  const compatBase = pricing?.compatibility ?? 99

  const firstPaidEligible = limits?.first_paid_discount_eligible ?? false

  const firstPaidPercent = limits?.first_paid_discount_percent ?? pricing?.first_paid_discount_percent ?? 30

  const perDayStars = pricing?.subscription_per_day_stars ?? Math.round((pricing?.plans?.[0]?.stars ?? 450) / 30)

  const spreadPacks = pricing?.spread_packs?.length ? pricing.spread_packs : DEFAULT_SPREAD_PACKS

  const loveBundle = pricing?.love_bundle ?? DEFAULT_LOVE_BUNDLE

  const invitesCount = referral?.invites_count ?? 0

  const milestones: ReferralMilestone[] =

    referral?.milestones?.length

      ? referral.milestones

      : DEFAULT_MILESTONES.map((m) => ({

          ...m,

          reached: invitesCount >= m.invites_required,

        }))

  const nextMilestone =

    referral?.next_milestone ??

    milestones.find((m) => !m.reached) ??

    null

  const isReferralFocus = location.hash === '#referral'

  useEffect(() => {
    if (!isReferralFocus) return
    const scrollToReferral = () => {
      referralSectionRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
    const timer = window.setTimeout(scrollToReferral, 80)
    return () => window.clearTimeout(timer)
  }, [isReferralFocus, isLoading, referral])

  return (

    <div className="page-shell pb-12">

      <h1 className="text-2xl font-display font-bold mb-2 max-w-lg mx-auto">
        {isReferralFocus ? 'Пригласи друга' : 'Premium'}
      </h1>

      <p className="text-white/50 text-sm mb-6 max-w-lg mx-auto">
        {isReferralFocus
          ? 'Приглашайте друзей и получайте награды'
          : 'Пакеты, подписки и разовые покупки'}
      </p>



      <motion.div

        initial={{ opacity: 0, y: 20 }}

        animate={{ opacity: 1, y: 0 }}

        className="max-w-lg mx-auto space-y-4 w-full min-w-0"

      >

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



        <SectionTitle>🎁 Акции</SectionTitle>



        {firstPaidEligible && (

          <motion.div className="rounded-2xl px-4 py-4 border border-amber-400/40 bg-amber-500/10 text-white">

            <p className="font-semibold mb-1">−{firstPaidPercent}% на первый платный расклад</p>

            <p className="text-sm text-white/70 mb-3">

              Вы сделали {limits?.completed_spreads ?? 2}+ расклада — следующий за{' '}

              {limits?.first_paid_discounted_price ?? applyDiscount(singleBase, firstPaidPercent)} ⭐

              вместо {singleBase} ⭐

            </p>

            <button

              type="button"

              disabled={!!busy}

              onClick={() => handlePurchase('single_spread')}

              className="w-full py-3 rounded-xl bg-tarot-gold/20 border border-tarot-gold/40 text-tarot-gold font-semibold active:scale-[0.98]"

            >

              {busy === 'single_spread' ? 'Оплата...' : 'Купить со скидкой'}

            </button>

          </motion.div>

        )}



        {limitReached && (

          <div className="rounded-2xl px-4 py-4 border border-tarot-gold/40 bg-tarot-gold/10 text-white">

            <p className="font-semibold mb-1">✨ Бесплатный расклад использован</p>

            <p className="text-sm text-white/70">

              Следующий бесплатный через {limits?.period_days ?? 3} дн.

              {nextDate ? ` (${nextDate})` : ''}. Купите пакет или подписку ниже.

            </p>

          </div>

        )}



        <GlassCard>

          <PromoCodeField onApplied={setPromoPercent} onCleared={() => setPromoPercent(0)} />

        </GlassCard>



        <SectionTitle>📦 Пакеты раскладов</SectionTitle>



        {spreadPacks.map((pack) => (

          <GlassCard

            key={pack.pack}

            onClick={busy ? undefined : () => handlePurchase(pack.pack)}

            className={`flex items-center justify-between gap-3 min-w-0 border-emerald-400/30 ${

              busy === pack.pack ? 'opacity-60' : ''

            }`}

          >

            <div className="min-w-0 flex-1">

              <p className="font-semibold text-lg">📦 {pack.label}</p>

              <p className="text-white/50 text-sm">

                +{pack.spreads} расклада к лимиту • экономия {pack.savings_percent}%

              </p>

            </div>

            {renderPrice(pack.stars)}

          </GlassCard>

        ))}



        <SectionTitle>💕 Для отношений</SectionTitle>



        <GlassCard

          onClick={busy ? undefined : () => handlePurchase('compatibility')}

          className={`flex items-center justify-between gap-3 min-w-0 border-pink-400/20 ${

            busy === 'compatibility' ? 'opacity-60' : ''

          }`}

        >

          <div className="min-w-0 flex-1">

            <p className="font-semibold">💕 Проверка на пару</p>

            <p className="text-white/50 text-sm break-words">

              Солнце и Луна двух карт — узнайте до важного разговора

            </p>

          </div>

          {renderPrice(compatBase)}

        </GlassCard>



        <GlassCard

          onClick={busy ? undefined : () => handlePurchase('love_bundle')}

          className={`flex items-center justify-between gap-3 min-w-0 border-pink-400/30 ${

            busy === 'love_bundle' ? 'opacity-60' : ''

          }`}

        >

          <div className="min-w-0 flex-1">

            <p className="font-semibold">💞 Пакет «Любовь»</p>

            <p className="text-white/50 text-sm break-words">

              {loveBundle.description} • −{loveBundle.savings_percent}%

            </p>

          </div>

          {renderPrice(

            loveBundle.original_stars,

            promoPercent > 0 ? 0 : loveBundle.savings_percent,

          )}

        </GlassCard>



        <SectionTitle>🃏 Разовые покупки</SectionTitle>



        <GlassCard

          onClick={busy ? undefined : () => handlePurchase('single_spread')}

          className={`flex items-center justify-between gap-3 min-w-0 ${

            busy === 'single_spread' ? 'opacity-60' : ''

          }`}

        >

          <div className="min-w-0 flex-1">

            <p className="font-semibold">1 расклад</p>

            <p className="text-white/50 text-sm">

              +1 к лимиту

              {firstPaidEligible ? ` • −${firstPaidPercent}% сейчас` : ''}

            </p>

          </div>

          {renderPrice(singleBase, firstPaidEligible && promoPercent === 0 ? firstPaidPercent : 0)}

        </GlassCard>



        <GlassCard className="border-tarot-gold/20">

          <p className="text-tarot-gold text-sm font-semibold mb-3">Сравнение</p>

          <div className="space-y-2 text-sm">

            <div className="flex justify-between gap-3 text-white/70">

              <span>1 расклад</span>

              <span>{singleBase} ⭐</span>

            </div>

            <div className="flex justify-between gap-3 text-white/90">

              <span>3 расклада (пакет)</span>

              <span className="text-emerald-300">{spreadPacks[0]?.stars} ⭐</span>

            </div>

            <div className="flex justify-between gap-3 text-white/90">

              <span>Premium 1 мес</span>

              <span className="text-tarot-gold">≈{perDayStars} ⭐/день</span>

            </div>

          </div>

        </GlassCard>



        <SectionTitle>⭐️ Подписки Premium</SectionTitle>



        {limits?.is_premium && premiumExpires && (
          <div className="rounded-2xl px-4 py-4 border border-emerald-400/40 bg-emerald-500/10 text-white">
            <p className="font-semibold mb-1">✅ Premium активен</p>
            <p className="text-sm text-white/70">
              {premiumPlanLabel ? `Тариф: ${premiumPlanLabel}. ` : ''}
              Действует до {premiumExpires}. Продление добавит дни к текущему сроку.
            </p>
          </div>
        )}



        <GlassCard className="text-center border-tarot-gold/30 py-5">

          <span className="text-4xl">⭐️</span>

          <h2 className="text-xl font-bold mt-2">Полный доступ</h2>

          <p className="text-white/60 text-sm mt-1">15 раскладов в сутки • Вся история • Проверка на пару бесплатно</p>

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

                transition={{ delay: i * 0.05 }}

              >

                <GlassCard

                  onClick={busy ? undefined : () => handlePurchase('subscription', plan.plan)}

                  className={`flex items-center justify-between gap-3 min-w-0 relative ${

                    busy === plan.plan ? 'opacity-60' : ''

                  }`}

                >

                  {plan.plan === 'month_6' && (

                    <span className="absolute -top-2 right-3 text-[10px] px-2 py-0.5 rounded-full bg-tarot-gold text-tarot-dark font-bold">

                      ВЫГОДНО

                    </span>

                  )}

                  {plan.plan === 'month_3' && (
                    <span className="absolute -top-2 right-3 text-[10px] px-2 py-0.5 rounded-full bg-white/15 text-white/80">
                      ≈{Math.round(plan.stars / plan.duration_days)} ⭐/день
                    </span>
                  )}

                  {plan.plan === 'month_1' && (

                    <span className="absolute -top-2 right-3 text-[10px] px-2 py-0.5 rounded-full bg-white/15 text-white/80">

                      ≈{perDayStars} ⭐/день

                    </span>

                  )}

                  <div className="min-w-0 flex-1">

                    <p className="font-semibold text-lg">{PLAN_LABELS[plan.plan]}</p>

                    <p className="text-white/50 text-sm break-words">{plan.features.join(' • ')}</p>

                  </div>

                  {renderPrice(plan.stars)}

                </GlassCard>

              </motion.div>

            ))}



        <section id="referral" ref={referralSectionRef} className="scroll-mt-20 space-y-4">
        <SectionTitle>🎁 Пригласи друга</SectionTitle>



        <GlassCard className="border-emerald-400/30">

          <div className="flex items-start gap-3">

            <span className="text-3xl">🎁</span>

            <div className="flex-1 min-w-0">

              <h2 className="text-lg font-bold">Реферальная программа</h2>

              <p className="text-white/60 text-sm mt-1">За каждого друга — расклад вам обоим. Лестница наград:</p>

              <ul className="mt-3 space-y-1.5">

                {milestones.map((m) => (

                  <li

                    key={m.invites_required}

                    className={`text-sm flex items-center gap-2 ${

                      m.reached ? 'text-emerald-300/90' : 'text-white/50'

                    }`}

                  >

                    <span>{m.reached ? '✅' : '○'}</span>

                    <span>

                      {m.invites_required} {m.invites_required === 1 ? 'друг' : 'друга'} — {m.reward}

                    </span>

                  </li>

                ))}

              </ul>

              {nextMilestone && (

                <p className="text-amber-200/90 text-sm mt-2">

                  До награды: {nextMilestone.invites_required - invitesCount}{' '}

                  {nextMilestone.invites_required - invitesCount === 1 ? 'друг' : 'друга'} → {nextMilestone.reward}

                </p>

              )}

              <p className="text-emerald-300/90 text-sm mt-2">

                Приглашено: {invitesCount}

                {(limits?.bonus_spreads ?? 0) > 0 ? ` • Доступно: ${limits?.bonus_spreads} раскл.` : ''}

              </p>

              <div className="flex flex-wrap gap-2 mt-4">

                <button

                  type="button"

                  onClick={shareReferralLink}

                  disabled={!referral?.link}

                  className="px-4 py-2 rounded-xl bg-emerald-500/20 border border-emerald-400/30 text-emerald-200 text-sm font-medium"

                >

                  Поделиться

                </button>

                <button

                  type="button"

                  onClick={copyReferralLink}

                  disabled={!referral?.link}

                  className="px-4 py-2 rounded-xl bg-white/10 border border-white/15 text-white/90 text-sm font-medium"

                >

                  Копировать

                </button>

              </div>

            </div>

          </div>

        </GlassCard>

        </section>



        <SectionTitle>🔔 Уведомления</SectionTitle>



        <GlassCard className="flex items-center justify-between gap-3 min-w-0">

          <div className="min-w-0 flex-1">

            <p className="font-semibold">Карта дня в 9:00</p>

            <p className="text-white/50 text-sm">Push в боте + совет сделать расклад</p>

          </div>

          <button

            type="button"

            onClick={toggleCardPush}

            className={`w-12 h-7 rounded-full transition relative shrink-0 ${

              preferences?.daily_card_push !== false ? 'bg-tarot-gold' : 'bg-white/20'

            }`}

          >

            <span

              className={`absolute top-1 w-5 h-5 rounded-full bg-white transition ${

                preferences?.daily_card_push !== false ? 'left-6' : 'left-1'

              }`}

            />

          </button>

        </GlassCard>

      </motion.div>

    </div>

  )

}


