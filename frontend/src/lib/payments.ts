import { useQueryClient } from '@tanstack/react-query'
import { api } from '@/api/client'
import { getStoredPromoCode } from '@/lib/promo'
import { haptic } from '@/lib/telegram'

async function waitForPaymentActivation(): Promise<void> {
  for (let attempt = 0; attempt < 8; attempt += 1) {
    await new Promise((resolve) => setTimeout(resolve, 750))
    try {
      await api.getLimits()
      return
    } catch {
      // Backend may still be confirming the Stars payment.
    }
  }
}

export async function openStarsPayment(
  paymentType: string,
  options?: {
    plan?: string
    onPaid?: () => void
    onError?: (message: string) => void
  },
): Promise<'paid' | 'free' | 'cancelled' | 'failed' | 'unavailable'> {
  const promoCode = getStoredPromoCode() ?? undefined
  const payment = await api.createPayment(paymentType, options?.plan, promoCode)

  if (payment.free || payment.status === 'completed') {
    haptic('success')
    return 'free'
  }

  const tg = window.Telegram?.WebApp
  if (!tg?.openInvoice || !payment.invoice_link) {
    options?.onError?.('Оплата звёздами доступна только внутри Telegram.')
    return 'unavailable'
  }

  return new Promise((resolve) => {
    tg.openInvoice!(payment.invoice_link!, (status: string) => {
      if (status === 'paid') {
        haptic('success')
        void waitForPaymentActivation().then(() => {
          options?.onPaid?.()
        })
        resolve('paid')
      } else if (status === 'failed') {
        haptic('error')
        resolve('failed')
      } else {
        resolve('cancelled')
      }
    })
  })
}

export function useInvalidateAfterPayment() {
  const queryClient = useQueryClient()
  return () => {
    queryClient.invalidateQueries({ queryKey: ['limits'] })
  }
}
