import { motion } from 'framer-motion'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/api/client'
import { useAppNavigation } from '@/hooks/useAppNavigation'
import { Button, GlassCard, Skeleton } from '@/components/ui'
import { NatalChartWheel } from '@/components/astrology/NatalChartWheel'
import { haptic } from '@/lib/telegram'

export function NatalChartPage() {
  const { goTo } = useAppNavigation()
  const { data, isLoading, error } = useQuery({
    queryKey: ['natal-chart'],
    queryFn: api.getNatalChart,
    retry: false,
  })

  if (isLoading) {
    return (
      <div className="min-h-screen gradient-bg px-4 pt-20 pb-8 space-y-4">
        <Skeleton className="h-72 w-full rounded-3xl" />
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-32 w-full" />
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className="min-h-screen gradient-bg flex flex-col items-center justify-center px-6 text-center">
        <div className="text-5xl mb-4">🌌</div>
        <p className="text-white/70 mb-2">Натальная карта недоступна</p>
        <p className="text-white/50 text-sm mb-6">
          Укажите дату, время и город рождения в анкете при следующем раскладе
        </p>
        <Button onClick={() => goTo('welcome')}>Сделать расклад</Button>
      </div>
    )
  }

  return (
    <div className="page-shell">
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="text-center mb-6 px-2">
        <h1 className="text-2xl sm:text-3xl font-display font-bold text-white mb-2">Натальная карта</h1>
        <p className="text-white/60 text-sm break-words">
          {data.birth_date}
          {data.birth_time ? ` • ${data.birth_time}` : ' • время неизвестно'}
          {data.birth_city ? ` • ${data.birth_city}` : ''}
        </p>
      </motion.div>

      <GlassCard className="mb-6 flex flex-col items-center py-6 min-w-0 overflow-hidden">
        <NatalChartWheel
          planets={data.planets}
          ascendant={data.ascendant}
          ascendantEmoji={data.ascendant_emoji}
          ascendantAngle={data.ascendant_longitude}
        />
        {data.ascendant && (
          <p className="text-tarot-gold text-sm mt-3">
            Асцендент: {data.ascendant_emoji} {data.ascendant}
            {data.ascendant_degree != null ? ` ${data.ascendant_degree}°` : ''}
          </p>
        )}
        {data.time_unknown && (
          <p className="text-white/40 text-xs mt-2 text-center px-4">
            Без точного времени асцендент и дома приблизительны
          </p>
        )}
      </GlassCard>

      <div className="max-w-md mx-auto space-y-4">
        <GlassCard>
          <p className="text-white/80 leading-relaxed">{data.summary}</p>
        </GlassCard>

        {data.planets.map((planet, i) => (
          <motion.div key={planet.key} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.05 * i }}>
            <GlassCard>
              <h3 className="text-tarot-gold font-semibold mb-1 break-words">
                {planet.symbol} {planet.name} в {planet.sign_emoji} {planet.sign}
                <span className="text-white/40 font-normal text-sm"> {planet.degree}°</span>
                {planet.house ? <span className="text-white/40 font-normal text-sm"> • {planet.house} дом</span> : null}
              </h3>
              <p className="text-white/75 text-sm leading-relaxed break-words">{planet.interpretation}</p>
            </GlassCard>
          </motion.div>
        ))}

        {data.aspects.length > 0 && (
          <GlassCard>
            <h3 className="text-tarot-gold font-semibold mb-3">Ключевые аспекты</h3>
            <ul className="space-y-2">
              {data.aspects.map((asp, idx) => (
                <li key={idx} className="text-white/70 text-sm break-words">
                  <span className="text-white/90">{asp.planet_a} — {asp.planet_b}</span>
                  {' '}({asp.aspect}): {asp.description}
                </li>
              ))}
            </ul>
          </GlassCard>
        )}
      </div>

      <div className="max-w-md mx-auto mt-8 space-y-3">
        <Button
          onClick={() => {
            haptic('light')
            goTo('compatibility')
          }}
        >
          Что между вами 💕
        </Button>
        <Button variant="secondary" onClick={() => goTo('portrait')}>
          Мой портрет
        </Button>
      </div>
    </div>
  )
}
