from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.admin.router import router as admin_router
from app.api.v1.router import router as v1_router
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.application.services.promo_service import PromoService
    from app.infrastructure.database.session import async_session

    async with async_session() as session:
        await PromoService(session).ensure_default_codes()
        await session.commit()
    yield


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    lifespan=lifespan,
)

origins = [settings.frontend_url, "https://web.telegram.org"]
if settings.telegram_webapp_url:
    origins.append(settings.telegram_webapp_url.rstrip("/"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"https://.*\.tuna\.am",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(v1_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok", "app": settings.app_name}
