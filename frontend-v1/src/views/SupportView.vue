<script setup>
import { computed, ref } from 'vue'
import { Clock3, LifeBuoy, MessageSquareText, Plus, Search, Send } from 'lucide-vue-next'
import { mockTickets } from '../mock/data'
import PremiumSelect from '../components/PremiumSelect.vue'

const searchQuery = ref('')
const subject = ref('')
const description = ref('')
const selectedTicket = ref(mockTickets[0])

const filteredTickets = computed(() => {
  const query = searchQuery.value.trim()
  if (!query) return mockTickets
  return mockTickets.filter((ticket) => `${ticket.subject} ${ticket.id}`.toLowerCase().includes(query.toLowerCase()))
})

const statusClass = (status) => {
  if (status === 'در انتظار پاسخ') return 'warning'
  if (status === 'پاسخ داده شد') return 'info'
  if (status === 'بسته') return 'success'
  return 'neutral'
}

const threads = {
  'TK-1042': [
    { sender: 'support', text: 'درخواست شما برای بررسی واریز اولیه ثبت شد. تیم بررسی تراکنش را آغاز کرده است.', time: 'امروز • ۱۴:۳۲' },
    { sender: 'user', text: 'تشکر، آیا می‌توانم زمان دقیق تکمیل را بدانم؟', time: 'امروز • ۱۴:۳۴' },
    { sender: 'support', text: 'در حال حاضر در صف بررسی است و معمولاً تا ۲ ساعت آینده نتیجه اعلام می‌شود.', time: 'امروز • ۱۴:۳۷' },
  ],
  'TK-1038': [
    { sender: 'support', text: 'در خصوص نرخ سفارش، به‌روزرسانی‌ها در بازار لحظه‌ای اعمال شده است.', time: 'دیروز • ۱۱:۲۸' },
    { sender: 'user', text: 'ممنون، برای سفارش بعدی با نرخ جاری اقدام می‌کنم.', time: 'دیروز • ۱۱:۳۱' },
  ],
  'TK-1035': [
    { sender: 'support', text: 'درخواست تغییر روش تسویه ثبت شد و در حال بررسی است.', time: '۳ روز قبل • ۱۰:۵۶' },
    { sender: 'user', text: 'با تشکر، لطفاً وضعیت را به من اطلاع دهید.', time: '۳ روز قبل • ۱۰:۵۸' },
  ],
}

const selectedConversation = computed(() => threads[selectedTicket.value.id] || [
  { sender: 'support', text: 'درخواست شما ثبت شد و تیم پشتیبانی در حال بررسی است.', time: 'همین حالا' },
])

const createTicket = () => {
  if (!subject.value.trim() || !description.value.trim()) return
  const generatedId = `TK-${Math.floor(Math.random() * 9000 + 1000)}`
  const ticket = {
    id: generatedId,
    subject: subject.value,
    status: 'در انتظار پاسخ',
    priority: 'متوسط',
    updated: 'همین حالا',
  }
  mockTickets.unshift(ticket)
  selectedTicket.value = ticket
  subject.value = ''
  description.value = ''
  threads[ticket.id] = [{ sender: 'support', text: 'درخواست جدید ثبت شد و پشتیبانی در حال بررسی است.', time: 'همین حالا' }]
}
</script>

<template>
  <div class="support-shell">
    <header class="page-header">
      <div>
        <div class="page-kicker">پلتفرم OTC</div>
        <h1 class="page-title">مرکز پشتیبانی</h1>
        <p class="page-subtitle">پاسخ‌گویی و پیگیری درخواست‌های شما</p>
      </div>
    </header>

    <section class="panel support-hero">
      <div class="hero-copy">
        <div class="hero-badge">
          <LifeBuoy :size="15" />
          نیاز به کمک دارید؟
        </div>
        <h2>درخواست خود را ثبت کنید یا سابقه تیکت‌ها را بررسی کنید.</h2>
      </div>

      <div class="hero-controls">
        <label class="search-wrap">
          <Search :size="16" />
          <input v-model="searchQuery" type="text" placeholder="جستجو در مرکز پشتیبانی..." />
        </label>
        <button type="button" class="primary-button" @click="selectedTicket = filteredTickets[0] || mockTickets[0]">
          <Plus :size="16" />
          ایجاد درخواست جدید
        </button>
      </div>
    </section>

    <div class="support-grid">
      <section class="panel ticket-panel">
        <div class="panel-head">
          <div>
            <div class="panel-label">درخواست‌ها</div>
            <h3>تیکت‌های من</h3>
          </div>
          <span class="inline-pill info">{{ filteredTickets.length }}</span>
        </div>

        <div class="ticket-list">
          <div
            v-for="ticket in filteredTickets"
            :key="ticket.id"
            :class="['ticket-row', { active: selectedTicket.id === ticket.id }]"
            @click="selectedTicket = ticket"
          >
            <div class="ticket-main">
              <div class="ticket-subject">{{ ticket.subject }}</div>
              <div class="ticket-meta">
                <span>{{ ticket.id }}</span>
                <span>•</span>
                <span>{{ ticket.updated }}</span>
              </div>
            </div>

            <div class="ticket-side">
              <span :class="['status-badge', statusClass(ticket.status)]">{{ ticket.status }}</span>
              <span class="priority-tag">{{ ticket.priority }}</span>
            </div>
          </div>
        </div>
      </section>

      <section class="panel form-panel">
        <div class="panel-head compact">
          <div>
            <div class="panel-label">ثبت درخواست</div>
            <h3>تیکت جدید</h3>
          </div>
        </div>

        <div class="form-stack">
          <label class="field">
            <span>موضوع</span>
            <input v-model="subject" class="premium-input" type="text" placeholder="موضوع درخواست" />
          </label>

          <label class="field">
            <span>اولویت</span>
            <PremiumSelect :model-value="'متوسط'" :options="[
              { value: 'پایین', label: 'پایین' },
              { value: 'متوسط', label: 'متوسط' },
              { value: 'بالا', label: 'بالا' },
            ]" placeholder="اولویت" />
          </label>

          <label class="field">
            <span>توضیحات</span>
            <textarea v-model="description" class="premium-textarea" placeholder="در خصوص مشکل یا سؤال خود توضیح دهید..."></textarea>
          </label>

          <button type="button" class="primary-button" @click="createTicket">
            <Send :size="15" />
            ارسال درخواست
          </button>
        </div>
      </section>
    </div>

    <section class="panel conversation-panel">
      <div class="panel-head conversation-head">
        <div>
          <div class="panel-label">گفت‌وگو</div>
          <h3>{{ selectedTicket.subject }}</h3>
        </div>
        <span class="inline-pill neutral">{{ selectedTicket.id }}</span>
      </div>

      <div class="conversation-box">
        <div v-for="message in selectedConversation" :key="`${message.sender}-${message.time}`" :class="['message-row', message.sender === 'user' ? 'outgoing' : 'incoming']">
          <div class="message-bubble">
            <div class="message-header">
              <span>{{ message.sender === 'user' ? 'شما' : 'پشتیبانی' }}</span>
              <time>{{ message.time }}</time>
            </div>
            <p>{{ message.text }}</p>
          </div>
        </div>
      </div>

      <div class="composer-wrap">
        <textarea class="premium-textarea composer" placeholder="پیام خود را بنویسید..." />
        <button type="button" class="primary-button send-button">
          <Send :size="15" />
          ارسال
        </button>
      </div>
    </section>
  </div>
</template>

<style scoped>
.support-shell {
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
  color: #d9b86a;
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.page-title {
  margin: 10px 0 0;
  font-size: clamp(2rem, 3vw, 2.8rem);
  line-height: 1.15;
  letter-spacing: -0.05em;
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

.support-hero,
.ticket-panel,
.form-panel,
.conversation-panel {
  padding: 24px;
}

.support-hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
}

.hero-copy {
  flex: 1;
}

.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-height: 32px;
  padding: 0 12px;
  border-radius: 999px;
  background: rgba(212, 169, 90, 0.08);
  border: 1px solid rgba(212, 169, 90, 0.2);
  color: #f0ce7b;
  font-size: 0.76rem;
  font-weight: 700;
}

.hero-copy h2 {
  margin: 14px 0 0;
  max-width: 700px;
  font-size: clamp(1.45rem, 2vw, 2rem);
  letter-spacing: -0.04em;
  line-height: 1.35;
}

.hero-controls {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
  min-width: min(100%, 430px);
}

.search-wrap {
  flex: 1;
  min-width: 200px;
  display: flex;
  align-items: center;
  gap: 10px;
  min-height: 48px;
  padding: 0 14px;
  border-radius: 14px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(255, 255, 255, 0.02);
  color: var(--text-muted);
}

.search-wrap:focus-within {
  border-color: rgba(212, 169, 90, 0.5);
  box-shadow: 0 0 0 3px rgba(212, 169, 90, 0.12);
}

.search-wrap input {
  width: 100%;
  border: 0;
  background: transparent;
  outline: none;
  color: var(--text);
  font-size: 0.9rem;
}

.search-wrap input::placeholder,
.premium-input::placeholder,
.premium-textarea::placeholder {
  color: var(--text-muted);
}

.primary-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 46px;
  padding: 0 18px;
  border-radius: 12px;
  border: 1px solid rgba(212, 169, 90, 0.28);
  background: linear-gradient(135deg, rgba(212, 169, 90, 0.2), rgba(212, 169, 90, 0.08));
  color: #f4d69c;
  font-weight: 800;
}

.support-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.5fr) minmax(0, 0.9fr);
  gap: 20px;
}

.panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 18px;
}

.panel-label {
  color: var(--text-muted);
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.panel-head h3 {
  margin: 6px 0 0;
  font-size: clamp(1.35rem, 1.7vw, 1.8rem);
  letter-spacing: -0.04em;
}

.ticket-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.ticket-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 14px;
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.05);
  background: rgba(255, 255, 255, 0.015);
  cursor: pointer;
  transition: all 0.18s ease;
}

.ticket-row:hover,
.ticket-row.active {
  background: rgba(212, 169, 90, 0.03);
  border-color: rgba(212, 169, 90, 0.18);
}

.ticket-main {
  min-width: 0;
}

.ticket-subject {
  color: var(--text);
  font-weight: 700;
  line-height: 1.5;
}

.ticket-meta {
  margin-top: 6px;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
  color: var(--text-muted);
  font-size: 0.72rem;
}

.ticket-side {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 8px;
}

.status-badge,
.inline-pill,
.priority-tag {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 28px;
  padding: 0 10px;
  border-radius: 999px;
  font-size: 0.68rem;
  font-weight: 700;
}

.status-badge.warning,
.inline-pill.info,
.priority-tag {
  background: rgba(212, 169, 90, 0.08);
  border: 1px solid rgba(212, 169, 90, 0.18);
  color: #e8c883;
}

.status-badge.info {
  background: rgba(58, 111, 248, 0.08);
  border: 1px solid rgba(58, 111, 248, 0.18);
  color: #8bb3ff;
}

.status-badge.success {
  background: rgba(22, 199, 132, 0.08);
  border: 1px solid rgba(22, 199, 132, 0.18);
  color: #9be5c1;
}

.status-badge.neutral,
.inline-pill.neutral {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: var(--text-soft);
}

.form-stack {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 9px;
}

.field span {
  color: var(--text-soft);
  font-size: 0.74rem;
  font-weight: 700;
}

.premium-input,
.premium-select,
.premium-textarea {
  width: 100%;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 14px;
  background: rgba(13, 23, 40, 0.9);
  color: var(--text);
  outline: none;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.premium-input,
.premium-select {
  min-height: 48px;
  padding: 0 14px;
}

.premium-textarea {
  min-height: 120px;
  padding: 12px 14px;
  resize: vertical;
}

.premium-input:focus,
.premium-select:focus,
.premium-textarea:focus {
  border-color: rgba(212, 169, 90, 0.6);
  box-shadow: 0 0 0 3px rgba(212, 169, 90, 0.12);
}

.conversation-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.conversation-head {
  margin-bottom: 0;
}

.conversation-box {
  display: flex;
  flex-direction: column;
  gap: 14px;
  min-height: 250px;
  padding: 18px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.message-row {
  display: flex;
}

.message-row.outgoing {
  justify-content: flex-end;
}

.message-bubble {
  max-width: 72%;
  padding: 12px 14px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.message-row.outgoing .message-bubble {
  background: rgba(212, 169, 90, 0.06);
  border-color: rgba(212, 169, 90, 0.18);
}

.message-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 8px;
  color: var(--text-soft);
  font-size: 0.72rem;
}

.message-bubble p {
  margin: 0;
  color: var(--text);
  font-size: 0.86rem;
  line-height: 1.7;
}

.composer-wrap {
  display: flex;
  align-items: flex-end;
  gap: 12px;
  padding-top: 8px;
}

.composer {
  flex: 1;
  min-height: 108px;
}

.send-button {
  flex: 0 0 auto;
}

@media (max-width: 1024px) {
  .support-hero {
    flex-direction: column;
    align-items: stretch;
  }

  .hero-controls {
    justify-content: stretch;
    min-width: 0;
  }

  .support-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .support-hero,
  .ticket-panel,
  .form-panel,
  .conversation-panel {
    padding: 18px 16px;
  }

  .ticket-row {
    flex-direction: column;
    align-items: flex-start;
  }

  .ticket-side {
    align-items: flex-start;
  }

  .message-bubble {
    max-width: 88%;
  }

  .composer-wrap {
    flex-direction: column;
  }

  .send-button {
    width: 100%;
  }
}
</style>
