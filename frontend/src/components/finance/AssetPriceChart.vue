<script setup lang="ts">
import { computed, ref, useId, watch } from 'vue'
import type { PortfolioPeriod, PricePoint } from '@/types'
import { formatToman } from '@/utils/formatters'
import AppIcon from '@/components/ui/AppIcon.vue'

const props = withDefaults(defineProps<{
  points: PricePoint[]
  period: PortfolioPeriod
  loading?: boolean
  error?: string
}>(), { loading: false, error: '' })

const emit = defineEmits<{
  'update:period': [period: PortfolioPeriod]
  retry: []
}>()

const ranges: Array<{ value: PortfolioPeriod; label: string }> = [
  { value: '24h', label: '۲۴ ساعت' },
  { value: '7d', label: '۷ روز' },
  { value: '30d', label: '۳۰ روز' },
]
const width = 720
const height = 190
const top = 16
const bottom = 158
const id = useId().replace(/:/g, '')
const gradientId = `asset-price-${id}`
const titleId = `asset-chart-${id}`
const helpId = `asset-chart-help-${id}`
const selectedIndex = ref(-1)
const announcement = ref('')

const validPoints = computed(() => props.points.filter((point) => (
  Number.isFinite(Date.parse(point.timestamp))
  && Number.isFinite(Number(point.priceToman))
  && Number(point.priceToman) > 0
)))
const prices = computed(() => validPoints.value.map((point) => Number(point.priceToman)))
const minimum = computed(() => prices.value.length ? Math.min(...prices.value) : 0)
const maximum = computed(() => prices.value.length ? Math.max(...prices.value) : 0)
const valueRange = computed(() => Math.max(1, maximum.value - minimum.value))
const coordinates = computed(() => validPoints.value.map((point, index, collection) => ({
  x: collection.length <= 1 ? width / 2 : (index / (collection.length - 1)) * width,
  y: bottom - ((Number(point.priceToman) - minimum.value) / valueRange.value) * (bottom - top),
  point,
})))
const linePath = computed(() => coordinates.value.map((point, index) => (
  `${index ? 'L' : 'M'} ${point.x.toFixed(2)} ${point.y.toFixed(2)}`
)).join(' '))
const areaPath = computed(() => {
  if (!coordinates.value.length) return ''
  const first = coordinates.value[0]!
  const last = coordinates.value[coordinates.value.length - 1]!
  return `${linePath.value} L ${last.x.toFixed(2)} ${height} L ${first.x.toFixed(2)} ${height} Z`
})
const selected = computed(() => selectedIndex.value < 0
  ? undefined
  : coordinates.value[Math.min(selectedIndex.value, coordinates.value.length - 1)])
const isUp = computed(() => {
  if (prices.value.length < 2) return true
  return prices.value[prices.value.length - 1]! >= prices.value[0]!
})
const periodLabel = computed(() => ranges.find((item) => item.value === props.period)?.label ?? '')
const axisIndexes = computed(() => {
  if (!validPoints.value.length) return []
  return [...new Set([0, Math.floor((validPoints.value.length - 1) / 2), validPoints.value.length - 1])]
})

const dateFormatter = new Intl.DateTimeFormat('fa-IR-u-ca-persian', {
  timeZone: 'Asia/Tehran', month: 'short', day: 'numeric',
})
const timeFormatter = new Intl.DateTimeFormat('fa-IR-u-ca-persian', {
  timeZone: 'Asia/Tehran', hour: '2-digit', minute: '2-digit',
})
const tooltipFormatter = new Intl.DateTimeFormat('fa-IR-u-ca-persian', {
  timeZone: 'Asia/Tehran', year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit',
})

function axisLabel(timestamp: string): string {
  const date = new Date(timestamp)
  return props.period === '24h' ? timeFormatter.format(date) : dateFormatter.format(date)
}

const accessibleSummary = computed(() => {
  if (props.loading) return `در حال دریافت نمودار قیمت در بازه ${periodLabel.value}`
  if (props.error) return `نمودار قیمت دریافت نشد. ${props.error}`
  if (!validPoints.value.length) return `داده‌ای برای نمودار قیمت در بازه ${periodLabel.value} موجود نیست.`
  return `نمودار قیمت در بازه ${periodLabel.value}. کمترین ${formatToman(String(minimum.value))} و بیشترین ${formatToman(String(maximum.value))}.`
})

function selectFromPointer(event: PointerEvent): void {
  if (!coordinates.value.length) return
  const bounds = (event.currentTarget as HTMLElement).getBoundingClientRect()
  const ratio = Math.min(1, Math.max(0, (event.clientX - bounds.left) / Math.max(1, bounds.width)))
  selectedIndex.value = Math.round(ratio * (coordinates.value.length - 1))
}

function announce(): void {
  if (!selected.value) return
  announcement.value = `${tooltipFormatter.format(new Date(selected.value.point.timestamp))}، ${formatToman(selected.value.point.priceToman)}`
}

function onKeydown(event: KeyboardEvent): void {
  if (!coordinates.value.length) return
  const last = coordinates.value.length - 1
  const current = selectedIndex.value < 0 ? last : selectedIndex.value
  let next = current
  if (event.key === 'ArrowLeft') next = Math.max(0, current - 1)
  else if (event.key === 'ArrowRight') next = Math.min(last, current + 1)
  else if (event.key === 'Home') next = 0
  else if (event.key === 'End') next = last
  else return
  event.preventDefault()
  selectedIndex.value = next
  announce()
}

watch(validPoints, () => { selectedIndex.value = -1; announcement.value = '' })
</script>

<template>
  <section class="asset-price-chart" :class="isUp ? 'trend-up' : 'trend-down'" :aria-labelledby="titleId">
    <header>
      <div><strong>روند قیمت</strong><span>دادهٔ واقعی بازار</span></div>
      <div class="chart-ranges" role="group" aria-label="انتخاب بازه نمودار قیمت">
        <button
          v-for="range in ranges"
          :key="range.value"
          type="button"
          :aria-pressed="period === range.value"
          :disabled="loading && period === range.value"
          @click="emit('update:period', range.value)"
        >{{ range.label }}</button>
      </div>
    </header>
    <p :id="titleId" class="sr-only">{{ accessibleSummary }}</p>
    <p :id="helpId" class="sr-only">برای بررسی نقاط نمودار از کلیدهای جهت‌دار، ابتدا و انتها استفاده کنید.</p>

    <div v-if="error && !loading" class="chart-state" role="alert">
      <AppIcon name="warning" :size="22" />
      <span><strong>نمودار قیمت دریافت نشد</strong><small>{{ error }}</small></span>
      <button type="button" @click="emit('retry')"><AppIcon name="refresh" :size="16" /> تلاش دوباره</button>
    </div>
    <div v-else-if="!loading && validPoints.length < 2" class="chart-state" role="status">
      <AppIcon name="markets" :size="22" />
      <span><strong>دادهٔ کافی وجود ندارد</strong><small>پس از دریافت نقاط بیشتر، روند قیمت اینجا نمایش داده می‌شود.</small></span>
    </div>
    <div
      v-else
      class="chart-canvas"
      :tabindex="loading ? -1 : 0"
      role="group"
      :aria-label="accessibleSummary"
      :aria-describedby="helpId"
      @focus="selectedIndex = validPoints.length - 1"
      @keydown="onKeydown"
      @pointerdown="selectFromPointer"
      @pointermove="($event.pointerType === 'mouse') && selectFromPointer($event)"
      @pointerleave="selectedIndex = -1"
    >
      <svg viewBox="0 0 720 190" preserveAspectRatio="none" aria-hidden="true" focusable="false">
        <defs><linearGradient :id="gradientId" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="currentColor" stop-opacity=".26" /><stop offset="1" stop-color="currentColor" stop-opacity="0" /></linearGradient></defs>
        <g class="grid"><path d="M0 34H720" /><path d="M0 88H720" /><path d="M0 142H720" /></g>
        <path v-if="areaPath" class="area" :d="areaPath" :fill="`url(#${gradientId})`" />
        <path v-if="linePath" class="line" :d="linePath" pathLength="1" />
        <g v-if="selected" class="selection"><path :d="`M${selected.x} 12V160`" /><circle :cx="selected.x" :cy="selected.y" r="5" /><circle :cx="selected.x" :cy="selected.y" r="2" /></g>
      </svg>
      <div v-if="selected && !loading" class="tooltip" :style="{ left: `${selected.x / width * 100}%`, top: `${Math.max(3, selected.y / height * 100 - 10)}%`, '--shift': selected.x < 90 ? '0%' : selected.x > 630 ? '-100%' : '-50%' }" aria-hidden="true">
        <strong>{{ formatToman(selected.point.priceToman) }}</strong><span>{{ tooltipFormatter.format(new Date(selected.point.timestamp)) }}</span>
      </div>
      <div class="axis" aria-hidden="true"><span v-for="index in axisIndexes" :key="index">{{ axisLabel(validPoints[index]!.timestamp) }}</span></div>
      <div v-if="loading" class="chart-loading" role="status"><span class="sr-only">در حال دریافت نمودار قیمت</span><i /><i /><i /></div>
    </div>
    <p class="sr-only" aria-live="polite">{{ announcement }}</p>
  </section>
</template>

<style scoped>
.asset-price-chart { min-width: 0; margin-top: var(--space-5); color: var(--color-primary); }
.asset-price-chart > header { display: flex; align-items: center; justify-content: space-between; gap: var(--space-3); }
.asset-price-chart > header > div:first-child { display: grid; color: var(--color-text-primary); }
.asset-price-chart > header strong { font-size: var(--font-size-sm); }
.asset-price-chart > header span { color: var(--color-text-muted); font-size: .68rem; }
.chart-ranges { display: grid; grid-template-columns: repeat(3, auto); gap: .2rem; padding: .2rem; border: 1px solid var(--color-border-soft); border-radius: .7rem; background: var(--color-surface-2); }
.chart-ranges button { min-width: 3.5rem; min-height: 2.75rem; padding-inline: .55rem; border: 0; border-radius: .5rem; background: transparent; color: var(--color-text-muted); font-family: inherit; font-size: .7rem; }
.chart-ranges button[aria-pressed='true'] { background: var(--color-primary-soft); color: var(--color-primary); }
.chart-ranges button:focus-visible,.chart-state button:focus-visible,.chart-canvas:focus-visible { outline: 2px solid var(--color-border-focus); outline-offset: 2px; }
.chart-canvas { position: relative; height: 12rem; margin-top: var(--space-3); outline: 0; direction: ltr; touch-action: pan-y; }
.chart-canvas svg { display: block; width: 100%; height: calc(100% - 1.5rem); overflow: visible; }
.grid path { fill: none; stroke: var(--color-border-soft); stroke-width: 1; vector-effect: non-scaling-stroke; }
.area { color: var(--color-primary); }.line { fill: none; stroke: var(--color-primary); stroke-linecap: round; stroke-linejoin: round; stroke-width: 2.4; vector-effect: non-scaling-stroke; }
.trend-down { color: var(--color-danger); }.trend-down .area,.trend-down .line { color: var(--color-danger); stroke: var(--color-danger); }
.selection path { stroke: var(--color-border-hover); stroke-dasharray: 3 4; vector-effect: non-scaling-stroke; }.selection circle:first-of-type { fill: var(--color-surface-1); stroke: currentColor; stroke-width: 2.4; }.selection circle:last-of-type { fill: var(--color-text-primary); }
.tooltip { position: absolute; z-index: 2; display: grid; width: max-content; max-width: min(14rem, 72vw); gap: .12rem; padding: .5rem .65rem; border: 1px solid var(--color-border-hover); border-radius: .65rem; background: var(--color-surface-raised); box-shadow: var(--shadow-md); color: var(--color-text-primary); direction: rtl; pointer-events: none; transform: translate(var(--shift), -100%); }
.tooltip strong,.tooltip span { white-space: nowrap; }.tooltip strong { font-size: .75rem; }.tooltip span { color: var(--color-text-muted); font-size: .66rem; }
.axis { position: absolute; inset: auto 0 0; display: flex; justify-content: space-between; color: var(--color-text-muted); font-size: .67rem; direction: ltr; }
.chart-state { display: grid; min-height: 10rem; grid-template-columns: auto minmax(0, 1fr) auto; align-items: center; gap: var(--space-3); margin-top: var(--space-3); padding: var(--space-4); border: 1px dashed var(--color-border-hover); border-radius: var(--radius-md); background: var(--color-surface-2); }
.chart-state > span { display: grid; color: var(--color-text-primary); }.chart-state small { color: var(--color-text-muted); }.chart-state button { display: inline-flex; min-height: 2.75rem; align-items: center; gap: var(--space-1); padding-inline: var(--space-3); border: 1px solid var(--color-border); border-radius: var(--radius-sm); background: var(--color-surface-3); color: var(--color-text-secondary); font-family: inherit; }
.chart-loading { position: absolute; inset: 0 0 1.3rem; display: grid; align-content: center; gap: .65rem; padding-inline: 8%; border-radius: var(--radius-sm); background: color-mix(in srgb, var(--color-surface-1) 88%, transparent); backdrop-filter: blur(3px); }.chart-loading i { height: .55rem; border-radius: var(--radius-pill); background: linear-gradient(90deg, var(--color-surface-3), var(--color-primary-soft), var(--color-surface-3)); background-size: 220% 100%; animation: asset-chart-loading 1.4s ease-in-out infinite; }.chart-loading i:nth-child(1) { width: 70%; }.chart-loading i:nth-child(2) { width: 92%; }.chart-loading i:nth-child(3) { width: 55%; }
@keyframes asset-chart-loading { to { background-position: -220% 0; } }
@media (max-width: 520px) { .asset-price-chart > header { align-items: stretch; flex-direction: column; }.chart-ranges { grid-template-columns: repeat(3, minmax(0, 1fr)); }.chart-ranges button { min-width: 0; }.chart-canvas { height: 10.5rem; }.chart-state { grid-template-columns: auto minmax(0,1fr); }.chart-state button { grid-column: 2; justify-self: start; } }
@media (prefers-reduced-motion: reduce) { .chart-loading i { animation: none; } }
:global([data-reduce-motion='true']) .chart-loading i { animation: none; }
</style>
