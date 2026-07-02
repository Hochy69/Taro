import { motion } from 'framer-motion'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/api/client'
import { useAppStore } from '@/store/appStore'
import { useAppNavigation } from '@/hooks/useAppNavigation'
import { GlassCard } from '@/components/ui'
import { haptic } from '@/lib/telegram'

export function WelcomePage() {
  const { goTo } = useAppNavigation()
  const { setCategory } = useAppStore()
  const { data: categories, isLoading } = useQuery({
    queryKey: ['categories'],
    queryFn: api.getCategories,
  })
  const { data: limits } = useQuery({
    queryKey: ['limits'],
    queryFn: api.getLimits,
  })

  const handleSelect = (category: NonNullable<typeof categories>[0]) => {
    haptic('medium')
    setCategory(category)
    if (limits && !limits.can_spread) {
      goTo('subscription')
      return
    }
    goTo('questionnaire')
  }

  return (
    <div className="min-h-screen gradient-bg px-4 pt-20 pb-24">
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center mb-10"
      >
        <motion.div
          animate={{ rotate: [0, 5, -5, 0] }}
          transition={{ duration: 4, repeat: Infinity }}
          className="text-6xl mb-4"
        >
          🔮
        </motion.div>
        <h1 className="text-3xl font-display font-bold text-white mb-3">
          Добро пожаловать в Мир Таро
        </h1>
        <p className="text-white/60 text-lg">
          Выберите сферу жизни, которая волнует вас сейчас
        </p>
      </motion.div>

      <div className="grid grid-cols-2 gap-3 max-w-md mx-auto">
        {isLoading
          ? Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="h-28 skeleton rounded-2xl" />
            ))
          : categories?.map((cat, i) => (
              <GlassCard key={cat.slug} onClick={() => handleSelect(cat)} delay={i * 0.08}>
                <div className="text-center py-2">
                  <span className="text-4xl block mb-2">{cat.emoji}</span>
                  <span className="font-semibold text-white">{cat.name}</span>
                </div>
              </GlassCard>
            ))}
      </div>
    </div>
  )
}
