<script setup lang="ts">
import { computed } from 'vue'
import type { DepositAddress } from '@/types'
import { formatCrypto, toPersianDigits } from '@/utils/formatters'
import AppCard from '@/components/ui/AppCard.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import CopyButton from '@/components/ui/CopyButton.vue'
import QrCode from './QrCode.vue'

const props = defineProps<{
  depositAddress: DepositAddress
  assetName?: string
  networkName?: string
}>()

const displayAsset = computed(() => props.assetName || props.depositAddress.assetSymbol)
const displayNetwork = computed(() => props.networkName || props.depositAddress.networkCode)
const minimumDeposit = computed(() => formatCrypto(props.depositAddress.minimumDeposit, {
  symbol: props.depositAddress.assetSymbol,
  maximumFractionDigits: 8,
}))
</script>

<template>
  <AppCard class="deposit-card" padding="none">
    <header class="deposit-card__header">
      <span class="deposit-card__header-icon" aria-hidden="true"><AppIcon name="qr" :size="22" /></span>
      <span>
        <strong>آدرس واریز {{ displayAsset }}</strong>
        <small>شبکه {{ displayNetwork }}</small>
      </span>
    </header>

    <div class="deposit-card__content">
      <div class="deposit-card__qr">
        <QrCode :value="depositAddress.address" :label="`کد QR آدرس واریز ${displayAsset} روی شبکه ${displayNetwork}`" />
        <span><AppIcon name="qr" :size="15" />برای اسکن، دوربین کیف پول را روبه‌روی کد بگیرید</span>
      </div>

      <div class="deposit-card__details">
        <section class="address-block">
          <div class="address-block__title">
            <span>
              <small>آدرس کیف پول</small>
              <b dir="ltr">{{ depositAddress.networkCode }}</b>
            </span>
            <CopyButton :value="depositAddress.address" label="کپی آدرس" />
          </div>
          <code dir="ltr">{{ depositAddress.address }}</code>
        </section>

        <section v-if="depositAddress.memo" class="address-block address-block--memo">
          <div class="address-block__title">
            <span>
              <small>ممو / تگ مقصد</small>
              <b>وارد کردن ممو الزامی است</b>
            </span>
            <CopyButton :value="depositAddress.memo" label="کپی ممو" />
          </div>
          <code dir="ltr">{{ depositAddress.memo }}</code>
        </section>

        <dl class="deposit-card__facts">
          <div>
            <dt><AppIcon name="arrowDown" :size="17" />حداقل واریز</dt>
            <dd dir="ltr">{{ minimumDeposit }}</dd>
          </div>
          <div>
            <dt><AppIcon name="check" :size="17" />تأییدهای موردنیاز</dt>
            <dd>{{ toPersianDigits(depositAddress.requiredConfirmations) }} تأیید شبکه</dd>
          </div>
        </dl>
      </div>
    </div>

    <footer class="deposit-card__warning" role="note">
      <span aria-hidden="true"><AppIcon name="warning" :size="20" /></span>
      <p>
        فقط <strong dir="ltr">{{ depositAddress.assetSymbol }}</strong> را روی شبکه
        <strong>{{ displayNetwork }}</strong> به این آدرس ارسال کنید. ارسال دارایی یا انتخاب شبکه دیگر ممکن است باعث از دست رفتن دارایی شود.
      </p>
    </footer>
  </AppCard>
</template>

<style scoped>
.deposit-card { overflow: hidden; }
.deposit-card__header { display: flex; align-items: center; gap: var(--space-3); padding: var(--space-4) var(--space-5); border-block-end: 1px solid var(--color-border-soft); background: linear-gradient(90deg, transparent, var(--color-primary-soft)); }
.deposit-card__header-icon { display: grid; width: 2.7rem; height: 2.7rem; flex: 0 0 auto; border: 1px solid rgba(67, 139, 255, .2); border-radius: var(--radius-md); background: var(--color-primary-soft); color: var(--color-primary); place-items: center; }
.deposit-card__header > span:last-child { display: grid; }
.deposit-card__header strong { font-size: var(--font-size-lg); font-weight: 600; }
.deposit-card__header small { color: var(--color-text-muted); font-size: var(--font-size-xs); }
.deposit-card__content { display: grid; grid-template-columns: 13rem minmax(0, 1fr); gap: var(--space-6); padding: var(--space-5); }
.deposit-card__qr { display: flex; min-width: 0; flex-direction: column; align-items: center; justify-content: center; gap: var(--space-3); padding: var(--space-4); border: 1px solid var(--color-border-soft); border-radius: var(--radius-lg); background: var(--color-surface-2); }
.deposit-card__qr :deep(.qr-code) { width: 10.5rem; height: 10.5rem; box-shadow: 0 8px 24px rgba(0, 0, 0, .18); }
.deposit-card__qr > span { display: inline-flex; align-items: flex-start; gap: var(--space-1); color: var(--color-text-muted); font-size: .68rem; line-height: 1.55; text-align: center; }
.deposit-card__qr > span svg { flex: 0 0 auto; margin-top: .15rem; }
.deposit-card__details { display: grid; min-width: 0; align-content: start; gap: var(--space-3); }
.address-block { display: grid; gap: var(--space-3); min-width: 0; padding: var(--space-4); border: 1px solid var(--color-border); border-radius: var(--radius-md); background: var(--color-surface-2); }
.address-block--memo { border-color: rgba(242, 184, 75, .24); background: linear-gradient(135deg, var(--color-warning-soft), var(--color-surface-2) 55%); }
.address-block__title { display: flex; min-width: 0; align-items: center; justify-content: space-between; gap: var(--space-3); }
.address-block__title > span { display: grid; min-width: 0; }
.address-block__title small { color: var(--color-text-muted); font-size: var(--font-size-xs); }
.address-block__title b { color: var(--color-text-secondary); font-size: .7rem; font-weight: 500; }
.address-block--memo .address-block__title b { color: var(--color-warning); }
.address-block code { overflow-wrap: anywhere; color: var(--color-text-primary); font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: var(--font-size-sm); line-height: 1.75; text-align: left; unicode-bidi: isolate; }
.deposit-card__facts { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--space-3); margin: 0; }
.deposit-card__facts > div { display: grid; gap: .2rem; padding: var(--space-3) var(--space-4); border-radius: var(--radius-md); background: var(--color-surface-2); }
.deposit-card__facts dt { display: flex; align-items: center; gap: var(--space-1); color: var(--color-text-muted); font-size: var(--font-size-xs); }
.deposit-card__facts dt svg { color: var(--color-primary); }
.deposit-card__facts dd { margin: 0; color: var(--color-text-secondary); font-size: var(--font-size-sm); font-weight: 600; }
.deposit-card__warning { display: flex; align-items: flex-start; gap: var(--space-3); margin: 0 var(--space-5) var(--space-5); padding: var(--space-3) var(--space-4); border: 1px solid rgba(242, 184, 75, .2); border-radius: var(--radius-md); background: var(--color-warning-soft); color: var(--color-warning); }
.deposit-card__warning > span { display: grid; width: 2rem; height: 2rem; flex: 0 0 auto; border-radius: var(--radius-sm); background: rgba(242, 184, 75, .1); place-items: center; }
.deposit-card__warning p { margin: 0; color: var(--color-text-secondary); font-size: var(--font-size-xs); line-height: 1.85; }
.deposit-card__warning strong { color: var(--color-warning); font-weight: 600; }
@media (max-width: 767px) {
  .deposit-card__header { padding: var(--space-4); }
  .deposit-card__header strong { font-size: var(--font-size-md); }
  .deposit-card__content { grid-template-columns: 1fr; gap: var(--space-4); padding: var(--space-4); }
  .deposit-card__qr { padding: var(--space-4); }
  .deposit-card__qr :deep(.qr-code) { width: 9.5rem; height: 9.5rem; }
  .deposit-card__facts { grid-template-columns: 1fr; }
  .deposit-card__warning { margin: 0 var(--space-4) var(--space-4); }
}
@media (max-width: 399px) {
  .address-block__title { align-items: flex-start; }
  .address-block__title :deep(.copy-button) { min-height: 2.25rem; padding-inline: var(--space-2); }
  .address-block__title :deep(.copy-button span) { display: none; }
}
</style>
