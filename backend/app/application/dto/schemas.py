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
    zodiac_sign: str | None = None


class UserResponse(BaseModel):
    id: int
    telegram_id: int
    first_name: str | None
    username: str | None
    is_premium: bool
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
    bonus_spreads: int
    period_days: int = 1
    next_available_at: str | None = None


class PaymentCreateRequest(BaseModel):
    payment_type: str  # single_spread | subscription
    plan: str | None = None  # month_1 | month_3 | month_6


class PaymentResponse(BaseModel):
    id: int
    payment_type: str
    stars_amount: int
    status: str
    plan: str | None = None
    invoice_link: str | None = None

    model_config = {"from_attributes": True}


class StarsConfirmRequest(BaseModel):
    payload: str  # our internal payment id
    telegram_payment_charge_id: str
    secret: str


class SubscriptionPlanResponse(BaseModel):
    plan: str
    stars: int
    duration_days: int
    daily_spreads: int
    features: list[str]


class PricingResponse(BaseModel):
    single_spread: int
    plans: list[SubscriptionPlanResponse]


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
