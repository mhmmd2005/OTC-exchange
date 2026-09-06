<script setup>
import {computed, onMounted, ref} from 'vue'
import {AlertTriangle, CheckCircle2, CircleUserRound, FileText, Loader, ShieldCheck} from 'lucide-vue-next'
import kycService from '../services/kyc'

const loading = ref(false)
const submitting = ref(false)
const error = ref(null)
const kyc = ref(null)
const documentInput = ref(null)

const formData = ref({
  first_name: '',
  last_name: '',
  national_id: '',
  birth_date: '',
  phone_number: '',
  email: '',
  identity_document: null,
})

const MAX_FILE_SIZE = 5 * 1024 * 1024
const allowedTypes = ['image/jpeg', 'image/png', 'application/pdf']

const statusMeta = computed(() => {
  if (!kyc.value) {
    return {
      label: 'شروع احراز هویت',
      tone: 'info',
      detail: 'لطفاً اطلاعات هویتی خود را وارد و درخواست احراز هویت را ثبت کنید.',
    }
  }

  if (kyc.value.status === 'approved') {
    return {
      label: 'تأیید شده',
      tone: 'success',
      detail: 'احراز هویت شما با موفقیت تأیید شد. حساب شما آماده استفاده از امکانات کامل صرافی است.',
    }
  }

  if (kyc.value.status === 'rejected') {
    return {
      label: 'رد شده',
      tone: 'danger',
      detail: 'درخواست احراز هویت شما تأیید نشد. لطفاً دلیل رد درخواست را بررسی کرده و اطلاعات یا مدارک را اصلاح کنید.',
    }
  }

  if (kyc.value.status === 'pending') {
    return {
      label: 'در حال بررسی',
      tone: 'warning',
      detail: 'درخواست احراز هویت شما با موفقیت ثبت شد و در حال بررسی است. لطفاً تا اعلام نتیجه منتظر بمانید.',
    }
  }

  return {
    label: 'نامعلوم',
    tone: 'info',
    detail: 'وضعیت احراز هویت نامشخص است.',
  }
})

const isLocked = computed(() => {
  return kyc.value?.status === 'pending' || kyc.value?.status === 'approved'
})

const documentLabel = computed(() => {
  const document = formData.value.identity_document
  if (!document) return 'انتخاب تصویر یا فایل مدرک'
  return document.name || 'مدرک انتخاب شده'
})

function statusClass(value) {
  if (value === 'approved') return 'success'
  if (value === 'rejected') return 'danger'
  if (value === 'pending') return 'warning'
  return 'info'
}

function syncForm(data) {
  formData.value = {
    first_name: data?.first_name || '',
    last_name: data?.last_name || '',
    national_id: data?.national_id || '',
    birth_date: data?.birth_date || '',
    phone_number: data?.phone_number || '',
    email: data?.email || '',
    identity_document: null,
  }
}

function loadKyc() {
  loading.value = true
  error.value = null

  kycService
      .get()
      .then((response) => {
        kyc.value = response.data
        syncForm(kyc.value)
      })
      .catch((err) => {
        error.value = err.message || 'خطایی رخ داد.'
      })
      .finally(() => {
        loading.value = false
      })
}

function handleDocumentChange(event) {
  const file = event.target.files?.[0] || null

  if (!file) {
    formData.value.identity_document = null
    return
  }

  if (!allowedTypes.includes(file.type)) {
    error.value = 'فرمت مدرک باید JPG، PNG یا PDF باشد.'
    formData.value.identity_document = null
    event.target.value = ''
    return
  }

  if (file.size > MAX_FILE_SIZE) {
    error.value = 'حجم فایل نباید بیشتر از 5 مگابایت باشد.'
    formData.value.identity_document = null
    event.target.value = ''
    return
  }

  formData.value.identity_document = file
  error.value = null
}

function validateForm() {
  if (!formData.value.first_name.trim()) {
    error.value = 'نام را وارد کنید.'
    return false
  }

  if (!formData.value.last_name.trim()) {
    error.value = 'نام خانوادگی را وارد کنید.'
    return false
  }

  if (!formData.value.national_id.trim()) {
    error.value = 'کد ملی را وارد کنید.'
    return false
  }

  if (!/^\d{10}$/.test(formData.value.national_id.trim())) {
    error.value = 'کد ملی باید 10 رقم باشد.'
    return false
  }

  if (!formData.value.birth_date) {
    error.value = 'تاریخ تولد را وارد کنید.'
    return false
  }

  if (!formData.value.identity_document) {
    error.value = 'تصویر یا فایل مدرک شناسایی خود را انتخاب کنید.'
    return false
  }

  return true
}

function submitKyc() {
  if (!validateForm()) return

  submitting.value = true
  error.value = null

  kycService
      .submit(formData.value)
      .then((response) => {
        kyc.value = response.data
        syncForm(kyc.value)
      })
      .catch((err) => {
        error.value = err.message || 'ثبت درخواست احراز هویت با خطا مواجه شد.'
      })
      .finally(() => {
        submitting.value = false
      })
}

function resubmitKyc() {
  submitKyc()
}

onMounted(() => {
  loadKyc()
})
</script>

<template>
  <div class="kyc-shell">
    <header class="page-header">
      <div>
        <div class="page-kicker">پلتفرم OTC</div>
        <h1 class="page-title">احراز هویت</h1>
        <p class="page-subtitle">تکمیل اطلاعات هویتی برای فعال‌سازی کامل حساب</p>
      </div>
    </header>

    <section class="panel status-panel">
      <div class="status-head">
        <div>
          <div class="panel-label">وضعیت احراز هویت</div>
          <h2>بررسی هویت شما</h2>
        </div>
        <span v-if="kyc" :class="['status-badge', statusClass(kyc.status)]">
          {{ statusMeta.label }}
        </span>
      </div>

      <div class="status-grid">
        <p class="status-detail">{{ statusMeta.detail }}</p>

        <div v-if="kyc && kyc.status === 'rejected' && kyc.rejection_reason" class="rejection-reason">
          <strong>دلیل رد درخواست:</strong>
          <p>{{ kyc.rejection_reason }}</p>
        </div>
      </div>
    </section>

    <div v-if="error" class="error-alert">
      <AlertTriangle :size="18"/>
      <span>{{ error }}</span>
    </div>

    <section v-if="loading" class="panel loading-panel">
      <div class="loading-state">
        <Loader class="spinner"/>
        <p>در حال بارگذاری اطلاعات...</p>
      </div>
    </section>

    <section v-else-if="kyc" class="panel form-panel">
      <div v-if="kyc.can_edit" class="form-container">
        <div class="section-title-row">
          <div class="section-tag">
            <CircleUserRound :size="16"/>
            اطلاعات شخصی
          </div>
        </div>

        <div class="form-grid two">
          <div class="field">
            <label>نام</label>
            <input
                v-model="formData.first_name"
                type="text"
                class="premium-input"
                :disabled="submitting"
                placeholder="نام"
            />
          </div>

          <div class="field">
            <label>نام خانوادگی</label>
            <input
                v-model="formData.last_name"
                type="text"
                class="premium-input"
                :disabled="submitting"
                placeholder="نام خانوادگی"
            />
          </div>

          <div class="field">
            <label>کد ملی</label>
            <input
                v-model="formData.national_id"
                type="text"
                inputmode="numeric"
                maxlength="10"
                class="premium-input"
                :disabled="submitting"
                placeholder="کد ملی 10 رقمی"
            />
          </div>

          <div class="field">
            <label>تاریخ تولد</label>
            <input
                v-model="formData.birth_date"
                type="date"
                class="premium-input"
                :disabled="submitting"
            />
          </div>

          <div class="field">
            <label>شماره موبایل</label>
            <input
                v-model="formData.phone_number"
                type="text"
                class="premium-input readonly-input"
                readonly
            />
          </div>

          <div class="field">
            <label>ایمیل (اختیاری)</label>
            <input
                v-model="formData.email"
                type="email"
                class="premium-input"
                :disabled="submitting"
                placeholder="ایمیل"
            />
          </div>
        </div>

        <div class="section-title-row document-section-title">
          <div class="section-tag">
            <FileText :size="16"/>
            مدرک شناسایی
          </div>
        </div>

        <div class="document-upload">
          <input
              ref="documentInput"
              type="file"
              accept=".jpg,.jpeg,.png,.pdf"
              :disabled="submitting"
              @change="handleDocumentChange"
          />

          <button
              type="button"
              class="document-button"
              :disabled="submitting"
              @click="documentInput?.click()"
          >
            <FileText :size="19"/>
            <span>{{ documentLabel }}</span>
          </button>

          <div class="document-help">
            فقط یک مدرک شناسایی معتبر و خوانا ارسال کنید.
            فرمت‌های مجاز: JPG، PNG، PDF — حداکثر 5 مگابایت
          </div>

          <div v-if="formData.identity_document" class="document-selected">
            <FileText :size="16"/>
            <span>{{ formData.identity_document.name }}</span>
          </div>
        </div>

        <div class="security-note">
          <AlertTriangle :size="15"/>
          اطلاعات و مدارک شما فقط برای فرآیند احراز هویت و حفظ امنیت حساب استفاده می‌شود.
        </div>

        <div class="modal-actions">
          <button
              type="button"
              class="primary-btn"
              @click="kyc.status === 'rejected' ? resubmitKyc() : submitKyc()"
              :disabled="submitting"
          >
            <Loader v-if="submitting" class="inline-spinner"/>
            {{
              submitting
                  ? 'در حال ارسال...'
                  : kyc.status === 'rejected'
                      ? 'ارسال مجدد'
                      : 'ارسال درخواست احراز هویت'
            }}
          </button>
        </div>
      </div>

      <div v-else class="form-container read-only">
        <div class="section-title-row">
          <div class="section-tag">
            <ShieldCheck :size="16"/>
            اطلاعات ثبت شده
          </div>
        </div>

        <div class="form-grid two">
          <div class="field">
            <label>نام</label>
            <div class="static-value">{{ kyc.first_name || '-' }}</div>
          </div>

          <div class="field">
            <label>نام خانوادگی</label>
            <div class="static-value">{{ kyc.last_name || '-' }}</div>
          </div>

          <div class="field">
            <label>کد ملی</label>
            <div class="static-value">{{ kyc.national_id || '-' }}</div>
          </div>

          <div class="field">
            <label>تاریخ تولد</label>
            <div class="static-value">{{ kyc.birth_date || '-' }}</div>
          </div>

          <div class="field">
            <label>شماره موبایل</label>
            <div class="static-value">{{ kyc.phone_number || '-' }}</div>
          </div>

          <div class="field">
            <label>ایمیل</label>
            <div class="static-value">{{ kyc.email || '-' }}</div>
          </div>

          <div class="field full">
            <label>مدرک شناسایی</label>
            <div class="static-value document-static">
              <FileText :size="17"/>
              <span>
                {{
                  typeof kyc.identity_document === 'string'
                      ? 'مدرک شناسایی ثبت شده'
                      : kyc.identity_document?.name || 'مدرک شناسایی ثبت شده'
                }}
              </span>
            </div>
          </div>
        </div>

        <div v-if="kyc.status === 'pending'" class="status-message warning">
          <AlertTriangle :size="16"/>
          درخواست احراز هویت شما با موفقیت ثبت شد و در حال بررسی است. لطفاً تا اعلام نتیجه منتظر بمانید.
        </div>

        <div v-else-if="kyc.status === 'approved'" class="status-message success">
          <CheckCircle2 :size="16"/>
          احراز هویت شما با موفقیت تأیید شد. حساب شما آماده استفاده از امکانات کامل صرافی است.
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.kyc-shell {
  width: 100%;
  max-width: 1120px;
  margin: 0 auto;
  padding: 32px;
  color: var(--text-primary)
}

.page-header {
  margin-bottom: 32px
}

.page-kicker {
  font-size: .75rem;
  color: var(--gold);
  font-weight: 700;
  letter-spacing: .08em;
  text-transform: uppercase;
  margin-bottom: 10px
}

.page-title {
  margin: 0 0 10px;
  font-size: 2.2rem;
  font-weight: 800;
  letter-spacing: -.045em;
  color: var(--text-primary)
}

.page-subtitle {
  margin: 0;
  color: var(--text-muted);
  font-size: .98rem;
  line-height: 1.9
}

.panel {
  background: var(--surface-card);
  border: 1px solid var(--border-default);
  border-radius: 20px;
  box-shadow: var(--shadow-card);
  color: var(--text-primary);
  margin-bottom: 22px
}

.status-panel {
  padding: 28px;
  background: linear-gradient(135deg, var(--surface-card), var(--surface-alt))
}

.status-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 22px
}

.panel-label {
  margin-bottom: 7px;
  color: var(--text-muted);
  font-size: .76rem;
  font-weight: 700;
  letter-spacing: .04em
}

.status-head h2 {
  margin: 0;
  font-size: 1.5rem;
  color: var(--text-primary)
}

.status-grid {
  display: flex;
  flex-direction: column;
  gap: 14px
}

.status-detail {
  margin: 0;
  color: var(--text-secondary);
  font-size: .95rem;
  line-height: 1.9
}

.status-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 8px 14px;
  border-radius: 999px;
  border: 1px solid transparent;
  font-size: .78rem;
  font-weight: 700;
  white-space: nowrap
}

.status-badge.success {
  background: var(--success-soft);
  border-color: rgba(22, 199, 132, .18);
  color: var(--success)
}

.status-badge.warning {
  background: var(--warning-soft);
  border-color: rgba(212, 169, 90, .18);
  color: var(--warning)
}

.status-badge.danger {
  background: var(--danger-soft);
  border-color: rgba(234, 57, 67, .18);
  color: var(--danger)
}

.status-badge.info {
  background: var(--info-soft);
  border-color: rgba(58, 111, 248, .18);
  color: var(--info)
}

.rejection-reason {
  padding: 16px 18px;
  background: var(--danger-soft);
  border: 1px solid rgba(234, 57, 67, .14);
  border-right: 3px solid var(--danger);
  border-radius: 14px
}

.rejection-reason strong {
  display: block;
  margin-bottom: 7px;
  color: var(--danger);
  font-size: .84rem
}

.rejection-reason p {
  margin: 0;
  color: var(--text-secondary);
  line-height: 1.9;
  font-size: .9rem
}

.error-alert {
  display: flex;
  align-items: center;
  gap: 11px;
  padding: 14px 16px;
  margin-bottom: 20px;
  background: var(--danger-soft);
  border: 1px solid rgba(234, 57, 67, .16);
  border-radius: 14px;
  color: var(--danger);
  font-size: .9rem
}

.loading-panel {
  padding: 54px 28px
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  color: var(--text-muted)
}

.spinner {
  width: 32px;
  height: 32px;
  color: var(--gold);
  animation: spin 1s linear infinite
}

.form-panel {
  padding: 28px
}

.form-container {
  display: flex;
  flex-direction: column;
  gap: 24px
}

.section-title-row {
  display: flex;
  align-items: center;
  margin-bottom: 4px
}

.document-section-title {
  margin-top: 6px
}

.section-tag {
  display: inline-flex;
  align-items: center;
  gap: 9px;
  color: var(--text-primary);
  font-size: 1rem;
  font-weight: 700
}

.form-grid {
  display: grid;
  grid-template-columns:repeat(2, minmax(0, 1fr));
  gap: 20px
}

.field {
  display: flex;
  flex-direction: column;
  gap: 9px
}

.field.full {
  grid-column: 1/-1
}

.field label {
  font-size: .82rem;
  font-weight: 600;
  color: var(--text-secondary)
}

.premium-input {
  width: 100%;
  min-height: 52px;
  padding: 0 16px;
  background: var(--surface-input);
  border: 1px solid var(--border-default);
  border-radius: 13px;
  color: var(--text-primary);
  font-size: .94rem;
  font-family: inherit;
  outline: none;
  transition: .2s
}

.premium-input::placeholder {
  color: var(--text-muted)
}

.premium-input:hover {
  border-color: var(--border-strong)
}

.premium-input:focus {
  border-color: var(--gold);
  box-shadow: 0 0 0 3px var(--ring)
}

.premium-input:disabled {
  background: var(--surface-soft);
  border-color: var(--border-subtle);
  color: var(--text-disabled);
  cursor: not-allowed
}

.readonly-input {
  background: var(--surface-soft);
  color: var(--text-secondary);
  cursor: default
}

.document-upload {
  display: flex;
  flex-direction: column;
  gap: 10px
}

.document-upload > input {
  display: none
}

.document-button {
  min-height: 58px;
  padding: 0 18px;
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 11px;
  border: 1px dashed var(--border-strong);
  border-radius: 14px;
  background: var(--surface-input);
  color: var(--text-secondary);
  font-family: inherit;
  font-size: .9rem;
  cursor: pointer;
  transition: .2s;
  text-align: right
}

.document-button:hover:not(:disabled) {
  border-color: var(--gold);
  background: var(--surface-alt);
  color: var(--text-primary)
}

.document-button:disabled {
  opacity: .55;
  cursor: not-allowed
}

.document-help {
  color: var(--text-muted);
  font-size: .78rem;
  line-height: 1.8
}

.document-selected {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 11px 13px;
  border-radius: 11px;
  background: var(--success-soft);
  border: 1px solid rgba(22, 199, 132, .12);
  color: var(--success);
  font-size: .82rem
}

.document-static {
  gap: 9px
}

.security-note {
  display: flex;
  align-items: flex-start;
  gap: 11px;
  padding: 15px 16px;
  background: var(--info-soft);
  border: 1px solid rgba(58, 111, 248, .14);
  border-radius: 13px;
  color: var(--text-secondary);
  font-size: .82rem;
  line-height: 1.9
}

.security-note svg {
  flex: 0 0 auto;
  margin-top: 4px;
  color: var(--info)
}

.status-message {
  display: flex;
  align-items: flex-start;
  gap: 11px;
  padding: 15px 16px;
  border-radius: 13px;
  font-size: .84rem;
  line-height: 1.9
}

.status-message.warning {
  background: var(--warning-soft);
  border: 1px solid rgba(212, 169, 90, .14);
  color: var(--warning)
}

.status-message.success {
  background: var(--success-soft);
  border: 1px solid rgba(22, 199, 132, .14);
  color: var(--success)
}

.status-message svg {
  flex: 0 0 auto;
  margin-top: 4px
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding-top: 20px;
  margin-top: 2px;
  border-top: 1px solid var(--border-subtle)
}

.primary-btn {
  min-height: 50px;
  padding: 0 24px;
  border: 1px solid var(--gold);
  border-radius: 13px;
  background: linear-gradient(135deg, var(--gold-light), var(--gold));
  color: #111827;
  font-family: inherit;
  font-size: .88rem;
  font-weight: 800;
  cursor: pointer;
  box-shadow: 0 10px 22px rgba(212, 169, 90, .12);
  transition: .2s
}

.primary-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 14px 28px rgba(212, 169, 90, .18)
}

.primary-btn:disabled {
  opacity: .55;
  cursor: not-allowed;
  transform: none;
  box-shadow: none
}

.inline-spinner {
  width: 17px;
  height: 17px;
  animation: spin 1s linear infinite
}

@keyframes spin {
  from {
    transform: rotate(0)
  }
  to {
    transform: rotate(360deg)
  }
}

@media (max-width: 900px) {
  .kyc-shell {
    max-width: 100%;
    padding: 24px
  }

  .form-panel, .status-panel {
    padding: 24px
  }
}

@media (max-width: 760px) {
  .kyc-shell {
    padding: 18px
  }

  .page-header {
    margin-bottom: 22px
  }

  .page-title {
    font-size: 1.8rem
  }

  .status-head {
    flex-direction: column;
    align-items: flex-start
  }

  .form-grid {
    grid-template-columns:1fr
  }

  .field.full {
    grid-column: auto
  }

  .modal-actions {
    flex-direction: column
  }

  .modal-actions button {
    width: 100%
  }
}

@media (max-width: 480px) {
  .kyc-shell {
    padding: 14px
  }

  .status-panel, .form-panel {
    padding: 18px
  }

  .page-title {
    font-size: 1.55rem
  }

  .page-subtitle {
    font-size: .86rem
  }

  .status-head h2 {
    font-size: 1.2rem
  }

  .premium-input, .static-value {
    min-height: 48px
  }
}
</style>