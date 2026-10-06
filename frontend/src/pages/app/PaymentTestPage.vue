<script setup lang="ts">
import {
  computed,
  onMounted,
  ref,
} from 'vue'
import {
  useRoute,
  useRouter,
} from 'vue-router'
import type { Transaction } from '@/types'
import { ApiError } from '@/services/api'
import { walletService } from '@/services/wallet.service'

const route = useRoute()
const router = useRouter()

const token = computed(() =>
  String(
    route.params.token || '',
  ),
)

const loading = ref(true)
const paying = ref(false)
const requestError = ref('')

const payment = ref<
  Awaited<
    ReturnType<
      typeof walletService.getTestTomanDeposit
    >
  > | null
>(null)

const transaction = ref<Transaction | null>(
  null,
)

const isSucceeded = computed(
  () =>
    payment.value?.status ===
      'succeeded'
    || Boolean(transaction.value),
)

const formattedAmount = computed(() => {
  const value = payment.value?.amount

  if (!value) {
    return '—'
  }

  return `${new Intl.NumberFormat(
    'fa-IR',
  ).format(
    Number(value),
  )} تومان`
})

const statusLabel = computed(() => {
  if (
    transaction.value
    || payment.value?.status === 'succeeded'
  ) {
    return 'پرداخت موفق'
  }

  if (
    payment.value?.status ===
    'verifying'
  ) {
    return 'در حال تأیید'
  }

  if (
    payment.value?.status ===
    'callback_received'
  ) {
    return 'در حال بررسی'
  }

  if (
    payment.value?.status ===
    'expired'
  ) {
    return 'منقضی شده'
  }

  if (
    payment.value?.status ===
    'failed'
  ) {
    return 'ناموفق'
  }

  return 'آماده پرداخت'
})

function errorMessage(
  error: unknown,
): string {
  if (
    error instanceof ApiError
  ) {
    return error.message
  }

  if (
    error instanceof Error
  ) {
    return error.message
  }

  return 'پرداخت انجام نشد. دوباره تلاش کنید.'
}

async function loadPayment(): Promise<void> {
  loading.value = true
  requestError.value = ''

  try {
    payment.value =
      await walletService.getTestTomanDeposit(
        token.value,
      )
  } catch (error) {
    requestError.value =
      errorMessage(error)
  } finally {
    loading.value = false
  }
}

async function startTestPayment(): Promise<void> {
  if (
    paying.value
    || isSucceeded.value
  ) {
    return
  }

  paying.value = true
  requestError.value = ''

  try {
    const result =
      await walletService.payTestTomanDeposit(
        token.value,
      )

    transaction.value = result

    if (payment.value) {
      payment.value = {
        ...payment.value,
        status: 'succeeded',
      }
    }
  } catch (error) {
    requestError.value =
      errorMessage(error)

    await loadPayment()
  } finally {
    paying.value = false
  }
}

function cancelPayment(): void {
  router.back()
}

function returnToDeposit(): void {
  router.push(
    '/app/deposit/toman',
  )
}

onMounted(() => {
  void loadPayment()
})
</script>

<template>
  <main class="payment-test-page">
    <section class="payment-card">
      <div
        class="payment-icon"
        :class="{
          'payment-icon--success':
            isSucceeded,
          'payment-icon--loading':
            loading,
        }"
        aria-hidden="true"
      >
        <span v-if="isSucceeded">
          ✓
        </span>

        <span v-else>
          $
        </span>
      </div>

      <div class="payment-header">
        <span class="payment-kicker">
          درگاه پرداخت آزمایشی روشا
        </span>

        <h1 class="payment-title">
          {{ isSucceeded
            ? 'پرداخت با موفقیت انجام شد'
            : 'پرداخت آزمایشی'
          }}
        </h1>

        <p class="payment-description">
          این صفحه رفتار درگاه پرداخت را در
          محیط توسعه شبیه‌سازی می‌کند.
        </p>
      </div>

      <div
        v-if="loading"
        class="loading-state"
      >
        در حال دریافت اطلاعات پرداخت...
      </div>

      <template v-else>
        <div
          v-if="requestError"
          class="notice notice--danger"
          role="alert"
        >
          {{ requestError }}
        </div>

        <div
          v-if="payment"
          class="payment-details"
        >
          <div class="detail-row">
            <span class="detail-label">
              مبلغ پرداخت
            </span>

            <strong class="detail-value">
              {{ formattedAmount }}
            </strong>
          </div>

          <div class="detail-row">
            <span class="detail-label">
              وضعیت
            </span>

            <strong
              class="detail-value status"
              :class="{
                'status--success':
                  isSucceeded,
              }"
            >
              {{ statusLabel }}
            </strong>
          </div>

          <div class="detail-row">
            <span class="detail-label">
              شناسه پرداخت
            </span>

            <strong
              class="detail-value ltr"
            >
              {{ token }}
            </strong>
          </div>

          <div
            v-if="transaction"
            class="detail-row"
          >
            <span class="detail-label">
              شماره تراکنش
            </span>

            <strong
              class="detail-value ltr"
            >
              {{
                transaction.referenceNumber
              }}
            </strong>
          </div>
        </div>

        <div
          v-if="!isSucceeded"
          class="actions"
        >
          <button
            type="button"
            class="primary-button"
            :disabled="paying"
            @click="startTestPayment"
          >
            <span
              v-if="paying"
            >
              در حال پردازش...
            </span>

            <span v-else>
              پرداخت آزمایشی
            </span>
          </button>

          <button
            type="button"
            class="secondary-button"
            :disabled="paying"
            @click="cancelPayment"
          >
            انصراف
          </button>
        </div>

        <div
          v-else
          class="actions"
        >
          <button
            type="button"
            class="primary-button"
            @click="returnToDeposit"
          >
            بازگشت به واریز تومان
          </button>
        </div>

        <div
          v-if="!isSucceeded"
          class="notice"
        >
          پرداخت موفق فقط پس از تأیید درگاه،
          Verify و تسویه حساب در بک‌اند باعث
          افزایش موجودی کیف پول می‌شود.
        </div>

        <div
          v-else
          class="notice notice--success"
        >
          مبلغ پرداخت‌شده در کیف پول تومان شما
          ثبت و تراکنش مالی آن ایجاد شد.
        </div>
      </template>
    </section>
  </main>
</template>

<style scoped>
.payment-test-page {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 32px 20px;
  background:
    radial-gradient(
      circle at top,
      rgba(42, 112, 190, 0.18),
      transparent 38%
    ),
    var(
      --color-background,
      #06111d
    );
  direction: rtl;
}

.payment-card {
  width: min(
    100%,
    560px
  );
  padding: 32px;
  border: 1px solid
    rgba(
      120,
      170,
      220,
      0.2
    );
  border-radius: 24px;
  background:
    rgba(
      10,
      28,
      45,
      0.95
    );
  box-shadow:
    0 24px 70px
    rgba(
      0,
      0,
      0,
      0.28
    );
}

.payment-icon {
  width: 72px;
  height: 72px;
  margin:
    0 auto
    20px;
  display: grid;
  place-items: center;
  border-radius: 22px;
  background:
    rgba(
      52,
      120,
      212,
      0.12
    );
  color: #6ba7ff;
  font-size: 30px;
  font-weight: 800;
}

.payment-icon--success {
  background:
    rgba(
      48,
      201,
      159,
      0.12
    );
  color: #35c995;
}

.payment-header {
  text-align: center;
}

.payment-kicker {
  display: inline-block;
  margin-bottom: 8px;
  color: #35c995;
  font-size: 14px;
  font-weight: 700;
}

.payment-title {
  margin: 0;
  color: #ffffff;
  font-size: 30px;
  font-weight: 800;
  line-height: 1.4;
}

.payment-description {
  margin:
    12px auto
    0;
  max-width: 420px;
  color: #8ea4bb;
  line-height: 1.9;
  font-size: 14px;
}

.loading-state {
  margin-top: 28px;
  padding: 20px;
  border-radius: 14px;
  background:
    rgba(
      60,
      110,
      170,
      0.1
    );
  color: #b9cce0;
  text-align: center;
}

.payment-details {
  margin-top: 28px;
  border-top: 1px solid
    rgba(
      140,
      170,
      200,
      0.12
    );
}

.detail-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;
  padding: 18px 0;
  border-bottom: 1px solid
    rgba(
      140,
      170,
      200,
      0.12
    );
}

.detail-label {
  color: #8097ad;
  white-space: nowrap;
}

.detail-value {
  color: #ffffff;
  text-align: left;
  word-break: break-all;
}

.detail-value.status {
  color: #e5ad3a;
  word-break: normal;
}

.detail-value.status--success {
  color: #35c995;
}

.ltr {
  direction: ltr;
}

.actions {
  display: grid;
  gap: 10px;
  margin-top: 26px;
}

.primary-button,
.secondary-button {
  width: 100%;
  min-height: 56px;
  border-radius: 14px;
  padding: 0 20px;
  font: inherit;
  font-weight: 700;
  cursor: pointer;
  transition:
    transform 0.2s ease,
    opacity 0.2s ease;
}

.primary-button:hover:not(:disabled),
.secondary-button:hover:not(:disabled) {
  transform: translateY(-1px);
}

.primary-button:disabled,
.secondary-button:disabled {
  cursor: not-allowed;
  opacity: 0.65;
}

.primary-button {
  border: 1px solid
    rgba(
      100,
      170,
      255,
      0.18
    );
  background: #3478d4;
  color: #ffffff;
}

.secondary-button {
  border: 1px solid
    rgba(
      110,
      160,
      210,
      0.35
    );
  background: transparent;
  color: #ffffff;
}

.notice {
  margin-top: 16px;
  padding: 14px 16px;
  border-radius: 12px;
  background:
    rgba(
      231,
      170,
      58,
      0.1
    );
  color: #e5ad3a;
  font-size: 13px;
  line-height: 1.8;
  text-align: center;
}

.notice--danger {
  background:
    rgba(
      240,
      108,
      117,
      0.1
    );
  color: #f06c75;
}

.notice--success {
  background:
    rgba(
      53,
      201,
      149,
      0.1
    );
  color: #35c995;
}

@media (max-width: 640px) {
  .payment-card {
    padding:
      24px
      18px;
    border-radius: 20px;
  }

  .payment-title {
    font-size: 25px;
  }

  .detail-row {
    flex-direction: column;
    gap: 8px;
  }

  .detail-value {
    text-align: right;
  }
}
</style>