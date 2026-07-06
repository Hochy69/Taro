from datetime import date, datetime

from pydantic import BaseModel, Field


class TelegramAuthRequest(BaseModel):
    init_data: str


class TelegramAuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"
    is_returning: bool
    last_category: str | None = None


class ProfileUpdate(BaseModel):
    name: str | None = None
    birth_date: date | None = None
    birth_time: str | None = None
    birth_city: str | None = None
    gender: str | None = None
    zodiac_sign: str | None = None


class UserResponse(BaseModel):
    id: int
    telegram_id: int
    first_name: str | None
    username: str | None
    is_premium: bool
    is_admin: bool = False
    terms_accepted: bool = False
    profile: ProfileUpdate | None = None

    model_config = {"from_attributes": True}


class AcceptTermsResponse(BaseModel):
    terms_accepted: bool
    accepted_at: datetime


class ShareMessageResponse(BaseModel):
    share_message_id: str


class AdminGrantRequest(BaseModel):
    internal_secret: str
    word: str
    telegram_id: int
    username: str | None = None
    first_name: str | None = None


class ReferralResponse(BaseModel):
    code: str
    link: str
    invites_count: int
    bonus_earned: int
    milestones: list["ReferralMilestoneResponse"] = []
    next_milestone: "ReferralMilestoneResponse | None" = None


class ReferralMilestoneResponse(BaseModel):
    invites_required: int
    reward: str
    reached: bool


class ReferralPendingRequest(BaseModel):
    telegram_id: int
    referral_code: str
    secret: str


class CategoryResponse(BaseModel):
    id: int
    slug: str
    name: str
    emoji: str
    description: str | None = None

    model_config = {"from_attributes": True}


class CreateSpreadRequest(BaseModel):
    category_slug: str
    situation: str = Field(..., min_length=3, max_length=1000)
    emotion: str
    profile: ProfileUpdate | None = None


class CardResponse(BaseModel):
    id: int
    slug: str
    name: str
    position: str
    is_reversed: bool
    image_url: str | None = None

    model_config = {"from_attributes": True}


class SpreadResponse(BaseModel):
    id: int
    category_slug: str
    category_name: str
    situation: str | None
    emotion: str | None
    status: str
    cards: list[CardResponse]
    created_at: str

    model_config = {"from_attributes": True}


class AIResultResponse(BaseModel):
    response_text: str
    past: str | None
    present: str | None
    future: str | None
    advice: str | None
    conclusion: str | None
    generation_time_ms: int

    model_config = {"from_attributes": True}


class SpreadDetailResponse(SpreadResponse):
    ai_result: AIResultResponse | None = None


class LimitsResponse(BaseModel):
    can_spread: bool
    used_today: int
    daily_limit: int
    is_premium: bool
    is_admin: bool = False
    bonus_spreads: int
    compatibility_credits: int = 0
    period_days: int = 1
    next_available_at: str | None = None
    completed_spreads: int = 0
    first_paid_discount_eligible: bool = False
    first_paid_discounted_price: int | None = None
    first_paid_discount_percent: int = 0
    subscription_plan: str | None = None
    subscription_expires_at: str | None = None


class PaymentCreateRequest(BaseModel):
    payment_type: str  # single_spread | subscription | compatibility | spread_pack_3 | spread_pack_5 | love_bundle
    plan: str | None = None  # month_1 | month_3 | month_6
    promo_code: str | None = None


class PromoValidateRequest(BaseModel):
    code: str


class PromoValidateResponse(BaseModel):
    code: str
    discount_percent: int
    uses_left: int | None = None


class PaymentResponse(BaseModel):
    id: int
    payment_type: str
    stars_amount: int
    status: str
    plan: str | None = None
    invoice_link: str | None = None
    original_stars_amount: int | None = None
    discount_percent: int | None = None
    promo_code: str | None = None
    free: bool = False

    model_config = {"from_attributes": True}


class StarsConfirmRequest(BaseModel):
    payload: str  # our internal payment id
    telegram_payment_charge_id: str
    secret: str


class PreCheckoutValidateRequest(BaseModel):
    payload: str
    total_amount: int
    currency: str
    secret: str


class SubscriptionPlanResponse(BaseModel):
    plan: str
    stars: int
    duration_days: int
    daily_spreads: int
    features: list[str]


class SpreadPackResponse(BaseModel):
    pack: str
    stars: int
    spreads: int
    savings_percent: int
    label: str


class LoveBundleResponse(BaseModel):
    stars: int
    original_stars: int
    savings_percent: int
    description: str


class PricingResponse(BaseModel):
    single_spread: int
    compatibility: int
    plans: list[SubscriptionPlanResponse]
    spread_packs: list[SpreadPackResponse] = []
    love_bundle: LoveBundleResponse | None = None
    first_paid_discount_percent: int = 0
    subscription_per_day_stars: int | None = None


class FavoriteRequest(BaseModel):
    spread_id: int


class HistoryItemResponse(BaseModel):
    id: int
    category_name: str
    category_emoji: str
    cards: list[str]
    situation: str | None
    conclusion: str | None
    created_at: str
    is_favorite: bool = False


class CardOfDayCardResponse(BaseModel):
    id: int
    slug: str
    name: str
    is_reversed: bool
    image_url: str | None = None


class CardOfDayResponse(BaseModel):
    date: str
    card: CardOfDayCardResponse
    meaning: str
    advice: str
    conclusion: str
    text: str


class LunarBirthResponse(BaseModel):
    lunar_day: str
    title: str
    meaning: str
    advice: str


class ZodiacPortraitResponse(BaseModel):
    zodiac_sign: str
    emoji: str
    summary: str
    essence: str
    strengths: str
    shadow: str
    love: str
    career: str
    advice: str
    text: str
    lunar: LunarBirthResponse | None = None


class PlanetPositionResponse(BaseModel):
    key: str
    name: str
    symbol: str
    sign: str
    sign_emoji: str
    degree: float
    longitude: float
    house: int | None = None
    interpretation: str
    wheel_angle: float


class HousePositionResponse(BaseModel):
    house: int
    sign: str
    sign_emoji: str
    degree: float


class AspectResponse(BaseModel):
    planet_a: str
    planet_b: str
    aspect: str
    angle: float
    description: str


class NatalChartResponse(BaseModel):
    birth_date: str
    birth_time: str | None = None
    birth_city: str | None = None
    time_unknown: bool = False
    ascendant: str | None = None
    ascendant_emoji: str | None = None
    ascendant_degree: float | None = None
    ascendant_longitude: float | None = None
    summary: str
    planets: list[PlanetPositionResponse]
    houses: list[HousePositionResponse]
    aspects: list[AspectResponse]
    text: str


class PartnerBirthData(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    birth_date: date
    birth_time: str | None = None
    birth_city: str | None = None
    gender: str | None = None


class CompatibilityResponse(BaseModel):
    partner_name: str
    score: int
    summary: str
    user_sun_sign: str
    partner_sun_sign: str
    user_moon_sign: str
    partner_moon_sign: str
    sun_match: str
    moon_match: str | None = None
    love: str
    friendship: str
    challenges: str
    advice: str
    text: str


class UserPreferencesUpdate(BaseModel):
    daily_card_push: bool | None = None


class UserPreferencesResponse(BaseModel):
    daily_card_push: bool
