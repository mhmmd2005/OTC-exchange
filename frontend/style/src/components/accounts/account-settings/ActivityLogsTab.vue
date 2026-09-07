<script setup lang="ts">
import { onMounted, ref, computed, watch } from 'vue';
import { useAuthStore } from '@/stores/auth';
import { RefreshIcon, DeviceDesktopAnalyticsIcon, SearchIcon, DownloadIcon } from 'vue-tabler-icons';

type LogItem = {
  event_type: string;
  ip_address: string | null;
  country: string | null;
  user_agent: string | null;
  timestamp: string; // ISO
};

const auth = useAuthStore();

const loading = ref(false);
const errorMsg = ref<string | null>(null);
const logs = ref<LogItem[]>([]);

// table state
const headers = [
  { title: 'Time', value: 'timestamp', sortable: true },
  { title: 'Event', value: 'event_type', sortable: true },
  { title: 'IP', value: 'ip_address', sortable: true },
  { title: 'Country', value: 'country', sortable: true },
  { title: 'User Agent', value: 'user_agent', sortable: false },
];

const search = ref('');
const page = ref(1);
const itemsPerPage = ref(10);
const sortBy = ref<{ key: string; order: 'asc' | 'desc' }[]>([{ key: 'timestamp', order: 'desc' }]);

async function load() {
  loading.value = true;
  errorMsg.value = null;
  try {
    const data = await auth.getActivityLogs();
    // supports both plain array and paginated {results, count}
    logs.value = Array.isArray(data) ? data : Array.isArray(data?.results) ? data.results : [];
  } catch (e: any) {
    errorMsg.value = typeof e === 'string' ? e : (e?.detail || e?.message || 'Failed to load activity logs');
  } finally {
    loading.value = false;
  }
}

function fmtDate(iso: string) {
  try {
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return iso;
    return d.toLocaleString();
  } catch {
    return iso;
  }
}

const csvData = computed(() => {
  const rows = [['Time', 'Event', 'IP', 'Country', 'User Agent']];
  for (const r of logs.value) {
    rows.push([fmtDate(r.timestamp), r.event_type || '', r.ip_address || '', r.country || '', r.user_agent || '']);
  }
  return rows.map((r) => r.map(v => `"${String(v).replace(/"/g, '""')}"`).join(',')).join('\n');
});

function downloadCSV() {
  const blob = new Blob([csvData.value], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `activity-logs-${new Date().toISOString().slice(0,10)}.csv`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

onMounted(load);

// reset to first page on search change
watch(search, () => { page.value = 1; });
</script>

<template>
  <v-card elevation="10">
    <v-card-item>
      <div class="d-flex align-center justify-space-between">
        <div class="d-flex align-center">
          <DeviceDesktopAnalyticsIcon class="mr-2" />
          <h5 class="text-h5">Activity Logs</h5>
        </div>
        <div class="d-flex ga-2">
          <v-btn variant="text" :disabled="loading" @click="load" rounded="pill">
            <RefreshIcon size="18" class="mr-1" /> Refresh
          </v-btn>
          <v-btn variant="tonal" color="primary" :disabled="!logs.length" @click="downloadCSV" rounded="pill">
            <DownloadIcon size="18" class="mr-1" /> Export CSV
          </v-btn>
        </div>
      </div>
      <div class="text-subtitle-1 text-grey100 mt-2">
        Recent sign-ins and security events for your account.
      </div>
    </v-card-item>

    <v-divider />

    <v-card-text>
      <v-alert v-if="errorMsg" type="error" class="mb-4" variant="tonal">{{ errorMsg }}</v-alert>

      <div class="d-flex align-center justify-space-between mb-3">
        <v-text-field
          v-model="search"
          prepend-inner-icon="mdi-magnify"
          label="Search logs"
          placeholder="Filter by event, IP, country, agent..."
          variant="outlined"
          density="comfortable"
          hide-details="auto"
          clearable
          class="mr-2"
        />
        <div class="d-flex align-center">
          <span class="text-caption mr-2">Rows:</span>
          <v-select
            v-model="itemsPerPage"
            :items="[5,10,20,50]"
            density="compact"
            variant="outlined"
            style="max-width: 90px"
            hide-details
          />
        </div>
      </div>

      <div v-if="loading" class="py-10 text-center">
        <v-progress-circular indeterminate />
      </div>

      <div v-else>
        <v-data-table
          :headers="headers"
          :items="logs"
          :search="search"
          :page.sync="page"
          :items-per-page="itemsPerPage"
          :sort-by="sortBy"
          class="elevation-1"
          hover
          density="comfortable"
        >
          <template #item.timestamp="{ item }">
            {{ fmtDate(item.timestamp) }}
          </template>
          <template #item.event_type="{ item }">
            <v-chip size="small" :color="item.event_type?.includes('fail') ? 'error' : 'primary'" variant="tonal">
              {{ item.event_type }}
            </v-chip>
          </template>
          <template #no-data>
            <div class="text-body-2 py-6 text-center">No activity found.</div>
          </template>
        </v-data-table>
      </div>
    </v-card-text>
  </v-card>
</template>
