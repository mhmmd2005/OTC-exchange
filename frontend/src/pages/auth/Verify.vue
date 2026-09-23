<script setup lang="ts">
import {
  computed,
  defineAsyncComponent,
  ref,
  watch,
} from 'vue'
import {
  RouterLink,
  useRoute,
  useRouter,
} from 'vue-router'
import {useAuthStore} from '@/stores/auth'
import AppButton from '@/components/ui/AppButton.vue'
import AppCard from '@/components/ui/AppCard.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import AppInput from '@/components/ui/AppInput.vue'
import OtpInput from '@/components/ui/OtpInput.vue'
import type {OtpPurpose} from '@/types'
import {
  maskMobile,
  queryValue,
  safeAppRedirect,
} from './auth.utils'
import {normalizeDigits} from '@/utils/formatters'

const DemoCodeHint =
    import.meta.env.DEV
    && import.meta.env.VITE_USE_MOCK_API === 'true'
        ? defineAsyncComponent(
            () =>
                import(
                    '@/components/ui/DemoCodeHint.vue'
                ),
        )
        : null

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const code = ref('')
const loading = ref(false)
const resendLoading = ref(false)
const otpError = ref('')
const resendMessage = ref('')

const purpose = computed<OtpPurpose>(() => {
  const requested =
      queryValue(
          route.query.purpose,
      )

  if (
      requested === 'login'
      || requested === 'register'
      || requested === 'reset_password'
      || requested === 'phone_verification'
      || requested === 'withdrawal'
  ) {
    return requested
  }

  return 'register'
})

const isTwoFactorStep = computed(
    () =>
        purpose.value === 'login'
        && queryValue(
            route.query.stage,
        ) === 'two_factor',
)

const activeChallenge = computed(() => {
  const challenge =
      auth.otpChallenge

  return challenge?.purpose
      === purpose.value
      ? challenge
      : null
})

const twoFactorChallenge = computed(
    () =>
        auth.twoFactorLoginChallenge,
)

const mobile = computed(
    () =>
        activeChallenge
            .value?.mobile
        ?? '',
)

const isPasswordReset = computed(
    () =>
        purpose.value
        === 'reset_password',
)

const isAccountVerification = computed(
    () =>
        queryValue(
            route.query.context,
        ) === 'kyc',
)

const returnTo = computed(() =>
    safeAppRedirect(
        route.query.returnTo,
        isAccountVerification.value
            ? '/app/verification'
            : '/app/dashboard?welcome=1',
    ),
)

const maskedMobile = computed(
    () =>
        maskMobile(
            mobile.value,
        ),
)

const editRoute = computed(() => {
  if (isTwoFactorStep.value) {
    return '/auth/login'
  }

  if (isPasswordReset.value) {
    return '/auth/forgot-password'
  }

  if (isAccountVerification.value) {
    return '/app/verification'
  }

  if (purpose.value === 'login') {
    return '/auth/login'
  }

  return '/auth/register'
})

const backLabel = computed(() => {
  if (isTwoFactorStep.value) {
    return 'بازگشت به ورود'
  }

  if (isPasswordReset.value) {
    return 'بازگشت به بازیابی رمز عبور'
  }

  if (isAccountVerification.value) {
    return 'بازگشت به احراز هویت'
  }

  if (purpose.value === 'login') {
    return 'بازگشت به ورود'
  }

  return 'بازگشت به ثبت‌نام'
})

const challengeMissing = computed(
    () => {
      if (isTwoFactorStep.value) {
        return !twoFactorChallenge.value
      }

      return !activeChallenge.value
    },
)

const pageKicker = computed(
    () =>
        isTwoFactorStep.value
            ? 'ورود دومرحله‌ای'
            : 'تأیید شماره موبایل',
)

const pageTitle = computed(
    () =>
        isTwoFactorStep.value
            ? 'کد Authenticator را وارد کنید'
            : 'کد پیامک‌شده را وارد کنید',
)

const pageDescription = computed(() => {
  if (isTwoFactorStep.value) {
    return twoFactorChallenge.value
        ? 'برای تکمیل ورود، کد ۶ رقمی فعلی برنامه Authenticator را وارد کنید.'
        : 'درخواست ورود دومرحله‌ای در این مرورگر در دسترس نیست.'
  }

  if (!challengeMissing.value) {
    return `یک کد ۶ رقمی به ${maskedMobile.value} فرستادیم.`
  }

  return 'درخواست قبلی در این مرورگر در دسترس نیست.'
})

const submitLabel = computed(() => {
  if (isTwoFactorStep.value) {
    return 'تأیید و ورود'
  }

  if (isPasswordReset.value) {
    return 'تأیید و ادامه'
  }

  if (isAccountVerification.value) {
    return 'تأیید و بازگشت به احراز هویت'
  }

  return 'تأیید و ورود به پنل'
})

const securityNote = computed(() =>
    isTwoFactorStep.value
        ? 'کد Authenticator شخصی است و هرگز آن را در اختیار دیگران قرار ندهید.'
        : 'این کد شخصی است. کارشناسان روشا هرگز آن را از شما درخواست نمی‌کنند.',
)

watch(
    code,
    () => {
      otpError.value = ''
      resendMessage.value = ''
    },
)

function updateTwoFactorCode(
    value: string,
): void {
  code.value =
      normalizeDigits(
          value,
      )
          .replace(/\D/g, '')
          .slice(0, 6)

  otpError.value = ''
}

async function verifyCode(): Promise<void> {
  if (loading.value) return

  if (isTwoFactorStep.value) {
    if (!twoFactorChallenge.value) {
      otpError.value =
          'درخواست ورود دومرحله‌ای در دسترس نیست؛ دوباره وارد شوید.'
      return
    }

    if (code.value.length !== 6) {
      otpError.value =
          'کد Authenticator باید ۶ رقم باشد.'
      return
    }

    loading.value = true
    otpError.value = ''

    try {
      await auth.verifyTwoFactorLogin(
          normalizeDigits(
              code.value,
          ).replace(/\D/g, ''),
      )

      await router.push(
          returnTo.value,
      )
    } catch (error) {
      otpError.value =
          error instanceof Error
              ? error.message
              : 'بررسی کد Authenticator انجام نشد. لطفاً دوباره تلاش کنید.'
    } finally {
      loading.value = false
    }

    return
  }

  if (!activeChallenge.value) {
    otpError.value =
        'درخواست کد در دسترس نیست یا منقضی شده است؛ دوباره کد بگیرید.'
    return
  }

  if (code.value.length !== 6) {
    otpError.value =
        'کد تأیید باید ۶ رقم باشد.'
    return
  }

  loading.value = true
  otpError.value = ''

  try {
    if (isPasswordReset.value) {
      await auth.verifyPasswordResetOtp({
        challengeId:
            activeChallenge.value
                .challengeId,
        mobile:
            mobile.value,
        purpose:
            'reset_password',
        code:
            code.value,
      })

      await router.push(
          '/auth/reset-password',
      )

      return
    }

    const result =
        await auth.verifyOtp({
          challengeId:
              activeChallenge.value
                  .challengeId,
          mobile:
              mobile.value,
          purpose:
              purpose.value,
          code:
              code.value,
        })

    if (
        purpose.value === 'login'
        && 'twoFactorToken' in result
    ) {
      await router.push({
        path: '/auth/verify',
        query: {
          purpose: 'login',
          stage: 'two_factor',
          returnTo: returnTo.value,
        },
      })

      return
    }

    await router.push(
        returnTo.value,
    )
  } catch (error) {
    otpError.value =
        error instanceof Error
            ? error.message
            : 'بررسی کد انجام نشد. لطفاً دوباره تلاش کنید.'
  } finally {
    loading.value = false
  }
}

async function resendCode(): Promise<void> {
  if (isTwoFactorStep.value) {
    otpError.value =
        'برای ورود دومرحله‌ای نیازی به ارسال کد جدید نیست.'
    return
  }

  if (resendLoading.value) return

  if (!activeChallenge.value) {
    otpError.value =
        'برای ارسال کد، شماره موبایل را دوباره وارد کنید.'
    return
  }

  resendLoading.value = true
  otpError.value = ''
  resendMessage.value = ''

  try {
    await auth.requestOtp({
      mobile:
          mobile.value,
      purpose:
          purpose.value,
    })

    resendMessage.value =
        'کد جدید با موفقیت ارسال شد.'
  } catch (error) {
    otpError.value =
        error instanceof Error
            ? error.message
            : 'ارسال دوباره کد ممکن نشد. چند لحظه دیگر تلاش کنید.'
  } finally {
    resendLoading.value = false
  }
}

async function cancelTwoFactorLogin(): Promise<void> {
  auth.cancelTwoFactorLogin()

  await router.push({
    name: 'login',
    query: {
      redirect: returnTo.value,
    },
  })
}
</script>

<template>
  <AppCard
      padding="lg"
      class="auth-view verify-card"
  >
    <div
        class="verify-symbol"
        :class="{
          'verify-symbol--two-factor':
              isTwoFactorStep,
        }"
        aria-hidden="true"
    >
      <AppIcon
          :name="
            isTwoFactorStep
              ? 'shield'
              : 'phone'
          "
          :size="26"
      />

      <span>
        <AppIcon
            name="check"
            :size="13"
        />
      </span>
    </div>

    <div class="auth-intro verify-intro">
      <span class="auth-kicker">
        {{ pageKicker }}
      </span>

      <h1 class="auth-title">
        {{ pageTitle }}
      </h1>

      <p class="auth-description">
        <template v-if="isTwoFactorStep">
          <template v-if="twoFactorChallenge">
            {{ pageDescription }}
          </template>

          <template v-else>
            {{ pageDescription }}
          </template>
        </template>

        <template v-else>
          <template v-if="!challengeMissing">
            یک کد ۶ رقمی به
            <strong
                class="mobile-number"
                dir="ltr"
            >
              {{ maskedMobile }}
            </strong>
            فرستادیم.
          </template>

          <template v-else>
            {{ pageDescription }}
          </template>

          <RouterLink
              class="auth-link edit-number"
              :to="editRoute"
              v-if="!isTwoFactorStep"
          >
            {{
              challengeMissing
                  ? 'دریافت کد تازه'
                  : 'اصلاح شماره'
            }}
          </RouterLink>
        </template>
      </p>
    </div>

    <form
        class="auth-form"
        novalidate
        @submit.prevent="verifyCode"
    >
      <template v-if="isTwoFactorStep">
        <div class="two-factor-guide">
          <span>
            <AppIcon
                name="shield"
                :size="22"
            />
          </span>

          <div>
            <strong>
              تأیید ورود با Authenticator
            </strong>

            <p>
              کد ۶ رقمی فعلی برنامه
              Authenticator را وارد کنید.
            </p>
          </div>
        </div>

        <AppInput
            :model-value="code"
            label="کد ۶ رقمی Authenticator"
            inputmode="numeric"
            autocomplete="one-time-code"
            maxlength="6"
            ltr
            :error="otpError"
            placeholder="••••••"
            :disabled="challengeMissing"
            @update:model-value="
              updateTwoFactorCode
            "
        />

        <DemoCodeHint
            v-if="DemoCodeHint && !challengeMissing"
            context="two-factor"
        />
      </template>

      <template v-else>
        <OtpInput
            v-model="code"
            :loading="loading"
            :resend-loading="
              resendLoading
            "
            :error="otpError"
            :countdown-seconds="
              activeChallenge
                ? Math.max(
                    0,
                    Math.ceil(
                      (
                        Date.parse(
                          activeChallenge
                              .resendAt,
                        )
                        - Date.now()
                      ) / 1000,
                    ),
                  )
                : 0
            "
            :disabled="challengeMissing"
            @complete="verifyCode"
            @resend="resendCode"
        />

        <DemoCodeHint
            v-if="
              DemoCodeHint
              && !challengeMissing
            "
            context="otp"
        />

        <p
            v-if="resendMessage"
            class="resend-success"
            role="status"
        >
          <AppIcon
              name="check"
              :size="17"
          />

          {{ resendMessage }}
        </p>
      </template>

      <AppButton
          type="submit"
          size="lg"
          block
          :loading="loading"
          :disabled="
            challengeMissing
            || code.length !== 6
          "
      >
        {{ submitLabel }}
      </AppButton>

      <div class="auth-security-note">
        <AppIcon
            name="lock"
            :size="18"
        />

        <span>
          {{ securityNote }}
        </span>
      </div>
    </form>

    <p class="auth-footer">
      <button
          v-if="isTwoFactorStep"
          type="button"
          class="auth-link back-link"
          @click="cancelTwoFactorLogin"
      >
        <AppIcon
            name="chevronRight"
            :size="17"
        />

        {{ backLabel }}
      </button>

      <RouterLink
          v-else
          class="auth-link back-link"
          :to="editRoute"
      >
        <AppIcon
            name="chevronRight"
            :size="17"
        />

        {{ backLabel }}
      </RouterLink>
    </p>
  </AppCard>
</template>

<style scoped>
.verify-card {
  text-align: right;
}

.verify-symbol {
  position: relative;
  display: grid;
  width: 3.5rem;
  height: 3.5rem;
  margin-bottom: var(--space-5);
  border: 1px solid rgba(67, 139, 255, .22);
  border-radius: 1.1rem;
  background: var(--color-primary-soft);
  color: #83b4ff;
  place-items: center;
}

.verify-symbol--two-factor {
  border-color: rgba(53, 201, 149, .22);
  background: var(--color-success-soft);
  color: var(--color-success);
}

.verify-symbol > span {
  position: absolute;
  inset: auto auto -.25rem -.25rem;
  display: grid;
  width: 1.35rem;
  height: 1.35rem;
  border: 2px solid var(--color-surface-1);
  border-radius: 50%;
  background: var(--color-success);
  color: #061b14;
  place-items: center;
}

.verify-intro {
  margin-bottom: var(--space-6);
}

.mobile-number {
  display: inline-block;
  color: var(--color-text-secondary);
  font-variant-numeric: tabular-nums;
}

.edit-number {
  display: inline-block;
  margin-inline-start: var(--space-1);
  font-size: var(--font-size-xs);
}

.resend-success {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  margin: calc(var(--space-2) * -1) 0 0;
  color: var(--color-success);
  font-size: var(--font-size-xs);
}

.demo-hint {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  margin: calc(var(--space-1) * -1) 0 0;
  padding: var(--space-2);
  border-radius: var(--radius-sm);
  background: var(--color-info-soft);
  color: var(--color-info);
  font-size: var(--font-size-xs);
}

.two-factor-guide {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-4);
  border: 1px solid var(--color-border-soft);
  border-radius: var(--radius-md);
  background: var(--color-primary-soft);
}

.two-factor-guide > span {
  display: grid;
  width: 2.75rem;
  height: 2.75rem;
  flex: 0 0 auto;
  border-radius: .8rem;
  background: var(--color-surface-2);
  color: var(--color-primary);
  place-items: center;
}

.two-factor-guide > div {
  display: grid;
  min-width: 0;
  gap: var(--space-1);
}

.two-factor-guide strong {
  font-size: var(--font-size-sm);
}

.two-factor-guide p {
  margin: 0;
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
  line-height: 1.8;
}

.back-link {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  border: 0;
  padding: 0;
  background: transparent;
  cursor: pointer;
}

@media (max-width: 420px) {
  .two-factor-guide {
    align-items: flex-start;
  }
}
</style>