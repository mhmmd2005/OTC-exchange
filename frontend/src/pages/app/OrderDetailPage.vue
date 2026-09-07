<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import type { OtcOrder } from '@/types'
import { orderService } from '@/services/order.service'
import { formatCrypto, formatPersianDateTime, formatToman } from '@/utils/formatters'
import AppButton from '@/components/ui/AppButton.vue'
import AppCard from '@/components/ui/AppCard.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import AppModal from '@/components/ui/AppModal.vue'
import AppSkeleton from '@/components/ui/AppSkeleton.vue'
import CopyButton from '@/components/ui/CopyButton.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import StatusBadge from '@/components/ui/StatusBadge.vue'
import AssetAvatar from '@/components/finance/AssetAvatar.vue'

const route = useRoute(), router = useRouter()
const order = ref<OtcOrder | null>(null)
const loading = ref(true), error = ref(''), cancelOpen = ref(false), cancelling = ref(false)
const refreshError = ref('')
const actionError = ref('')
const cancellationHeading = ref<HTMLElement | null>(null)
let requestSequence = 0
let refreshTimer: number | undefined
const color = computed(() => {
  const colors: Record<string, string> = { USDT:'#26A17B',BTC:'#F7931A',ETH:'#627EEA',TRX:'#EF0027',TON:'#0098EA' }
  return colors[order.value?.assetSymbol || ''] || '#438BFF'
})
const isActive = computed(() => order.value
  ? ['pending_payment', 'payment_confirmed', 'processing'].includes(order.value.status)
  : false)
const load = async (silent = false) => {
  const id = String(route.params.id || '')
  const requestId = ++requestSequence
  if (!silent) {
    loading.value = true
    order.value = null
  }
  error.value = ''
  refreshError.value = ''
  try {
    const response = await orderService.getById(id)
    if (requestId === requestSequence && String(route.params.id || '') === id) order.value = response
  } catch (reason) {
    if (requestId !== requestSequence) return
    const message = reason instanceof Error ? reason.message : 'سفارش پیدا نشد.'
    if (silent && order.value) refreshError.value = message
    else error.value = message
  } finally {
    if (requestId === requestSequence && !silent) loading.value = false
  }
}
const cancelOrder = async () => {
  if (!order.value || cancelling.value) return
  cancelling.value = true
  actionError.value = ''
  try {
    order.value = await orderService.cancel(order.value.id)
    cancelOpen.value = false
    await nextTick()
    cancellationHeading.value?.focus({ preventScroll: true })
  } catch (caught) {
    actionError.value = caught instanceof Error ? caught.message : 'لغو سفارش انجام نشد.'
  } finally {
    cancelling.value = false
  }
}
watch(() => route.params.id, () => { void load() }, { immediate: true })
onMounted(() => {
  refreshTimer = window.setInterval(() => {
    if (document.visibilityState === 'visible' && isActive.value && !cancelling.value) void load(true)
  }, 15_000)
})
onBeforeUnmount(() => {
  requestSequence += 1
  if (refreshTimer !== undefined) window.clearInterval(refreshTimer)
})
</script>

<template>
  <div class="page order-detail-page">
    <PageHeader title="جزئیات سفارش" description="مسیر و اطلاعات کامل این سفارش" back-to="/app/orders">
      <template #actions><AppButton variant="secondary" size="sm" :to="`/app/support?orderId=${order?.id || ''}&new=1`" icon="help">سؤال درباره سفارش</AppButton></template>
    </PageHeader>
    <AppSkeleton v-if="loading" height="28rem" radius="var(--radius-xl)" />
    <EmptyState v-else-if="!order" icon="warning" title="سفارش پیدا نشد" :description="error"><AppButton to="/app/orders">بازگشت به سفارش‌ها</AppButton></EmptyState>
    <template v-else>
      <div v-if="actionError && !cancelOpen" class="action-error" role="alert"><AppIcon name="warning" :size="18" /><span>{{ actionError }}</span><button type="button" aria-label="بستن پیام خطا" @click="actionError = ''"><AppIcon name="close" :size="16" /></button></div>
      <div class="detail-grid">
        <AppCard class="order-summary" padding="lg">
          <header><div class="order-title"><AssetAvatar :symbol="order.assetSymbol" :color="color" size="lg" /><div><span>{{ order.side === 'buy' ? 'خرید' : 'فروش' }} {{ order.assetNameFa }}</span><strong>{{ formatCrypto(order.cryptoAmount, { symbol: order.assetSymbol }) }}</strong></div></div><StatusBadge domain="order" :status="order.status" /></header>
          <div class="order-number"><span><small>شماره سفارش</small><bdi>{{ order.orderNumber }}</bdi></span><CopyButton :value="order.orderNumber" /></div>
          <dl class="detail-list"><div><dt>نرخ معامله</dt><dd>{{ formatToman(order.rateToman) }}</dd></div><div><dt>مبلغ سفارش</dt><dd>{{ formatToman(order.tomanAmount) }}</dd></div><div><dt>کارمزد</dt><dd>{{ formatToman(order.feeToman) }}</dd></div><div class="final"><dt>مبلغ نهایی</dt><dd>{{ formatToman(order.finalTomanAmount) }}</dd></div><div><dt>مبدأ پرداخت</dt><dd>{{ order.paymentSource || 'کیف پول تومان' }}</dd></div><div><dt>مقصد</dt><dd>{{ order.destination || `کیف پول ${order.assetNameFa}` }}</dd></div><div><dt>زمان ثبت</dt><dd>{{ formatPersianDateTime(order.createdAt) }}</dd></div></dl>
          <AppButton v-if="order.status === 'pending_payment'" variant="danger" block @click="cancelOpen = true">لغو سفارش</AppButton>
        </AppCard>
        <AppCard class="timeline-card" padding="lg">
          <h2 v-if="order.status === 'cancelled'" ref="cancellationHeading" tabindex="-1">سفارش لغو شد</h2><h2 v-else>مسیر سفارش</h2><p>{{ isActive ? 'وضعیت سفارش هر ۱۵ ثانیه به‌صورت خودکار به‌روزرسانی می‌شود.' : 'این سفارش به وضعیت نهایی رسیده است.' }}</p>
          <div v-if="refreshError" class="refresh-error" role="alert"><AppIcon name="warning" :size="17" /><span>{{ refreshError }}</span><button type="button" @click="load(true)">تلاش دوباره</button></div>
          <ol class="timeline"><li v-for="event in order.timeline" :key="event.id" :class="{ completed: event.completed, current: event.current }"><span class="timeline-dot"><AppIcon v-if="event.completed" name="check" :size="14" /><i v-else /></span><div><strong>{{ event.title }}</strong><p v-if="event.description">{{ event.description }}</p><small v-if="event.occurredAt">{{ formatPersianDateTime(event.occurredAt) }}</small></div></li></ol>
          <div class="timeline-help"><AppIcon name="info" :size="18" /><span>اگر سفارش بیش از ۱۰ دقیقه در یک مرحله ماند، پشتیبانی آن را بررسی می‌کند.</span></div>
        </AppCard>
      </div>
      <div class="detail-actions-mobile"><AppButton block :to="`/app/support?orderId=${order.id}&new=1`" variant="secondary">سؤال درباره این سفارش</AppButton><AppButton block @click="router.push(`/app/trade?side=${order.side}&asset=${order.assetSymbol}`)">تکرار معامله</AppButton></div>
    </template>
    <AppModal v-model="cancelOpen" title="لغو سفارش" description="این اقدام پس از تأیید قابل بازگشت نیست." size="sm" :dismissible="!cancelling">
      <p class="cancel-copy">مطمئنید می‌خواهید سفارش <bdi>{{ order?.orderNumber }}</bdi> را لغو کنید؟ موجودی مسدودشده آزاد خواهد شد.</p>
      <div v-if="actionError" class="modal-action-error" role="alert"><AppIcon name="warning" :size="18" /><span>{{ actionError }}</span></div>
      <template #footer><AppButton variant="danger" block :loading="cancelling" @click="cancelOrder">بله، لغو شود</AppButton><AppButton variant="secondary" :disabled="cancelling" @click="cancelOpen = false">انصراف</AppButton></template>
    </AppModal>
  </div>
</template>

<style scoped>
.order-detail-page { max-width: 72rem; }.action-error { display: flex; align-items: center; gap: var(--space-2); margin-bottom: var(--space-4); padding: var(--space-3); border: 1px solid rgba(240,108,117,.2); border-radius: var(--radius-md); background: var(--color-danger-soft); color: var(--color-danger); }.action-error span { flex: 1; }.action-error button { display: grid; width: 2rem; height: 2rem; border: 0; border-radius: var(--radius-sm); background: transparent; color: inherit; place-items: center; }.modal-action-error { display: flex; align-items: center; gap: var(--space-2); margin-top: var(--space-4); padding: var(--space-3); border-radius: var(--radius-md); background: var(--color-danger-soft); color: var(--color-danger); font-size: var(--font-size-sm); }.detail-grid { display: grid; grid-template-columns: minmax(0, 1.05fr) minmax(20rem, .75fr); gap: var(--space-5); align-items: start; }.order-summary header { display: flex; align-items: center; justify-content: space-between; gap: var(--space-4); }.order-title { display: flex; align-items: center; gap: var(--space-3); }.order-title > div { display: grid; }.order-title span { color: var(--color-text-muted); font-size: var(--font-size-sm); }.order-title strong { font-size: var(--font-size-xl); }.order-number { display: flex; align-items: center; gap: var(--space-3); margin-block: var(--space-6); padding: var(--space-4); border: 1px dashed var(--color-border-hover); border-radius: var(--radius-md); background: var(--color-surface-2); }.order-number > span { display: grid; flex: 1; }.order-number small { color: var(--color-text-muted); }.order-number bdi { font-weight: 700; direction: ltr; }.detail-list { display: grid; gap: var(--space-3); margin: 0; }.detail-list div { display: flex; justify-content: space-between; gap: var(--space-4); padding-bottom: var(--space-3); border-block-end: 1px solid var(--color-border-soft); }.detail-list dt { color: var(--color-text-muted); }.detail-list dd { margin: 0; font-weight: 500; text-align: end; }.detail-list .final { margin-block: var(--space-1); padding: var(--space-4); border: 0; border-radius: var(--radius-md); background: var(--color-primary-soft); }.detail-list .final dd { color: var(--color-primary); font-size: var(--font-size-lg); font-weight: 700; }.timeline-card h2 { margin: 0; font-size: var(--font-size-lg); }.timeline-card > p { color: var(--color-text-muted); font-size: var(--font-size-xs); }.refresh-error { display: flex; align-items: center; gap: var(--space-2); padding: var(--space-2) var(--space-3); border-radius: var(--radius-sm); background: var(--color-danger-soft); color: var(--color-danger); font-size: var(--font-size-xs); }.refresh-error span { flex: 1; }.refresh-error button { border: 0; background: transparent; color: inherit; font-weight: 700; text-decoration: underline; }.timeline { display: grid; margin: var(--space-6) 0; padding: 0; list-style: none; }.timeline li { position: relative; display: grid; grid-template-columns: 2rem 1fr; gap: var(--space-3); min-height: 5.6rem; }.timeline li:not(:last-child)::before { position: absolute; inset-block-start: 1.65rem; inset-block-end: 0; inset-inline-start: .92rem; width: 2px; background: var(--color-border); content: ''; }.timeline li.completed:not(:last-child)::before { background: var(--color-success); }.timeline-dot { z-index: 1; display: grid; width: 1.9rem; height: 1.9rem; border: 2px solid var(--color-border); border-radius: 50%; background: var(--color-surface-1); color: white; place-items: center; }.timeline-dot i { width: .4rem; height: .4rem; border-radius: 50%; background: var(--color-border-hover); }.completed .timeline-dot { border-color: var(--color-success); background: var(--color-success); }.current .timeline-dot { border-color: var(--color-primary); box-shadow: 0 0 0 5px var(--color-primary-soft); }.current .timeline-dot i { background: var(--color-primary); }.timeline li > div { display: grid; align-content: start; }.timeline p { margin: .15rem 0; color: var(--color-text-muted); font-size: var(--font-size-xs); }.timeline small { color: var(--color-text-muted); font-size: .68rem; }.timeline-help { display: flex; gap: var(--space-2); padding: var(--space-3); border-radius: var(--radius-md); background: var(--color-info-soft); color: var(--color-info); font-size: var(--font-size-xs); }.detail-actions-mobile { display: none; }.cancel-copy { margin: 0; color: var(--color-text-secondary); line-height: 2; }
@media (max-width: 900px) { .detail-grid { grid-template-columns: 1fr; } }
@media (max-width: 767px) { .order-summary header { align-items: flex-start; }.order-title strong { font-size: var(--font-size-lg); }.detail-list { font-size: var(--font-size-sm); }.detail-actions-mobile { display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-2); margin-top: var(--space-4); } }
</style>
