# 🔮 Мир Таро — Telegram Mini App

Современное коммерческое Telegram Mini App для онлайн-раскладов Таро с AI-интерпретацией, подписками через Telegram Stars и премиальным UX.

## Архитектура

```
tarot-mini-app/
├── frontend/          # React 19 + Vite + TailwindCSS + Framer Motion
├── backend/           # FastAPI + SQLAlchemy 2 Async + Celery
├── bot/               # aiogram 3 Telegram Bot
└── docker-compose.yml
```

### Clean Architecture (Backend)

```
backend/app/
├── domain/            # Сущности и интерфейсы репозиториев
├── application/       # Бизнес-логика, DTO, сервисы
├── infrastructure/    # БД, AI, Redis, Celery
└── api/               # HTTP endpoints (v1 + admin)
```

## Стек

| Слой | Технологии |
|------|-----------|
| Frontend | React 19, TypeScript, Vite, TailwindCSS, Framer Motion, React Query, Zustand |
| Backend | FastAPI, Python 3.12, SQLAlchemy 2 Async, PostgreSQL, Alembic, Redis, Celery |
| Bot | aiogram 3, Telegram Stars, WebApp API |
| AI | OpenAI, Claude, Gemini, OpenRouter (переключается через `.env`) |

## Быстрый старт

### 1. Клонирование и настройка

```bash
cd tarot-mini-app
cp .env.example .env
# Заполните TELEGRAM_BOT_TOKEN, AI_PROVIDER, API ключи
```

### 2. Docker (рекомендуется)

```bash
docker-compose up -d postgres redis
docker-compose up backend frontend bot
```

### 3. Локальная разработка

**Backend:**
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
alembic upgrade head
python scripts/seed.py
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

**Bot:**
```bash
cd bot
pip install -r requirements.txt
python -m app.main
```

**Celery (уведомления):**
```bash
cd backend
celery -A app.infrastructure.celery_app worker --loglevel=info
celery -A app.infrastructure.celery_app beat --loglevel=info
```

## Экраны приложения

1. **Приветствие** — выбор категории (6 карточек)
2. **Анкета** — пошаговые вопросы с анимациями
3. **Колода** — тасовка, частицы, переворот 3 карт
4. **Расшифровка** — AI-интерпретация по шаблону
5. **Монетизация** — Telegram Stars подписки
6. **Повторный вход** — экран «С возвращением!»

## API Endpoints

| Метод | Путь | Описание |
|-------|------|----------|
| POST | `/api/v1/auth/telegram` | Авторизация через WebApp |
| GET | `/api/v1/categories` | Категории раскладов |
| POST | `/api/v1/spreads` | Создать расклад |
| POST | `/api/v1/spreads/{id}/interpret` | AI-расшифровка |
| GET | `/api/v1/history` | История раскладов |
| GET | `/api/v1/pricing` | Тарифы |
| POST | `/api/v1/payments` | Создать платёж |
| GET | `/api/v1/admin/dashboard` | Админ-дашборд |

## Монетизация (Telegram Stars)

| Тариф | Цена | Возможности |
|-------|------|-------------|
| Бесплатно | — | 1 расклад/день, 5 в истории |
| Разовый | 50 ⭐️ | +1 расклад |
| 1 месяц | 150 ⭐️ | 15/день, полная история |
| 3 месяца | 400 ⭐️ | Экономия 11% |
| 6 месяцев | 700 ⭐️ | Экономия 22% |

## AI-провайдеры

Переключение в `.env`:

```env
AI_PROVIDER=openai    # openai | claude | gemini | openrouter
AI_MODEL=gpt-4o-mini
OPENAI_API_KEY=sk-...
```

## Уведомления (Celery)

- За 3 дня до окончания подписки
- В день окончания
- После окончания
- Неактивным: через 3, 7, 14 дней

## Админ-панель

API доступен по `/api/v1/admin/*`:
- Dashboard (DAU, MAU, ARPU, конверсия)
- Пользователи (поиск, блокировка)
- Финансы (доход по периодам)

## Масштабирование

Архитектура предусматривает:
- Новые колоды (`tarot_decks`)
- Новые типы раскладов
- Карта дня, натальная карта, совместимость
- Реферальная система, промокоды
- A/B-тестирование, мультиязычность
- White Label для других ботов

## Тесты

```bash
cd backend
pytest tests/ -v
```

## Лицензия

Proprietary. All rights reserved.
