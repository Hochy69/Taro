import { motion } from 'framer-motion'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/api/client'
import { useAppStore } from '@/store/appStore'
import { useAppNavigation } from '@/hooks/useAppNavigation'
import { Button, GlassCard } from '@/components/ui'
import { haptic } from '@/lib/telegram'

const CATEGORY_NAMES: Record<string, string> = {
  love: 'Любовь',
  money: 'Деньги',
  career: 'Карьера',
  family: 'Семья',
  destiny: 'Предназначение',
  general: 'Общий расклад',
}

export function ReturningPage() {
  const { lastCategory, resetFlow, setCategory } = useAppStore()
  const { goTo } = useAppNavigation()
  const { data: categories } = useQuery({ queryKey: ['categories'], queryFn: api.getCategories })
  const categoryName = lastCategory ? CATEGORY_NAMES[lastCategory] || lastCategory : 'Общий расклад'

  const continueTopic = () => {
    haptic('medium')
    if (lastCategory) {
      // Restore the previously chosen category so the flow can complete.
      const found = categories?.find((c) => c.slug === lastCategory)
      setCategory(
        found ?? { id: 0, slug: lastCategory, name: categoryName, emoji: '🔮' },
      )
      goTo('questionnaire')
    } else {
      goTo('welcome')
    }
  }

  return (
    <div className="min-h-screen gradient-bg flex flex-col items-center justify-center px-6">
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        className="w-full max-w-sm"
      >
        <div className="text-center mb-8">
          <motion.span
            animate={{ scale: [1, 1.1, 1] }}
            transition={{ duration: 2, repeat: Infinity }}
            className="text-5xl block mb-4"
          >
            ✨
          </motion.span>
          <h1 className="text-2xl font-display font-bold mb-2">С возвращением!</h1>
          <p className="text-white/60">
            Последняя тема: <span className="text-tarot-gold">{categoryName}</span>
          </p>
        </div>

        <GlassCard className="mb-4">
          <p className="text-center text-white/80 mb-4">Что хотите сделать?</p>
          <div className="space-y-3">
            <Button onClick={continueTopic}>
              Продолжить эту тему
            </Button>
            <Button
              variant="secondary"
              onClick={() => {
                haptic('light')
                goTo('welcome')
              }}
            >
              Новая категория
            </Button>
            <Button
              variant="secondary"
              onClick={() => {
                haptic('light')
                resetFlow()
                goTo('welcome')
              }}
            >
              Заполнить анкету заново
            </Button>
          </div>
        </GlassCard>
      </motion.div>
    </div>
  )
}
