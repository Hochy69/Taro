const ZODIAC_SIGNS = [
  { name: 'Козерог', start: [12, 22], end: [1, 19] },
  { name: 'Водолей', start: [1, 20], end: [2, 18] },
  { name: 'Рыбы', start: [2, 19], end: [3, 20] },
  { name: 'Овен', start: [3, 21], end: [4, 19] },
  { name: 'Телец', start: [4, 20], end: [5, 20] },
  { name: 'Близнецы', start: [5, 21], end: [6, 20] },
  { name: 'Рак', start: [6, 21], end: [7, 22] },
  { name: 'Лев', start: [7, 23], end: [8, 22] },
  { name: 'Дева', start: [8, 23], end: [9, 22] },
  { name: 'Весы', start: [9, 23], end: [10, 22] },
  { name: 'Скорпион', start: [10, 23], end: [11, 21] },
  { name: 'Стрелец', start: [11, 22], end: [12, 21] },
]

export function initTelegramWebApp(): void {
  const tg = window.Telegram?.WebApp
  if (!tg) {
    unlockPageScroll()
    return
  }

  tg.ready()
  tg.expand()

  applyTelegramSafeAreaInsets(tg)

  if (typeof tg.disableVerticalSwipes === 'function') {
    tg.disableVerticalSwipes()
  }

  unlockPageScroll()

  if (typeof tg.onEvent === 'function') {
    tg.onEvent('viewportChanged', () => {
      applyTelegramSafeAreaInsets(tg)
      unlockPageScroll()
    })
  }
}

function applyTelegramSafeAreaInsets(tg: NonNullable<Window['Telegram']>['WebApp']): void {
  const root = document.documentElement
  const inset = tg.contentSafeAreaInset ?? tg.safeAreaInset
  if (!inset) return
  root.style.setProperty('--tg-safe-top', `${inset.top}px`)
  root.style.setProperty('--tg-safe-bottom', `${inset.bottom}px`)
  root.style.setProperty('--tg-safe-left', `${inset.left}px`)
  root.style.setProperty('--tg-safe-right', `${inset.right}px`)
}

/** Android WebView / Telegram often locks body scroll — restore it. */
export function unlockPageScroll(): void {
  const html = document.documentElement
  const body = document.body
  html.style.height = 'auto'
  html.style.minHeight = '100%'
  html.style.overflowY = 'auto'
  html.style.overflowX = 'hidden'
  html.style.setProperty('-webkit-overflow-scrolling', 'touch')
  body.style.height = 'auto'
  body.style.minHeight = '100%'
  body.style.overflowY = 'auto'
  body.style.overflowX = 'hidden'
  body.style.setProperty('-webkit-overflow-scrolling', 'touch')
  body.style.touchAction = 'pan-y'
}

export function getZodiacFromDate(dateStr: string): string {
  const date = new Date(dateStr)
  const month = date.getMonth() + 1
  const day = date.getDate()

  for (const sign of ZODIAC_SIGNS) {
    const [startM, startD] = sign.start
    const [endM, endD] = sign.end
    if (
      (month === startM && day >= startD) ||
      (month === endM && day <= endD)
    ) {
      return sign.name
    }
  }
  return 'Козерог'
}

export function haptic(type: 'light' | 'medium' | 'heavy' | 'success' | 'error' = 'light') {
  const tg = window.Telegram?.WebApp
  if (!tg?.HapticFeedback) return

  if (type === 'success' || type === 'error') {
    tg.HapticFeedback.notificationOccurred(type)
  } else {
    tg.HapticFeedback.impactOccurred(type)
  }
}

export function openInvoice(stars: number, title: string) {
  const tg = window.Telegram?.WebApp
  if (tg?.openInvoice) {
    // Invoice URL would come from backend in production
    console.log(`Opening invoice: ${title} - ${stars} stars`)
  }
}

/** Open Telegram's native "choose chat" share sheet (Mini App). */
export function openTelegramSharePicker(options: { text: string; url?: string }): boolean {
  const tg = window.Telegram?.WebApp
  const text = options.text.trim()
  const url = options.url?.trim()
  if (!tg?.openTelegramLink || (!text && !url)) return false

  const params: string[] = []
  if (url) params.push(`url=${encodeURIComponent(url)}`)
  if (text) params.push(`text=${encodeURIComponent(text)}`)
  tg.openTelegramLink(`https://t.me/share/url?${params.join('&')}`)
  return true
}

/** Native Telegram Mini App share (chat picker inside the app). */
export function shareTelegramMessage(preparedMessageId: string): Promise<boolean> {
  const tg = window.Telegram?.WebApp
  if (!tg?.shareMessage) {
    return Promise.resolve(false)
  }
  return new Promise((resolve) => {
    tg.shareMessage!(preparedMessageId, (sent) => resolve(Boolean(sent)))
  })
}

async function copyToClipboard(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text)
    return true
  } catch {
    return false
  }
}

/**
 * Share via Telegram chat picker (shareMessage or t.me/share/url).
 * Clipboard is only a last resort outside Telegram.
 */
export async function shareContent(
  text: string,
  options?: { url?: string; preparedMessageId?: string },
): Promise<'picker' | 'copied' | 'failed'> {
  const trimmed = text.trim()
  if (!trimmed && !options?.url?.trim()) return 'failed'

  if (options?.preparedMessageId) {
    const sent = await shareTelegramMessage(options.preparedMessageId)
    if (sent) return 'picker'
  }

  if (openTelegramSharePicker({ text: trimmed, url: options?.url })) {
    return 'picker'
  }

  if (trimmed && (await copyToClipboard(trimmed))) {
    return 'copied'
  }
  return 'failed'
}

/** Copy text to clipboard with a Telegram alert (for explicit "Copy" buttons). */
export async function shareText(text: string): Promise<'copied' | 'failed'> {
  const trimmed = text.trim()
  if (!trimmed) return 'failed'

  if (await copyToClipboard(trimmed)) {
    window.Telegram?.WebApp?.showAlert?.(
      'Текст скопирован. Откройте чат и вставьте сообщение (долгое нажатие → Вставить).',
    )
    return 'copied'
  }
  return 'failed'
}

declare global {
  interface Window {
    Telegram?: {
      WebApp: {
        initData: string
        ready: () => void
        expand: () => void
        close: () => void
        colorScheme: 'light' | 'dark'
        themeParams: Record<string, string>
        HapticFeedback?: {
          impactOccurred: (style: string) => void
          notificationOccurred: (type: string) => void
        }
        openInvoice?: (url: string, callback?: (status: string) => void) => void
        openTelegramLink?: (url: string) => void
        shareMessage?: (msgId: string, callback?: (success: boolean) => void) => void
        showAlert?: (message: string, callback?: () => void) => void
        MainButton: {
          text: string
          show: () => void
          hide: () => void
          onClick: (cb: () => void) => void
        }
        BackButton?: {
          isVisible: boolean
          show: () => void
          hide: () => void
          onClick: (cb: () => void) => void
          offClick: (cb: () => void) => void
        }
        disableVerticalSwipes?: () => void
        enableVerticalSwipes?: () => void
        safeAreaInset?: { top: number; bottom: number; left: number; right: number }
        contentSafeAreaInset?: { top: number; bottom: number; left: number; right: number }
        onEvent?: (eventType: string, callback: () => void) => void
        offEvent?: (eventType: string, callback: () => void) => void
      }
    }
  }
}
