import { useState } from 'react'
import { motion } from 'framer-motion'
import { api } from '@/api/client'
import { useAppStore } from '@/store/appStore'
import { setAuthMeta, loadAuthMeta } from '@/api/client'
import { haptic } from '@/lib/telegram'

const SECTIONS: { title: string; body: string[] }[] = [
  {
    title: '1. Общие положения',
    body: [
      'Настоящее Пользовательское соглашение (публичная оферта) регулирует отношения между сервисом «Мир Таро» (далее — Сервис) и пользователем (далее — Пользователь) при использовании Telegram-приложения Сервиса.',
      'Начиная использовать Сервис, Пользователь подтверждает, что полностью прочитал, понял и безоговорочно принимает условия настоящего Соглашения.',
    ],
  },
  {
    title: '2. Характер услуг',
    body: [
      'Сервис предоставляет доступ к раскладам карт Таро и их интерпретациям исключительно в развлекательных и психологически-поддерживающих целях.',
      'Информация, получаемая через Сервис, не является профессиональной консультацией (медицинской, психологической, юридической или финансовой) и не гарантирует наступления каких-либо событий. Все решения Пользователь принимает самостоятельно и на свой риск.',
    ],
  },
  {
    title: '3. Возрастное ограничение',
    body: [
      'Сервис предназначен для лиц старше 18 лет. Используя Сервис, Пользователь подтверждает, что достиг совершеннолетия.',
    ],
  },
  {
    title: '4. Оплата и подписка',
    body: [
      'Отдельные функции Сервиса (подписка, дополнительные расклады) предоставляются на платной основе за Telegram Stars (XTR).',
      'Оплата производится через встроенные платёжные средства Telegram. Возврат средств осуществляется в соответствии с правилами Telegram и применимым законодательством.',
      'Бесплатный расклад доступен ограниченно (1 раз в 3 дня). Последующие расклады в этот период предоставляются платно.',
    ],
  },
  {
    title: '5. Обработка данных',
    body: [
      'Для работы Сервиса обрабатываются данные из вашего профиля Telegram, а также сведения, которые вы вводите добровольно (имя, дата рождения, описание ситуации).',
      'Данные используются только для формирования персональных раскладов и улучшения работы Сервиса и не передаются третьим лицам, кроме случаев, предусмотренных законом.',
    ],
  },
  {
    title: '6. Ответственность',
    body: [
      'Сервис не несёт ответственности за любые решения и действия Пользователя, принятые на основании полученных интерпретаций.',
      'Сервис предоставляется «как есть». Мы стремимся к бесперебойной работе, но не гарантируем отсутствие технических сбоев.',
    ],
  },
  {
    title: '7. Принятие условий',
    body: [
      'Нажимая кнопку «Принять и продолжить», Пользователь выражает своё полное и безоговорочное согласие с настоящим Соглашением. Без принятия условий доступ к функциям Сервиса не предоставляется.',
    ],
  },
]

export function TermsGate() {
  const { setTermsAccepted } = useAppStore()
  const [checked, setChecked] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleAccept = async () => {
    if (!checked || busy) return
    haptic('medium')
    setBusy(true)
    setError(null)
    try {
      await api.acceptTerms()
      const meta = loadAuthMeta()
      if (meta) {
        setAuthMeta({ ...meta, terms_accepted: true })
      }
      setTermsAccepted(true)
      haptic('success')
    } catch (e) {
      haptic('error')
      console.error(e)
      setError('Не удалось сохранить согласие. Проверьте связь и попробуйте ещё раз.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="fixed inset-0 z-[100] gradient-bg flex flex-col">
      <div className="px-5 pt-8 pb-4 text-center shrink-0">
        <div className="text-4xl mb-2">📜</div>
        <h1 className="text-xl font-display font-bold text-white">
          Пользовательское соглашение
        </h1>
        <p className="text-white/50 text-sm mt-1">
          Пожалуйста, ознакомьтесь и примите условия, чтобы продолжить
        </p>
      </div>

      <div className="flex-1 overflow-y-auto px-5 pb-4">
        <div className="max-w-lg mx-auto space-y-4">
          {SECTIONS.map((section) => (
            <div key={section.title} className="glass-card">
              <h3 className="font-semibold text-tarot-gold mb-2">{section.title}</h3>
              {section.body.map((p, i) => (
                <p key={i} className="text-white/75 text-sm leading-relaxed mb-2 last:mb-0">
                  {p}
                </p>
              ))}
            </div>
          ))}
        </div>
      </div>

      <div className="shrink-0 p-4 bg-gradient-to-t from-tarot-dark via-tarot-dark/95 to-transparent">
        <div className="max-w-lg mx-auto space-y-3">
          {error && (
            <p className="text-red-300 text-sm text-center">{error}</p>
          )}
          <label className="flex items-start gap-3 cursor-pointer select-none">
            <input
              type="checkbox"
              checked={checked}
              onChange={(e) => setChecked(e.target.checked)}
              className="mt-1 h-5 w-5 shrink-0 accent-tarot-gold"
            />
            <span className="text-white/80 text-sm">
              Мне исполнилось 18 лет, я прочитал(а) и принимаю условия Пользовательского
              соглашения (оферты).
            </span>
          </label>
          <motion.button
            whileTap={{ scale: 0.98 }}
            disabled={!checked || busy}
            onClick={handleAccept}
            className={`w-full py-4 rounded-2xl font-semibold transition ${
              checked && !busy
                ? 'bg-gradient-to-r from-tarot-gold to-yellow-400 text-tarot-dark'
                : 'bg-white/10 text-white/40 cursor-not-allowed'
            }`}
          >
            {busy ? 'Сохраняем…' : 'Принять и продолжить'}
          </motion.button>
        </div>
      </div>
    </div>
  )
}
