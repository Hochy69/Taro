import { create } from 'zustand'
import type { Category, Spread, AIResult } from '@/api/client'

export type AppScreen =
  | 'welcome'
  | 'returning'
  | 'questionnaire'
  | 'deck'
  | 'reading'
  | 'result'
  | 'history'
  | 'subscription'
  | 'cardOfDay'
  | 'portrait'
  | 'natalChart'
  | 'compatibility'

interface QuestionnaireData {
  name: string
  birthDate: string
  birthTime: string
  birthTimeUnknown: boolean
  birthCity: string
  gender: string
  zodiacSign: string
  situation: string
  emotion: string
}

interface AppState {
  screen: AppScreen
  isAuthenticated: boolean
  isPremium: boolean
  termsAccepted: boolean
  isReturning: boolean
  lastCategory: string | null
  selectedCategory: Category | null
  questionnaire: QuestionnaireData
  currentSpread: Spread | null
  aiResult: AIResult | null
  questionnaireStep: number

  setScreen: (screen: AppScreen) => void
  setAuth: (isPremium: boolean, isReturning: boolean, lastCategory: string | null) => void
  setTermsAccepted: (accepted: boolean) => void
  setCategory: (category: Category) => void
  updateQuestionnaire: (data: Partial<QuestionnaireData>) => void
  setQuestionnaireStep: (step: number) => void
  setSpread: (spread: Spread) => void
  setAIResult: (result: AIResult) => void
  resetFlow: () => void
}

const initialQuestionnaire: QuestionnaireData = {
  name: '',
  birthDate: '',
  birthTime: '',
  birthTimeUnknown: false,
  birthCity: '',
  gender: '',
  zodiacSign: '',
  situation: '',
  emotion: '',
}

export const useAppStore = create<AppState>((set) => ({
  screen: 'welcome',
  isAuthenticated: false,
  isPremium: false,
  termsAccepted: false,
  isReturning: false,
  lastCategory: null,
  selectedCategory: null,
  questionnaire: { ...initialQuestionnaire },
  currentSpread: null,
  aiResult: null,
  questionnaireStep: 0,

  setScreen: (screen) => set({ screen }),
  setAuth: (isPremium, isReturning, lastCategory) =>
    set({ isAuthenticated: true, isPremium, isReturning, lastCategory }),
  setTermsAccepted: (accepted) => set({ termsAccepted: accepted }),
  setCategory: (category) => set({ selectedCategory: category }),
  updateQuestionnaire: (data) =>
    set((s) => ({ questionnaire: { ...s.questionnaire, ...data } })),
  setQuestionnaireStep: (step) => set({ questionnaireStep: step }),
  setSpread: (spread) => set({ currentSpread: spread }),
  setAIResult: (result) => set({ aiResult: result }),
  resetFlow: () =>
    set({
      selectedCategory: null,
      questionnaire: { ...initialQuestionnaire },
      currentSpread: null,
      aiResult: null,
      questionnaireStep: 0,
    }),
}))
