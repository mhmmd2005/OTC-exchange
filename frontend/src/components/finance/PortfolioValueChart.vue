<script setup lang="ts">
import { computed, ref, useId, watch } from 'vue'
import type { PortfolioPeriod, PortfolioValuePoint } from '@/types'
import { formatPercentage, formatToman } from '@/utils/formatters'
import AppIcon from '@/components/ui/AppIcon.vue'

const props = withDefaults(defineProps<{
  points: PortfolioValuePoint[]
  period: PortfolioPeriod
  loading?: boolean
  error?: string
  hidden?: boolean
}>(), {
  loading: false,
  error: '',
  hidden: false,
})

const emit = defineEmits<{
  'update:period': [period: PortfolioPeriod]
  retry: []
}>()

const ranges: Array<{ value: PortfolioPeriod; label: string }> = [
  { value: '24h', label: '۲۴ ساعت' },
  { value: '7d', label: '۷ روز' },
  { value: '30d', label: '۳۰ روز' },
]

const chartId = useId().replace(/:/g, '')
const gradientId = `portfolio-area-${chartId}`
const titleId = `portfolio-chart-title-${chartId}`
const helpId = `portfolio-chart-help-${chartId}`
const viewBoxWidth = 720
const viewBoxHeight = 164
const chartTop = 12
const chartBottom = 144
const selectedIndex = ref(-1)
const keyboardAnnouncement = ref('')

const validPoints = computed(() => props.points.filter((point) => (
  Number.isFinite(Date.parse(point.timestamp))
  && Number.isFinite(Number(point.valueToman))
)))

const values = computed(() => validPoints.value.map((point) => Number(point.valueToman)))
const minimum = computed(() => values.value.length ? Math.min(...values.value) : 0)
const maximum = computed(() => values.value.length ? Math.max(...values.value) : 0)
const valueRange = computed(() => Math.max(1, maximum.value - minimum.value))

const coordinates = computed(() => validPoints.value.map((point, index, collection) => {
  const x = collection.length <= 1 ? viewBoxWidth / 2 : (index / (collection.length - 1)) * viewBoxWidth
  const normalized = (Number(point.valueToman) - minimum.value) / valueRange.value
  const y = chartBottom - normalized * (chartBottom - chartTop)
  return { x, y, point }
}))

const linePath = computed(() => coordinates.value.map((point, index) => (
  `${index ? 'L' : 'M'} ${point.x.toFixed(2)} ${point.y.toFixed(2)}`
)).join(' '))

const areaPath = computed(() => {
  if (!coordinates.value.length) return ''
  const first = coordinates.value[0]
  const last = coordinates.value[coordinates.value.length - 1]
  return `${linePath.value} L ${last.x.toFixed(2)} ${viewBoxHeight} L ${first.x.toFixed(2)} ${viewBoxHeight} Z`
})

const firstValue = computed(() => validPoints.value[0]?.valueToman ?? '0')
const lastValue = computed(() => validPoints.value[validPoints.value.length - 1]?.valueToman ?? '0')
const trendPercent = computed(() => {
  const first = Number(firstValue.value)
  if (!Number.isFinite(first) || first === 0) return 0
  return ((Number(lastValue.value) - first) / first) * 100
})
const trendDirection = computed(() => trendPercent.value < 0 ? 'down' : 'up')
const selectedCoordinate = computed(() => {
  if (!coordinates.value.length || selectedIndex.value < 0) return undefined
  return coordinates.value[Math.min(selectedIndex.value, coordinates.value.length - 1)]
})

const axisPoints = computed(() => {
  if (!validPoints.value.length) return []
  const indexes = [...new Set([0, Math.floor((validPoints.value.length - 1) / 2), validPoints.value.length - 1])]
  return indexes.map((index) => ({ index, point: validPoints.value[index] }))
})

const periodLabel = computed(() => ranges.find((range) => range.value === props.period)?.label ?? '')

const compactDateFormatter = new Intl.DateTimeFormat('fa-IR-u-ca-persian', {
  timeZone: 'Asia/Tehran',
  month: 'short',
  day: 'numeric',
})
const timeFormatter = new Intl.DateTimeFormat('fa-IR-u-ca-persian', {
  timeZone: 'Asia/Tehran',
  hour: '2-digit',
  minute: '2-digit',
})
const tooltipDateFormatter = new Intl.DateTimeFormat('fa-IR-u-ca-persian', {
  timeZone: 'Asia/Tehran',
  year: 'numeric',
  month: 'long',
  day: 'numeric',
  hour: '2-digit',
  minute: '2-digit',
})

function formatAxisDate(timestamp: string): string {
  const date = new Date(timestamp)
  return props.period === '24h' ? timeFormatter.format(date) : compactDateFormatter.format(date)
}

function formatTooltipDate(timestamp: string): string {
  return tooltipDateFormatter.format(new Date(timestamp))
}

const accessibleSummary = computed(() => {
  if (props.loading) return `در حال دریافت روند ارزش دارایی در بازه ${periodLabel.value}`
  if (props.error) return `روند ارزش دارایی دریافت نشد. ${props.error}`
  if (!validPoints.value.length) return `داده‌ای برای روند ارزش دارایی در بازه ${periodLabel.value} موجود نیست.`
  if (props.hidden) return `نمودار روند ارزش دارایی در بازه ${periodLabel.value}. مبلغ‌ها پنهان هستند.`
  return `نمودار روند ارزش دارایی در بازه ${periodLabel.value}. از ${formatToman(firstValue.value)} به ${formatToman(lastValue.value)} رسیده است. تغییر ${formatPercentage(trendPercent.value, { showSign: true })}.`
})

function selectFromPointer(event: PointerEvent): void {
  if (!coordinates.value.length) return
  const bounds = (event.currentTarget as HTMLElement).getBoundingClientRect()
  const ratio = Math.min(1, Math.max(0, (event.clientX - bounds.left) / Math.max(1, bounds.width)))
  selectedIndex.value = Math.round(ratio * (coordinates.value.length - 1))
}

function onPointerMove(event: PointerEvent): void {
  if (event.pointerType === 'mouse') selectFromPointer(event)
}

function announceSelected(): void {
  const selected = selectedCoordinate.value
  if (!selected) return
  keyboardAnnouncement.value = props.hidden
    ? `${formatTooltipDate(selected.point.timestamp)}، مبلغ پنهان است.`
    : `${formatTooltipDate(selected.point.timestamp)}، ${formatToman(selected.point.valueToman)}`
}

function onKeydown(event: KeyboardEvent): void {
  if (!coordinates.value.length) return
  const lastIndex = coordinates.value.length - 1
  const current = selectedIndex.value < 0 ? lastIndex : selectedIndex.value
  let next = current
  if (event.key === 'ArrowLeft') next = Math.max(0, current - 1)
  else if (event.key === 'ArrowRight') next = Math.min(lastIndex, current + 1)
  else if (event.key === 'Home') next = 0
  else if (event.key === 'End') next = lastIndex
  else return
  event.preventDefault()
  selectedIndex.value = next
  announceSelected()
}

watch(validPoints, () => {
  selectedIndex.value = -1
  keyboardAnnouncement.value = ''
}, { immediate: true })
</script>

<template>
  <section class="value-chart" :class="[`trend--${trendDirection}`, { 'is-loading': loading }]" :aria-labelledby="titleId">
    <header class="value-chart__header">
      <div>
        <span class="value-chart__eyebrow"><i /> روند ارزش دارایی</span>
        <span v-if="validPoints.length && !hidden" class="value-chart__change">
          <AppIcon :name="trendDirection === 'up' ? 'arrowUp' : 'arrowDown'" :size="14" />
          {{ formatPercentage(trendPercent, { showSign: true }) }}
        </span>
      </div>
      <div class="value-chart__ranges" role="group" aria-label="انتخاب بازه نمودار دارایی">
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

    <div v-if="error && !loading" class="value-chart__state" role="alert">
      <span><AppIcon name="warning" :size="20" /></span>
      <div><strong>روند دارایی دریافت نشد</strong><small>{{ error }}</small></div>
      <button type="button" @click="emit('retry')"><AppIcon name="refresh" :size="16" /> تلاش دوباره</button>
    </div>

    <div v-else-if="!loading && !validPoints.length" class="value-chart__state" role="status">
      <span><AppIcon name="markets" :size="20" /></span>
      <div><strong>هنوز روندی برای نمایش ندارید</strong><small>با نگهداری رمزارز، تغییر ارزش دارایی اینجا نمایش داده می‌شود.</small></div>
    </div>

    <div
      v-else
      class="value-chart__canvas"
      :tabindex="loading ? -1 : 0"
      role="group"
      :aria-label="accessibleSummary"
      :aria-describedby="helpId"
      @focus="selectedIndex = validPoints.length - 1"
      @keydown="onKeydown"
      @pointerdown="selectFromPointer"
      @pointermove="onPointerMove"
      @pointerleave="selectedIndex = -1"
    >
      <svg viewBox="0 0 720 164" preserveAspectRatio="none" aria-hidden="true" focusable="false">
        <defs>
          <linearGradient :id="gradientId" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="currentColor" stop-opacity="0.28" />
            <stop offset="100%" stop-color="currentColor" stop-opacity="0" />
          </linearGradient>
        </defs>
        <g class="chart-grid">
          <path d="M0 35 H720" />
          <path d="M0 88 H720" />
          <path d="M0 141 H720" />
        </g>
        <path v-if="areaPath" class="chart-area" :d="areaPath" :fill="`url(#${gradientId})`" />
        <path v-if="linePath" class="chart-line" :d="linePath" pathLength="1" />
        <g v-if="selectedCoordinate" class="chart-selection">
          <path :d="`M ${selectedCoordinate.x} 10 V 146`" />
          <circle :cx="selectedCoordinate.x" :cy="selectedCoordinate.y" r="5" />
          <circle :cx="selectedCoordinate.x" :cy="selectedCoordinate.y" r="2" />
        </g>
      </svg>

      <div
        v-if="selectedCoordinate && !loading"
        class="value-chart__tooltip"
        :style="{
          left: `${(selectedCoordinate.x / viewBoxWidth) * 100}%`,
          top: `${Math.max(4, (selectedCoordinate.y / viewBoxHeight) * 100 - 15)}%`,
          '--tooltip-shift': selectedCoordinate.x < 90 ? '0%' : selectedCoordinate.x > 630 ? '-100%' : '-50%',
        }"
        aria-hidden="true"
      >
        <strong>{{ hidden ? '••••••••' : formatToman(selectedCoordinate.point.valueToman) }}</strong>
        <span>{{ formatTooltipDate(selectedCoordinate.point.timestamp) }}</span>
      </div>

      <div class="value-chart__axis" aria-hidden="true">
        <span v-for="axis in axisPoints" :key="axis.index">{{ formatAxisDate(axis.point.timestamp) }}</span>
      </div>

      <div v-if="loading" class="value-chart__loading" role="status">
        <span class="sr-only">در حال دریافت روند ارزش دارایی</span>
        <i /><i /><i />
      </div>
    </div>

    <p class="sr-only" aria-live="polite">{{ keyboardAnnouncement }}</p>
  </section>
</template>

<style scoped>
.value-chart { min-width: 0; margin-top: var(--space-5); padding-top: var(--space-4); border-block-start: 1px solid rgba(255,255,255,.085); }
.value-chart__header, .value-chart__header > div:first-child { display: flex; align-items: center; justify-content: space-between; gap: var(--space-3); }
.value-chart__eyebrow { display: inline-flex; align-items: center; gap: var(--space-2); color: #a9b9cc; font-size: var(--font-size-xs); font-weight: 600; }
.value-chart__eyebrow i { width: .42rem; height: .42rem; border-radius: 50%; background: #45d2a1; box-shadow: 0 0 0 3px rgba(69,210,161,.1); }
.value-chart__change { display: inline-flex; align-items: center; gap: .15rem; direction: ltr; color: #5cddb1; font-size: .7rem; font-weight: 650; }
.trend--down .value-chart__change { color: #ff8b94; }
.value-chart__ranges { display: inline-grid; grid-template-columns: repeat(3, auto); gap: .2rem; padding: .2rem; border: 1px solid rgba(255,255,255,.085); border-radius: .75rem; background: rgba(1,9,18,.26); }
.value-chart__ranges button { min-width: 3.75rem; min-height: 2.75rem; padding-inline: .65rem; border: 0; border-radius: .55rem; background: transparent; color: #8296ad; font-family: inherit; font-size: .72rem; transition: color var(--transition-fast), background var(--transition-fast), box-shadow var(--transition-fast); }
.value-chart__ranges button:hover { color: #eaf2fc; }
.value-chart__ranges button[aria-pressed='true'] { background: rgba(76,141,255,.2); box-shadow: 0 0 0 1px rgba(111,167,255,.22) inset; color: #dce9ff; }
.value-chart__ranges button:focus-visible { outline: 2px solid #8bb7ff; outline-offset: 2px; }
.value-chart__ranges button:disabled { opacity: .7; cursor: wait; }
.value-chart__canvas { position: relative; height: 10.5rem; margin-top: var(--space-3); color: #67a0ff; direction: ltr; outline: none; touch-action: pan-y; }
.value-chart__canvas:focus-visible { border-radius: var(--radius-sm); box-shadow: 0 0 0 2px #8bb7ff; }
.value-chart__canvas svg { display: block; width: 100%; height: calc(100% - 1.5rem); overflow: visible; }
.chart-grid path { fill: none; stroke: rgba(173,198,225,.09); stroke-width: 1; vector-effect: non-scaling-stroke; }
.chart-area { color: #4c8dff; }
.chart-line { fill: none; stroke: #76aaff; stroke-linecap: round; stroke-linejoin: round; stroke-width: 2.3; vector-effect: non-scaling-stroke; }
.chart-selection path { stroke: rgba(205,223,247,.25); stroke-dasharray: 3 4; stroke-width: 1; vector-effect: non-scaling-stroke; }
.chart-selection circle:first-of-type { fill: #0c1b2b; stroke: #8db8ff; stroke-width: 2.5; vector-effect: non-scaling-stroke; }
.chart-selection circle:last-of-type { fill: #e8f1ff; }
.value-chart__tooltip { position: absolute; z-index: 2; display: grid; width: max-content; max-width: min(13rem, 70vw); gap: .1rem; padding: .5rem .65rem; border: 1px solid rgba(130,178,255,.22); border-radius: .65rem; background: rgba(5,16,29,.94); box-shadow: 0 10px 28px rgba(0,0,0,.32); color: #eef5ff; direction: rtl; pointer-events: none; transform: translate(var(--tooltip-shift), -100%); }
.value-chart__tooltip strong { font-size: .75rem; font-weight: 650; white-space: nowrap; }
.value-chart__tooltip span { color: #8ea3ba; font-size: .68rem; white-space: nowrap; }
.value-chart__axis { position: absolute; inset: auto 0 0; display: flex; justify-content: space-between; color: #71869d; direction: ltr; font-size: .68rem; }
.value-chart__state { display: grid; min-height: 10.5rem; grid-template-columns: auto minmax(0,1fr) auto; align-items: center; gap: var(--space-3); margin-top: var(--space-3); padding: var(--space-4); border: 1px dashed rgba(157,184,215,.16); border-radius: var(--radius-md); background: rgba(4,13,23,.18); }
.value-chart__state > span { display: grid; width: 2.65rem; height: 2.65rem; border-radius: .8rem; background: rgba(76,141,255,.11); color: #79a9fa; place-items: center; }
.value-chart__state > div { display: grid; gap: .2rem; }
.value-chart__state strong { color: #dce6f2; font-size: var(--font-size-xs); }
.value-chart__state small { color: #7d91a9; font-size: .68rem; line-height: 1.7; }
.value-chart__state > button { display: inline-flex; min-height: 2.75rem; align-items: center; gap: .35rem; padding-inline: var(--space-3); border: 1px solid rgba(130,178,255,.25); border-radius: .7rem; background: rgba(76,141,255,.1); color: #a9c9ff; font-family: inherit; font-size: .72rem; font-weight: 600; }
.value-chart__state > button:focus-visible { outline: 2px solid #8bb7ff; outline-offset: 2px; }
.value-chart__loading { position: absolute; inset: 0 0 1.3rem; display: grid; align-content: center; gap: .65rem; padding-inline: 7%; border-radius: var(--radius-sm); background: rgba(8,22,37,.74); backdrop-filter: blur(3px); }
.value-chart__loading i { display: block; height: .55rem; border-radius: var(--radius-pill); background: linear-gradient(90deg, rgba(111,167,255,.06), rgba(111,167,255,.2), rgba(111,167,255,.06)); background-size: 220% 100%; animation: chart-loading 1.4s ease-in-out infinite; }
.value-chart__loading i:nth-child(1) { width: 72%; }
.value-chart__loading i:nth-child(2) { width: 90%; animation-delay: .08s; }
.value-chart__loading i:nth-child(3) { width: 58%; animation-delay: .16s; }
@keyframes chart-loading { to { background-position: -220% 0; } }
@media (max-width: 480px) {
  .value-chart { margin-top: var(--space-4); padding-top: var(--space-3); }
  .value-chart__header { align-items: flex-start; flex-direction: column; }
  .value-chart__ranges { width: 100%; grid-template-columns: repeat(3, minmax(0,1fr)); }
  .value-chart__ranges button { min-width: 0; }
  .value-chart__canvas, .value-chart__state { min-height: 9rem; height: 9rem; }
  .value-chart__canvas svg { height: calc(100% - 1.35rem); }
  .value-chart__tooltip { max-width: 64vw; }
  .value-chart__state { grid-template-columns: auto minmax(0,1fr); }
  .value-chart__state > button { grid-column: 2; justify-self: start; }
}
@media (prefers-reduced-motion: reduce) { .value-chart__loading i { animation: none; } }
:global([data-reduce-motion='true']) .value-chart__loading i { animation: none; }
</style>
