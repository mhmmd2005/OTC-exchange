<!-- src/components/billing/BillingHistoryTable.vue -->
<script setup lang="ts">
import { ref, watch } from 'vue'
import { useBillingStore } from '@/stores/billing'

const billing = useBillingStore()

const headers = [
  { title: 'Date', value: 'created_at' },
  { title: 'Type', value: 'type' },
  { title: 'Status', value: 'status' },
  { title: 'Direction', value: 'direction' },
  { title: 'Amount', value: 'amount' },
  { title: 'Currency', value: 'currency' },
  { title: 'Provider', value: 'provider' },
  { title: 'Provider Ref', value: 'provider_ref' },
  { title: 'Ref ID', value: 'ref_id' },
  { title: 'Actions', value: 'actions', sortable: false },
]

const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const rows = ref<any[]>([])
const loading = ref(false)

const filters = ref<{ q?: string; status?: string; direction?: string; date_from?: string; date_to?: string }>({
  q: '', status: '', direction: '', date_from: '', date_to: '',
})

async function fetchRows() {
  loading.value = true
  try {
    const params: Record<string, any> = { page: page.value, page_size: pageSize.value }
    Object.entries(filters.value).forEach(([k, v]) => { if (v) params[k] = v })

    const data = await billing.getHistory(params)
    rows.value = (data?.results ?? data?.items ?? data?.data ?? []) as any[]
    total.value = Number(data?.count ?? data?.total ?? rows.value.length)
  } finally {
    loading.value = false
  }
}

watch([page, pageSize, filters], fetchRows, { deep: true, immediate: true })

function canPay(item: any) {
  const isTopup = item?.kind === 'FUNDING' || item?.ref_type === 'Top-up' || item?.ref_type === 'Funding'
  const pending = String(item?.status || '').toUpperCase()
  return isTopup && (pending === 'PENDING' || pending === 'PARTIAL') && !!item?.payment_url
}
function payNow(item: any) {
  if (item?.payment_url) window.open(item.payment_url, '_blank', 'noopener')
}

function formatMoney(x: string | number) {
  const n = typeof x === 'number' ? x : Number(x)
  if (Number.isNaN(n)) return String(x ?? '')
  return n.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

// ---- Date helpers ----
function parseAPIDate(val: string | Date | null | undefined): Date | null {
  if (!val) return null
  if (val instanceof Date) return val
  const s = String(val)
  const tzNoColon = /([+-]\d{2})(\d{2})$/
  const fixed = tzNoColon.test(s) ? s.replace(tzNoColon, (_m, h, m) => `${h}:${m}`) : s
  const d = new Date(fixed)
  return isNaN(d.getTime()) ? null : d
}

function formatDate(val: string | Date): string {
  const d = parseAPIDate(val)
  if (!d) return String(val ?? '')
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const hh = String(d.getHours()).padStart(2, '0')
  const mm = String(d.getMinutes()).padStart(2, '0')
  return `${y}/${m}/${day} ${hh}:${mm}`
}

// ---- Type display ----
function displayType(item: any): string {
  if (String(item?.kind).toUpperCase() === 'FUNDING') return 'Top-up'
  const t = String(item?.type || '')
  return t.replace(/\s*\(.*\)$/, '')
}
</script>

<template>
  <v-data-table
    :headers="headers"
    :items="rows"
    :items-length="total"
    v-model:page="page"
    v-model:items-per-page="pageSize"
    :loading="loading"
    class="elevation-1 compact-table"
  >
    <!-- Date -->
    <template #item.created_at="{ item }">
      <span class="text-no-wrap">{{ formatDate(item.created_at) }}</span>
    </template>

    <!-- Type -->
    <template #item.type="{ item }">
      <span>{{ displayType(item) }}</span>
    </template>

    <!-- Direction -->
    <template #item.direction="{ item }">
      <v-chip :color="item.direction === 'CREDIT' ? 'success' : 'error'" size="x-small">
        {{ item.direction }}
      </v-chip>
    </template>

    <!-- Amount -->
    <template #item.amount="{ item }">
      <span>{{ formatMoney(item.amount) }} {{ item.currency }}</span>
    </template>

    <!-- Provider Ref -->
    <template #item.provider_ref="{ item }">
      <span v-if="item.provider_ref" class="text-caption">
        <code>{{ item.provider_ref }}</code>
      </span>
      <span v-else class="text-disabled text-caption">—</span>
    </template>

    <!-- Ref ID -->
    <template #item.ref_id="{ item }">
      <span v-if="item.ref_id" class="text-caption">
        <code>{{ item.ref_id }}</code>
      </span>
      <span v-else class="text-disabled text-caption">—</span>
    </template>

    <!-- Actions -->
    <template #item.actions="{ item }">
      <v-btn
        v-if="canPay(item)"
        size="small"
        color="primary"
        variant="elevated"
        class="rounded-pill text-white font-weight-medium"
        prepend-icon="mdi-credit-card"
        @click="payNow(item)"
      >
        Continue Payment
      </v-btn>
    </template>
  </v-data-table>
</template>
