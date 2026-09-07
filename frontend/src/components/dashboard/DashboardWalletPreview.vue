<script setup lang="ts">
import type { WalletAsset } from '@/types'
import { formatCrypto, formatToman } from '@/utils/formatters'
import AppButton from '@/components/ui/AppButton.vue'
import AssetAvatar from '@/components/finance/AssetAvatar.vue'

defineProps<{
  assets: WalletAsset[]
  hidden?: boolean
}>()

function primaryValue(asset: WalletAsset): string {
  return asset.symbol === 'IRT'
    ? formatToman(asset.total, { showCurrency: false })
    : formatCrypto(asset.total)
}

function secondaryValue(asset: WalletAsset): string {
  return asset.symbol === 'IRT'
    ? formatToman(asset.available, { showCurrency: false })
    : formatToman(asset.tomanValue, { showCurrency: false })
}

function actionFor(asset: WalletAsset): { label: string; to: string } {
  if (asset.symbol === 'IRT') return { label: 'واریز', to: '/app/deposit/toman' }
  if (asset.buyEnabled) return { label: 'خرید', to: `/app/trade?side=buy&asset=${asset.symbol}` }
  if (asset.depositEnabled) return { label: 'واریز', to: `/app/deposit/crypto/${asset.symbol}` }
  return { label: 'جزئیات', to: `/app/wallet/${asset.symbol}` }
}
</script>

<template>
  <div class="wallet-preview">
    <ul v-if="assets.length" aria-label="خلاصه دارایی‌های کیف پول">
      <li v-for="asset in assets" :key="asset.symbol">
        <RouterLink :to="`/app/wallet/${asset.symbol}`" class="wallet-preview__identity">
          <AssetAvatar :symbol="asset.symbol" :color="asset.color" />
          <span>
            <strong>{{ asset.nameFa }}</strong>
            <small dir="ltr">{{ asset.symbol }} · {{ asset.nameEn }}</small>
          </span>
        </RouterLink>

        <span class="wallet-preview__value wallet-preview__value--primary">
          <small>{{ asset.symbol === 'IRT' ? 'موجودی تومان' : 'موجودی کل' }}</small>
          <strong>
            <bdi :dir="asset.symbol === 'IRT' ? 'rtl' : 'ltr'">{{ hidden ? '••••••' : primaryValue(asset) }}</bdi>
            <em>{{ asset.symbol === 'IRT' ? 'تومان' : asset.symbol }}</em>
          </strong>
        </span>

        <span class="wallet-preview__value wallet-preview__value--secondary">
          <small>{{ asset.symbol === 'IRT' ? 'قابل استفاده' : 'معادل روز' }}</small>
          <strong>
            <bdi>{{ hidden ? '••••••' : secondaryValue(asset) }}</bdi>
            <em>تومان</em>
          </strong>
        </span>

        <AppButton
          class="wallet-preview__action"
          size="sm"
          variant="secondary"
          :to="actionFor(asset).to"
        >{{ actionFor(asset).label }}</AppButton>
      </li>
    </ul>

    <div v-else class="wallet-preview__empty" role="status">
      هنوز دارایی‌ای برای نمایش در داشبورد ندارید.
    </div>
  </div>
</template>

<style scoped>
.wallet-preview {
  min-width: 0;
  container: dashboard-wallet-preview / inline-size;
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
  grid-template-columns: minmax(10rem, 1.15fr) minmax(10rem, .95fr) minmax(10rem, 1fr) auto;
  align-items: center;
  gap: var(--space-4);
  padding: .75rem var(--space-4);
  border-block-end: 1px solid var(--color-border-soft);
  transition: background var(--transition-fast);
}

li:last-child { border-block-end: 0; }

.wallet-preview__identity {
  display: flex;
  min-width: 0;
  min-height: 2.75rem;
  align-items: center;
  gap: var(--space-3);
}

.wallet-preview__identity > span,
.wallet-preview__value {
  display: grid;
  min-width: 0;
  gap: .12rem;
  line-height: 1.45;
}

.wallet-preview__identity strong {
  min-width: 0;
  color: var(--color-text-primary);
  font-size: var(--font-size-sm);
  font-weight: 650;
  overflow-wrap: anywhere;
}

.wallet-preview__identity small,
.wallet-preview__value > small {
  color: var(--color-text-muted);
  font-size: .68rem;
}

.wallet-preview__identity small { overflow-wrap: anywhere; }

.wallet-preview__value strong {
  display: flex;
  min-width: 0;
  align-items: baseline;
  gap: .3rem;
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  font-variant-numeric: tabular-nums;
  font-weight: 600;
  line-height: 1.55;
}

.wallet-preview__value--primary strong {
  color: var(--color-text-primary);
  font-weight: 680;
}

.wallet-preview__value bdi {
  min-width: 0;
  unicode-bidi: isolate;
}

.wallet-preview__value em {
  flex: 0 0 auto;
  color: var(--color-text-muted);
  font-size: .68rem;
  font-style: normal;
  font-weight: 500;
}

.wallet-preview__action {
  min-width: 4.5rem;
  flex-shrink: 0;
}

.wallet-preview__empty {
  padding: var(--space-7) var(--space-4);
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
  text-align: center;
}

@media (hover: hover) {
  li:hover { background: var(--color-surface-2); }
}

@container dashboard-wallet-preview (max-width: 50rem) {
  li {
    min-height: 0;
    grid-template-columns: minmax(0, 1fr) minmax(9rem, .72fr);
    gap: var(--space-3) var(--space-4);
    padding-block: var(--space-4);
  }

  .wallet-preview__identity { grid-row: 1; grid-column: 1; }
  .wallet-preview__action { grid-row: 1; grid-column: 2; justify-self: end; }
  .wallet-preview__value--primary { grid-row: 2; grid-column: 1; }
  .wallet-preview__value--secondary { grid-row: 2; grid-column: 2; }
}

@container dashboard-wallet-preview (max-width: 28rem) {
  li {
    grid-template-columns: minmax(0, 1fr) auto;
    gap: var(--space-2) var(--space-3);
    padding-inline: var(--space-3);
  }

  .wallet-preview__action { min-width: 4.25rem; }
  .wallet-preview__value--primary { grid-row: 2; grid-column: 1 / -1; padding-top: var(--space-2); border-block-start: 1px solid var(--color-border-soft); }
  .wallet-preview__value--secondary { grid-row: 3; grid-column: 1 / -1; }
  .wallet-preview__value--secondary { display: flex; align-items: baseline; justify-content: space-between; gap: var(--space-3); }
  .wallet-preview__value--secondary strong { justify-content: flex-end; text-align: end; }
}
</style>
