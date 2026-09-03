<script setup>
import { mockSecurity } from '../mock/data'
import { AlertTriangle, CheckCircle2, KeyRound, LockKeyhole, Monitor, ShieldCheck, Smartphone } from 'lucide-vue-next'

const securityMethods = [
  { label: 'رمز عبور', status: 'فعال', hint: 'آخرین تغییر: ۳ روز پیش', action: 'تغییر رمز', icon: LockKeyhole },
  { label: 'احراز هویت دو مرحله‌ای', status: 'فعال', hint: 'کد یک‌بار مصرف فعال است', action: 'مدیریت', icon: ShieldCheck },
  { label: 'تأیید شماره موبایل', status: 'فعال', hint: 'تأیید شده در ۱۴۰۳/۰۵/۲۱', action: 'مشاهده', icon: Smartphone },
  { label: 'تأیید ایمیل', status: 'فعال', hint: 'آخرین تأیید: همین حالا', action: 'مدیریت', icon: KeyRound },
]
</script>

<template>
  <div class="security-shell">
    <header class="page-header">
      <div>
        <div class="page-kicker">پلتفرم OTC</div>
        <h1 class="page-title">امنیت</h1>
        <p class="page-subtitle">مدیریت و بررسی امنیت حساب کاربری</p>
      </div>
    </header>

    <section class="panel security-summary">
      <div class="summary-head">
        <div>
          <div class="panel-label">وضعیت امنیت حساب</div>
          <h2>امنیت حساب</h2>
        </div>
        <span class="status-badge success">ایمن</span>
      </div>

      <div class="summary-body">
        <div class="shield-wrap">
          <div class="shield-icon">
            <ShieldCheck :size="28" />
          </div>
        </div>

        <div class="summary-copy">
          <div class="score-row">
            <strong>۸۰٪</strong>
            <small>سطح امنیت</small>
          </div>
          <p>حساب شما در سطح امن قرار دارد. برخی اقدامات پیشنهادی برای افزایش سطح حفاظت در دسترس هستند.</p>
        </div>
      </div>
    </section>

    <div class="security-grid">
      <section class="panel methods-panel">
        <div class="panel-header compact">
          <div>
            <div class="panel-label">روش‌های امنیتی</div>
            <h3>حفاظت حساب</h3>
          </div>
        </div>

        <div class="security-list">
          <div v-for="method in securityMethods" :key="method.label" class="security-row">
            <div class="row-main">
              <div class="row-icon">
                <component :is="method.icon" :size="18" />
              </div>
              <div class="row-copy">
                <strong>{{ method.label }}</strong>
                <small>{{ method.hint }}</small>
              </div>
            </div>

            <div class="row-side">
              <span class="method-status">{{ method.status }}</span>
              <button type="button" class="method-action">{{ method.action }}</button>
            </div>
          </div>
        </div>
      </section>

      <section class="panel action-panel">
        <div class="panel-header compact">
          <div>
            <div class="panel-label">اقدامات</div>
            <h3>تنظیمات امنیتی</h3>
          </div>
        </div>

        <div class="action-stack">
          <div class="action-card">
            <div class="action-main">
              <div class="action-icon"><KeyRound :size="17" /></div>
              <div>
                <strong>تغییر رمز عبور</strong>
                <small>آخرین به‌روزرسانی: ۳ روز پیش</small>
              </div>
            </div>
            <button type="button" class="secondary-btn">تغییر</button>
          </div>

          <div class="action-card">
            <div class="action-main">
              <div class="action-icon"><ShieldCheck :size="17" /></div>
              <div>
                <strong>احراز هویت دو مرحله‌ای</strong>
                <small>کد یک‌بار مصرف فعال است</small>
              </div>
            </div>
            <button type="button" class="secondary-btn">مدیریت</button>
          </div>

          <div class="action-card warning-card">
            <div class="action-main">
              <div class="action-icon"><AlertTriangle :size="17" /></div>
              <div>
                <strong>پیشنهاد امنیتی</strong>
                <small>نشست‌های ناشناس را بررسی کنید</small>
              </div>
            </div>
            <button type="button" class="secondary-btn">بررسی</button>
          </div>
        </div>
      </section>
    </div>

    <div class="security-grid bottom-grid">
      <section class="panel session-panel">
        <div class="panel-header compact">
          <div>
            <div class="panel-label">نشست‌ها</div>
            <h3>نشست‌های فعال</h3>
          </div>
        </div>

        <div class="list-block">
          <div v-for="session in mockSecurity.activeSessions" :key="session.ip" class="list-item">
            <div class="list-main">
              <div class="device-icon"><Monitor :size="16" /></div>
              <div>
                <strong>{{ session.device }}</strong>
                <small>{{ session.location }} • {{ session.ip }}</small>
              </div>
            </div>
            <span :class="['session-tag', session.status === 'فعال' ? 'active' : 'inactive']">{{ session.status }}</span>
          </div>
        </div>
      </section>

      <section class="panel history-panel">
        <div class="panel-header compact">
          <div>
            <div class="panel-label">ثبت‌ها</div>
            <h3>تاریخچه ورود</h3>
          </div>
        </div>

        <div class="list-block">
          <div v-for="item in mockSecurity.loginHistory" :key="item.time" class="list-item">
            <div class="list-main">
              <div class="device-icon"><CheckCircle2 :size="16" /></div>
              <div>
                <strong>{{ item.time }}</strong>
                <small>{{ item.location }} • {{ item.ip }}</small>
              </div>
            </div>
            <span class="session-tag active">ورود موفق</span>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.security-shell {
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

.security-summary,
.methods-panel,
.action-panel,
.session-panel,
.history-panel {
  padding: 24px;
}

.summary-head,
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

.summary-head h2,
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

.summary-body {
  display: grid;
  grid-template-columns: 100px minmax(0, 1fr);
  gap: 18px;
  align-items: center;
}

.shield-wrap {
  display: flex;
  align-items: center;
  justify-content: center;
}

.shield-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 82px;
  height: 82px;
  border-radius: 22px;
  background: rgba(212,169,90,0.08);
  border: 1px solid rgba(212,169,90,0.18);
  color: #f4d89a;
}

.summary-copy {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.score-row {
  display: flex;
  align-items: baseline;
  gap: 10px;
}

.score-row strong {
  font-size: clamp(2rem, 2.8vw, 2.8rem);
  letter-spacing: -0.05em;
  color: var(--text);
}

.score-row small {
  color: var(--text-muted);
  font-size: 0.75rem;
}

.summary-copy p {
  margin: 0;
  color: var(--text-soft);
  line-height: 1.8;
  font-size: 0.82rem;
}

.security-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.3fr) minmax(0, 0.9fr);
  gap: 20px;
}

.security-list,
.list-block,
.action-stack {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.security-row,
.list-item,
.action-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 12px;
  border-radius: 16px;
  background: rgba(255,255,255,0.02);
  border: 1px solid rgba(255,255,255,0.06);
}

.row-main,
.list-main,
.action-main {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.row-icon,
.device-icon,
.action-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  border-radius: 10px;
  background: rgba(212,169,90,0.08);
  border: 1px solid rgba(212,169,90,0.18);
  color: #f4d89a;
}

.row-copy,
.action-main > div,
.list-main > div {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.row-copy strong,
.action-main strong,
.list-main strong {
  color: var(--text);
  font-size: 0.84rem;
}

.row-copy small,
.action-main small,
.list-main small {
  color: var(--text-muted);
  font-size: 0.66rem;
}

.row-side {
  display: flex;
  align-items: center;
  gap: 10px;
}

.method-status {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 28px;
  padding: 0 10px;
  border-radius: 999px;
  background: rgba(22,199,132,0.10);
  border: 1px solid rgba(22,199,132,0.18);
  color: #8ef1c2;
  font-size: 0.68rem;
  font-weight: 700;
}

.method-action,
.secondary-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 36px;
  padding: 0 12px;
  border-radius: 12px;
  border: 1px solid rgba(212,169,90,0.24);
  background: rgba(212,169,90,0.06);
  color: #f3d99f;
  font-weight: 700;
}

.action-card.warning-card {
  border-color: rgba(212,169,90,0.2);
  background: rgba(212,169,90,0.04);
}

.warning-card .action-icon {
  background: rgba(212,169,90,0.12);
}

.session-tag {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 28px;
  padding: 0 10px;
  border-radius: 999px;
  font-size: 0.68rem;
  font-weight: 700;
}

.session-tag.active {
  background: rgba(22,199,132,0.10);
  border: 1px solid rgba(22,199,132,0.18);
  color: #8ef1c2;
}

.session-tag.inactive {
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.08);
  color: #dfe7ff;
}

.bottom-grid {
  margin-top: 0;
}

@media (max-width: 980px) {
  .security-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .summary-head,
  .panel-header,
  .security-row,
  .list-item,
  .action-card {
    flex-direction: column;
    align-items: flex-start;
  }

  .summary-body {
    grid-template-columns: 1fr;
  }

  .row-side,
  .action-card .secondary-btn,
  .method-action {
    width: 100%;
    justify-content: center;
  }

  .security-summary,
  .methods-panel,
  .action-panel,
  .session-panel,
  .history-panel {
    padding: 18px 16px;
  }
}
</style>
