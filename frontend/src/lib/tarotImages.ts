/** Rider–Waite Smith (public domain) — локальные копии в /public/cards/ */
export const TAROT_CARD_IMAGES: Record<string, string> = {
  'the-fool': '/cards/the-fool.jpg',
  'the-magician': '/cards/the-magician.jpg',
  'the-high-priestess': '/cards/the-high-priestess.jpg',
  'the-empress': '/cards/the-empress.jpg',
  'the-emperor': '/cards/the-emperor.jpg',
  'the-hierophant': '/cards/the-hierophant.jpg',
  'the-lovers': '/cards/the-lovers.jpg',
  'the-chariot': '/cards/the-chariot.jpg',
  strength: '/cards/strength.jpg',
  'the-hermit': '/cards/the-hermit.jpg',
  'wheel-of-fortune': '/cards/wheel-of-fortune.jpg',
  justice: '/cards/justice.jpg',
  'the-hanged-man': '/cards/the-hanged-man.jpg',
  death: '/cards/death.jpg',
  temperance: '/cards/temperance.jpg',
  'the-devil': '/cards/the-devil.jpg',
  'the-tower': '/cards/the-tower.jpg',
  'the-star': '/cards/the-star.jpg',
  'the-moon': '/cards/the-moon.jpg',
  'the-sun': '/cards/the-sun.jpg',
  judgement: '/cards/judgement.jpg',
  'the-world': '/cards/the-world.jpg',
}

const WIKIMEDIA_SOURCES: Record<string, string> = {
  'the-fool': 'https://upload.wikimedia.org/wikipedia/commons/9/90/RWS_Tarot_00_Fool.jpg',
  'the-magician': 'https://upload.wikimedia.org/wikipedia/commons/d/de/RWS_Tarot_01_Magician.jpg',
  'the-high-priestess': 'https://upload.wikimedia.org/wikipedia/commons/8/88/RWS_Tarot_02_High_Priestess.jpg',
  'the-empress': 'https://upload.wikimedia.org/wikipedia/commons/d/d2/RWS_Tarot_03_Empress.jpg',
  'the-emperor': 'https://upload.wikimedia.org/wikipedia/commons/c/c3/RWS_Tarot_04_Emperor.jpg',
  'the-hierophant': 'https://upload.wikimedia.org/wikipedia/commons/8/8d/RWS_Tarot_05_Hierophant.jpg',
  'the-lovers': 'https://upload.wikimedia.org/wikipedia/commons/3/3a/RWS_Tarot_06_Lovers.jpg',
  'the-chariot': 'https://upload.wikimedia.org/wikipedia/commons/9/9b/RWS_Tarot_07_Chariot.jpg',
  strength: 'https://upload.wikimedia.org/wikipedia/commons/f/f5/RWS_Tarot_08_Strength.jpg',
  'the-hermit': 'https://upload.wikimedia.org/wikipedia/commons/4/4d/RWS_Tarot_09_Hermit.jpg',
  'wheel-of-fortune': 'https://upload.wikimedia.org/wikipedia/commons/3/3c/RWS_Tarot_10_Wheel_of_Fortune.jpg',
  justice: 'https://upload.wikimedia.org/wikipedia/commons/e/e0/RWS_Tarot_11_Justice.jpg',
  'the-hanged-man': 'https://upload.wikimedia.org/wikipedia/commons/2/2b/RWS_Tarot_12_Hanged_Man.jpg',
  death: 'https://upload.wikimedia.org/wikipedia/commons/d/d7/RWS_Tarot_13_Death.jpg',
  temperance: 'https://upload.wikimedia.org/wikipedia/commons/f/f8/RWS_Tarot_14_Temperance.jpg',
  'the-devil': 'https://upload.wikimedia.org/wikipedia/commons/5/55/RWS_Tarot_15_Devil.jpg',
  'the-tower': 'https://upload.wikimedia.org/wikipedia/commons/5/53/RWS_Tarot_16_Tower.jpg',
  'the-star': 'https://upload.wikimedia.org/wikipedia/commons/d/db/RWS_Tarot_17_Star.jpg',
  'the-moon': 'https://upload.wikimedia.org/wikipedia/commons/7/7f/RWS_Tarot_18_Moon.jpg',
  'the-sun': 'https://upload.wikimedia.org/wikipedia/commons/1/17/RWS_Tarot_19_Sun.jpg',
  judgement: 'https://upload.wikimedia.org/wikipedia/commons/d/dd/RWS_Tarot_20_Judgement.jpg',
  'the-world': 'https://upload.wikimedia.org/wikipedia/commons/f/ff/RWS_Tarot_21_World.jpg',
}

export function getTarotCardImage(slug: string, imageUrl?: string | null): string | null {
  if (slug && TAROT_CARD_IMAGES[slug]) return TAROT_CARD_IMAGES[slug]
  if (imageUrl) return imageUrl.replace(/\.webp$/, '.jpg')
  return null
}

export function getTarotCardRemoteFallback(slug: string): string | null {
  return WIKIMEDIA_SOURCES[slug] ?? null
}
