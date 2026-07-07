import type { Limits } from '@/api/client'
import { applyDiscount, getStoredPromoPercent } from '@/lib/promo'

export function getSingleSpreadCheckoutPrice(
  limits: Limits | undefined,
  basePrice: number,
): { base: number; final: number; discountPercent: number; hasDiscount: boolean } {
  const promoPercent = getStoredPromoPercent()
  const firstPaidPercent = limits?.first_paid_discount_eligible
    ? limits.first_paid_discount_percent ?? 30
    : 0

  let discountPercent = 0
  if (promoPercent > 0) {
    discountPercent = promoPercent
  } else if (firstPaidPercent > 0) {
    discountPercent = firstPaidPercent
  }

  const final =
    !promoPercent && limits?.first_paid_discounted_price != null && firstPaidPercent > 0
      ? limits.first_paid_discounted_price
      : applyDiscount(basePrice, discountPercent)

  return {
    base: basePrice,
    final,
    discountPercent,
    hasDiscount: discountPercent > 0 && final < basePrice,
  }
}
