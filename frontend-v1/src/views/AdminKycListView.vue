<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { AlertTriangle, CheckCircle2, Clock, FileText, Loader, ShieldCheck, User } from 'lucide-vue-next'
import adminKycService from '../services/adminKyc'

const router = useRouter()
const loading = ref(false)
const error = ref(null)
const applications = ref([])

const pendingApplications = computed(() => {
  return applications.value.filter(app => app.status === 'pending')
})

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

function openDetails(id) {
  router.push(`/admin/kyc/${id}`)
}

function loadApplications() {
  loading.value = true
  error.value = null

  adminKycService
    .get()
    .then((response) => {
      applications.value = response.data
    })
    .catch((err) => {
      error.value = err.message || 'خطایی رخ داد.'
    })
    .finally(() => {
      loading.value = false
    })
}

onMounted(() => {
  loadApplications()
})
</script>

<template>
  <div class="admin-kyc-shell">
    <header class="page-header">
      <div>
        <div class="page-kicker">پنل مدیریت</div>
        <h1 class="page-title">مدیریت احراز هویت</h1>
        <p class="page-subtitle">بررسی و مدیریت درخواست‌های احراز هویت کاربران</p>
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

    <section v-else class="panel">
      <div class="panel-head">
        <div class="panel-title">
          <ShieldCheck :size="20"/>
          <span>درخواست‌های در انتظار بررسی</span>
        </div>
        <span class="panel-count">{{ pendingApplications.length }}</span>
      </div>

      <div v-if="pendingApplications.length === 0" class="empty-state">
        <Clock :size="48"/>
        <p>درخواستی برای بررسی وجود ندارد.</p>
      </div>

      <div v-else class="applications-list">
        <div
          v-for="app in pendingApplications"
          :key="app.id"
          class="application-card"
          @click="openDetails(app.id)"
        >
          <div class="card-header">
            <div class="user-info">
              <div class="user-avatar">
                <User :size="20"/>
              </div>
              <div class="user-details">
                <strong>{{ app.first_name }} {{ app.last_name }}</strong>
                <span>{{ app.phone_number }}</span>
              </div>
            </div>
            <span :class="['status-badge', statusClass(app.status)]">
              {{ statusLabel(app.status) }}
            </span>
          </div>

          <div class="card-body">
            <div class="info-row">
              <span class="info-label">کد ملی:</span>
              <span class="info-value">{{ app.national_id }}</span>
            </div>
            <div class="info-row">
              <span class="info-label">تاریخ ثبت:</span>
              <span class="info-value">{{ formatDate(app.submitted_at) }}</span>
            </div>
            <div class="info-row" v-if="app.identity_document">
              <span class="info-label">مدرک:</span>
              <span class="info-value document-info">
                <FileText :size="14"/>
                {{ app.identity_document.name || 'مدرک شناسایی' }}
              </span>
            </div>
          </div>

          <div class="card-footer">
            <button class="view-btn">
              مشاهده جزئیات
            </button>
          </div>
        </div>
      </div>
    </section>

    <section v-if="applications.length > 0 && pendingApplications.length !== applications.length" class="panel">
      <div class="panel-head">
        <div class="panel-title">
          <CheckCircle2 :size="20"/>
          <span>سایر درخواست‌ها</span>
        </div>
        <span class="panel-count">{{ applications.length - pendingApplications.length }}</span>
      </div>

      <div class="applications-list">
        <div
          v-for="app in applications.filter(a => a.status !== 'pending')"
          :key="app.id"
          class="application-card processed"
          @click="openDetails(app.id)"
        >
          <div class="card-header">
            <div class="user-info">
              <div class="user-avatar">
                <User :size="20"/>
              </div>
              <div class="user-details">
                <strong>{{ app.first_name }} {{ app.last_name }}</strong>
                <span>{{ app.phone_number }}</span>
              </div>
            </div>
            <span :class="['status-badge', statusClass(app.status)]">
              {{ statusLabel(app.status) }}
            </span>
          </div>

          <div class="card-body">
            <div class="info-row">
              <span class="info-label">کد ملی:</span>
              <span class="info-value">{{ app.national_id }}</span>
            </div>
            <div class="info-row">
              <span class="info-label">تاریخ ثبت:</span>
              <span class="info-value">{{ formatDate(app.submitted_at) }}</span>
            </div>
          </div>

          <div class="card-footer">
            <button class="view-btn">
              مشاهده جزئیات
            </button>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.admin-kyc-shell {
  width: 100%;
  max-width: 1200px;
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

.panel-count {
  padding: 6px 14px;
  background: var(--surface-input);
  border: 1px solid var(--border-default);
  border-radius: 999px;
  font-size: .8rem;
  font-weight: 700;
  color: var(--text-secondary)
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

@keyframes spin {
  from { transform: rotate(0) }
  to { transform: rotate(360deg) }
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 28px;
  gap: 16px;
  color: var(--text-muted)
}

.empty-state svg {
  color: var(--border-strong)
}

.empty-state p {
  font-size: .95rem
}

.applications-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 20px 28px 28px
}

.application-card {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 20px;
  background: var(--surface-input);
  border: 1px solid var(--border-default);
  border-radius: 14px;
  cursor: pointer;
  transition: .2s
}

.application-card:hover {
  border-color: var(--border-strong);
  background: var(--surface-alt)
}

.application-card.processed {
  opacity: .7
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px
}

.user-avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  background: var(--surface-soft);
  border: 1px solid var(--border-subtle);
  border-radius: 12px;
  color: var(--text-muted)
}

.user-details {
  display: flex;
  flex-direction: column;
  gap: 4px
}

.user-details strong {
  font-size: .95rem;
  color: var(--text-primary)
}

.user-details span {
  font-size: .82rem;
  color: var(--text-muted)
}

.status-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 6px 12px;
  border-radius: 999px;
  border: 1px solid transparent;
  font-size: .75rem;
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

.card-body {
  display: flex;
  flex-direction: column;
  gap: 10px
}

.info-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px
}

.info-label {
  font-size: .82rem;
  color: var(--text-muted)
}

.info-value {
  font-size: .85rem;
  color: var(--text-secondary);
  font-weight: 500
}

.document-info {
  display: flex;
  align-items: center;
  gap: 6px
}

.card-footer {
  padding-top: 12px;
  border-top: 1px solid var(--border-subtle)
}

.view-btn {
  width: 100%;
  min-height: 42px;
  padding: 0 16px;
  border: 1px solid var(--border-default);
  border-radius: 10px;
  background: var(--surface);
  color: var(--text-secondary);
  font-family: inherit;
  font-size: .85rem;
  font-weight: 600;
  cursor: pointer;
  transition: .2s
}

.view-btn:hover {
  border-color: var(--gold);
  color: var(--text-primary)
}

@media (max-width: 900px) {
  .admin-kyc-shell {
    max-width: 100%;
    padding: 24px
  }

  .panel-head {
    padding: 20px 24px
  }

  .applications-list {
    padding: 16px 24px 24px
  }
}

@media (max-width: 760px) {
  .admin-kyc-shell {
    padding: 18px
  }

  .page-header {
    margin-bottom: 22px
  }

  .page-title {
    font-size: 1.8rem
  }

  .card-header {
    flex-direction: column;
    align-items: flex-start
  }

  .info-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px
  }
}

@media (max-width: 480px) {
  .admin-kyc-shell {
    padding: 14px
  }

  .panel-head {
    padding: 16px 18px
  }

  .applications-list {
    padding: 12px 18px 18px
  }

  .page-title {
    font-size: 1.55rem
  }

  .page-subtitle {
    font-size: .86rem
  }
}
</style>
