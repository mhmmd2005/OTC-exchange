<script setup lang="ts">
import {computed, nextTick, reactive, ref, watch} from 'vue'
import {useRouter} from 'vue-router'

import {useAuthStore} from '@/stores/auth'
import {ApiError, verificationService} from '@/services'

import type {BasicIdentityInput, UserProfile, VerificationStep,} from '@/types'

import {normalizeDigits} from '@/utils/formatters'
import {persianDateBoundaryIso} from '@/utils/persianDateInput'

import AppButton from '@/components/ui/AppButton.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import AppInput from '@/components/ui/AppInput.vue'

const MAX_FILE_BYTES = 5 * 1024 * 1024
const IDENTITY_FILE_TYPES = [
  'image/jpeg',
  'image/png',
  'application/pdf',
] as const

const props = withDefaults(defineProps<{
  step: VerificationStep
  profile: UserProfile | null
  basicInfo?: BasicIdentityInput | null
  allowCancel?: boolean
}>(), {
  basicInfo: null,
  allowCancel: false,
})

const emit = defineEmits<{
  submitted: [message: string]
  cancel: []
}>()

const router = useRouter()
const auth = useAuthStore()

const submitting = ref(false)
const formElement = ref<HTMLFormElement | null>(null)
const formError = ref('')
const selectedFrontFile = ref<File | null>(null)
const selectedBackFile = ref<File | null>(null)

const selectedFrontFileName = ref('')
const selectedBackFileName = ref('')

const identityUploadExpanded = ref(false)
const basicForm = reactive<BasicIdentityInput>({
  firstName: '',
  lastName: '',
  fatherName: '',
  nationalId: '',
  birthDate: '',
})
const basicErrors = reactive<Record<string, string>>({})

const isWaiting = computed(() => props.step.status === 'pending')

const isIdentityApproved = computed(
    () =>
        props.step.id === 'identity'
        && props.step.status === 'verified',
)
const isIdentityReady = computed(
    () =>
        Boolean(
            selectedFrontFile.value
            && selectedBackFile.value,
        ),
)
const primaryLabel = computed(() => ({
  mobile: 'دریافت کد تأیید',
  basic_info: 'ثبت اطلاعات و ادامه',
  identity: 'ارسال مدرک برای بررسی',
  bank: 'افزودن حساب بانکی',
}[props.step.id]))

const primaryIcon = computed(() => ({
  mobile: 'phone',
  basic_info: 'arrowLeft',
  identity: 'upload',
  bank: 'bank',
}[props.step.id]))

function isoToPersianDate(value: string): string {
  if (!value) return ''

  const date = new Date(`${value}T00:00:00Z`)
  if (Number.isNaN(date.getTime())) return ''

  const parts = new Intl.DateTimeFormat(
      'fa-IR-u-ca-persian',
      {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        timeZone: 'UTC',
      },
  ).formatToParts(date)

  const year = parts.find((item) => item.type === 'year')?.value || ''
  const month = parts.find((item) => item.type === 'month')?.value || ''
  const day = parts.find((item) => item.type === 'day')?.value || ''

  return `${year}/${month}/${day}`
}

function reset(): void {
  formError.value = ''
  selectedFrontFile.value = null
  selectedBackFile.value = null

  selectedFrontFileName.value = ''
  selectedBackFileName.value = ''

  identityUploadExpanded.value = false

  Object.keys(basicErrors).forEach(
      (key) => delete basicErrors[key],
  )

  Object.assign(basicForm, {
    firstName: props.basicInfo?.firstName || '',
    lastName: props.basicInfo?.lastName || '',
    fatherName: props.basicInfo?.fatherName || '',
    nationalId: props.basicInfo?.nationalId || '',
    birthDate: props.basicInfo?.birthDate
        ? isoToPersianDate(props.basicInfo.birthDate)
        : '',
  })
}

watch(
    () => [
      props.step.id,
      props.step.status,
      props.basicInfo,
    ] as const,
    reset,
    {
      immediate: true,
      deep: true,
    },
)

function validateBasic(): boolean {
  Object.keys(basicErrors).forEach(
      (key) => delete basicErrors[key],
  )

  if (!basicForm.firstName.trim()) {
    basicErrors.firstName = 'نام را وارد کنید.'
  }

  if (!basicForm.lastName.trim()) {
    basicErrors.lastName = 'نام خانوادگی را وارد کنید.'
  }
  if (!basicForm.fatherName.trim()) {
    basicErrors.fatherName = 'نام پدر را وارد کنید.'
  }
  const nationalId = normalizeDigits(
      basicForm.nationalId,
  )

  if (!/^\d{10}$/.test(nationalId)) {
    basicErrors.nationalId = 'کد ملی باید ۱۰ رقم باشد.'
  }

  if (!basicForm.birthDate.trim()) {
    basicErrors.birthDate = 'تاریخ تولد را وارد کنید.'
  } else if (
      !persianDateBoundaryIso(
          basicForm.birthDate,
          'start',
      )
  ) {
    basicErrors.birthDate =
        'تاریخ تولد معتبر را مانند ۱۳۷۲/۰۸/۱۹ وارد کنید.'
  }

  const firstInvalid = [
    'firstName',
    'lastName',
    'fatherName',
    'nationalId',
    'birthDate',
  ].find((key) => basicErrors[key])

  if (firstInvalid) {
    void nextTick(() => {
      formElement.value
          ?.querySelector<HTMLInputElement>(
              `[name="${firstInvalid}"]`,
          )
          ?.focus()
    })
  }

  return Object.keys(basicErrors).length === 0
}

function fileValidationError(file: File): string {
  if (
      !IDENTITY_FILE_TYPES.includes(
          file.type as typeof IDENTITY_FILE_TYPES[number],
      )
  ) {
    return 'فرمت مدرک باید JPG، PNG یا PDF باشد.'
  }

  if (!file.size) {
    return 'فایل انتخاب‌شده خالی است.'
  }

  if (file.size > MAX_FILE_BYTES) {
    return 'حجم مدرک نباید بیشتر از ۵ مگابایت باشد.'
  }

  return ''
}

function onFileSelected(
    event: Event,
    side: 'front' | 'back',
): void {
  const input = event.target as HTMLInputElement

  formError.value = ''

  const file = input.files?.[0]

  if (!file) {
    if (side === 'front') {
      selectedFrontFile.value = null
      selectedFrontFileName.value = ''
    } else {
      selectedBackFile.value = null
      selectedBackFileName.value = ''
    }

    return
  }

  const error = fileValidationError(file)

  if (error) {
    if (side === 'front') {
      selectedFrontFile.value = null
      selectedFrontFileName.value = ''
    } else {
      selectedBackFile.value = null
      selectedBackFileName.value = ''
    }

    formError.value = error
    input.value = ''

    return
  }

  if (side === 'front') {
    selectedFrontFile.value = file
    selectedFrontFileName.value = file.name
  } else {
    selectedBackFile.value = file
    selectedBackFileName.value = file.name
  }
}

function readableError(
    caught: unknown,
    fallback: string,
): string {
  return caught instanceof Error
      ? caught.message
      : fallback
}

async function submit(): Promise<void> {
  if (
      isWaiting.value
      || props.step.locked
      || submitting.value
  ) {
    return
  }

  formError.value = ''

  if (props.step.id === 'bank') {
    await router.push(
        props.step.actionRoute || '/app/bank-accounts',
    )
    return
  }

  submitting.value = true

  try {
    if (props.step.id === 'mobile') {
      if (!props.profile?.mobile) {
        throw new Error(
            'شماره موبایل حساب در دسترس نیست.',
        )
      }

      await auth.requestOtp({
        mobile: props.profile.mobile,
        purpose: 'phone_verification',
      })

      await router.push({
        name: 'verify',
        query: {
          purpose: 'phone_verification',
          context: 'kyc',
          returnTo: '/app/verification',
        },
      })

      return
    }

    if (props.step.id === 'basic_info') {
      if (!validateBasic()) return

      const result =
          await verificationService.submitBasicInfo({
            firstName: basicForm.firstName.trim(),
            lastName: basicForm.lastName.trim(),
            fatherName: basicForm.fatherName.trim(),
            nationalId: normalizeDigits(
                basicForm.nationalId,
            ),
            birthDate: basicForm.birthDate.trim(),
          })

      emit(
          'submitted',
          result.message
          || 'اطلاعات هویتی با موفقیت ثبت شد.',
      )

      return
    }

    if (props.step.id === 'identity') {
      if (
          !selectedFrontFile.value
          || !selectedBackFile.value
      ) {
        identityUploadExpanded.value = true

        formError.value =
            'تصویر روی کارت و پشت کارت را انتخاب کنید.'

        return
      }

      const frontError = fileValidationError(
          selectedFrontFile.value,
      )

      if (frontError) {
        formError.value = frontError
        return
      }

      const backError = fileValidationError(
          selectedBackFile.value,
      )

      if (backError) {
        formError.value = backError
        return
      }

      const result =
          await verificationService.submitIdentityDocument(
              selectedFrontFile.value,
              selectedBackFile.value,
          )

      emit(
          'submitted',
          result.message
          || 'اطلاعات شما برای بررسی ادمین ارسال شد.',
      )
    }
  } catch (caught) {
    if (
        caught instanceof ApiError
        && caught.details?.fields
    ) {
      Object.assign(
          basicErrors,
          caught.details.fields,
      )
    }

    formError.value = readableError(
        caught,
        'ارسال اطلاعات انجام نشد.',
    )
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <form
      ref="formElement"
      class="verification-step-form"
      novalidate
      @submit.prevent="submit"
  >
    <div
        v-if="step.rejectionReason"
        class="step-message step-message--warning"
    >
      <AppIcon name="warning" :size="19"/>
      <span>
        <strong>نیاز به اصلاح</strong>
        {{ step.rejectionReason }}
      </span>
    </div>

    <div
        v-if="isWaiting"
        class="step-message step-message--pending"
        role="status"
    >
      <AppIcon name="clock" :size="21"/>
      <span>
        <strong>اطلاعات در حال بررسی است</strong>
        نتیجه بررسی در حساب شما اعلام می‌شود.
      </span>
    </div>

    <div
        v-if="formError"
        class="step-message step-message--danger"
        role="alert"
    >
      {{ formError }}
    </div>

    <template
        v-if="!isWaiting && step.id === 'mobile'"
    >
      <div class="step-intro">
        <span><AppIcon name="phone" :size="28"/></span>
        <div>
          <strong>تأیید مالکیت شماره موبایل</strong>
          <p>کد یک‌بارمصرف به شماره ثبت‌شده حساب ارسال می‌شود.</p>
        </div>
      </div>

      <div class="readonly-value">
        <span>شماره موبایل</span>
        <bdi dir="ltr">{{ profile?.mobile || '—' }}</bdi>
      </div>
    </template>

    <template
        v-else-if="!isWaiting && step.id === 'basic_info'"
    >
      <div class="form-grid">
        <AppInput
            v-model="basicForm.firstName"
            name="firstName"
            label="نام"
            autocomplete="given-name"
            required
            maxlength="64"
            :error="basicErrors.firstName"
        />

        <AppInput
            v-model="basicForm.lastName"
            name="lastName"
            label="نام خانوادگی"
            autocomplete="family-name"
            required
            maxlength="96"
            :error="basicErrors.lastName"
        />

        <AppInput
            v-model="basicForm.fatherName"
            name="fatherName"
            label="نام پدر"
            autocomplete="additional-name"
            required
            maxlength="96"
            :error="basicErrors.fatherName"
        />
      </div>

      <AppInput
          v-model="basicForm.nationalId"
          name="nationalId"
          label="کد ملی"
          inputmode="numeric"
          autocomplete="off"
          required
          maxlength="10"
          ltr
          :error="basicErrors.nationalId"
      />

      <AppInput
          v-model="basicForm.birthDate"
          name="birthDate"
          label="تاریخ تولد"
          placeholder="۱۳۷۲/۰۸/۱۹"
          inputmode="numeric"
          autocomplete="bday"
          required
          maxlength="10"
          ltr
          :error="basicErrors.birthDate"
      />
    </template>

    <template
        v-else-if="isIdentityApproved"
    >
      <div class="step-message step-message--success" role="status">
        <AppIcon name="check" :size="21"/>
        <span>
          <strong>مدرک شناسایی تأیید شد</strong>
          مدرک شما توسط کارشناسان بررسی و تأیید شده است.
        </span>
      </div>
    </template>

    <template
        v-else-if="!isWaiting && step.id === 'identity'"
    >
      <div class="step-intro">
        <span>
            <AppIcon
                name="verify"
                :size="30"
            />
        </span>

        <div>
          <strong>مدرک شناسایی</strong>

          <p>
            تصویر واضح کارت ملی خود را ارسال کنید.
            نور کافی باشد، تمام بخش‌های کارت دیده شوند
            و تصویر تار یا بریده نباشد.
          </p>
        </div>
      </div>

      <button
          v-if="!identityUploadExpanded"
          type="button"
          class="file-drop identity-upload-trigger"
          @click="identityUploadExpanded = true"
      >
        <AppIcon
            name="upload"
            :size="24"
        />

        <span>
            <strong>
                انتخاب مدرک شناسایی
            </strong>

            <small>
                روی کارت و پشت کارت را بارگذاری کنید
            </small>
        </span>

        <AppIcon
            name="chevronLeft"
            :size="18"
        />
      </button>

      <div
          v-else
          class="identity-sides"
      >
        <label
            class="file-drop"
            :class="{
                selected: selectedFrontFile,
            }"
        >
          <input
              type="file"
              accept="image/jpeg,image/png,application/pdf"
              @change="
                    onFileSelected($event, 'front')
                "
          />

          <AppIcon
              :name="
                    selectedFrontFile
                        ? 'check'
                        : 'upload'
                "
              :size="24"
          />

          <span>
                <strong>
                    {{
                    selectedFrontFileName
                    || 'روی کارت'
                  }}
                </strong>

                <small>
                    {{
                    selectedFrontFile
                        ? 'فایل روی کارت آماده است'
                        : 'تصویر روی کارت را انتخاب کنید'
                  }}
                </small>
            </span>
        </label>

        <label
            class="file-drop"
            :class="{
                selected: selectedBackFile,
            }"
        >
          <input
              type="file"
              accept="image/jpeg,image/png,application/pdf"
              @change="
                    onFileSelected($event, 'back')
                "
          />

          <AppIcon
              :name="
                    selectedBackFile
                        ? 'check'
                        : 'upload'
                "
              :size="24"
          />

          <span>
                <strong>
                    {{
                    selectedBackFileName
                    || 'پشت کارت'
                  }}
                </strong>

                <small>
                    {{
                    selectedBackFile
                        ? 'فایل پشت کارت آماده است'
                        : 'تصویر پشت کارت را انتخاب کنید'
                  }}
                </small>
            </span>
        </label>
      </div>
    </template>

    <template
        v-else-if="!isWaiting && step.id === 'bank'"
    >
      <div class="step-intro">
        <span><AppIcon name="bank" :size="30"/></span>
        <div>
          <strong>حساب بانکی به نام خودتان</strong>
          <p>برای واریز و برداشت تومان، حداقل یک حساب بانکی تأییدشده لازم است.</p>
        </div>
      </div>
    </template>

    <div class="privacy-note">
      <AppIcon name="lock" :size="17"/>
      اطلاعات شما فقط برای احراز هویت و حفاظت از حساب استفاده می‌شود.
    </div>

    <div
        v-if="!isWaiting && !isIdentityApproved"
        class="form-actions"
    >
      <AppButton
          type="submit"
          block
          size="lg"
          :icon="primaryIcon"
          :loading="submitting"
          :disabled="
    step.locked
    || (
        step.id === 'identity'
        && !isIdentityReady
    )
"
      >
        {{ primaryLabel }}
      </AppButton>

      <AppButton
          v-if="allowCancel"
          type="button"
          variant="secondary"
          :disabled="submitting"
          @click="emit('cancel')"
      >
        انصراف
      </AppButton>
    </div>
  </form>
</template>

<style scoped>
.verification-step-form {
  display: grid;
  gap: var(--space-4)
}

.form-grid {
  display: grid;
  grid-template-columns:repeat(2, minmax(0, 1fr));
  gap: var(--space-3)
}

.step-message {
  display: flex;
  align-items: flex-start;
  gap: var(--space-2);
  padding: var(--space-3);
  border-radius: var(--radius-md);
  font-size: var(--font-size-sm)
}

.step-message span {
  display: grid;
  gap: .15rem;
  color: var(--color-text-secondary)
}

.step-message--warning, .step-message--pending {
  background: var(--color-warning-soft);
  color: var(--color-warning)
}

.step-message--danger {
  background: var(--color-danger-soft);
  color: var(--color-danger)
}

.step-message--success {
  background: var(--color-success-soft);
  color: var(--color-success);
}

.step-intro {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  padding: var(--space-4);
  border-radius: var(--radius-md);
  background: var(--color-surface-2)
}

.step-intro > span {
  display: grid;
  width: 3.5rem;
  height: 3.5rem;
  flex: 0 0 auto;
  border-radius: 1rem;
  background: var(--color-primary-soft);
  color: var(--color-primary);
  place-items: center
}

.step-intro p {
  margin: .15rem 0 0;
  color: var(--color-text-muted);
  font-size: var(--font-size-xs)
}

.readonly-value {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  min-height: 3.25rem;
  padding: var(--space-3) var(--space-4);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface-input)
}

.readonly-value span {
  color: var(--color-text-muted);
  font-size: var(--font-size-sm)
}

.readonly-value bdi {
  color: var(--color-text-primary);
  font-weight: 700
}

.identity-upload-trigger {
  width: 100%;
  border: 1px dashed var(--color-border-hover);
  text-align: right;
  font: inherit;
}

.identity-upload-trigger > span {
  flex: 1;
}

.identity-upload-trigger > span {
  display: grid;
  gap: .15rem;
  min-width: 0;
}

.identity-upload-trigger > span strong {
  color: var(--color-text-primary);
}

.identity-upload-trigger > span small {
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
}

.identity-upload-trigger:hover {
  border-color: var(--color-border-focus);
  background: var(--color-surface-2);
}

.identity-sides {
  display: grid;
  grid-template-columns: repeat(
        2,
        minmax(0, 1fr)
    );
  gap: var(--space-3);
}

.identity-sides .file-drop {
  min-height: 7rem;
}

@media (max-width: 560px) {
  .identity-sides {
    grid-template-columns: minmax(0, 1fr);
  }
}

.file-drop {
  position: relative;
  display: flex;
  align-items: center;
  gap: var(--space-3);
  min-height: 6rem;
  padding: var(--space-4);
  border: 1px dashed var(--color-border-hover);
  border-radius: var(--radius-md);
  background: var(--color-surface-2);
  color: var(--color-primary);
  cursor: pointer
}

.file-drop.selected {
  border-color: var(--color-success);
  color: var(--color-success)
}

.file-drop:focus-within {
  border-color: var(--color-border-focus);
  box-shadow: var(--shadow-focus)
}

.file-drop input {
  position: absolute;
  width: 1px;
  height: 1px;
  opacity: 0
}

.file-drop span {
  display: grid;
  min-width: 0;
  color: var(--color-text-primary)
}

.file-drop strong {
  overflow: hidden;
  text-overflow: ellipsis
}

.file-drop small {
  color: var(--color-text-muted);
  font-size: var(--font-size-xs)
}

.privacy-note {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  color: var(--color-text-muted);
  font-size: var(--font-size-xs)
}

.form-actions {
  display: grid;
  grid-template-columns:minmax(0, 1fr) auto;
  align-items: center;
  gap: var(--space-3)
}

@media (max-width: 520px) {
  .form-grid {
    grid-template-columns:minmax(0, 1fr)
  }

  .step-intro {
    align-items: flex-start
  }

  .form-actions {
    grid-template-columns:minmax(0, 1fr)
  }
}
</style>