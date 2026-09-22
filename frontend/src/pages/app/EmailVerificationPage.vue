<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppButton from '@/components/ui/AppButton.vue'
import { userService } from '@/services/user.service'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const verifying = ref(true)
const success = ref(false)
const errorMessage = ref('')

const token = computed(() => {
  const value = route.query.token
  return typeof value === 'string' ? value : ''
})

async function verifyEmail(): Promise<void> {
  if (!token.value) {
    verifying.value = false
    errorMessage.value = 'لینک تأیید ایمیل معتبر نیست.'
    return
  }

  try {
    const updated = await userService.verifyEmail(token.value)

    auth.user = updated
    success.value = true
  } catch (error) {
    console.error(error)
    errorMessage.value = 'لینک تأیید ایمیل نامعتبر یا منقضی شده است.'
  } finally {
    verifying.value = false
  }
}

function goToProfile(): void {
  router.push('/app/profile')
}

onMounted(verifyEmail)
</script>

<template>
  <section class="email-verification-page">
    <div class="verification-card">
      <div v-if="verifying" class="verification-state">
        <div class="state-icon loading">
          <span class="spinner"></span>
        </div>

        <h1>در حال تأیید ایمیل</h1>
        <p>
          لطفاً چند لحظه صبر کنید...
        </p>
      </div>

      <div v-else-if="success" class="verification-state">
        <div class="state-icon success">
          ✓
        </div>

        <h1>ایمیل با موفقیت تأیید شد</h1>

        <p>
          نشانی ایمیل حساب شما با موفقیت تأیید شد.
        </p>

        <AppButton
          class="profile-button"
          @click="goToProfile"
        >
          بازگشت به پروفایل
        </AppButton>
      </div>

      <div v-else class="verification-state">
        <div class="state-icon error">
          !
        </div>

        <h1>تأیید ایمیل انجام نشد</h1>

        <p>
          {{ errorMessage }}
        </p>

        <AppButton
          class="profile-button"
          @click="goToProfile"
        >
          بازگشت به پروفایل
        </AppButton>
      </div>
    </div>
  </section>
</template>

<style scoped>
.email-verification-page {
  min-height: calc(100vh - 120px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem 1rem;
}

.verification-card {
  width: 100%;
  max-width: 32rem;
  padding: 2.5rem 2rem;
  border: 1px solid var(--border-color);
  border-radius: 1.25rem;
  background: var(--surface);
  text-align: center;
  box-shadow: var(--shadow-sm);
}

.verification-state {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.state-icon {
  width: 4.5rem;
  height: 4.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 1.25rem;
  border-radius: 50%;
  font-size: 2rem;
  font-weight: 700;
}

.state-icon.success {
  background: rgba(34, 197, 94, 0.12);
  color: #22c55e;
}

.state-icon.error {
  background: rgba(239, 68, 68, 0.12);
  color: #ef4444;
}

.state-icon.loading {
  background: var(--surface-soft);
}

.spinner {
  width: 2rem;
  height: 2rem;
  border: 3px solid var(--border-color);
  border-top-color: var(--primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

h1 {
  margin: 0 0 0.75rem;
  font-size: 1.35rem;
  font-weight: 700;
  color: var(--text-primary);
}

p {
  margin: 0;
  line-height: 1.8;
  color: var(--text-secondary);
}

.profile-button {
  margin-top: 1.5rem;
  min-width: 10rem;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>