import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useAppStore } from '@/store/appStore'
import { useAppNavigation } from '@/hooks/useAppNavigation'
import { Button, Particles } from '@/components/ui'
import { TarotCardBack, TarotCardVisual } from '@/components/tarot/TarotCardVisual'
import { haptic } from '@/lib/telegram'

type Phase = 'stack' | 'shuffling' | 'dealt' | 'revealing' | 'revealed'

const POSITIONS = ['past', 'present', 'future'] as const
const POSITION_LABELS = { past: 'Прошлое', present: 'Настоящее', future: 'Будущее' }

export function DeckPage() {
  const { currentSpread } = useAppStore()
  const { goTo } = useAppNavigation()
  const [phase, setPhase] = useState<Phase>('stack')
  const [revealedCount, setRevealedCount] = useState(0)

  const cards = currentSpread?.cards || []

  useEffect(() => {
    if (!currentSpread) {
      goTo('welcome', true)
    }
  }, [currentSpread, goTo])

  if (!currentSpread) {
    return null
  }

  const startReading = () => {
    haptic('medium')
    setPhase('shuffling')
    setTimeout(() => setPhase('dealt'), 2000)
    setTimeout(() => setPhase('revealing'), 3500)
    setTimeout(() => setRevealedCount(1), 4000)
    setTimeout(() => setRevealedCount(2), 5000)
    setTimeout(() => setRevealedCount(3), 6000)
    setTimeout(() => {
      setPhase('revealed')
      haptic('success')
    }, 6500)
  }

  return (
    <div className="min-h-screen gradient-bg flex flex-col items-center justify-center px-4 relative overflow-hidden">
      {(phase === 'shuffling' || phase === 'dealt') && <Particles />}

      <motion.div
        animate={{ scale: phase === 'shuffling' ? 1.1 : 1 }}
        transition={{ duration: 2 }}
        className="relative w-full max-w-sm"
      >
        {phase === 'stack' && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex flex-col items-center"
          >
            <div className="relative h-64 w-40 mb-8">
              {Array.from({ length: 5 }).map((_, i) => (
                <motion.div
                  key={i}
                  className="absolute"
                  style={{ top: -i * 3, left: i * 2, zIndex: i }}
                  animate={{ y: [0, -5, 0] }}
                  transition={{ duration: 2, delay: i * 0.1, repeat: Infinity }}
                >
                  <TarotCardBack size="lg" />
                </motion.div>
              ))}
            </div>
            <Button onClick={startReading}>Узнать судьбу</Button>
          </motion.div>
        )}

        {(phase === 'shuffling' || phase === 'dealt' || phase === 'revealing' || phase === 'revealed') && (
          <div className="flex justify-center gap-3">
            {POSITIONS.map((pos, i) => {
              const card = cards.find((c) => c.position === pos)
              const isRevealed = revealedCount > i

              return (
                <div key={pos} className="flex flex-col items-center gap-2">
                  <AnimatePresence mode="wait">
                    <motion.div
                      key={isRevealed ? 'front' : 'back'}
                      initial={{ rotateY: 90 }}
                      animate={{ rotateY: 0 }}
                      transition={{ duration: 0.5 }}
                      style={{ perspective: 1000 }}
                    >
                      {isRevealed && card ? (
                        <TarotCardVisual
                          slug={card.slug}
                          name={card.name}
                          imageUrl={card.image_url}
                          isReversed={card.is_reversed}
                          size="md"
                        />
                      ) : (
                        <TarotCardBack size="md" />
                      )}
                    </motion.div>
                  </AnimatePresence>
                  <span className="text-xs text-white/50">{POSITION_LABELS[pos]}</span>
                </div>
              )
            })}
          </div>
        )}

        {phase === 'revealed' && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-10"
          >
            <Button onClick={() => goTo('reading')}>Забрать судьбу</Button>
          </motion.div>
        )}
      </motion.div>
    </div>
  )
}
