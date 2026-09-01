# OTC Exchange

This repository contains the existing Vue 3 + Vite frontend at the project root and a new Django + DRF backend under `backend/`.

## Current project structure

- Frontend: `/` (Vue 3, Vite, Pinia, Router)
- Backend: `/backend` (Django REST API foundation)

## Frontend setup

```bash
npm install
npm run dev
```

The frontend remains in place and is not connected to the backend in this phase.

## Backend setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver
```

## Python and Node versions

- Python: 3.12+
- Node: 18+ recommended

## Environment variables

See `backend/.env.example` for the required variables:

- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG`
- `DJANGO_ALLOWED_HOSTS`
- `USE_SQLITE_FOR_DEV`
- `DATABASE_NAME`
- `DATABASE_USER`
- `DATABASE_PASSWORD`
- `DATABASE_HOST`
- `DATABASE_PORT`
- `CORS_ALLOWED_ORIGINS`
- `REDIS_URL`

## PostgreSQL setup

The production target is PostgreSQL. Configure the database settings in `backend/.env` before using PostgreSQL locally.

If PostgreSQL is unavailable, set `USE_SQLITE_FOR_DEV=True` temporarily in `.env` to validate migrations locally. This is explicitly a fallback for local development only.

## Backend commands

```bash
cd backend
python manage.py check
python manage.py makemigrations
python manage.py migrate
python manage.py test
python manage.py createsuperuser
```

## API foundation

The backend exposes:

- `/api/v1/`
- `/api/v1/assets/`
- `/api/v1/wallets/`
- `/api/v1/otc/`
- `/api/v1/orders/`
- `/api/v1/trades/`
- `/api/v1/transactions/`
- `/api/v1/kyc/`
- `/api/v1/security/`
- `/api/v1/support/`
- `/api/schema/`
- `/api/docs/`

This phase focuses on the backend foundation, not frontend API integration.
