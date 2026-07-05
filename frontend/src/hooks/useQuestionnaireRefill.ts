import { useCallback } from 'react'
import { type Category } from '@/api/client'
import { useAppNavigation } from '@/hooks/useAppNavigation'
import { useAppStore } from '@/store/appStore'
import { haptic } from '@/lib/telegram'

export function useQuestionnaireRefill() {
  const beginQuestionnaireRefill = useAppStore((s) => s.beginQuestionnaireRefill)
  const setCategory = useAppStore((s) => s.setCategory)
  const { goTo } = useAppNavigation()

  return useCallback(
    (categories?: Category[]) => {
      haptic('medium')
      const category = beginQuestionnaireRefill()
      if (!category) {
        window.Telegram?.WebApp?.showAlert?.(
          'Сначала выберите категорию расклада на главном экране.',
        )
        return false
      }

      const resolved = categories?.find((c) => c.slug === category.slug) ?? category
      setCategory(resolved)
      goTo('questionnaire')
      return true
    },
    [beginQuestionnaireRefill, setCategory, goTo],
  )
}
