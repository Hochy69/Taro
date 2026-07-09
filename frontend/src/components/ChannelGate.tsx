import { useState } from 'react'
import { motion } from 'framer-motion'
import { api } from '@/api/client'
import { haptic, openTelegramLink } from '@/lib/telegram'

type Props = {
  channelUrl: string
  onVerified: () => void
}

export function ChannelGate({ channelUrl, onVerified }: Props) {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const openChannel = () => {
    haptic('light')
    openTelegramLink(channelUrl)
  }

  const checkSubscription = async () => {
    if (busy) return
    haptic('medium')
    setBusy(true)
    setError(null)
    try {
      const res = await api.getChannelSubscription()
      if (!res.required || res.subscribed) {
        haptic('success')
        onVerified()
        return
      }
      setError('Подписка не найдена. Подпишитесь на канал и нажмите «Я подписался» снова.')
    } catch {
      setError('Не удалось проверить подписку. Попробуйте ещё раз.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="min-h-screen gradient-bg flex items-center justify-center px-6 py-10">
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-md glass-card rounded-3xl p-6 text-center"
      >
        <div className="text-5xl mb-4">📢</div>
        <h1 className="text-xl font-bold mb-3">Подпишитесь на канал</h1>
        <p className="text-white/70 text-sm mb-6 leading-relaxed">
          Чтобы открыть расклады, подпишитесь на наш Telegram-канал — там карта дня, советы по
          отношениям и полезные материалы.
        </p>
        <div className="space-y-3">
          <button
            type="button"
            onClick={openChannel}
            className="w-full py-3 rounded-2xl bg-gradient-to-r from-tarot-gold to-yellow-400 text-tarot-dark font-semibold"
          >
            Подписаться на канал
          </button>
          <button
            type="button"
            onClick={checkSubscription}
            disabled={busy}
            className="w-full py-3 rounded-2xl bg-white/10 text-white font-semibold disabled:opacity-50"
          >
            {busy ? 'Проверяем…' : 'Я подписался'}
          </button>
        </div>
        {error && <p className="text-red-300 text-sm mt-4">{error}</p>}
      </motion.div>
    </div>
  )
}
