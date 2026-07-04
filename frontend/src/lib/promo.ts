const PROMO_KEY = 'tarot_promo_code'
const PROMO_PERCENT_KEY = 'tarot_promo_percent'

export function getStoredPromoCode(): string | null {
  return sessionStorage.getItem(PROMO_KEY)
}

export function getStoredPromoPercent(): number {
  const raw = sessionStorage.getItem(PROMO_PERCENT_KEY)
  if (!raw) return 0
  const n = Number(raw)
  return Number.isFinite(n) ? n : 0
}

export function setStoredPromo(code: string, discountPercent: number) {
  sessionStorage.setItem(PROMO_KEY, code)
  sessionStorage.setItem(PROMO_PERCENT_KEY, String(discountPercent))
}

export function clearStoredPromo() {
  sessionStorage.removeItem(PROMO_KEY)
  sessionStorage.removeItem(PROMO_PERCENT_KEY)
}

export function applyDiscount(price: number, discountPercent: number): number {
  if (discountPercent >= 100) return 0
  if (discountPercent <= 0) return price
  return Math.max(1, Math.round((price * (100 - discountPercent)) / 100))
}

export function formatPrice(price: number, discountPercent: number): string {
  const final = applyDiscount(price, discountPercent)
  if (discountPercent > 0 && final < price) {
    return `${final} ⭐`
  }
  return `${price} ⭐`
}
