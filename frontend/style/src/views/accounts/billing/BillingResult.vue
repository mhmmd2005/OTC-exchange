<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useBillingStore } from '@/stores/billing'

type Mode = 'success' | 'cancel'
const props = defineProps<{ mode?: Mode }>()
const mode = props.mode || 'success'

const route = useRoute()
const router = useRouter()
const billing = useBillingStore()

const loading = ref(true)
const errorMsg = ref('')
const // core data
  status = ref<'PENDING'|'PARTIAL'|'PAID'|'FAILED'|'EXPIRED'|string>('PENDING'),
  verified = ref(false),
  credited = ref(false),
  fundingId = ref<number | null>(null),
  amount = ref<string>('0.00'),
  currency = ref<string>('USD'),
  provider = ref<string>('NOWPAY'),
  invoiceId = ref<string | null>(null),
  paymentId = ref<string | null>(null),
  paymentUrl = ref<string | null>(null),
  completedAt = ref<string | null>(null)

const // polling
  pollTimer = ref<number | null>(null),
  tries = ref(0),
  backoffMs = ref(4000), // start ~4s, will grow
  nextIn = ref(Math.floor(backoffMs.value / 1000)),
  tickTimer = ref<number | null>(null)

const isWaiting = computed(() =>
  !credited.value && (status.value === 'PENDING' || status.value === 'PARTIAL')
)
const isTerminalFailure = computed(() => status.value === 'FAILED' || status.value === 'EXPIRED')
const isTerminalSuccess = computed(() => credited.value && status.value === 'PAID')

const headline = computed(() => {
  if (isTerminalSuccess.value) return 'Payment confirmed'
  if (isTerminalFailure.value) return status.value === 'FAILED' ? 'Payment failed' : 'Invoice expired'
  return mode === 'cancel' ? 'Payment not completed yet' : 'Waiting for confirmations'
})

const headlineIcon = computed(() => {
  if (isTerminalSuccess.value) return 'mdi-check-decagram'
  if (isTerminalFailure.value) return 'mdi-close-octagon'
  return 'mdi-timer-sand'
})
const headlineColor = computed(() => {
  if (isTerminalSuccess.value) return 'success'
  if (isTerminalFailure.value) return 'error'
  return 'info'
})

async function fetchOnce() {
  try {
    const q = route.query
    const data = await billing.getTopupResult({
      payment_id: (q.payment_id || q.NP_id || q.id) as string | undefined,
      order_id: q.order_id as string | undefined,
      invoice_id: q.invoice_id as string | undefined,
      funding_id: q.funding_id as string | undefined,
    })

    status.value = data?.status || 'PENDING'
    verified.value = !!data?.verified
    credited.value = !!data?.credited
    fundingId.value = data?.funding_id ?? null
    amount.value = data?.amount || '0.00'
    currency.value = data?.currency || 'USD'
    provider.value = data?.provider || 'NOWPAY'
    invoiceId.value = data?.invoice_id || null
    paymentId.value = data?.payment_id || null
    paymentUrl.value = data?.payment_url || null
    completedAt.value = data?.completed_at || null

    errorMsg.value = ''
    return true
  } catch (e: any) {
    errorMsg.value = e?.message || 'Failed to load payment result'
    return false
  } finally {
    loading.value = false
  }
}

function startBackoffPolling() {
  stopPolling()
  if (!isWaiting.value) return
  tries.value = 0
  backoffMs.value = 4000
  scheduleNext()
  startSecondTicker()
}

function scheduleNext() {
  if (!isWaiting.value) return
  nextIn.value = Math.floor(backoffMs.value / 1000)
  pollTimer.value = window.setTimeout(async () => {
    tries.value += 1
    await fetchOnce()
    if (isWaiting.value && tries.value < 40) {
      // grow backoff up to ~30s
      backoffMs.value = Math.min(Math.floor(backoffMs.value * 1.5), 30000)
      scheduleNext()
    } else {
      stopPolling()
    }
  }, backoffMs.value)
}

function startSecondTicker() {
  stopTicker()
  tickTimer.value = window.setInterval(() => {
    if (nextIn.value > 0) nextIn.value -= 1
  }, 1000)
}

function stopPolling() {
  if (pollTimer.value) { clearTimeout(pollTimer.value); pollTimer.value = null }
  stopTicker()
}
function stopTicker() {
  if (tickTimer.value) { clearInterval(tickTimer.value); tickTimer.value = null }
}

function toBilling() { router.push('/billing') }
function openPayment() { if (paymentUrl.value) window.open(paymentUrl.value, '_blank', 'noopener') }

async function copy(text?: string | null) {
  if (!text) return
  try { await navigator.clipboard.writeText(text) } catch {}
}

onMounted(async () => {
  await fetchOnce()
  startBackoffPolling()
})
onBeforeUnmount(() => { stopPolling() })

const steps = computed(() => {
  // basic 4-step timeline
  const s = status.value
  const created = true
  const initiated = !!invoiceId.value || !!paymentId.value
  const confirming = s === 'PENDING' || s === 'PARTIAL'
  const done = credited.value || s === 'PAID'
  const failed = isTerminalFailure.value

  return [
    { title: 'Created', active: created, icon: 'mdi-file-document-outline' },
    { title: 'Payment initiated', active: initiated, icon: 'mdi-open-in-new' },
    { title: failed ? 'Stopped' : 'Confirmations', active: confirming || done || failed, icon: failed ? 'mdi-close-octagon' : 'mdi-timer-sand' },
    { title: failed ? 'Not credited' : 'Credited', active: done, icon: failed ? 'mdi-cancel' : 'mdi-check-circle' },
  ]
})
</script>

<template>
  <v-container class="py-8" style="max-width: 980px;">
    <v-card class="rounded-2xl pa-6" :loading="loading">
      <div class="d-flex align-center">
        <v-avatar size="44" :color="headlineColor" variant="tonal" class="mr-3">
          <v-icon :icon="headlineIcon" size="28" />
        </v-avatar>
        <div class="mr-4">
          <div class="text-h6">{{ headline }}</div>
          <div class="text-body-2 text-medium-emphasis">
            <span v-if="isWaiting">
              Waiting for network confirmations
              <span v-if="nextIn>0">· next check in {{ nextIn }}s</span>
            </span>
            <span v-else-if="isTerminalSuccess">Wallet has been credited</span>
            <span v-else-if="isTerminalFailure">Payment not finalized</span>
          </div>
        </div>
        <v-spacer />
        <v-chip v-if="fundingId" size="small" variant="elevated" class="font-mono">Funding #{{ fundingId }}</v-chip>
      </div>

      <v-alert v-if="errorMsg" type="error" variant="tonal" class="mt-4 rounded-lg">
        {{ errorMsg }}
      </v-alert>

      <v-row class="mt-6" v-else>
        <!-- Left: summary -->
        <v-col cols="12" md="7">
          <v-card class="rounded-xl mb-4" variant="outlined">
            <v-card-text>
              <div class="d-flex align-center mb-3">
                <v-icon icon="mdi-receipt-text" class="mr-2" />
                <div class="text-subtitle-1 font-weight-medium">Summary</div>
                <v-spacer />
                <v-chip size="small" :color="verified ? 'success' : 'grey'" variant="tonal">
                  <v-icon :icon="verified ? 'mdi-shield-check' : 'mdi-shield-off-outline'" size="16" class="mr-1" />
                  {{ verified ? 'IPN verified' : 'Awaiting IPN' }}
                </v-chip>
              </div>

              <v-list density="compact" lines="one">
                <v-list-item>
                  <template #prepend><v-icon icon="mdi-cash" /></template>
                  <v-list-item-title>Amount</v-list-item-title>
                  <v-list-item-subtitle class="font-mono">
                    {{ amount }} {{ currency }}
                  </v-list-item-subtitle>
                </v-list-item>

                <v-list-item>
                  <template #prepend><v-icon icon="mdi-bank" /></template>
                  <v-list-item-title>Provider</v-list-item-title>
                  <v-list-item-subtitle>{{ provider }}</v-list-item-subtitle>
                </v-list-item>

                <v-list-item v-if="invoiceId">
                  <template #prepend><v-icon icon="mdi-file-key-outline" /></template>
                  <v-list-item-title>Invoice ID</v-list-item-title>
                  <v-list-item-subtitle class="font-mono">
                    {{ invoiceId }}
                    <v-btn icon size="x-small" variant="text" @click="copy(invoiceId)"><v-icon icon="mdi-content-copy" size="16"/></v-btn>
                  </v-list-item-subtitle>
                </v-list-item>

                <v-list-item v-if="paymentId">
                  <template #prepend><v-icon icon="mdi-key-link" /></template>
                  <v-list-item-title>Payment ID</v-list-item-title>
                  <v-list-item-subtitle class="font-mono">
                    {{ paymentId }}
                    <v-btn icon size="x-small" variant="text" @click="copy(paymentId)"><v-icon icon="mdi-content-copy" size="16"/></v-btn>
                  </v-list-item-subtitle>
                </v-list-item>

                <v-list-item>
                  <template #prepend><v-icon icon="mdi-information-outline" /></template>
                  <v-list-item-title>Status</v-list-item-title>
                  <v-list-item-subtitle class="text-uppercase">
                    {{ status }}
                    <span v-if="completedAt"> · completed at {{ completedAt }}</span>
                  </v-list-item-subtitle>
                </v-list-item>
              </v-list>

              <v-expand-transition>
                <v-alert
                  v-if="isWaiting"
                  type="info"
                  class="mt-3 rounded-lg"
                  variant="tonal"
                >
                  Crypto payments can take a few minutes to confirm. This page refreshes automatically.
                </v-alert>
              </v-expand-transition>
            </v-card-text>
          </v-card>

          <v-card class="rounded-xl" variant="outlined">
            <v-card-text>
              <div class="text-subtitle-1 font-weight-medium mb-3">Status</div>
              <div class="d-flex flex-wrap">
                <div
                  v-for="(step, i) in steps"
                  :key="i"
                  class="d-flex align-center mr-6 mb-3"
                >
                  <v-avatar size="28" :color="step.active ? 'primary' : 'grey'" variant="tonal" class="mr-2">
                    <v-icon :icon="step.icon" size="18" />
                  </v-avatar>
                  <div class="text-body-2">{{ step.title }}</div>
                </div>
              </div>
            </v-card-text>
          </v-card>
        </v-col>

        <!-- Right: actions -->
        <v-col cols="12" md="5">
          <v-card class="rounded-xl" elevation="2">
            <v-card-text>
              <div class="text-subtitle-1 font-weight-medium mb-3">Actions</div>

              <v-btn
                color="primary"
                class="mb-2"
                block
                size="large"
                prepend-icon="mdi-view-dashboard"
                @click="toBilling"
              >Go to Billing</v-btn>

              <v-btn
                v-if="isWaiting && paymentUrl"
                variant="tonal"
                class="mb-2"
                block
                size="large"
                prepend-icon="mdi-open-in-new"
                @click="openPayment"
              >Open Payment Page</v-btn>

              <v-btn
                v-if="isTerminalFailure"
                color="error"
                variant="tonal"
                class="mb-2"
                block
                size="large"
                prepend-icon="mdi-reload"
                @click="toBilling"
              >Try Again</v-btn>

              <v-divider class="my-4" />

              <div class="text-caption text-medium-emphasis">
                This page uses secure server-side webhooks to confirm payments. Refreshing won't duplicate charges.
              </div>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
    </v-card>
  </v-container>
</template>
