<script setup lang="ts">
import {computed, nextTick, onBeforeUnmount, onMounted, ref, watch} from 'vue'

import AppIcon from '@/components/ui/AppIcon.vue'

type Method = 'GET' | 'POST' | 'PUT' | 'DELETE'
type IntegrationStatus = 'done' | 'warning' | 'todo'

interface Endpoint {
  method: Method
  path: string
  description: string
}

interface ApiSection {
  title: string
  basePath?: string
  endpoints: Endpoint[]
  note?: string
}

interface BackendApp {
  name: string
  description: string
  features: string[]
}

interface TechItem {
  name: string
  role: string
  version: string
  icon: string
}

interface IntegrationItem {
  status: IntegrationStatus
  title: string
  description: string
}

const sections = [
  {id: 'overview', title: 'معرفی پروژه'},
  {id: 'tech-stack', title: 'فناوری‌ها'},
  {id: 'backend', title: 'معماری Backend'},
  {id: 'frontend', title: 'معماری Frontend'},
  {id: 'integration', title: 'وضعیت یکپارچه‌سازی'},
  {id: 'workflow', title: 'گردش کار توسعه'},
  {id: 'notes', title: 'نکات مهم'},
]

const activeSection = ref('overview')
const tocOpen = ref(false)
const copiedPath = ref<string | null>(null)

const apiBaseUrl = computed(
    () => import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
)

const apiDocsUrl = computed(() => `${apiBaseUrl.value}/api/docs/`)
const apiSchemaUrl = computed(() => `${apiBaseUrl.value}/api/schema/`)

const techItems: TechItem[] = [
  {name: 'Django', role: 'فریم‌ورک Backend', version: '5.1.5', icon: 'server'},
  {name: 'DRF', role: 'REST API', version: '3.15.2', icon: 'code'},
  {name: 'PostgreSQL', role: 'پایگاه داده Production', version: 'Production', icon: 'database'},
  {name: 'SQLite', role: 'پایگاه داده توسعه', version: 'Development', icon: 'database'},
  {name: 'Redis', role: 'Cache / Queue', version: '5.1.0', icon: 'bolt'},
  {name: 'Celery', role: 'پردازش پس‌زمینه', version: '5.4.0', icon: 'clock'},
  {name: 'Vue 3', role: 'Frontend', version: '3.5.42', icon: 'layout'},
  {name: 'TypeScript', role: 'زبان برنامه‌نویسی', version: '5.9.2', icon: 'code'},
  {name: 'Pinia', role: 'مدیریت وضعیت', version: '3.0.1', icon: 'layers'},
  {name: 'Vite', role: 'Build Tool', version: '8.2.2', icon: 'bolt'},
]

const backendApps: BackendApp[] = [
  {
    name: 'accounts',
    description: 'مدیریت کاربران و احراز هویت',
    features: ['OTP', 'JWT', 'حساب بانکی', 'Session'],
  },
  {
    name: 'assets',
    description: 'مدیریت دارایی‌ها و شبکه‌های رمزارزی',
    features: ['Asset', 'Network', 'قیمت', '24h'],
  },
  {
    name: 'wallets',
    description: 'مدیریت کیف پول و موجودی کاربران',
    features: ['Balance', 'Locked', 'Address'],
  },
  {
    name: 'markets',
    description: 'مدیریت بازار و داده‌های قیمتی',
    features: ['Market', 'Price', '24h Volume'],
  },
  {
    name: 'otc',
    description: 'منطق معاملات OTC و Quote',
    features: ['Quote', 'Deal', 'Buy/Sell', 'Fee'],
  },
  {
    name: 'orders',
    description: 'مدیریت سفارش‌ها و Timeline',
    features: ['Order', 'Timeline', 'Status'],
  },
  {
    name: 'trades',
    description: 'ثبت معاملات اجراشده',
    features: ['Execution', 'Price', 'Fee'],
  },
  {
    name: 'transactions',
    description: 'تاریخچه تراکنش‌های مالی',
    features: ['Deposit', 'Withdraw', 'Buy', 'Sell'],
  },
  {
    name: 'kyc',
    description: 'احراز هویت و بررسی مدارک',
    features: ['KYC', 'Documents', 'Approval'],
  },
  {
    name: 'security',
    description: 'رویدادها و قابلیت‌های امنیتی',
    features: ['Events', 'Sessions', '2FA'],
  },
  {
    name: 'support',
    description: 'پشتیبانی، FAQ و تیکت‌ها',
    features: ['Tickets', 'Messages', 'FAQ'],
  },
  {
    name: 'notifications',
    description: 'اعلان‌های کاربر',
    features: ['Notifications', 'Unread', 'Actions'],
  },
]

const apiSections: ApiSection[] = [
  {
    title: 'احراز هویت',
    basePath: '/api/v1/auth/',
    endpoints: [
      {method: 'POST', path: '/request-login-otp/', description: 'درخواست OTP ورود'},
      {method: 'POST', path: '/request-registration-otp/', description: 'درخواست OTP ثبت‌نام'},
      {method: 'POST', path: '/verify-otp/', description: 'تأیید کد OTP'},
      {method: 'POST', path: '/login/verify-password/', description: 'ورود با رمز عبور'},
      {method: 'POST', path: '/register/set-password/', description: 'تنظیم رمز عبور ثبت‌نام'},
      {method: 'POST', path: '/refresh/', description: 'تمدید Access Token'},
      {method: 'POST', path: '/logout/', description: 'خروج از حساب'},
      {method: 'GET', path: '/me/', description: 'دریافت اطلاعات کاربر فعلی'},
      {method: 'POST', path: '/request-password-reset-otp/', description: 'درخواست OTP بازیابی رمز'},
      {method: 'POST', path: '/reset-password/', description: 'بازنشانی رمز عبور'},
    ],
  },
  {
    title: 'دارایی‌ها',
    basePath: '/api/v1/assets/',
    endpoints: [
      {method: 'GET', path: '/', description: 'دریافت فهرست دارایی‌ها'},
      {method: 'GET', path: '/<symbol>/', description: 'دریافت جزئیات دارایی'},
      {method: 'GET', path: '/<symbol>/networks/', description: 'دریافت شبکه‌های دارایی'},
      {method: 'GET', path: '/<symbol>/history/', description: 'دریافت تاریخچه قیمت'},
    ],
  },
  {
    title: 'کیف پول',
    basePath: '/api/v1/wallets/',
    endpoints: [
      {method: 'GET', path: '/', description: 'دریافت کیف پول‌های کاربر'},
      {method: 'GET', path: '/summary/', description: 'دریافت خلاصه کیف پول'},
    ],
    note: 'مسیر سازگاری Frontend نیز وجود دارد: GET /api/v1/wallet',
  },
  {
    title: 'معاملات OTC',
    basePath: '/api/v1/otc/',
    endpoints: [
      {method: 'POST', path: '/quotes', description: 'دریافت Quote خرید یا فروش'},
      {method: 'GET', path: '/quotes/<id>', description: 'دریافت جزئیات Quote'},
      {method: 'POST', path: '/orders', description: 'ثبت سفارش OTC'},
    ],
    note: 'همین API از طریق مسیر سازگاری /api/v1/trade/ نیز در دسترس است.',
  },
  {
    title: 'مسیر سازگاری Trade',
    basePath: '/api/v1/trade/',
    endpoints: [
      {method: 'POST', path: '/quotes', description: 'دریافت Quote خرید یا فروش'},
      {method: 'GET', path: '/quotes/<id>', description: 'دریافت جزئیات Quote'},
      {method: 'POST', path: '/orders', description: 'ثبت سفارش OTC'},
    ],
  },
  {
    title: 'سفارش‌ها',
    basePath: '/api/v1/orders/',
    endpoints: [
      {method: 'GET', path: '/', description: 'دریافت فهرست سفارش‌ها'},
      {method: 'GET', path: '/<id>/', description: 'دریافت جزئیات سفارش'},
      {method: 'POST', path: '/<id>/cancel', description: 'لغو سفارش'},
    ],
  },
  {
    title: 'معاملات اجراشده',
    basePath: '/api/v1/trades/',
    endpoints: [
      {method: 'GET', path: '/', description: 'دریافت فهرست معاملات'},
    ],
  },
  {
    title: 'تراکنش‌ها',
    basePath: '/api/v1/transactions/',
    endpoints: [
      {method: 'GET', path: '/', description: 'دریافت تاریخچه تراکنش‌ها'},
    ],
  },
  {
    title: 'احراز هویت KYC',
    basePath: '/api/v1/kyc/',
    endpoints: [
      {method: 'GET', path: '/', description: 'دریافت یا ایجاد پرونده KYC'},
      {method: 'POST', path: '/submit/', description: 'ارسال پرونده KYC'},
      {method: 'PUT', path: '/update/', description: 'به‌روزرسانی پرونده KYC'},
      {method: 'GET', path: '/status/', description: 'دریافت وضعیت KYC'},
      {method: 'GET', path: '/admin/', description: 'مدیریت پرونده‌های KYC توسط ادمین'},
      {method: 'GET', path: '/admin/<pk>/', description: 'مشاهده جزئیات پرونده'},
      {method: 'POST', path: '/admin/<pk>/approve/', description: 'تأیید پرونده'},
      {method: 'POST', path: '/admin/<pk>/reject/', description: 'رد پرونده'},
    ],
  },
  {
    title: 'امنیت',
    basePath: '/api/v1/security/',
    endpoints: [
      {method: 'GET', path: '/', description: 'دریافت خلاصه امنیتی'},
      {method: 'GET', path: '/sessions/', description: 'دریافت نشست‌های فعال'},
      {method: 'DELETE', path: '/sessions/<session_id>/', description: 'لغو یک نشست'},
      {method: 'DELETE', path: '/sessions/others/', description: 'لغو سایر نشست‌ها'},
      {method: 'GET', path: '/events/', description: 'دریافت رویدادهای امنیتی'},
      {method: 'GET', path: '/login-history/', description: 'دریافت تاریخچه ورود'},
      {method: 'POST', path: '/password/', description: 'تغییر رمز عبور'},
      {method: 'POST', path: '/two-factor/setup/', description: 'راه‌اندازی 2FA'},
      {method: 'POST', path: '/two-factor/', description: 'مدیریت 2FA'},
      {method: 'POST', path: '/anti-phishing/', description: 'تنظیم کد ضد فیشینگ'},
      {method: 'GET', path: '/withdrawal-whitelist/', description: 'دریافت لیست سفید برداشت'},
    ],
  },
  {
    title: 'اعلان‌ها',
    basePath: '/api/v1/notifications/',
    endpoints: [
      {method: 'GET', path: '/', description: 'دریافت اعلان‌ها'},
      {method: 'GET', path: '/unread-count', description: 'دریافت تعداد اعلان‌های خوانده‌نشده'},
      {method: 'GET', path: '/<pk>', description: 'خوانده‌شدن یک اعلان'},
      {method: 'POST', path: '/read-all', description: 'علامت‌گذاری همه اعلان‌ها به‌عنوان خوانده‌شده'},
    ],
    note: 'سیستم اعلان‌ها در وضعیت فعلی هنوز کاملاً عملیاتی نشده است.',
  },
  {
    title: 'پشتیبانی',
    basePath: '/api/v1/support/',
    endpoints: [
      {method: 'GET', path: '/faqs', description: 'دریافت FAQها'},
      {method: 'GET', path: '/tickets', description: 'دریافت تیکت‌ها'},
      {method: 'POST', path: '/tickets', description: 'ایجاد تیکت'},
      {method: 'GET', path: '/tickets/<pk>', description: 'مشاهده جزئیات تیکت'},
      {method: 'POST', path: '/tickets/<pk>/messages', description: 'ارسال پیام در تیکت'},
      {method: 'POST', path: '/tickets/<pk>/close', description: 'بستن تیکت'},
    ],
  },
  {
    title: 'بازارها',
    basePath: '/api/v1/markets',
    endpoints: [
      {method: 'GET', path: '/', description: 'دریافت فهرست بازارها'},
    ],
    note: 'این Endpoint احراز هویت می‌خواهد و داده‌های فعلی بازار برای محیط توسعه و تست هستند.',
  },
  {
    title: 'مستندات API',
    endpoints: [
      {method: 'GET', path: '/api/schema/', description: 'دریافت OpenAPI Schema'},
      {method: 'GET', path: '/api/docs/', description: 'باز کردن Swagger UI'},
    ],
  },
]

const integrationItems: IntegrationItem[] = [
  {
    status: 'done',
    title: 'احراز هویت و JWT',
    description: 'پیاده‌سازی و تست اولیه انجام شده است.',
  },
  {
    status: 'done',
    title: 'تنظیمات و امنیت',
    description: 'APIهای Preferences و Security یکپارچه شده‌اند.',
  },
  {
    status: 'done',
    title: 'حساب‌های بانکی',
    description: 'مدیریت حساب بانکی با Frontend یکپارچه شده است.',
  },
  {
    status: 'done',
    title: 'خلاصه Verification',
    description: 'Summary یکپارچه شده، اما فرآیند کامل KYC Production هنوز آماده نیست.',
  },
  {
    status: 'done',
    title: 'کیف پول',
    description: 'Wallet summary پیاده‌سازی و تست شده است.',
  },
  {
    status: 'done',
    title: 'بازارها',
    description: 'API بازار و اتصال آن به Frontend تست شده است.',
  },
  {
    status: 'done',
    title: 'سفارش‌ها',
    description: 'لیست و جریان اولیه سفارش‌ها یکپارچه شده است.',
  },
  {
    status: 'done',
    title: 'تراکنش‌ها',
    description: 'API لیست تراکنش‌ها یکپارچه و تست شده است.',
  },
  {
    status: 'done',
    title: 'پشتیبانی',
    description: 'APIهای FAQ و Ticket یکپارچه شده‌اند.',
  },
  {
    status: 'done',
    title: 'Quoteهای OTC',
    description: 'دریافت Quote در سطح API تست شده است.',
  },
  {
    status: 'warning',
    title: 'اجرای کامل سفارش OTC',
    description: 'نیازمند تست و تکمیل منطق کسب‌وکار است.',
  },
  {
    status: 'warning',
    title: 'اعلان‌ها',
    description: 'در حال حاضر محدود و در سطح Stub هستند.',
  },
  {
    status: 'warning',
    title: 'Celery',
    description: 'پیکربندی شده، اما Taskهای Production کامل نشده‌اند.',
  },
  {
    status: 'todo',
    title: 'WebSocket و Real-time',
    description: 'قابلیت‌های Production هنوز پیاده‌سازی نشده‌اند.',
  },
  {
    status: 'todo',
    title: 'پرداخت و Blockchain',
    description: 'Integration مربوط به پرداخت و Blockchain هنوز پیاده‌سازی نشده است.',
  },
]

const workflowSteps = [
  {number: '01', title: 'Backend', description: 'راه‌اندازی محیط Backend و وابستگی‌ها'},
  {number: '02', title: 'Migration', description: 'اعمال Migrationهای دیتابیس'},
  {number: '03', title: 'API', description: 'اجرای سرور Django و API'},
  {number: '04', title: 'Frontend', description: 'اجرای Vite و رابط کاربری'},
  {number: '05', title: 'Integration', description: 'اتصال Frontend به APIها'},
  {number: '06', title: 'Testing', description: 'تست صفحه، API و جریان‌ها'},
]

const backendEnvironment = [
  'DJANGO_SECRET_KEY',
  'DJANGO_DEBUG',
  'DJANGO_ALLOWED_HOSTS',
  'USE_SQLITE_FOR_DEV',
  'DATABASE_NAME',
  'DATABASE_USER',
  'DATABASE_PASSWORD',
  'DATABASE_HOST',
  'DATABASE_PORT',
  'CORS_ALLOWED_ORIGINS',
  'REDIS_URL',
  'REDIS_CACHE_URL',
  'JWT_ACCESS_MINUTES',
  'JWT_REFRESH_DAYS',
  'JWT_IDLE_TIMEOUT_SECONDS',
  'SMS_PROVIDER',
]

const frontendEnvironment = [
  'VITE_API_BASE_URL',
  'VITE_USE_MOCK_API',
]

const isCopied = (path: string) => copiedPath.value === path

async function copyEndpoint(path: string): Promise<void> {
  try {
    await navigator.clipboard.writeText(path)
    copiedPath.value = path

    window.setTimeout(() => {
      if (copiedPath.value === path) {
        copiedPath.value = null
      }
    }, 1400)
  } catch {
    copiedPath.value = null
  }
}

const scrollToSection = async (id: string) => {
  activeSection.value = id
  tocOpen.value = false

  await nextTick()

  document.getElementById(id)?.scrollIntoView({
    behavior: 'smooth',
    block: 'start',
  })
}

let observer: IntersectionObserver | null = null

function setupSectionObserver(): void {
  observer?.disconnect()

  const elements = sections
      .map(({id}) => document.getElementById(id))
      .filter((element): element is HTMLElement => Boolean(element))

  if (!elements.length) return

  observer = new IntersectionObserver(
      (entries) => {
        const visible = entries
            .filter((entry) => entry.isIntersecting)
            .sort((a, b) => b.intersectionRatio - a.intersectionRatio)

        if (visible[0]) {
          activeSection.value = visible[0].target.id
        }
      },
      {
        root: null,
        rootMargin: '-18% 0px -68% 0px',
        threshold: [0.05, 0.2, 0.5, 0.8],
      },
  )

  elements.forEach((element) => observer?.observe(element))
}

watch(tocOpen, (isOpen) => {
  document.body.classList.toggle('docs-toc-open', isOpen)
})

onMounted(() => {
  setupSectionObserver()
})

onBeforeUnmount(() => {
  observer?.disconnect()
  document.body.classList.remove('docs-toc-open')
})
</script>

<template>
  <div class="docs-page">
    <section class="docs-hero">
      <div class="docs-hero__glow" aria-hidden="true"/>

      <div class="docs-hero__top">
        <span class="docs-eyebrow">
          <span class="docs-eyebrow__dot"/>
          مستندات فنی پلتفرم
        </span>

        <div class="docs-hero__actions">
          <a
              :href="apiDocsUrl"
              target="_blank"
              rel="noopener noreferrer"
              class="docs-action docs-action--primary"
          >
            <AppIcon name="external" :size="18"/>
            <span>Swagger API</span>
          </a>

          <a
              :href="apiSchemaUrl"
              target="_blank"
              rel="noopener noreferrer"
              class="docs-action"
          >
            <AppIcon name="code" :size="18"/>
            <span>OpenAPI Schema</span>
          </a>
        </div>
      </div>

      <div class="docs-hero__body">
        <div class="docs-hero__copy">
          <h1>مستندات OTC Exchange</h1>

          <p>
            راهنمای فنی معماری، APIها و وضعیت توسعه پلتفرم خرید و فروش
            رمزارز OTC.
          </p>

          <div class="docs-status-row">
            <span class="docs-status docs-status--info">
              در حال توسعه و یکپارچه‌سازی
            </span>

            <span class="docs-status docs-status--danger">
              آماده Production نیست
            </span>
          </div>
        </div>

        <div class="docs-hero__facts">
          <div class="hero-fact">
            <span>Backend</span>
            <strong>Django + DRF</strong>
          </div>

          <div class="hero-fact">
            <span>Frontend</span>
            <strong>Vue 3 + TypeScript</strong>
          </div>

          <div class="hero-fact">
            <span>API</span>
            <strong>REST + OpenAPI</strong>
          </div>
        </div>
      </div>
    </section>

    <div class="docs-layout">
      <main class="docs-main">
        <section id="overview" class="docs-section">
          <div class="section-heading">
            <span class="section-heading__index">01</span>

            <div>
              <h2>معرفی پروژه</h2>
            </div>
          </div>

          <div class="overview-grid">
            <div class="overview-copy">
              <p>
                OTC Exchange یک پلتفرم خرید و فروش رمزارز با معماری مستقل
                Frontend و Backend است. کاربران می‌توانند از طریق Quoteهای OTC
                خرید و فروش انجام دهند، کیف پول خود را مدیریت کنند، سفارش‌ها
                و تراکنش‌ها را مشاهده کنند و فرآیند احراز هویت را دنبال کنند.
              </p>

              <div class="overview-points">
                <div class="overview-point">
                  <span class="point-icon">
                    <AppIcon name="shield" :size="17"/>
                  </span>
                  <span>احراز هویت و کنترل دسترسی مبتنی بر JWT</span>
                </div>

                <div class="overview-point">
                  <span class="point-icon">
                    <AppIcon name="wallet" :size="17"/>
                  </span>
                  <span>مدیریت کیف پول، سفارش و تراکنش</span>
                </div>

                <div class="overview-point">
                  <span class="point-icon">
                    <AppIcon name="code" :size="17"/>
                  </span>
                  <span>API مستقل برای اتصال Frontend و Backend</span>
                </div>
              </div>
            </div>

            <div class="architecture">
              <div class="architecture__label">معماری کلی</div>

              <div class="architecture__flow">
                <div class="architecture__node">
                  <strong>Vue 3</strong>
                  <span>Frontend</span>
                </div>

                <div class="architecture__arrow">↓</div>

                <div class="architecture__node architecture__node--accent">
                  <strong>REST API</strong>
                  <span>Django REST Framework</span>
                </div>

                <div class="architecture__arrow">↓</div>

                <div class="architecture__node">
                  <strong>Data Layer</strong>
                  <span>PostgreSQL / Redis</span>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section id="tech-stack" class="docs-section">
          <div class="section-heading">
            <span class="section-heading__index">02</span>

            <div>
              <h2>فناوری‌های استفاده‌شده</h2>
            </div>
          </div>

          <div class="tech-grid">
            <article
                v-for="tech in techItems"
                :key="tech.name"
                class="tech-card"
            >
              <div class="tech-card__top">
                <span class="tech-card__icon">
                  <AppIcon :name="tech.icon" :size="19"/>
                </span>

                <span class="tech-card__version">
                  {{ tech.version }}
                </span>
              </div>

              <strong>{{ tech.name }}</strong>
              <span>{{ tech.role }}</span>
            </article>
          </div>
        </section>

        <section id="backend" class="docs-section">
          <div class="section-heading">
            <span class="section-heading__index">03</span>

            <div>
              <h2>معماری Backend</h2>
            </div>
          </div>

          <div class="module-header">
            <div>
              <h3>Django Apps</h3>
              <p>
                {{ backendApps.length }} ماژول مستقل در
                <code>backend/apps/</code>
              </p>
            </div>

            <span class="module-count">
              {{ backendApps.length }} Modules
            </span>
          </div>

          <div class="apps-grid">
            <article
                v-for="app in backendApps"
                :key="app.name"
                class="app-card"
            >
              <div class="app-card__header">
                <code>{{ app.name }}</code>
                <AppIcon name="chevronLeft" :size="16"/>
              </div>

              <p>{{ app.description }}</p>

              <div class="app-card__tags">
                <span
                    v-for="feature in app.features"
                    :key="feature"
                >
                  {{ feature }}
                </span>
              </div>
            </article>
          </div>

          <div class="info-strip">
            <AppIcon name="info" :size="18"/>
            <span>
              مدل‌ها و مسیرهای اصلی پیاده‌سازی شده‌اند، اما یکپارچه‌سازی API و
              منطق کسب‌وکار همچنان در حال توسعه است.
            </span>
          </div>

          <div class="subsection">
            <div class="subsection-heading">
              <div>
                <span class="      ">API</span>
                <h3>مرجع Endpointها</h3>
              </div>

              <code>/api/v1/</code>
            </div>

            <div class="api-groups">
              <article
                  v-for="section in apiSections"
                  :key="section.title"
                  class="api-group"
              >
                <div class="api-group__header">
                  <div>
                    <h4>{{ section.title }}</h4>

                    <code v-if="section.basePath">
                      {{ section.basePath }}
                    </code>
                  </div>
                </div>

                <div class="api-table">
                  <div
                      v-for="endpoint in section.endpoints"
                      :key="`${section.title}-${endpoint.method}-${endpoint.path}`"
                      class="api-row"
                  >
                    <span
                        class="api-method"
                        :class="`api-method--${endpoint.method.toLowerCase()}`"
                    >
                      {{ endpoint.method }}
                    </span>

                    <code class="api-path">
                      {{ endpoint.path }}
                    </code>

                    <span class="api-description">
                      {{ endpoint.description }}
                    </span>

                    <button
                        type="button"
                        class="copy-button"
                        :aria-label="`کپی ${endpoint.path}`"
                        @click="copyEndpoint(endpoint.path)"
                    >
                      <AppIcon
                          :name="isCopied(endpoint.path) ? 'check' : 'copy'"
                          :size="16"
                      />
                      <span>
                        {{ isCopied(endpoint.path) ? 'کپی شد' : 'کپی' }}
                      </span>
                    </button>
                  </div>
                </div>

                <div v-if="section.note" class="api-note">
                  <AppIcon name="info" :size="16"/>
                  <span>{{ section.note }}</span>
                </div>
              </article>
            </div>
          </div>

          <div class="subsection">
            <div class="subsection-heading">
              <div>
                <span class="      ">Security</span>
                <h3>احراز هویت</h3>
              </div>
            </div>

            <div class="data-list">
              <div class="data-row">
                <span>شناسه اصلی</span>
                <strong>شماره موبایل</strong>
              </div>

              <div class="data-row">
                <span>تأیید هویت</span>
                <strong>SMS OTP</strong>
              </div>

              <div class="data-row">
                <span>Access Token</span>
                <strong>۱۵ دقیقه</strong>
              </div>

              <div class="data-row">
                <span>Refresh Token</span>
                <strong>۷ روز</strong>
              </div>

              <div class="data-row">
                <span>Idle Timeout</span>
                <strong>۳۰ دقیقه</strong>
              </div>

              <div class="data-row">
                <span>Session Storage</span>
                <strong>Redis</strong>
              </div>

              <div class="data-row">
                <span>Authentication Class</span>
                <code>IdleTimeoutJWTAuthentication</code>
              </div>
            </div>
          </div>

          <div class="backend-meta-grid">
            <div class="meta-panel">
              <div class="meta-panel__header">
                <h3>Database</h3>
                <span>DB</span>
              </div>

              <div class="data-list">
                <div class="data-row">
                  <span>Production</span>
                  <strong>PostgreSQL</strong>
                </div>

                <div class="data-row">
                  <span>Development</span>
                  <strong>SQLite</strong>
                </div>

                <div class="data-row">
                  <span>Migration</span>
                  <strong>در حال توسعه</strong>
                </div>
              </div>
            </div>

            <div class="meta-panel">
              <div class="meta-panel__header">
                <h3>Celery</h3>
                <span>QUEUE</span>
              </div>

              <div class="data-list">
                <div class="data-row">
                  <span>Broker</span>
                  <strong>Redis</strong>
                </div>

                <div class="data-row">
                  <span>Serialization</span>
                  <strong>JSON</strong>
                </div>

                <div class="data-row">
                  <span>وضعیت</span>
                  <strong>Taskها ناقص</strong>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section id="frontend" class="docs-section">
          <div class="section-heading">
            <span class="section-heading__index">04</span>

            <div>
              <h2>معماری Frontend</h2>
            </div>
          </div>

          <div class="structure-layout">
            <div>
              <div class="subsection-heading">
                <div>
                  <span class="subsection-heading__eyebrow">Structure</span>
                  <h3>ساختار پروژه</h3>
                </div>
              </div>

              <div class="structure-grid">
                <div class="structure-item">
                  <code>src/pages/</code>
                  <span>صفحه‌های احراز هویت و اپلیکیشن</span>
                </div>

                <div class="structure-item">
                  <code>src/components/</code>
                  <span>کامپوننت‌های قابل استفاده مجدد</span>
                </div>

                <div class="structure-item">
                  <code>src/router/</code>
                  <span>مدیریت مسیرها</span>
                </div>

                <div class="structure-item">
                  <code>src/stores/</code>
                  <span>مدیریت State با Pinia</span>
                </div>

                <div class="structure-item">
                  <code>src/services/</code>
                  <span>لایه ارتباط با API</span>
                </div>

                <div class="structure-item">
                  <code>src/types/</code>
                  <span>تعریف TypeScript Types</span>
                </div>

                <div class="structure-item">
                  <code>src/utils/</code>
                  <span>توابع و ابزارهای عمومی</span>
                </div>
              </div>
            </div>

            <div class="frontend-features">
              <div class="subsection-heading">
                <div>
                  <span class="subsection-heading__eyebrow">Experience</span>
                  <h3>ویژگی‌های کلیدی</h3>
                </div>
              </div>

              <div class="feature-pills">
                <span>رابط فارسی و RTL</span>
                <span>Mock API</span>
                <span>JWT Auto Refresh</span>
                <span>Route Guards</span>
                <span>Responsive</span>
                <span>API Error Handling</span>
              </div>
            </div>
          </div>

          <div class="build-panel">
            <div class="subsection-heading">
              <div>
                <span class="subsection-heading__eyebrow">Build</span>
                <h3>Build Configuration</h3>
              </div>
            </div>

            <div class="data-list">
              <div class="data-row">
                <span>Development</span>
                <strong>Vite + HMR</strong>
              </div>

              <div class="data-row">
                <span>Production</span>
                <strong>TypeScript Build</strong>
              </div>

              <div class="data-row">
                <span>Target</span>
                <strong>ES2020</strong>
              </div>
            </div>
          </div>
        </section>

        <section id="integration" class="docs-section">
          <div class="section-heading">
            <span class="section-heading__index">05</span>

            <div>
              <h2>وضعیت یکپارچه‌سازی</h2>
            </div>
          </div>

          <div class="integration-summary">
            <div class="integration-summary__item integration-summary__item--done">
              <span class="integration-summary__icon">
                <AppIcon name="check" :size="17"/>
              </span>

              <div>
                <strong>یکپارچه و تست‌شده</strong>
                <span>بخش‌های اصلی اتصال Frontend و Backend</span>
              </div>
            </div>

            <div class="integration-summary__item integration-summary__item--warning">
              <span class="integration-summary__icon">
                <AppIcon name="warning" :size="17"/>
              </span>

              <div>
                <strong>نیازمند تست یا توسعه بیشتر</strong>
                <span>بخش‌هایی که هنوز منطق کامل ندارند</span>
              </div>
            </div>

            <div class="integration-summary__item integration-summary__item--todo">
              <span class="integration-summary__icon">
                <AppIcon name="clock" :size="17"/>
              </span>

              <div>
                <strong>پیاده‌سازی نشده</strong>
                <span>قابلیت‌های Production آینده</span>
              </div>
            </div>
          </div>

          <div class="integration-list">
            <article
                v-for="item in integrationItems"
                :key="item.title"
                class="integration-row"
                :class="`integration-row--${item.status}`"
            >
              <span class="integration-row__icon">
                <AppIcon
                    :name="item.status === 'done' ? 'check' : item.status === 'warning' ? 'warning' : 'clock'"
                    :size="17"
                />
              </span>

              <div class="integration-row__content">
                <strong>{{ item.title }}</strong>
                <span>{{ item.description }}</span>
              </div>

              <span class="integration-row__status">
                {{
                  item.status === 'done'
                      ? 'تکمیل'
                      : item.status === 'warning'
                          ? 'در حال توسعه'
                          : 'آینده'
                }}
              </span>
            </article>
          </div>
        </section>

        <section id="workflow" class="docs-section">
          <div class="section-heading">
            <span class="section-heading__index">06</span>

            <div>

              <h2>گردش کار توسعه</h2>
            </div>
          </div>

          <div class="workflow">
            <div
                v-for="(step, index) in workflowSteps"
                :key="step.number"
                class="workflow-step"
            >
              <span class="workflow-step__number">{{ step.number }}</span>

              <div>
                <strong>{{ step.title }}</strong>
                <span>{{ step.description }}</span>
              </div>

              <AppIcon
                  v-if="index !== workflowSteps.length - 1"
                  name="chevronLeft"
                  :size="18"
                  class="workflow-step__arrow"
              />
            </div>
          </div>

          <div class="command-grid">
            <div class="command-panel">
              <div class="command-panel__header">
                <div>
                  <span>Backend</span>
                  <strong>راه‌اندازی محیط Django</strong>
                </div>
              </div>

              <pre><code>cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver</code></pre>
            </div>

            <div class="command-panel">
              <div class="command-panel__header">
                <div>
                  <span>Frontend</span>
                  <strong>راه‌اندازی محیط Vue</strong>
                </div>
              </div>

              <pre><code>cd frontend
npm install
npm run dev</code></pre>
            </div>

            <div class="command-panel command-panel--wide">
              <div class="command-panel__header">
                <div>
                  <span>Mock API</span>
                  <strong>اجرای Frontend با داده آزمایشی</strong>
                </div>
              </div>

              <pre><code>VITE_USE_MOCK_API=true npm run dev</code></pre>
            </div>
          </div>

          <div class="environment-panel">
            <div class="subsection-heading">
              <div>
                <span class="subsection-heading__eyebrow">Environment</span>
                <h3>متغیرهای محیطی</h3>
              </div>
            </div>

            <div class="environment-columns">
              <div>
                <span class="environment-title">Backend</span>

                <div class="environment-list">
                  <code
                      v-for="item in backendEnvironment"
                      :key="item"
                  >
                    {{ item }}
                  </code>
                </div>
              </div>

              <div>
                <span class="environment-title">Frontend</span>

                <div class="environment-list">
                  <code
                      v-for="item in frontendEnvironment"
                      :key="item"
                  >
                    {{ item }}
                  </code>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section id="notes" class="docs-section">
          <div class="section-heading">
            <span class="section-heading__index">07</span>

            <div>
              <h2>نکات مهم</h2>
            </div>
          </div>

          <div class="notice">
            <div class="notice__icon">
              <AppIcon name="warning" :size="22"/>
            </div>

            <div class="notice__content">
              <span class="notice__label">وضعیت فعلی پروژه</span>

              <h3>
                پروژه در مرحله توسعه و یکپارچه‌سازی است و برای Production آماده
                نیست.
              </h3>

              <div class="notice__list">
                <div>قابلیت‌های امنیتی نیازمند تست و Audit بیشتر هستند.</div>
                <div>پرداخت و Blockchain هنوز پیاده‌سازی نشده‌اند.</div>
                <div>Real-time Production هنوز پیاده‌سازی نشده است.</div>
                <div>تست Performance و Load Testing انجام نشده است.</div>
                <div>تنظیم Production مربوط به SMS Provider باقی مانده است.</div>
                <div>فرآیند کامل Production برای KYC هنوز تکمیل نشده است.</div>
              </div>
            </div>
          </div>

          <div class="docs-cta">
            <div>
              <span>API Documentation</span>
              <h3>APIهای Backend را مستقیم تست کن</h3>
              <p>
                برای مشاهده Schema و اجرای مستقیم Endpointها از Swagger
                استفاده کن.
              </p>
            </div>

            <div class="docs-cta__actions">
              <a
                  :href="apiDocsUrl"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="docs-action docs-action--primary"
              >
                <AppIcon name="external" :size="18"/>
                <span>باز کردن Swagger</span>
              </a>

              <a
                  :href="apiSchemaUrl"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="docs-action"
              >
                <AppIcon name="code" :size="18"/>
                <span>مشاهده OpenAPI</span>
              </a>
            </div>
          </div>
        </section>
      </main>

      <aside class="docs-sidebar">
        <button
            type="button"
            class="sidebar-mobile-toggle"
            :aria-expanded="tocOpen"
            @click="tocOpen = !tocOpen"
        >
          <span>
            <AppIcon name="menu" :size="18"/>
            فهرست مطالب
          </span>

          <AppIcon
              :name="tocOpen ? 'chevronUp' : 'chevronDown'"
              :size="17"
          />
        </button>

        <nav
            class="sidebar-nav"
            :class="{ 'sidebar-nav--open': tocOpen }"
            aria-label="فهرست مطالب"
        >
          <div class="sidebar-nav__label">در این صفحه</div>

          <button
              v-for="(section, index) in sections"
              :key="section.id"
              type="button"
              class="sidebar-link"
              :class="{ 'sidebar-link--active': activeSection === section.id }"
              @click="scrollToSection(section.id)"
          >
            <span>{{ String(index + 1).padStart(2, '0') }}</span>
            <strong>{{ section.title }}</strong>
          </button>
        </nav>
      </aside>
    </div>
  </div>
</template>


<style scoped>
.docs-page {
  width: min(100%, 1380px);
  margin-inline: auto;
  padding: 2rem var(--page-gutter) 5rem;
  direction: rtl;
}

/* =========================================================
   HERO
   ========================================================= */

.docs-hero {
  position: relative;
  overflow: hidden;
  margin-bottom: 3rem;
  padding: clamp(1.5rem, 3vw, 2.5rem);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  background: linear-gradient(
      145deg,
      color-mix(in srgb, var(--color-primary-soft) 78%, transparent),
      transparent 62%
  ),
  var(--surface-primary);
  box-shadow: var(--shadow-sm);
}

.docs-hero__glow {
  position: absolute;
  inset-block-start: -8rem;
  inset-inline-end: -6rem;
  width: 20rem;
  height: 20rem;
  border-radius: 50%;
  background: color-mix(in srgb, var(--color-primary) 10%, transparent);
  filter: blur(24px);
  pointer-events: none;
}

.docs-hero__top,
.docs-hero__body {
  position: relative;
  z-index: 1;
}

.docs-hero__top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 2rem;
}

.docs-eyebrow {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  color: var(--color-primary);
  font-size: var(--font-size-sm);
  font-weight: 700;
}

.docs-eyebrow__dot {
  width: 0.5rem;
  height: 0.5rem;
  flex: 0 0 auto;
  border-radius: 50%;
  background: var(--color-success);
  box-shadow: 0 0 0 0.3rem var(--color-success-soft);
}

.docs-hero__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.6rem;
}

.docs-action {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  min-height: 2.65rem;
  padding-inline: 1rem;
  border: 1px solid var(--control-border);
  border-radius: var(--radius-md);
  background: var(--surface-secondary);
  color: var(--text-primary);
  font-size: var(--font-size-sm);
  font-weight: 650;
  box-shadow: var(--shadow-xs);
  transition: background var(--transition-fast),
  border-color var(--transition-fast),
  transform var(--transition-fast),
  box-shadow var(--transition-fast);
}

.docs-action:hover {
  border-color: var(--color-border-hover);
  background: var(--surface-tertiary);
}

.docs-action:active {
  transform: translateY(1px);
}

.docs-action--primary {
  border-color: color-mix(in srgb, var(--color-primary) 20%, transparent);
  background: var(--action-primary);
  color: var(--on-primary);
  box-shadow: 0 8px 22px var(--color-primary-shadow);
}

.docs-action--primary:hover {
  background: var(--action-primary-hover);
}

.docs-hero__body {
  display: grid;
  grid-template-columns: minmax(0, 1.5fr) minmax(18rem, 0.75fr);
  gap: 3rem;
  align-items: end;
}

.docs-hero__copy {
  min-width: 0;
}

.docs-hero__copy h1 {
  max-width: 50rem;
  margin: 0 0 0.85rem;
  font-size: clamp(2rem, 4vw, 3.35rem);
  font-weight: 800;
  letter-spacing: -0.035em;
  line-height: 1.18;
}

.docs-hero__copy p {
  max-width: 46rem;
  margin: 0 0 1.25rem;
  color: var(--text-secondary);
  font-size: clamp(1rem, 1.45vw, 1.1rem);
  line-height: 1.95;
}

.docs-status-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.docs-status {
  display: inline-flex;
  align-items: center;
  min-height: 2rem;
  padding-inline: 0.75rem;
  border-radius: var(--radius-pill);
  font-size: var(--font-size-xs);
  font-weight: 700;
}

.docs-status--info {
  background: var(--color-info-soft);
  color: var(--color-info);
}

.docs-status--danger {
  background: var(--color-danger-soft);
  color: var(--color-danger);
}

.docs-hero__facts {
  display: grid;
  gap: 0.6rem;
}

.hero-fact {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  min-width: 0;
  padding: 0.8rem 0.95rem;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  background: color-mix(in srgb, var(--surface-secondary) 82%, transparent);
}

.hero-fact span {
  color: var(--text-muted);
  font-size: var(--font-size-xs);
}

.hero-fact strong {
  color: var(--text-primary);
  font-size: var(--font-size-sm);
  text-align: end;
}

/* =========================================================
   PAGE LAYOUT
   ========================================================= */

.docs-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 18rem;
  gap: clamp(1.5rem, 3vw, 3.5rem);
  align-items: start;
}

.docs-main {
  min-width: 0;
  grid-column: 1;
}

.docs-sidebar {
  min-width: 0;
  grid-column: 2;
  position: sticky;
  top: calc(var(--header-height) + 1.25rem);
}

.sidebar-mobile-toggle {
  display: none;
}

.sidebar-nav {
  margin: 0;
  padding: 0.65rem;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--surface-primary);
  box-shadow: var(--shadow-xs);
}

.sidebar-nav__label {
  margin: 0.4rem 0.55rem 0.65rem;
  color: var(--text-muted);
  font-size: var(--font-size-xs);
  font-weight: 700;
}

.sidebar-link {
  position: relative;
  display: grid;
  grid-template-columns: 1.9rem minmax(0, 1fr);
  align-items: center;
  width: 100%;
  gap: 0.55rem;
  padding: 0.7rem;
  border: 0;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--text-secondary);
  text-align: start;
  transition: background var(--transition-fast),
  color var(--transition-fast);
}

.sidebar-link span {
  color: var(--text-muted);
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 0.68rem;
  font-weight: 700;
  direction: ltr;
}

.sidebar-link strong {
  min-width: 0;
  font-size: var(--font-size-sm);
  font-weight: 600;
  line-height: 1.6;
}

.sidebar-link:hover {
  background: var(--surface-secondary);
  color: var(--text-primary);
}

.sidebar-link--active {
  background: var(--color-primary-soft);
  color: var(--color-primary);
}

.sidebar-link--active span {
  color: var(--color-primary);
}

.sidebar-link--active::before {
  position: absolute;
  inset-block: 0.5rem;
  inset-inline-end: 0;
  width: 2px;
  border-radius: 999px;
  background: var(--color-primary);
  content: '';
}

/* =========================================================
   SECTIONS
   ========================================================= */

.docs-section {
  scroll-margin-top: calc(var(--header-height) + 2rem);
  margin-bottom: clamp(4rem, 6vw, 5.5rem);
}

.docs-section:last-child {
  margin-bottom: 0;
}

.section-heading {
  display: flex;
  align-items: flex-start;
  justify-content: flex-start;
  width: 100%;
  gap: 0.85rem;
  margin-bottom: 1.75rem;
}

.section-heading > div {
  display: flex;
  align-items: baseline;
  gap: 0.7rem;
  min-width: 0;
  flex: 1;
}

.section-heading__index {
  display: grid;
  width: 2.6rem;
  height: 2.6rem;
  flex: 0 0 auto;
  place-items: center;
  border: 1px solid var(--color-primary-border);
  border-radius: var(--radius-md);
  background: var(--color-primary-soft);
  color: var(--color-primary);
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: var(--font-size-xs);
  font-weight: 800;
  direction: ltr;
}

.subsection-heading__eyebrow {
  order: 2;
  display: inline-block;
  margin: 0;
  flex: 0 0 auto;
  color: var(--color-primary);
  font-size: 0.68rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  direction: ltr;
}

.section-heading h2 {
  order: 1;
  margin: 0;
  color: var(--text-primary);
  font-size: clamp(1.45rem, 2vw, 1.95rem);
  font-weight: 750;
  letter-spacing: -0.018em;
  line-height: 1.35;
}

/* =========================================================
   COMMON SUBSECTION
   ========================================================= */

.subsection {
  margin-top: 3rem;
}

.subsection-heading {
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 1rem;
}

.subsection-heading h3 {
  margin: 0;
  color: var(--text-primary);
  font-size: 1.2rem;
  font-weight: 750;
  line-height: 1.45;
}

.subsection-heading > code {
  flex: 0 0 auto;
  padding: 0.4rem 0.65rem;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  background: var(--surface-secondary);
  color: var(--color-primary);
  font-size: 0.7rem;
  direction: ltr;
}

/* =========================================================
   OVERVIEW
   ========================================================= */

.overview-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.1fr) minmax(20rem, 0.85fr);
  gap: 1.5rem;
}

.overview-copy {
  min-width: 0;
  padding-block: 0.25rem;
}

.overview-copy > p {
  margin: 0 0 1.25rem;
  color: var(--text-secondary);
  line-height: 2;
}

.overview-points {
  display: grid;
  gap: 0.55rem;
}

.overview-point {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  min-width: 0;
  padding: 0.75rem 0.8rem;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  background: var(--surface-secondary);
  color: var(--text-secondary);
  font-size: var(--font-size-sm);
  line-height: 1.7;
}

.point-icon {
  display: grid;
  width: 2rem;
  height: 2rem;
  flex: 0 0 auto;
  place-items: center;
  border-radius: var(--radius-sm);
  background: var(--color-primary-soft);
  color: var(--color-primary);
}

.architecture {
  min-width: 0;
  padding: 1.25rem;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--surface-secondary);
}

.architecture__label {
  margin-bottom: 1rem;
  color: var(--text-muted);
  font-size: var(--font-size-xs);
  font-weight: 700;
}

.architecture__flow {
  display: grid;
  gap: 0.5rem;
}

.architecture__node {
  padding: 0.8rem 1rem;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  background: var(--surface-primary);
  text-align: center;
}

.architecture__node strong,
.architecture__node span {
  display: block;
}

.architecture__node strong {
  color: var(--text-primary);
  font-size: var(--font-size-sm);
}

.architecture__node span {
  margin-top: 0.15rem;
  color: var(--text-muted);
  font-size: var(--font-size-xs);
}

.architecture__node--accent {
  border-color: var(--color-primary-border);
  background: var(--color-primary-soft);
}

.architecture__node--accent strong {
  color: var(--color-primary);
}

.architecture__arrow {
  color: var(--color-primary);
  font-size: 1rem;
  line-height: 1;
  text-align: center;
}

/* =========================================================
   TECH STACK
   ========================================================= */

.tech-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 0.75rem;
}

.tech-card {
  min-width: 0;
  padding: 1rem;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  background: var(--surface-primary);
  box-shadow: var(--shadow-xs);
  transition: border-color var(--transition-fast),
  background var(--transition-fast),
  transform var(--transition-fast),
  box-shadow var(--transition-fast);
}

.tech-card:hover {
  border-color: var(--color-border-hover);
  background: var(--surface-secondary);
  box-shadow: var(--shadow-sm);
  transform: translateY(-2px);
}

.tech-card__top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  margin-bottom: 0.9rem;
}

.tech-card__icon {
  display: grid;
  width: 2.25rem;
  height: 2.25rem;
  flex: 0 0 auto;
  place-items: center;
  border-radius: var(--radius-sm);
  background: var(--color-primary-soft);
  color: var(--color-primary);
}

.tech-card__version {
  min-width: 0;
  overflow: hidden;
  color: var(--text-muted);
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 0.6rem;
  text-overflow: ellipsis;
  white-space: nowrap;
  direction: ltr;
}

.tech-card strong,
.tech-card > span {
  display: block;
}

.tech-card strong {
  color: var(--text-primary);
  font-size: var(--font-size-sm);
}

.tech-card > span {
  margin-top: 0.25rem;
  color: var(--text-muted);
  font-size: var(--font-size-xs);
  line-height: 1.55;
}

/* =========================================================
   BACKEND APPS
   ========================================================= */

.module-header {
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 1rem;
}

.module-header h3,
.module-header p {
  margin: 0;
}

.module-header h3 {
  color: var(--text-primary);
  font-size: 1.15rem;
}

.module-header p {
  margin-top: 0.25rem;
  color: var(--text-muted);
  font-size: var(--font-size-sm);
}

.module-count {
  flex: 0 0 auto;
  padding: 0.35rem 0.65rem;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-pill);
  background: var(--surface-secondary);
  color: var(--text-muted);
  font-size: var(--font-size-xs);
  direction: ltr;
}

.apps-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.75rem;
}

.app-card {
  display: flex;
  min-width: 0;
  flex-direction: column;
  padding: 1rem;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  background: var(--surface-secondary);
  transition: border-color var(--transition-fast),
  background var(--transition-fast);
}

.app-card:hover {
  border-color: var(--color-border-hover);
  background: var(--surface-primary);
}

.app-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

.app-card__header code {
  padding: 0;
  background: transparent;
  color: var(--color-primary);
  font-size: var(--font-size-sm);
  direction: ltr;
}

.app-card__header svg {
  color: var(--text-muted);
}

.app-card p {
  min-height: 3rem;
  margin: 0 0 0.85rem;
  color: var(--text-secondary);
  font-size: var(--font-size-xs);
  line-height: 1.75;
}

.app-card__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
  margin-top: auto;
}

.app-card__tags span {
  padding: 0.25rem 0.45rem;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  background: var(--surface-tertiary);
  color: var(--text-muted);
  font-size: 0.62rem;
  direction: ltr;
}

.info-strip,
.api-note {
  display: flex;
  align-items: flex-start;
  gap: 0.55rem;
  padding: 0.75rem 0.85rem;
  border: 1px solid var(--color-primary-border);
  border-radius: var(--radius-md);
  background: var(--color-primary-soft);
  color: var(--color-primary);
  font-size: var(--font-size-xs);
  line-height: 1.8;
}

.info-strip {
  margin-top: 1rem;
}

.info-strip :deep(svg),
.api-note :deep(svg) {
  flex: 0 0 auto;
  margin-top: 0.15rem;
}

/* =========================================================
   API
   ========================================================= */

.api-groups {
  display: grid;
  gap: 0;
  overflow: hidden;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  background: var(--surface-primary);
}

.api-group {
  background: var(--surface-primary);
}

.api-group + .api-group {
  border-top: 1px solid var(--border-subtle);
}

.api-group__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-width: 0;
  padding: 0.9rem 1rem;
  background: linear-gradient(
      90deg,
      color-mix(in srgb, var(--color-primary-soft) 42%, transparent),
      transparent 75%
  ),
  var(--surface-secondary);
  border-bottom: 1px solid var(--border-subtle);
}

.api-group__header h4 {
  margin: 0 0 0.2rem;
  color: var(--text-primary);
  font-size: var(--font-size-sm);
}

.api-group__header code {
  padding: 0;
  background: transparent;
  color: var(--color-primary);
  font-size: 0.7rem;
  direction: ltr;
}

.api-table {
  display: grid;
}

.api-row {
  display: grid;
  grid-template-columns: 4.4rem minmax(14rem, 1.1fr) minmax(12rem, 1fr) auto;
  gap: 0.8rem;
  align-items: center;
  min-width: 0;
  padding: 0.75rem 1rem;
  background: var(--surface-primary);
  transition: background var(--transition-fast);
}

.api-row + .api-row {
  border-top: 1px solid var(--border-subtle);
}

.api-row:hover {
  background: var(--surface-secondary);
}

.api-method {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 1.75rem;
  padding-inline: 0.45rem;
  border-radius: var(--radius-sm);
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 0.63rem;
  font-weight: 800;
  direction: ltr;
}

.api-method--get {
  background: var(--color-success-soft);
  color: var(--color-success);
}

.api-method--post {
  background: var(--color-primary-soft);
  color: var(--color-primary);
}

.api-method--put {
  background: var(--color-warning-soft);
  color: var(--color-warning);
}

.api-method--delete {
  background: var(--color-danger-soft);
  color: var(--color-danger);
}

.api-path {
  min-width: 0;
  overflow-wrap: anywhere;
  padding: 0;
  background: transparent;
  color: var(--text-primary);
  font-size: 0.7rem;
  line-height: 1.7;
  direction: ltr;
  text-align: left;
}

.api-description {
  min-width: 0;
  color: var(--text-muted);
  font-size: var(--font-size-xs);
  line-height: 1.65;
}

.copy-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.3rem;
  min-height: 2rem;
  padding-inline: 0.55rem;
  border: 1px solid transparent;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--text-muted);
  font-size: 0.63rem;
  white-space: nowrap;
}

.copy-button:hover {
  border-color: var(--border-subtle);
  background: var(--surface-tertiary);
  color: var(--text-primary);
}

.api-note {
  margin: 0.7rem 0.85rem 0.85rem;
  background: var(--surface-secondary);
  color: var(--text-muted);
}

/* =========================================================
   DATA LISTS
   ========================================================= */

.data-list {
  display: grid;
  overflow: hidden;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  background: var(--surface-primary);
}

.data-row {
  display: grid;
  grid-template-columns: minmax(9rem, 0.7fr) minmax(0, 1fr);
  gap: 1rem;
  align-items: center;
  min-width: 0;
  padding: 0.8rem 1rem;
}

.data-row + .data-row {
  border-top: 1px solid var(--border-subtle);
}

.data-row span {
  color: var(--text-muted);
  font-size: var(--font-size-sm);
}

.data-row strong,
.data-row code {
  min-width: 0;
  color: var(--text-primary);
  font-size: var(--font-size-sm);
  line-height: 1.7;
}

.data-row code {
  justify-self: start;
  overflow-wrap: anywhere;
  direction: ltr;
}

.backend-meta-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1rem;
  margin-top: 1rem;
}

.meta-panel,
.build-panel,
.environment-panel {
  min-width: 0;
  padding: 1.2rem;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  background: var(--surface-secondary);
  margin-top: 10px;
}

.meta-panel__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 1rem;
}

.meta-panel__header h3 {
  margin: 0;
  color: var(--text-primary);
  font-size: var(--font-size-md);
}

.meta-panel__header span {
  color: var(--text-muted);
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 0.62rem;
  direction: ltr;
}

/* =========================================================
   FRONTEND
   ========================================================= */

.structure-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.35fr) minmax(18rem, 0.8fr);
  gap: 1.5rem;
}

.structure-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.75rem;
}

.structure-item {
  min-width: 0;
  padding: 0.85rem;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  background: var(--surface-secondary);
}

.structure-item code {
  display: block;
  overflow-wrap: anywhere;
  padding: 0;
  margin-bottom: 0.3rem;
  background: transparent;
  color: var(--color-primary);
  font-size: 0.7rem;
  direction: ltr;
}

.structure-item span {
  color: var(--text-muted);
  font-size: var(--font-size-xs);
  line-height: 1.7;
}

.frontend-features {
  min-width: 0;
}

.feature-pills {
  display: flex;
  flex-wrap: wrap;
  gap: 0.45rem;
}

.feature-pills span {
  padding: 0.38rem 0.6rem;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-pill);
  background: var(--surface-secondary);
  color: var(--text-secondary);
  font-size: var(--font-size-xs);
}

/* =========================================================
   INTEGRATION
   ========================================================= */

.integration-summary {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.integration-summary__item {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  min-width: 0;
  padding: 1rem;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  background: var(--surface-secondary);
}

.integration-summary__icon {
  display: grid;
  width: 2.25rem;
  height: 2.25rem;
  flex: 0 0 auto;
  place-items: center;
  border-radius: var(--radius-sm);
}

.integration-summary__item--done .integration-summary__icon {
  background: var(--color-success-soft);
  color: var(--color-success);
}

.integration-summary__item--warning .integration-summary__icon {
  background: var(--color-warning-soft);
  color: var(--color-warning);
}

.integration-summary__item--todo .integration-summary__icon {
  background: var(--surface-tertiary);
  color: var(--text-muted);
}

.integration-summary__item strong,
.integration-summary__item span {
  display: block;
}

.integration-summary__item strong {
  color: var(--text-primary);
  font-size: var(--font-size-sm);
  line-height: 1.5;
}

.integration-summary__item > div > span {
  margin-top: 0.25rem;
  color: var(--text-muted);
  font-size: 0.7rem;
  line-height: 1.7;
}

.integration-list {
  display: grid;
  gap: 0.5rem;
}

.integration-row {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  gap: 0.75rem;
  align-items: center;
  min-width: 0;
  padding: 0.8rem 0.95rem;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  background: var(--surface-primary);
}

.integration-row__icon {
  display: grid;
  width: 2rem;
  height: 2rem;
  flex: 0 0 auto;
  place-items: center;
  border-radius: 50%;
}

.integration-row--done .integration-row__icon {
  background: var(--color-success-soft);
  color: var(--color-success);
}

.integration-row--warning .integration-row__icon {
  background: var(--color-warning-soft);
  color: var(--color-warning);
}

.integration-row--todo .integration-row__icon {
  background: var(--surface-tertiary);
  color: var(--text-muted);
}

.integration-row__content {
  min-width: 0;
}

.integration-row__content strong,
.integration-row__content span {
  display: block;
}

.integration-row__content strong {
  color: var(--text-primary);
  font-size: var(--font-size-sm);
  line-height: 1.55;
}

.integration-row__content span {
  margin-top: 0.15rem;
  color: var(--text-muted);
  font-size: var(--font-size-xs);
  line-height: 1.65;
}

.integration-row__status {
  flex: 0 0 auto;
  padding: 0.3rem 0.55rem;
  border-radius: var(--radius-pill);
  background: var(--surface-secondary);
  color: var(--text-muted);
  font-size: 0.62rem;
  white-space: nowrap;
}

.integration-row--done .integration-row__status {
  background: var(--color-success-soft);
  color: var(--color-success);
}

.integration-row--warning .integration-row__status {
  background: var(--color-warning-soft);
  color: var(--color-warning);
}

/* =========================================================
   WORKFLOW
   ========================================================= */

.workflow {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  overflow: hidden;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  background: var(--surface-primary);
}

.workflow-step {
  min-width: 0;
  padding: 1rem;
  background: var(--surface-primary);
}

.workflow-step + .workflow-step {
  border-inline-start: 1px solid var(--border-subtle);
}

.workflow-step__number {
  display: inline-flex;
  width: 2rem;
  height: 2rem;
  align-items: center;
  justify-content: center;
  margin-bottom: 0.7rem;
  border-radius: 50%;
  background: var(--color-primary-soft);
  color: var(--color-primary);
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 0.63rem;
  font-weight: 800;
  direction: ltr;
}

.workflow-step strong,
.workflow-step span {
  display: block;
}

.workflow-step strong {
  color: var(--text-primary);
  font-size: var(--font-size-sm);
  line-height: 1.5;
}

.workflow-step > div span {
  margin-top: 0.25rem;
  color: var(--text-muted);
  font-size: 0.68rem;
  line-height: 1.7;
}

.command-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1rem;
  margin-top: 1.5rem;
}

.command-panel {
  min-width: 0;
  overflow: hidden;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  background: var(--surface-secondary);
}

.command-panel--wide {
  grid-column: 1 / -1;
}

.command-panel__header {
  padding: 0.8rem 1rem;
  border-bottom: 1px solid var(--border-subtle);
}

.command-panel__header span,
.command-panel__header strong {
  display: block;
}

.command-panel__header span {
  margin-bottom: 0.2rem;
  color: var(--color-primary);
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 0.63rem;
  direction: ltr;
}

.command-panel__header strong {
  color: var(--text-primary);
  font-size: var(--font-size-sm);
  line-height: 1.5;
}

.command-panel pre {
  margin: 0;
  padding: 1rem;
  overflow-x: auto;
}

.command-panel code {
  display: block;
  width: max-content;
  min-width: 100%;
  padding: 0;
  background: transparent;
  color: var(--text-secondary);
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 0.7rem;
  line-height: 1.8;
  direction: ltr;
  text-align: left;
  white-space: pre;
}

.environment-panel {
  margin-top: 1.5rem;
}

.environment-columns {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1.5rem;
}

.environment-title {
  display: block;
  margin-bottom: 0.7rem;
  color: var(--text-primary);
  font-size: var(--font-size-sm);
  font-weight: 700;
}

.environment-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
}

.environment-list code {
  padding: 0.38rem 0.55rem;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  background: var(--surface-primary);
  color: var(--color-primary);
  font-size: 0.61rem;
  direction: ltr;
}

/* =========================================================
   NOTICE + CTA
   ========================================================= */

.notice {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: 1rem;
  padding: clamp(1rem, 2vw, 1.4rem);
  border: 1px solid color-mix(in srgb, var(--color-warning) 26%, transparent);
  border-radius: var(--radius-lg);
  background: linear-gradient(
      135deg,
      var(--color-warning-soft),
      transparent 70%
  ),
  var(--surface-primary);
}

.notice__icon {
  display: grid;
  width: 2.75rem;
  height: 2.75rem;
  place-items: center;
  border-radius: var(--radius-md);
  background: var(--color-warning);
  color: var(--color-bg-app);
}

.notice__content {
  min-width: 0;
}

.notice__label {
  display: block;
  margin-bottom: 0.25rem;
  color: var(--color-warning);
  font-size: 0.7rem;
  font-weight: 800;
}

.notice__content h3 {
  margin: 0 0 1rem;
  color: var(--text-primary);
  font-size: 1rem;
  font-weight: 700;
  line-height: 1.8;
}

.notice__list {
  display: grid;
  gap: 0.35rem;
}

.notice__list div {
  position: relative;
  padding-inline-start: 1rem;
  color: var(--text-secondary);
  font-size: var(--font-size-sm);
  line-height: 1.7;
}

.notice__list div::before {
  position: absolute;
  inset-inline-start: 0;
  inset-block-start: 0.68em;
  width: 0.3rem;
  height: 0.3rem;
  border-radius: 50%;
  background: var(--color-warning);
  content: '';
}

.docs-cta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1.5rem;
  margin-top: 1.5rem;
  padding: clamp(1rem, 2.4vw, 1.4rem);
  border: 1px solid var(--color-primary-border);
  border-radius: var(--radius-lg);
  background: linear-gradient(
      135deg,
      var(--color-primary-soft),
      transparent 72%
  ),
  var(--surface-primary);
}

.docs-cta > div:first-child {
  min-width: 0;
}

.docs-cta > div:first-child > span {
  color: var(--color-primary);
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 0.65rem;
  font-weight: 800;
  direction: ltr;
}

.docs-cta h3 {
  margin: 0.3rem 0;
  color: var(--text-primary);
  font-size: 1rem;
  line-height: 1.5;
}

.docs-cta p {
  margin: 0;
  color: var(--text-muted);
  font-size: var(--font-size-sm);
  line-height: 1.7;
}

.docs-cta__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.6rem;
  flex: 0 0 auto;
}

/* =========================================================
   RESPONSIVE
   ========================================================= */

@media (max-width: 1199px) {
  .tech-grid {
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }

  .apps-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .workflow {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .workflow-step:nth-child(n + 4) {
    border-top: 1px solid var(--border-subtle);
  }

  .workflow-step:nth-child(4) {
    border-inline-start: 0;
  }
}

@media (max-width: 1023px) {
  .docs-layout {
    grid-template-columns: 1fr;
  }

  .docs-main {
    grid-column: 1;
  }

  .docs-sidebar {
    grid-column: 1;
    grid-row: 1;
    position: static;
    margin-bottom: 0.5rem;
  }

  .sidebar-mobile-toggle {
    display: flex;
    align-items: center;
    justify-content: space-between;
    width: 100%;
    min-height: 3rem;
    padding-inline: 0.9rem;
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-md);
    background: var(--surface-primary);
    color: var(--text-primary);
    font-size: var(--font-size-sm);
    font-weight: 700;
  }

  .sidebar-mobile-toggle > span {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
  }

  .sidebar-nav {
    display: none;
    margin-top: 0.5rem;
  }

  .sidebar-nav--open {
    display: block;
  }

  .docs-hero__body {
    grid-template-columns: 1fr;
    gap: 1.5rem;
  }

  .docs-hero__facts {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .overview-grid,
  .structure-layout {
    grid-template-columns: 1fr;
  }

  .backend-meta-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .integration-summary {
    grid-template-columns: 1fr;
  }

  .api-row {
    grid-template-columns: 4.5rem minmax(0, 1fr) auto;
  }

  .api-description {
    grid-column: 2 / 4;
  }
}

@media (max-width: 767px) {
  .docs-page {
    padding-block: 1rem calc(var(--mobile-nav-height) + var(--safe-bottom) + 2rem);
    padding-inline: 1rem;
  }

  .docs-hero {
    margin-bottom: 2rem;
    padding: 1rem;
    border-radius: var(--radius-lg);
  }

  .docs-hero__top {
    align-items: stretch;
    flex-direction: column;
    margin-bottom: 1.5rem;
  }

  .docs-hero__actions {
    width: 100%;
  }

  .docs-action {
    flex: 1 1 0;
    min-width: 0;
  }

  .docs-hero__copy h1 {
    font-size: 1.8rem;
  }

  .docs-hero__copy p {
    font-size: var(--font-size-sm);
  }

  .docs-hero__facts {
    grid-template-columns: 1fr;
    gap: 0.45rem;
  }

  .hero-fact {
    padding: 0.7rem 0.8rem;
  }

  .docs-section {
    margin-bottom: 3.75rem;
  }

  .section-heading {
    margin-bottom: 1.25rem;
  }

  .section-heading__index {
    width: 2.35rem;
    height: 2.35rem;
  }

  .section-heading h2 {
    font-size: 1.35rem;
  }

  .subsection {
    margin-top: 2.25rem;
  }

  .subsection-heading {
    align-items: flex-start;
    flex-direction: column;
    gap: 0.6rem;
  }

  .tech-grid,
  .apps-grid,
  .structure-grid,
  .command-grid,
  .environment-columns,
  .workflow,
  .backend-meta-grid {
    grid-template-columns: 1fr;
  }

  .api-row {
    grid-template-columns: 4rem minmax(0, 1fr) auto;
    gap: 0.5rem;
    padding: 0.75rem;
  }

  .api-description {
    grid-column: 2 / 4;
  }

  .copy-button {
    min-width: 2rem;
    padding-inline: 0.45rem;
  }

  .copy-button span {
    display: none;
  }

  .data-row {
    grid-template-columns: 1fr;
    gap: 0.25rem;
  }

  .data-row code {
    justify-self: start;
  }

  .integration-row {
    grid-template-columns: auto minmax(0, 1fr);
  }

  .integration-row__status {
    grid-column: 2;
    justify-self: start;
  }

  .notice {
    grid-template-columns: 1fr;
  }

  .docs-cta {
    align-items: stretch;
    flex-direction: column;
  }

  .docs-cta__actions {
    width: 100%;
  }

  .docs-cta__actions .docs-action {
    flex: 1 1 0;
  }
}

@media (prefers-reduced-motion: reduce) {
  .tech-card,
  .docs-action,
  .app-card,
  .api-row {
    transition: none;
  }
}

:global(body.docs-toc-open) {
  overflow: hidden;
}
</style>

