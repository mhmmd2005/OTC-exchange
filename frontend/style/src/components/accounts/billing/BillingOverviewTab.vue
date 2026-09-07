<!-- src/components/billing/BillingOverviewTab.vue -->
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useBillingStore } from '@/stores/billing'

type Overview = {
  wallet_balance: string
  charges_this_month: string
  remaining_credit: string
  currency: string
}

const billing = useBillingStore()
const loading = ref(true)
const data = ref<Overview | null>(null)
const errorMsg = ref('')

onMounted(async () => {
  try {
    const o = await billing.getOverview()
    data.value = o as Overview
  } catch (e: any) {
    errorMsg.value =
      typeof e === 'string' ? e : (e?.detail || e?.message || 'Failed to load overview')
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div>
    <v-skeleton-loader v-if="loading" type="card, list-item, list-item, list-item" />
    <div v-else>
      <v-alert v-if="errorMsg" type="error" class="mb-4">{{ errorMsg }}</v-alert>

      <v-row v-if="data">
        <v-col cols="12" md="4">
          <v-card class="pa-4" elevation="2">
            <div class="text-caption">Charges This Month</div>
            <div class="text-h5">{{ data.currency }} {{ data.charges_this_month }}</div>
          </v-card>
        </v-col>
        <v-col cols="12" md="4">
          <v-card class="pa-4" elevation="2">
            <div class="text-caption">Remaining Credit</div>
            <div class="text-h5">{{ data.currency }} {{ data.remaining_credit }}</div>
          </v-card>
        </v-col>
        <v-col cols="12" md="4">
          <v-card class="pa-4" elevation="2">
            <div class="text-caption">Account Balance</div>
            <div class="text-h5">{{ data.currency }} {{ data.wallet_balance }}</div>
          </v-card>
        </v-col>
      </v-row>
    </div>
  </div>
</template>
