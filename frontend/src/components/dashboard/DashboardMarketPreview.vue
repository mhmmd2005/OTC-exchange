<script setup lang="ts">
import type { MarketAsset } from '@/types'
import { compareDecimal } from '@/utils/financial'
import { formatPercentage, formatToman } from '@/utils/formatters'
import AppButton from '@/components/ui/AppButton.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import AssetAvatar from '@/components/finance/AssetAvatar.vue'

defineProps<{ assets: MarketAsset[] }>()

function isPositive(asset: MarketAsset): boolean {
  return compareDecimal(asset.change24hPercent, '0') >= 0
}
</script>

<template>
  <div class="market-preview">
    <ul v-if="assets.length" aria-label="خلاصه قیمت ارزها">
      <li v-for="asset in assets" :key="asset.symbol">
        <RouterLink :to="`/app/markets/${asset.symbol}`" class="market-preview__identity">
          <AssetAvatar :symbol="asset.symbol" :color="asset.color" />
          <span>
            <strong>{{ asset.nameFa }}</strong>
            <small dir="ltr">{{ asset.symbol }} · {{ asset.nameEn }}</small>
          </span>
        </RouterLink>

        <span class="market-preview__price">
          <small>قیمت خرید</small>
          <strong><bdi>{{ formatToman(asset.buyPriceToman, { showCurrency: false }) }}</bdi><em>تومان</em></strong>
        </span>

        <span class="market-preview__change" :class="isPositive(asset) ? 'up' : 'down'">
          <AppIcon :name="isPositive(asset) ? 'arrowUp' : 'arrowDown'" :size="14" />
          <bdi dir="ltr">{{ formatPercentage(asset.change24hPercent, { showSign: true }) }}</bdi>
        </span>

        <AppButton
          class="market-preview__action"
          size="sm"
          :disabled="!asset.tradable"
          :to="asset.tradable ? `/app/trade?side=buy&asset=${asset.symbol}` : undefined"
        >خرید</AppButton>
      </li>
    </ul>

    <div v-else class="market-preview__empty" role="status">
      در حال حاضر نرخی برای نمایش موجود نیست.
    </div>
  </div>
</template>

<style scoped>
.market-preview {
  min-width: 0;
  container: dashboard-market-preview / inline-size;
}

ul {
  display: grid;
  margin: 0;
  padding: 0;
  list-style: none;
}

li {
  display: grid;
  min-width: 0;
  min-height: 4.9rem;
  grid-template-columns: minmax(9.5rem, 1.18fr) minmax(10rem, 1fr) auto auto;
  align-items: center;
  gap: var(--space-4);
  padding: .75rem var(--space-4);
  border-block-end: 1px solid var(--color-border-soft);
  transition: background var(--transition-fast);
}

li:last-child { border-block-end: 0; }

.market-preview__identity {
  display: flex;
  min-width: 0;
  min-height: 2.75rem;
  align-items: center;
  gap: var(--space-3);
}

.market-preview__identity > span,
.market-preview__price {
  display: grid;
  min-width: 0;
  gap: .12rem;
  line-height: 1.45;
}

.market-preview__identity strong {
  min-width: 0;
  color: var(--color-text-primary);
  font-size: var(--font-size-sm);
  font-weight: 650;
  overflow-wrap: anywhere;
}

.market-preview__identity small,
.market-preview__price > small {
  color: var(--color-text-muted);
  font-size: .68rem;
}

.market-preview__identity small { overflow-wrap: anywhere; }

.market-preview__price strong {
  display: flex;
  min-width: 0;
  align-items: baseline;
  gap: .3rem;
  color: var(--color-text-primary);
  font-size: var(--font-size-sm);
  font-variant-numeric: tabular-nums;
  font-weight: 650;
  line-height: 1.55;
}

.market-preview__price bdi { min-width: 0; unicode-bidi: isolate; }
.market-preview__price em { flex: 0 0 auto; color: var(--color-text-muted); font-size: .68rem; font-style: normal; font-weight: 500; }

.market-preview__change {
  display: inline-flex;
  width: max-content;
  min-height: 1.8rem;
  align-items: center;
  gap: .18rem;
  padding-inline: .48rem;
  border-radius: var(--radius-pill);
  font-size: var(--font-size-xs);
  font-variant-numeric: tabular-nums;
  font-weight: 650;
  white-space: nowrap;
}

.market-preview__change.up { background: var(--color-success-soft); color: var(--color-success); }
.market-preview__change.down { background: var(--color-danger-soft); color: var(--color-danger); }

.market-preview__action {
  min-width: 4.5rem;
  flex-shrink: 0;
}

.market-preview__empty {
  padding: var(--space-7) var(--space-4);
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
  text-align: center;
}

@media (hover: hover) {
  li:hover { background: var(--color-surface-2); }
}

@container dashboard-market-preview (max-width: 31rem) {
  li {
    min-height: 0;
    grid-template-columns: minmax(0, 1fr) auto;
    gap: var(--space-3);
    padding-block: var(--space-4);
  }

  .market-preview__identity { grid-row: 1; grid-column: 1; }
  .market-preview__change { grid-row: 1; grid-column: 2; }
  .market-preview__price { grid-row: 2; grid-column: 1; padding-top: var(--space-2); border-block-start: 1px solid var(--color-border-soft); }
  .market-preview__action { grid-row: 2; grid-column: 2; align-self: end; }
}

@container dashboard-market-preview (max-width: 23rem) {
  li { padding-inline: var(--space-3); }
  .market-preview__identity { gap: var(--space-2); }
  .market-preview__change { padding-inline: .4rem; }
  .market-preview__action { min-width: 4.25rem; }
}
</style>
