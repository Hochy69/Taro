import { useQueryClient } from '@tanstack/react-query'
import { api, type Limits } from '@/api/client'
import { getStoredPromoCode, clearStoredPromo } from '@/lib/promo'
import { haptic } from '@/lib/telegram'

const POLL_ATTEMPTS = 16
const POLL_INTERVAL_MS = 750

function isActivated(
  paymentType: string,
  limits: Limits,
  before: Limits | null,
): boolean {
  if (limits.is_admin) return true

  if (paymentType === 'subscription') {
    return limits.is_premium
  }

  if (paymentType === 'compatibility') {
    return limits.is_premium || limits.compatibility_credits > (before?.compatibility_credits ?? 0)
  }

  if (paymentType === 'love_bundle') {
    return (
      limits.is_premium
      || limits.compatibility_credits > (before?.compatibility_credits ?? 0)
      || limits.bonus_spreads > (before?.bonus_spreads ?? 0)
    )
  }

  if (paymentType === 'spread_pack_3' || paymentType === 'spread_pack_5' || paymentType === 'single_spread') {
    return limits.bonus_spreads > (before?.bonus_spreads ?? 0) || limits.is_premium
  }

  return true
}

async function waitForPaymentActivation(
  paymentType: string,
  before: Limits | null,
): Promise<boolean> {
  for (let attempt = 0; attempt < POLL_ATTEMPTS; attempt += 1) {
    await new Promise((resolve) => setTimeout(resolve, POLL_INTERVAL_MS))
    try {
      const limits = await api.getLimits()
      if (isActivated(paymentType, limits, before)) {
        return true
      }
    } catch {
      // Backend may still be confirming the Stars payment via the bot.
    }
  }
  return false
}

export async function openStarsPayment(
  paymentType: string,
  options?: {
    plan?: string
    onPaid?: () => void
    onError?: (message: string) => void
  },
): Promise<'paid' | 'free' | 'cancelled' | 'failed' | 'unavailable'> {
  const beforeLimits = await api.getLimits().catch(() => null)
  const promoCode = getStoredPromoCode() ?? undefined
  const payment = await api.createPayment(paymentType, options?.plan, promoCode)

  if (payment.free || payment.status === 'completed') {
    haptic('success')
    if (payment.promo_code) clearStoredPromo()
    options?.onPaid?.()
    return 'free'
  }

  const tg = window.Telegram?.WebApp
  if (!tg?.openInvoice || !payment.invoice_link) {
    options?.onError?.('Оплата звёздами доступна только внутри Telegram.')
    return 'unavailable'
  }

  return new Promise((resolve) => {
    tg.openInvoice!(payment.invoice_link!, (status: string) => {
      void (async () => {
        if (status === 'paid') {
          haptic('success')
          const activated = await waitForPaymentActivation(paymentType, beforeLimits)
          if (activated) {
            if (payment.promo_code) clearStoredPromo()
            options?.onPaid?.()
            resolve('paid')
            return
          }
          options?.onError?.(
            'Оплата принята Telegram. Доступ активируется в течение минуты — обновите экран.',
          )
          resolve('failed')
        } else if (status === 'failed') {
          haptic('error')
          resolve('failed')
        } else {
          resolve('cancelled')
        }
      })()
    })
  })
}

export function useInvalidateAfterPayment() {
  const queryClient = useQueryClient()
  return () => {
    queryClient.invalidateQueries({ queryKey: ['limits'] })
  }
}
