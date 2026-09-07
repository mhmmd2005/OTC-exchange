<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import type { AssetNetwork, DepositAddress, Transaction } from '@/types'
import { transactionService } from '@/services/transaction.service'
import { walletService } from '@/services/wallet.service'
import { useWalletStore } from '@/stores/wallet'
import { formatCrypto, toPersianDigits } from '@/utils/formatters'
import AppButton from '@/components/ui/AppButton.vue'
import AppCard from '@/components/ui/AppCard.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import AppSkeleton from '@/components/ui/AppSkeleton.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import AssetAvatar from '@/components/finance/AssetAvatar.vue'
import AssetSelect from '@/components/finance/AssetSelect.vue'
import TransactionList from '@/components/transactions/TransactionList.vue'
import DepositAddressCard from '@/components/wallet/DepositAddressCard.vue'
import NetworkSelector from '@/components/wallet/NetworkSelector.vue'

const route = useRoute()
const router = useRouter()
const walletStore = useWalletStore()
const selectedSymbol = ref('')
const networks = ref<AssetNetwork[]>([])
const networkCode = ref('')
const depositAddress = ref<DepositAddress | null>(null)
const transactions = ref<Transaction[]>([])
const loading = ref(true)
const addressLoading = ref(false)
const error = ref('')
const addressError = ref('')
const historyError = ref('')
let assetRequestSequence = 0
let addressRequestSequence = 0
let historyRequestSequence = 0
let walletReady = false

const cryptoAssets = computed(() => walletStore.assets.filter((asset) => asset.symbol !== 'IRT'))
const assetBalances = computed<Record<string, string>>(() => Object.fromEntries(
  cryptoAssets.value.map((asset) => [asset.symbol, asset.available]),
))
const disabledAssetSymbols = computed(() => cryptoAssets.value
  .filter((asset) => !asset.depositEnabled)
  .map((asset) => asset.symbol))
const disabledAssetDescriptions = computed<Record<string, string>>(() => Object.fromEntries(
  disabledAssetSymbols.value.map((symbol) => [symbol, 'واریز این ارز موقتاً غیرفعال است']),
))
const selectedAsset = computed(() => cryptoAssets.value.find((asset) => asset.symbol === selectedSymbol.value))
const selectedNetwork = computed(() => networks.value.find((network) => network.code === networkCode.value))
const historyTitle = computed(() => selectedNetwork.value
  ? `واریزهای اخیر ${selectedAsset.value?.nameFa ?? ''} روی شبکه ${selectedNetwork.value.displayName}`
  : `واریزهای اخیر ${selectedAsset.value?.nameFa ?? ''}`)
const selectableNetwork = (network: AssetNetwork) => network.depositEnabled
  && network.status !== 'maintenance'
  && network.status !== 'disabled'

function requestedRouteSymbol(): string {
  return String(route.params.symbol || '').toUpperCase()
}

function resolveAssetSymbol(): string {
  const requestedAsset = cryptoAssets.value.find((asset) => asset.symbol === requestedRouteSymbol())
  return requestedAsset?.symbol
    || cryptoAssets.value.find((asset) => asset.depositEnabled)?.symbol
    || cryptoAssets.value[0]?.symbol
    || ''
}

function syncAssetRoute(symbol: string) {
  if (!symbol || requestedRouteSymbol() === symbol) return
  void router.replace({ name: 'crypto-deposit', params: { symbol }, query: { ...route.query } })
}

function syncDepositRoute(symbol: string, code = networkCode.value) {
  if (!symbol) return
  const query = { ...route.query }
  if (code) query.network = code
  else delete query.network
  if (requestedRouteSymbol() === symbol && String(route.query.network || '') === code) return
  void router.replace({ name: 'crypto-deposit', params: { symbol }, query })
}

async function loadDepositAddress() {
  const symbol = selectedSymbol.value
  const code = networkCode.value
  const requestId = ++addressRequestSequence
  depositAddress.value = null
  addressError.value = ''
  if (!symbol || !code) return
  addressLoading.value = true
  try {
    const response = await walletService.getDepositAddress(symbol, code)
    if (requestId === addressRequestSequence) depositAddress.value = response
  } catch (caught) {
    if (requestId === addressRequestSequence) {
      addressError.value = caught instanceof Error ? caught.message : 'آدرس واریز آماده نشد.'
    }
  } finally {
    if (requestId === addressRequestSequence) addressLoading.value = false
  }
}

async function loadHistory() {
  const symbol = selectedSymbol.value
  const code = networkCode.value
  const requestId = ++historyRequestSequence
  transactions.value = []
  historyError.value = ''
  if (!symbol || !code) return
  try {
    const response = await transactionService.list({
      type: 'crypto_deposit',
      assetSymbol: symbol,
      networkCode: code,
      pageSize: 5,
    })
    if (requestId === historyRequestSequence) transactions.value = response.items
  } catch (caught) {
    if (requestId === historyRequestSequence) {
      historyError.value = caught instanceof Error ? caught.message : 'سابقه واریزها دریافت نشد.'
    }
  }
}

function selectNetwork(code: string) {
  if (networkCode.value === code) return
  const requestedNetwork = networks.value.find((network) => network.code === code)
  if (!requestedNetwork || !selectableNetwork(requestedNetwork)) return
  networkCode.value = code
  syncDepositRoute(selectedSymbol.value, code)
  void loadDepositAddress()
  void loadHistory()
}

async function loadAssetData() {
  const symbol = selectedSymbol.value
  const requestId = ++assetRequestSequence
  addressRequestSequence += 1
  historyRequestSequence += 1
  networks.value = []
  networkCode.value = ''
  depositAddress.value = null
  transactions.value = []
  addressError.value = ''
  if (!symbol) return
  loading.value = true
  error.value = ''
  try {
    const networkResult = await walletService.getNetworks(symbol)
    if (requestId !== assetRequestSequence) return
    networks.value = networkResult
    const routeNetwork = String(route.query.network || '').toUpperCase()
    const preferredNetwork = networkResult.find(
      (network) => network.code === routeNetwork && selectableNetwork(network),
    )
    networkCode.value = preferredNetwork?.code || networkResult.find(selectableNetwork)?.code || ''
    syncDepositRoute(symbol, networkCode.value)
    if (networkCode.value) await Promise.all([loadDepositAddress(), loadHistory()])
  } catch (caught) {
    if (requestId === assetRequestSequence) {
      error.value = caught instanceof Error ? caught.message : 'اطلاعات واریز رمزارز دریافت نشد.'
    }
  } finally {
    if (requestId === assetRequestSequence) loading.value = false
  }
}

async function initialize() {
  loading.value = true
  error.value = ''
  try {
    await walletStore.fetchWallet()
    walletReady = true
    selectedSymbol.value = resolveAssetSymbol()
    if (!selectedSymbol.value) loading.value = false
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : 'کیف پول بارگیری نشد.'
    loading.value = false
  }
}

watch(selectedSymbol, (symbol) => {
  syncAssetRoute(symbol)
  void loadAssetData()
})
watch(() => route.params.symbol, () => {
  if (!walletReady) return
  const symbol = resolveAssetSymbol()
  if (symbol !== selectedSymbol.value) selectedSymbol.value = symbol
  else syncAssetRoute(symbol)
})
watch(() => route.query.network, (value) => {
  if (!walletReady || !networks.value.length) return
  const code = String(value || '').toUpperCase()
  const requestedNetwork = networks.value.find(
    (network) => network.code === code && selectableNetwork(network),
  )
  if (requestedNetwork && requestedNetwork.code !== networkCode.value) {
    selectNetwork(requestedNetwork.code)
  } else if (!requestedNetwork) {
    syncDepositRoute(selectedSymbol.value)
  }
})
onMounted(initialize)
</script>

<template>
  <div class="page crypto-deposit-page">
    <PageHeader title="واریز رمزارز" description="دریافت آدرس امن واریز روی شبکه انتخابی" back-to="/app/wallet" />

    <div v-if="loading && !selectedAsset" class="deposit-skeleton">
      <AppSkeleton height="34rem" radius="var(--radius-xl)" />
      <AppSkeleton height="23rem" radius="var(--radius-xl)" />
    </div>

    <AppCard v-else-if="error && !selectedAsset" class="state-card">
      <EmptyState icon="warning" title="واریز رمزارز آماده نشد" :description="error"><AppButton @click="initialize">تلاش دوباره</AppButton></EmptyState>
    </AppCard>

    <AppCard v-else-if="!selectedAsset" class="state-card">
      <EmptyState icon="wallet" title="رمزارزی برای واریز وجود ندارد" description="در حال حاضر هیچ کیف پول رمزارزی در حساب شما فعال نیست."><AppButton to="/app/wallet">بازگشت به کیف پول</AppButton></EmptyState>
    </AppCard>

    <div v-else-if="selectedAsset" class="deposit-layout">
      <section class="deposit-main" aria-label="اطلاعات واریز رمزارز">
        <AppCard padding="lg">
          <div class="flow-heading"><span><AppIcon name="download" :size="24" /></span><div><h2>ارز و شبکه واریز</h2><p>شبکه مبدأ باید دقیقاً با شبکه انتخابی یکسان باشد.</p></div></div>
          <div class="selectors">
            <AssetSelect
              v-model="selectedSymbol"
              :assets="cryptoAssets"
              :balances="assetBalances"
              :disabled-symbols="disabledAssetSymbols"
              :disabled-descriptions="disabledAssetDescriptions"
              label="ارز مورد نظر"
              balance-label="موجودی"
              show-balance
              required
            />
            <div class="selected-balance">
              <AssetAvatar :symbol="selectedAsset.symbol" :color="selectedAsset.color" />
              <span><small>موجودی فعلی</small><strong>{{ formatCrypto(selectedAsset.total, { symbol: selectedAsset.symbol }) }}</strong></span>
            </div>
            <NetworkSelector
              :model-value="networkCode"
              :networks="networks"
              mode="deposit"
              label="شبکه انتقال"
              :error="addressError && !networkCode ? addressError : undefined"
              @update:model-value="selectNetwork"
            />
          </div>
        </AppCard>

        <div v-if="addressLoading" class="address-loading"><AppSkeleton height="25rem" radius="var(--radius-xl)" /></div>
        <DepositAddressCard
          v-else-if="depositAddress"
          :deposit-address="depositAddress"
          :asset-name="selectedAsset.nameFa"
          :network-name="selectedNetwork?.displayName"
        />
        <AppCard v-else-if="addressError" class="address-error">
          <EmptyState icon="warning" title="آدرس واریز در دسترس نیست" :description="addressError"><AppButton v-if="networkCode" variant="secondary" @click="loadDepositAddress">تلاش دوباره</AppButton></EmptyState>
        </AppCard>
        <AppCard v-else-if="!networks.some(selectableNetwork)" class="address-error">
          <EmptyState icon="warning" title="شبکه فعالی وجود ندارد" description="واریز این رمزارز روی همه شبکه‌ها موقتاً متوقف است. وضعیت شبکه‌ها را بعداً دوباره بررسی کنید." />
        </AppCard>
      </section>

      <aside class="deposit-aside">
        <AppCard>
          <div class="aside-heading"><span><AppIcon name="shield" :size="21" /></span><h3>پیش از انتقال</h3></div>
          <ol class="steps">
            <li><span>۱</span><p><strong>ارز را بررسی کنید</strong><small>تنها {{ selectedAsset.symbol }} به این آدرس ارسال کنید.</small></p></li>
            <li><span>۲</span><p><strong>شبکه را یکسان بگیرید</strong><small>شبکه کیف پول مبدأ و روشا باید یکی باشد.</small></p></li>
            <li><span>۳</span><p><strong>منتظر تأیید بمانید</strong><small v-if="selectedNetwork">پس از {{ toPersianDigits(selectedNetwork.confirmations) }} تأیید شبکه، موجودی به‌روز می‌شود.</small></p></li>
          </ol>
        </AppCard>
        <div class="critical-warning"><AppIcon name="warning" :size="21" /><span><strong>هشدار مهم</strong><small>ارسال ارز یا شبکه متفاوت ممکن است باعث از دست رفتن دائمی دارایی شود.</small></span></div>
      </aside>
    </div>

    <AppCard v-if="selectedAsset" class="history-card" padding="none">
      <div class="card-heading"><div><h2>{{ historyTitle }}</h2><p>{{ selectedNetwork ? `تأییدها و وضعیت واریزهای شبکه ${selectedNetwork.displayName}` : 'تأییدها و وضعیت واریزهای رمزارز' }}</p></div><RouterLink :to="{ path: '/app/transactions', query: { type: 'crypto_deposit', asset: selectedAsset.symbol, ...(networkCode ? { network: networkCode } : {}) } }">{{ networkCode ? 'همه واریزهای این شبکه' : 'همه واریزها' }} <AppIcon name="chevronLeft" :size="16" /></RouterLink></div>
      <TransactionList v-if="transactions.length" :transactions="transactions" compact />
      <EmptyState v-else-if="historyError" icon="warning" title="سابقه واریزها دریافت نشد" :description="historyError"><AppButton variant="secondary" size="sm" @click="loadAssetData">تلاش دوباره</AppButton></EmptyState>
      <EmptyState v-else icon="download" title="واریزی ثبت نشده" description="پس از ارسال و شناسایی تراکنش در شبکه، وضعیت آن اینجا نمایش داده می‌شود." />
    </AppCard>

    <div v-if="error && selectedAsset" class="inline-error" role="alert"><AppIcon name="warning" :size="18" /><span>{{ error }}</span><button type="button" @click="loadAssetData">تلاش دوباره</button></div>
  </div>
</template>

<style scoped>
.crypto-deposit-page { max-width: 78rem; }
.deposit-layout, .deposit-skeleton { display: grid; grid-template-columns: minmax(29rem, 1.18fr) minmax(19rem, .62fr); align-items: start; gap: var(--space-5); }
.deposit-main, .deposit-aside { display: grid; gap: var(--space-4); }
.flow-heading { display: flex; align-items: center; gap: var(--space-3); }
.flow-heading > span { display: grid; width: 3rem; height: 3rem; border-radius: .9rem; background: var(--color-success-soft); color: var(--color-success); place-items: center; }
.flow-heading h2 { margin: 0; font-size: var(--font-size-lg); }
.flow-heading p { margin: .1rem 0 0; color: var(--color-text-muted); font-size: var(--font-size-xs); }
.selectors { display: grid; gap: var(--space-5); margin-top: var(--space-6); }
.selected-balance { display: flex; align-items: center; gap: var(--space-3); padding: var(--space-3); border: 1px solid var(--color-border-soft); border-radius: var(--radius-lg); background: var(--color-surface-2); }
.selected-balance span { display: grid; }
.selected-balance small { color: var(--color-text-muted); font-size: var(--font-size-xs); }
.selected-balance strong { font-size: var(--font-size-sm); }
.aside-heading { display: flex; align-items: center; gap: var(--space-3); }
.aside-heading > span { display: grid; width: 2.8rem; height: 2.8rem; border-radius: .85rem; background: var(--color-primary-soft); color: var(--color-primary); place-items: center; }
.aside-heading h3 { margin: 0; font-size: var(--font-size-md); }
.steps { display: grid; gap: var(--space-4); margin: var(--space-5) 0 0; padding: 0; list-style: none; }
.steps li { display: flex; align-items: start; gap: var(--space-3); }
.steps li > span { display: grid; width: 1.75rem; height: 1.75rem; flex: 0 0 auto; border-radius: 50%; background: var(--color-surface-3); color: var(--color-primary); font-size: var(--font-size-xs); font-weight: 700; place-items: center; }
.steps p { display: grid; margin: 0; }
.steps strong { font-size: var(--font-size-sm); }
.steps small { color: var(--color-text-muted); font-size: var(--font-size-xs); }
.critical-warning { display: flex; gap: var(--space-3); padding: var(--space-4); border: 1px solid rgba(240,108,117,.18); border-radius: var(--radius-lg); background: var(--color-danger-soft); color: var(--color-danger); }
.critical-warning > span { display: grid; }
.critical-warning strong { color: var(--color-text-primary); font-size: var(--font-size-sm); }
.critical-warning small { color: var(--color-text-secondary); font-size: var(--font-size-xs); }
.history-card { margin-top: var(--space-5); overflow: hidden; }
.card-heading { display: flex; align-items: center; justify-content: space-between; gap: var(--space-4); padding: var(--space-5); border-block-end: 1px solid var(--color-border-soft); }
.card-heading h2 { margin: 0; font-size: var(--font-size-lg); }
.card-heading p { margin: .1rem 0 0; color: var(--color-text-muted); font-size: var(--font-size-xs); }
.card-heading a { display: inline-flex; align-items: center; gap: .2rem; color: var(--color-primary); font-size: var(--font-size-xs); font-weight: 600; }
.inline-error { display: flex; align-items: center; gap: var(--space-2); margin-top: var(--space-4); padding: var(--space-3) var(--space-4); border: 1px solid rgba(240,108,117,.18); border-radius: var(--radius-md); background: var(--color-danger-soft); color: var(--color-danger); }
.inline-error span { flex: 1; }
.inline-error button { border: 0; background: transparent; color: inherit; font-weight: 600; text-decoration: underline; }
.state-card, .address-error { width: 100%; }
@media (max-width: 920px) { .deposit-layout, .deposit-skeleton { grid-template-columns: 1fr; } .deposit-aside { grid-template-columns: 1fr 1fr; } }
@media (max-width: 767px) { .deposit-aside { grid-template-columns: 1fr; } .history-card { margin-top: var(--space-4); } .card-heading { padding: var(--space-4); } .card-heading p { display: none; } }
</style>
