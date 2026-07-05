import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useAppStore } from '@/store/appStore'
import { useAppNavigation } from '@/hooks/useAppNavigation'
import { Button } from '@/components/ui'
import { getZodiacFromDate, haptic } from '@/lib/telegram'
import { api } from '@/api/client'

const EMOTIONS = [
  { id: 'anxiety', label: 'тревога', emoji: '😰' },
  { id: 'fear', label: 'страх', emoji: '😨' },
  { id: 'hope', label: 'надежда', emoji: '🌟' },
  { id: 'love', label: 'любовь', emoji: '❤️' },
  { id: 'confusion', label: 'растерянность', emoji: '😕' },
  { id: 'anger', label: 'злость', emoji: '😤' },
  { id: 'expectation', label: 'ожидание', emoji: '⏳' },
  { id: 'other', label: 'другое', emoji: '💭' },
]

const GENDERS = [
  { id: 'm', label: 'Мужской', emoji: '♂️' },
  { id: 'w', label: 'Женский', emoji: '♀️' },
]

const STEPS = ['name', 'birthDate', 'birthDetails', 'situation', 'emotion'] as const

export function QuestionnairePage() {
  const {
    questionnaire,
    updateQuestionnaire,
    questionnaireStep,
    setQuestionnaireStep,
    selectedCategory,
    setSpread,
    skipQuestionnairePrefill,
    clearQuestionnairePrefill,
  } = useAppStore()
  const { goTo } = useAppNavigation()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const step = STEPS[questionnaireStep]
  const isLast = questionnaireStep === STEPS.length - 1

  useEffect(() => {
    if (skipQuestionnairePrefill) {
      setQuestionnaireStep(0)
      clearQuestionnairePrefill()
      return
    }

    if (questionnaireStep !== 0) return

    const hasName = questionnaire.name.trim().length >= 2
    const hasBirthDate = questionnaire.birthDate.length > 0
    const hasBirthDetails =
      questionnaire.birthCity.trim().length >= 2 &&
      questionnaire.gender.length > 0 &&
      (questionnaire.birthTimeUnknown || questionnaire.birthTime.length > 0)

    if (hasName && hasBirthDate && hasBirthDetails) {
      setQuestionnaireStep(3)
    } else if (hasName && hasBirthDate) {
      setQuestionnaireStep(2)
    } else if (hasName) {
      setQuestionnaireStep(1)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [skipQuestionnairePrefill])

  const canProceed = () => {
    switch (step) {
      case 'name':
        return questionnaire.name.trim().length >= 2
      case 'birthDate':
        return questionnaire.birthDate.length > 0
      case 'birthDetails':
        return (
          questionnaire.birthCity.trim().length >= 2 &&
          (questionnaire.birthTimeUnknown || questionnaire.birthTime.length > 0) &&
          questionnaire.gender.length > 0
        )
      case 'situation':
        return questionnaire.situation.trim().length >= 5
      case 'emotion':
        return questionnaire.emotion.length > 0
      default:
        return false
    }
  }

  const handleNext = async () => {
    haptic('light')
    if (!isLast) {
      if (step === 'birthDate' && questionnaire.birthDate) {
        updateQuestionnaire({ zodiacSign: getZodiacFromDate(questionnaire.birthDate) })
      }
      setQuestionnaireStep(questionnaireStep + 1)
      return
    }

    if (!selectedCategory) {
      setError('Не выбрана категория. Вернитесь на главный экран.')
      return
    }
    setLoading(true)
    setError(null)
    try {
      const spread = await api.createSpread({
        category_slug: selectedCategory.slug,
        situation: questionnaire.situation,
        emotion: questionnaire.emotion,
        profile: {
          name: questionnaire.name,
          birth_date: questionnaire.birthDate,
          birth_time: questionnaire.birthTimeUnknown ? undefined : questionnaire.birthTime,
          birth_city: questionnaire.birthCity,
          gender: questionnaire.gender,
          zodiac_sign: questionnaire.zodiacSign,
        },
      })
      setSpread(spread)
      haptic('success')
      goTo('deck')
    } catch (e) {
      haptic('error')
      console.error(e)
      const msg = e instanceof Error ? e.message : ''
      if (/limit|подписк|расклад доступен/i.test(msg)) {
        setError(
          'Бесплатный расклад доступен раз в 3 дня. Оформите подписку или купите разовый расклад за звёзды, чтобы сделать расклад сейчас.',
        )
      } else {
        setError('Не удалось подготовить колоду. Проверьте связь и попробуйте ещё раз.')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="page-shell flex flex-col px-4 sm:px-6 overflow-x-hidden">
      <div className="flex gap-2 mb-8">
        {STEPS.map((_, i) => (
          <div
            key={i}
            className={`h-1 flex-1 rounded-full transition-colors ${
              i <= questionnaireStep ? 'bg-tarot-gold' : 'bg-white/10'
            }`}
          />
        ))}
      </div>

      <AnimatePresence mode="wait">
        <motion.div
          key={step}
          initial={{ opacity: 0, x: 24 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -24 }}
          transition={{ duration: 0.3 }}
          className="flex-1 flex flex-col"
        >
          {step === 'name' && (
            <>
              <h2 className="text-2xl font-display font-bold mb-2">Как вас зовут?</h2>
              <p className="text-white/50 mb-6">Карты обращаются к вам лично</p>
              <input
                type="text"
                value={questionnaire.name}
                onChange={(e) => updateQuestionnaire({ name: e.target.value })}
                placeholder="Ваше имя"
                className="w-full px-4 py-4 glass rounded-2xl text-white text-lg
                           placeholder:text-white/30 focus:outline-none focus:ring-2 focus:ring-tarot-gold/50"
                autoFocus
              />
            </>
          )}

          {step === 'birthDate' && (
            <>
              <h2 className="text-2xl font-display font-bold mb-2">Дата рождения</h2>
              <p className="text-white/50 mb-6">Для точного расклада и портрета</p>
              <input
                type="date"
                value={questionnaire.birthDate}
                onChange={(e) => {
                  const date = e.target.value
                  updateQuestionnaire({
                    birthDate: date,
                    zodiacSign: date ? getZodiacFromDate(date) : '',
                  })
                }}
                className="w-full px-4 py-4 glass rounded-2xl text-white text-lg
                           focus:outline-none focus:ring-2 focus:ring-tarot-gold/50"
              />
              {questionnaire.zodiacSign && (
                <motion.p
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="mt-4 text-tarot-gold text-center text-lg"
                >
                  ✨ {questionnaire.zodiacSign}
                </motion.p>
              )}
            </>
          )}

          {step === 'birthDetails' && (
            <>
              <h2 className="text-2xl font-display font-bold mb-2">Данные рождения</h2>
              <p className="text-white/50 mb-6">Как на натальной карте — для вашего портрета</p>

              <label className="block text-white/60 text-sm mb-2">Время рождения</label>
              <input
                type="time"
                value={questionnaire.birthTime}
                disabled={questionnaire.birthTimeUnknown}
                onChange={(e) => updateQuestionnaire({ birthTime: e.target.value })}
                className="w-full px-4 py-4 glass rounded-2xl text-white text-lg mb-3
                           focus:outline-none focus:ring-2 focus:ring-tarot-gold/50
                           disabled:opacity-40"
              />
              <label className="flex items-center gap-3 mb-6 text-white/70">
                <input
                  type="checkbox"
                  checked={questionnaire.birthTimeUnknown}
                  onChange={(e) =>
                    updateQuestionnaire({
                      birthTimeUnknown: e.target.checked,
                      birthTime: e.target.checked ? '' : questionnaire.birthTime,
                    })
                  }
                  className="w-5 h-5 accent-tarot-gold"
                />
                Не знаю точное время
              </label>

              <label className="block text-white/60 text-sm mb-2">Город рождения</label>
              <input
                type="text"
                value={questionnaire.birthCity}
                onChange={(e) => updateQuestionnaire({ birthCity: e.target.value })}
                placeholder="Например: Москва"
                className="w-full px-4 py-4 glass rounded-2xl text-white text-lg mb-6
                           placeholder:text-white/30 focus:outline-none focus:ring-2 focus:ring-tarot-gold/50"
              />

              <p className="text-white/60 text-sm mb-3">Пол</p>
              <div className="grid grid-cols-2 gap-3">
                {GENDERS.map((g) => (
                  <motion.button
                    key={g.id}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => {
                      haptic('light')
                      updateQuestionnaire({ gender: g.id })
                    }}
                    className={`p-4 rounded-2xl text-left transition-all ${
                      questionnaire.gender === g.id
                        ? 'bg-tarot-gold/20 border-2 border-tarot-gold'
                        : 'glass border-2 border-transparent'
                    }`}
                  >
                    <span className="text-2xl block mb-1">{g.emoji}</span>
                    <span className="text-white">{g.label}</span>
                  </motion.button>
                ))}
              </div>
            </>
          )}

          {step === 'situation' && (
            <>
              <h2 className="text-2xl font-display font-bold mb-2">
                Какая ситуация вас волнует?
              </h2>
              <p className="text-white/50 mb-6">Опишите коротко, что на душе</p>
              <textarea
                value={questionnaire.situation}
                onChange={(e) => updateQuestionnaire({ situation: e.target.value })}
                placeholder="Расскажите о своей ситуации..."
                rows={4}
                className="w-full px-4 py-4 glass rounded-2xl text-white text-lg resize-none
                           placeholder:text-white/30 focus:outline-none focus:ring-2 focus:ring-tarot-gold/50"
                autoFocus
              />
            </>
          )}

          {step === 'emotion' && (
            <>
              <h2 className="text-2xl font-display font-bold mb-2">
                Какие эмоции испытываете?
              </h2>
              <p className="text-white/50 mb-6">Выберите одну</p>
              <div className="grid grid-cols-2 gap-3">
                {EMOTIONS.map((em) => (
                  <motion.button
                    key={em.id}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => {
                      haptic('light')
                      updateQuestionnaire({ emotion: em.label })
                    }}
                    className={`p-4 rounded-2xl text-left transition-all ${
                      questionnaire.emotion === em.label
                        ? 'bg-tarot-gold/20 border-2 border-tarot-gold'
                        : 'glass border-2 border-transparent'
                    }`}
                  >
                    <span className="text-2xl block mb-1">{em.emoji}</span>
                    <span className="text-white capitalize">{em.label}</span>
                  </motion.button>
                ))}
              </div>
            </>
          )}
        </motion.div>
      </AnimatePresence>

      <div className="mt-auto pt-6">
        {error && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-3 rounded-2xl border border-red-400/30 bg-red-500/10 px-4 py-3 text-sm text-red-200"
          >
            <p>{error}</p>
            {/limit|подписк/i.test(error) && (
              <button
                onClick={() => goTo('subscription')}
                className="mt-2 font-semibold text-tarot-gold underline underline-offset-2"
              >
                Перейти к подписке ⭐️
              </button>
            )}
          </motion.div>
        )}
        <Button onClick={handleNext} disabled={!canProceed() || loading}>
          {loading ? 'Подготовка колоды...' : isLast ? 'К колоде ✨' : 'Далее'}
        </Button>
      </div>
    </div>
  )
}
