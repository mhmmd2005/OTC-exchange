<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import AppButton from '@/components/ui/AppButton.vue'
import AppCard from '@/components/ui/AppCard.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import AppModal from '@/components/ui/AppModal.vue'
import AppSkeleton from '@/components/ui/AppSkeleton.vue'
import AppSwitch from '@/components/ui/AppSwitch.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import { usePreferencesStore } from '@/stores/preferences'
import type { ThemePreference, UserPreferences } from '@/types'
import { formatToman, toPersianDigits } from '@/utils/formatters'

const preferencesStore = usePreferencesStore()
const ready = ref(false)
const pageError = ref('')
const feedback = ref('')
const saving = ref(false)
const resetOpen = ref(false)
const initialSnapshot = ref('')

type SettingsDraft = Omit<UserPreferences, 'theme'>

const draft = reactive<SettingsDraft>({
  hideBalances: false,
  hideZeroBalances: false,
  usePersianDigits: true,
  reduceMotion: false,
  favoriteAssets: [],
  notificationChannels: { inApp: true, sms: true, email: false },
})

const themes: Array<{ value: ThemePreference; label: string; description: string; icon: string }> = [
  { value: 'system', label: 'سیستم', description: 'هماهنگ با تنظیم روشنایی دستگاه', icon: 'settings' },
  { value: 'light', label: 'روشن', description: 'کنتراست روشن برای محیط روز', icon: 'sparkle' },
  { value: 'dark', label: 'تیره', description: 'خوانایی آرام‌تر در محیط کم‌نور', icon: 'eye-off' },
]

const defaults: UserPreferences = {
  theme: 'dark',
  hideBalances: false,
  hideZeroBalances: false,
  usePersianDigits: true,
  reduceMotion: false,
  favoriteAssets: ['USDT', 'BTC'],
  notificationChannels: { inApp: true, sms: true, email: false },
}

const currentSnapshot = computed(() => JSON.stringify({
  hideBalances: draft.hideBalances,
  hideZeroBalances: draft.hideZeroBalances,
  usePersianDigits: draft.usePersianDigits,
  reduceMotion: draft.reduceMotion,
  favoriteAssets: draft.favoriteAssets,
  notificationChannels: draft.notificationChannels,
}))
const dirty = computed(() => ready.value && currentSnapshot.value !== initialSnapshot.value)
const selectedTheme = computed(() => preferencesStore.theme)
const activeNotificationCount = computed(() => Object.values(draft.notificationChannels).filter(Boolean).length)
const balancePreview = computed(() => draft.hideBalances ? '•••••••• تومان' : formatToman('128450000'))

function assignDraft(value: UserPreferences): void {
  draft.hideBalances = value.hideBalances
  draft.hideZeroBalances = value.hideZeroBalances
  draft.usePersianDigits = value.usePersianDigits
  draft.reduceMotion = value.reduceMotion
  draft.favoriteAssets = [...value.favoriteAssets]
  Object.assign(draft.notificationChannels, value.notificationChannels)
}

function snapshotDraft(): UserPreferences {
  return {
    theme: selectedTheme.value,
    hideBalances: draft.hideBalances,
    hideZeroBalances: draft.hideZeroBalances,
    usePersianDigits: draft.usePersianDigits,
    reduceMotion: draft.reduceMotion,
    favoriteAssets: [...draft.favoriteAssets],
    notificationChannels: { ...draft.notificationChannels },
  }
}

function previewDraft(): void {
  preferencesStore.preview(snapshotDraft())
}

function setTheme(theme: ThemePreference): void {
  if (selectedTheme.value === theme && !preferencesStore.themeSyncError) return
  feedback.value = ''
  void preferencesStore.saveTheme(theme).catch(() => undefined)
}

function setBoolean(key: 'hideBalances' | 'hideZeroBalances' | 'usePersianDigits' | 'reduceMotion', value: boolean): void {
  draft[key] = value
  if (key === 'usePersianDigits' || key === 'reduceMotion') previewDraft()
}

function setNotification(key: keyof UserPreferences['notificationChannels'], value: boolean): void {
  draft.notificationChannels[key] = value
}

async function hydrate(): Promise<void> {
  ready.value = false
  pageError.value = ''
  try {
    await preferencesStore.hydrate()
    assignDraft(preferencesStore.preferences)
    preferencesStore.apply()
    initialSnapshot.value = currentSnapshot.value
  } catch (caught) {
    pageError.value = caught instanceof Error ? caught.message : 'تنظیمات بارگیری نشد.'
  } finally {
    ready.value = true
  }
}

async function savePreferences(force = false): Promise<void> {
  if ((!dirty.value && !force) || saving.value) return
  saving.value = true
  pageError.value = ''
  feedback.value = ''
  try {
    await preferencesStore.saveRemote(snapshotDraft())
    assignDraft(preferencesStore.preferences)
    initialSnapshot.value = currentSnapshot.value
    feedback.value = 'تنظیمات با موفقیت ذخیره شد.'
  } catch (caught) {
    preferencesStore.apply()
    pageError.value = caught instanceof Error ? caught.message : 'ذخیره تنظیمات انجام نشد.'
  } finally {
    saving.value = false
  }
}

async function save(): Promise<void> {
  await savePreferences()
}

function discardChanges(): void {
  assignDraft(preferencesStore.preferences)
  preferencesStore.apply()
  initialSnapshot.value = currentSnapshot.value
  feedback.value = 'تغییرات ذخیره‌نشده کنار گذاشته شد.'
}

async function resetSettings(): Promise<void> {
  preferencesStore.setTheme(defaults.theme)
  assignDraft(defaults)
  previewDraft()
  resetOpen.value = false
  await savePreferences(true)
}

onMounted(hydrate)
onBeforeUnmount(() => preferencesStore.apply())
</script>

<template>
  <div class="page settings-page">
    <PageHeader title="تنظیمات" description="ظاهر، حریم موجودی و روش دریافت اطلاع‌رسانی‌ها را شخصی‌سازی کنید.">
      <template #actions><AppButton icon="check" :disabled="!dirty" :loading="saving" @click="save">ذخیره تغییرات</AppButton></template>
    </PageHeader>

    <div v-if="feedback" class="notice success" role="status"><AppIcon name="check" :size="19" /><span>{{ feedback }}</span><button type="button" aria-label="بستن" @click="feedback = ''"><AppIcon name="close" :size="16" /></button></div>
    <div v-if="pageError || preferencesStore.error" class="notice danger" role="alert"><AppIcon name="warning" :size="19" /><span>{{ pageError || preferencesStore.error }}</span><button type="button" @click="hydrate">تلاش دوباره</button></div>

    <template v-if="!ready">
      <AppCard padding="lg"><AppSkeleton height="1.4rem" width="10rem" /><div class="theme-skeletons"><AppSkeleton v-for="i in 3" :key="i" height="8rem" /></div></AppCard>
      <div class="settings-layout"><AppCard v-for="i in 2" :key="i" padding="lg"><AppSkeleton v-for="j in 4" :key="j" height="4rem" :style="{ marginBottom: '1rem' }" /></AppCard></div>
    </template>

    <template v-else>
      <AppCard padding="lg" class="appearance-card">
        <div class="section-heading"><span><AppIcon name="sparkle" :size="21" /></span><div><h2>ظاهر برنامه</h2><p>انتخاب شما همان لحظه اعمال و برای ورودهای بعدی ذخیره می‌شود.</p></div><span class="live-label"><i />ذخیره خودکار</span></div>
        <div class="theme-grid" role="radiogroup" aria-label="پوسته برنامه">
          <label v-for="theme in themes" :key="theme.value" :class="{ active: selectedTheme === theme.value }">
            <input type="radio" name="theme" :value="theme.value" :checked="selectedTheme === theme.value" @change="setTheme(theme.value)" />
            <span class="theme-preview" :class="`preview-${theme.value}`"><i /><i /><i /><b /></span>
            <span class="theme-copy"><span class="theme-icon"><AppIcon :name="theme.icon" :size="18" /></span><span><strong>{{ theme.label }}</strong><small>{{ theme.description }}</small></span><AppIcon v-if="selectedTheme === theme.value" name="check" :size="17" /></span>
          </label>
        </div>
        <div class="theme-persistence" :class="{ danger: preferencesStore.themeSyncError }" :role="preferencesStore.themeSyncError ? 'alert' : 'status'" aria-live="polite">
          <AppIcon :name="preferencesStore.themeSyncing ? 'refresh' : preferencesStore.themeSyncError ? 'warning' : 'check'" :size="17" />
          <span v-if="preferencesStore.themeSyncing">در حال همگام‌سازی انتخاب با حساب شما…</span>
          <span v-else-if="preferencesStore.themeSyncError">پوسته روی این دستگاه ذخیره شد؛ همگام‌سازی حساب انجام نشد.</span>
          <span v-else>پوسته انتخابی روی این دستگاه ذخیره شده است.</span>
          <button v-if="preferencesStore.themeSyncError" type="button" @click="setTheme(selectedTheme)">تلاش دوباره</button>
        </div>
      </AppCard>

      <div class="settings-layout">
        <AppCard padding="lg" class="preference-card">
          <div class="section-heading"><span><AppIcon name="eye" :size="21" /></span><div><h2>نمایش دارایی</h2><p>موجودی‌ها را در فضاهای عمومی خصوصی نگه دارید.</p></div></div>
          <div class="balance-preview"><span><small>نمونه موجودی کل</small><strong :class="{ masked: draft.hideBalances }">{{ balancePreview }}</strong></span><span class="preview-eye"><AppIcon :name="draft.hideBalances ? 'eye-off' : 'eye'" :size="21" /></span></div>
          <div class="switch-list">
            <AppSwitch :model-value="draft.hideBalances" label="پنهان‌کردن موجودی‌ها" description="مبالغ حساس در داشبورد و کیف پول پوشانده شوند." @update:model-value="setBoolean('hideBalances', $event)" />
            <AppSwitch :model-value="draft.hideZeroBalances" label="پنهان‌کردن دارایی‌های صفر" description="دارایی بدون موجودی در فهرست کیف پول نمایش داده نشود." @update:model-value="setBoolean('hideZeroBalances', $event)" />
          </div>
          <div class="privacy-tip"><AppIcon name="shield" :size="18" /><span>برای پنهان‌کردن سریع موجودی، از آیکن چشم کنار جمع دارایی‌ها نیز می‌توانید استفاده کنید.</span></div>
        </AppCard>

        <AppCard padding="lg" class="preference-card">
          <div class="section-heading"><span><AppIcon name="settings" :size="21" /></span><div><h2>نمایش و دسترس‌پذیری</h2><p>اعداد و حرکت‌های رابط را مطابق نیاز خود تنظیم کنید.</p></div></div>
          <div class="switch-list no-preview">
            <AppSwitch :model-value="draft.usePersianDigits" label="نمایش ارقام فارسی" description="اعداد عمومی رابط با رقم‌های فارسی نمایش داده شوند." @update:model-value="setBoolean('usePersianDigits', $event)" />
            <AppSwitch :model-value="draft.reduceMotion" label="کاهش حرکت رابط" description="انیمیشن‌ها و جابه‌جایی‌های غیرضروری کمتر شوند." @update:model-value="setBoolean('reduceMotion', $event)" />
          </div>
          <div class="digit-preview"><span><small>نمونه رابط</small><strong>{{ draft.usePersianDigits ? '۱۲,۵۰۰,۰۰۰ تومان' : '12,500,000 تومان' }}</strong></span><i /><span><small>نمونه فنی</small><strong class="ltr">12,500,000 IRT</strong></span></div>
        </AppCard>
      </div>

      <AppCard padding="lg" class="notifications-settings">
        <div class="section-heading"><span><AppIcon name="bell" :size="21" /></span><div><h2>کانال‌های اطلاع‌رسانی</h2><p>انتخاب کنید رویدادهای مهم حساب از چه راهی به شما برسند.</p></div><span class="channel-count">{{ toPersianDigits(activeNotificationCount) }} کانال فعال</span></div>
        <div class="channel-grid">
          <div class="channel-item"><span class="channel-icon"><AppIcon name="bell" :size="23" /></span><div><strong>اعلان داخل برنامه</strong><small>وضعیت سفارش، تراکنش و درخواست پشتیبانی</small><em>پیشنهادشده</em></div><AppSwitch :model-value="draft.notificationChannels.inApp" label="فعال‌سازی اعلان داخل برنامه" @update:model-value="setNotification('inApp', $event)" /></div>
          <div class="channel-item"><span class="channel-icon"><AppIcon name="phone" :size="23" /></span><div><strong>پیامک</strong><small>رویدادهای حساس امنیتی و مالی</small></div><AppSwitch :model-value="draft.notificationChannels.sms" label="فعال‌سازی پیامک" @update:model-value="setNotification('sms', $event)" /></div>
          <div class="channel-item"><span class="channel-icon"><AppIcon name="mail" :size="23" /></span><div><strong>ایمیل</strong><small>خلاصه رویدادها و هشدارهای امنیتی</small></div><AppSwitch :model-value="draft.notificationChannels.email" label="فعال‌سازی ایمیل" @update:model-value="setNotification('email', $event)" /></div>
        </div>
        <div v-if="activeNotificationCount === 0" class="channel-warning"><AppIcon name="warning" :size="18" />همه کانال‌ها خاموش هستند؛ ممکن است رویدادهای مهم حساب را دیرتر ببینید.</div>
      </AppCard>

      <AppCard padding="lg" class="settings-footer-card">
        <div><span><AppIcon name="refresh" :size="21" /></span><div><h3>بازگردانی تنظیمات</h3><p>پوسته و ترجیحات نمایش به حالت پیشنهادی روشا بازگردد.</p></div></div><AppButton variant="ghost" size="sm" @click="resetOpen = true">بازگردانی پیش‌فرض‌ها</AppButton>
      </AppCard>

      <div v-if="dirty" class="save-bar" role="status"><span><i />تغییرات ذخیره‌نشده دارید</span><div><AppButton variant="ghost" size="sm" @click="discardChanges">لغو تغییرات</AppButton><AppButton size="sm" icon="check" :loading="saving" @click="save">ذخیره تنظیمات</AppButton></div></div>
    </template>

    <AppModal v-model="resetOpen" title="بازگردانی تنظیمات پیش‌فرض؟" description="پوسته، نمایش موجودی و کانال‌های اعلان به حالت پیشنهادی بازمی‌گردند." size="sm">
      <div class="reset-summary"><span><AppIcon name="refresh" :size="24" /></span><p>فهرست دارایی‌های محبوب نیز به انتخاب اولیه بازگردانده می‌شود.</p></div>
      <template #footer><AppButton variant="danger" block :loading="saving" @click="resetSettings">بازگردانی تنظیمات</AppButton><AppButton variant="secondary" :disabled="saving" @click="resetOpen = false">انصراف</AppButton></template>
    </AppModal>
  </div>
</template>

<style scoped>
.settings-page { display: grid; align-content: start; gap: var(--space-5); }.settings-page :deep(.page-header) { margin-bottom: 0; }.notice { display: flex; align-items: center; gap: var(--space-2); padding: var(--space-3) var(--space-4); border: 1px solid; border-radius: var(--radius-md); font-size: var(--font-size-sm); }.notice span { flex: 1; }.notice button { border: 0; background: transparent; color: inherit; font-weight: 600; }.notice.success { border-color: rgba(53,201,149,.22); background: var(--color-success-soft); color: var(--color-success); }.notice.danger { border-color: rgba(240,108,117,.22); background: var(--color-danger-soft); color: var(--color-danger); }.theme-skeletons { display: grid; grid-template-columns: repeat(3,1fr); gap: var(--space-4); margin-top: var(--space-5); }
:global(html[data-reduce-motion='true'] *), :global(html[data-reduce-motion='true'] *::before), :global(html[data-reduce-motion='true'] *::after) { scroll-behavior: auto !important; animation-duration: .01ms !important; animation-iteration-count: 1 !important; transition-duration: .01ms !important; }
.section-heading { display: flex; align-items: center; gap: var(--space-3); margin-bottom: var(--space-5); }.section-heading > span:first-child { display: grid; width: 2.75rem; height: 2.75rem; flex: 0 0 auto; border-radius: .85rem; background: var(--color-primary-soft); color: var(--color-primary); place-items: center; }.section-heading > div { min-width: 0; flex: 1; }.section-heading h2 { margin: 0; font-size: var(--font-size-lg); }.section-heading p { margin: .1rem 0 0; color: var(--color-text-muted); font-size: var(--font-size-xs); }.live-label { display: inline-flex; align-items: center; gap: var(--space-2); color: var(--color-text-muted); font-size: var(--font-size-xs); }.live-label i { width: .5rem; height: .5rem; border-radius: 50%; background: var(--color-success); box-shadow: 0 0 0 4px var(--color-success-soft); }
.theme-grid { display: grid; grid-template-columns: repeat(3,1fr); gap: var(--space-4); }.theme-grid > label { display: grid; gap: var(--space-3); padding: var(--space-3); border: 1px solid var(--color-border); border-radius: var(--radius-lg); background: var(--color-surface-2); cursor: pointer; transition: border-color var(--transition-fast),transform var(--transition-fast); }.theme-grid > label:hover { border-color: var(--color-border-hover); transform: translateY(-1px); }.theme-grid > label.active { border-color: var(--color-primary); box-shadow: 0 0 0 2px var(--color-primary-soft); }.theme-grid input { position: absolute; width: 1px; height: 1px; opacity: 0; }.theme-preview { position: relative; display: block; height: 5.5rem; overflow: hidden; border: 1px solid var(--preview-border); border-radius: var(--radius-md); background: var(--preview-bg); }.theme-preview i { position: absolute; border-radius: .25rem; background: var(--preview-surface); }.theme-preview i:nth-child(1) { inset-block: .45rem; inset-inline-start: .45rem; width: 22%; }.theme-preview i:nth-child(2) { inset-block-start: .55rem; inset-inline-start: 29%; width: 32%; height: .5rem; }.theme-preview i:nth-child(3) { inset-block-start: 1.55rem; inset-inline-start: 29%; width: 60%; height: 2.8rem; }.theme-preview b { position: absolute; inset-block-start: 2.1rem; inset-inline-start: 35%; width: 28%; height: .55rem; border-radius: .25rem; background: var(--color-primary); }.preview-dark { --preview-bg:#07111e;--preview-surface:#17283d;--preview-border:#2b4563; }.preview-light { --preview-bg:#f4f7fb;--preview-surface:#dce4ed;--preview-border:#bccbdd; }.preview-system { --preview-bg:linear-gradient(105deg,#f4f7fb 0 50%,#07111e 50%);--preview-surface:var(--color-primary);--preview-border:#5a718d; }.theme-copy { display: grid; grid-template-columns: auto 1fr auto; align-items: center; gap: var(--space-2); }.theme-icon { display: grid; width: 2.2rem; height: 2.2rem; border-radius: .65rem; background: var(--color-surface-3); color: var(--color-text-secondary); place-items: center; }.active .theme-icon { background: var(--color-primary-soft); color: var(--color-primary); }.theme-copy > span:nth-child(2) { display: grid; }.theme-copy small { color: var(--color-text-muted); font-size: .68rem; }.theme-copy > svg { color: var(--color-primary); }
.theme-persistence { display: flex; align-items: center; gap: var(--space-2); min-height: 2.75rem; margin-top: var(--space-4); padding: var(--space-2) var(--space-3); border: 1px solid var(--color-border-soft); border-radius: var(--radius-md); background: var(--color-surface-2); color: var(--color-text-muted); font-size: var(--font-size-xs); }.theme-persistence > svg { flex: 0 0 auto; color: var(--color-success); }.theme-persistence > span { min-width: 0; flex: 1; }.theme-persistence.danger { border-color: color-mix(in srgb,var(--color-warning) 26%,transparent); background: var(--color-warning-soft); color: var(--color-text-secondary); }.theme-persistence.danger > svg { color: var(--color-warning); }.theme-persistence button { min-height: 2.25rem; padding-inline: var(--space-3); border: 0; border-radius: var(--radius-sm); background: var(--color-warning-soft); color: var(--color-warning); font-weight: 600; }
.settings-layout { display: grid; grid-template-columns: 1fr 1fr; align-items: start; gap: var(--space-5); }.balance-preview { display: flex; align-items: center; justify-content: space-between; gap: var(--space-4); margin-bottom: var(--space-4); padding: var(--space-4); border: 1px solid var(--color-border-soft); border-radius: var(--radius-lg); background: linear-gradient(120deg,var(--color-surface-2),var(--color-primary-soft)); }.balance-preview > span:first-child { display: grid; }.balance-preview small { color: var(--color-text-muted); font-size: var(--font-size-xs); }.balance-preview strong { font-size: var(--font-size-xl); }.balance-preview strong.masked { letter-spacing: .08em; }.preview-eye { display: grid; width: 2.75rem; height: 2.75rem; border-radius: .85rem; background: var(--color-primary-soft); color: var(--color-primary); place-items: center; }.switch-list { display: grid; }.switch-list :deep(.switch-row) { padding-block: var(--space-4); }.switch-list :deep(.switch-row + .switch-row) { border-top: 1px solid var(--color-border-soft); }.switch-list.no-preview { margin-top: -.25rem; }.privacy-tip { display: flex; align-items: flex-start; gap: var(--space-2); margin-top: var(--space-4); padding: var(--space-3); border-radius: var(--radius-md); background: var(--color-info-soft); color: var(--color-info); font-size: var(--font-size-xs); }.privacy-tip span { color: var(--color-text-secondary); }.digit-preview { display: flex; align-items: center; justify-content: space-between; gap: var(--space-3); margin-top: var(--space-4); padding: var(--space-4); border-radius: var(--radius-md); background: var(--color-surface-2); }.digit-preview > span { display: grid; }.digit-preview small { color: var(--color-text-muted); font-size: .68rem; }.digit-preview strong { font-size: var(--font-size-sm); }.digit-preview i { width: 1px; height: 2.5rem; background: var(--color-border); }
.channel-count { margin-inline-start: auto; padding: .25rem .55rem; border-radius: var(--radius-pill); background: var(--color-surface-2); color: var(--color-text-muted); font-size: var(--font-size-xs); }.channel-grid { display: grid; grid-template-columns: repeat(3,1fr); gap: var(--space-4); }.channel-item { display: grid; grid-template-columns: auto 1fr; gap: var(--space-3); padding: var(--space-4); border: 1px solid var(--color-border-soft); border-radius: var(--radius-lg); background: var(--color-surface-2); }.channel-icon { display: grid; width: 3rem; height: 3rem; border-radius: .9rem; background: var(--color-primary-soft); color: var(--color-primary); place-items: center; }.channel-item > div { display: flex; align-content: start; flex-wrap: wrap; column-gap: var(--space-2); }.channel-item strong { width: 100%; }.channel-item small { width: 100%; color: var(--color-text-muted); font-size: var(--font-size-xs); }.channel-item em { margin-top: var(--space-2); padding: .12rem .45rem; border-radius: var(--radius-pill); background: var(--color-success-soft); color: var(--color-success); font-size: .68rem; font-style: normal; }.channel-item :deep(.switch-row) { grid-column: 1 / -1; padding-top: var(--space-3); border-top: 1px solid var(--color-border-soft); }.channel-warning { display: flex; align-items: center; gap: var(--space-2); margin-top: var(--space-4); padding: var(--space-3); border-radius: var(--radius-md); background: var(--color-warning-soft); color: var(--color-warning); font-size: var(--font-size-sm); }
.settings-footer-card { display: flex; align-items: center; justify-content: space-between; gap: var(--space-4); }.settings-footer-card > div { display: flex; align-items: center; gap: var(--space-3); }.settings-footer-card > div > span { display: grid; width: 2.75rem; height: 2.75rem; border-radius: .85rem; background: var(--color-surface-2); color: var(--color-text-muted); place-items: center; }.settings-footer-card h3 { margin: 0; font-size: var(--font-size-md); }.settings-footer-card p { margin: .1rem 0 0; color: var(--color-text-muted); font-size: var(--font-size-xs); }.save-bar { position: sticky; z-index: 10; bottom: calc(var(--space-4) + var(--safe-bottom)); display: flex; align-items: center; justify-content: space-between; gap: var(--space-4); width: min(100%,42rem); margin-inline: auto; padding: var(--space-3); border: 1px solid var(--color-border-hover); border-radius: var(--radius-lg); background: color-mix(in srgb,var(--color-surface-raised) 94%,transparent); box-shadow: var(--shadow-md); backdrop-filter: blur(14px); }.save-bar > span { display: flex; align-items: center; gap: var(--space-2); font-size: var(--font-size-sm); }.save-bar > span i { width: .5rem; height: .5rem; border-radius: 50%; background: var(--color-warning); }.save-bar > div { display: flex; gap: var(--space-2); }.reset-summary { display: flex; align-items: center; gap: var(--space-3); padding: var(--space-4); border-radius: var(--radius-md); background: var(--color-danger-soft); }.reset-summary > span { display: grid; width: 2.75rem; height: 2.75rem; border-radius: .8rem; background: rgba(240,108,117,.1); color: var(--color-danger); place-items: center; }.reset-summary p { margin: 0; color: var(--color-text-secondary); }
.notice button { display: inline-grid; min-width: 2.75rem; min-height: 2.75rem; padding-inline: var(--space-2); border-radius: var(--radius-sm); place-items: center; }.notice button:focus-visible { outline: 2px solid currentColor; outline-offset: 2px; }
.appearance-card,.notifications-settings { position: relative; overflow: hidden; }.appearance-card::after,.notifications-settings::after { position: absolute; inset-block: 8%; inset-inline-start: 0; width: 2px; border-radius: var(--radius-pill); background: linear-gradient(180deg,transparent,var(--color-gold),transparent); content: ''; opacity: .62; }.appearance-card > *,.notifications-settings > * { position: relative; z-index: 1; }
.theme-grid input:focus-visible + .theme-preview { outline: 2px solid var(--color-border-focus); outline-offset: 3px; }
.theme-grid > label:active { transform: scale(.995); }
.balance-preview > span:first-child { min-width: 0; }.balance-preview strong { overflow-wrap: anywhere; }
.channel-item :deep(.switch-copy) { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); clip-path: inset(50%); white-space: nowrap; }
.channel-item { transition: border-color var(--transition-fast), background var(--transition-fast), transform var(--transition-fast); }
@media (hover: hover) { .channel-item:hover { border-color: var(--color-border-hover); background: color-mix(in srgb,var(--color-primary-soft) 32%,var(--color-surface-2)); transform: translateY(-1px); } }
@media (max-width: 1199px) { .save-bar { bottom: calc(var(--mobile-nav-height) + var(--safe-bottom) + var(--space-2)); } }
@media (max-width: 1000px) { .channel-grid { grid-template-columns: 1fr; }.channel-item { grid-template-columns: auto minmax(0,1fr) auto; }.channel-item :deep(.switch-row) { grid-column: auto; padding: 0; border: 0; } }
@media (max-width: 767px) { .theme-skeletons,.theme-grid,.settings-layout { grid-template-columns: 1fr; }.theme-grid > label { grid-template-columns: 7rem 1fr; align-items: center; }.theme-preview { height: 4.8rem; }.theme-copy { grid-template-columns: auto 1fr auto; }.section-heading { align-items: flex-start; }.live-label { display: none; }.balance-preview strong { font-size: var(--font-size-lg); }.digit-preview { align-items: flex-start; flex-direction: column; }.digit-preview i { width: 100%; height: 1px; }.channel-count { display: none; }.channel-item { grid-template-columns: auto minmax(0,1fr); }.channel-item :deep(.switch-row) { grid-column: 1 / -1; padding-top: var(--space-3); border-top: 1px solid var(--color-border-soft); }.settings-footer-card { align-items: flex-start; flex-direction: column; }.settings-footer-card :deep(.app-button) { width: 100%; }.save-bar { bottom: calc(var(--mobile-nav-height) + var(--safe-bottom) + var(--space-2)); }.save-bar > span { display: none; }.save-bar > div { width: 100%; }.save-bar :deep(.app-button) { flex: 1; } }
@media (max-width: 399px) {
  .theme-grid > label { grid-template-columns: 5.75rem minmax(0, 1fr); gap: var(--space-2); padding: var(--space-2); }
  .theme-preview { height: 4.25rem; }
  .theme-icon { width: 2rem; height: 2rem; }
  .theme-copy { gap: var(--space-1); }
  .balance-preview { gap: var(--space-2); padding: var(--space-3); }
  .balance-preview strong { font-size: var(--font-size-md); }
  .channel-item { gap: var(--space-2); padding: var(--space-3); }
  .channel-icon { width: 2.6rem; height: 2.6rem; }
  .settings-footer-card > div { align-items: flex-start; }
  .save-bar { padding: var(--space-2); }
  .save-bar > div { gap: var(--space-1); }
  .save-bar :deep(.app-button) { min-height: 2.75rem; padding-inline: var(--space-2); }
}
</style>
