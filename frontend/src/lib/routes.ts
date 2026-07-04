import type { AppScreen } from '@/store/appStore'

export const ROUTES: Record<AppScreen, string> = {
  welcome: '/',
  returning: '/returning',
  questionnaire: '/questionnaire',
  deck: '/deck',
  reading: '/reading',
  result: '/reading',
  history: '/history',
  subscription: '/subscription',
  cardOfDay: '/card-of-day',
  portrait: '/portrait',
  natalChart: '/natal-chart',
  compatibility: '/compatibility',
}

export const PATH_TO_SCREEN: Record<string, AppScreen> = {
  '/': 'welcome',
  '/returning': 'returning',
  '/questionnaire': 'questionnaire',
  '/deck': 'deck',
  '/reading': 'reading',
  '/history': 'history',
  '/subscription': 'subscription',
  '/card-of-day': 'cardOfDay',
  '/portrait': 'portrait',
  '/natal-chart': 'natalChart',
  '/compatibility': 'compatibility',
}
