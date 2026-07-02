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
}

export const PATH_TO_SCREEN: Record<string, AppScreen> = {
  '/': 'welcome',
  '/returning': 'returning',
  '/questionnaire': 'questionnaire',
  '/deck': 'deck',
  '/reading': 'reading',
  '/history': 'history',
  '/subscription': 'subscription',
}
