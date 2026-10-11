<script setup lang="ts">
import {computed, onBeforeUnmount, onMounted, ref, watch,} from 'vue'

import AppButton from '@/components/ui/AppButton.vue'
import AppIcon from '@/components/ui/AppIcon.vue'

import {adminApi} from '@/services/admin/adminApi'

import type {
  AdminTicket,
  AdminTicketCategory,
  AdminTicketListResponse,
  AdminTicketPriority,
  AdminTicketStatus,
} from '@/services/admin/supportAdmin.service'

const PAGE_SIZE = 20
const SEARCH_DEBOUNCE_MS = 300

const BASE_PATH = '/admin/support/tickets/'

const statusLabels: Record<AdminTicketStatus, string> = {
  open: 'باز',
  pending: 'در انتظار پاسخ کاربر',
  resolved: 'پاسخ داده شده',
  closed: 'بسته شده',
}

const categoryLabels: Record<AdminTicketCategory, string> = {
  trade: 'معامله',
  deposit: 'واریز',
  withdrawal: 'برداشت',
  verification: 'احراز هویت',
  bank: 'حساب بانکی',
  security: 'امنیت',
  technical: 'مشکل فنی',
  other: 'سایر',
}

const priorityLabels: Record<AdminTicketPriority, string> = {
  low: 'کم',
  medium: 'متوسط',
  high: 'زیاد',
  urgent: 'فوری',
}

const statusOptions: Array<{
  value: AdminTicketStatus | ''
  label: string
}> = [
  {value: '', label: 'همه وضعیت‌ها'},
  {value: 'open', label: statusLabels.open},
  {value: 'pending', label: statusLabels.pending},
  {value: 'resolved', label: statusLabels.resolved},
  {value: 'closed', label: statusLabels.closed},
]

const categoryOptions: Array<{
  value: AdminTicketCategory | ''
  label: string
}> = [
  {value: '', label: 'همه دسته‌بندی‌ها'},
  ...Object.entries(categoryLabels).map(([value, label]) => ({
    value: value as AdminTicketCategory,
    label,
  })),
]

const priorityOptions: Array<{
  value: AdminTicketPriority | ''
  label: string
}> = [
  {value: '', label: 'همه اولویت‌ها'},
  ...Object.entries(priorityLabels).map(([value, label]) => ({
    value: value as AdminTicketPriority,
    label,
  })),
]

const dateFormatter = new Intl.DateTimeFormat('fa-IR', {
  dateStyle: 'short',
  timeStyle: 'short',
})

const tickets = ref<AdminTicket[]>([])
const total = ref(0)
const page = ref(1)

const search = ref('')
const statusFilter = ref<AdminTicketStatus | ''>('')
const categoryFilter = ref<AdminTicketCategory | ''>('')
const priorityFilter = ref<AdminTicketPriority | ''>('')

const selectedId = ref<number | null>(null)
const selectedTicket = ref<AdminTicket | null>(null)

const loading = ref(true)
const refreshing = ref(false)
const detailLoading = ref(false)
const replying = ref(false)
const savingStatus = ref(false)

const listError = ref('')
const detailError = ref('')
const replyError = ref('')
const statusError = ref('')
const feedback = ref('')

const replyBody = ref('')
const statusDraft = ref<AdminTicketStatus>('open')

let listRequestId = 0
let detailRequestId = 0
let searchTimer: ReturnType<typeof setTimeout> | undefined
let hasLoadedOnce = false

const totalPages = computed(() =>
    Math.max(1, Math.ceil(total.value / PAGE_SIZE)),
)

const firstVisibleItem = computed(() => {
  if (total.value === 0) return 0

  return (page.value - 1) * PAGE_SIZE + 1
})

const lastVisibleItem = computed(() =>
    Math.min(page.value * PAGE_SIZE, total.value),
)

const canReply = computed(() =>
    Boolean(
        selectedTicket.value
        && selectedTicket.value.status !== 'closed',
    ),
)

const hasStatusChanges = computed(() =>
    Boolean(
        selectedTicket.value
        && statusDraft.value !== selectedTicket.value.status,
    ),
)

const isSelectedTicketInCurrentList = computed(() =>
        selectedId.value !== null
        && tickets.value.some(
            (ticket) => ticket.id === selectedId.value,
        ),
)

function formatDate(value?: string | null): string {
  if (!value) return '—'

  const date = new Date(value)

  if (Number.isNaN(date.getTime())) {
    return '—'
  }

  return dateFormatter.format(date)
}

function readableError(
    error: unknown,
    fallback: string,
): string {
  if (error instanceof Error && error.message.trim()) {
    return error.message
  }

  return fallback
}

function statusLabel(status: AdminTicketStatus): string {
  return statusLabels[status] ?? status
}

function categoryLabel(category: AdminTicketCategory): string {
  return categoryLabels[category] ?? category
}

function priorityLabel(priority: AdminTicketPriority): string {
  return priorityLabels[priority] ?? priority
}

function statusClass(status: AdminTicketStatus): string {
  return `status-${status}`
}

function priorityClass(priority: AdminTicketPriority): string {
  return `priority-${priority}`
}

function buildListQuery(): string {
  const params = new URLSearchParams()

  params.set('page', String(page.value))
  params.set('pageSize', String(PAGE_SIZE))

  const normalizedSearch = search.value.trim()

  if (normalizedSearch) {
    params.set('search', normalizedSearch)
  }

  if (statusFilter.value) {
    params.set('status', statusFilter.value)
  }

  if (categoryFilter.value) {
    params.set('category', categoryFilter.value)
  }

  if (priorityFilter.value) {
    params.set('priority', priorityFilter.value)
  }

  return params.toString()
}

function clearSelection(): void {
  selectedId.value = null
  selectedTicket.value = null

  detailError.value = ''
  replyError.value = ''
  statusError.value = ''
  feedback.value = ''
  replyBody.value = ''

  detailRequestId += 1
  detailLoading.value = false
}

async function loadTickets(
    options: {
      clearSelectionIfHidden?: boolean
    } = {},
): Promise<void> {
  const requestId = ++listRequestId

  listError.value = ''

  if (hasLoadedOnce) {
    refreshing.value = true
  } else {
    loading.value = true
  }

  try {
    const query = buildListQuery()

    const result = await adminApi.get<AdminTicketListResponse>(
        `${BASE_PATH}?${query}`,
    )

    // نتیجه درخواست قدیمی نباید داده‌های جدید را جایگزین کند.
    if (requestId !== listRequestId) return

    const lastPage = Math.max(
        1,
        Math.ceil(result.total / PAGE_SIZE),
    )

    // اگر حذف یا فیلترشدن داده‌ها صفحه فعلی را نامعتبر کرد،
    // به آخرین صفحه معتبر برگرد.
    if (page.value > lastPage) {
      page.value = lastPage

      await loadTickets(options)
      return
    }

    tickets.value = result.items
    total.value = result.total
    hasLoadedOnce = true

    if (
        options.clearSelectionIfHidden
        && selectedId.value !== null
        && !result.items.some(
            (ticket) => ticket.id === selectedId.value,
        )
    ) {
      clearSelection()
    }
  } catch (error) {
    if (requestId !== listRequestId) return

    listError.value = readableError(
        error,
        'بارگذاری درخواست‌های پشتیبانی انجام نشد.',
    )
  } finally {
    if (requestId === listRequestId) {
      loading.value = false
      refreshing.value = false
      hasLoadedOnce = true
    }
  }
}

async function loadTicketDetails(
    id: number,
    clearBeforeLoad = true,
): Promise<void> {
  const requestId = ++detailRequestId

  selectedId.value = id

  detailError.value = ''
  replyError.value = ''
  statusError.value = ''
  feedback.value = ''

  if (clearBeforeLoad) {
    selectedTicket.value = null
    replyBody.value = ''
  }

  detailLoading.value = true

  try {
    const ticket = await adminApi.get<AdminTicket>(
        `${BASE_PATH}${id}/`,
    )

    // جزئیات تیکت قبلی نباید روی تیکت انتخاب‌شده جدید بنشیند.
    if (
        requestId !== detailRequestId
        || selectedId.value !== id
    ) {
      return
    }

    selectedTicket.value = ticket
    statusDraft.value = ticket.status
  } catch (error) {
    if (
        requestId !== detailRequestId
        || selectedId.value !== id
    ) {
      return
    }

    detailError.value = readableError(
        error,
        'جزئیات این درخواست بارگذاری نشد.',
    )
  } finally {
    if (requestId === detailRequestId) {
      detailLoading.value = false
    }
  }
}

function openTicket(ticket: AdminTicket): void {
  if (selectedId.value === ticket.id && selectedTicket.value) {
    return
  }

  void loadTicketDetails(ticket.id)
}

function reloadSelectedTicket(): void {
  if (selectedId.value === null) return

  void loadTicketDetails(selectedId.value, false)
}

async function refreshData(): Promise<void> {
  const currentId = selectedId.value

  const tasks: Promise<unknown>[] = [
    loadTickets(),
  ]

  if (currentId !== null) {
    tasks.push(loadTicketDetails(currentId, false))
  }

  await Promise.allSettled(tasks)
}

async function sendReply(): Promise<void> {
  const ticket = selectedTicket.value
  const body = replyBody.value.trim()

  if (
      !ticket
      || ticket.status === 'closed'
      || replying.value
      || body.length < 2
  ) {
    if (body.length < 2) {
      replyError.value = 'متن پاسخ را وارد کنید.'
    }

    return
  }

  const ticketId = ticket.id

  replying.value = true
  replyError.value = ''
  detailError.value = ''
  feedback.value = ''

  try {
    const updatedTicket = await adminApi.post<AdminTicket>(
        `${BASE_PATH}${ticketId}/reply/`,
        {
          body: body,
        },
    )

    if (selectedId.value !== ticketId) return

    selectedTicket.value = updatedTicket
    statusDraft.value = updatedTicket.status
    replyBody.value = ''
    feedback.value = 'پاسخ با موفقیت ارسال شد.'

    // فهرست را تازه کن، اما جزئیات انتخاب‌شده را به‌اجبار نبند.
    await loadTickets()
  } catch (error) {
    if (selectedId.value !== ticketId) return

    replyError.value = readableError(
        error,
        'ارسال پاسخ انجام نشد.',
    )
  } finally {
    replying.value = false
  }
}

async function saveStatus(): Promise<void> {
  const ticket = selectedTicket.value

  if (
      !ticket
      || savingStatus.value
      || statusDraft.value === ticket.status
  ) {
    return
  }

  const ticketId = ticket.id

  savingStatus.value = true
  statusError.value = ''
  feedback.value = ''

  try {
    const updatedTicket = await adminApi.patch<AdminTicket>(
        `${BASE_PATH}${ticketId}/status/`,
        {
          status: statusDraft.value,
        },
    )

    if (selectedId.value !== ticketId) return

    selectedTicket.value = updatedTicket
    statusDraft.value = updatedTicket.status
    feedback.value = 'وضعیت درخواست به‌روزرسانی شد.'

    // اگر تغییر وضعیت باعث حذف تیکت از فیلتر فعلی شود،
    // نمای جزئیات باز می‌ماند.
    await loadTickets()
  } catch (error) {
    if (selectedId.value !== ticketId) return

    statusError.value = readableError(
        error,
        'تغییر وضعیت درخواست انجام نشد.',
    )

    statusDraft.value = ticket.status
  } finally {
    savingStatus.value = false
  }
}

function goToPage(nextPage: number): void {
  if (
      nextPage < 1
      || nextPage > totalPages.value
      || nextPage === page.value
  ) {
    return
  }

  page.value = nextPage

  void loadTickets({
    clearSelectionIfHidden: true,
  })
}

function scheduleFilterRefresh(): void {
  page.value = 1

  if (searchTimer) {
    clearTimeout(searchTimer)
  }

  searchTimer = setTimeout(() => {
    void loadTickets({
      clearSelectionIfHidden: true,
    })
  }, SEARCH_DEBOUNCE_MS)
}

watch(
    [search, statusFilter, categoryFilter, priorityFilter],
    scheduleFilterRefresh,
)

onMounted(() => {
  void loadTickets()
})

onBeforeUnmount(() => {
  if (searchTimer) {
    clearTimeout(searchTimer)
  }

  // پاسخ درخواست‌های در حال اجرا پس از خروج از صفحه نادیده گرفته می‌شوند.
  listRequestId += 1
  detailRequestId += 1
})
</script>

<template>
  <section class="support-tickets-page" dir="rtl">
    <header class="page-heading">
      <div class="page-heading__content">
        <div class="eyebrow">
          <AppIcon name="support" :size="16"/>
          مرکز پشتیبانی
        </div>

        <h1>درخواست‌های پشتیبانی</h1>

        <p>
          درخواست‌های کاربران را بررسی کنید، پاسخ دهید
          و وضعیت پیگیری را مدیریت کنید.
        </p>
      </div>

      <AppButton
          variant="secondary"
          icon="refresh"
          :loading="loading || refreshing"
          @click="refreshData"
      >
        به‌روزرسانی
      </AppButton>
    </header>

    <div class="summary-row">
      <div class="summary-item">
                <span class="summary-item__icon summary-item__icon--blue">
                    <AppIcon name="ticket" :size="19"/>
                </span>

        <div>
          <span>کل درخواست‌های منطبق</span>
          <strong>{{ total.toLocaleString('fa-IR') }}</strong>
        </div>
      </div>

      <div class="summary-item">
                <span class="summary-item__icon summary-item__icon--amber">
                    <AppIcon name="clock" :size="19"/>
                </span>

        <div>
          <span>در انتظار بررسی در این صفحه</span>
          <strong>
            {{
              tickets.filter(
                  (ticket) =>
                      ticket.status === 'open'
                      || ticket.status === 'pending',
              ).length.toLocaleString('fa-IR')
            }}
          </strong>
        </div>
      </div>

      <div class="summary-item">
                <span class="summary-item__icon summary-item__icon--green">
                    <AppIcon name="check" :size="19"/>
                </span>

        <div>
          <span>پاسخ داده‌شده در این صفحه</span>
          <strong>
            {{
              tickets.filter(
                  (ticket) => ticket.status === 'resolved',
              ).length.toLocaleString('fa-IR')
            }}
          </strong>
        </div>
      </div>
    </div>

    <div class="tickets-layout">
      <!-- فهرست درخواست‌ها -->
      <section class="panel tickets-panel">
        <div class="panel-heading">
          <div>
            <h2>فهرست درخواست‌ها</h2>
            <p>برای مشاهده گفت‌وگو، یک درخواست را انتخاب کنید.</p>
          </div>

          <span class="panel-count">
                        {{ total.toLocaleString('fa-IR') }}
                    </span>
        </div>

        <div class="filters">
          <label class="search-field">
            <AppIcon name="search" :size="18"/>

            <input
                v-model="search"
                type="search"
                placeholder="جست‌وجو در شماره، موضوع یا کاربر..."
                aria-label="جست‌وجوی درخواست‌ها"
            />

            <button
                v-if="search"
                type="button"
                class="clear-search"
                aria-label="پاک کردن جست‌وجو"
                @click="search = ''"
            >
              <AppIcon name="close" :size="16"/>
            </button>
          </label>

          <div class="filter-grid">
            <label class="filter-control">
              <span>وضعیت</span>

              <select v-model="statusFilter">
                <option
                    v-for="option in statusOptions"
                    :key="option.value"
                    :value="option.value"
                >
                  {{ option.label }}
                </option>
              </select>
            </label>

            <label class="filter-control">
              <span>دسته‌بندی</span>

              <select v-model="categoryFilter">
                <option
                    v-for="option in categoryOptions"
                    :key="option.value"
                    :value="option.value"
                >
                  {{ option.label }}
                </option>
              </select>
            </label>

            <label class="filter-control">
              <span>اولویت</span>

              <select v-model="priorityFilter">
                <option
                    v-for="option in priorityOptions"
                    :key="option.value"
                    :value="option.value"
                >
                  {{ option.label }}
                </option>
              </select>
            </label>
          </div>
        </div>

        <div
            v-if="listError && tickets.length"
            class="inline-error"
            role="alert"
        >
          <AppIcon name="warning" :size="18"/>
          <span>{{ listError }}</span>

          <button
              type="button"
              aria-label="تلاش دوباره"
              @click="refreshData"
          >
            تلاش دوباره
          </button>
        </div>

        <div
            v-if="loading && !tickets.length"
            class="ticket-skeletons"
            aria-label="در حال بارگذاری درخواست‌ها"
        >
          <div
              v-for="index in 6"
              :key="index"
              class="ticket-skeleton"
          >
            <span class="skeleton skeleton-circle"/>

            <div class="skeleton-content">
              <span class="skeleton skeleton-line skeleton-line--long"/>
              <span class="skeleton skeleton-line skeleton-line--short"/>
              <span class="skeleton skeleton-line skeleton-line--medium"/>
            </div>
          </div>
        </div>

        <div
            v-else-if="listError && !tickets.length"
            class="empty-panel"
            role="alert"
        >
                    <span class="empty-panel__icon empty-panel__icon--error">
                        <AppIcon name="warning" :size="26"/>
                    </span>

          <h3>بارگذاری انجام نشد</h3>
          <p>{{ listError }}</p>

          <AppButton
              variant="secondary"
              icon="refresh"
              :loading="refreshing"
              @click="refreshData"
          >
            تلاش دوباره
          </AppButton>
        </div>

        <div
            v-else-if="!tickets.length"
            class="empty-panel"
        >
                    <span class="empty-panel__icon">
                        <AppIcon name="ticket" :size="26"/>
                    </span>

          <h3>درخواستی پیدا نشد</h3>

          <p>
            با تغییر فیلترها یا عبارت جست‌وجو دوباره بررسی کنید.
          </p>

          <button
              v-if="
                            search
                            || statusFilter
                            || categoryFilter
                            || priorityFilter
                        "
              type="button"
              class="text-action"
              @click="
                            search = '';
                            statusFilter = '';
                            categoryFilter = '';
                            priorityFilter = ''
                        "
          >
            پاک کردن فیلترها
          </button>
        </div>

        <div v-else class="ticket-list">
          <button
              v-for="ticket in tickets"
              :key="ticket.id"
              type="button"
              class="ticket-list-item"
              :class="{
                            'ticket-list-item--active':
                                selectedId === ticket.id,
                        }"
              :aria-pressed="selectedId === ticket.id"
              @click="openTicket(ticket)"
          >
                        <span
                            class="ticket-list-item__icon"
                            :class="statusClass(ticket.status)"
                        >
                            <AppIcon name="message" :size="20"/>
                        </span>

            <span class="ticket-list-item__body">
                            <span class="ticket-list-item__top">
                                <strong class="ticket-number" dir="ltr">
                                    {{ ticket.ticketNumber }}
                                </strong>

                                <span
                                    class="status-pill"
                                    :class="statusClass(ticket.status)"
                                >
                                    {{ statusLabel(ticket.status) }}
                                </span>
                            </span>

                            <strong class="ticket-subject">
                                {{ ticket.subject }}
                            </strong>

                            <span class="ticket-user">
                                <AppIcon name="user" :size="14"/>
                                {{ ticket.userName || 'کاربر' }}
                            </span>

                            <span class="ticket-list-item__bottom">
                                <span>
                                    {{ categoryLabel(ticket.category) }}
                                </span>

                                <span
                                    class="priority-label"
                                    :class="priorityClass(ticket.priority)"
                                >
                                    {{ priorityLabel(ticket.priority) }}
                                </span>

                                <span class="ticket-date">
                                    {{ formatDate(ticket.updatedAt) }}
                                </span>
                            </span>
                        </span>

            <AppIcon
                name="chevronLeft"
                :size="17"
                class="ticket-chevron"
            />
          </button>
        </div>

        <footer
            v-if="total > PAGE_SIZE"
            class="pagination"
        >
                    <span>
                        {{ firstVisibleItem.toLocaleString('fa-IR') }}
                        تا
                        {{ lastVisibleItem.toLocaleString('fa-IR') }}
                        از
                        {{ total.toLocaleString('fa-IR') }}
                    </span>

          <div class="pagination__controls">
            <button
                type="button"
                aria-label="صفحه قبلی"
                :disabled="page <= 1 || loading || refreshing"
                @click="goToPage(page - 1)"
            >
              <AppIcon name="chevronRight" :size="17"/>
            </button>

            <span>
                            {{ page.toLocaleString('fa-IR') }}
                            /
                            {{ totalPages.toLocaleString('fa-IR') }}
                        </span>

            <button
                type="button"
                aria-label="صفحه بعدی"
                :disabled="
                                page >= totalPages
                                || loading
                                || refreshing
                            "
                @click="goToPage(page + 1)"
            >
              <AppIcon name="chevronLeft" :size="17"/>
            </button>
          </div>
        </footer>
      </section>

      <!-- جزئیات و گفت‌وگوی درخواست -->
      <section class="panel detail-panel">
        <div
            v-if="detailLoading && !selectedTicket"
            class="detail-loading"
        >
          <span class="skeleton skeleton-circle skeleton-circle--large"/>
          <span class="skeleton skeleton-line skeleton-line--long"/>
          <span class="skeleton skeleton-line skeleton-line--medium"/>
          <span class="skeleton skeleton-line skeleton-line--long"/>
          <span class="skeleton skeleton-line skeleton-line--short"/>
        </div>

        <div
            v-else-if="detailError && !selectedTicket"
            class="empty-panel"
            role="alert"
        >
                    <span class="empty-panel__icon empty-panel__icon--error">
                        <AppIcon name="warning" :size="26"/>
                    </span>

          <h3>جزئیات بارگذاری نشد</h3>
          <p>{{ detailError }}</p>

          <AppButton
              variant="secondary"
              icon="refresh"
              :loading="detailLoading"
              @click="reloadSelectedTicket"
          >
            تلاش دوباره
          </AppButton>
        </div>

        <div
            v-else-if="!selectedTicket"
            class="detail-placeholder"
        >
                    <span class="detail-placeholder__icon">
                        <AppIcon name="message" :size="31"/>
                    </span>

          <h2>یک درخواست را انتخاب کنید</h2>

          <p>
            جزئیات درخواست، پیام‌های کاربر و ابزار پاسخ‌گویی
            در این قسمت نمایش داده می‌شود.
          </p>
        </div>

        <template v-else>
          <header class="detail-heading">
            <div class="detail-heading__main">
                            <span class="detail-heading__icon">
                                <AppIcon name="ticket" :size="22"/>
                            </span>

              <div class="detail-heading__text">
                <div class="detail-heading__eyebrow">
                                    <span dir="ltr">
                                        {{ selectedTicket.ticketNumber }}
                                    </span>

                  <span>·</span>

                  <span>
                                        {{ categoryLabel(selectedTicket.category) }}
                                    </span>
                </div>

                <h2>{{ selectedTicket.subject }}</h2>

                <p>
                  ثبت درخواست:
                  {{ formatDate(selectedTicket.createdAt) }}
                </p>
              </div>
            </div>

            <button
                type="button"
                class="icon-button"
                :disabled="detailLoading"
                aria-label="بارگذاری مجدد جزئیات"
                @click="reloadSelectedTicket"
            >
              <AppIcon name="refresh" :size="18"/>
            </button>
          </header>

          <div
              v-if="feedback"
              class="feedback-banner"
              role="status"
          >
            <AppIcon name="check" :size="18"/>
            <span>{{ feedback }}</span>

            <button
                type="button"
                aria-label="بستن پیام"
                @click="feedback = ''"
            >
              <AppIcon name="close" :size="16"/>
            </button>
          </div>

          <div
              v-if="detailError"
              class="inline-error detail-inline-error"
              role="alert"
          >
            <AppIcon name="warning" :size="17"/>
            <span>{{ detailError }}</span>
          </div>

          <div class="ticket-meta">
            <div class="meta-item">
              <span>وضعیت فعلی</span>

              <span
                  class="status-pill"
                  :class="statusClass(selectedTicket.status)"
              >
                                {{ statusLabel(selectedTicket.status) }}
                            </span>
            </div>

            <div class="meta-item">
              <span>اولویت</span>

              <span
                  class="priority-label"
                  :class="priorityClass(selectedTicket.priority)"
              >
                                {{ priorityLabel(selectedTicket.priority) }}
                            </span>
            </div>

            <div class="meta-item">
              <span>آخرین به‌روزرسانی</span>
              <strong>
                {{ formatDate(selectedTicket.updatedAt) }}
              </strong>
            </div>
          </div>

          <div class="user-card">
                        <span class="user-card__avatar">
                            <AppIcon name="user" :size="21"/>
                        </span>

            <div class="user-card__main">
              <strong>
                {{ selectedTicket.userName || 'کاربر' }}
              </strong>

              <div class="user-card__contacts">
                                <span v-if="selectedTicket.userPhone">
                                    <AppIcon name="phone" :size="14"/>
                                    <span dir="ltr">
                                        {{ selectedTicket.userPhone }}
                                    </span>
                                </span>

                <span v-if="selectedTicket.userEmail">
                                    <AppIcon name="mail" :size="14"/>
                                    <span dir="ltr">
                                        {{ selectedTicket.userEmail }}
                                    </span>
                                </span>
              </div>
            </div>
          </div>

          <section class="status-editor">
            <label for="ticket-status">تغییر وضعیت درخواست</label>

            <div class="status-editor__controls">
              <select
                  id="ticket-status"
                  v-model="statusDraft"
                  :disabled="savingStatus"
              >
                <option
                    v-for="option in statusOptions.filter(
                                        (item) => item.value !== '',
                                    )"
                    :key="option.value"
                    :value="option.value"
                >
                  {{ option.label }}
                </option>
              </select>

              <AppButton
                  variant="secondary"
                  size="sm"
                  :disabled="!hasStatusChanges || savingStatus"
                  :loading="savingStatus"
                  @click="saveStatus"
              >
                ثبت وضعیت
              </AppButton>
            </div>

            <p
                v-if="statusError"
                class="field-error"
                role="alert"
            >
              {{ statusError }}
            </p>
          </section>

          <div
              v-if="
                            !isSelectedTicketInCurrentList
                            && (search || statusFilter || categoryFilter || priorityFilter)
                        "
              class="filter-context-note"
          >
            این درخواست با فیلترهای فعلی در فهرست دیده نمی‌شود،
            اما جزئیات آن همچنان باز است.
          </div>

          <div class="conversation-heading">
            <div>
              <h3>گفت‌وگو</h3>
              <p>پیام‌های ثبت‌شده برای این درخواست</p>
            </div>

            <span class="message-count">
                            {{
                (selectedTicket.messages?.length ?? 0)
                    .toLocaleString('fa-IR')
              }}
                            پیام
                        </span>
          </div>

          <div
              v-if="detailLoading && selectedTicket"
              class="detail-refreshing"
              role="status"
          >
            <span class="loading-dot"/>
            در حال به‌روزرسانی جزئیات...
          </div>

          <div
              v-if="!selectedTicket.messages?.length"
              class="messages-empty"
          >
            هنوز پیامی برای این درخواست ثبت نشده است.
          </div>

          <div
              v-else
              class="message-thread"
              aria-live="polite"
          >
            <article
                v-for="message in selectedTicket.messages"
                :key="message.id"
                class="message-item"
                :class="{
                                'message-item--support': message.sender === 'support',
                                'message-item--user': message.sender === 'user',
                            }"
            >
                            <span
                                class="message-avatar"
                                :class="{
                                    'message-avatar--support': message.sender === 'support',
                                }"
                            >
                                <AppIcon
                                    :name="
                                        message.sender === 'support'
                                            ? 'support'
                                            : 'user'
                                    "
                                    :size="18"
                                />
                            </span>

              <div class="message-card">
                <div class="message-card__header">
                  <strong>
                    {{ message.senderName }}
                  </strong>

                  <time :datetime="message.createdAt">
                    {{ formatDate(message.createdAt) }}
                  </time>
                </div>

                <p>{{ message.body }}</p>
              </div>
            </article>
          </div>

          <div
              v-if="selectedTicket.status === 'closed'"
              class="closed-notice"
          >
            <AppIcon name="lock" :size="20"/>

            <div>
              <strong>این درخواست بسته شده است.</strong>
              <p>
                وضعیت درخواست را به حالت دیگری تغییر دهید
                تا امکان ادامه پیگیری فراهم شود.
              </p>
            </div>
          </div>

          <form
              v-else
              class="reply-composer"
              @submit.prevent="sendReply"
          >
            <label for="ticket-reply">پاسخ مدیر</label>

            <textarea
                id="ticket-reply"
                v-model="replyBody"
                rows="4"
                maxlength="10000"
                placeholder="پاسخ خود را بنویسید..."
                :disabled="replying"
                :aria-invalid="Boolean(replyError)"
                @input="replyError = ''"
            />

            <div class="reply-composer__footer">
                            <span>
                                {{ replyBody.length.toLocaleString('fa-IR') }}
                                / ۱۰٬۰۰۰
                            </span>

              <AppButton
                  type="submit"
                  icon="send"
                  :loading="replying"
                  :disabled="replyBody.trim().length < 2"
              >
                ارسال پاسخ
              </AppButton>
            </div>

            <p
                v-if="replyError"
                class="field-error"
                role="alert"
            >
              {{ replyError }}
            </p>
          </form>
        </template>
      </section>
    </div>
  </section>
</template>

<style scoped>
.support-tickets-page {
  display: grid;
  gap: 1.25rem;
  min-width: 0;
  color: var(--color-text-primary);
}

.page-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
}

.page-heading__content {
  min-width: 0;
}

.eyebrow {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  margin-bottom: 0.45rem;
  color: var(--color-primary);
  font-size: var(--font-size-xs);
  font-weight: 700;
}

.page-heading h1 {
  margin: 0;
  font-size: clamp(1.25rem, 2.1vw, 1.8rem);
  line-height: 1.6;
}

.page-heading p {
  margin: 0.25rem 0 0;
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
  line-height: 1.9;
}

.summary-row {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.85rem;
}

.summary-item {
  display: flex;
  align-items: center;
  gap: 0.85rem;
  min-width: 0;
  padding: 1rem;
  border: 1px solid var(--color-border-soft);
  border-radius: 1rem;
  background: var(--color-surface-1);
}

.summary-item > div {
  display: grid;
  gap: 0.25rem;
  min-width: 0;
}

.summary-item > div > span {
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
  line-height: 1.7;
}

.summary-item strong {
  font-size: 1.2rem;
  font-variant-numeric: tabular-nums;
}

.summary-item__icon {
  display: grid;
  flex: 0 0 auto;
  width: 2.75rem;
  height: 2.75rem;
  border-radius: 0.85rem;
  place-items: center;
}

.summary-item__icon--blue {
  color: var(--color-primary);
  background: var(--color-primary-soft);
}

.summary-item__icon--amber {
  color: var(--color-warning);
  background: var(--color-warning-soft);
}

.summary-item__icon--green {
  color: var(--color-success);
  background: var(--color-success-soft);
}

.tickets-layout {
  display: grid;
  grid-template-columns: minmax(19rem, 0.85fr) minmax(0, 1.5fr);
  align-items: start;
  gap: 1rem;
  min-width: 0;
}

.panel {
  min-width: 0;
  overflow: hidden;
  border: 1px solid var(--color-border-soft);
  border-radius: 1rem;
  background: var(--color-surface-1);
}

.panel-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 1.1rem 1.15rem;
  border-bottom: 1px solid var(--color-border-soft);
}

.panel-heading h2 {
  margin: 0;
  font-size: var(--font-size-md);
}

.panel-heading p {
  margin: 0.3rem 0 0;
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
  line-height: 1.8;
}

.panel-count,
.message-count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 auto;
  min-height: 1.8rem;
  padding: 0.2rem 0.6rem;
  border: 1px solid var(--color-border-soft);
  border-radius: 0.65rem;
  background: var(--color-surface-2);
  color: var(--color-text-secondary);
  font-size: var(--font-size-xs);
  font-variant-numeric: tabular-nums;
}

.filters {
  display: grid;
  gap: 0.8rem;
  padding: 1rem;
  border-bottom: 1px solid var(--color-border-soft);
  background: var(--color-surface);
}

.search-field {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  min-width: 0;
  min-height: 2.8rem;
  padding-inline: 0.8rem;
  border: 1px solid var(--color-border);
  border-radius: 0.75rem;
  background: var(--color-surface-1);
  color: var(--color-text-muted);
  transition: border-color var(--transition-fast),
  box-shadow var(--transition-fast);
}

.search-field:focus-within {
  border-color: var(--color-border-focus);
  box-shadow: var(--shadow-focus);
}

.search-field input {
  width: 100%;
  min-width: 0;
  padding: 0.65rem 0;
  border: 0;
  outline: 0;
  background: transparent;
  color: var(--color-text-primary);
  font: inherit;
  font-size: var(--font-size-xs);
}

.search-field input::placeholder {
  color: var(--color-text-muted);
}

.search-field input::-webkit-search-cancel-button {
  display: none;
}

.clear-search,
.icon-button {
  display: grid;
  flex: 0 0 auto;
  width: 2.25rem;
  height: 2.25rem;
  border: 0;
  border-radius: 0.6rem;
  background: transparent;
  color: var(--color-text-muted);
  place-items: center;
  cursor: pointer;
}

.clear-search:hover,
.icon-button:hover:not(:disabled) {
  background: var(--color-surface-3);
  color: var(--color-text-primary);
}

.filter-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.55rem;
}

.filter-control {
  display: grid;
  gap: 0.35rem;
  min-width: 0;
}

.filter-control > span,
.status-editor > label,
.reply-composer > label {
  color: var(--color-text-secondary);
  font-size: var(--font-size-xs);
  font-weight: 650;
}

.filter-control select,
.status-editor select {
  width: 100%;
  min-width: 0;
  min-height: 2.65rem;
  padding: 0.4rem 0.55rem;
  border: 1px solid var(--color-border);
  border-radius: 0.65rem;
  outline: 0;
  background: var(--color-surface-1);
  color: var(--color-text-primary);
  font: inherit;
  font-size: var(--font-size-xs);
}

.filter-control select:focus,
.status-editor select:focus {
  border-color: var(--color-border-focus);
  box-shadow: var(--shadow-focus);
}

.ticket-list {
  display: grid;
}

.ticket-list-item {
  display: flex;
  align-items: flex-start;
  gap: 0.7rem;
  width: 100%;
  min-width: 0;
  padding: 1rem 0.9rem;
  border: 0;
  border-bottom: 1px solid var(--color-border-soft);
  background: transparent;
  color: inherit;
  text-align: start;
  cursor: pointer;
  transition: background var(--transition-fast),
  box-shadow var(--transition-fast);
}

.ticket-list-item:last-child {
  border-bottom: 0;
}

.ticket-list-item:hover {
  background: var(--color-surface-2);
}

.ticket-list-item--active {
  background: var(--color-primary-soft);
  box-shadow: inset -3px 0 var(--color-primary);
}

.ticket-list-item__icon {
  display: grid;
  flex: 0 0 auto;
  width: 2.45rem;
  height: 2.45rem;
  border-radius: 0.75rem;
  background: var(--color-surface-3);
  color: var(--color-text-secondary);
  place-items: center;
}

.ticket-list-item__icon.status-open {
  color: var(--color-primary);
  background: var(--color-primary-soft);
}

.ticket-list-item__icon.status-pending {
  color: var(--color-warning);
  background: var(--color-warning-soft);
}

.ticket-list-item__icon.status-resolved {
  color: var(--color-success);
  background: var(--color-success-soft);
}

.ticket-list-item__body {
  display: grid;
  flex: 1;
  gap: 0.45rem;
  min-width: 0;
}

.ticket-list-item__top,
.ticket-list-item__bottom {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.4rem;
  min-width: 0;
}

.ticket-list-item__top {
  justify-content: space-between;
}

.ticket-number {
  color: var(--color-primary);
  font-size: 0.7rem;
  font-weight: 750;
}

.ticket-subject {
  display: -webkit-box;
  overflow: hidden;
  color: var(--color-text-primary);
  font-size: var(--font-size-sm);
  font-weight: 650;
  line-height: 1.8;
  overflow-wrap: anywhere;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.ticket-user {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
}

.ticket-list-item__bottom {
  color: var(--color-text-muted);
  font-size: 0.68rem;
}

.ticket-date {
  margin-inline-start: auto;
  font-variant-numeric: tabular-nums;
}

.status-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: fit-content;
  max-width: 100%;
  padding: 0.2rem 0.5rem;
  border: 1px solid transparent;
  border-radius: 999px;
  font-size: 0.66rem;
  font-weight: 650;
  line-height: 1.7;
  overflow-wrap: anywhere;
}

.status-open {
  border-color: color-mix(in srgb, var(--color-primary) 25%, transparent);
  background: var(--color-primary-soft);
  color: var(--color-primary);
}

.status-pending {
  border-color: color-mix(in srgb, var(--color-warning) 28%, transparent);
  background: var(--color-warning-soft);
  color: var(--color-warning);
}

.status-resolved {
  border-color: color-mix(in srgb, var(--color-success) 25%, transparent);
  background: var(--color-success-soft);
  color: var(--color-success);
}

.status-closed {
  border-color: var(--color-border);
  background: var(--color-surface-3);
  color: var(--color-text-muted);
}

.priority-label {
  display: inline-flex;
  align-items: center;
  width: fit-content;
  font-size: 0.7rem;
  font-weight: 700;
}

.priority-low {
  color: var(--color-text-muted);
}

.priority-medium {
  color: var(--color-info);
}

.priority-high {
  color: var(--color-warning);
}

.priority-urgent {
  color: var(--color-danger);
}

.ticket-chevron {
  flex: 0 0 auto;
  margin-top: 0.35rem;
  color: var(--color-text-muted);
}

.pagination {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.7rem;
  padding: 0.8rem 1rem;
  border-top: 1px solid var(--color-border-soft);
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
}

.pagination__controls {
  display: flex;
  align-items: center;
  gap: 0.55rem;
  color: var(--color-text-secondary);
  font-variant-numeric: tabular-nums;
}

.pagination__controls button {
  display: grid;
  width: 2.25rem;
  height: 2.25rem;
  border: 1px solid var(--color-border);
  border-radius: 0.65rem;
  background: var(--color-surface-1);
  color: var(--color-text-primary);
  place-items: center;
  cursor: pointer;
}

.pagination__controls button:hover:not(:disabled) {
  border-color: var(--color-border-focus);
  background: var(--color-surface-2);
}

.pagination__controls button:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.empty-panel,
.detail-placeholder {
  display: grid;
  justify-items: center;
  gap: 0.75rem;
  padding: 3rem 1.25rem;
  text-align: center;
}

.empty-panel__icon,
.detail-placeholder__icon {
  display: grid;
  width: 3.6rem;
  height: 3.6rem;
  border-radius: 1.1rem;
  background: var(--color-primary-soft);
  color: var(--color-primary);
  place-items: center;
}

.empty-panel__icon--error {
  background: var(--color-danger-soft);
  color: var(--color-danger);
}

.empty-panel h3,
.detail-placeholder h2 {
  margin: 0;
  font-size: var(--font-size-md);
}

.empty-panel p,
.detail-placeholder p {
  max-width: 23rem;
  margin: 0;
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
  line-height: 1.9;
}

.text-action {
  min-height: 2.5rem;
  padding: 0.45rem 0.7rem;
  border: 0;
  border-radius: 0.6rem;
  background: transparent;
  color: var(--color-primary);
  font: inherit;
  font-size: var(--font-size-sm);
  cursor: pointer;
}

.text-action:hover {
  background: var(--color-primary-soft);
}

.ticket-skeletons {
  display: grid;
}

.ticket-skeleton {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  padding: 1.05rem 0.9rem;
  border-bottom: 1px solid var(--color-border-soft);
}

.skeleton {
  display: block;
  border-radius: 0.5rem;
  background: var(--color-surface-3);
  animation: skeleton-pulse 1.35s ease-in-out infinite;
}

.skeleton-circle {
  flex: 0 0 auto;
  width: 2.45rem;
  height: 2.45rem;
  border-radius: 0.75rem;
}

.skeleton-circle--large {
  width: 3.5rem;
  height: 3.5rem;
  border-radius: 1rem;
}

.skeleton-content {
  display: grid;
  flex: 1;
  gap: 0.65rem;
}

.skeleton-line {
  height: 0.7rem;
}

.skeleton-line--long {
  width: 85%;
}

.skeleton-line--medium {
  width: 60%;
}

.skeleton-line--short {
  width: 35%;
}

.inline-error {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.8rem 1rem;
  background: var(--color-danger-soft);
  color: var(--color-danger);
  font-size: var(--font-size-xs);
  line-height: 1.8;
}

.inline-error span {
  flex: 1;
  min-width: 0;
  overflow-wrap: anywhere;
}

.inline-error button {
  flex: 0 0 auto;
  padding: 0.3rem 0.45rem;
  border: 0;
  border-radius: 0.4rem;
  background: transparent;
  color: inherit;
  font: inherit;
  font-weight: 700;
  cursor: pointer;
}

.detail-panel {
  display: grid;
  min-height: 40rem;
  align-content: start;
}

.detail-loading {
  display: grid;
  justify-items: start;
  gap: 1rem;
  padding: 2rem;
}

.detail-loading .skeleton {
  max-width: 100%;
}

.detail-heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.8rem;
  padding: 1.25rem;
  border-bottom: 1px solid var(--color-border-soft);
}

.detail-heading__main {
  display: flex;
  align-items: flex-start;
  gap: 0.85rem;
  min-width: 0;
}

.detail-heading__icon {
  display: grid;
  flex: 0 0 auto;
  width: 3rem;
  height: 3rem;
  border-radius: 0.9rem;
  background: var(--color-primary-soft);
  color: var(--color-primary);
  place-items: center;
}

.detail-heading__text {
  min-width: 0;
}

.detail-heading__eyebrow {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.4rem;
  margin-bottom: 0.25rem;
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
}

.detail-heading__eyebrow span:first-child {
  color: var(--color-primary);
  font-weight: 700;
}

.detail-heading h2 {
  margin: 0;
  font-size: var(--font-size-md);
  line-height: 1.8;
  overflow-wrap: anywhere;
}

.detail-heading p {
  margin: 0.3rem 0 0;
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
}

.icon-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.feedback-banner {
  display: flex;
  align-items: center;
  gap: 0.55rem;
  padding: 0.75rem 1rem;
  background: var(--color-success-soft);
  color: var(--color-success);
  font-size: var(--font-size-sm);
}

.feedback-banner span {
  flex: 1;
}

.feedback-banner button {
  display: grid;
  width: 2rem;
  height: 2rem;
  border: 0;
  border-radius: 0.5rem;
  background: transparent;
  color: inherit;
  place-items: center;
  cursor: pointer;
}

.detail-inline-error {
  border-top: 1px solid var(--color-border-soft);
  border-bottom: 1px solid var(--color-border-soft);
}

.ticket-meta {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.8rem;
  padding: 1rem 1.25rem;
  border-bottom: 1px solid var(--color-border-soft);
}

.meta-item {
  display: grid;
  align-content: start;
  justify-items: start;
  gap: 0.4rem;
  min-width: 0;
}

.meta-item > span:first-child {
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
}

.meta-item > strong {
  font-size: var(--font-size-xs);
  font-weight: 650;
  overflow-wrap: anywhere;
}

.user-card {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  min-width: 0;
  padding: 1rem 1.25rem;
  border-bottom: 1px solid var(--color-border-soft);
}

.user-card__avatar {
  display: grid;
  flex: 0 0 auto;
  width: 2.75rem;
  height: 2.75rem;
  border-radius: 50%;
  background: var(--color-surface-3);
  color: var(--color-text-secondary);
  place-items: center;
}

.user-card__main {
  display: grid;
  gap: 0.35rem;
  min-width: 0;
}

.user-card__main > strong {
  overflow-wrap: anywhere;
  font-size: var(--font-size-sm);
}

.user-card__contacts {
  display: flex;
  flex-wrap: wrap;
  gap: 0.6rem 1rem;
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
}

.user-card__contacts > span {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  min-width: 0;
  overflow-wrap: anywhere;
}

.status-editor {
  display: grid;
  gap: 0.55rem;
  padding: 1rem 1.25rem;
  border-bottom: 1px solid var(--color-border-soft);
  background: var(--color-surface);
}

.status-editor__controls {
  display: flex;
  align-items: center;
  gap: 0.65rem;
}

.status-editor__controls select {
  max-width: 20rem;
}

.field-error {
  margin: 0;
  color: var(--color-danger);
  font-size: var(--font-size-xs);
  line-height: 1.8;
  overflow-wrap: anywhere;
}

.filter-context-note {
  padding: 0.7rem 1.25rem;
  border-bottom: 1px solid var(--color-border-soft);
  background: var(--color-surface-2);
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
  line-height: 1.9;
}

.conversation-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 1.1rem 1.25rem;
  border-bottom: 1px solid var(--color-border-soft);
}

.conversation-heading h3 {
  margin: 0;
  font-size: var(--font-size-md);
}

.conversation-heading p {
  margin: 0.25rem 0 0;
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
}

.detail-refreshing {
  display: flex;
  align-items: center;
  gap: 0.55rem;
  padding: 0.65rem 1.25rem;
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
}

.loading-dot {
  width: 0.45rem;
  height: 0.45rem;
  border-radius: 50%;
  background: var(--color-primary);
  animation: skeleton-pulse 1s ease-in-out infinite;
}

.message-thread {
  display: grid;
  gap: 1rem;
  max-height: 32rem;
  overflow-y: auto;
  padding: 1.25rem;
  overscroll-behavior: contain;
}

.message-item {
  display: flex;
  align-items: flex-start;
  gap: 0.65rem;
  min-width: 0;
}

.message-item--user {
  flex-direction: row-reverse;
}

.message-avatar {
  display: grid;
  flex: 0 0 auto;
  width: 2.25rem;
  height: 2.25rem;
  border-radius: 0.75rem;
  background: var(--color-surface-3);
  color: var(--color-text-secondary);
  place-items: center;
}

.message-avatar--support {
  background: var(--color-primary-soft);
  color: var(--color-primary);
}

.message-card {
  flex: 0 1 auto;
  min-width: 0;
  max-width: 88%;
  padding: 0.8rem 0.9rem;
  border: 1px solid var(--color-border-soft);
  border-radius: 0.85rem;
  background: var(--color-surface-2);
}

.message-item--support .message-card {
  border-color: color-mix(in srgb, var(--color-primary) 18%, transparent);
  background: var(--color-primary-soft);
}

.message-card__header {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 0.35rem 1rem;
}

.message-card__header strong {
  font-size: var(--font-size-xs);
}

.message-card__header time {
  color: var(--color-text-muted);
  font-size: 0.68rem;
}

.message-card p {
  margin: 0.5rem 0 0;
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  line-height: 2;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}

.messages-empty {
  padding: 2rem 1.25rem;
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
  text-align: center;
}

.closed-notice {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  margin: 0 1.25rem 1.25rem;
  padding: 0.9rem;
  border: 1px solid var(--color-border-soft);
  border-radius: 0.85rem;
  background: var(--color-surface-2);
  color: var(--color-text-secondary);
}

.closed-notice > svg {
  flex: 0 0 auto;
}

.closed-notice strong {
  font-size: var(--font-size-sm);
}

.closed-notice p {
  margin: 0.3rem 0 0;
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
  line-height: 1.9;
}

.reply-composer {
  display: grid;
  gap: 0.6rem;
  padding: 1.25rem;
  border-top: 1px solid var(--color-border-soft);
  background: var(--color-surface);
}

.reply-composer textarea {
  width: 100%;
  min-width: 0;
  min-height: 7rem;
  padding: 0.8rem 0.9rem;
  border: 1px solid var(--color-border);
  border-radius: 0.75rem;
  outline: 0;
  background: var(--color-surface-1);
  color: var(--color-text-primary);
  font: inherit;
  font-size: var(--font-size-sm);
  line-height: 1.9;
  resize: vertical;
  transition: border-color var(--transition-fast),
  box-shadow var(--transition-fast);
}

.reply-composer textarea:focus {
  border-color: var(--color-border-focus);
  box-shadow: var(--shadow-focus);
}

.reply-composer textarea:disabled {
  opacity: 0.65;
  cursor: wait;
}

.reply-composer textarea[aria-invalid='true'] {
  border-color: var(--color-danger);
}

.reply-composer__footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
}

.reply-composer__footer > span {
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
  font-variant-numeric: tabular-nums;
}

@keyframes skeleton-pulse {
  0%,
  100% {
    opacity: 0.5;
  }

  50% {
    opacity: 1;
  }
}

@media (max-width: 1150px) {
  .tickets-layout {
    grid-template-columns: minmax(17rem, 0.9fr) minmax(0, 1.2fr);
  }

  .filter-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 850px) {
  .tickets-layout {
    grid-template-columns: minmax(0, 1fr);
  }

  .detail-panel {
    min-height: 24rem;
  }

  .filter-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 600px) {
  .support-tickets-page {
    gap: 0.9rem;
  }

  .page-heading {
    align-items: flex-start;
    flex-direction: column;
  }

  .page-heading > :deep(.app-button) {
    width: 100%;
  }

  .summary-row {
    grid-template-columns: 1fr;
    gap: 0.6rem;
  }

  .summary-item {
    padding: 0.8rem;
  }

  .summary-item__icon {
    width: 2.5rem;
    height: 2.5rem;
  }

  .filter-grid {
    grid-template-columns: 1fr;
  }

  .ticket-list-item {
    padding: 0.9rem 0.7rem;
  }

  .ticket-list-item__top {
    align-items: flex-start;
    flex-direction: column;
  }

  .ticket-date {
    width: 100%;
    margin-inline-start: 0;
  }

  .detail-heading {
    padding: 1rem;
  }

  .detail-heading__main {
    gap: 0.6rem;
  }

  .detail-heading__icon {
    width: 2.5rem;
    height: 2.5rem;
  }

  .ticket-meta {
    grid-template-columns: 1fr 1fr;
    padding: 0.9rem 1rem;
  }

  .ticket-meta > :last-child {
    grid-column: 1 / -1;
  }

  .user-card {
    padding: 0.9rem 1rem;
  }

  .status-editor {
    padding: 0.9rem 1rem;
  }

  .status-editor__controls {
    align-items: stretch;
    flex-direction: column;
  }

  .status-editor__controls select {
    max-width: none;
  }

  .conversation-heading {
    padding: 0.9rem 1rem;
  }

  .message-thread {
    padding: 1rem;
  }

  .message-card {
    max-width: 94%;
    padding: 0.7rem;
  }

  .message-avatar {
    width: 2rem;
    height: 2rem;
  }

  .reply-composer {
    padding: 1rem;
  }

  .pagination {
    flex-wrap: wrap;
  }
}

@media (prefers-reduced-motion: reduce) {
  .skeleton,
  .loading-dot {
    animation: none;
  }

  *,
  *::before,
  *::after {
    scroll-behavior: auto !important;
    transition-duration: 0.01ms !important;
  }
}
</style>