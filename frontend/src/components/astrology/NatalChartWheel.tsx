interface Planet {
  symbol: string
  sign_emoji: string
  wheel_angle: number
  name: string
}

interface Props {
  planets: Planet[]
  ascendant?: string | null
  ascendantEmoji?: string | null
  ascendantAngle?: number | null
}

const SIGNS = ['♈', '♉', '♊', '♋', '♌', '♍', '♎', '♏', '♐', '♑', '♒', '♓']

export function NatalChartWheel({ planets, ascendant, ascendantEmoji, ascendantAngle }: Props) {
  const size = 280
  const cx = size / 2
  const cy = size / 2
  const outerR = 120
  const innerR = 78
  const planetR = 98

  const toXY = (angleDeg: number, radius: number) => {
    const rad = ((angleDeg - 90) * Math.PI) / 180
    return {
      x: cx + radius * Math.cos(rad),
      y: cy + radius * Math.sin(rad),
    }
  }

  return (
    <svg viewBox={`0 0 ${size} ${size}`} className="w-full max-w-[300px] mx-auto">
      <defs>
        <radialGradient id="wheelGlow" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#D4AF37" stopOpacity="0.15" />
          <stop offset="100%" stopColor="#0F0A1A" stopOpacity="0" />
        </radialGradient>
      </defs>
      <circle cx={cx} cy={cy} r={outerR + 8} fill="url(#wheelGlow)" />
      <circle cx={cx} cy={cy} r={outerR} fill="none" stroke="#D4AF37" strokeOpacity="0.35" strokeWidth="1.5" />
      <circle cx={cx} cy={cy} r={innerR} fill="none" stroke="#ffffff" strokeOpacity="0.12" strokeWidth="1" />

      {SIGNS.map((emoji, i) => {
        const angle = i * 30 + 15
        const { x, y } = toXY(angle, outerR - 14)
        return (
          <text key={emoji} x={x} y={y} textAnchor="middle" dominantBaseline="middle" fontSize="14" fill="#D4AF37" opacity="0.85">
            {emoji}
          </text>
        )
      })}

      {Array.from({ length: 12 }).map((_, i) => {
        const { x, y } = toXY(i * 30, outerR)
        const { x: x2, y: y2 } = toXY(i * 30, innerR)
        return (
          <line key={i} x1={x} y1={y} x2={x2} y2={y2} stroke="#ffffff" strokeOpacity="0.08" strokeWidth="1" />
        )
      })}

      {planets.map((p) => {
        const { x, y } = toXY(p.wheel_angle, planetR)
        return (
          <g key={p.name}>
            <circle cx={x} cy={y} r="11" fill="#1A1225" stroke="#D4AF37" strokeOpacity="0.5" strokeWidth="1" />
            <text x={x} y={y + 1} textAnchor="middle" dominantBaseline="middle" fontSize="12" fill="#fff">
              {p.symbol}
            </text>
          </g>
        )
      })}

      {ascendant && ascendantAngle != null && (
        <g>
          {(() => {
            const { x, y } = toXY(ascendantAngle, outerR + 2)
            const { x: x2, y: y2 } = toXY(ascendantAngle, innerR - 4)
            return (
              <>
                <line x1={x} y1={y} x2={x2} y2={y2} stroke="#D4AF37" strokeWidth="2" strokeOpacity="0.7" />
                <text x={x} y={y - 10} textAnchor="middle" fontSize="10" fill="#D4AF37">
                  ASC {ascendantEmoji}
                </text>
              </>
            )
          })()}
        </g>
      )}

      <text x={cx} y={cy} textAnchor="middle" dominantBaseline="middle" fontSize="11" fill="#ffffff" opacity="0.4">
        натальная карта
      </text>
    </svg>
  )
}
