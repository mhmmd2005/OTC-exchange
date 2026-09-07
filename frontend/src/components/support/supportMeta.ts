import type { SupportCategory } from '@/types'

export interface SupportCategoryMeta {
  label: string
  icon: string
}

export const SUPPORT_CATEGORIES: ReadonlyArray<SupportCategoryMeta & { value: SupportCategory }> = [
  { value: 'trade', label: 'خرید و فروش', icon: 'trade' },
  { value: 'deposit', label: 'واریز', icon: 'arrowDown' },
  { value: 'withdrawal', label: 'برداشت', icon: 'arrowUp' },
  { value: 'verification', label: 'احراز هویت', icon: 'verify' },
  { value: 'bank', label: 'حساب بانکی', icon: 'bank' },
  { value: 'security', label: 'امنیت', icon: 'shield' },
  { value: 'technical', label: 'مشکل فنی', icon: 'settings' },
  { value: 'other', label: 'سایر', icon: 'help' },
]

export function supportCategoryMeta(category: SupportCategory): SupportCategoryMeta {
  return SUPPORT_CATEGORIES.find((item) => item.value === category)
    ?? { label: 'سایر', icon: 'help' }
}
