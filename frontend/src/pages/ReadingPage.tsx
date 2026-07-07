import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { useQuery } from '@tanstack/react-query'
import { useAppStore } from '@/store/appStore'
import { useAppNavigation } from '@/hooks/useAppNavigation'
import { Button, Skeleton } from '@/components/ui'
import { TarotCardVisual } from '@/components/tarot/TarotCardVisual'
import { api, type AIResult, type Spread, type SpreadCard } from '@/api/client'
import { haptic, shareContent } from '@/lib/telegram'

function buildShareText(spread: Spread, result: AIResult): string {
  const cards = spread.cards
    .map((c: SpreadCard) => `${c.name}${c.is_reversed ? ' (перев.)' : ''}`)
    .join(' • ')

  const lines = [
    '🔮 Мой расклад в Мире Таро',
    spread.category_name ? `Тема: ${spread.category_name}` : '',
    cards ? `Карты: ${cards}` : '',
    '',
  ]

  if (result.conclusion) {
    lines.push('✨ Главный вывод', result.conclusion, '')
  }
  if (result.advice) {
    lines.push('💫 Совет карт', result.advice)
  }

  return lines.filter((l, i, arr) => !(l === '' && arr[i + 1] === '')).join('\n').slice(0, 3500)
}

export function ReadingPage() {
  const {
    currentSpread,
    aiResult,
    setAIResult,
  } = useAppStore()
  const { goTo } = useAppNavigation()
  const [failed, setFailed] = useState(false)
  const [attempt, setAttempt] = useState(0)
  const [shareBusy, setShareBusy] = useState(false)
  const { data: limits } = useQuery({ queryKey: ['limits'], queryFn: api.getLimits })
  const { data: pricing } = useQuery({ queryKey: ['pricing'], queryFn: api.getPricing })
  const isPremiumUser = Boolean(limits?.is_premium || limits?.is_admin)
  const singleSpreadPrice = pricing?.single_spread ?? 59

  useEffect(() => {
    if (!currentSpread) {
      goTo('welcome', true)
    }
  }, [currentSpread, goTo])

  useEffect(() => {
    if (!currentSpread || aiResult) return

    let cancelled = false
    const generate = async () => {
      try {
        setFailed(false)
        const result = await api.interpretSpread(currentSpread.id)
        if (cancelled) return
        setAIResult(result)
        haptic('success')
      } catch (e) {
        if (cancelled) return
        try {
          const spread = await api.getSpread(currentSpread.id)
          if (spread.ai_result) {
            setAIResult(spread.ai_result)
            haptic('success')
            return
          }
        } catch {
          // ignore recovery errors
        }
        haptic('error')
        console.error(e)
        setFailed(true)
      }
    }
    generate()
    return () => {
      cancelled = true
    }
  }, [currentSpread, aiResult, setAIResult, attempt])

  if (!aiResult && failed) {
    return (
      <div className="min-h-screen gradient-bg flex flex-col items-center justify-center px-6 text-center">
        <div className="text-5xl mb-6">🌫️</div>
        <p className="text-white/80 text-lg mb-2">Карты задумались чуть дольше обычного</p>
        <p className="text-white/50 mb-8">Попробуем открыть их ещё раз?</p>
        <div className="w-full max-w-xs space-y-3">
          <Button onClick={() => setAttempt((a) => a + 1)}>Попробовать снова</Button>
          <Button variant="secondary" onClick={() => goTo('welcome')}>
            На главную
          </Button>
        </div>
      </div>
    )
  }

  if (!aiResult) {
    return (
      <div className="min-h-screen gradient-bg flex flex-col items-center justify-center px-6">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 3, repeat: Infinity, ease: 'linear' }}
          className="text-5xl mb-6"
        >
          🔮
        </motion.div>
        <p className="text-white/70 text-lg mb-8">Карты раскрывают тайну...</p>
        <div className="w-full max-w-sm space-y-4">
          <Skeleton className="h-4 w-3/4" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-5/6" />
          <Skeleton className="h-20 w-full" />
        </div>
      </div>
    )
  }

  const sections = [
    { title: 'Карта прошлого', text: aiResult.past, icon: '🕰️' },
    { title: 'Карта настоящего', text: aiResult.present, icon: '✨' },
    { title: 'Карта будущего', text: aiResult.future, icon: '🌟' },
    { title: 'Совет карт', text: aiResult.advice, icon: '💫' },
    { title: 'Главный вывод', text: aiResult.conclusion, icon: '🔮' },
  ]

  const handleShare = async () => {
    if (!currentSpread || !aiResult || shareBusy) return
    setShareBusy(true)
    haptic('medium')
    const text = buildShareText(currentSpread, aiResult)
    try {
      const { share_message_id } = await api.prepareSpreadShare(currentSpread.id)
      const result = await shareContent(text, { preparedMessageId: share_message_id })
      if (result === 'picker') haptic('success')
      else if (result === 'copied') {
        window.Telegram?.WebApp?.showAlert?.(
          'Не удалось открыть выбор чата. Текст скопирован — вставьте вручную.',
        )
      } else {
        haptic('error')
        window.Telegram?.WebApp?.showAlert?.('Не удалось поделиться. Попробуйте ещё раз.')
      }
    } catch (e) {
      console.error(e)
      const result = await shareContent(text)
      if (result === 'picker') haptic('success')
      else if (result === 'copied') {
        window.Telegram?.WebApp?.showAlert?.(
          'Не удалось открыть выбор чата. Текст скопирован — вставьте вручную.',
        )
      } else {
        haptic('error')
        window.Telegram?.WebApp?.showAlert?.('Не удалось поделиться. Попробуйте ещё раз.')
      }
    } finally {
      setShareBusy(false)
    }
  }

  return (
    <div className={`page-shell ${isPremiumUser ? 'pb-44' : 'pb-60'}`}>
      <motion.h1
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="text-2xl font-display font-bold text-center mb-6"
      >
        Ваш расклад
      </motion.h1>

      {currentSpread?.cards && currentSpread.cards.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex flex-wrap justify-center gap-2 sm:gap-3 mb-8 max-w-lg mx-auto w-full min-w-0 px-1"
        >
          {currentSpread.cards.map((card) => (
            <TarotCardVisual
              key={card.id}
              slug={card.slug}
              name={card.name}
              imageUrl={card.image_url}
              isReversed={card.is_reversed}
              size="sm"
              showName
            />
          ))}
        </motion.div>
      )}

      <div className="max-w-lg mx-auto space-y-4">
        {sections.map((section, i) => (
          section.text && (
            <motion.div
              key={section.title}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.15 }}
              className="glass-card"
            >
              <h3 className="font-semibold text-tarot-gold mb-2 flex items-center gap-2">
                <span>{section.icon}</span> {section.title}
              </h3>
              <p className="text-white/80 leading-relaxed break-words">{section.text}</p>
            </motion.div>
          )
        ))}
        <div
          className={isPremiumUser ? 'h-36' : 'h-52'}
          aria-hidden
        />
      </div>

      <div className="fixed bottom-0 left-0 right-0 z-30 p-4 pb-[max(1rem,env(safe-area-inset-bottom))] bg-gradient-to-t from-tarot-dark via-tarot-dark/95 to-transparent max-w-full overflow-hidden pointer-events-none">
        <div className="max-w-lg mx-auto space-y-2 w-full min-w-0 pointer-events-auto">
          {isPremiumUser ? (
            <>
              <Button onClick={() => goTo('history')}>История</Button>
              <div className="grid grid-cols-2 gap-2">
                <Button variant="secondary" onClick={() => goTo('welcome')}>
                  Новый расклад
                </Button>
                <Button variant="secondary" onClick={handleShare} disabled={shareBusy}>
                  {shareBusy ? 'Отправка…' : 'Поделиться'}
                </Button>
              </div>
            </>
          ) : (
            <>
              <Button onClick={() => goTo('subscription')}>
                ⭐️ Оформить подписку
              </Button>
              <div className="grid grid-cols-2 gap-2">
                <Button variant="secondary" onClick={() => goTo('subscription')}>
                  ⭐️ Ещё расклад ({singleSpreadPrice})
                </Button>
                <Button variant="secondary" onClick={handleShare} disabled={shareBusy}>
                  {shareBusy ? '…' : 'Поделиться'}
                </Button>
              </div>
              <Button variant="secondary" onClick={() => goTo('history')}>
                Архив раскладов
              </Button>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
