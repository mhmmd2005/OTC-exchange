# OTC Exchange Backend

This directory contains the Django + DRF backend for the OTC Exchange project. The frontend remains in the repository root and is intentionally not connected to the backend during this phase.

## Tech stack

- Python 3.12+
- Django 5.1
- Django REST Framework
- PostgreSQL (production target)
- drf-spectacular for OpenAPI docs
- django-environ for environment-based settings

## Setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver
```

## Local database notes

The project is configured for PostgreSQL by default. If PostgreSQL is not available locally, set `USE_SQLITE_FOR_DEV=True` in `.env` to use SQLite temporarily for local setup and migration validation. This is explicitly documented and not the default production configuration.

## Useful commands

```bash
python manage.py check
python manage.py makemigrations
python manage.py migrate
python manage.py test
python manage.py createsuperuser
```
