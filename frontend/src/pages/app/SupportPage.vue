<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { SUPPORT_CATEGORIES, supportCategoryMeta } from '@/components/support/supportMeta'
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
import { ApiError, supportService } from '@/services'
import type { CreateTicketInput, FaqItem, SupportCategory, SupportTicket, TicketStatus } from '@/types'
import { formatPersianDateTime, toPersianDigits } from '@/utils/formatters'

const route = useRoute()
const router = useRouter()
const section = ref<'faq' | 'tickets'>(route.query.tab === 'tickets' ? 'tickets' : 'faq')
const faqSearch = ref('')
const faqCategory = ref<SupportCategory | ''>('')
const faqs = ref<FaqItem[]>([])
const faqsLoading = ref(true)
const faqsError = ref('')
const openFaqId = ref('')

const tickets = ref<SupportTicket[]>([])
const ticketsTotal = ref(0)
const ticketsLoading = ref(true)
const ticketsError = ref('')
const ticketSearch = ref('')
const ticketStatus = ref<TicketStatus | ''>('')

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
  { label: 'راهنما و سؤالات', value: 'faq' },
  { label: 'درخواست‌های من', value: 'tickets' },
]
const ticketStatuses: Array<{ value: TicketStatus | ''; label: string }> = [
  { value: '', label: 'همه وضعیت‌ها' },
  { value: 'open', label: 'باز' },
  { value: 'waiting_for_user', label: 'در انتظار پاسخ شما' },
  { value: 'answered', label: 'پاسخ داده شده' },
  { value: 'closed', label: 'بسته شده' },
]
const ticketCategoryOptions = SUPPORT_CATEGORIES.map(({ value, label }) => ({ value, label }))

const faqCountLabel = computed(() => faqsLoading.value ? 'در حال جست‌وجو…' : `${toPersianDigits(faqs.value.length)} پاسخ`)

function readableError(caught: unknown, fallback: string): string {
  return caught instanceof Error ? caught.message : fallback
}

async function loadFaqs(): Promise<void> {
  faqsLoading.value = true
  faqsError.value = ''
  try {
    faqs.value = await supportService.listFaqs(faqSearch.value, faqCategory.value || undefined)
    if (openFaqId.value && !faqs.value.some((faq) => faq.id === openFaqId.value)) openFaqId.value = ''
  } catch (caught) {
    faqsError.value = readableError(caught, 'پاسخ‌های راهنما بارگیری نشدند.')
  } finally {
    faqsLoading.value = false
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
    })
    tickets.value = result.items
    ticketsTotal.value = result.total
  } catch (caught) {
    ticketsError.value = readableError(caught, 'درخواست‌های پشتیبانی بارگیری نشدند.')
  } finally {
    ticketsLoading.value = false
  }
}

function openCreate(category?: SupportCategory): void {
  createError.value = ''
  Object.keys(fieldErrors).forEach((key) => delete fieldErrors[key])
  if (category) ticketForm.category = category
  createOpen.value = true
  if (route.query.new !== '1') {
    void router.replace({ query: { ...route.query, new: '1' } })
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
  const query = { ...route.query }
  delete query.new
  delete query.orderId
  void router.replace({ query })
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
  if (faqTimer) clearTimeout(faqTimer)
  faqTimer = setTimeout(loadFaqs, 220)
})

let ticketTimer: ReturnType<typeof setTimeout> | undefined
watch([ticketSearch, ticketStatus], () => {
  if (ticketTimer) clearTimeout(ticketTimer)
  ticketTimer = setTimeout(loadTickets, 220)
})

watch(section, (value) => {
  const tab = value === 'tickets' ? 'tickets' : undefined
  if (route.query.tab === tab || (!tab && route.query.tab === undefined)) return
  void router.replace({ query: { ...route.query, tab } })
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
  { immediate: true },
)

onMounted(() => {
  void Promise.all([loadFaqs(), loadTickets()])
})
</script>

<template>
  <div class="page support-page">
    <PageHeader title="پشتیبانی" description="پاسخ سریع سؤال‌ها را پیدا کنید یا مستقیماً با تیم روشا در ارتباط باشید.">
      <template #actions><AppButton icon="plus" @click="openCreate()">درخواست جدید</AppButton></template>
    </PageHeader>

    <AppCard class="support-hero" padding="lg">
      <div class="hero-copy">
        <span class="support-avatar"><AppIcon name="help" :size="30" /></span>
        <div><span class="eyebrow">مرکز راهنمای روشا</span><h2>چطور می‌توانیم کمک کنیم؟</h2><p>ابتدا بین پاسخ‌های کوتاه جست‌وجو کنید؛ اگر کافی نبود، درخواست پشتیبانی بسازید.</p></div>
      </div>
      <div class="service-promise"><span><i />پشتیبانی آنلاین</span><small>پاسخ درخواست‌ها معمولاً در کوتاه‌ترین زمان کاری</small></div>
    </AppCard>

    <AppTabs v-model="section" :items="sectionTabs" class="section-tabs" />

    <section v-if="section === 'faq'" class="faq-section">
      <div class="faq-search-wrap">
        <AppInput v-model="faqSearch" icon="search" inputmode="search" placeholder="مثلاً «زمان برداشت تومان»" label="جست‌وجو در راهنما" />
        <span>{{ faqCountLabel }}</span>
      </div>
      <div class="category-strip" aria-label="دسته‌بندی سؤالات">
        <button type="button" :class="{ active: !faqCategory }" :aria-pressed="!faqCategory" @click="faqCategory = ''"><AppIcon name="help" :size="18" />همه</button>
        <button v-for="item in SUPPORT_CATEGORIES" :key="item.value" type="button" :class="{ active: faqCategory === item.value }" :aria-pressed="faqCategory === item.value" @click="faqCategory = item.value"><AppIcon :name="item.icon" :size="18" />{{ item.label }}</button>
      </div>

      <AppCard padding="none" class="faq-list-card">
        <div v-if="faqsLoading" class="faq-skeletons"><div v-for="i in 4" :key="i"><AppSkeleton width="60%" height="1.1rem" /><AppSkeleton width="1.5rem" height="1.5rem" radius="50%" /></div></div>
        <div v-else-if="faqsError" class="load-error"><AppIcon name="warning" :size="26" /><div><strong>راهنما در دسترس نیست</strong><p>{{ faqsError }}</p></div><AppButton variant="secondary" size="sm" icon="refresh" @click="loadFaqs">تلاش دوباره</AppButton></div>
        <EmptyState v-else-if="!faqs.length" icon="search" title="پاسخی پیدا نشد" description="عبارت کوتاه‌تری جست‌وجو کنید یا درخواست پشتیبانی بسازید."><AppButton @click="openCreate(faqCategory || 'other')">ثبت درخواست</AppButton></EmptyState>
        <div v-else class="faq-list">
          <article v-for="faq in faqs" :key="faq.id" :class="{ open: openFaqId === faq.id }">
            <button type="button" :aria-expanded="openFaqId === faq.id" :aria-controls="`faq-answer-${faq.id}`" @click="openFaqId = openFaqId === faq.id ? '' : faq.id">
              <span class="faq-icon"><AppIcon :name="supportCategoryMeta(faq.category).icon" :size="20" /></span>
              <span><strong>{{ faq.question }}</strong><small>{{ supportCategoryMeta(faq.category).label }}</small></span>
              <AppIcon :name="openFaqId === faq.id ? 'chevronUp' : 'chevronDown'" :size="19" />
            </button>
            <div v-if="openFaqId === faq.id" :id="`faq-answer-${faq.id}`" class="faq-answer"><p>{{ faq.answer }}</p><div><span v-for="tag in faq.tags" :key="tag">{{ tag }}</span></div></div>
          </article>
        </div>
      </AppCard>

      <AppCard class="still-need-help" padding="lg">
        <span><AppIcon name="mail" :size="25" /></span>
        <div><h3>هنوز پاسخ خود را پیدا نکردید؟</h3><p>جزئیات موضوع را برای تیم پشتیبانی بنویسید تا دقیق‌تر بررسی کنیم.</p></div>
        <AppButton variant="secondary" icon="plus" @click="openCreate(faqCategory || undefined)">ساخت درخواست</AppButton>
      </AppCard>
    </section>

    <section v-else class="tickets-section">
      <div class="tickets-toolbar">
        <div><h2>درخواست‌های من</h2><span>{{ toPersianDigits(ticketsTotal) }} درخواست</span></div>
        <div><AppInput v-model="ticketSearch" icon="search" inputmode="search" placeholder="موضوع یا شماره درخواست" /><AppSelect v-model="ticketStatus" :options="ticketStatuses" aria-label="فیلتر درخواست‌ها بر اساس وضعیت" /></div>
      </div>

      <AppCard padding="none" class="tickets-card">
        <div v-if="ticketsLoading" class="ticket-skeletons"><div v-for="i in 3" :key="i"><AppSkeleton width="3rem" height="3rem" radius="1rem" /><span><AppSkeleton width="45%" height="1.05rem" /><AppSkeleton width="70%" height=".8rem" /></span></div></div>
        <div v-else-if="ticketsError" class="load-error"><AppIcon name="warning" :size="26" /><div><strong>درخواست‌ها بارگیری نشدند</strong><p>{{ ticketsError }}</p></div><AppButton variant="secondary" size="sm" icon="refresh" @click="loadTickets">تلاش دوباره</AppButton></div>
        <EmptyState v-else-if="!tickets.length" icon="help" title="درخواستی در این فهرست نیست" description="اگر به کمک نیاز دارید، یک درخواست جدید برای پشتیبانی ثبت کنید."><AppButton icon="plus" @click="openCreate()">درخواست جدید</AppButton></EmptyState>
        <div v-else class="ticket-list">
          <RouterLink v-for="ticket in tickets" :key="ticket.id" :to="`/app/support/tickets/${ticket.id}`" class="ticket-row">
            <span class="ticket-icon"><AppIcon :name="supportCategoryMeta(ticket.category).icon" :size="22" /></span>
            <div class="ticket-copy"><div><h3>{{ ticket.subject }}</h3><StatusBadge domain="ticket" :status="ticket.status" /></div><p><span class="ltr">{{ ticket.ticketNumber }}</span><i />{{ supportCategoryMeta(ticket.category).label }}<i />آخرین به‌روزرسانی {{ formatPersianDateTime(ticket.updatedAt) }}</p></div>
            <div class="message-count"><AppIcon name="mail" :size="17" />{{ toPersianDigits(ticket.messages.length) }} پیام</div>
            <AppIcon name="chevronLeft" :size="20" />
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
          <AppSelect v-model="ticketForm.category" :options="ticketCategoryOptions" label="دسته‌بندی" :error="fieldErrors.category" required />
          <AppInput v-model="ticketForm.orderId" label="شماره سفارش (اختیاری)" placeholder="ORD-..." ltr />
        </div>
        <AppInput v-model="ticketForm.subject" label="موضوع" placeholder="خلاصه‌ای روشن از درخواست" :error="fieldErrors.subject" />
        <label class="textarea-field"><span>توضیحات</span><textarea v-model="ticketForm.body" rows="6" placeholder="چه اتفاقی افتاده و از ما چه کمکی می‌خواهید؟" :class="{ invalid: fieldErrors.body }" :aria-invalid="Boolean(fieldErrors.body)" :aria-describedby="fieldErrors.body ? 'support-ticket-body-error' : undefined" @input="fieldErrors.body = ''" /><small id="support-ticket-body-error" :class="{ error: fieldErrors.body }" :role="fieldErrors.body ? 'alert' : undefined">{{ fieldErrors.body || `${toPersianDigits(ticketForm.body.length)} کاراکتر` }}</small></label>
        <div class="safe-support-note"><AppIcon name="shield" :size="18" />پشتیبانی هرگز رمز عبور یا کد ورود شما را درخواست نمی‌کند.</div>
      </form>
      <template #footer><AppButton block :loading="creating" @click="createTicket">ثبت درخواست</AppButton><AppButton variant="secondary" :disabled="creating" @click="closeCreate">انصراف</AppButton></template>
    </AppModal>
  </div>
</template>

<style scoped>
.support-page { display: grid; align-content: start; gap: var(--space-5); }.support-page :deep(.page-header) { margin-bottom: 0; }
.support-hero { display: flex; align-items: center; justify-content: space-between; gap: var(--space-6); background: linear-gradient(125deg, var(--color-surface-1), var(--color-primary-soft)); }.hero-copy { display: flex; align-items: center; gap: var(--space-4); }.support-avatar { display: grid; width: 4rem; height: 4rem; flex: 0 0 auto; border: 1px solid rgba(67,139,255,.2); border-radius: 1.25rem; background: var(--color-primary-soft); color: var(--color-primary); place-items: center; }.eyebrow { color: var(--color-primary); font-size: var(--font-size-xs); font-weight: 600; }.hero-copy h2 { margin: .1rem 0; font-size: var(--font-size-xl); }.hero-copy p { margin: 0; color: var(--color-text-muted); font-size: var(--font-size-sm); }.service-promise { display: grid; justify-items: end; padding: var(--space-3) var(--space-4); border: 1px solid var(--color-border-soft); border-radius: var(--radius-md); background: var(--color-surface-2); }.service-promise > span { display: flex; align-items: center; gap: var(--space-2); font-weight: 600; }.service-promise i { width: .5rem; height: .5rem; border-radius: 50%; background: var(--color-success); box-shadow: 0 0 0 4px var(--color-success-soft); }.service-promise small { color: var(--color-text-muted); font-size: var(--font-size-xs); }.section-tabs { width: min(100%, 32rem); margin-inline: auto; }
.faq-section,.tickets-section { display: grid; gap: var(--space-4); }.faq-search-wrap { position: relative; width: min(100%, 45rem); margin-inline: auto; }.faq-search-wrap > span { position: absolute; inset-block-end: .9rem; inset-inline-end: var(--space-4); color: var(--color-text-muted); font-size: var(--font-size-xs); pointer-events: none; }.faq-search-wrap :deep(input) { padding-inline-end: 6rem; }.category-strip { display: flex; gap: var(--space-2); overflow-x: auto; padding-bottom: var(--space-1); }.category-strip button { display: inline-flex; align-items: center; gap: var(--space-2); min-height: 2.6rem; flex: 0 0 auto; padding-inline: var(--space-4); border: 1px solid var(--color-border); border-radius: var(--radius-pill); background: var(--color-surface-1); color: var(--color-text-muted); font-size: var(--font-size-sm); }.category-strip button:hover { border-color: var(--color-border-hover); color: var(--color-text-primary); }.category-strip button.active { border-color: rgba(67,139,255,.3); background: var(--color-primary-soft); color: var(--color-primary); }
.faq-list-card,.tickets-card { overflow: hidden; }.faq-skeletons { display: grid; }.faq-skeletons > div { display: flex; align-items: center; justify-content: space-between; gap: var(--space-4); padding: var(--space-5); }.faq-skeletons > div + div { border-top: 1px solid var(--color-border-soft); }.load-error { display: flex; align-items: center; gap: var(--space-4); padding: var(--space-8); color: var(--color-danger); }.load-error > div { flex: 1; color: var(--color-text-primary); }.load-error p { margin: .1rem 0 0; color: var(--color-text-muted); font-size: var(--font-size-sm); }
.faq-list article + article { border-top: 1px solid var(--color-border-soft); }.faq-list article > button { display: grid; grid-template-columns: auto 1fr auto; align-items: center; gap: var(--space-3); width: 100%; padding: var(--space-5); border: 0; background: transparent; text-align: start; }.faq-list article > button:hover { background: var(--color-surface-2); }.faq-icon { display: grid; width: 2.75rem; height: 2.75rem; border-radius: .85rem; background: var(--color-primary-soft); color: var(--color-primary); place-items: center; }.faq-list article > button > span:nth-child(2) { display: grid; }.faq-list strong { font-size: var(--font-size-md); }.faq-list small { color: var(--color-text-muted); font-size: var(--font-size-xs); }.faq-list article > button > svg { color: var(--color-text-muted); }.faq-answer { padding: 0 calc(var(--space-5) + 3.5rem) var(--space-5) var(--space-5); }.faq-answer p { margin: 0; color: var(--color-text-secondary); line-height: 2; }.faq-answer > div { display: flex; flex-wrap: wrap; gap: var(--space-2); margin-top: var(--space-3); }.faq-answer > div span { padding: .15rem .5rem; border-radius: var(--radius-pill); background: var(--color-surface-2); color: var(--color-text-muted); font-size: .68rem; }
.still-need-help { display: flex; align-items: center; gap: var(--space-4); }.still-need-help > span { display: grid; width: 3rem; height: 3rem; border-radius: .9rem; background: var(--color-gold-soft); color: var(--color-gold); place-items: center; }.still-need-help > div { flex: 1; }.still-need-help h3 { margin: 0; font-size: var(--font-size-md); }.still-need-help p { margin: .1rem 0 0; color: var(--color-text-muted); font-size: var(--font-size-sm); }
.tickets-toolbar { display: flex; align-items: end; justify-content: space-between; gap: var(--space-4); }.tickets-toolbar > div:first-child { display: flex; align-items: baseline; gap: var(--space-2); }.tickets-toolbar h2 { margin: 0; font-size: var(--font-size-lg); }.tickets-toolbar > div:first-child span { color: var(--color-text-muted); font-size: var(--font-size-xs); }.tickets-toolbar > div:last-child { display: grid; grid-template-columns: minmax(14rem,1fr) 12rem; gap: var(--space-3); min-width: min(100%,31rem); }
.ticket-skeletons { display: grid; }.ticket-skeletons > div { display: flex; align-items: center; gap: var(--space-4); padding: var(--space-5); }.ticket-skeletons > div + div { border-top: 1px solid var(--color-border-soft); }.ticket-skeletons span { display: grid; flex: 1; gap: var(--space-2); }.ticket-list { display: grid; }.ticket-row { display: grid; grid-template-columns: auto minmax(0,1fr) auto auto; align-items: center; gap: var(--space-4); padding: var(--space-5); transition: background var(--transition-fast); }.ticket-row + .ticket-row { border-top: 1px solid var(--color-border-soft); }.ticket-row:hover { background: var(--color-surface-2); }.ticket-icon { display: grid; width: 3rem; height: 3rem; border-radius: 1rem; background: var(--color-primary-soft); color: var(--color-primary); place-items: center; }.ticket-copy { min-width: 0; }.ticket-copy > div { display: flex; align-items: center; gap: var(--space-3); }.ticket-copy h3 { margin: 0; overflow: hidden; font-size: var(--font-size-md); text-overflow: ellipsis; white-space: nowrap; }.ticket-copy p { display: flex; align-items: center; gap: var(--space-2); margin: .25rem 0 0; color: var(--color-text-muted); font-size: var(--font-size-xs); }.ticket-copy p i { width: .25rem; height: .25rem; border-radius: 50%; background: var(--color-border-hover); }.message-count { display: flex; align-items: center; gap: var(--space-1); color: var(--color-text-muted); font-size: var(--font-size-xs); }.ticket-row > svg { color: var(--color-text-muted); }
.ticket-form { display: grid; gap: var(--space-4); }.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-3); }.form-error { padding: var(--space-3); border-radius: var(--radius-md); background: var(--color-danger-soft); color: var(--color-danger); font-size: var(--font-size-sm); }.textarea-field { display: grid; gap: var(--space-2); }.textarea-field > span { color: var(--color-text-secondary); font-size: var(--font-size-sm); font-weight: 500; }.textarea-field textarea { width: 100%; resize: vertical; min-height: 8rem; padding: var(--space-3) var(--space-4); border: 1px solid var(--color-border); border-radius: var(--radius-md); outline: 0; background: var(--color-surface-2); line-height: 1.9; }.textarea-field textarea:focus { border-color: var(--color-border-focus); background: var(--color-surface-1); box-shadow: var(--shadow-focus); }.textarea-field textarea.invalid { border-color: var(--color-danger); }.textarea-field small { color: var(--color-text-muted); font-size: var(--font-size-xs); }.textarea-field small.error { color: var(--color-danger); }.safe-support-note { display: flex; align-items: center; gap: var(--space-2); padding: var(--space-3); border-radius: var(--radius-md); background: var(--color-info-soft); color: var(--color-text-secondary); font-size: var(--font-size-xs); }.safe-support-note svg { color: var(--color-info); }
.support-hero { position: relative; overflow: hidden; }.support-hero::after { position: absolute; inset-block: 16%; inset-inline-start: 0; width: 2px; border-radius: var(--radius-pill); background: linear-gradient(180deg,transparent,var(--color-gold),transparent); content: ''; opacity: .72; }.support-hero > * { position: relative; z-index: 1; }
.category-strip { overscroll-behavior-inline: contain; scrollbar-width: none; }.category-strip::-webkit-scrollbar { display: none; }.category-strip button { min-height: 2.75rem; }
.category-strip button:focus-visible,.faq-list article > button:focus-visible,.ticket-row:focus-visible { outline: 2px solid var(--color-border-focus); outline-offset: -2px; }
.faq-list article.open { background: linear-gradient(90deg,var(--color-primary-soft),transparent 76%); }
.ticket-row { min-height: 5.5rem; }
.ticket-copy h3 { overflow: visible; text-overflow: clip; white-space: normal; overflow-wrap: anywhere; }
@media (hover: hover) { .ticket-row:hover { background: linear-gradient(90deg,var(--color-primary-soft),var(--color-surface-2)); } }
@media (max-width: 900px) { .support-hero { align-items: flex-start; flex-direction: column; }.service-promise { width: 100%; align-items: start; justify-items: start; }.ticket-row { grid-template-columns: auto minmax(0,1fr) auto; }.message-count { display: none; } }
@media (max-width: 767px) { .support-avatar { width: 3.25rem; height: 3.25rem; }.hero-copy { align-items: flex-start; }.hero-copy h2 { font-size: var(--font-size-lg); }.section-tabs { width: 100%; }.faq-answer { padding: 0 var(--space-4) var(--space-4); }.faq-list article > button { min-height: 4.75rem; padding: var(--space-4); }.faq-icon { width: 2.4rem; height: 2.4rem; }.still-need-help { align-items: flex-start; flex-wrap: wrap; }.still-need-help > div { min-width: calc(100% - 4rem); }.still-need-help :deep(.app-button) { width: 100%; min-height: 2.75rem; }.tickets-toolbar { align-items: stretch; flex-direction: column; }.tickets-toolbar > div:last-child { grid-template-columns: 1fr; min-width: 0; }.ticket-row { gap: var(--space-3); padding: var(--space-4); }.ticket-copy > div { align-items: flex-start; flex-direction: column; gap: var(--space-1); }.ticket-copy p { flex-wrap: wrap; }.ticket-copy p span ~ * { display: none; }.form-grid { grid-template-columns: 1fr; }.load-error { align-items: flex-start; flex-wrap: wrap; padding: var(--space-5); }.load-error > div { min-width: calc(100% - 4rem); }.load-error :deep(.app-button) { min-height: 2.75rem; } }
@media (max-width: 399px) {
  .hero-copy { gap: var(--space-3); }
  .support-avatar { width: 3rem; height: 3rem; border-radius: .9rem; }
  .hero-copy p { font-size: var(--font-size-xs); }
  .service-promise { padding: var(--space-3); }
  .faq-search-wrap > span { inset-inline-end: var(--space-3); }
  .category-strip { margin-inline: calc(var(--space-1) * -1); padding-inline: var(--space-1); }
  .faq-list article > button { grid-template-columns: minmax(0, 1fr) auto; gap: var(--space-2); }
  .faq-icon { display: none; }
  .ticket-row { grid-template-columns: 2.5rem minmax(0, 1fr) auto; gap: var(--space-2); padding-inline: var(--space-3); }
  .ticket-icon { width: 2.5rem; height: 2.5rem; border-radius: .8rem; }
  .ticket-copy h3 { font-size: var(--font-size-sm); }
}
</style>
