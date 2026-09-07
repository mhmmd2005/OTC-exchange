<script setup lang="ts">
import { computed } from 'vue'
import type { PortfolioPeriod, PortfolioValuePoint } from '@/types'
import AppIcon from '@/components/ui/AppIcon.vue'
import PortfolioValueChart from '@/components/finance/PortfolioValueChart.vue'
import { formatToman } from '@/utils/formatters'

const props = withDefaults(defineProps<{
  total: string
  toman: string
  crypto: string
  hidden?: boolean
  updatedLabel?: string
  history?: PortfolioValuePoint[]
  historyPeriod?: PortfolioPeriod
  historyLoading?: boolean
  historyError?: string
}>(), {
  hidden: false,
  updatedLabel: undefined,
  history: undefined,
  historyPeriod: '7d',
  historyLoading: false,
  historyError: '',
})

defineEmits<{
  toggle: []
  'update:historyPeriod': [period: PortfolioPeriod]
  retryHistory: []
}>()

const hasChart = computed(() => (
  props.history !== undefined || props.historyLoading || Boolean(props.historyError)
))
</script>

<template>
  <section class="portfolio" :class="{ 'portfolio--chart': hasChart }">
    <div class="portfolio__glow" aria-hidden="true" />
    <header>
      <div class="portfolio__title">
        <span class="portfolio__mark"><AppIcon name="wallet" :size="20" /></span>
        <div><span>ارزش کل دارایی</span><small>مجموع موجودی تومان و رمزارزها</small></div>
      </div>
      <button type="button" :aria-label="hidden ? 'نمایش موجودی' : 'مخفی کردن موجودی'" @click="$emit('toggle')"><AppIcon :name="hidden ? 'eye-off' : 'eye'" :size="20" /></button>
    </header>
    <div class="portfolio__value" :class="{ hidden }"><bdi>{{ hidden ? '••••••••' : formatToman(total, { showCurrency: false }) }}</bdi> <small>تومان</small></div>
    <div v-if="updatedLabel" class="portfolio__meta"><span class="live"><i />{{ updatedLabel }}</span></div>
    <div class="portfolio__split">
      <div><span>موجودی تومان</span><strong><bdi>{{ hidden ? '••••••' : formatToman(toman) }}</bdi></strong></div>
      <div><span>ارزش رمزارزها</span><strong><bdi>{{ hidden ? '••••••' : formatToman(crypto) }}</bdi></strong></div>
    </div>
    <PortfolioValueChart
      v-if="hasChart"
      :points="history ?? []"
      :period="historyPeriod"
      :loading="historyLoading"
      :error="historyError"
      :hidden="hidden"
      @update:period="$emit('update:historyPeriod', $event)"
      @retry="$emit('retryHistory')"
    />
  </section>
</template>

<style scoped>
.portfolio { position: relative; min-height: 16.3rem; overflow: hidden; padding: var(--space-6); border: 1px solid rgba(100, 160, 255, .22); border-radius: var(--radius-xl); background: linear-gradient(145deg, #112b49 0%, #0b1b2d 58%, #0f1a27 100%); box-shadow: 0 20px 48px rgba(0, 7, 17, .18); color: #f4f7fb; isolation: isolate; }
.portfolio--chart { min-height: 29rem; background: radial-gradient(circle at 82% 5%, rgba(53,112,217,.2), transparent 34%), linear-gradient(145deg, #112b49 0%, #0b1b2d 58%, #0f1a27 100%); }
.portfolio::before { position: absolute; z-index: -1; inset: 0; background: linear-gradient(110deg, rgba(255,255,255,.035), transparent 35%); content: ''; }
.portfolio::after { position: absolute; z-index: -1; inset-block-end: -6rem; inset-inline-start: -4rem; width: 15rem; height: 15rem; border: 1px solid rgba(221,183,110,.13); border-radius: 50%; box-shadow: 0 0 0 2.7rem rgba(221,183,110,.018); content: ''; }
.portfolio__glow { position: absolute; z-index: -1; inset-block-start: -7rem; inset-inline-end: -4rem; width: 20rem; height: 20rem; border-radius: 50%; background: radial-gradient(circle, rgba(67,139,255,.25), transparent 67%); }
header { position: relative; display: flex; align-items: flex-start; justify-content: space-between; gap: var(--space-4); color: #a9b9cc; }
.portfolio__title { display: flex; align-items: center; gap: var(--space-3); }
.portfolio__title > div { display: grid; }
.portfolio__title small { color: #8498ae; font-size: var(--font-size-xs); }
.portfolio__mark { display: grid; width: 2.65rem; height: 2.65rem; flex: 0 0 auto; border: 1px solid rgba(111,167,255,.22); border-radius: .85rem; background: rgba(67,139,255,.12); color: #82b2ff; place-items: center; }
header button { display: grid; width: 2.65rem; height: 2.65rem; flex: 0 0 auto; border: 1px solid rgba(255,255,255,.1); border-radius: .85rem; background: rgba(255,255,255,.055); color: #b8c6d6; transition: border-color var(--transition-fast), background var(--transition-fast), color var(--transition-fast); place-items: center; }
header button:hover { border-color: rgba(130,178,255,.28); background: rgba(67,139,255,.11); color: #fff; }
.portfolio__value { position: relative; display: flex; align-items: baseline; gap: var(--space-2); margin-top: var(--space-5); font-size: clamp(2rem, 3.5vw, 2.65rem); font-weight: 700; letter-spacing: -.035em; line-height: 1.3; }
.portfolio__value.hidden { letter-spacing: .13em; }
.portfolio__value small { color: #a9b9cc; font-size: var(--font-size-sm); font-weight: 500; letter-spacing: 0; }
.portfolio__meta { position: relative; display: flex; align-items: center; gap: var(--space-4); margin-top: var(--space-2); color: #8498ae; font-size: var(--font-size-xs); }
.portfolio__meta span { display: inline-flex; align-items: center; gap: var(--space-1); }
.portfolio__meta .live i { width: .42rem; height: .42rem; border-radius: 50%; background: #45d2a1; box-shadow: 0 0 0 3px rgba(69,210,161,.1); }
.portfolio__split { position: relative; display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-3); margin-top: var(--space-5); padding-top: var(--space-4); border-block-start: 1px solid rgba(255,255,255,.085); }
.portfolio__split div { display: grid; gap: .25rem; }
.portfolio__split span { color: #8498ae; font-size: var(--font-size-xs); }
.portfolio__split strong { font-size: var(--font-size-sm); font-weight: 600; }
@media (max-width: 420px) { .portfolio { min-height: 15.3rem; padding: var(--space-5); } .portfolio__title small { display: none; } .portfolio__value { margin-top: var(--space-4); font-size: clamp(1.75rem, 9vw, 2.3rem); } .portfolio__split { gap: var(--space-2); margin-top: var(--space-4); } .portfolio__split strong { font-size: var(--font-size-xs); } }
</style>
