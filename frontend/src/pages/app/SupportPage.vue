<script setup lang="ts">
import {computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch} from 'vue'
import {useRoute, useRouter} from 'vue-router'
import {SUPPORT_CATEGORIES, supportCategoryMeta} from '@/components/support/supportMeta'
import AppButton from '@/components/ui/AppButton.vue'
import AppCard from '@/components/ui/AppCard.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import AppInput from '@/components/ui/AppInput.vue'
import AppModal from '@/components/ui/AppModal.vue'
import AppSelect from '@/components/ui/AppSelect.vue'
import AppSkeleton from '@/components/ui/AppSkeleton.vue'
import AppTabs from '@/components/ui/AppTabs.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import StatusBadge from '@/components/ui/StatusBadge.vue'
import {ApiError, supportService} from '@/services'
import type {CreateTicketInput, FaqItem, SupportCategory, SupportTicket, TicketStatus} from '@/types'
import {formatPersianDateTime, toPersianDigits} from '@/utils/formatters'

const route = useRoute()
const router = useRouter()
const section = ref<'faq' | 'tickets'>(route.query.tab === 'tickets' ? 'tickets' : 'faq')
const faqSearch = ref('')
const faqCategory = ref<SupportCategory | ''>('')
const faqs = ref<FaqItem[]>([])
const faqsLoading = ref(true)
const faqsHasLoaded = ref(false)
const faqsError = ref('')
const openFaqId = ref('')
const faqPage = ref(1)
const faqListRef = ref<HTMLElement | null>(null)
const faqViewLoading = ref(false)
const FAQ_PAGE_SIZE = 5
const FAQ_PAGE_LOADING_MS = 480

let faqRequestId = 0
let faqPageLoadingTimer: ReturnType<typeof setTimeout> | undefined

const tickets = ref<SupportTicket[]>([])
const ticketsTotal = ref(0)
const ticketsLoading = ref(true)
const ticketsError = ref('')
const ticketSearch = ref('')
const ticketStatus = ref<TicketStatus | ''>('')
const ticketCategory = ref<SupportCategory | ''>('')
const createOpen = ref(route.query.new === '1')
const creating = ref(false)
const createError = ref('')
const fieldErrors = reactive<Record<string, string>>({})
const ticketForm = reactive<CreateTicketInput>({
  subject: '',
  category: 'other',
  body: '',
  orderId: typeof route.query.orderId === 'string' ? route.query.orderId : undefined,
})

const sectionTabs = [
  {label: 'راهنما و سؤالات', value: 'faq'},
  {label: 'درخواست‌های من', value: 'tickets'},
]
const ticketStatuses: Array<{ value: TicketStatus | ''; label: string }> = [
  {value: '', label: 'همه وضعیت‌ها'},
  {value: 'open', label: 'باز'},
  {value: 'waiting_for_user', label: 'در انتظار پاسخ شما'},
  {value: 'answered', label: 'پاسخ داده شده'},
  {value: 'closed', label: 'بسته شده'},
]
const ticketCategoryOptions: Array<{
  value: SupportCategory | ''
  label: string
}> = [
  {value: '', label: 'همه دسته‌بندی‌ها'},
  ...SUPPORT_CATEGORIES.map(({value, label}) => ({
    value,
    label,
  })),
]

const activeFaq = computed(() =>
  faqs.value.find((faq) => faq.id === openFaqId.value) ?? null,
)

// The «همه» category is paginated in groups of five; specific categories remain unpaginated.
const isAllFaqCategory = computed(() => !faqCategory.value)
const faqTotalPages = computed(() =>
  isAllFaqCategory.value
    ? Math.max(1, Math.ceil(faqs.value.length / FAQ_PAGE_SIZE))
    : 1,
)
const faqPages = computed(() =>
  Array.from({length: faqTotalPages.value}, (_, index) => index + 1),
)
const visibleFaqs = computed(() => {
  if (!isAllFaqCategory.value) return faqs.value

  const start = (faqPage.value - 1) * FAQ_PAGE_SIZE
  return faqs.value.slice(start, start + FAQ_PAGE_SIZE)
})

function showFaqPageLoading(): void {
  if (faqPageLoadingTimer) clearTimeout(faqPageLoadingTimer)

  faqViewLoading.value = true
  faqPageLoadingTimer = setTimeout(() => {
    faqViewLoading.value = false
    faqPageLoadingTimer = undefined
  }, FAQ_PAGE_LOADING_MS)
}

function clearFaqPageLoadingTimer(): void {
  if (faqPageLoadingTimer) {
    clearTimeout(faqPageLoadingTimer)
    faqPageLoadingTimer = undefined
  }
}

function goToFaqPage(page: number): void {
  if (page < 1 || page > faqTotalPages.value || page === faqPage.value) return

  clearFaqPageLoadingTimer()
  showFaqPageLoading()
  faqPage.value = page
  openFaqId.value = ''
  void nextTick(() => {
    if (faqListRef.value) faqListRef.value.scrollTop = 0
  })
}

function toggleFaq(faqId: string): void {
  // Clicking the currently open question closes its answer without scrolling.
  if (openFaqId.value === faqId) {
    openFaqId.value = ''
    return
  }

  openFaqId.value = faqId
}

let faqScrollAnimationFrame: number | null = null

function findFaqScrollContainer(element: HTMLElement): HTMLElement | Window {
  let parent = element.parentElement

  while (parent && parent !== document.body && parent !== document.documentElement) {
    const styles = window.getComputedStyle(parent)
    const canScrollY = /(auto|scroll|overlay)/.test(styles.overflowY)
      && parent.scrollHeight > parent.clientHeight + 1

    if (canScrollY) return parent
    parent = parent.parentElement
  }

  return window
}

function scrollToActiveAnswer(): void {
  const faqId = activeFaq.value?.id
  if (!faqId) return

  // Wait for Vue's transition/layout to settle, then use a slower custom animation.
  requestAnimationFrame(() => {
    const answerElement = document.getElementById(`faq-answer-${faqId}`)
    if (!answerElement || activeFaq.value?.id !== faqId) return

    if (faqScrollAnimationFrame !== null) {
      cancelAnimationFrame(faqScrollAnimationFrame)
      faqScrollAnimationFrame = null
    }

    const prefersReducedMotion = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false
    const scrollContainer = findFaqScrollContainer(answerElement)
    // Resolve the union once into a stable, explicitly typed element reference.
    // This avoids TypeScript treating the container as Window | HTMLElement
    // inside later callbacks and branches.
    const elementScrollContainer: HTMLElement | null =
      scrollContainer === window ? null : scrollContainer as HTMLElement
    const answerRect = answerElement.getBoundingClientRect()
    const scrollMarginTop = Number.parseFloat(window.getComputedStyle(answerElement).scrollMarginTop) || 0
    let startTop: number
    let targetTop: number

    if (elementScrollContainer === null) {
      startTop = window.scrollY
      targetTop = Math.max(
        0,
        Math.min(
          document.documentElement.scrollHeight - window.innerHeight,
          startTop + answerRect.top - scrollMarginTop,
        ),
      )
    } else {
      startTop = elementScrollContainer.scrollTop
      targetTop = Math.max(
        0,
        Math.min(
          elementScrollContainer.scrollHeight - elementScrollContainer.clientHeight,
          startTop + answerRect.top - elementScrollContainer.getBoundingClientRect().top - scrollMarginTop,
        ),
      )
    }

    const setScrollTop = (top: number): void => {
      if (elementScrollContainer === null) window.scrollTo(0, top)
      else elementScrollContainer.scrollTop = top
    }

    if (prefersReducedMotion || Math.abs(targetTop - startTop) < 2) {
      setScrollTop(targetTop)
      return
    }

    // 900ms with ease-in-out feels deliberate without making the interface sluggish.
    const duration = 1500
    let animationStart: number | null = null

    const animateScroll = (timestamp: number) => {
      if (animationStart === null) animationStart = timestamp
      const progress = Math.min((timestamp - animationStart) / duration, 1)
      const easedProgress = progress < 0.5
        ? 4 * progress * progress * progress
        : 1 - Math.pow(-2 * progress + 2, 3) / 2

      setScrollTop(startTop + (targetTop - startTop) * easedProgress)

      if (progress < 1) {
        faqScrollAnimationFrame = requestAnimationFrame(animateScroll)
      } else {
        faqScrollAnimationFrame = null
      }
    }

    faqScrollAnimationFrame = requestAnimationFrame(animateScroll)
  })
}

const faqCountLabel = computed(() => {
  if (faqsLoading.value && !faqsHasLoaded.value) {
    return 'در حال بارگذاری…'
  }

  return `${toPersianDigits(faqs.value.length)} پاسخ`
})

function readableError(caught: unknown, fallback: string): string {
  return caught instanceof Error ? caught.message : fallback
}

async function loadFaqs(): Promise<void> {
  const requestId = ++faqRequestId

  clearFaqPageLoadingTimer()
  faqsLoading.value = true
  if (faqsHasLoaded.value) faqViewLoading.value = true
  faqsError.value = ''

  try {
    const result = await supportService.listFaqs(
        faqSearch.value,
        faqCategory.value || undefined,
    )

    if (requestId !== faqRequestId) {
      return
    }

    faqs.value = result
    faqsHasLoaded.value = true

    if (
        openFaqId.value
        && !faqs.value.some(
            (faq) => faq.id === openFaqId.value,
        )
    ) {
      openFaqId.value = ''
    }
  } catch (caught) {
    if (requestId !== faqRequestId) {
      return
    }

    faqsError.value = readableError(
        caught,
        'پاسخ‌های راهنما بارگیری نشدند.',
    )
  } finally {
    if (requestId === faqRequestId) {
      faqsLoading.value = false
      faqViewLoading.value = false
      clearFaqPageLoadingTimer()
    }
  }
}

async function loadTickets(): Promise<void> {
  ticketsLoading.value = true
  ticketsError.value = ''
  try {
    const result = await supportService.listTickets({
      pageSize: 30,
      search: ticketSearch.value,
      status: ticketStatus.value || undefined,
      category: ticketCategory.value || undefined,
    })
    tickets.value = result.items
    ticketsTotal.value = result.total
  } catch (caught) {
    ticketsError.value = readableError(caught, 'درخواست‌های پشتیبانی بارگیری نشدند.')
  } finally {
    ticketsLoading.value = false
  }
}

async function refreshPage(): Promise<void> {
  await Promise.allSettled([
    loadFaqs(),
    loadTickets(),
  ])
}

function openCreate(category?: SupportCategory): void {
  createError.value = ''
  Object.keys(fieldErrors).forEach((key) => delete fieldErrors[key])
  if (category) ticketForm.category = category
  createOpen.value = true
  if (route.query.new !== '1') {
    void router.replace({query: {...route.query, new: '1'}})
  }
}

function resetCreate(orderId?: string): void {
  ticketForm.subject = ''
  ticketForm.category = 'other'
  ticketForm.body = ''
  ticketForm.orderId = orderId
  createError.value = ''
  Object.keys(fieldErrors).forEach((key) => delete fieldErrors[key])
}

function closeCreate(): void {
  if (creating.value) return
  createOpen.value = false
  resetCreate()
  const query = {...route.query}
  delete query.new
  delete query.orderId
  void router.replace({query})
}

function validateTicket(): boolean {
  Object.keys(fieldErrors).forEach((key) => delete fieldErrors[key])
  if (ticketForm.subject.trim().length < 5) fieldErrors.subject = 'موضوع را کمی دقیق‌تر بنویسید.'
  if (ticketForm.body.trim().length < 10) fieldErrors.body = 'برای بررسی بهتر، حداقل ۱۰ کاراکتر توضیح بنویسید.'
  return Object.keys(fieldErrors).length === 0
}

async function createTicket(): Promise<void> {
  if (!validateTicket()) return
  creating.value = true
  createError.value = ''
  try {
    const ticket = await supportService.createTicket({
      subject: ticketForm.subject.trim(),
      category: ticketForm.category,
      body: ticketForm.body.trim(),
      orderId: ticketForm.orderId?.trim() || undefined,
    })
    createOpen.value = false
    resetCreate()
    await router.push(`/app/support/tickets/${ticket.id}`)
  } catch (caught) {
    if (caught instanceof ApiError && caught.details?.fields) Object.assign(fieldErrors, caught.details.fields)
    createError.value = readableError(caught, 'ثبت درخواست پشتیبانی انجام نشد.')
  } finally {
    creating.value = false
  }
}

let faqTimer: ReturnType<typeof setTimeout> | undefined

watch([faqSearch, faqCategory], () => {
  faqRequestId += 1
  clearFaqPageLoadingTimer()
  faqViewLoading.value = faqsHasLoaded.value
  faqPage.value = 1
  openFaqId.value = ''
  void nextTick(() => {
    if (faqListRef.value) faqListRef.value.scrollTop = 0
  })

  if (faqTimer) {
    clearTimeout(faqTimer)
  }

  faqTimer = setTimeout(() => {
    faqTimer = undefined
    void loadFaqs()
  }, 220)
})

let ticketTimer: ReturnType<typeof setTimeout> | undefined
watch([ticketSearch, ticketStatus, ticketCategory], () => {
  if (ticketTimer) clearTimeout(ticketTimer)
  ticketTimer = setTimeout(loadTickets, 220)
})

watch(section, (value) => {
  const tab = value === 'tickets' ? 'tickets' : undefined
  if (route.query.tab === tab || (!tab && route.query.tab === undefined)) return
  void router.replace({query: {...route.query, tab}})
})

watch(
    () => [route.query.tab, route.query.new, route.query.orderId] as const,
    ([tab, newTicket, orderId]) => {
      const routeSection = tab === 'tickets' ? 'tickets' : 'faq'
      if (section.value !== routeSection) section.value = routeSection

      const contextualOrderId = typeof orderId === 'string' ? orderId : undefined
      if (ticketForm.orderId !== contextualOrderId) ticketForm.orderId = contextualOrderId

      if (newTicket === '1') {
        createError.value = ''
        Object.keys(fieldErrors).forEach((key) => delete fieldErrors[key])
        createOpen.value = true
      } else if (createOpen.value) {
        createOpen.value = false
        resetCreate(contextualOrderId)
      }
    },
    {immediate: true},
)

onBeforeUnmount(() => {
  if (faqTimer) clearTimeout(faqTimer)
  if (ticketTimer) clearTimeout(ticketTimer)
  clearFaqPageLoadingTimer()
  if (faqScrollAnimationFrame !== null) {
    cancelAnimationFrame(faqScrollAnimationFrame)
    faqScrollAnimationFrame = null
  }
})

onMounted(() => {
  void Promise.all([loadFaqs(), loadTickets()])
})
</script>

<template>
  <div class="page support-page">
    <PageHeader
        title="پشتیبانی"
        description="پاسخ سریع سؤال‌ها را پیدا کنید یا مستقیماً با تیم روشا در ارتباط باشید."
    >
      <template #actions>
        <div class="support-header-actions">
          <AppButton
              variant="secondary"
              size="sm"
              icon="refresh"
              :loading="faqsLoading || ticketsLoading"
              @click="refreshPage"
          >
            به‌روزرسانی
          </AppButton>

          <AppButton
              icon="plus"
              @click="openCreate()"
          >
            درخواست جدید
          </AppButton>
        </div>
      </template>
    </PageHeader>

    <AppCard class="support-hero" padding="lg">
      <div class="hero-copy">
        <span class="support-avatar"><AppIcon name="help" :size="30"/></span>
        <div><span class="eyebrow">مرکز راهنمای روشا</span>
          <h2>چطور می‌توانیم کمک کنیم؟</h2>
          <p>ابتدا بین پاسخ‌های کوتاه جست‌وجو کنید؛ اگر کافی نبود، درخواست پشتیبانی بسازید.</p></div>
      </div>
      <div class="service-promise"><span><i/>پشتیبانی آنلاین</span><small>پاسخ درخواست‌ها معمولاً در کوتاه‌ترین زمان
        کاری</small></div>
    </AppCard>

    <AppTabs v-model="section" :items="sectionTabs" class="section-tabs"/>

    <section v-if="section === 'faq'" class="faq-section">
      <div class="faq-search-wrap">
        <AppInput v-model="faqSearch" icon="search" inputmode="search" placeholder="مثلاً «زمان برداشت تومان»"
                  label="جست‌وجو در راهنما"/>
        <span>{{ faqCountLabel }}</span>
      </div>
      <div class="category-strip" aria-label="دسته‌بندی سؤالات">
        <button type="button" :class="{ active: !faqCategory }" :aria-pressed="!faqCategory" @click="faqCategory = ''">
          <AppIcon name="help" :size="18"/>
          همه
        </button>
        <button v-for="item in SUPPORT_CATEGORIES" :key="item.value" type="button"
                :class="{ active: faqCategory === item.value }" :aria-pressed="faqCategory === item.value"
                @click="faqCategory = item.value">
          <AppIcon :name="item.icon" :size="18"/>
          {{ item.label }}
        </button>
      </div>

      <AppCard padding="none" class="faq-list-card">
        <div
            v-if="faqsLoading && !faqsHasLoaded"
            class="faq-skeletons faq-skeletons--initial"
            role="status"
            aria-live="polite"
            aria-label="در حال بارگذاری سؤالات"
        >
          <div v-for="i in 5" :key="i" class="faq-skeleton-row">
            <AppSkeleton width="2.4rem" height="2.4rem" radius=".8rem"/>
            <div class="faq-skeleton-copy">
              <AppSkeleton :width="i % 2 === 0 ? '56%' : '70%'" height="1rem"/>
              <AppSkeleton width="4.2rem" height=".7rem" radius="999px"/>
            </div>
            <AppSkeleton width="2.4rem" height="2.4rem" radius=".8rem"/>
          </div>
          <span class="faq-skeleton-label">در حال بارگذاری سؤالات…</span>
        </div>
        <div v-else-if="faqsError && !faqsHasLoaded" class="load-error">
          <AppIcon name="warning" :size="26"/>
          <div><strong>راهنما در دسترس نیست</strong>
            <p>{{ faqsError }}</p></div>
          <AppButton variant="secondary" size="sm" icon="refresh" @click="loadFaqs">تلاش دوباره</AppButton>
        </div>
        <EmptyState
            v-else-if="!faqs.length && !faqViewLoading"
            icon="search"
            title="پاسخی پیدا نشد"
            description="عبارت کوتاه‌تری جست‌وجو کنید یا درخواست پشتیبانی بسازید."
        >
          <AppButton @click="openCreate(faqCategory || 'other')">
            ثبت درخواست
          </AppButton>
        </EmptyState>
        <template v-else>
          <div ref="faqListRef" class="faq-list">
            <div
                v-if="faqViewLoading"
                class="faq-skeletons faq-skeletons--in-list"
                role="status"
                aria-live="polite"
                aria-label="در حال به‌روزرسانی سؤالات"
            >
              <div v-for="i in 5" :key="i" class="faq-skeleton-row">
                <AppSkeleton width="2.4rem" height="2.4rem" radius=".8rem"/>
                <div class="faq-skeleton-copy">
                  <AppSkeleton :width="i % 2 === 0 ? '56%' : '70%'" height="1rem"/>
                  <AppSkeleton width="4.2rem" height=".7rem" radius="999px"/>
                </div>
                <AppSkeleton width="2.4rem" height="2.4rem" radius=".8rem"/>
              </div>
              <span class="faq-skeleton-label">در حال به‌روزرسانی سؤالات…</span>
            </div>
            <template v-else>
            <article v-for="faq in visibleFaqs" :key="faq.id" :class="{ open: openFaqId === faq.id }">
              <button
                  :id="`faq-question-${faq.id}`"
                  type="button"
                  class="faq-question"
                  :aria-expanded="openFaqId === faq.id"
                  :aria-controls="openFaqId === faq.id ? `faq-answer-${faq.id}` : undefined"
                  @click="toggleFaq(faq.id)"
              >
                <span class="faq-icon">
                  <AppIcon :name="supportCategoryMeta(faq.category).icon" :size="20"/>
                </span>

                <span class="faq-question-copy">
                  <strong class="faq-question-title">{{ faq.question }}</strong>
                  <span class="faq-question-category">
                    {{ supportCategoryMeta(faq.category).label }}
                  </span>
                </span>

                <span class="faq-toggle-icon" aria-hidden="true">
                  <AppIcon
                      :name="openFaqId === faq.id ? 'chevronUp' : 'chevronDown'"
                      :size="19"
                  />
                </span>
              </button>
            </article>
            </template>
          </div>

          <nav
              v-if="isAllFaqCategory && faqTotalPages > 1"
              class="faq-pagination"
              aria-label="صفحه‌بندی سؤالات"
              dir="rtl"
          >
            <button type="button" :disabled="faqViewLoading || faqsLoading || faqPage <= 1" @click="goToFaqPage(faqPage - 1)">
              قبلی
            </button>
            <button
                v-for="page in faqPages"
                :key="page"
                type="button"
                :class="{ active: faqPage === page }"
                :disabled="faqViewLoading || faqsLoading"
                :aria-current="faqPage === page ? 'page' : undefined"
                :aria-label="`رفتن به صفحه ${toPersianDigits(page)}`"
                @click="goToFaqPage(page)"
            >
              {{ toPersianDigits(page) }}
            </button>
            <span class="faq-pagination-status">
              صفحه {{ toPersianDigits(faqPage) }} از {{ toPersianDigits(faqTotalPages) }}
            </span>
            <button type="button" :disabled="faqViewLoading || faqsLoading || faqPage >= faqTotalPages" @click="goToFaqPage(faqPage + 1)">
              بعدی
            </button>
          </nav>
        </template>

      </AppCard>

      <Transition name="faq-panel" mode="out-in" @after-enter="scrollToActiveAnswer">
        <section
            v-if="activeFaq"
            :key="activeFaq.id"
            :id="`faq-answer-${activeFaq.id}`"
            class="faq-selected-answer-card"
            :aria-labelledby="`faq-question-${activeFaq.id}`"
            aria-live="polite"
        >
          <div class="faq-selected-question">
            <div class="faq-selected-question-label">
              <span class="faq-selected-question-dot" aria-hidden="true"></span>
              <span>سؤال انتخاب‌شده</span>
            </div>
            <h3>{{ activeFaq.question }}</h3>
            <span class="faq-question-category">
              {{ supportCategoryMeta(activeFaq.category).label }}
            </span>
          </div>

          <div class="faq-answer">
            <div class="faq-answer-heading">
              <span class="faq-answer-heading-icon">
                <AppIcon name="check" :size="16"/>
              </span>
              <strong>پاسخ</strong>
            </div>

            <p class="faq-answer-text">{{ activeFaq.answer }}</p>

            <div v-if="activeFaq.tags?.length" class="faq-tags" aria-label="برچسب‌های مرتبط">
              <span v-for="tag in activeFaq.tags" :key="tag">{{ tag }}</span>
            </div>
          </div>
        </section>
      </Transition>

      <AppCard class="still-need-help" padding="lg">
        <span><AppIcon name="mail" :size="25"/></span>
        <div><h3>هنوز پاسخ خود را پیدا نکردید؟</h3>
          <p>جزئیات موضوع را برای تیم پشتیبانی بنویسید تا دقیق‌تر بررسی کنیم.</p></div>
        <AppButton variant="secondary" icon="plus" @click="openCreate(faqCategory || undefined)">ساخت درخواست
        </AppButton>
      </AppCard>
    </section>

    <section v-else class="tickets-section">
      <div class="tickets-toolbar">
        <div><h2>درخواست‌های من</h2><span>{{ toPersianDigits(ticketsTotal) }} درخواست</span></div>
        <div>
          <AppInput v-model="ticketSearch" icon="search" inputmode="search" placeholder="موضوع یا شماره درخواست"/>
          <AppSelect v-model="ticketStatus" :options="ticketStatuses" aria-label="فیلتر درخواست‌ها بر اساس وضعیت"/>
          <AppSelect
              v-model="ticketCategory"
              :options="ticketCategoryOptions"
              aria-label="فیلتر درخواست‌ها بر اساس دسته‌بندی"
          />
        </div>
      </div>

      <AppCard padding="none" class="tickets-card">
        <div v-if="ticketsLoading" class="ticket-skeletons">
          <div v-for="i in 3" :key="i">
            <AppSkeleton width="3rem" height="3rem" radius="1rem"/>
            <span><AppSkeleton width="45%" height="1.05rem"/><AppSkeleton width="70%" height=".8rem"/></span></div>
        </div>
        <div v-else-if="ticketsError" class="load-error">
          <AppIcon name="warning" :size="26"/>
          <div><strong>درخواست‌ها بارگیری نشدند</strong>
            <p>{{ ticketsError }}</p></div>
          <AppButton variant="secondary" size="sm" icon="refresh" @click="loadTickets">تلاش دوباره</AppButton>
        </div>
        <EmptyState v-else-if="!tickets.length" icon="help" title="درخواستی در این فهرست نیست"
                    description="اگر به کمک نیاز دارید، یک درخواست جدید برای پشتیبانی ثبت کنید.">
          <AppButton icon="plus" @click="openCreate()">درخواست جدید</AppButton>
        </EmptyState>
        <div v-else class="ticket-list">
          <RouterLink v-for="ticket in tickets" :key="ticket.id" :to="`/app/support/tickets/${ticket.id}`"
                      class="ticket-row">
            <span class="ticket-icon"><AppIcon :name="supportCategoryMeta(ticket.category).icon" :size="22"/></span>
            <div class="ticket-copy">
              <div><h3>{{ ticket.subject }}</h3>
                <StatusBadge domain="ticket" :status="ticket.status"/>
              </div>
              <p><span class="ltr">{{ ticket.ticketNumber }}</span><i/>{{
                  supportCategoryMeta(ticket.category).label
                }}<i/>آخرین به‌روزرسانی {{ formatPersianDateTime(ticket.updatedAt) }}</p></div>
            <div class="message-count">
              <AppIcon name="mail" :size="17"/>
              {{ toPersianDigits(ticket.messages.length) }} پیام
            </div>
            <AppIcon name="chevronLeft" :size="20"/>
          </RouterLink>
        </div>
      </AppCard>
    </section>

    <AppModal
        :model-value="createOpen"
        title="درخواست پشتیبانی جدید"
        description="با توضیح دقیق‌تر، پاسخ مناسب‌تری دریافت می‌کنید."
        size="lg"
        :dismissible="!creating"
        @update:model-value="(value) => { if (!value) closeCreate() }"
    >
      <form class="ticket-form" @submit.prevent="createTicket">
        <div v-if="createError" class="form-error" role="alert">{{ createError }}</div>
        <div class="form-grid">
          <AppSelect v-model="ticketForm.category" :options="ticketCategoryOptions" label="دسته‌بندی"
                     :error="fieldErrors.category" required/>
          <AppInput v-model="ticketForm.orderId" label="شماره سفارش (اختیاری)" placeholder="ORD-..." ltr/>
        </div>
        <AppInput v-model="ticketForm.subject" label="موضوع" placeholder="خلاصه‌ای روشن از درخواست"
                  :error="fieldErrors.subject"/>
        <label class="textarea-field"><span>توضیحات</span><textarea v-model="ticketForm.body" rows="6"
                                                                    placeholder="چه اتفاقی افتاده و از ما چه کمکی می‌خواهید؟"
                                                                    :class="{ invalid: fieldErrors.body }"
                                                                    :aria-invalid="Boolean(fieldErrors.body)"
                                                                    :aria-describedby="fieldErrors.body ? 'support-ticket-body-error' : undefined"
                                                                    @input="fieldErrors.body = ''"/><small
            id="support-ticket-body-error" :class="{ error: fieldErrors.body }"
            :role="fieldErrors.body ? 'alert' : undefined">{{
            fieldErrors.body || `${toPersianDigits(ticketForm.body.length)} کاراکتر`
          }}</small></label>
        <div class="safe-support-note">
          <AppIcon name="shield" :size="18"/>
          پشتیبانی هرگز رمز عبور یا کد ورود شما را درخواست نمی‌کند.
        </div>
      </form>
      <template #footer>
        <AppButton block :loading="creating" @click="createTicket">ثبت درخواست</AppButton>
        <AppButton variant="secondary" :disabled="creating" @click="closeCreate">انصراف</AppButton>
      </template>
    </AppModal>
  </div>
</template>

<style scoped>
.support-page {
  display: grid;
  align-content: start;
  gap: var(--space-5);
}

.support-page :deep(.page-header) {
  margin-bottom: 0;
}

.support-header-actions {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
}

.support-hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-6);
  background: linear-gradient(125deg, var(--color-surface-1), var(--color-primary-soft));
}

.hero-copy {
  display: flex;
  align-items: center;
  gap: var(--space-4);
}

.support-avatar {
  display: grid;
  width: 4rem;
  height: 4rem;
  flex: 0 0 auto;
  border: 1px solid rgba(67, 139, 255, .2);
  border-radius: 1.25rem;
  background: var(--color-primary-soft);
  color: var(--color-primary);
  place-items: center;
}

.eyebrow {
  color: var(--color-primary);
  font-size: var(--font-size-xs);
  font-weight: 600;
}

.hero-copy h2 {
  margin: .1rem 0;
  font-size: var(--font-size-xl);
}

.hero-copy p {
  margin: 0;
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
}

.service-promise {
  display: grid;
  justify-items: end;
  padding: var(--space-3) var(--space-4);
  border: 1px solid var(--color-border-soft);
  border-radius: var(--radius-md);
  background: var(--color-surface-2);
}

.service-promise > span {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-weight: 600;
}

.service-promise i {
  width: .5rem;
  height: .5rem;
  border-radius: 50%;
  background: var(--color-success);
  box-shadow: 0 0 0 4px var(--color-success-soft);
}

.service-promise small {
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
}

.section-tabs {
  width: min(100%, 32rem);
  margin-inline: auto;
}

.faq-section, .tickets-section {
  display: grid;
  gap: var(--space-4);
}

/* Leave enough room after the final FAQ element for scrolling and mobile viewports. */
.faq-section {
  padding-block-end: max(var(--space-8), env(safe-area-inset-bottom, 0px));
}

.faq-search-wrap {
  position: relative;
  width: min(100%, 45rem);
  margin-inline: auto;
}

.faq-search-wrap > span {
  position: absolute;
  inset-block-end: .9rem;
  inset-inline-end: var(--space-4);
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
  pointer-events: none;
}

.faq-search-wrap :deep(input) {
  padding-inline-end: 6rem;
}

.category-strip {
  display: flex;
  gap: var(--space-2);
  overflow-x: auto;
  padding-bottom: var(--space-1);
}

.category-strip button {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  min-height: 2.6rem;
  flex: 0 0 auto;
  padding-inline: var(--space-4);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-pill);
  background: var(--color-surface-1);
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
}

.category-strip button:hover {
  border-color: var(--color-border-hover);
  color: var(--color-text-primary);
}

.category-strip button.active {
  border-color: rgba(67, 139, 255, .3);
  background: var(--color-primary-soft);
  color: var(--color-primary);
}

.faq-list-card, .tickets-card {
  overflow: hidden;
}

.faq-skeletons {
  display: grid;
  width: 100%;
}

.faq-skeletons--initial {
  min-height: 18rem;
}

.faq-skeleton-row {
  display: flex;
  direction: rtl;
  align-items: center;
  gap: var(--space-4);
  min-height: 5.25rem;
  padding: var(--space-5);
  box-sizing: border-box;
}

.faq-skeleton-row + .faq-skeleton-row {
  border-top: 1px solid var(--color-border-soft);
}

.faq-skeleton-copy {
  display: flex;
  flex: 1 1 auto;
  flex-direction: column;
  align-items: flex-start;
  gap: .65rem;
  min-width: 0;
}

.faq-skeleton-label {
  padding: 0 var(--space-5) var(--space-4);
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
  text-align: center;
}

.faq-skeletons--in-list .faq-skeleton-label {
  padding-top: var(--space-2);
}

@media (max-width: 767px) {
  .faq-skeleton-row {
    gap: var(--space-3);
    min-height: 4.9rem;
    padding: var(--space-4);
  }
}

@media (prefers-reduced-motion: reduce) {
  .faq-skeletons :deep(*) {
    animation-duration: .01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: .01ms !important;
  }
}

.load-error {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  padding: var(--space-8);
  color: var(--color-danger);
}

.load-error > div {
  flex: 1;
  color: var(--color-text-primary);
}

.load-error p {
  margin: .1rem 0 0;
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
}

.faq-list {
  max-height: min(36rem, 65vh);
  overflow-y: auto;
  overscroll-behavior: contain;
  scrollbar-gutter: stable;
  /* Keep the last question away from the clipped edge of the rounded card. */
  padding-block-end: var(--space-3);
  scroll-padding-block: var(--space-3);
  box-sizing: border-box;
}

@media (max-width: 767px) {
  .faq-list {
    max-height: 60vh;
  }
}

.faq-pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-wrap: wrap;
  gap: .45rem;
  padding: var(--space-4);
  border-top: 1px solid var(--color-border-soft);
  background: var(--color-surface-1);
}

.faq-pagination button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 2.5rem;
  min-height: 2.5rem;
  padding: .4rem .7rem;
  border: 1px solid var(--color-border-soft);
  border-radius: .7rem;
  background: var(--color-surface-2);
  color: var(--color-text-primary);
  font: inherit;
  font-size: var(--font-size-sm);
  cursor: pointer;
  transition: border-color 180ms ease, background-color 180ms ease, color 180ms ease;
}

.faq-pagination button:hover:not(:disabled) {
  border-color: color-mix(in srgb, var(--color-primary) 45%, transparent);
  color: var(--color-primary);
}

.faq-pagination button.active {
  border-color: color-mix(in srgb, var(--color-primary) 38%, transparent);
  background: var(--color-primary-soft);
  color: var(--color-primary);
  font-weight: 700;
}

.faq-pagination button:disabled {
  opacity: .42;
  cursor: not-allowed;
}

.faq-pagination-status {
  padding-inline: .4rem;
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
  white-space: nowrap;
}

.faq-pagination button:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

@media (max-width: 480px) {
  .faq-pagination {
    gap: .35rem;
    padding: var(--space-3);
  }

  .faq-pagination button {
    min-width: 2.25rem;
    min-height: 2.25rem;
    padding: .35rem .55rem;
  }

  .faq-pagination-status {
    flex-basis: 100%;
    order: 3;
    text-align: center;
  }
}

.faq-list article + article {
  border-top: 1px solid var(--color-border-soft);
}

.faq-list article {
  min-width: 0;
  background: var(--color-surface-1);
  transition: background-color 220ms ease;
}

.faq-list article.open {
  background: var(--color-surface-1);
}

.faq-list article > .faq-question {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  align-items: center;
  gap: var(--space-3);
  width: 100%;
  min-width: 0;
  padding: var(--space-5);
  border: 0;
  background: transparent;
  color: var(--color-text-primary);
  text-align: start;
  cursor: pointer;
  transition: background-color 220ms ease;
}

.faq-list article > .faq-question:hover {
  background: var(--color-surface-2);
}

.faq-list article.open > .faq-question {
  background: var(--color-primary-soft);
}

.faq-icon {
  display: grid;
  width: 2.75rem;
  height: 2.75rem;
  border-radius: .85rem;
  background: var(--color-primary-soft);
  color: var(--color-primary);
  place-items: center;
}

.faq-question-copy {
  display: grid;
  justify-items: start;
  gap: .45rem;
  min-width: 0;
}

.faq-question-title {
  color: var(--color-text-primary);
  font-size: var(--font-size-md);
  font-weight: 700;
  line-height: 1.9;
  overflow-wrap: anywhere;
}

.faq-question-category {
  display: inline-flex;
  align-items: center;
  width: fit-content;
  max-width: 100%;
  padding: .12rem .55rem;
  border: 1px solid var(--color-border-soft);
  border-radius: var(--radius-pill);
  background: var(--color-surface-1);
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
  line-height: 1.7;
}

.faq-toggle-icon {
  display: grid;
  width: 2.25rem;
  height: 2.25rem;
  flex: 0 0 auto;
  border: 1px solid var(--color-border-soft);
  border-radius: .7rem;
  background: var(--color-surface-1);
  color: var(--color-text-muted);
  place-items: center;
  transition: transform 240ms ease, color 240ms ease, border-color 240ms ease;
}

.faq-list article.open .faq-toggle-icon {
  border-color: color-mix(in srgb, var(--color-primary) 28%, transparent);
  color: var(--color-primary);
}

/* The answer is a separate panel below the scrollable question list. */
.faq-selected-answer-card {
  /* Keep the complete answer away from both sticky headers and the viewport bottom. */
  scroll-margin-top: 5.5rem;
  scroll-margin-bottom: 3rem;
  min-width: 0;
  margin-top: var(--space-4);
  padding: var(--space-5);
  border: 1px solid var(--color-border-soft);
  border-radius: var(--radius-lg, 1rem);
  background: var(--color-surface-1);
  box-shadow: 0 8px 24px rgb(0 0 0 / 8%);
}

.faq-selected-question {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: var(--space-3);
  margin-bottom: var(--space-4);
  padding-bottom: var(--space-4);
  border-bottom: 1px solid var(--color-border-soft);
}

.faq-selected-question-label {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
  font-weight: 700;
}

.faq-selected-question-dot {
  width: .5rem;
  height: .5rem;
  flex: 0 0 auto;
  border-radius: 50%;
  background: var(--color-primary);
}

.faq-selected-question h3 {
  margin: 0;
  color: var(--color-text-primary);
  font-size: var(--font-size-md);
  font-weight: 750;
  line-height: 1.9;
  overflow-wrap: anywhere;
}

.faq-answer {
  min-width: 0;
  padding: var(--space-4) var(--space-5);
  border: 1px solid var(--color-border-soft);
  border-inline-start: 3px solid var(--color-primary);
  border-radius: var(--radius-md);
  background: var(--color-surface-2);
}

.faq-answer-heading {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  margin-bottom: var(--space-3);
  padding-bottom: var(--space-3);
  border-bottom: 1px solid var(--color-border-soft);
  color: var(--color-primary);
  font-size: var(--font-size-sm);
}

.faq-answer-heading-icon {
  display: grid;
  width: 1.65rem;
  height: 1.65rem;
  flex: 0 0 auto;
  border-radius: .5rem;
  background: var(--color-primary-soft);
  color: var(--color-primary);
  place-items: center;
}

.faq-answer-text {
  margin: 0;
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  line-height: 2.15;
  white-space: pre-line;
  overflow-wrap: anywhere;
}

.faq-tags {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
  margin-top: var(--space-4);
  padding-top: var(--space-3);
  border-top: 1px dashed var(--color-border-soft);
}

.faq-tags span {
  padding: .2rem .6rem;
  border: 1px solid var(--color-border-soft);
  border-radius: var(--radius-pill);
  background: var(--color-surface-1);
  color: var(--color-text-muted);
  font-size: .68rem;
  line-height: 1.7;
}

.still-need-help {
  display: flex;
  align-items: center;
  gap: var(--space-4);
}

.still-need-help > span {
  display: grid;
  width: 3rem;
  height: 3rem;
  border-radius: .9rem;
  background: var(--color-gold-soft);
  color: var(--color-gold);
  place-items: center;
}

.still-need-help > div {
  flex: 1;
}

.still-need-help h3 {
  margin: 0;
  font-size: var(--font-size-md);
}

.still-need-help p {
  margin: .1rem 0 0;
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
}

.tickets-toolbar {
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: var(--space-4);
}

.tickets-toolbar > div:first-child {
  display: flex;
  align-items: baseline;
  gap: var(--space-2);
}

.tickets-toolbar h2 {
  margin: 0;
  font-size: var(--font-size-lg);
}

.tickets-toolbar > div:first-child span {
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
}

.tickets-toolbar > div:last-child {
  display: grid;
  grid-template-columns: minmax(12rem, 1fr) 12rem 12rem;
  gap: var(--space-3);
  min-width: min(100%, 40rem);
}

.ticket-skeletons {
  display: grid;
}

.ticket-skeletons > div {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  padding: var(--space-5);
}

.ticket-skeletons > div + div {
  border-top: 1px solid var(--color-border-soft);
}

.ticket-skeletons span {
  display: grid;
  flex: 1;
  gap: var(--space-2);
}

.ticket-list {
  display: grid;
}

.ticket-row {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto auto;
  align-items: center;
  gap: var(--space-4);
  padding: var(--space-5);
  transition: background var(--transition-fast);
}

.ticket-row + .ticket-row {
  border-top: 1px solid var(--color-border-soft);
}

.ticket-row:hover {
  background: var(--color-surface-2);
}

.ticket-icon {
  display: grid;
  width: 3rem;
  height: 3rem;
  border-radius: 1rem;
  background: var(--color-primary-soft);
  color: var(--color-primary);
  place-items: center;
}

.ticket-copy {
  min-width: 0;
}

.ticket-copy > div {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.ticket-copy h3 {
  margin: 0;
  overflow: hidden;
  font-size: var(--font-size-md);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ticket-copy p {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  margin: .25rem 0 0;
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
}

.ticket-copy p i {
  width: .25rem;
  height: .25rem;
  border-radius: 50%;
  background: var(--color-border-hover);
}

.message-count {
  display: flex;
  align-items: center;
  gap: var(--space-1);
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
}

.ticket-row > svg {
  color: var(--color-text-muted);
}

.ticket-form {
  display: grid;
  gap: var(--space-4);
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-3);
}

.form-error {
  padding: var(--space-3);
  border-radius: var(--radius-md);
  background: var(--color-danger-soft);
  color: var(--color-danger);
  font-size: var(--font-size-sm);
}

.textarea-field {
  display: grid;
  gap: var(--space-2);
}

.textarea-field > span {
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  font-weight: 500;
}

.textarea-field textarea {
  width: 100%;
  resize: vertical;
  min-height: 8rem;
  padding: var(--space-3) var(--space-4);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  outline: 0;
  background: var(--color-surface-2);
  line-height: 1.9;
}

.textarea-field textarea:focus {
  border-color: var(--color-border-focus);
  background: var(--color-surface-1);
  box-shadow: var(--shadow-focus);
}

.textarea-field textarea.invalid {
  border-color: var(--color-danger);
}

.textarea-field small {
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
}

.textarea-field small.error {
  color: var(--color-danger);
}

.safe-support-note {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-3);
  border-radius: var(--radius-md);
  background: var(--color-info-soft);
  color: var(--color-text-secondary);
  font-size: var(--font-size-xs);
}

.safe-support-note svg {
  color: var(--color-info);
}

.support-hero {
  position: relative;
  overflow: hidden;
}

.support-hero::after {
  position: absolute;
  inset-block: 16%;
  inset-inline-start: 0;
  width: 2px;
  border-radius: var(--radius-pill);
  background: linear-gradient(180deg, transparent, var(--color-gold), transparent);
  content: '';
  opacity: .72;
}

.support-hero > * {
  position: relative;
  z-index: 1;
}

.category-strip {
  overscroll-behavior-inline: contain;
  scrollbar-width: none;
}

.category-strip::-webkit-scrollbar {
  display: none;
}

.category-strip button {
  min-height: 2.75rem;
}

.category-strip button:focus-visible, .faq-list article > button:focus-visible, .ticket-row:focus-visible {
  outline: 2px solid var(--color-border-focus);
  outline-offset: -2px;
}



.ticket-row {
  min-height: 5.5rem;
}

.ticket-copy h3 {
  overflow: visible;
  text-overflow: clip;
  white-space: normal;
  overflow-wrap: anywhere;
}

@media (hover: hover) {
  .ticket-row:hover {
    background: linear-gradient(90deg, var(--color-primary-soft), var(--color-surface-2));
  }
}

@media (max-width: 900px) {
  .support-hero {
    align-items: flex-start;
    flex-direction: column;
  }

  .service-promise {
    width: 100%;
    align-items: start;
    justify-items: start;
  }

  .ticket-row {
    grid-template-columns: auto minmax(0, 1fr) auto;
  }

  .message-count {
    display: none;
  }
}

@media (max-width: 900px) {
  .tickets-toolbar {
    align-items: stretch;
    flex-direction: column;
  }

  .tickets-toolbar > div:last-child {
    grid-template-columns: minmax(0, 1fr);
    min-width: 0;
  }
}

@media (max-width: 767px) {
  .support-avatar {
    width: 3.25rem;
    height: 3.25rem;
  }

  .hero-copy {
    align-items: flex-start;
  }

  .hero-copy h2 {
    font-size: var(--font-size-lg);
  }

  .section-tabs {
    width: 100%;
  }

  .faq-list article > button {
    min-height: 4.75rem;
    padding: var(--space-4);
  }

  .faq-icon {
    width: 2.4rem;
    height: 2.4rem;
  }

  .still-need-help {
    align-items: flex-start;
    flex-wrap: wrap;
  }

  .still-need-help > div {
    min-width: calc(100% - 4rem);
  }

  .still-need-help :deep(.app-button) {
    width: 100%;
    min-height: 2.75rem;
  }

  .tickets-toolbar {
    align-items: stretch;
    flex-direction: column;
  }

  .tickets-toolbar > div:last-child {
    grid-template-columns: 1fr;
    min-width: 0;
  }

  .ticket-row {
    gap: var(--space-3);
    padding: var(--space-4);
  }

  .ticket-copy > div {
    align-items: flex-start;
    flex-direction: column;
    gap: var(--space-1);
  }

  .ticket-copy p {
    flex-wrap: wrap;
  }

  .ticket-copy p span ~ * {
    display: none;
  }

  .form-grid {
    grid-template-columns: 1fr;
  }

  .load-error {
    align-items: flex-start;
    flex-wrap: wrap;
    padding: var(--space-5);
  }

  .load-error > div {
    min-width: calc(100% - 4rem);
  }

  .load-error :deep(.app-button) {
    min-height: 2.75rem;
  }
}

@media (max-width: 399px) {
  .hero-copy {
    gap: var(--space-3);
  }

  .support-avatar {
    width: 3rem;
    height: 3rem;
    border-radius: .9rem;
  }

  .hero-copy p {
    font-size: var(--font-size-xs);
  }

  .service-promise {
    padding: var(--space-3);
  }

  .faq-search-wrap > span {
    inset-inline-end: var(--space-3);
  }

  .category-strip {
    margin-inline: calc(var(--space-1) * -1);
    padding-inline: var(--space-1);
  }

  .faq-list article > button {
    grid-template-columns: minmax(0, 1fr) auto;
    gap: var(--space-2);
  }

  .faq-icon {
    display: none;
  }

  .ticket-row {
    grid-template-columns: 2.5rem minmax(0, 1fr) auto;
    gap: var(--space-2);
    padding-inline: var(--space-3);
  }

  .ticket-icon {
    width: 2.5rem;
    height: 2.5rem;
    border-radius: .8rem;
  }

  .ticket-copy h3 {
    font-size: var(--font-size-sm);
  }
}

/* Smoothly reveal the selected answer outside the question-list container. */
.faq-panel-enter-active,
.faq-panel-leave-active {
  transition: opacity 240ms ease, transform 240ms ease;
}

.faq-panel-enter-from,
.faq-panel-leave-to {
  opacity: 0;
  transform: translateY(8px);
}

@media (max-width: 767px) {
  .faq-list article > .faq-question {
    gap: var(--space-3);
    padding: var(--space-4);
  }

  .faq-selected-answer-card {
    margin-top: var(--space-3);
    padding: var(--space-4);
  }

  .faq-answer {
    padding: var(--space-4);
  }

  .faq-selected-question h3 {
    font-size: var(--font-size-sm);
  }

  .faq-question-title {
    font-size: var(--font-size-sm);
  }
}

/* Respect the user's reduced-motion preference. */
@media (prefers-reduced-motion: reduce) {
  .faq-panel-enter-active,
  .faq-panel-leave-active,
  .faq-list article,
  .faq-list article > .faq-question,
  .faq-toggle-icon {
    transition: none;
  }
}
</style>
