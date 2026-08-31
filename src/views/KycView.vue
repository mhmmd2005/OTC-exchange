<script setup>
import { computed, ref } from 'vue'
import { AlertTriangle, CheckCircle2, CircleUserRound, FileCheck2, ShieldCheck, Upload } from 'lucide-vue-next'
import { mockKyc } from '../mock/data'

const currentStep = ref(1)
const kyc = mockKyc
const steps = ['اطلاعات شخصی', 'اطلاعات هویتی', 'آپلود مدارک', 'تأیید اطلاعات', 'نمایش وضعیت']

const statusMeta = computed(() => {
  if (kyc.status === 'تأیید شده') return { label: 'تأیید شده', tone: 'success', detail: 'احراز هویت شما با موفقیت تکمیل شد.' }
  if (kyc.status === 'رد شده') return { label: 'رد شده', tone: 'danger', detail: 'برای ادامه، اطلاعات یا مدارک نامعتبر باید اصلاح شوند.' }
  return { label: 'در انتظار بررسی', tone: 'warning', detail: 'درخواست شما در حال بررسی توسط تیم احراز هویت است.' }
})

const progressValue = computed(() => Math.round((currentStep.value / steps.length) * 100))

const nextStep = () => {
  currentStep.value = Math.min(currentStep.value + 1, steps.length)
}

const prevStep = () => {
  currentStep.value = Math.max(currentStep.value - 1, 1)
}

function statusClass(value) {
  if (value === 'تأیید شده') return 'success'
  if (value === 'رد شده') return 'danger'
  return 'warning'
}
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
        <span :class="['status-badge', statusClass(statusMeta.label)]">{{ statusMeta.label }}</span>
      </div>

      <div class="status-grid">
        <div class="status-main">
          <div class="status-copy">
            <ShieldCheck :size="18" />
            <span>سطح احراز هویت: سطح ۲</span>
          </div>
          <div class="progress-meta">
            <strong>{{ progressValue }}%</strong>
            <small>پیشرفت</small>
          </div>
        </div>

        <div class="progress-bar" aria-label="پیشرفت احراز هویت">
          <span :style="{ width: `${progressValue}%` }" />
        </div>

        <p class="status-detail">{{ statusMeta.detail }}</p>
      </div>
    </section>

    <div class="kyc-grid">
      <aside class="panel steps-panel">
        <div class="panel-header compact">
          <div>
            <div class="panel-label">فرآیند</div>
            <h3>مراحل احراز هویت</h3>
          </div>
        </div>

        <div class="kyc-steps">
          <div v-for="(step, index) in steps" :key="step" :class="['step-item', { done: currentStep > index + 1, active: currentStep === index + 1 }]">
            <div class="step-number">{{ index + 1 }}</div>
            <div class="step-text">
              <strong>{{ step }}</strong>
              <small>{{ currentStep === index + 1 ? 'در حال انجام' : currentStep > index + 1 ? 'تکمیل شده' : 'در انتظار' }}</small>
            </div>
          </div>
        </div>
      </aside>

      <section class="panel workflow-panel">
        <div v-if="currentStep === 1" class="content-box">
          <div class="section-title-row">
            <div class="section-tag"><CircleUserRound :size="16" /> اطلاعات شخصی</div>
          </div>

          <div class="form-grid two">
            <div class="field">
              <label>نام</label>
              <input class="premium-input" value="مهدی" />
            </div>
            <div class="field">
              <label>نام خانوادگی</label>
              <input class="premium-input" value="قاسمی" />
            </div>
            <div class="field">
              <label>تاریخ تولد</label>
              <input class="premium-input" value="۱۳۸۲/۰۷/۰۹" />
            </div>
            <div class="field">
              <label>کشور</label>
              <input class="premium-input" value="ایران" />
            </div>
          </div>
        </div>

        <div v-else-if="currentStep === 2" class="content-box">
          <div class="section-title-row">
            <div class="section-tag"><FileCheck2 :size="16" /> اطلاعات هویتی</div>
          </div>

          <div class="form-grid two">
            <div class="field">
              <label>کد ملی</label>
              <input class="premium-input" value="۱۲۳۴۵۶۷۸۹۰" />
            </div>
            <div class="field">
              <label>شماره شناسنامه</label>
              <input class="premium-input" value="AB-118728" />
            </div>
            <div class="field">
              <label>محل صدور</label>
              <input class="premium-input" value="تهران" />
            </div>
            <div class="field">
              <label>آدرس سکونت</label>
              <input class="premium-input" value="تهران، خیابان ولیعصر" />
            </div>
          </div>
        </div>

        <div v-else-if="currentStep === 3" class="content-box">
          <div class="section-title-row">
            <div class="section-tag"><Upload :size="16" /> آپلود مدارک</div>
          </div>

          <div class="upload-grid">
            <div class="upload-box">
              <div class="upload-icon"><Upload :size="20" /></div>
              <strong>تصویر کارت ملی</strong>
              <small>کارت ملی از دو طرف</small>
            </div>
            <div class="upload-box">
              <div class="upload-icon"><Upload :size="20" /></div>
              <strong>سلفی با مدارک</strong>
              <small>حضور شما در برابر مدارک</small>
            </div>
          </div>
        </div>

        <div v-else-if="currentStep === 4" class="content-box">
          <div class="section-title-row">
            <div class="section-tag"><CheckCircle2 :size="16" /> تأیید اطلاعات</div>
          </div>

          <div class="summary-box">
            <div class="summary-row"><span>نام کامل</span><strong>مهدی قاسمی</strong></div>
            <div class="summary-row"><span>کد ملی</span><strong>۱۲۳۴۵۶۷۸۹۰</strong></div>
            <div class="summary-row"><span>وضعیت مدارک</span><strong>ارسال شده</strong></div>
            <div class="summary-row"><span>انطباق اطلاعات</span><strong>تأیید شده</strong></div>
          </div>
        </div>

        <div v-else class="content-box">
          <div class="section-title-row">
            <div class="section-tag"><ShieldCheck :size="16" /> وضعیت نهایی</div>
          </div>

          <div class="result-box">
            <div class="result-head">
              <span :class="['status-badge', statusClass(statusMeta.label)]">{{ statusMeta.label }}</span>
            </div>
            <h3>درخواست شما ثبت شد</h3>
            <p>در حال بررسی توسط تیم احراز هویت. نتیجه نهایی پس از بررسی مدارک به شما اطلاع داده می‌شود.</p>
          </div>
        </div>

        <div class="security-note">
          <AlertTriangle :size="15" />
          اطلاعات شما تنها برای فرآیند احراز هویت استفاده می‌شود و در حفظ امنیت حساب شما نقش دارد.
        </div>

        <div class="modal-actions">
          <button v-if="currentStep > 1" type="button" class="secondary-btn" @click="prevStep">قبلی</button>
          <button v-if="currentStep < steps.length" type="button" class="primary-btn" @click="nextStep">بعدی</button>
          <button v-if="currentStep === steps.length" type="button" class="primary-btn">ثبت نهایی</button>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.kyc-shell {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  padding: 4px 4px 0;
}

.page-kicker {
  color: #f1d089;
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.page-title {
  margin: 8px 0 0;
  font-size: clamp(2rem, 3vw, 2.75rem);
  line-height: 1.15;
  letter-spacing: -0.04em;
  color: var(--text);
}

.page-subtitle {
  margin: 8px 0 0;
  color: var(--text-muted);
  font-size: 0.85rem;
}

.panel {
  background: var(--surface-card);
  border: 1px solid var(--border-subtle);
  border-radius: 26px;
  box-shadow: var(--shadow-card);
  backdrop-filter: blur(18px);
}

.status-panel,
.steps-panel,
.workflow-panel {
  padding: 24px;
}

.status-head,
.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 18px;
}

.panel-label {
  color: #a9b0c3;
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.status-head h2,
.panel-header h3 {
  margin: 6px 0 0;
  font-size: clamp(1.45rem, 1.8vw, 1.9rem);
  letter-spacing: -0.04em;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 28px;
  padding: 0 10px;
  border-radius: 999px;
  font-size: 0.68rem;
  font-weight: 700;
}

.status-badge.success {
  background: rgba(22,199,132,0.10);
  border: 1px solid rgba(22,199,132,0.18);
  color: #8ef1c2;
}

.status-badge.warning {
  background: rgba(212,169,90,0.10);
  border: 1px solid rgba(212,169,90,0.2);
  color: #f4d89a;
}

.status-badge.danger {
  background: rgba(234,57,67,0.10);
  border: 1px solid rgba(234,57,67,0.18);
  color: #f9b1b7;
}

.status-grid {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.status-main {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.status-copy {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: var(--text-soft);
  font-weight: 700;
}

.progress-meta {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 2px;
}

.progress-meta strong {
  font-size: 1.55rem;
  letter-spacing: -0.04em;
}

.progress-meta small {
  color: var(--text-muted);
  font-size: 0.7rem;
}

.progress-bar {
  width: 100%;
  height: 12px;
  border-radius: 999px;
  overflow: hidden;
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.06);
}

.progress-bar span {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, rgba(244,216,154,0.9), rgba(212,169,90,0.75));
}

.status-detail {
  margin: 0;
  color: var(--text-soft);
  line-height: 1.8;
  font-size: 0.82rem;
}

.kyc-grid {
  display: grid;
  grid-template-columns: minmax(280px, 0.8fr) minmax(0, 1.4fr);
  gap: 20px;
}

.kyc-steps {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.step-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 12px;
  border-radius: 16px;
  border: 1px solid rgba(255,255,255,0.06);
  background: rgba(255,255,255,0.02);
  transition: all 0.2s ease;
}

.step-item.done {
  border-color: rgba(22,199,132,0.18);
  background: rgba(22,199,132,0.04);
}

.step-item.active {
  border-color: rgba(212,169,90,0.32);
  background: rgba(212,169,90,0.05);
}

.step-number {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 10px;
  background: rgba(212,169,90,0.12);
  border: 1px solid rgba(212,169,90,0.18);
  color: #f4d89a;
  font-weight: 800;
  font-size: 0.8rem;
}

.step-text {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.step-text strong {
  color: var(--text);
  font-size: 0.84rem;
}

.step-text small {
  color: var(--text-muted);
  font-size: 0.68rem;
}

.workflow-panel {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.content-box {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.section-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.section-tag {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: #f4d89a;
  font-size: 0.78rem;
  font-weight: 700;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.field label {
  color: var(--text-soft);
  font-size: 0.8rem;
  font-weight: 700;
}

.premium-input {
  width: 100%;
  height: 52px;
  border-radius: 16px;
  padding: 0 16px;
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.08);
  color: var(--text);
  outline: none;
}

.premium-input:focus {
  border-color: rgba(212,169,90,0.38);
  box-shadow: 0 0 0 3px rgba(212,169,90,0.08);
}

.upload-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.upload-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  min-height: 180px;
  border-radius: 18px;
  background: rgba(255,255,255,0.02);
  border: 1px dashed rgba(255,255,255,0.12);
  color: var(--text-soft);
  text-align: center;
  padding: 16px;
}

.upload-icon {
  width: 42px;
  height: 42px;
  border-radius: 12px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: rgba(212,169,90,0.08);
  border: 1px solid rgba(212,169,90,0.18);
  color: #f4d89a;
}

.upload-box strong {
  color: var(--text);
  font-size: 0.9rem;
}

.upload-box small {
  color: var(--text-muted);
  font-size: 0.74rem;
}

.summary-box {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px;
  border-radius: 18px;
  background: rgba(255,255,255,0.02);
  border: 1px solid rgba(255,255,255,0.06);
}

.summary-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  color: var(--text-soft);
  font-size: 0.82rem;
}

.summary-row strong {
  color: var(--text);
}

.result-box {
  padding: 18px;
  border-radius: 18px;
  background: rgba(212,169,90,0.04);
  border: 1px solid rgba(212,169,90,0.15);
}

.result-head {
  margin-bottom: 12px;
}

.result-box h3 {
  margin: 0 0 8px;
  font-size: 1.3rem;
}

.result-box p {
  margin: 0;
  color: var(--text-soft);
  line-height: 1.8;
  font-size: 0.82rem;
}

.security-note {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  width: fit-content;
  padding: 10px 12px;
  border-radius: 12px;
  background: rgba(58,111,248,0.06);
  border: 1px solid rgba(58,111,248,0.16);
  color: var(--text-soft);
  font-size: 0.75rem;
  line-height: 1.7;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 6px;
}

.primary-btn,
.secondary-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 46px;
  padding: 0 18px;
  border-radius: 12px;
  font-weight: 700;
  transition: all 0.2s ease;
}

.primary-btn {
  border: 1px solid rgba(212,169,90,0.22);
  background: linear-gradient(135deg, #f2d89d, #d4a95a);
  color: #101827;
  box-shadow: 0 10px 26px rgba(212,169,90,0.22);
}

.secondary-btn {
  border: 1px solid rgba(212,169,90,0.24);
  background: rgba(212,169,90,0.06);
  color: #f3d99f;
}

.primary-btn:hover,
.secondary-btn:hover {
  transform: translateY(-1px);
}

@media (max-width: 1024px) {
  .kyc-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .status-head,
  .panel-header,
  .status-main,
  .modal-actions {
    flex-direction: column;
    align-items: flex-start;
  }

  .form-grid,
  .upload-grid {
    grid-template-columns: 1fr;
  }

  .status-panel,
  .steps-panel,
  .workflow-panel {
    padding: 18px 16px;
  }

  .security-note {
    width: 100%;
  }
}
</style>
