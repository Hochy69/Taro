import { api } from '@/api/client'
import { setStoredPromo } from '@/lib/promo'

/** Silently apply promo from ?promo=CODE (not shown in the app UI). */
export async function tryApplyPromoFromUrl(): Promise<void> {
  const params = new URLSearchParams(window.location.search)
  const raw = params.get('promo')?.trim()
  if (!raw) return

  try {
    const result = await api.validatePromo(raw)
    setStoredPromo(result.code, result.discount_percent)
  } catch {
    // Invalid or exhausted — ignore without surfacing codes in the UI.
  }

  window.history.replaceState({}, '', window.location.pathname + window.location.hash)
}
