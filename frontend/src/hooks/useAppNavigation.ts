import { useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { ROUTES, PATH_TO_SCREEN } from '@/lib/routes'
import { useAppStore, type AppScreen } from '@/store/appStore'
import { useLocation } from 'react-router-dom'
import { useEffect } from 'react'

type GoToOptions = { replace?: boolean; hash?: string }

export function useAppNavigation() {
  const navigate = useNavigate()
  const setScreen = useAppStore((s) => s.setScreen)

  const goTo = useCallback(
    (screen: AppScreen, options?: boolean | GoToOptions) => {
      const opts: GoToOptions =
        typeof options === 'boolean' ? { replace: options } : (options ?? {})
      setScreen(screen)
      const hash = opts.hash ? `#${opts.hash}` : ''
      navigate(`${ROUTES[screen]}${hash}`, { replace: opts.replace })
    },
    [navigate, setScreen],
  )

  return { goTo }
}

/** Sync URL → Zustand screen on back/forward navigation */
export function useSyncRouteToStore() {
  const location = useLocation()
  const setScreen = useAppStore((s) => s.setScreen)

  useEffect(() => {
    const screen = PATH_TO_SCREEN[location.pathname]
    if (screen) {
      setScreen(screen)
    }
  }, [location.pathname, setScreen])
}
