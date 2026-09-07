<script setup lang="ts">
import { computed, nextTick, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ApiError, verificationService } from '@/services'
import type { BasicIdentityInput, UserProfile, VerificationStep } from '@/types'
import { normalizeDigits } from '@/utils/formatters'
import { persianDateBoundaryIso } from '@/utils/persianDateInput'
import AppButton from '@/components/ui/AppButton.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import AppInput from '@/components/ui/AppInput.vue'

const MAX_FILE_BYTES = 5 * 1024 * 1024
const IMAGE_FILE_TYPES = ['image/jpeg', 'image/png'] as const
const IDENTITY_FILE_TYPES = [...IMAGE_FILE_TYPES, 'application/pdf'] as const

const props = withDefaults(defineProps<{
  step: VerificationStep
  profile: UserProfile | null
  allowCancel?: boolean
}>(), {
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
const selectedFile = ref<File | null>(null)
const selectedFileName = ref('')
const basicForm = reactive<BasicIdentityInput>({ firstName: '', lastName: '', nationalId: '', birthDate: '' })
const basicErrors = reactive<Record<string, string>>({})

const isWaiting = computed(() => props.step.status === 'pending')
const acceptedFileTypes = computed(() => props.step.id === 'selfie'
  ? IMAGE_FILE_TYPES.join(',')
  : IDENTITY_FILE_TYPES.join(','))
const fileFormatHint = computed(() => props.step.id === 'selfie'
  ? 'JPG یا PNG؛ حداکثر ۵ مگابایت'
  : 'JPG، PNG یا PDF؛ حداکثر ۵ مگابایت')
const primaryLabel = computed(() => ({
  mobile: 'دریافت کد تأیید',
  basic_info: 'ثبت اطلاعات و ادامه',
  identity: 'ارسال مدرک برای بررسی',
  bank: 'افزودن حساب بانکی',
  selfie: 'ارسال تصویر برای بررسی',
}[props.step.id]))
const primaryIcon = computed(() => ({
  mobile: 'phone',
  basic_info: 'arrowLeft',
  identity: 'upload',
  bank: 'bank',
  selfie: 'upload',
}[props.step.id]))

function reset(): void {
  formError.value = ''
  selectedFile.value = null
  selectedFileName.value = ''
  Object.keys(basicErrors).forEach((key) => delete basicErrors[key])
  Object.assign(basicForm, {
    firstName: props.profile?.firstName || '',
    lastName: props.profile?.lastName || '',
    nationalId: props.profile?.nationalId || '',
    birthDate: props.profile?.birthDate || '',
  })
}

watch(() => [props.step.id, props.profile] as const, reset, { immediate: true })

function validateBasic(): boolean {
  Object.keys(basicErrors).forEach((key) => delete basicErrors[key])
  if (!basicForm.firstName.trim()) basicErrors.firstName = 'نام را وارد کنید.'
  if (!basicForm.lastName.trim()) basicErrors.lastName = 'نام خانوادگی را وارد کنید.'
  if (!/^\d{10}$/.test(normalizeDigits(basicForm.nationalId))) basicErrors.nationalId = 'کد ملی باید ۱۰ رقم باشد.'
  if (!basicForm.birthDate.trim()) basicErrors.birthDate = 'تاریخ تولد را وارد کنید.'
  else if (!persianDateBoundaryIso(basicForm.birthDate, 'start')) basicErrors.birthDate = 'تاریخ تولد معتبر را مانند ۱۳۷۲/۰۸/۱۹ وارد کنید.'
  const firstInvalid = ['firstName', 'lastName', 'nationalId', 'birthDate'].find((key) => basicErrors[key])
  if (firstInvalid) {
    void nextTick(() => formElement.value?.querySelector<HTMLInputElement>(`[name="${firstInvalid}"]`)?.focus())
  }
  return Object.keys(basicErrors).length === 0
}

function fileValidationError(file: File): string {
  const allowedTypes: readonly string[] = props.step.id === 'selfie' ? IMAGE_FILE_TYPES : IDENTITY_FILE_TYPES
  if (!allowedTypes.includes(file.type)) {
    return props.step.id === 'selfie'
      ? 'برای تصویر چهره فقط فایل JPG یا PNG انتخاب کنید.'
      : 'فرمت مدرک باید JPG، PNG یا PDF باشد.'
  }
  if (!file.size) return 'فایل انتخاب‌شده خالی است؛ فایل دیگری انتخاب کنید.'
  if (file.size > MAX_FILE_BYTES) return 'حجم فایل بیشتر از ۵ مگابایت است؛ فایل کوچک‌تری انتخاب کنید.'
  return ''
}

function onFileSelected(event: Event): void {
  const input = event.target as HTMLInputElement
  formError.value = ''
  const file = input.files?.[0]
  if (!file) {
    selectedFile.value = null
    selectedFileName.value = ''
    return
  }
  const validationError = fileValidationError(file)
  if (validationError) {
    selectedFile.value = null
    selectedFileName.value = ''
    formError.value = validationError
    input.value = ''
    return
  }
  selectedFile.value = file
  selectedFileName.value = file.name
}

function readableError(caught: unknown, fallback: string): string {
  return caught instanceof Error ? caught.message : fallback
}

async function submit(): Promise<void> {
  if (isWaiting.value || submitting.value) return
  formError.value = ''

  if (props.step.id === 'bank') {
    await router.push(props.step.actionRoute || '/app/bank-accounts')
    return
  }

  submitting.value = true
  try {
    if (props.step.id === 'mobile') {
      if (!props.profile?.mobile) throw new Error('شماره موبایل حساب در دسترس نیست؛ با پشتیبانی تماس بگیرید.')
      await auth.requestOtp({ mobile: props.profile.mobile, purpose: 'login' })
      await router.push({
        name: 'verify',
        query: { purpose: 'login', context: 'kyc', returnTo: '/app/verification' },
      })
      return
    }

    if (props.step.id === 'basic_info') {
      if (!validateBasic()) return
      await verificationService.submitBasicInfo({
        ...basicForm,
        nationalId: normalizeDigits(basicForm.nationalId),
      })
    } else {
      if (!selectedFile.value) {
        formError.value = props.step.id === 'selfie'
          ? 'یک تصویر واضح از چهره برای بررسی انتخاب کنید.'
          : 'تصویر مدرک یا فایل PDF آن را برای بررسی انتخاب کنید.'
        return
      }
      const validationError = fileValidationError(selectedFile.value)
      if (validationError) {
        formError.value = validationError
        return
      }
      const payload = new FormData()
      payload.append('document', selectedFile.value)
      await verificationService.submitStep(props.step.id, payload)
    }

    emit('submitted', `${props.step.title} برای بررسی ارسال شد. نتیجه از طریق اعلان به شما اطلاع داده می‌شود.`)
  } catch (caught) {
    if (caught instanceof ApiError && caught.details?.fields) Object.assign(basicErrors, caught.details.fields)
    formError.value = readableError(caught, 'ارسال اطلاعات انجام نشد.')
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <form ref="formElement" class="verification-step-form" novalidate @submit.prevent="submit">
    <div v-if="step.rejectionReason" class="step-message step-message--warning">
      <AppIcon name="warning" :size="19" />
      <span><strong>نیاز به اصلاح</strong>{{ step.rejectionReason }}</span>
    </div>

    <div v-if="isWaiting" class="step-message step-message--pending" role="status">
      <AppIcon name="clock" :size="21" />
      <span><strong>اطلاعات در حال بررسی است</strong>پس از پایان بررسی، نتیجه از طریق اعلان به شما اطلاع داده می‌شود.</span>
    </div>

    <div v-if="formError" class="step-message step-message--danger" role="alert">{{ formError }}</div>

    <template v-if="!isWaiting && step.id === 'mobile'">
      <div class="step-intro">
        <span><AppIcon name="phone" :size="28" /></span>
        <div><strong>تأیید مالکیت شماره موبایل</strong><p>کد یک‌بارمصرف به شماره ثبت‌شده حساب ارسال می‌شود.</p></div>
      </div>
      <div class="readonly-value"><span>شماره موبایل</span><bdi dir="ltr">{{ profile?.mobile || '—' }}</bdi></div>
    </template>

    <template v-else-if="!isWaiting && step.id === 'basic_info'">
      <div class="form-grid">
        <AppInput v-model="basicForm.firstName" name="firstName" label="نام" autocomplete="given-name" required maxlength="64" :error="basicErrors.firstName" />
        <AppInput v-model="basicForm.lastName" name="lastName" label="نام خانوادگی" autocomplete="family-name" required maxlength="96" :error="basicErrors.lastName" />
      </div>
      <AppInput v-model="basicForm.nationalId" name="nationalId" label="کد ملی" inputmode="numeric" autocomplete="off" required maxlength="10" ltr :error="basicErrors.nationalId" />
      <AppInput v-model="basicForm.birthDate" name="birthDate" label="تاریخ تولد" placeholder="۱۳۷۲/۰۸/۱۹" inputmode="numeric" autocomplete="bday" required maxlength="10" ltr :error="basicErrors.birthDate" />
    </template>

    <template v-else-if="!isWaiting && (step.id === 'identity' || step.id === 'selfie')">
      <div class="step-intro">
        <span><AppIcon :name="step.id === 'selfie' ? 'profile' : 'verify'" :size="30" /></span>
        <div>
          <strong>{{ step.id === 'selfie' ? 'تصویر واضح از چهره' : 'تصویر واضح مدرک شناسایی' }}</strong>
          <p>نور کافی باشد، همه گوشه‌ها دیده شوند و نوشته‌ها تار یا پوشیده نباشند.</p>
        </div>
      </div>
      <label class="file-drop" :class="{ selected: selectedFile }">
        <input
          type="file"
          :accept="acceptedFileTypes"
          :capture="step.id === 'selfie' ? 'user' : undefined"
          @change="onFileSelected"
        />
        <AppIcon :name="selectedFile ? 'check' : 'upload'" :size="24" />
        <span><strong>{{ selectedFileName || 'انتخاب تصویر' }}</strong><small>{{ selectedFile ? 'فایل آماده ارسال است' : fileFormatHint }}</small></span>
      </label>
    </template>

    <template v-else-if="!isWaiting && step.id === 'bank'">
      <div class="step-intro">
        <span><AppIcon name="bank" :size="30" /></span>
        <div><strong>حساب بانکی به نام خودتان</strong><p>برای واریز و برداشت تومان، حداقل یک حساب بانکی تأییدشده لازم است.</p></div>
      </div>
    </template>

    <div class="privacy-note"><AppIcon name="lock" :size="17" />اطلاعات شما فقط برای احراز هویت و حفاظت از حساب استفاده می‌شود.</div>

    <div v-if="!isWaiting" class="form-actions">
      <AppButton type="submit" block size="lg" :icon="primaryIcon" :loading="submitting">{{ primaryLabel }}</AppButton>
      <AppButton v-if="allowCancel" type="button" variant="secondary" :disabled="submitting" @click="emit('cancel')">انصراف</AppButton>
    </div>
  </form>
</template>

<style scoped>
.verification-step-form { display: grid; gap: var(--space-4); }
.form-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--space-3); }
.step-message { display: flex; align-items: flex-start; gap: var(--space-2); padding: var(--space-3); border-radius: var(--radius-md); font-size: var(--font-size-sm); }
.step-message span { display: grid; gap: .15rem; color: var(--color-text-secondary); }
.step-message strong { color: inherit; }
.step-message--warning,.step-message--pending { background: var(--color-warning-soft); color: var(--color-warning); }
.step-message--danger { background: var(--color-danger-soft); color: var(--color-danger); }
.step-intro { display: flex; align-items: center; gap: var(--space-4); padding: var(--space-4); border-radius: var(--radius-md); background: var(--color-surface-2); }
.step-intro > span { display: grid; width: 3.5rem; height: 3.5rem; flex: 0 0 auto; border-radius: 1rem; background: var(--color-primary-soft); color: var(--color-primary); place-items: center; }
.step-intro p { margin: .15rem 0 0; color: var(--color-text-muted); font-size: var(--font-size-xs); }
.readonly-value { display: flex; align-items: center; justify-content: space-between; gap: var(--space-3); min-height: 3.25rem; padding: var(--space-3) var(--space-4); border: 1px solid var(--color-border); border-radius: var(--radius-md); background: var(--color-surface-input); }
.readonly-value span { color: var(--color-text-muted); font-size: var(--font-size-sm); }
.readonly-value bdi { color: var(--color-text-primary); font-weight: 700; }
.file-drop { position: relative; display: flex; align-items: center; gap: var(--space-3); min-height: 6rem; padding: var(--space-4); border: 1px dashed var(--color-border-hover); border-radius: var(--radius-md); background: var(--color-surface-2); color: var(--color-primary); cursor: pointer; }
.file-drop.selected { border-color: var(--color-success); color: var(--color-success); }
.file-drop:focus-within { border-color: var(--color-border-focus); box-shadow: var(--shadow-focus); }
.file-drop input { position: absolute; width: 1px; height: 1px; opacity: 0; }
.file-drop span { display: grid; min-width: 0; color: var(--color-text-primary); }
.file-drop strong { overflow: hidden; text-overflow: ellipsis; }
.file-drop small { color: var(--color-text-muted); font-size: var(--font-size-xs); }
.privacy-note { display: flex; align-items: center; gap: var(--space-2); color: var(--color-text-muted); font-size: var(--font-size-xs); }
.form-actions { display: grid; grid-template-columns: minmax(0, 1fr) auto; align-items: center; gap: var(--space-3); }
@media (max-width: 520px) {
  .form-grid { grid-template-columns: minmax(0, 1fr); }
  .step-intro { align-items: flex-start; }
  .form-actions { grid-template-columns: minmax(0, 1fr); }
}
</style>
