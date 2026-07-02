import { useState } from 'react'
import { getTarotCardImage, getTarotCardRemoteFallback } from '@/lib/tarotImages'

type Size = 'sm' | 'md' | 'lg'

const SIZE_CLASS: Record<Size, string> = {
  sm: 'w-20 h-[7.5rem]',
  md: 'w-28 h-[10.5rem]',
  lg: 'w-36 h-[13.5rem]',
}

interface TarotCardVisualProps {
  slug: string
  name: string
  imageUrl?: string | null
  isReversed?: boolean
  faceDown?: boolean
  size?: Size
  showName?: boolean
  className?: string
}

export function TarotCardBack({ size = 'md', className = '' }: { size?: Size; className?: string }) {
  return (
    <div
      className={`${SIZE_CLASS[size]} rounded-xl overflow-hidden shadow-lg shadow-black/40
                  border-2 border-amber-700/60 relative ${className}`}
      aria-hidden
    >
      <div className="absolute inset-0 bg-gradient-to-br from-[#1a0f2e] via-[#2d1b4e] to-[#0f0a1a]" />
      <div
        className="absolute inset-1.5 rounded-lg border border-amber-600/40
                   bg-[repeating-linear-gradient(45deg,rgba(212,175,55,0.08)_0px,rgba(212,175,55,0.08)_2px,transparent_2px,transparent_8px)]"
      />
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="w-[70%] aspect-square rounded-full border-2 border-amber-500/50 flex items-center justify-center">
          <span className="text-2xl text-amber-400/90">☽</span>
        </div>
      </div>
    </div>
  )
}

export function TarotCardVisual({
  slug,
  name,
  imageUrl,
  isReversed = false,
  faceDown = false,
  size = 'md',
  showName = false,
  className = '',
}: TarotCardVisualProps) {
  const [imgSrc, setImgSrc] = useState<string | null>(
    () => getTarotCardImage(slug, imageUrl),
  )
  const [triedRemote, setTriedRemote] = useState(false)

  if (faceDown) {
    return <TarotCardBack size={size} className={className} />
  }

  const handleError = () => {
    if (!triedRemote) {
      const remote = getTarotCardRemoteFallback(slug)
      if (remote) {
        setTriedRemote(true)
        setImgSrc(remote)
        return
      }
    }
    setImgSrc(null)
  }

  return (
    <div className={`flex flex-col items-center gap-1.5 ${className}`}>
      <div
        className={`${SIZE_CLASS[size]} rounded-xl overflow-hidden shadow-lg shadow-black/40
                    border-2 border-amber-700/70 bg-amber-50 relative`}
      >
        {imgSrc ? (
          <img
            src={imgSrc}
            alt={name}
            loading="lazy"
            onError={handleError}
            className={`w-full h-full object-cover transition-transform duration-500
              ${isReversed ? 'rotate-180' : ''}`}
          />
        ) : (
          <div
            className={`w-full h-full flex flex-col items-center justify-center p-2
              bg-gradient-to-b from-amber-100 to-amber-200 text-tarot-dark text-center
              ${isReversed ? 'rotate-180' : ''}`}
          >
            <span className="text-[10px] uppercase tracking-wider text-amber-800/70 mb-1">Таро</span>
            <span className="text-xs font-bold leading-tight">{name}</span>
          </div>
        )}
        {isReversed && (
          <div className="absolute top-1 left-0 right-0 text-center pointer-events-none">
            <span className="text-[9px] bg-red-900/80 text-red-100 px-1.5 py-0.5 rounded-full">
              перевёрнутая
            </span>
          </div>
        )}
      </div>
      {showName && (
        <span className="text-xs text-white/70 text-center max-w-[7rem] leading-tight">{name}</span>
      )}
    </div>
  )
}
