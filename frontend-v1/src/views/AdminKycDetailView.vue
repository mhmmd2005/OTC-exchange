<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { AlertTriangle, ArrowRight, CheckCircle2, FileText, Loader, ShieldCheck, User, X } from 'lucide-vue-next'
import adminKycService from '../services/adminKyc'

const router = useRouter()
const route = useRoute()

const loading = ref(false)
const submitting = ref(false)
const error = ref(null)
const kyc = ref(null)

const showRejectDialog = ref(false)
const rejectReason = ref('')

const kycId = computed(() => route.params.id)

function formatDate(isoString) {
  if (!isoString) return '-'
  return new Date(isoString).toLocaleDateString('fa-IR', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function formatFileSize(bytes) {
  if (!bytes) return '-'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

function statusClass(status) {
  if (status === 'approved') return 'success'
  if (status === 'rejected') return 'danger'
  if (status === 'pending') return 'warning'
  return 'info'
}

function statusLabel(status) {
  if (status === 'approved') return 'تأیید شده'
  if (status === 'rejected') return 'رد شده'
  if (status === 'pending') return 'در حال بررسی'
  return 'نامعلوم'
}

const isProcessed = computed(() => {
  return kyc.value?.status === 'approved' || kyc.value?.status === 'rejected'
})

const canApprove = computed(() => {
  return kyc.value?.status === 'pending' && !submitting.value
})

const canReject = computed(() => {
  return kyc.value?.status === 'pending' && !submitting.value
})

function loadKyc() {
  loading.value = true
  error.value = null

  adminKycService
    .getById(kycId.value)
    .then((response) => {
      kyc.value = response.data
    })
    .catch((err) => {
      error.value = err.message || 'خطایی رخ داد.'
    })
    .finally(() => {
      loading.value = false
    })
}

function openRejectDialog() {
  rejectReason.value = ''
  showRejectDialog.value = true
}

function closeRejectDialog() {
  showRejectDialog.value = false
  rejectReason.value = ''
}

function approveKyc() {
  if (!confirm('آیا از تأیید این درخواست احراز هویت اطمینان دارید؟')) {
    return
  }

  submitting.value = true
  error.value = null

  adminKycService
    .approve(kycId.value)
    .then((response) => {
      kyc.value = response.data
    })
    .catch((err) => {
      error.value = err.message || 'خطایی رخ داد.'
    })
    .finally(() => {
      submitting.value = false
    })
}

function rejectKyc() {
  if (!rejectReason.value.trim()) {
    error.value = 'لطفاً دلیل رد درخواست را وارد کنید.'
    return
  }

  submitting.value = true
  error.value = null

  adminKycService
    .reject(kycId.value, rejectReason.value)
    .then((response) => {
      kyc.value = response.data
      closeRejectDialog()
    })
    .catch((err) => {
      error.value = err.message || 'خطایی رخ داد.'
    })
    .finally(() => {
      submitting.value = false
    })
}

function goBack() {
  router.push('/admin/kyc')
}

onMounted(() => {
  loadKyc()
})
</script>

<template>
  <div class="admin-kyc-detail-shell">
    <header class="page-header">
      <button class="back-btn" @click="goBack">
        <ArrowRight :size="18"/>
        <span>بازگشت</span>
      </button>
      <div>
        <div class="page-kicker">پنل مدیریت</div>
        <h1 class="page-title">جزئیات درخواست احراز هویت</h1>
        <p class="page-subtitle">بررسی اطلاعات و مدارک کاربر</p>
      </div>
    </header>

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

    <section v-else-if="kyc" class="panel">
      <div class="panel-head">
        <div class="panel-title">
          <ShieldCheck :size="20"/>
          <span>اطلاعات کاربر</span>
        </div>
        <span :class="['status-badge', statusClass(kyc.status)]">
          {{ statusLabel(kyc.status) }}
        </span>
      </div>

      <div class="panel-body">
        <div class="user-summary">
          <div class="user-avatar-large">
            <User :size="32"/>
          </div>
          <div class="user-meta">
            <h2>{{ kyc.first_name }} {{ kyc.last_name }}</h2>
            <span>{{ kyc.phone_number }}</span>
            <span v-if="kyc.email">{{ kyc.email }}</span>
          </div>
        </div>

        <div class="info-grid">
          <div class="info-card">
            <div class="info-label">نام</div>
            <div class="info-value">{{ kyc.first_name || '-' }}</div>
          </div>

          <div class="info-card">
            <div class="info-label">نام خانوادگی</div>
            <div class="info-value">{{ kyc.last_name || '-' }}</div>
          </div>

          <div class="info-card">
            <div class="info-label">کد ملی</div>
            <div class="info-value">{{ kyc.national_id || '-' }}</div>
          </div>

          <div class="info-card">
            <div class="info-label">تاریخ تولد</div>
            <div class="info-value">{{ kyc.birth_date || '-' }}</div>
          </div>

          <div class="info-card">
            <div class="info-label">شماره موبایل</div>
            <div class="info-value">{{ kyc.phone_number || '-' }}</div>
          </div>

          <div class="info-card">
            <div class="info-label">ایمیل</div>
            <div class="info-value">{{ kyc.email || '-' }}</div>
          </div>

          <div class="info-card">
            <div class="info-label">تاریخ ثبت درخواست</div>
            <div class="info-value">{{ formatDate(kyc.submitted_at) }}</div>
          </div>

          <div class="info-card" v-if="kyc.reviewed_at">
            <div class="info-label">تاریخ بررسی</div>
            <div class="info-value">{{ formatDate(kyc.reviewed_at) }}</div>
          </div>
        </div>

        <div class="document-section">
          <div class="section-title">
            <FileText :size="18"/>
            <span>مدرک شناسایی</span>
          </div>

          <div v-if="kyc.identity_document" class="document-card">
            <div class="document-info">
              <FileText :size="24"/>
              <div class="document-details">
                <strong>{{ kyc.identity_document.name || 'مدرک شناسایی' }}</strong>
                <span v-if="kyc.identity_document.type">{{ kyc.identity_document.type }}</span>
                <span v-if="kyc.identity_document.size">حجم: {{ formatFileSize(kyc.identity_document.size) }}</span>
              </div>
            </div>
            <div class="document-note">
              <AlertTriangle :size="14"/>
              <span>در حالت Mock، فقط متادیتای فایل نمایش داده می‌شود.</span>
            </div>
          </div>

          <div v-else class="document-card empty">
            <FileText :size="24"/>
            <span>مدرکی ثبت نشده است</span>
          </div>
        </div>

        <div v-if="kyc.rejection_reason" class="rejection-reason">
          <strong>دلیل رد درخواست:</strong>
          <p>{{ kyc.rejection_reason }}</p>
        </div>
      </div>

      <div class="panel-footer">
        <div class="actions">
          <button
            class="action-btn approve"
            :disabled="!canApprove"
            @click="approveKyc"
          >
            <Loader v-if="submitting" class="inline-spinner"/>
            <CheckCircle2 v-else :size="18"/>
            <span>{{ submitting ? 'در حال پردازش...' : 'تأیید درخواست' }}</span>
          </button>

          <button
            class="action-btn reject"
            :disabled="!canReject"
            @click="openRejectDialog"
          >
            <X :size="18"/>
            <span>رد درخواست</span>
          </button>
        </div>
      </div>
    </section>

    <div v-if="showRejectDialog" class="modal-overlay" @click="closeRejectDialog">
      <div class="modal" @click.stop>
        <div class="modal-header">
          <h3>رد درخواست احراز هویت</h3>
          <button class="modal-close" @click="closeRejectDialog">
            <X :size="18"/>
          </button>
        </div>

        <div class="modal-body">
          <p class="modal-desc">لطفاً دلیل رد درخواست را وارد کنید. این دلیل به کاربر نمایش داده خواهد شد.</p>
          <textarea
            v-model="rejectReason"
            class="reject-input"
            placeholder="دلیل رد درخواست..."
            rows="4"
            :disabled="submitting"
          ></textarea>
        </div>

        <div class="modal-footer">
          <button class="modal-btn secondary" @click="closeRejectDialog" :disabled="submitting">
            انصراف
          </button>
          <button class="modal-btn danger" @click="rejectKyc" :disabled="submitting || !rejectReason.trim()">
            <Loader v-if="submitting" class="inline-spinner"/>
            <span>{{ submitting ? 'در حال پردازش...' : 'ثبت رد درخواست' }}</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.admin-kyc-detail-shell {
  width: 100%;
  max-width: 1000px;
  margin: 0 auto;
  padding: 32px;
  color: var(--text-primary)
}

.page-header {
  margin-bottom: 32px;
  display: flex;
  align-items: center;
  gap: 20px
}

.back-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  border: 1px solid var(--border-default);
  border-radius: 12px;
  background: var(--surface-input);
  color: var(--text-secondary);
  font-family: inherit;
  font-size: .85rem;
  font-weight: 600;
  cursor: pointer;
  transition: .2s
}

.back-btn:hover {
  border-color: var(--gold);
  color: var(--text-primary)
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

.panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24px 28px;
  border-bottom: 1px solid var(--border-subtle)
}

.panel-title {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--text-primary)
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

.panel-body {
  padding: 28px
}

.user-summary {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 24px;
  background: var(--surface-input);
  border: 1px solid var(--border-default);
  border-radius: 16px;
  margin-bottom: 24px
}

.user-avatar-large {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 64px;
  height: 64px;
  background: var(--surface-soft);
  border: 1px solid var(--border-subtle);
  border-radius: 16px;
  color: var(--text-muted)
}

.user-meta {
  display: flex;
  flex-direction: column;
  gap: 6px
}

.user-meta h2 {
  margin: 0;
  font-size: 1.3rem;
  color: var(--text-primary)
}

.user-meta span {
  font-size: .9rem;
  color: var(--text-muted)
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  margin-bottom: 24px
}

.info-card {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 16px;
  background: var(--surface-input);
  border: 1px solid var(--border-default);
  border-radius: 12px
}

.info-label {
  font-size: .78rem;
  color: var(--text-muted);
  font-weight: 600
}

.info-value {
  font-size: .95rem;
  color: var(--text-secondary);
  font-weight: 500
}

.document-section {
  margin-bottom: 24px
}

.section-title {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
  font-size: 1rem;
  font-weight: 700;
  color: var(--text-primary)
}

.document-card {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 20px;
  background: var(--surface-input);
  border: 1px solid var(--border-default);
  border-radius: 14px
}

.document-card.empty {
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: var(--text-muted)
}

.document-info {
  display: flex;
  align-items: flex-start;
  gap: 14px
}

.document-info svg {
  flex: 0 0 auto;
  color: var(--text-muted)
}

.document-details {
  display: flex;
  flex-direction: column;
  gap: 6px
}

.document-details strong {
  font-size: .95rem;
  color: var(--text-primary)
}

.document-details span {
  font-size: .82rem;
  color: var(--text-muted)
}

.document-note {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  background: var(--warning-soft);
  border: 1px solid rgba(212, 169, 90, .14);
  border-radius: 10px;
  font-size: .82rem;
  color: var(--warning)
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

.panel-footer {
  padding: 20px 28px 28px;
  border-top: 1px solid var(--border-subtle)
}

.actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 10px;
  min-height: 48px;
  padding: 0 20px;
  border-radius: 12px;
  font-family: inherit;
  font-size: .88rem;
  font-weight: 700;
  cursor: pointer;
  transition: .2s
}

.action-btn:disabled {
  opacity: .5;
  cursor: not-allowed
}

.action-btn.approve {
  background: linear-gradient(135deg, var(--success-soft), var(--success));
  border: 1px solid rgba(22, 199, 132, .3);
  color: #0f5132
}

.action-btn.approve:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 8px 20px rgba(22, 199, 132, .2)
}

.action-btn.reject {
  background: var(--danger-soft);
  border: 1px solid rgba(234, 57, 67, .3);
  color: var(--danger)
}

.action-btn.reject:hover:not(:disabled) {
  background: var(--danger);
  color: white
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

.inline-spinner {
  width: 17px;
  height: 17px;
  animation: spin 1s linear infinite
}

@keyframes spin {
  from { transform: rotate(0) }
  to { transform: rotate(360deg) }
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, .6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 200;
  padding: 20px
}

.modal {
  background: var(--surface-card);
  border: 1px solid var(--border-default);
  border-radius: 20px;
  box-shadow: var(--shadow-modal);
  width: 100%;
  max-width: 500px;
  color: var(--text-primary)
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid var(--border-subtle)
}

.modal-header h3 {
  margin: 0;
  font-size: 1.1rem;
  color: var(--text-primary)
}

.modal-close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  background: var(--surface-input);
  border-radius: 8px;
  color: var(--text-muted);
  cursor: pointer;
  transition: .2s
}

.modal-close:hover {
  background: var(--surface-alt);
  color: var(--text-primary)
}

.modal-body {
  padding: 24px
}

.modal-desc {
  margin: 0 0 16px;
  color: var(--text-secondary);
  font-size: .9rem;
  line-height: 1.8
}

.reject-input {
  width: 100%;
  padding: 12px 16px;
  background: var(--surface-input);
  border: 1px solid var(--border-default);
  border-radius: 12px;
  color: var(--text-primary);
  font-family: inherit;
  font-size: .9rem;
  resize: vertical;
  outline: none;
  transition: .2s
}

.reject-input::placeholder {
  color: var(--text-muted)
}

.reject-input:focus {
  border-color: var(--gold);
  box-shadow: 0 0 0 3px var(--ring)
}

.reject-input:disabled {
  background: var(--surface-soft);
  border-color: var(--border-subtle);
  color: var(--text-disabled);
  cursor: not-allowed
}

.modal-footer {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  padding: 16px 24px 24px;
  border-top: 1px solid var(--border-subtle)
}

.modal-btn {
  min-height: 42px;
  padding: 0 20px;
  border-radius: 10px;
  font-family: inherit;
  font-size: .88rem;
  font-weight: 700;
  cursor: pointer;
  transition: .2s
}

.modal-btn:disabled {
  opacity: .5;
  cursor: not-allowed
}

.modal-btn.secondary {
  background: var(--surface-input);
  border: 1px solid var(--border-default);
  color: var(--text-secondary)
}

.modal-btn.secondary:hover:not(:disabled) {
  background: var(--surface-alt);
  color: var(--text-primary)
}

.modal-btn.danger {
  background: var(--danger);
  border: 1px solid var(--danger);
  color: white
}

.modal-btn.danger:hover:not(:disabled) {
  background: #c82333;
  border-color: #c82333
}

@media (max-width: 900px) {
  .admin-kyc-detail-shell {
    max-width: 100%;
    padding: 24px
  }

  .info-grid {
    grid-template-columns: 1fr
  }
}

@media (max-width: 760px) {
  .admin-kyc-detail-shell {
    padding: 18px
  }

  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px
  }

  .page-title {
    font-size: 1.8rem
  }

  .user-summary {
    flex-direction: column;
    text-align: center
  }

  .actions {
    flex-direction: column
  }

  .action-btn {
    width: 100%;
    justify-content: center
  }
}

@media (max-width: 480px) {
  .admin-kyc-detail-shell {
    padding: 14px
  }

  .panel-head, .panel-body, .panel-footer {
    padding: 20px 18px
  }

  .page-title {
    font-size: 1.55rem
  }

  .page-subtitle {
    font-size: .86rem
  }

  .modal {
    margin: 10px
  }
}
</style>
