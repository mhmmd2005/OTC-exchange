<script setup lang="ts">
import {computed, onMounted, reactive, ref, watch} from 'vue'
import BankLogo from '@/components/finance/BankLogo.vue'
import DigitalBankCard from '@/components/finance/DigitalBankCard.vue'
import AppButton from '@/components/ui/AppButton.vue'
import AppCard from '@/components/ui/AppCard.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import AppInput from '@/components/ui/AppInput.vue'
import AppModal from '@/components/ui/AppModal.vue'
import AppSkeleton from '@/components/ui/AppSkeleton.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import {ApiError, bankService} from '@/services'
import type {BankAccount, IranianBank} from '@/types'
import {
  formatCardNumber,
  formatIban,
  formatMaskedCardOverview,
  normalizeDigits,
  toPersianDigits,
} from '@/utils/formatters'
import {isValidIranianCardNumber, isValidIranianIban} from '@/utils/validators'

const accounts = ref<BankAccount[]>([])
const loading = ref(true)
const pageError = ref('')
const feedback = ref('')
const addOpen = ref(false)
const deleteTarget = ref<BankAccount | null>(null)
const submitting = ref(false)
const preferredLoadingId = ref('')
const deleting = ref(false)
const detectedBank = ref<IranianBank | null>(null)
const detectingBank = ref(false)

const form = reactive({cardNumber: '', iban: '', accountNumber: ''})
const formErrors = reactive<Record<string, string>>({})

const verifiedCount = computed(() => accounts.value.filter((account) => account.status === 'verified').length)

function errorMessage(error: unknown, fallback: string): string {
  return error instanceof Error ? error.message : fallback
}

function resetForm(): void {
  form.cardNumber = ''
  form.iban = ''
  form.accountNumber = ''
  detectedBank.value = null
  Object.keys(formErrors).forEach((key) => delete formErrors[key])
}

function openAdd(): void {
  resetForm()
  feedback.value = ''
  addOpen.value = true
}

async function loadAccounts(): Promise<void> {
  loading.value = true
  pageError.value = ''
  try {
    accounts.value = await bankService.listAccounts()
  } catch (error) {
    pageError.value = errorMessage(error, 'حساب‌های بانکی بارگیری نشدند.')
  } finally {
    loading.value = false
  }
}

let detectionSequence = 0
watch(() => form.cardNumber, async (value) => {
  const digits = normalizeDigits(value).replace(/\D/g, '')
  formErrors.cardNumber = ''
  if (digits.length < 6) {
    detectedBank.value = null
    return
  }
  const sequence = ++detectionSequence
  detectingBank.value = true
  try {
    const bank = await bankService.detectBank(digits.slice(0, 6))
    if (sequence === detectionSequence) detectedBank.value = bank
  } catch {
    if (sequence === detectionSequence) detectedBank.value = null
  } finally {
    if (sequence === detectionSequence) detectingBank.value = false
  }
})

function updateCardNumber(value: string): void {
  form.cardNumber = formatCardNumber(value)
}

function updateIban(value: string): void {
  form.iban = formatIban(value)
}

function validateForm(): boolean {
  Object.keys(formErrors).forEach((key) => delete formErrors[key])

  const cardNumber = normalizeDigits(form.cardNumber).replace(/\D/g, '')
  const iban = formatIban(form.iban).replace(/\s/g, '')

  if (!/^\d{16}$/.test(cardNumber)) {
    formErrors.cardNumber = 'شماره کارت باید ۱۶ رقم باشد.'
  } else if (!isValidIranianCardNumber(cardNumber)) {
    formErrors.cardNumber = 'شماره کارت معتبر نیست؛ رقم‌ها را دوباره بررسی کنید.'
  }

  if (!/^IR\d{24}$/.test(iban)) {
    formErrors.iban = 'شماره شبا باید با IR شروع شود و ۲۴ رقم داشته باشد.'
  } else if (!isValidIranianIban(iban)) {
    formErrors.iban = 'شماره شبای واردشده معتبر نیست.'
  }

  return Object.keys(formErrors).every((key) => !formErrors[key])
}

async function addAccount(): Promise<void> {
  if (!validateForm()) return
  submitting.value = true
  try {
    await bankService.addAccount({
      cardNumber: form.cardNumber,
      iban: form.iban,
      accountNumber: form.accountNumber.trim() || undefined,
    })
    await loadAccounts()
    addOpen.value = false
    feedback.value = 'حساب بانکی ثبت شد و برای بررسی ارسال شد.'
  } catch (error) {
    if (error instanceof ApiError && error.details?.fields) Object.assign(formErrors, error.details.fields)
    formErrors.form = errorMessage(error, 'ثبت حساب بانکی انجام نشد.')
  } finally {
    submitting.value = false
  }
}

async function setPreferred(account: BankAccount): Promise<void> {
  preferredLoadingId.value = account.id
  pageError.value = ''
  try {
    await bankService.setPreferred(account.id)
    await loadAccounts()
    feedback.value = `${account.bank.nameFa} به‌عنوان حساب منتخب تنظیم شد.`
  } catch (error) {
    pageError.value = errorMessage(error, 'تغییر حساب منتخب انجام نشد.')
  } finally {
    preferredLoadingId.value = ''
  }
}

async function removeAccount(): Promise<void> {
  if (!deleteTarget.value) return
  const target = deleteTarget.value
  deleting.value = true
  pageError.value = ''
  try {
    await bankService.removeAccount(target.id)
    const bankName = target.bank.nameFa
    deleteTarget.value = null
    await loadAccounts()
    feedback.value = `حساب ${bankName} حذف شد.`
  } catch (error) {
    pageError.value = errorMessage(error, 'حذف حساب بانکی انجام نشد.')
    deleteTarget.value = null
  } finally {
    deleting.value = false
  }
}

onMounted(loadAccounts)
</script>

<template>
  <div class="page bank-page">
    <PageHeader title="حساب‌های بانکی" description="حساب‌های به‌نام خودتان را برای واریز و برداشت مدیریت کنید.">
      <template #actions>
        <AppButton icon="plus" @click="openAdd">افزودن حساب</AppButton>
      </template>
    </PageHeader>

    <div v-if="feedback" class="notice notice--success" role="status">
      <AppIcon name="check" :size="20"/>
      <span>{{ feedback }}</span>
      <button type="button" aria-label="بستن پیام" @click="feedback = ''">
        <AppIcon name="close" :size="17"/>
      </button>
    </div>
    <div v-if="pageError" class="notice notice--danger" role="alert">
      <AppIcon name="warning" :size="20"/>
      <span>{{ pageError }}</span>
      <button type="button" @click="loadAccounts">تلاش دوباره</button>
    </div>

    <AppCard class="bank-overview" variant="financial" padding="lg">
      <div class="overview-copy">
        <div class="overview-icon">
          <AppIcon name="bank" :size="27"/>
        </div>
        <div>
          <span class="overview-eyebrow">کیف بانکی شما</span>
          <strong>{{ toPersianDigits(accounts.length) }} حساب ثبت‌شده</strong>
          <p>{{ toPersianDigits(verifiedCount) }} حساب برای تسویه تومان آماده است.</p>
        </div>
      </div>
      <div class="overview-security">
        <AppIcon name="shield" :size="20"/>
        <span><strong>مالکیت حساب کنترل می‌شود</strong><small>فقط حساب به‌نام صاحب حساب کاربری تأیید خواهد شد.</small></span>
      </div>
    </AppCard>

    <div v-if="loading" class="account-grid" aria-label="در حال بارگیری حساب‌ها">
      <AppCard v-for="index in 2" :key="index" padding="lg">
        <div class="skeleton-card">
          <AppSkeleton height="3rem" width="3rem" radius="1rem"/>
          <AppSkeleton height="1.25rem" width="8rem"/>
          <AppSkeleton height="1.6rem" width="80%"/>
          <AppSkeleton height="1rem" width="65%"/>
        </div>
      </AppCard>
    </div>

    <AppCard v-else-if="!accounts.length" padding="none">
      <EmptyState icon="bank" title="هنوز حساب بانکی ثبت نکرده‌اید"
                  description="برای واریز و برداشت تومان، یک حساب بانکی به نام خودتان اضافه کنید.">
        <AppButton icon="plus" @click="openAdd">افزودن حساب بانکی</AppButton>
      </EmptyState>
    </AppCard>

    <div v-else class="account-grid">
      <DigitalBankCard
          v-for="account in accounts"
          :key="account.id"
          :account="account"
          :preferred-loading="preferredLoadingId === account.id"
          @preferred="setPreferred"
          @remove="deleteTarget = $event"
      />
    </div>

    <AppModal v-model="addOpen" title="افزودن حساب بانکی" description="اطلاعات کارت و شبا باید متعلق به خودتان باشد."
              size="md">
      <form class="bank-form" @submit.prevent="addAccount">
        <div v-if="formErrors.form" class="form-error" role="alert">{{ formErrors.form }}</div>
        <AppInput
            :model-value="form.cardNumber"
            label="شماره کارت"
            placeholder="۶۲۱۹ ۸۶۱۰ ۳۴۵۶ ۷۸۱۲"
            inputmode="numeric"
            autocomplete="cc-number"
            ltr
            :error="formErrors.cardNumber"
            @update:model-value="updateCardNumber"
        />
        <div class="detected-bank" :class="{ 'is-empty': !detectedBank }" aria-live="polite">
          <BankLogo v-if="detectedBank" :bank="detectedBank" size="sm"/>
          <span v-else class="detected-icon"><AppIcon :name="detectingBank ? 'refresh' : 'bank'" :size="18"/></span>
          <span>
            <strong>{{
                detectingBank ? 'در حال شناسایی بانک…' : detectedBank?.nameFa || 'بانک صادرکننده به‌صورت خودکار شناسایی می‌شود'
              }}</strong>
            <small v-if="detectedBank">{{ detectedBank.nameEn }}</small>
          </span>
        </div>
        <AppInput
            :model-value="form.iban"
            label="شماره شبا"
            placeholder="IR82 0560 0800 8010 2735 0510 01"
            inputmode="text"
            autocomplete="off"
            ltr
            :error="formErrors.iban"
            @update:model-value="updateIban"
        />
        <AppInput v-model="form.accountNumber" label="شماره حساب (اختیاری)" inputmode="numeric" ltr/>
        <div class="ownership-alert">
          <AppIcon name="info" :size="19"/>
          <span>به‌دلیل الزامات مالی، حساب مشترک یا حساب متعلق به شخص دیگر تأیید نمی‌شود.</span></div>
      </form>
      <template #footer>
        <AppButton block :loading="submitting" @click="addAccount">ثبت و ارسال برای بررسی</AppButton>
        <AppButton variant="secondary" :disabled="submitting" @click="addOpen = false">انصراف</AppButton>
      </template>
    </AppModal>

    <AppModal
        :model-value="Boolean(deleteTarget)"
        title="حذف حساب بانکی؟"
        description="پس از حذف، برای استفاده دوباره باید حساب را ثبت کنید."
        size="sm"
        :dismissible="!deleting"
        @update:model-value="(value) => { if (!value && !deleting) deleteTarget = null }"
    >
      <div v-if="deleteTarget" class="delete-summary">
        <BankLogo :bank="deleteTarget.bank" size="md"/>
        <span><strong>{{ deleteTarget.bank.nameFa }}</strong><small
            class="ltr">{{ formatMaskedCardOverview(deleteTarget.cardNumber, {usePersianDigits: true}) }}</small></span>
      </div>
      <template #footer>
        <AppButton variant="danger" block :loading="deleting" @click="removeAccount">بله، حذف شود</AppButton>
        <AppButton variant="secondary" :disabled="deleting" @click="deleteTarget = null">انصراف</AppButton>
      </template>
    </AppModal>
  </div>
</template>

<style scoped>
.bank-page {
  display: grid;
  max-width: 76rem;
  align-content: start;
  gap: var(--space-5);
}

.bank-page :deep(.page-header) {
  margin-bottom: 0;
}

.notice {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  border: 1px solid;
  border-radius: var(--radius-md);
  font-size: var(--font-size-sm);
}

.notice > span {
  min-width: 0;
  flex: 1;
}

.notice button {
  display: inline-grid;
  min-width: 2.75rem;
  min-height: 2.75rem;
  padding-inline: var(--space-2);
  border: 0;
  border-radius: var(--radius-sm);
  background: transparent;
  color: inherit;
  font-weight: 600;
  place-items: center;
}

.notice button:focus-visible {
  outline: 2px solid currentColor;
  outline-offset: 2px;
}

.notice--success {
  border-color: rgba(53, 201, 149, .24);
  background: var(--color-success-soft);
  color: var(--color-success);
}

.notice--danger {
  border-color: rgba(240, 108, 117, .24);
  background: var(--color-danger-soft);
  color: var(--color-danger);
}

.bank-overview {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-5);
  overflow: hidden;
}

.bank-overview::after {
  position: absolute;
  inset-block: var(--space-4);
  inset-inline-start: 0;
  width: 2px;
  border-radius: var(--radius-pill);
  background: linear-gradient(180deg, transparent, var(--color-gold), transparent);
  content: '';
  opacity: .75;
}

.overview-copy {
  display: flex;
  min-width: 0;
  align-items: center;
  gap: var(--space-4);
}

.overview-icon {
  display: grid;
  width: 3.5rem;
  height: 3.5rem;
  flex: 0 0 auto;
  border: 1px solid var(--color-gold-border);
  border-radius: 1rem;
  background: var(--color-gold-soft);
  color: var(--color-gold);
  place-items: center;
}

.overview-copy > div:last-child {
  display: grid;
  min-width: 0;
}

.overview-eyebrow {
  color: var(--color-gold);
  font-size: var(--font-size-xs);
  font-weight: 600;
}

.bank-overview strong {
  font-size: var(--font-size-lg);
}

.bank-overview p {
  margin: 0;
  color: var(--text-muted);
  font-size: var(--font-size-sm);
}

.overview-security {
  display: flex;
  max-width: 25rem;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  background: color-mix(in srgb, var(--surface-secondary) 78%, transparent);
  color: var(--color-success);
}

.overview-security > span {
  display: grid;
}

.overview-security strong {
  color: var(--text-secondary);
  font-size: var(--font-size-sm);
}

.overview-security small {
  color: var(--text-muted);
  font-size: var(--font-size-xs);
}

.account-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--space-5);
}

.skeleton-card {
  display: grid;
  grid-template-columns: auto 1fr;
  align-items: center;
  gap: var(--space-4);
}

.skeleton-card :nth-child(n+3) {
  grid-column: 1 / -1;
}

.bank-form {
  display: grid;
  gap: var(--space-4);
}

.form-error {
  padding: var(--space-3);
  border-radius: var(--radius-md);
  background: var(--color-danger-soft);
  color: var(--color-danger);
  font-size: var(--font-size-sm);
}

.detected-bank {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  margin-top: calc(var(--space-2) * -1);
  padding: var(--space-3);
  border: 1px solid var(--color-border-soft);
  border-radius: var(--radius-md);
  background: var(--color-surface-2);
}

.detected-bank.is-empty {
  color: var(--color-text-muted);
}

.detected-icon {
  display: grid;
  width: 2.5rem;
  height: 2.5rem;
  flex: 0 0 auto;
  border-radius: .75rem;
  background: var(--color-surface-3);
  color: var(--text-muted);
  place-items: center;
}

.detected-bank > span:last-child {
  display: grid;
}

.detected-bank strong {
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  font-weight: 500;
}

.detected-bank small {
  color: var(--color-text-muted);
  direction: ltr;
  font-size: var(--font-size-xs);
  text-align: right;
}

.ownership-alert {
  display: flex;
  align-items: flex-start;
  gap: var(--space-2);
  padding: var(--space-3);
  border-radius: var(--radius-md);
  background: var(--color-info-soft);
  color: var(--color-info);
  font-size: var(--font-size-xs);
}

.ownership-alert span {
  color: var(--color-text-secondary);
}

.delete-summary {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-4);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface-2);
}

.delete-summary > span:last-child {
  display: grid;
  gap: .15rem;
}

.delete-summary small {
  color: var(--color-text-muted);
}

@media (max-width: 900px) {
  .account-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 767px) {
  .bank-overview {
    align-items: stretch;
    flex-direction: column;
  }

  .overview-security {
    width: 100%;
    max-width: none;
  }

  .account-grid {
    gap: var(--space-4);
  }
}

@media (max-width: 399px) {
  .bank-overview, .overview-copy {
    gap: var(--space-3);
  }

  .overview-icon {
    width: 3rem;
    height: 3rem;
    border-radius: .85rem;
  }

  .overview-security {
    padding: var(--space-3);
  }

  .bank-overview strong {
    font-size: var(--font-size-md);
  }
}
</style>
