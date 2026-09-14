# OTC Exchange - Project Documentation

## Project Overview

The OTC Exchange is a cryptocurrency over-the-counter trading platform consisting of a Django REST Framework backend and a Vue 3 frontend. The platform provides users with the ability to buy and sell cryptocurrencies through OTC quotes, manage wallets, handle orders and trades, and complete KYC verification.

**Current Status:** Development/Integration Phase - NOT PRODUCTION-READY

## Technology Stack

### Backend
- **Framework:** Django 5.1.5
- **API:** Django REST Framework 3.15.2
- **Authentication:** djangorestframework-simplejwt 5.3.1
- **Database:** PostgreSQL (production), SQLite (development fallback)
- **Cache/Queue:** Redis 5.1.0, Celery 5.4.0
- **API Documentation:** drf-spectacular 0.28.0
- **CORS:** django-cors-headers 4.6.0
- **Environment:** django-environ 0.11.2
- **Python Version:** 3.12+

### Frontend
- **Framework:** Vue 3.5.42
- **Build Tool:** Vite 8.2.2
- **Language:** TypeScript 5.9.2
- **State Management:** Pinia 3.0.1
- **Routing:** Vue Router 4.2.5
- **Node Version:** 18+ recommended

## Backend Architecture

### Django Apps/Modules

The backend is organized into 12 Django apps under `backend/apps/`:

1. **accounts** - User authentication and management
   - Custom User model with phone number as primary identifier
   - OTP verification system
   - Iranian bank account management
   - Password complexity validation
   - Session management with idle timeout

2. **assets** - Cryptocurrency asset management
   - Asset model with pricing data
   - AssetNetwork model for blockchain networks
   - Price tracking (24h change, high/low)

3. **wallets** - User wallet management
   - Wallet model with balance tracking
   - Available/locked balance separation
   - Deposit address management

4. **otc** - Over-the-counter trading
   - OTCQuote model for price quotes
   - OTCDeal model for executed trades
   - Buy/sell side support
   - Fee calculation

5. **orders** - Order management
   - Order model with market/limit types
   - OrderTimeline for status tracking
   - Payment processing workflow

6. **trades** - Trade execution
   - Trade model for executed transactions
   - Execution price and fee tracking

7. **transactions** - Transaction history
   - Transaction model for all financial operations
   - Support for deposits, withdrawals, buys, sells
   - Bank account and order references

8. **kyc** - Know Your Customer verification
   - KycApplication model
   - Document upload (identity, selfie)
   - Admin approval/rejection workflow

9. **security** - Security features
   - SecurityEvent logging
   - LoginHistory tracking
   - Session management
   - Two-factor authentication setup

10. **support** - Customer support
    - Ticket model with categories and priorities
    - TicketMessage for communication
    - FAQ management

11. **notifications** - User notifications
    - Notification model with categories
    - Read/unread status tracking
    - Actionable notifications

12. **markets** - Market data
    - Market model for asset markets
    - 24h volume and price tracking

**Note:** Core models and routes are implemented across the current modules. API/backend integration is ongoing. Some business logic and production integrations are still incomplete.

### API Structure

All API endpoints are prefixed with `/api/v1/`:

#### Authentication (`/api/v1/auth/`)
- `POST /request-login-otp/` - Request login OTP
- `POST /request-registration-otp/` - Request registration OTP
- `POST /verify-otp/` - Verify OTP code
- `POST /login/verify-password/` - Login with password
- `POST /register/set-password/` - Set password during registration
- `POST /refresh/` - Refresh JWT access token
- `POST /logout/` - Logout
- `GET /me/` - Get current user info
- `POST /request-password-reset-otp/` - Request password reset OTP
- `POST /reset-password/` - Reset password

#### Assets (`/api/v1/assets/`)
- `GET /` - List all assets
- `GET /<symbol>/` - Get asset details
- `GET /<symbol>/networks/` - Get asset networks
- `GET /<symbol>/history/` - Get price history

#### Wallets (`/api/v1/wallets/`)
- `GET /` - List user wallets
- `GET /summary/` - Get wallet summary

**Root-level endpoint:**
- `GET /api/v1/wallet` - Wallet summary endpoint (frontend compatibility/summary endpoint)

#### OTC Trading (`/api/v1/otc/`)
- `POST /quotes` - Create OTC quote
- `GET /quotes/<id>` - Get quote details
- `POST /orders` - Create OTC order

**Trade compatibility route** (maps to OTC API):
- `POST /api/v1/trade/quotes` - Create OTC quote
- `GET /api/v1/trade/quotes/<id>` - Get quote details
- `POST /api/v1/trade/orders` - Create OTC order

#### Orders (`/api/v1/orders/`)
- `GET /` - List orders
- `GET /<id>/` - Get order details
- `POST /<id>/cancel` - Cancel order

#### Trades (`/api/v1/trades/`)
- `GET /` - List trades

#### Transactions (`/api/v1/transactions/`)
- `GET /` - List transactions

#### KYC (`/api/v1/kyc/`)
- `GET /` - Get or create KYC application
- `POST /submit/` - Submit KYC application
- `PUT /update/` - Update KYC application
- `GET /status/` - Get KYC status
- `GET /admin/` - Admin: List KYC applications
- `GET /admin/<pk>/` - Admin: Get KYC details
- `POST /admin/<pk>/approve/` - Admin: Approve KYC
- `POST /admin/<pk>/reject/` - Admin: Reject KYC

#### Security (`/api/v1/security/`)
- `GET /` - Security overview
- `GET /sessions/` - List active sessions
- `DELETE /sessions/<session_id>/` - Revoke session
- `DELETE /sessions/others/` - Revoke other sessions
- `GET /events/` - List security events
- `GET /login-history/` - List login history
- `POST /password/` - Change password
- `POST /two-factor/setup/` - Setup 2FA
- `POST /two-factor/` - Manage 2FA
- `POST /anti-phishing/` - Set anti-phishing code
- `GET /withdrawal-whitelist/` - Get withdrawal whitelist

#### Notifications (`/api/v1/notifications/`)
- `GET /` - List notifications
- `GET /unread-count` - Get unread count
- `GET /<pk>` - Mark notification as read
- `POST /read-all` - Mark all as read

#### Support (`/api/v1/support/`)
- `GET /faqs` - List FAQs
- `GET /tickets` - List tickets
- `POST /tickets` - Create ticket
- `GET /tickets/<pk>` - Get ticket details
- `POST /tickets/<pk>/messages` - Add message to ticket
- `POST /tickets/<pk>/close` - Close ticket

#### Markets (`/api/v1/markets`)
- `GET /` - List markets (authenticated endpoint)

**Note:** Current market data is development/integration data and not a production live market feed.

#### Documentation
- `GET /api/schema/` - OpenAPI schema
- `GET /api/docs/` - Swagger UI documentation

### Authentication Approach

The platform uses a phone number-based authentication system with the following features:

- **Primary Identifier:** Phone number (username field disabled)
- **OTP Verification:** SMS-based OTP for login and registration
- **JWT Tokens:** Access tokens (15 min default) and refresh tokens (7 days default)
- **Idle Timeout:** Sessions expire after 30 minutes of inactivity (configurable)
- **Session Management:** Redis-based session storage with version control
- **Custom Authentication:** `IdleTimeoutJWTAuthentication` class with session validation
- **Password Complexity:** Custom validator for password strength

### Database Configuration

- **Production:** PostgreSQL with connection pooling
- **Development:** SQLite fallback (controlled by `USE_SQLITE_FOR_DEV` env var)
- **Migrations:** All 12 apps have migration files created

### Celery Integration

- **Broker:** Redis
- **Task Serialization:** JSON
- **Timezone:** Asia/Tehran
- **Configured** but task implementations not yet defined

## Frontend Architecture

### Project Structure

The frontend is a Vue 3 SPA with the following structure:

- **`src/pages/`** - Page components organized by feature
  - `auth/` - Authentication pages (login, register, verify, password reset)
  - `app/` - Main application pages (dashboard, trade, wallet, orders, etc.)
- **`src/components/`** - Reusable UI components
- **`src/router/`** - Vue Router configuration
- **`src/stores/`** - Pinia state management stores
  - `auth.ts` - Authentication state
  - `wallet.ts` - Wallet state
  - `markets.ts` - Market data state
  - `notifications.ts` - Notification state
  - `preferences.ts` - User preferences
- **`src/services/`** - API service layer
  - `api.ts` - Core API client with error handling
  - `live/` - Live API service implementations
  - `mock/` - Mock service implementations for development
  - Individual service files for each backend module
- **`src/types/`** - TypeScript type definitions
- **`src/utils/`** - Utility functions

### Key Features

- **Persian/Farsi Interface:** All UI text is in Persian
- **Mock API Support:** Development mode can use mock services instead of live API
- **JWT Token Management:** Automatic token refresh and storage
- **Route Guards:** Authentication and permission-based navigation
- **Responsive Design:** Mobile-first approach with navigation optimization
- **Error Handling:** Comprehensive API error handling with user-friendly messages

### Build Configuration

- **Development:** Vite dev server with HMR
- **Production:** Optimized build with TypeScript compilation
- **Alias Resolution:** Build-time alias for live services
- **Target:** ES2020

## Current Integration Status

- ✅ Authentication/JWT integration: implemented and tested
- ✅ Preferences and security APIs: integrated
- ✅ Bank accounts: integrated
- ✅ Verification summary: integrated, but full production KYC workflow is incomplete
- ✅ Wallet summary: integrated and tested
- ✅ Markets: integrated and tested at API level
- ✅ Orders: integrated and tested
- ✅ Transactions: integrated and tested
- ✅ Support: integrated
- ✅ OTC quote API: integrated and tested at API level
- ⚠️ OTC order execution: requires further testing
- ⚠️ Notifications: currently limited/stub-level and not a fully operational notification system
- ⚠️ Celery: configured, production task implementations not complete
- ⚠️ WebSocket/realtime production features: not implemented
- ⚠️ Payment/blockchain integrations: not implemented

## Development Workflow

### Backend Development

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Configure .env with database and Redis settings
python manage.py migrate
python manage.py runserver
```

### Frontend Development

```bash
cd frontend
npm install
npm run dev
```

For mock API development:
```bash
VITE_USE_MOCK_API=true npm run dev
```

### Environment Variables

Key backend environment variables (see `backend/.env.example`):
- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG`
- `DJANGO_ALLOWED_HOSTS`
- `USE_SQLITE_FOR_DEV`
- `DATABASE_NAME`, `DATABASE_USER`, `DATABASE_PASSWORD`, `DATABASE_HOST`, `DATABASE_PORT`
- `CORS_ALLOWED_ORIGINS`
- `REDIS_URL`, `REDIS_CACHE_URL`
- `JWT_ACCESS_MINUTES`, `JWT_REFRESH_DAYS`, `JWT_IDLE_TIMEOUT_SECONDS`
- `SMS_PROVIDER`

Key frontend environment variables (see `frontend/.env.example`):
- `VITE_API_BASE_URL`
- `VITE_USE_MOCK_API` (development only)

## Important Notes

- **This project is in active development and is NOT production-ready**
- Security features are implemented but require further testing and audit
- Payment processing and blockchain integration are not implemented
- Production realtime market/event streaming is not implemented
- Performance and load testing have not been completed
- Production SMS provider configuration is still required
- KYC document verification requires manual admin review
- Security audit is required before production deployment

## API Documentation

Interactive API documentation is available at:
- **Swagger UI:** `http://localhost:8000/api/docs/`
- **OpenAPI Schema:** `http://localhost:8000/api/schema/`

## License

Project license information should be added to the repository.
