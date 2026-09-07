<script setup lang="ts">
import { nextTick, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { supportCategoryMeta } from '@/components/support/supportMeta'
import AppButton from '@/components/ui/AppButton.vue'
import AppCard from '@/components/ui/AppCard.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import AppModal from '@/components/ui/AppModal.vue'
import AppSkeleton from '@/components/ui/AppSkeleton.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import StatusBadge from '@/components/ui/StatusBadge.vue'
import { supportService } from '@/services'
import type { SupportTicket } from '@/types'
import { formatPersianDate, formatPersianDateTime, formatTime, toPersianDigits } from '@/utils/formatters'
import { prefersReducedMotion } from '@/utils/motion'

const route = useRoute()
const ticket = ref<SupportTicket | null>(null)
const loading = ref(true)
const error = ref('')
const replyBody = ref('')
const replyError = ref('')
const replying = ref(false)
const closeOpen = ref(false)
const closing = ref(false)
const feedback = ref('')
const threadRef = ref<HTMLElement | null>(null)

function routeTicketId(): string {
  const raw = route.params.id
  return Array.isArray(raw) ? raw[0] ?? '' : String(raw ?? '')
}

function readableError(caught: unknown, fallback: string): string {
  return caught instanceof Error ? caught.message : fallback
}

async function load(): Promise<void> {
  const id = routeTicketId()
  if (!id) {
    error.value = 'شماره درخواست در نشانی صفحه وجود ندارد.'
    loading.value = false
    return
  }
  loading.value = true
  error.value = ''
  try {
    ticket.value = await supportService.getTicket(id)
  } catch (caught) {
    ticket.value = null
    error.value = readableError(caught, 'درخواست پشتیبانی بارگیری نشد.')
  } finally {
    loading.value = false
  }
}

async function sendReply(): Promise<void> {
  if (!ticket.value || replying.value || ticket.value.status === 'closed') return
  const body = replyBody.value.trim()
  if (body.length < 2) {
    replyError.value = 'متن پیام را وارد کنید.'
    return
  }
  replying.value = true
  replyError.value = ''
  try {
    const message = await supportService.reply(ticket.value.id, body)
    ticket.value.messages.push(message)
    ticket.value.updatedAt = message.createdAt
    ticket.value.status = 'open'
    replyBody.value = ''
    feedback.value = 'پاسخ شما ارسال شد.'
    await nextTick()
    threadRef.value?.lastElementChild?.scrollIntoView({
      behavior: prefersReducedMotion() ? 'auto' : 'smooth',
      block: 'nearest',
    })
  } catch (caught) {
    replyError.value = readableError(caught, 'ارسال پاسخ انجام نشد.')
  } finally {
    replying.value = false
  }
}

function onComposerKeydown(event: KeyboardEvent): void {
  if (event.key === 'Enter' && (event.ctrlKey || event.metaKey)) {
    event.preventDefault()
    void sendReply()
  }
}

async function closeTicket(): Promise<void> {
  if (!ticket.value) return
  closing.value = true
  try {
    ticket.value = await supportService.close(ticket.value.id)
    closeOpen.value = false
    feedback.value = 'درخواست پشتیبانی بسته شد.'
  } catch (caught) {
    error.value = readableError(caught, 'بستن درخواست انجام نشد.')
    closeOpen.value = false
  } finally {
    closing.value = false
  }
}

watch(() => route.params.id, load, { immediate: true })
</script>

<template>
  <div class="page ticket-detail-page">
    <PageHeader title="گفت‌وگو با پشتیبانی" description="پاسخ‌ها و جزئیات درخواست را در همین صفحه دنبال کنید." back-to="/app/support?tab=tickets">
      <template #actions>
        <AppButton v-if="ticket && ticket.status !== 'closed'" variant="secondary" icon="close" @click="closeOpen = true">بستن درخواست</AppButton>
      </template>
    </PageHeader>

    <template v-if="loading">
      <AppCard padding="lg"><div class="header-skeleton"><AppSkeleton height="3.5rem" width="3.5rem" radius="1rem" /><div><AppSkeleton height="1.3rem" width="15rem" /><AppSkeleton height=".85rem" width="10rem" /></div></div></AppCard>
      <div class="detail-layout"><AppCard padding="lg"><div class="message-skeleton" v-for="i in 3" :key="i"><AppSkeleton height="4.5rem" :width="i % 2 ? '72%' : '63%'" radius="1rem" /></div></AppCard><AppCard padding="lg"><AppSkeleton v-for="i in 4" :key="i" height="2.7rem" :style="{ marginBottom: '.75rem' }" /></AppCard></div>
    </template>

    <AppCard v-else-if="error || !ticket" padding="none">
      <EmptyState icon="warning" title="درخواست پیدا نشد" :description="error || 'ممکن است این درخواست حذف شده یا نشانی آن نادرست باشد.'"><AppButton variant="secondary" icon="refresh" @click="load">تلاش دوباره</AppButton><AppButton to="/app/support?tab=tickets" variant="ghost">بازگشت به پشتیبانی</AppButton></EmptyState>
    </AppCard>

    <template v-else>
      <div v-if="feedback" class="feedback" role="status"><AppIcon name="check" :size="18" /><span>{{ feedback }}</span><button type="button" aria-label="بستن" @click="feedback = ''"><AppIcon name="close" :size="16" /></button></div>

      <AppCard class="ticket-heading" padding="lg">
        <span class="category-icon"><AppIcon :name="supportCategoryMeta(ticket.category).icon" :size="25" /></span>
        <div class="ticket-title"><div><span class="ltr ticket-number">{{ ticket.ticketNumber }}</span><span>{{ supportCategoryMeta(ticket.category).label }}</span></div><h2>{{ ticket.subject }}</h2></div>
        <StatusBadge domain="ticket" :status="ticket.status" />
      </AppCard>

      <div class="detail-layout">
        <AppCard class="conversation-card" padding="none">
          <header class="conversation-header">
            <div><span class="online-dot" /><div><strong>پشتیبانی روشا</strong><small>پیام‌های این درخواست محفوظ و قابل پیگیری هستند.</small></div></div>
            <span>{{ toPersianDigits(ticket.messages.length) }} پیام</span>
          </header>

          <div ref="threadRef" class="message-thread" aria-live="polite">
            <article v-for="message in ticket.messages" :key="message.id" class="message" :class="message.sender">
              <span class="sender-avatar"><AppIcon :name="message.sender === 'support' ? 'help' : 'profile'" :size="19" /></span>
              <div class="message-content">
                <div class="message-meta"><strong>{{ message.senderName }}</strong><time :datetime="message.createdAt" :title="formatPersianDateTime(message.createdAt)">{{ formatPersianDate(message.createdAt, { month: 'long' }) }}، {{ formatTime(message.createdAt) }}</time></div>
                <p>{{ message.body }}</p>
                <div v-if="message.attachments?.length" class="attachments"><a v-for="attachment in message.attachments" :key="attachment.url" :href="attachment.url" target="_blank" rel="noopener"><AppIcon name="download" :size="17" />{{ attachment.name }}</a></div>
              </div>
            </article>
          </div>

          <div v-if="ticket.status === 'closed'" class="closed-banner"><span><AppIcon name="lock" :size="20" /></span><div><strong>این درخواست بسته شده است</strong><p>برای موضوع جدید، یک درخواست پشتیبانی تازه ثبت کنید.</p></div><AppButton to="/app/support?new=1" variant="secondary" size="sm" icon="plus">درخواست جدید</AppButton></div>
          <form v-else class="composer" @submit.prevent="sendReply">
            <label for="ticket-reply">پاسخ شما</label>
            <div class="composer-control" :class="{ invalid: replyError }">
              <textarea id="ticket-reply" v-model="replyBody" rows="4" placeholder="پیام خود را بنویسید…" :aria-invalid="Boolean(replyError)" :aria-describedby="replyError ? 'ticket-reply-error' : undefined" @input="replyError = ''" @keydown="onComposerKeydown" />
              <div><span>برای ارسال سریع <kbd>Ctrl</kbd> + <kbd>Enter</kbd></span><span>{{ toPersianDigits(replyBody.length) }} کاراکتر</span></div>
            </div>
            <span v-if="replyError" id="ticket-reply-error" class="reply-error" role="alert">{{ replyError }}</span>
            <div class="composer-footer"><p><AppIcon name="shield" :size="16" />رمز عبور یا کد تأیید را در پیام ننویسید.</p><AppButton type="submit" icon="arrowUp" :loading="replying" :disabled="replyBody.trim().length < 2">ارسال پاسخ</AppButton></div>
          </form>
        </AppCard>

        <aside class="ticket-sidebar">
          <AppCard padding="lg">
            <div class="aside-heading"><span><AppIcon name="info" :size="20" /></span><h2>جزئیات درخواست</h2></div>
            <dl>
              <div><dt>شماره درخواست</dt><dd class="ltr">{{ ticket.ticketNumber }}</dd></div>
              <div><dt>دسته‌بندی</dt><dd>{{ supportCategoryMeta(ticket.category).label }}</dd></div>
              <div><dt>اولویت</dt><dd>{{ ticket.priority === 'high' ? 'بالا' : 'عادی' }}</dd></div>
              <div><dt>تاریخ ثبت</dt><dd>{{ formatPersianDateTime(ticket.createdAt) }}</dd></div>
              <div><dt>آخرین به‌روزرسانی</dt><dd>{{ formatPersianDateTime(ticket.updatedAt) }}</dd></div>
            </dl>
          </AppCard>
          <AppCard v-if="ticket.orderId" padding="lg" class="related-order">
            <span><AppIcon name="orders" :size="21" /></span><div><small>سفارش مرتبط</small><strong class="ltr">{{ ticket.orderId }}</strong></div><RouterLink :to="`/app/orders/${ticket.orderId}`" aria-label="مشاهده سفارش"><AppIcon name="chevronLeft" :size="19" /></RouterLink>
          </AppCard>
          <AppCard padding="lg" class="help-note"><AppIcon name="clock" :size="21" /><div><strong>در انتظار پاسخ هستید؟</strong><p>با ارسال پیام تازه، درخواست شما در صف بررسی به‌روزرسانی می‌شود.</p></div></AppCard>
        </aside>
      </div>
    </template>

    <AppModal v-model="closeOpen" title="بستن درخواست پشتیبانی؟" description="پس از بستن، امکان ارسال پیام تازه در این گفت‌وگو وجود ندارد." size="sm">
      <p class="close-copy">اگر پاسخ خود را دریافت کرده‌اید، درخواست را ببندید. برای موضوع تازه همیشه می‌توانید درخواست جدید بسازید.</p>
      <template #footer><AppButton variant="danger" block :loading="closing" @click="closeTicket">بله، بسته شود</AppButton><AppButton variant="secondary" :disabled="closing" @click="closeOpen = false">انصراف</AppButton></template>
    </AppModal>
  </div>
</template>

<style scoped>
.ticket-title h2 { margin: .2rem 0 0; overflow: hidden; font-size: var(--font-size-xl); text-overflow: ellipsis; white-space: nowrap; }
@media (max-width: 767px) { .ticket-title h2 { font-size: var(--font-size-lg); } }
.ticket-detail-page { display: grid; align-content: start; gap: var(--space-5); }.ticket-detail-page :deep(.page-header) { margin-bottom: 0; }.header-skeleton { display: flex; align-items: center; gap: var(--space-4); }.header-skeleton > div { display: grid; grid-template-columns: minmax(0, 1fr); min-width: 0; flex: 1; gap: var(--space-2); }.header-skeleton :deep(.skeleton) { max-width: 100%; }.feedback { display: flex; align-items: center; gap: var(--space-2); padding: var(--space-3) var(--space-4); border: 1px solid rgba(53,201,149,.22); border-radius: var(--radius-md); background: var(--color-success-soft); color: var(--color-success); font-size: var(--font-size-sm); }.feedback span { flex: 1; }.feedback button { border: 0; background: transparent; color: inherit; }
.ticket-heading { display: flex; align-items: center; gap: var(--space-4); background: linear-gradient(120deg,var(--color-surface-1),var(--color-primary-soft)); }.category-icon { display: grid; width: 3.5rem; height: 3.5rem; flex: 0 0 auto; border-radius: 1rem; background: var(--color-primary-soft); color: var(--color-primary); place-items: center; }.ticket-title { min-width: 0; flex: 1; }.ticket-title > div { display: flex; align-items: center; gap: var(--space-2); color: var(--color-text-muted); font-size: var(--font-size-xs); }.ticket-number { color: var(--color-primary); font-weight: 600; }.ticket-title h1 { margin: .2rem 0 0; overflow: hidden; font-size: var(--font-size-xl); text-overflow: ellipsis; white-space: nowrap; }
.detail-layout { display: grid; grid-template-columns: minmax(0,1fr) minmax(17rem,23rem); align-items: start; gap: var(--space-5); }.conversation-card { overflow: clip; }.conversation-header { display: flex; align-items: center; justify-content: space-between; gap: var(--space-4); padding: var(--space-4) var(--space-5); border-bottom: 1px solid var(--color-border-soft); background: var(--color-surface-2); }.conversation-header > div { display: flex; align-items: center; gap: var(--space-3); }.conversation-header > div > div { display: grid; }.conversation-header small { color: var(--color-text-muted); font-size: var(--font-size-xs); }.conversation-header > span { color: var(--color-text-muted); font-size: var(--font-size-xs); }.online-dot { width: .6rem; height: .6rem; border-radius: 50%; background: var(--color-success); box-shadow: 0 0 0 5px var(--color-success-soft); }
.message-thread { display: grid; gap: var(--space-6); min-height: 18rem; padding: var(--space-6); background: linear-gradient(rgba(67,139,255,.018), transparent); }.message { display: flex; align-items: flex-start; gap: var(--space-3); max-width: 82%; }.message.user { margin-inline-start: auto; flex-direction: row-reverse; }.sender-avatar { display: grid; width: 2.5rem; height: 2.5rem; flex: 0 0 auto; border-radius: .8rem; background: var(--color-primary-soft); color: var(--color-primary); place-items: center; }.message.user .sender-avatar { background: var(--color-surface-3); color: var(--color-text-secondary); }.message-content { min-width: 0; padding: var(--space-3) var(--space-4); border: 1px solid var(--color-border-soft); border-radius: var(--radius-lg) var(--radius-sm) var(--radius-lg) var(--radius-lg); background: var(--color-surface-2); }.message.user .message-content { border-color: rgba(67,139,255,.18); border-radius: var(--radius-sm) var(--radius-lg) var(--radius-lg) var(--radius-lg); background: var(--color-primary-soft); }.message-meta { display: flex; align-items: center; justify-content: space-between; gap: var(--space-5); }.message-meta strong { font-size: var(--font-size-xs); }.message-meta time { color: var(--color-text-muted); font-size: .68rem; }.message-content p { margin: var(--space-2) 0 0; color: var(--color-text-secondary); line-height: 2; white-space: pre-wrap; }.attachments { display: flex; flex-wrap: wrap; gap: var(--space-2); margin-top: var(--space-3); }.attachments a { display: inline-flex; align-items: center; gap: var(--space-1); padding: .35rem .6rem; border-radius: var(--radius-sm); background: var(--color-surface-3); color: var(--color-primary); font-size: var(--font-size-xs); }
.composer { display: grid; gap: var(--space-2); padding: var(--space-5); border-top: 1px solid var(--color-border-soft); background: var(--color-surface-1); }.composer > label { color: var(--color-text-secondary); font-size: var(--font-size-sm); font-weight: 600; }.composer-control { overflow: hidden; border: 1px solid var(--color-border); border-radius: var(--radius-md); background: var(--color-surface-2); }.composer-control:focus-within { border-color: var(--color-border-focus); box-shadow: var(--shadow-focus); }.composer-control.invalid { border-color: var(--color-danger); }.composer textarea { width: 100%; min-height: 6rem; resize: vertical; padding: var(--space-3) var(--space-4); border: 0; outline: 0; background: transparent; line-height: 1.9; }.composer-control > div { display: flex; align-items: center; justify-content: space-between; gap: var(--space-2); padding: var(--space-2) var(--space-3); border-top: 1px solid var(--color-border-soft); color: var(--color-text-muted); font-size: .67rem; }.composer kbd { padding: .05rem .25rem; border: 1px solid var(--color-border); border-radius: .25rem; background: var(--color-surface-3); font: inherit; }.reply-error { color: var(--color-danger); font-size: var(--font-size-xs); }.composer-footer { display: flex; align-items: center; justify-content: space-between; gap: var(--space-4); }.composer-footer p { display: flex; align-items: center; gap: var(--space-1); margin: 0; color: var(--color-text-muted); font-size: var(--font-size-xs); }.closed-banner { display: flex; align-items: center; gap: var(--space-3); padding: var(--space-5); border-top: 1px solid var(--color-border-soft); background: var(--color-surface-2); }.closed-banner > span { display: grid; width: 2.75rem; height: 2.75rem; border-radius: .8rem; background: var(--color-surface-3); color: var(--color-text-muted); place-items: center; }.closed-banner > div { flex: 1; }.closed-banner p { margin: .1rem 0 0; color: var(--color-text-muted); font-size: var(--font-size-xs); }
.ticket-sidebar { display: grid; gap: var(--space-4); }.aside-heading { display: flex; align-items: center; gap: var(--space-2); margin-bottom: var(--space-4); }.aside-heading > span { display: grid; width: 2.25rem; height: 2.25rem; border-radius: .7rem; background: var(--color-primary-soft); color: var(--color-primary); place-items: center; }.aside-heading h2 { margin: 0; font-size: var(--font-size-md); }.ticket-sidebar dl { display: grid; gap: var(--space-3); margin: 0; }.ticket-sidebar dl > div { display: grid; grid-template-columns: 1fr minmax(0,1.4fr); gap: var(--space-3); padding-bottom: var(--space-3); border-bottom: 1px solid var(--color-border-soft); }.ticket-sidebar dl > div:last-child { padding: 0; border: 0; }.ticket-sidebar dt { color: var(--color-text-muted); font-size: var(--font-size-xs); }.ticket-sidebar dd { margin: 0; color: var(--color-text-secondary); font-size: var(--font-size-xs); text-align: end; overflow-wrap: anywhere; }.related-order { display: flex; align-items: center; gap: var(--space-3); }.related-order > span { display: grid; width: 2.7rem; height: 2.7rem; border-radius: .8rem; background: var(--color-primary-soft); color: var(--color-primary); place-items: center; }.related-order > div { display: grid; flex: 1; }.related-order small { color: var(--color-text-muted); }.related-order a { display: grid; width: 2.25rem; height: 2.25rem; border-radius: .7rem; background: var(--color-surface-2); color: var(--color-primary); place-items: center; }.help-note { display: flex; align-items: flex-start; gap: var(--space-3); color: var(--color-info); }.help-note div { color: var(--color-text-primary); }.help-note p { margin: .15rem 0 0; color: var(--color-text-muted); font-size: var(--font-size-xs); }.close-copy { margin: 0; color: var(--color-text-secondary); line-height: 2; }.message-skeleton { margin-bottom: var(--space-5); }.message-skeleton:nth-child(even) { display: flex; justify-content: end; }
.feedback button { display: inline-grid; min-width: 2.75rem; min-height: 2.75rem; border-radius: var(--radius-sm); place-items: center; }.feedback button:focus-visible { outline: 2px solid currentColor; outline-offset: 2px; }
.ticket-heading { position: relative; overflow: hidden; }.ticket-heading::after { position: absolute; inset-block: 18%; inset-inline-start: 0; width: 2px; border-radius: var(--radius-pill); background: linear-gradient(180deg,transparent,var(--color-gold),transparent); content: ''; opacity: .7; }.ticket-heading > * { position: relative; z-index: 1; }
.message-content p,.attachments a,.ticket-sidebar dd { overflow-wrap: anywhere; }
.ticket-title h1,.ticket-title h2 { overflow: visible; text-overflow: clip; white-space: normal; overflow-wrap: anywhere; }
.related-order > div { min-width: 0; }
.related-order strong { overflow-wrap: anywhere; }
.attachments a { min-height: 2.75rem; padding-inline: var(--space-3); }
.composer textarea { color: var(--color-text-primary); }
.composer textarea::placeholder { color: var(--color-text-muted); }
@media (max-width: 980px) { .detail-layout { grid-template-columns: 1fr; }.ticket-sidebar { grid-template-columns: 1fr 1fr; }.ticket-sidebar > :first-child { grid-row: span 2; } }
@media (max-width: 1199px) { .composer { position: sticky; z-index: calc(var(--z-nav) - 1); bottom: calc(var(--mobile-nav-height) + var(--safe-bottom)); border-top-color: var(--color-border-hover); background: color-mix(in srgb,var(--color-surface-1) 96%,transparent); box-shadow: 0 -12px 30px rgba(0,0,0,.16); backdrop-filter: blur(14px); } }
@media (max-width: 767px) { .ticket-title h1 { font-size: var(--font-size-lg); }.ticket-heading { align-items: flex-start; flex-wrap: wrap; }.ticket-heading > :deep(.status) { margin-inline-start: calc(3.5rem + var(--space-4)); }.message-thread { gap: var(--space-5); padding: var(--space-4); }.message { max-width: 94%; }.sender-avatar { display: none; }.message-content { padding: var(--space-3); }.message-meta { align-items: flex-start; flex-direction: column; gap: 0; }.composer { padding: var(--space-4); }.composer-control > div span:first-child { display: none; }.composer-footer p { display: none; }.composer-footer :deep(.app-button) { width: 100%; min-height: 2.75rem; }.ticket-sidebar { grid-template-columns: 1fr; }.ticket-sidebar > :first-child { grid-row: auto; }.closed-banner { align-items: flex-start; flex-wrap: wrap; }.closed-banner > div { min-width: calc(100% - 4rem); }.closed-banner :deep(.app-button) { width: 100%; min-height: 2.75rem; } }
@media (max-width: 399px) {
  .ticket-heading { display: grid; grid-template-columns: auto minmax(0, 1fr); gap: var(--space-3); }
  .category-icon { width: 3rem; height: 3rem; border-radius: .85rem; }
  .ticket-heading > :deep(.status) { grid-column: 2; justify-self: start; margin-inline-start: 0; }
  .ticket-title h2 { font-size: var(--font-size-md); }
  .conversation-header { align-items: flex-start; padding: var(--space-3); }
  .conversation-header small { display: none; }
  .message-thread { padding: var(--space-3); }
  .message { max-width: 97%; }
  .composer { padding: var(--space-3); }
  .composer textarea { min-height: 5rem; }
  .ticket-sidebar dl > div { grid-template-columns: 1fr; gap: .15rem; }
  .ticket-sidebar dd { text-align: start; }
}
@media (max-width: 767px) and (max-height: 640px) {
  .composer { grid-template-columns: minmax(0, 1fr) auto; align-items: center; gap: var(--space-2); padding: .25rem var(--space-2); }
  .composer > label,.composer-control > div { display: none; }
  .composer-control { min-width: 0; }
  .composer textarea { display: block; height: 2.625rem; min-height: 2.625rem; max-height: 2.625rem; resize: none; padding: .5rem var(--space-3); line-height: 1.5; }
  .composer-footer { display: block; }
  .composer-footer :deep(.app-button) { width: auto; min-width: 6.5rem; min-height: 2.75rem; }
  .reply-error { position: absolute; inset-block-end: calc(100% + var(--space-1)); inset-inline: var(--space-2); padding: var(--space-2) var(--space-3); border: 1px solid color-mix(in srgb,var(--color-danger) 35%,transparent); border-radius: var(--radius-sm); background: var(--color-surface-1); box-shadow: var(--shadow-md); }
}
</style>
