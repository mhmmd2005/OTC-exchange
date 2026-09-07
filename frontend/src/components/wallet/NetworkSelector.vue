<script setup lang="ts">
import { computed, nextTick, ref } from 'vue'
import type { AssetNetwork } from '@/types'
import { formatCrypto, toPersianDigits } from '@/utils/formatters'
import AppIcon from '@/components/ui/AppIcon.vue'
import AppModal from '@/components/ui/AppModal.vue'

export type NetworkSelectorMode = 'deposit' | 'withdrawal'

const props = withDefaults(defineProps<{
  networks: AssetNetwork[]
  modelValue?: string
  mode?: NetworkSelectorMode
  label?: string
  disabled?: boolean
  error?: string
}>(), {
  modelValue: '',
  mode: 'deposit',
  label: 'انتخاب شبکه',
  disabled: false,
  error: '',
})

const emit = defineEmits<{
  'update:modelValue': [code: string]
  change: [network: AssetNetwork]
}>()

const sheetOpen = ref(false)
const labelId = `network-label-${Math.random().toString(36).slice(2, 9)}`
const selectedNetwork = computed(() => props.networks.find((network) => network.code === props.modelValue))
const availableNetworks = computed(() => props.networks.filter((network) => !isUnavailable(network)))

function operationEnabled(network: AssetNetwork): boolean {
  return props.mode === 'deposit' ? network.depositEnabled : network.withdrawalEnabled
}

function isUnavailable(network: AssetNetwork): boolean {
  return props.disabled
    || !operationEnabled(network)
    || (props.mode === 'withdrawal' && network.status !== 'active')
    || network.status === 'maintenance'
    || network.status === 'disabled'
}

function statusLabel(network: AssetNetwork): string {
  if (!operationEnabled(network)) return props.mode === 'deposit' ? 'واریز غیرفعال' : 'برداشت غیرفعال'
  if (network.status === 'active') return 'فعال'
  if (network.status === 'congested') return 'پرترافیک'
  if (network.status === 'maintenance') return 'در حال نگهداری'
  return 'غیرفعال'
}

function statusTone(network: AssetNetwork): 'success' | 'warning' | 'danger' {
  if (!operationEnabled(network) || network.status === 'disabled') return 'danger'
  return network.status === 'active' ? 'success' : 'warning'
}

function unavailableReason(network: AssetNetwork): string {
  if (!operationEnabled(network)) {
    return props.mode === 'deposit' ? 'واریز از این شبکه موقتاً غیرفعال است.' : 'برداشت از این شبکه موقتاً غیرفعال است.'
  }
  if (network.status === 'maintenance') return 'شبکه در حال نگهداری است.'
  if (network.status === 'disabled') return 'شبکه در دسترس نیست.'
  if (props.mode === 'withdrawal' && network.status === 'congested') return 'برداشت در زمان پرترافیک این شبکه موقتاً متوقف است.'
  return ''
}

function primaryMetricLabel(): string {
  return props.mode === 'deposit' ? 'حداقل واریز' : 'کارمزد برداشت'
}

function primaryMetric(network: AssetNetwork): string {
  const amount = props.mode === 'deposit' ? network.minimumDeposit : network.withdrawalFee
  return formatCrypto(amount, { symbol: network.assetSymbol, maximumFractionDigits: 8 })
}

function arrivalTime(network: AssetNetwork): string {
  return `حدود ${toPersianDigits(network.estimatedArrivalMinutes)} دقیقه`
}

function choose(network: AssetNetwork, closeSheet = true): void {
  if (isUnavailable(network)) return
  emit('update:modelValue', network.code)
  emit('change', network)
  if (closeSheet) sheetOpen.value = false
}

function isTabStop(network: AssetNetwork): boolean {
  if (isUnavailable(network)) return false
  const selectedIsAvailable = availableNetworks.value.some((item) => item.code === props.modelValue)
  return selectedIsAvailable
    ? network.code === props.modelValue
    : network.code === availableNetworks.value[0]?.code
}

async function onRadioKeydown(event: KeyboardEvent): Promise<void> {
  const current = event.currentTarget as HTMLButtonElement
  const group = current.closest<HTMLElement>('[role="radiogroup"]')
  if (!group) return

  const radios = Array.from(group.querySelectorAll<HTMLButtonElement>('[role="radio"]:not(:disabled)'))
  const currentIndex = radios.indexOf(current)
  if (currentIndex < 0 || radios.length < 2) return

  const isRtl = getComputedStyle(group).direction === 'rtl'
  let targetIndex: number | undefined
  if (event.key === 'Home') targetIndex = 0
  else if (event.key === 'End') targetIndex = radios.length - 1
  else if (event.key === 'ArrowUp') targetIndex = (currentIndex - 1 + radios.length) % radios.length
  else if (event.key === 'ArrowDown') targetIndex = (currentIndex + 1) % radios.length
  else if (event.key === 'ArrowLeft') targetIndex = (currentIndex + (isRtl ? 1 : -1) + radios.length) % radios.length
  else if (event.key === 'ArrowRight') targetIndex = (currentIndex + (isRtl ? -1 : 1) + radios.length) % radios.length
  else return

  event.preventDefault()
  const target = radios[targetIndex]
  const network = props.networks.find((item) => item.code === target?.dataset.networkCode)
  if (!target || !network) return
  choose(network, false)
  await nextTick()
  target.focus()
}

function openSheet(): void {
  if (!props.disabled && props.networks.length > 0) sheetOpen.value = true
}
</script>

<template>
  <section class="network-selector" :class="{ 'network-selector--disabled': disabled }">
    <div class="network-selector__heading">
      <span :id="labelId" class="network-selector__label">{{ label }}</span>
      <span class="network-selector__hint">شبکه مبدأ و مقصد باید دقیقاً یکسان باشد</span>
    </div>

    <div v-if="networks.length" class="network-grid desktop-only" role="radiogroup" :aria-labelledby="labelId">
      <button
        v-for="network in networks"
        :key="network.id"
        type="button"
        class="network-card"
        :class="{
          'network-card--selected': network.code === modelValue,
          'network-card--unavailable': isUnavailable(network),
        }"
        role="radio"
        :data-network-code="network.code"
        :aria-checked="network.code === modelValue"
        :aria-describedby="isUnavailable(network) ? `network-reason-${network.id}` : undefined"
        :disabled="isUnavailable(network)"
        :tabindex="isTabStop(network) ? 0 : -1"
        @click="choose(network)"
        @keydown="onRadioKeydown"
      >
        <span class="network-card__top">
          <span class="network-card__identity">
            <strong>{{ network.displayName || network.name }}</strong>
            <small dir="ltr">{{ network.name }} · {{ network.code }}</small>
          </span>
          <span class="network-status" :class="`network-status--${statusTone(network)}`">
            <i aria-hidden="true" />{{ statusLabel(network) }}
          </span>
        </span>
        <span class="network-card__meta">
          <span><small>{{ primaryMetricLabel() }}</small><b dir="ltr">{{ primaryMetric(network) }}</b></span>
          <span><small>زمان تقریبی</small><b>{{ arrivalTime(network) }}</b></span>
        </span>
        <span v-if="isUnavailable(network)" :id="`network-reason-${network.id}`" class="network-card__reason">
          {{ unavailableReason(network) }}
        </span>
        <span class="network-card__check" aria-hidden="true"><AppIcon name="check" :size="15" :stroke-width="2.4" /></span>
      </button>
    </div>

    <button
      v-if="networks.length"
      type="button"
      class="network-trigger mobile-only"
      :class="{ 'network-trigger--selected': selectedNetwork, 'has-error': error }"
      :disabled="disabled"
      :aria-labelledby="labelId"
      aria-haspopup="dialog"
      :aria-expanded="sheetOpen"
      @click="openSheet"
    >
      <span v-if="selectedNetwork" class="network-trigger__copy">
        <strong>{{ selectedNetwork.displayName || selectedNetwork.name }}</strong>
        <small dir="ltr">{{ selectedNetwork.name }} · {{ selectedNetwork.code }}</small>
      </span>
      <span v-else class="network-trigger__placeholder">یک شبکه را انتخاب کنید</span>
      <span v-if="selectedNetwork" class="network-status" :class="`network-status--${statusTone(selectedNetwork)}`">
        <i aria-hidden="true" />{{ statusLabel(selectedNetwork) }}
      </span>
      <AppIcon name="chevronDown" :size="18" />
    </button>

    <div v-else class="network-empty" role="status">
      <AppIcon name="info" :size="20" />
      <span>در حال حاضر شبکه‌ای برای این دارایی در دسترس نیست.</span>
    </div>

    <p v-if="error" class="network-selector__error" role="alert">{{ error }}</p>

    <AppModal v-model="sheetOpen" :title="label" description="شبکه انتقال را با دقت بررسی کنید" size="sm">
      <div class="network-sheet" role="radiogroup" :aria-labelledby="labelId">
        <button
          v-for="network in networks"
          :key="network.id"
          type="button"
          class="network-sheet__item"
          :class="{
            'network-sheet__item--selected': network.code === modelValue,
            'network-sheet__item--unavailable': isUnavailable(network),
          }"
          role="radio"
          :data-network-code="network.code"
          :aria-checked="network.code === modelValue"
          :disabled="isUnavailable(network)"
          :tabindex="isTabStop(network) ? 0 : -1"
          @click="choose(network)"
          @keydown="onRadioKeydown"
        >
          <span class="network-sheet__top">
            <span class="network-card__identity">
              <strong>{{ network.displayName || network.name }}</strong>
              <small dir="ltr">{{ network.name }} · {{ network.code }}</small>
            </span>
            <span class="network-status" :class="`network-status--${statusTone(network)}`">
              <i aria-hidden="true" />{{ statusLabel(network) }}
            </span>
          </span>
          <span class="network-sheet__meta">
            <span>{{ primaryMetricLabel() }}: <b dir="ltr">{{ primaryMetric(network) }}</b></span>
            <span><AppIcon name="clock" :size="14" />{{ arrivalTime(network) }}</span>
          </span>
          <small v-if="isUnavailable(network)" class="network-card__reason">{{ unavailableReason(network) }}</small>
          <span v-if="network.code === modelValue" class="network-sheet__selected" aria-hidden="true">
            <AppIcon name="check" :size="16" :stroke-width="2.5" />
          </span>
        </button>
      </div>
    </AppModal>
  </section>
</template>

<style scoped>
.network-selector { display: grid; gap: var(--space-3); min-width: 0; }
.network-selector__heading { display: flex; align-items: center; justify-content: space-between; gap: var(--space-3); }
.network-selector__label { color: var(--color-text-secondary); font-size: var(--font-size-sm); font-weight: 600; }
.network-selector__hint { color: var(--color-text-muted); font-size: var(--font-size-xs); }
.network-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(15rem, 1fr)); gap: var(--space-3); }
.network-card { position: relative; display: grid; overflow: hidden; gap: var(--space-4); min-width: 0; padding: var(--space-4); border: 1px solid var(--color-border); border-radius: var(--radius-lg); outline: 0; background: var(--color-surface-2); color: var(--color-text-primary); text-align: start; transition: border-color var(--transition-fast), background var(--transition-fast), transform var(--transition-fast), box-shadow var(--transition-fast); }
.network-card:hover:not(:disabled) { border-color: var(--color-border-hover); background: var(--color-surface-3); transform: translateY(-1px); }
.network-card:focus-visible { border-color: var(--color-border-focus); box-shadow: var(--shadow-focus); }
.network-card--selected { border-color: var(--color-primary); background: linear-gradient(135deg, var(--color-primary-soft), var(--color-surface-2) 70%); box-shadow: inset 0 0 0 1px rgba(67, 139, 255, .12); }
.network-card--unavailable { cursor: not-allowed; opacity: .58; }
.network-card__top, .network-sheet__top { display: flex; min-width: 0; align-items: flex-start; justify-content: space-between; gap: var(--space-3); }
.network-card__identity { display: grid; min-width: 0; }
.network-card__identity strong { overflow: hidden; font-size: var(--font-size-md); font-weight: 600; text-overflow: ellipsis; white-space: nowrap; }
.network-card__identity small { overflow: hidden; color: var(--color-text-muted); font-size: var(--font-size-xs); text-align: start; text-overflow: ellipsis; white-space: nowrap; }
.network-card__meta { display: grid; grid-template-columns: minmax(0, 1.25fr) minmax(0, .75fr); gap: var(--space-3); padding-top: var(--space-3); border-block-start: 1px solid var(--color-border-soft); }
.network-card__meta > span { display: grid; min-width: 0; gap: .1rem; }
.network-card__meta small { color: var(--color-text-muted); font-size: .69rem; }
.network-card__meta b { overflow: hidden; font-size: var(--font-size-xs); font-weight: 500; text-overflow: ellipsis; white-space: nowrap; }
.network-status { display: inline-flex; flex: 0 0 auto; align-items: center; gap: .32rem; min-height: 1.55rem; padding: .1rem .48rem; border-radius: var(--radius-pill); font-size: .68rem; font-weight: 600; white-space: nowrap; }
.network-status i { width: .35rem; height: .35rem; border-radius: 50%; background: currentColor; }
.network-status--success { background: var(--color-success-soft); color: var(--color-success); }
.network-status--warning { background: var(--color-warning-soft); color: var(--color-warning); }
.network-status--danger { background: var(--color-danger-soft); color: var(--color-danger); }
.network-card__reason { color: var(--color-warning); font-size: .7rem; line-height: 1.55; }
.network-card__check { position: absolute; inset: auto auto .7rem .7rem; display: grid; width: 1.45rem; height: 1.45rem; border: 1px solid var(--color-border-hover); border-radius: 50%; background: var(--color-surface-1); color: transparent; place-items: center; transition: color var(--transition-fast), background var(--transition-fast), border-color var(--transition-fast); }
.network-card--selected .network-card__check { border-color: var(--color-primary); background: var(--color-primary); color: #fff; }
.network-empty { display: flex; align-items: center; gap: var(--space-2); padding: var(--space-4); border: 1px dashed var(--color-border); border-radius: var(--radius-md); background: var(--color-surface-2); color: var(--color-text-muted); font-size: var(--font-size-sm); }
.network-selector__error { margin: -.15rem 0 0; color: var(--color-danger); font-size: var(--font-size-xs); }
.network-selector--disabled { opacity: .65; }
.network-trigger { display: grid; grid-template-columns: minmax(0, 1fr) auto auto; width: 100%; min-height: 4.25rem; align-items: center; gap: var(--space-3); padding: .7rem var(--space-3); border: 1px solid var(--color-border); border-radius: var(--radius-md); background: var(--color-surface-2); color: var(--color-text-primary); text-align: start; }
.network-trigger--selected { border-color: rgba(67, 139, 255, .55); background: linear-gradient(135deg, var(--color-primary-soft), var(--color-surface-2)); }
.network-trigger.has-error { border-color: var(--color-danger); }
.network-trigger__copy { display: grid; min-width: 0; }
.network-trigger__copy strong { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.network-trigger__copy small { color: var(--color-text-muted); font-size: var(--font-size-xs); }
.network-trigger__placeholder { color: var(--color-text-muted); }
.network-sheet { display: grid; gap: var(--space-2); }
.network-sheet__item { position: relative; display: grid; gap: var(--space-3); width: 100%; padding: var(--space-4); border: 1px solid var(--color-border); border-radius: var(--radius-md); background: var(--color-surface-2); color: var(--color-text-primary); text-align: start; }
.network-sheet__item--selected { border-color: var(--color-primary); background: var(--color-primary-soft); }
.network-sheet__item--unavailable { cursor: not-allowed; opacity: .58; }
.network-sheet__meta { display: flex; flex-wrap: wrap; gap: var(--space-2) var(--space-4); padding-top: var(--space-2); border-block-start: 1px solid var(--color-border-soft); color: var(--color-text-muted); font-size: var(--font-size-xs); }
.network-sheet__meta span { display: inline-flex; align-items: center; gap: var(--space-1); }
.network-sheet__meta b { color: var(--color-text-secondary); font-weight: 500; }
.network-sheet__selected { position: absolute; inset: auto auto var(--space-3) var(--space-3); display: grid; width: 1.5rem; height: 1.5rem; border-radius: 50%; background: var(--color-primary); color: #fff; place-items: center; }
@media (max-width: 767px) {
  .network-selector__hint { display: none; }
  .network-selector__heading { justify-content: flex-start; }
  .network-trigger.mobile-only { display: grid !important; }
}
</style>
