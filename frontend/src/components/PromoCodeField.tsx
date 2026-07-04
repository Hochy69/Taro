import { useState } from 'react'
import { api } from '@/api/client'
import { clearStoredPromo, getStoredPromoCode, setStoredPromo } from '@/lib/promo'
import { haptic } from '@/lib/telegram'

interface PromoCodeFieldProps {
  onApplied?: (discountPercent: number) => void
  onCleared?: () => void
}

export function PromoCodeField({ onApplied, onCleared }: PromoCodeFieldProps) {
  const [input, setInput] = useState(getStoredPromoCode() ?? '')
  const [applied, setApplied] = useState(!!getStoredPromoCode())
  const [discount, setDiscount] = useState<number | null>(
    getStoredPromoCode() ? Number(sessionStorage.getItem('tarot_promo_percent')) || null : null,
  )
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const apply = async () => {
    const code = input.trim()
    if (!code) return
    setBusy(true)
    setError('')
    try {
      const result = await api.validatePromo(code)
      setStoredPromo(result.code, result.discount_percent)
      setApplied(true)
      setDiscount(result.discount_percent)
      haptic('success')
      onApplied?.(result.discount_percent)
    } catch (e) {
      haptic('error')
      setError(e instanceof Error ? e.message : 'Промокод недействителен')
      setApplied(false)
      setDiscount(null)
      clearStoredPromo()
      onCleared?.()
    } finally {
      setBusy(false)
    }
  }

  const clear = () => {
    setInput('')
    setApplied(false)
    setDiscount(null)
    setError('')
    clearStoredPromo()
    onCleared?.()
  }

  return (
    <div className="space-y-2">
      <p className="text-white/50 text-sm">Промокод</p>
      <div className="flex gap-2 min-w-0">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value.toUpperCase())}
          placeholder="Введите промокод"
          className="flex-1 min-w-0 px-4 py-2.5 rounded-xl bg-white/5 border border-white/10 text-white text-sm outline-none focus:border-tarot-gold/50 uppercase"
        />
        {applied ? (
          <button
            type="button"
            onClick={clear}
            className="px-4 py-2.5 rounded-xl bg-white/10 text-white/80 text-sm"
          >
            Сброс
          </button>
        ) : (
          <button
            type="button"
            onClick={apply}
            disabled={busy || !input.trim()}
            className="px-4 py-2.5 rounded-xl bg-tarot-gold/20 border border-tarot-gold/30 text-tarot-gold text-sm font-medium disabled:opacity-50"
          >
            {busy ? '…' : 'Применить'}
          </button>
        )}
      </div>
      {applied && discount !== null && (
        <p className="text-emerald-300/90 text-sm">Скидка {discount}% применена</p>
      )}
      {error && <p className="text-red-300/80 text-sm">{error}</p>}
    </div>
  )
}
