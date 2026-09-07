<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import AppButton from '@/components/ui/AppButton.vue'
import AppCard from '@/components/ui/AppCard.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import AppSkeleton from '@/components/ui/AppSkeleton.vue'
import AppTabs from '@/components/ui/AppTabs.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import { notificationService } from '@/services'
import { useNotificationsStore } from '@/stores/notifications'
import type { NotificationCategory, NotificationItem } from '@/types'
import { formatPersianDateTime, formatRelativeTime, toPersianDigits } from '@/utils/formatters'

const router = useRouter()
const notifications = useNotificationsStore()
const readFilter = ref<'all' | 'unread'>('all')
const category = ref<NotificationCategory | ''>('')
const unreadTotal = ref(0)
const actionLoadingId = ref('')
const feedback = ref('')

const viewTabs = [
  { label: 'همه اعلان‌ها', value: 'all' },
  { label: 'خوانده‌نشده', value: 'unread' },
]

const categories: Array<{ value: NotificationCategory | ''; label: string; icon: string }> = [
  { value: '', label: 'همه', icon: 'bell' },
  { value: 'order', label: 'سفارش', icon: 'orders' },
  { value: 'deposit', label: 'واریز', icon: 'arrowDown' },
  { value: 'withdrawal', label: 'برداشت', icon: 'arrowUp' },
  { value: 'verification', label: 'احراز هویت', icon: 'verify' },
  { value: 'security', label: 'امنیت', icon: 'shield' },
  { value: 'support', label: 'پشتیبانی', icon: 'help' },
  { value: 'system', label: 'سیستم', icon: 'settings' },
]

const visibleTitle = computed(() => {
  const selected = categories.find((item) => item.value === category.value)
  return category.value ? `اعلان‌های ${selected?.label ?? ''}` : 'آخرین اعلان‌ها'
})

function categoryMeta(value: NotificationCategory) {
  return categories.find((item) => item.value === value) ?? categories[0]
}

function readableError(error: unknown): string {
  return error instanceof Error ? error.message : 'اعلان‌ها بارگیری نشدند.'
}

async function load(): Promise<void> {
  feedback.value = ''
  try {
    const [, count] = await Promise.all([
      notifications.fetchNotifications({
        category: category.value || undefined,
        read: readFilter.value === 'unread' ? false : undefined,
      }),
      notificationService.getUnreadCount(),
    ])
    unreadTotal.value = count
  } catch {
    // The store exposes the localized error next to the list.
  }
}

async function markAll(): Promise<void> {
  if (!unreadTotal.value) return
  actionLoadingId.value = 'all'
  try {
    await notifications.markAllAsRead()
    unreadTotal.value = 0
    feedback.value = 'همه اعلان‌ها خوانده شدند.'
    if (readFilter.value === 'unread') await load()
  } catch (error) {
    feedback.value = readableError(error)
  } finally {
    actionLoadingId.value = ''
  }
}

async function markRead(item: NotificationItem): Promise<void> {
  if (item.read) return
  actionLoadingId.value = item.id
  try {
    await notifications.markAsRead(item.id)
    unreadTotal.value = Math.max(0, unreadTotal.value - 1)
    if (readFilter.value === 'unread') await load()
  } catch (error) {
    feedback.value = readableError(error)
  } finally {
    actionLoadingId.value = ''
  }
}

async function openNotification(item: NotificationItem): Promise<void> {
  if (actionLoadingId.value) return
  if (!item.read) {
    try {
      await markRead(item)
    } catch {
      // markRead already exposes a recoverable message; navigation is still useful.
    }
  }
  if (item.action?.to) await router.push(item.action.to)
}

watch([readFilter, category], load)
onMounted(load)
</script>

<template>
  <div class="page notifications-page">
    <PageHeader title="اعلان‌ها" description="رویدادهای مهم حساب و آخرین وضعیت درخواست‌ها را دنبال کنید.">
      <template #actions>
        <AppButton
          variant="secondary"
          icon="check"
          :disabled="!unreadTotal"
          :loading="actionLoadingId === 'all'"
          @click="markAll"
        >خواندن همه</AppButton>
      </template>
    </PageHeader>

    <AppCard class="notification-summary" padding="lg">
      <span class="summary-icon"><AppIcon name="bell" :size="27" /><i v-if="unreadTotal" /></span>
      <div>
        <strong v-if="unreadTotal">{{ toPersianDigits(unreadTotal) }} اعلان خوانده‌نشده دارید</strong>
        <strong v-else>همه‌چیز را دیده‌اید</strong>
        <p>{{ unreadTotal ? 'رویدادهای مهم را از همین صفحه بررسی کنید.' : 'اعلان تازه‌ای برای بررسی باقی نمانده است.' }}</p>
      </div>
      <span class="summary-caption">مرکز رویدادهای حساب</span>
    </AppCard>

    <div v-if="feedback" class="feedback" role="status">
      <AppIcon name="info" :size="18" /><span>{{ feedback }}</span>
      <button type="button" aria-label="بستن" @click="feedback = ''"><AppIcon name="close" :size="16" /></button>
    </div>

    <div class="notification-layout">
      <AppCard class="filters-card" padding="lg">
        <h2>دسته‌بندی‌ها</h2>
        <nav aria-label="فیلتر دسته اعلان‌ها">
          <button
            v-for="item in categories"
            :key="item.value || 'all'"
            type="button"
            :class="{ active: category === item.value }"
            :aria-pressed="category === item.value"
            @click="category = item.value"
          >
            <span><AppIcon :name="item.icon" :size="19" />{{ item.label }}</span>
            <AppIcon v-if="category === item.value" name="check" :size="16" />
          </button>
        </nav>
      </AppCard>

      <section class="notifications-main">
        <div class="list-toolbar">
          <div><h2>{{ visibleTitle }}</h2><span v-if="!notifications.loading">{{ toPersianDigits(notifications.total) }} مورد</span></div>
          <AppTabs v-model="readFilter" :items="viewTabs" />
        </div>

        <AppCard padding="none" class="notification-list-card">
          <div v-if="notifications.loading" class="notification-skeletons">
            <div v-for="index in 5" :key="index" class="notification-skeleton">
              <AppSkeleton width="3rem" height="3rem" radius="1rem" />
              <div><AppSkeleton width="45%" height="1rem" /><AppSkeleton width="85%" height=".8rem" /><AppSkeleton width="25%" height=".7rem" /></div>
            </div>
          </div>

          <div v-else-if="notifications.error" class="error-state" role="alert">
            <span><AppIcon name="warning" :size="25" /></span>
            <div><strong>بارگیری اعلان‌ها انجام نشد</strong><p>{{ notifications.error }}</p></div>
            <AppButton variant="secondary" size="sm" icon="refresh" @click="load">تلاش دوباره</AppButton>
          </div>

          <EmptyState
            v-else-if="!notifications.items.length"
            icon="bell"
            :title="readFilter === 'unread' ? 'اعلان خوانده‌نشده‌ای ندارید' : 'اعلانی در این دسته نیست'"
            :description="readFilter === 'unread' ? 'تمام رویدادهای مهم حساب را بررسی کرده‌اید.' : 'با رخ‌دادن رویداد جدید، اعلان آن اینجا نمایش داده می‌شود.'"
          >
            <AppButton v-if="readFilter === 'unread'" variant="secondary" @click="readFilter = 'all'">نمایش همه اعلان‌ها</AppButton>
          </EmptyState>

          <div v-else class="notification-list">
            <article
              v-for="item in notifications.items"
              :key="item.id"
              class="notification-item"
              :class="{ unread: !item.read }"
            >
              <span class="category-icon" :class="`category-${item.category}`">
                <AppIcon :name="categoryMeta(item.category).icon" :size="22" />
                <i v-if="!item.read" aria-label="خوانده‌نشده" />
              </span>
              <div class="notification-copy">
                <div class="item-heading"><h3>{{ item.title }}</h3><time :datetime="item.createdAt" :title="formatPersianDateTime(item.createdAt)">{{ formatRelativeTime(item.createdAt) }}</time></div>
                <p>{{ item.message }}</p>
                <div class="item-footer">
                  <span class="category-label">{{ categoryMeta(item.category).label }}</span>
                  <button
                    v-if="!item.read"
                    type="button"
                    :disabled="actionLoadingId === item.id"
                    :aria-busy="actionLoadingId === item.id || undefined"
                    @click.stop="markRead(item)"
                    @keydown.stop
                  ><span v-if="actionLoadingId === item.id" class="mini-spinner" />خواندم</button>
                  <RouterLink
                    v-if="item.action"
                    :to="item.action.to"
                    class="action-link"
                    @click.prevent="openNotification(item)"
                  >{{ item.action.label }}<AppIcon name="chevronLeft" :size="16" /></RouterLink>
                </div>
              </div>
            </article>
          </div>
        </AppCard>
      </section>
    </div>
  </div>
</template>

<style scoped>
.notifications-page { display: grid; align-content: start; gap: var(--space-5); }.notifications-page :deep(.page-header) { margin-bottom: 0; }
.notification-summary { display: flex; align-items: center; gap: var(--space-4); background: linear-gradient(115deg, var(--color-surface-1), var(--color-primary-soft)); }.summary-icon { position: relative; display: grid; width: 3.5rem; height: 3.5rem; flex: 0 0 auto; border-radius: 1rem; background: var(--color-primary-soft); color: var(--color-primary); place-items: center; }.summary-icon i { position: absolute; inset-block-start: .35rem; inset-inline-start: .35rem; width: .55rem; height: .55rem; border: 2px solid var(--color-surface-1); border-radius: 50%; background: var(--color-danger); }.notification-summary strong { font-size: var(--font-size-lg); }.notification-summary p { margin: .1rem 0 0; color: var(--color-text-muted); font-size: var(--font-size-sm); }.summary-caption { margin-inline-start: auto; padding: .4rem .7rem; border-radius: var(--radius-pill); background: var(--color-surface-2); color: var(--color-text-muted); font-size: var(--font-size-xs); }
.feedback { display: flex; align-items: center; gap: var(--space-2); padding: var(--space-3) var(--space-4); border: 1px solid rgba(99,179,237,.2); border-radius: var(--radius-md); background: var(--color-info-soft); color: var(--color-info); font-size: var(--font-size-sm); }.feedback > span { flex: 1; }.feedback button { border: 0; background: transparent; color: inherit; }
.notification-layout { display: grid; grid-template-columns: 15.5rem minmax(0,1fr); align-items: start; gap: var(--space-5); }.filters-card { position: sticky; top: calc(var(--header-height) + var(--space-5)); }.filters-card h2 { margin: 0 0 var(--space-3); font-size: var(--font-size-md); }.filters-card nav { display: grid; gap: var(--space-1); }.filters-card button { display: flex; align-items: center; justify-content: space-between; gap: var(--space-2); min-height: 2.75rem; padding-inline: var(--space-3); border: 0; border-radius: var(--radius-md); background: transparent; color: var(--color-text-muted); font-size: var(--font-size-sm); text-align: start; }.filters-card button > span { display: flex; align-items: center; gap: var(--space-2); }.filters-card button:hover { background: var(--color-surface-2); color: var(--color-text-primary); }.filters-card button.active { background: var(--color-primary-soft); color: var(--color-primary); font-weight: 600; }
.notifications-main { min-width: 0; }.list-toolbar { display: flex; align-items: center; justify-content: space-between; gap: var(--space-4); margin-bottom: var(--space-4); }.list-toolbar > div { display: flex; align-items: baseline; gap: var(--space-2); }.list-toolbar h2 { margin: 0; font-size: var(--font-size-lg); }.list-toolbar > div span { color: var(--color-text-muted); font-size: var(--font-size-xs); }.list-toolbar :deep(.tabs) { min-width: 19rem; }
.notification-list-card { overflow: hidden; }.notification-skeletons { display: grid; }.notification-skeleton { display: grid; grid-template-columns: auto 1fr; gap: var(--space-4); padding: var(--space-5); }.notification-skeleton + .notification-skeleton { border-top: 1px solid var(--color-border-soft); }.notification-skeleton > div { display: grid; gap: var(--space-2); }
.error-state { display: flex; align-items: center; gap: var(--space-4); padding: var(--space-8); }.error-state > span { display: grid; width: 3rem; height: 3rem; border-radius: 1rem; background: var(--color-danger-soft); color: var(--color-danger); place-items: center; }.error-state > div { flex: 1; }.error-state p { margin: .15rem 0 0; color: var(--color-text-muted); font-size: var(--font-size-sm); }
.notification-list { display: grid; }.notification-item { position: relative; display: grid; grid-template-columns: auto minmax(0,1fr); gap: var(--space-4); padding: var(--space-5); transition: background var(--transition-fast); }.notification-item + .notification-item { border-top: 1px solid var(--color-border-soft); }.notification-item.unread { background: linear-gradient(90deg, var(--color-primary-soft), transparent 62%); }.category-icon { position: relative; display: grid; width: 3rem; height: 3rem; border-radius: 1rem; background: var(--color-surface-3); color: var(--color-text-secondary); place-items: center; }.category-icon i { position: absolute; inset-block-start: -.1rem; inset-inline-start: -.1rem; width: .65rem; height: .65rem; border: 2px solid var(--color-surface-1); border-radius: 50%; background: var(--color-primary); }.category-order { background: var(--color-primary-soft); color: var(--color-primary); }.category-deposit { background: var(--color-success-soft); color: var(--color-success); }.category-withdrawal { background: var(--color-warning-soft); color: var(--color-warning); }.category-verification { background: var(--color-info-soft); color: var(--color-info); }.category-security { background: var(--color-danger-soft); color: var(--color-danger); }.category-support { background: var(--color-gold-soft); color: var(--color-gold); }
.notification-copy { min-width: 0; }.item-heading { display: flex; align-items: start; justify-content: space-between; gap: var(--space-4); }.item-heading h3 { margin: 0; font-size: var(--font-size-md); }.unread .item-heading h3 { font-weight: 700; }.item-heading time { flex: 0 0 auto; color: var(--color-text-muted); font-size: var(--font-size-xs); }.notification-copy > p { margin: var(--space-1) 0 var(--space-3); color: var(--color-text-secondary); font-size: var(--font-size-sm); line-height: 1.9; }.item-footer { display: flex; align-items: center; gap: var(--space-3); }.category-label { padding: .15rem .5rem; border-radius: var(--radius-pill); background: var(--color-surface-2); color: var(--color-text-muted); font-size: .68rem; }.item-footer button { display: inline-flex; align-items: center; gap: var(--space-1); border: 0; background: transparent; color: var(--color-primary); font-size: var(--font-size-xs); }.action-link { display: inline-flex; align-items: center; gap: .15rem; min-height: 2rem; margin-inline-start: auto; border-radius: var(--radius-sm); color: var(--color-primary); font-size: var(--font-size-xs); font-weight: 600; }.action-link:hover { color: var(--color-primary-hover); }.action-link:focus-visible { outline-offset: 2px; }.mini-spinner { width: .8rem; height: .8rem; border: 1px solid currentColor; border-inline-end-color: transparent; border-radius: 50%; animation: spin .7s linear infinite; } @keyframes spin { to { transform: rotate(360deg); } }
.feedback button { display: inline-grid; min-width: 2.75rem; min-height: 2.75rem; border-radius: var(--radius-sm); place-items: center; }.feedback button:focus-visible { outline: 2px solid currentColor; outline-offset: 2px; }
.notification-summary { position: relative; overflow: hidden; }.notification-summary::after { position: absolute; inset-block: 18%; inset-inline-start: 0; width: 2px; border-radius: var(--radius-pill); background: linear-gradient(180deg,transparent,var(--color-gold),transparent); content: ''; opacity: .68; }.notification-summary > * { position: relative; z-index: 1; }
.filters-card button:focus-visible,.item-footer button:focus-visible { outline: 2px solid var(--color-border-focus); outline-offset: 2px; }
.notification-item.unread::before { position: absolute; inset-block: var(--space-4); inset-inline-start: 0; width: 2px; border-radius: var(--radius-pill); background: var(--color-primary); content: ''; }
.item-footer button,.action-link { min-height: 2.75rem; padding-inline: var(--space-2); border-radius: var(--radius-sm); }
.notification-item { transition: background var(--transition-fast), transform var(--transition-fast); }
@media (hover: hover) { .notification-item:hover { background-color: color-mix(in srgb, var(--color-surface-2) 72%, transparent); } }
@media (max-width: 900px) { .notification-layout { grid-template-columns: 1fr; }.filters-card { position: static; padding: var(--space-3) !important; overflow-x: auto; overscroll-behavior-inline: contain; scrollbar-width: none; }.filters-card::-webkit-scrollbar { display: none; }.filters-card h2 { display: none; }.filters-card nav { display: flex; width: max-content; }.filters-card button { border: 1px solid var(--color-border-soft); }.filters-card button > svg { display: none; } }
@media (max-width: 767px) { .notification-summary { align-items: flex-start; }.summary-caption { display: none; }.list-toolbar { align-items: stretch; flex-direction: column; }.list-toolbar :deep(.tabs) { min-width: 0; }.notification-item { gap: var(--space-3); padding: var(--space-4); }.category-icon { width: 2.7rem; height: 2.7rem; }.item-heading { display: grid; gap: .1rem; }.notification-copy > p { display: -webkit-box; overflow: hidden; -webkit-box-orient: vertical; -webkit-line-clamp: 3; }.item-footer { flex-wrap: wrap; gap: var(--space-1) var(--space-2); }.action-link { max-width: 100%; overflow: visible; text-overflow: clip; white-space: normal; overflow-wrap: anywhere; }.error-state { align-items: flex-start; flex-wrap: wrap; padding: var(--space-5); }.error-state > div { min-width: calc(100% - 4rem); } }
@media (max-width: 399px) {
  .notification-summary { gap: var(--space-3); }
  .summary-icon { width: 3rem; height: 3rem; border-radius: .85rem; }
  .notification-summary strong { font-size: var(--font-size-md); }
  .notification-item { grid-template-columns: 2.5rem minmax(0, 1fr); gap: var(--space-2); padding-inline: var(--space-3); }
  .category-icon { width: 2.5rem; height: 2.5rem; border-radius: .8rem; }
  .item-heading h3 { font-size: var(--font-size-sm); }
  .item-footer { grid-column: 1 / -1; }
  .action-link { max-width: 100%; margin-inline-start: 0; }
}
</style>
