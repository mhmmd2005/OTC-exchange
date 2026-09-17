<script setup lang="ts">
import {computed, ref} from 'vue'
import AppButton from '@/components/ui/AppButton.vue'
import AppCard from '@/components/ui/AppCard.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import AppModal from '@/components/ui/AppModal.vue'
import StatusBadge from '@/components/ui/StatusBadge.vue'
import {type AdminBankAccount, type AdminKycApplication, kycAdminService,} from '@/services/admin/kycAdmin.service'
import {formatPersianDate} from '@/utils/formatters'

const props = defineProps<{
  application: AdminKycApplication
}>()

const emit = defineEmits<{
  close: []
  updated: []
}>()

const loading = ref(false)
const error = ref('')

const rejectStep = ref<
    'basic_info' | 'identity' | 'bank' | null
>(null)

const rejectReason = ref('')
const selectedBank = ref<AdminBankAccount | null>(null)

const basicInfo = computed(() => props.application)
const identity = computed(() => props.application)
const bankAccounts = computed(
    () => props.application.bankAccounts ?? [],
)

function clearError(): void {
  error.value = ''
}

function readableError(
    errorValue: unknown,
    fallback: string,
): string {
  return errorValue instanceof Error
      ? errorValue.message
      : fallback
}

function openReject(
    step: 'basic_info' | 'identity',
): void {
  clearError()
  rejectStep.value = step
  selectedBank.value = null
  rejectReason.value = ''
}

function openRejectBank(
    account: AdminBankAccount,
): void {
  clearError()
  rejectStep.value = 'bank'
  selectedBank.value = account
  rejectReason.value = ''
}

function closeReject(): void {
  rejectStep.value = null
  selectedBank.value = null
  rejectReason.value = ''
}

async function approve(
    step: 'basic_info' | 'identity',
): Promise<void> {
  if (loading.value) return

  loading.value = true
  error.value = ''

  try {
    if (step === 'basic_info') {
      await kycAdminService.approveBasicInfo(
          props.application.id,
      )
    } else {
      await kycAdminService.approveIdentity(
          props.application.id,
      )
    }

    emit('updated')
  } catch (caught) {
    error.value = readableError(
        caught,
        'عملیات تأیید انجام نشد.',
    )
  } finally {
    loading.value = false
  }
}

async function approveBank(
    account: AdminBankAccount,
): Promise<void> {
  if (loading.value) return

  loading.value = true
  error.value = ''

  try {
    await kycAdminService.approveBank(
        props.application.id,
        account.id,
    )

    emit('updated')
  } catch (caught) {
    error.value = readableError(
        caught,
        'تأیید حساب بانکی انجام نشد.',
    )
  } finally {
    loading.value = false
  }
}

async function reject(): Promise<void> {
  if (!rejectStep.value || loading.value) return

  const reason = rejectReason.value.trim()

  if (!reason) {
    error.value = 'دلیل رد را وارد کنید.'
    return
  }

  loading.value = true
  error.value = ''

  try {
    if (rejectStep.value === 'basic_info') {
      await kycAdminService.rejectBasicInfo(
          props.application.id,
          reason,
      )
    } else if (rejectStep.value === 'identity') {
      await kycAdminService.rejectIdentity(
          props.application.id,
          reason,
      )
    } else {
      if (!selectedBank.value) {
        error.value = 'حساب بانکی مورد نظر پیدا نشد.'
        return
      }

      await kycAdminService.rejectBank(
          props.application.id,
          selectedBank.value.id,
          reason,
      )
    }

    closeReject()
    emit('updated')
  } catch (caught) {
    error.value = readableError(
        caught,
        'عملیات رد انجام نشد.',
    )
  } finally {
    loading.value = false
  }
}

function documentUrl(): string {
  return props.application.identityDocument || ''
}

function formatCardNumber(cardNumber: string): string {
  const digits = cardNumber.replace(/\D/g, '')

  if (digits.length !== 16) {
    return cardNumber || '—'
  }

  return digits.replace(/(\d{4})(?=\d)/g, '$1-')
}

function formatIban(iban: string): string {
  const normalized = iban
      .replace(/\s+/g, '')
      .toUpperCase()

  if (!normalized) return '—'

  return normalized.replace(/(.{4})/g, '$1 ').trim()
}

function bankName(account: AdminBankAccount): string {
  return (
      account.bank?.nameFa ||
      account.bank?.nameEn ||
      'بانک نامشخص'
  )
}

function bankOwnerMatchesKyc(
    account: AdminBankAccount,
): boolean {
  const kycName = `${props.application.firstName} ${props.application.lastName}`
      .trim()

  return (
      account.ownerName.trim() === kycName &&
      kycName.length > 0
  )
}
</script>

<template>
  <div class="kyc-detail">
    <header class="detail-header">
      <div>
        <div class="detail-header__top">
          <h2>
            {{
              `${application.firstName} ${application.lastName}`.trim()
              || application.phoneNumber
              || 'KYC Application'
            }}
          </h2>

          <StatusBadge
              domain="kyc"
              :status="application.status"
          />
        </div>

        <p>
          {{ application.phoneNumber || '—' }}
        </p>
      </div>

      <AppButton
          variant="ghost"
          size="sm"
          icon="close"
          @click="emit('close')"
      >
        بستن
      </AppButton>
    </header>

    <div
        v-if="error"
        class="detail-error"
        role="alert"
    >
      <AppIcon name="warning" :size="18"/>
      <span>{{ error }}</span>

      <button
          type="button"
          @click="clearError"
      >
        <AppIcon name="close" :size="16"/>
      </button>
    </div>

    <div class="review-grid">
      <AppCard padding="lg" class="review-card">
        <header class="review-card__header">
          <div>
            <span class="review-card__icon">
              <AppIcon name="user" :size="21"/>
            </span>

            <div>
              <h3>اطلاعات هویتی</h3>
              <p>بررسی اطلاعات پایه کاربر</p>
            </div>
          </div>

          <StatusBadge
              domain="kyc"
              :status="basicInfo.basicInfoStatus"
          />
        </header>

        <div class="review-fields">
          <div>
            <span>نام</span>
            <strong>
              {{ basicInfo.firstName || '—' }}
            </strong>
          </div>

          <div>
            <span>نام خانوادگی</span>
            <strong>
              {{ basicInfo.lastName || '—' }}
            </strong>
          </div>

          <div>
            <span>کد ملی</span>
            <strong dir="ltr">
              {{ basicInfo.nationalId || '—' }}
            </strong>
          </div>

          <div>
            <span>تاریخ تولد</span>
            <strong>
              {{ basicInfo.birthDate || '—' }}
            </strong>
          </div>

          <div>
            <span>ارسال شده</span>
            <strong>
              {{
                basicInfo.basicInfoSubmittedAt
                    ? formatPersianDate(
                        basicInfo.basicInfoSubmittedAt,
                    )
                    : '—'
              }}
            </strong>
          </div>

          <div>
            <span>بررسی شده</span>
            <strong>
              {{
                basicInfo.basicInfoReviewedAt
                    ? formatPersianDate(
                        basicInfo.basicInfoReviewedAt,
                    )
                    : '—'
              }}
            </strong>
          </div>

          <div class="full">
            <span>بررسی‌کننده</span>
            <strong>
              {{ basicInfo.basicInfoReviewedBy || '—' }}
            </strong>
          </div>

          <div
              v-if="basicInfo.basicInfoRejectionReason"
              class="full rejection"
          >
            <span>علت رد</span>
            <strong>
              {{ basicInfo.basicInfoRejectionReason }}
            </strong>
          </div>
        </div>

        <div
            v-if="basicInfo.basicInfoStatus === 'pending'"
            class="review-actions"
        >
          <AppButton
              variant="primary"
              icon="check"
              :loading="loading"
              @click="approve('basic_info')"
          >
            تأیید اطلاعات هویتی
          </AppButton>

          <AppButton
              variant="secondary"
              icon="close"
              :disabled="loading"
              @click="openReject('basic_info')"
          >
            رد اطلاعات هویتی
          </AppButton>
        </div>

        <div
            v-else-if="basicInfo.basicInfoStatus === 'approved'"
            class="review-result approved"
        >
          <AppIcon name="check" :size="18"/>
          اطلاعات هویتی تأیید شده است.
        </div>
      </AppCard>

      <AppCard padding="lg" class="review-card">
        <header class="review-card__header">
          <div>
            <span class="review-card__icon">
              <AppIcon name="verify" :size="21"/>
            </span>

            <div>
              <h3>مدرک شناسایی</h3>
              <p>بررسی مدرک ارسال‌شده</p>
            </div>
          </div>

          <StatusBadge
              domain="kyc"
              :status="identity.identityStatus"
          />
        </header>

        <div class="review-fields">
          <div>
            <span>ارسال شده</span>
            <strong>
              {{
                identity.identitySubmittedAt
                    ? formatPersianDate(
                        identity.identitySubmittedAt,
                    )
                    : '—'
              }}
            </strong>
          </div>

          <div>
            <span>بررسی شده</span>
            <strong>
              {{
                identity.identityReviewedAt
                    ? formatPersianDate(
                        identity.identityReviewedAt,
                    )
                    : '—'
              }}
            </strong>
          </div>

          <div class="full">
            <span>بررسی‌کننده</span>
            <strong>
              {{ identity.identityReviewedBy || '—' }}
            </strong>
          </div>

          <div
              v-if="identity.identityRejectionReason"
              class="full rejection"
          >
            <span>علت رد</span>
            <strong>
              {{ identity.identityRejectionReason }}
            </strong>
          </div>

          <div class="full">
            <span>مدرک</span>

            <a
                v-if="documentUrl()"
                :href="documentUrl()"
                target="_blank"
                rel="noopener noreferrer"
                class="document-link"
            >
              <AppIcon
                  name="externalLink"
                  :size="16"
              />
              مشاهده مدرک شناسایی
            </a>

            <strong v-else>—</strong>
          </div>
        </div>

        <div
            v-if="identity.identityStatus === 'pending'"
            class="review-actions"
        >
          <AppButton
              variant="primary"
              icon="check"
              :loading="loading"
              @click="approve('identity')"
          >
            تأیید مدرک شناسایی
          </AppButton>

          <AppButton
              variant="secondary"
              icon="close"
              :disabled="loading"
              @click="openReject('identity')"
          >
            رد مدرک شناسایی
          </AppButton>
        </div>

        <div
            v-else-if="identity.identityStatus === 'approved'"
            class="review-result approved"
        >
          <AppIcon name="check" :size="18"/>
          مدرک شناسایی تأیید شده است.
        </div>
      </AppCard>

      <AppCard
          padding="lg"
          class="review-card bank-review-card"
      >
        <header class="review-card__header">
          <div>
            <span class="review-card__icon">
              <AppIcon name="bank" :size="21"/>
            </span>

            <div>
              <h3>حساب‌های بانکی</h3>
              <p>
                بررسی مستقل حساب‌های ثبت‌شده کاربر
              </p>
            </div>
          </div>

          <span class="bank-count">
            {{ bankAccounts.length }} حساب
          </span>
        </header>

        <div
            v-if="!bankAccounts.length"
            class="bank-empty"
        >
          <AppIcon name="bank" :size="24"/>
          <span>
            هنوز حساب بانکی برای این کاربر ثبت نشده است.
          </span>
        </div>

        <div
            v-else
            class="bank-list"
        >
          <div
              v-for="account in bankAccounts"
              :key="account.id"
              class="bank-account"
          >
            <div class="bank-account__header">
              <div>
                <strong>
                  {{ bankName(account) }}
                </strong>

                <span>
                  {{
                    account.preferred
                        ? 'حساب منتخب'
                        : 'حساب بانکی'
                  }}
                </span>
              </div>

              <StatusBadge
                  domain="bank"
                  :status="account.status"
              />
            </div>

            <div class="review-fields">
              <div>
                <span>نام صاحب حساب</span>
                <strong>
                  {{ account.ownerName || '—' }}
                </strong>
              </div>

              <div>
                <span>تطابق با احراز هویت</span>

                <strong
                    :class="{
                    'match-success':
                      bankOwnerMatchesKyc(account),
                    'match-danger':
                      !bankOwnerMatchesKyc(account),
                  }"
                >
                  {{
                    bankOwnerMatchesKyc(account)
                        ? 'مطابق است'
                        : 'مطابق نیست'
                  }}
                </strong>
              </div>

              <div>
                <span>شماره کارت</span>
                <strong dir="ltr">
                  {{ formatCardNumber(account.cardNumber) }}
                </strong>
              </div>

              <div>
                <span>شماره شبا</span>
                <strong dir="ltr">
                  {{ formatIban(account.iban) }}
                </strong>
              </div>

              <div>
                <span>شماره حساب</span>
                <strong dir="ltr">
                  {{ account.accountNumber || '—' }}
                </strong>
              </div>

              <div>
                <span>تاریخ ثبت</span>
                <strong>
                  {{
                    account.createdAt
                        ? formatPersianDate(account.createdAt)
                        : '—'
                  }}
                </strong>
              </div>

              <div
                  v-if="account.verifiedAt"
              >
                <span>تاریخ تأیید</span>
                <strong>
                  {{
                    formatPersianDate(account.verifiedAt)
                  }}
                </strong>
              </div>

              <div class="full">
                <span>قابل استفاده</span>
                <strong
                    :class="{
                    'match-success':
                      account.isUsable,
                    'match-danger':
                      !account.isUsable,
                  }"
                >
                  {{
                    account.isUsable
                        ? 'بله'
                        : 'خیر'
                  }}
                </strong>
              </div>

              <div
                  v-if="account.rejectionReason"
                  class="full rejection"
              >
                <span>علت رد</span>
                <strong>
                  {{ account.rejectionReason }}
                </strong>
              </div>
            </div>

            <div
                v-if="account.status === 'pending'"
                class="review-actions"
            >
              <AppButton
                  variant="primary"
                  icon="check"
                  :loading="loading"
                  :disabled="
                  loading ||
                  !bankOwnerMatchesKyc(account)
                "
                  @click="approveBank(account)"
              >
                تأیید حساب بانکی
              </AppButton>

              <AppButton
                  variant="secondary"
                  icon="close"
                  :disabled="loading"
                  @click="openRejectBank(account)"
              >
                رد حساب بانکی
              </AppButton>
            </div>

            <div
                v-else-if="account.status === 'verified'"
                class="review-result approved"
            >
              <AppIcon name="check" :size="18"/>
              حساب بانکی تأیید شده و قابل استفاده است.
            </div>

            <div
                v-else-if="account.status === 'rejected'"
                class="review-result rejected-result"
            >
              <AppIcon name="close" :size="18"/>
              این حساب بانکی رد شده است.
            </div>
          </div>
        </div>
      </AppCard>
    </div>

    <AppModal
        :model-value="Boolean(rejectStep)"
        :title="
        rejectStep === 'basic_info'
          ? 'رد اطلاعات هویتی'
          : rejectStep === 'identity'
            ? 'رد مدرک شناسایی'
            : 'رد حساب بانکی'
      "
        description="دلیل رد را وارد کنید. این دلیل برای کاربر قابل مشاهده خواهد بود."
        size="md"
        @update:model-value="
        (value) => !value && closeReject()
      "
    >
      <form
          class="reject-form"
          @submit.prevent="reject"
      >
        <label for="reject-reason">
          دلیل رد
        </label>

        <textarea
            id="reject-reason"
            v-model="rejectReason"
            rows="6"
            maxlength="2000"
            required
            placeholder="دلیل رد این مرحله را وارد کنید..."
        />

        <div class="reject-form__actions">
          <AppButton
              type="button"
              variant="secondary"
              :disabled="loading"
              @click="closeReject"
          >
            انصراف
          </AppButton>

          <AppButton
              type="submit"
              variant="primary"
              :loading="loading"
          >
            رد مرحله
          </AppButton>
        </div>
      </form>
    </AppModal>
  </div>
</template>

<style scoped>
.kyc-detail {
  display: grid;
  gap: var(--space-5);
}

.detail-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-4);
  padding-bottom: var(--space-4);
  border-bottom: 1px solid var(--color-border-soft);
}

.detail-header__top {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--space-3);
}

.detail-header h2 {
  margin: 0;
  font-size: var(--font-size-xl);
}

.detail-header p {
  margin: .25rem 0 0;
  color: var(--color-text-muted);
  direction: ltr;
}

.detail-error {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-3);
  border-radius: var(--radius-md);
  background: var(--color-danger-soft);
  color: var(--color-danger);
}

.detail-error span {
  flex: 1;
}

.detail-error button {
  display: grid;
  padding: .25rem;
  border: 0;
  background: transparent;
  color: inherit;
  cursor: pointer;
}

.review-grid {
  display: grid;
  grid-template-columns: repeat(
    2,
    minmax(0, 1fr)
  );
  gap: var(--space-5);
}

.review-card {
  display: grid;
  gap: var(--space-5);
}

.bank-review-card {
  grid-column: 1 / -1;
}

.review-card__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-3);
  padding-bottom: var(--space-4);
  border-bottom: 1px solid var(--color-border-soft);
}

.review-card__header > div {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.review-card__icon {
  display: grid;
  width: 2.7rem;
  height: 2.7rem;
  border-radius: .85rem;
  background: var(--color-primary-soft);
  color: var(--color-primary);
  place-items: center;
}

.review-card h3 {
  margin: 0;
}

.review-card__header p {
  margin: .15rem 0 0;
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
}

.review-fields {
  display: grid;
  grid-template-columns: repeat(
    2,
    minmax(0, 1fr)
  );
  gap: var(--space-4);
}

.review-fields > div {
  display: grid;
  gap: .2rem;
}

.review-fields .full {
  grid-column: 1 / -1;
}

.review-fields span {
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
}

.review-fields strong {
  color: var(--color-text-primary);
  font-size: var(--font-size-sm);
  line-height: 1.7;
}

.rejection {
  padding: var(--space-3);
  border-radius: var(--radius-md);
  background: var(--color-danger-soft);
}

.document-link {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  color: var(--color-primary);
  font-size: var(--font-size-sm);
  font-weight: 700;
}

.review-actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-3);
}

.review-result {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-3);
  border-radius: var(--radius-md);
  font-size: var(--font-size-sm);
  font-weight: 700;
}

.review-result.approved {
  background: var(--color-success-soft);
  color: var(--color-success);
}

.rejected-result {
  background: var(--color-danger-soft);
  color: var(--color-danger);
}

.reject-form {
  display: grid;
  gap: var(--space-4);
}

.reject-form label {
  font-size: var(--font-size-sm);
  font-weight: 700;
}

.reject-form textarea {
  width: 100%;
  min-height: 9rem;
  padding: var(--space-3);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface-input);
  color: var(--color-text-primary);
  resize: vertical;
}

.reject-form textarea:focus {
  outline: none;
  border-color: var(--color-border-focus);
  box-shadow: var(--shadow-focus);
}

.reject-form__actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-3);
}

.bank-count {
  padding: .35rem .65rem;
  border-radius: 999px;
  background: var(--color-surface-2);
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
  font-weight: 700;
}

.bank-list {
  display: grid;
  gap: var(--space-4);
}

.bank-account {
  display: grid;
  gap: var(--space-5);
  padding: var(--space-4);
  border: 1px solid var(--color-border-soft);
  border-radius: var(--radius-lg);
  background: var(--color-surface-2);
}

.bank-account__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-4);
}

.bank-account__header > div {
  display: grid;
  gap: .2rem;
}

.bank-account__header strong {
  color: var(--color-text-primary);
  font-size: var(--font-size-md);
}

.bank-account__header span {
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
}

.bank-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-3);
  min-height: 10rem;
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
}

.match-success {
  color: var(--color-success) !important;
}

.match-danger {
  color: var(--color-danger) !important;
}

@media (max-width: 900px) {
  .review-grid {
    grid-template-columns: 1fr;
  }

  .bank-review-card {
    grid-column: auto;
  }
}

@media (max-width: 560px) {
  .review-fields {
    grid-template-columns: 1fr;
  }

  .review-fields .full {
    grid-column: auto;
  }

  .review-actions,
  .reject-form__actions {
    flex-direction: column;
  }

  .bank-account__header {
    flex-direction: column;
  }
}
</style>