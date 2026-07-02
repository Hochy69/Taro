import { motion } from 'framer-motion'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/api/client'
import { useAppNavigation } from '@/hooks/useAppNavigation'
import { Button, GlassCard, Skeleton } from '@/components/ui'

export function HistoryPage() {
  const { goTo } = useAppNavigation()
  const { data: history, isLoading } = useQuery({
    queryKey: ['history'],
    queryFn: api.getHistory,
  })

  return (
    <div className="min-h-screen gradient-bg px-4 pt-20 pb-8">
      <h1 className="text-2xl font-display font-bold mb-6 max-w-lg mx-auto">
        История раскладов
      </h1>

      <div className="max-w-lg mx-auto space-y-3">
        {isLoading
          ? Array.from({ length: 3 }).map((_, i) => (
              <Skeleton key={i} className="h-24 w-full rounded-2xl" />
            ))
          : history?.length === 0
            ? (
              <GlassCard>
                <p className="text-center text-white/60 py-8">
                  Пока нет раскладов. Сделайте первый!
                </p>
              </GlassCard>
            )
            : history?.map((item, i) => (
              <motion.div
                key={item.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.05 }}
              >
                <GlassCard>
                  <div className="flex items-start justify-between">
                    <div>
                      <span className="text-lg mr-2">{item.category_emoji}</span>
                      <span className="font-semibold">{item.category_name}</span>
                      <p className="text-white/50 text-sm mt-1">
                        {new Date(item.created_at).toLocaleDateString('ru-RU')}
                      </p>
                    </div>
                    {item.is_favorite && <span>⭐</span>}
                  </div>
                  <p className="text-white/70 text-sm mt-2 line-clamp-2">
                    {item.conclusion || item.situation}
                  </p>
                  <div className="flex gap-2 mt-2">
                    {item.cards.map((c) => (
                      <span key={c} className="text-xs bg-white/10 px-2 py-1 rounded-lg">
                        {c}
                      </span>
                    ))}
                  </div>
                </GlassCard>
              </motion.div>
            ))}
      </div>

      <div className="mt-6 max-w-lg mx-auto">
        <Button onClick={() => goTo('welcome')}>Новый расклад</Button>
      </div>
    </div>
  )
}
