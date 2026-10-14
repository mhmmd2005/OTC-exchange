
<script setup lang="ts">
import { computed, type Component } from 'vue'
import { getBankIdentity } from '@/constants/banks'
import type { IranianBank } from '@/types'

import {
  AyandehColorIcon,
  BankinoColorIcon,
  BluBankColorIcon,
  CaspianColorIcon,
  DeyColorIcon,
  EghtesadNovinColorIcon,
  FuturebankColorIcon,
  GardeshgariColorIcon,
  IranEuropeColorIcon,
  IranVenezuelaColorIcon,
  IranZaminColorIcon,
  KarafarinColorIcon,
  KeshavarziColorIcon,
  KhavarMianehColorIcon,
  MaskanColorIcon,
  MehrIranColorIcon,
  MelallColorIcon,
  MelliColorIcon,
  MellatColorIcon,
  NoorColorIcon,
  ParsianColorIcon,
  PasargadColorIcon,
  PostColorIcon,
  RefahColorIcon,
  ResalatColorIcon,
  SaderatColorIcon,
  SamanColorIcon,
  SanatMadanColorIcon,
  SarmayehColorIcon,
  SepahColorIcon,
  ShahrColorIcon,
  SinaColorIcon,
  StandardCharteredColorIcon,
  TaavonEslamiColorIcon,
  TejaratColorIcon,
  ToseeColorIcon,
  ToseeSaderatColorIcon,
  ToseeTaavonColorIcon,
} from '@iran-utils/iranian-banks-vue-icons'

const props = withDefaults(
  defineProps<{
    bank: Pick<IranianBank, 'id' | 'nameFa' | 'nameEn'>
    size?: 'sm' | 'md' | 'lg'
  }>(),
  {
    size: 'md',
  },
)

const identity = computed(() => getBankIdentity(props.bank))

const logoStyle = computed(() => ({
  '--bank-primary': identity.value.primary,
  '--bank-secondary': identity.value.secondary,
}))

/**
 * یکسان‌سازی شناسه و نام بانک:
 * - حذف فاصله و نیم‌فاصله
 * - تبدیل حروف عربی ی و ک به فارسی
 * - حذف نویسه‌های جهت‌دهی متن
 */
function normalizeBankKey(value: string): string {
  return value
    .normalize('NFKC')
    .toLocaleLowerCase('fa-IR')
    .replace(/[يى]/g, 'ی')
    .replace(/ك/g, 'ک')
    .replace(/[\s\u200c\u200f\u200e_-]+/g, '')
}

/**
 * کامپوننت لوگوهای موجود در کتابخانه
 */
const bankLogoComponents: Readonly<Record<string, Component>> = {
  ayandeh: AyandehColorIcon,
  bankino: BankinoColorIcon,
  blubank: BluBankColorIcon,
  caspian: CaspianColorIcon,
  dey: DeyColorIcon,
  eghtesadnovin: EghtesadNovinColorIcon,
  futurebank: FuturebankColorIcon,
  gardeshgari: GardeshgariColorIcon,
  iraneurope: IranEuropeColorIcon,
  iranvenezuela: IranVenezuelaColorIcon,
  iranzamin: IranZaminColorIcon,
  karafarin: KarafarinColorIcon,
  keshavarzi: KeshavarziColorIcon,
  khavarmianeh: KhavarMianehColorIcon,
  maskan: MaskanColorIcon,
  mehriran: MehrIranColorIcon,
  melall: MelallColorIcon,
  melli: MelliColorIcon,
  mellat: MellatColorIcon,
  noor: NoorColorIcon,
  parsian: ParsianColorIcon,
  pasargad: PasargadColorIcon,
  post: PostColorIcon,
  refah: RefahColorIcon,
  resalat: ResalatColorIcon,
  saderat: SaderatColorIcon,
  saman: SamanColorIcon,
  sanatmadan: SanatMadanColorIcon,
  sarmayeh: SarmayehColorIcon,
  sepah: SepahColorIcon,
  shahr: ShahrColorIcon,
  sina: SinaColorIcon,
  standardchartered: StandardCharteredColorIcon,
  taavoneslami: TaavonEslamiColorIcon,
  tejarat: TejaratColorIcon,
  tosee: ToseeColorIcon,
  toseesaderat: ToseeSaderatColorIcon,
  toseetaavon: ToseeTaavonColorIcon,
}

/**
 * نام‌های جایگزین بانک‌ها.
 *
 * کلیدها در پایین با همان تابع normalizeBankKey نرمال می‌شوند؛
 * بنابراین لازم نیست فاصله و نیم‌فاصله را دستی حذف کنیم.
 */
const rawBankAliases: Readonly<Record<string, string>> = {
  // بانک ملی
  'بانک ملی ایران': 'melli',
  'بانک ملی': 'melli',
  'ملی': 'melli',
  'Bank Melli Iran': 'melli',
  'Melli Bank of Iran': 'melli',
  'Bank Melli': 'melli',
  bmi: 'melli',
  bank_melli_iran: 'melli',

  // بانک ملت
  'بانک ملت': 'mellat',
  'ملت': 'mellat',
  'Bank Mellat': 'mellat',
  bank_mellat: 'mellat',

  // بانک پاسارگاد
  'بانک پاسارگاد': 'pasargad',
  'پاسارگاد': 'pasargad',
  'Bank Pasargad': 'pasargad',
  'Pasargad Bank': 'pasargad',
  bank_pasargad: 'pasargad',

  // بانک مرکزی: لوگوی اختصاصی در فهرست واردشده موجود نیست.
  'بانک مرکزی جمهوری اسلامی ایران': 'generic',
  'Central Bank of Iran': 'generic',

  // بانک دی
  'بانک دی': 'dey',
  'دی': 'dey',
  'Dey Bank': 'dey',
  dey_bank: 'dey',

  // بانک اقتصاد نوین
  'بانک اقتصاد نوین': 'eghtesadnovin',
  'اقتصاد نوین': 'eghtesadnovin',
  'Eghtesad Novin Bank': 'eghtesadnovin',
  eghtesad_novin_bank: 'eghtesadnovin',

  // بانک توسعه صادرات ایران
  'بانک توسعه صادرات ایران': 'toseesaderat',
  'بانک توسعه صادرات': 'toseesaderat',
  'توسعه صادرات ایران': 'toseesaderat',
  'Export Development Bank of Iran': 'toseesaderat',
  'Tosee Saderat Bank': 'toseesaderat',
  export_development_bank_of_iran: 'toseesaderat',

  // بانک گردشگری
  'بانک گردشگری': 'gardeshgari',
  'گردشگری': 'gardeshgari',
  'Gardeshgari Bank': 'gardeshgari',

  // بانک ایران زمین
  'بانک ایران زمین': 'iranzamin',
  'ایران زمین': 'iranzamin',
  'Iran Zamin Bank': 'iranzamin',

  // بانک کارآفرین
  'بانک کارآفرین': 'karafarin',
  'کارآفرین': 'karafarin',
  'Karafarin Bank': 'karafarin',

  // بانک کشاورزی
  'بانک کشاورزی': 'keshavarzi',
  'کشاورزی': 'keshavarzi',
  'Keshavarzi Bank': 'keshavarzi',

  // بانک مسکن
  'بانک مسکن': 'maskan',
  'مسکن': 'maskan',
  'Maskan Bank': 'maskan',

  // بانک قرض‌الحسنه مهر ایران
  'بانک قرض الحسنه مهر ایران': 'mehriran',
  'بانک قرض‌الحسنه مهر ایران': 'mehriran',
  'قرض الحسنه مهر ایران': 'mehriran',
  'قرض‌الحسنه مهر ایران': 'mehriran',
  'Mehr Iran Bank': 'mehriran',
  mehr_iran_bank: 'mehriran',

  // مؤسسه اعتباری ملل
  'مؤسسه اعتباری ملل': 'melall',
  'موسسه اعتباری ملل': 'melall',
  'مؤسسه ملل': 'melall',
  'موسسه ملل': 'melall',
  'بانک ملل': 'melall',
  'Melal Credit Institution': 'melall',
  'Melall Credit Institution': 'melall',
  melal_credit_institution: 'melall',

  // بانک خاورمیانه
  'بانک خاورمیانه': 'khavarmianeh',
  'خاورمیانه': 'khavarmianeh',
  'Middle East Bank': 'khavarmianeh',

  // بانک پارسیان
  'بانک پارسیان': 'parsian',
  'پارسیان': 'parsian',
  'Parsian Bank': 'parsian',

  // پست بانک ایران
  'پست بانک ایران': 'post',
  'پست بانک': 'post',
  'Post Bank Iran': 'post',
  'Post Bank': 'post',

  // بانک رفاه کارگران
  'بانک رفاه کارگران': 'refah',
  'بانک رفاه': 'refah',
  'رفاه': 'refah',
  'Refah Kargaran Bank': 'refah',

  // بانک قرض‌الحسنه رسالت
  'بانک قرض الحسنه رسالت': 'resalat',
  'بانک قرض‌الحسنه رسالت': 'resalat',
  'بانک رسالت': 'resalat',
  'رسالت': 'resalat',
  'Resalat Bank': 'resalat',

  // بانک صادرات ایران
  'بانک صادرات ایران': 'saderat',
  'بانک صادرات': 'saderat',
  'صادرات': 'saderat',
  'Saderat Bank': 'saderat',

  // بانک سامان
  'بانک سامان': 'saman',
  'سامان': 'saman',
  'Saman Bank': 'saman',
  samanbank: 'saman',

  // بانک صنعت و معدن
  'بانک صنعت و معدن': 'sanatmadan',
  'صنعت و معدن': 'sanatmadan',
  'Sanat o Madan Bank': 'sanatmadan',

  // بانک سرمایه
  'بانک سرمایه': 'sarmayeh',
  'سرمایه': 'sarmayeh',
  'Sarmayeh Bank': 'sarmayeh',

  // بانک سپه
  'بانک سپه': 'sepah',
  'سپه': 'sepah',
  'Sepah Bank': 'sepah',

  // بانک شهر
  'بانک شهر': 'shahr',
  'شهر': 'shahr',
  'Shahr Bank': 'shahr',

  // بانک سینا
  'بانک سینا': 'sina',
  'سینا': 'sina',
  'Sina Bank': 'sina',

  // بانک تجارت
  'بانک تجارت': 'tejarat',
  'تجارت': 'tejarat',
  'Tejarat Bank': 'tejarat',

  // بانک توسعه تعاون
  'بانک توسعه تعاون': 'toseetaavon',
  'توسعه تعاون': 'toseetaavon',
  'Tosee Taavon Bank': 'toseetaavon',

  // بانک آینده
  'بانک آینده': 'ayandeh',
  'آینده': 'ayandeh',
  'Ayandeh Bank': 'ayandeh',

  // بانکینو
  'بانکینو': 'bankino',
  'Bankino': 'bankino',

  // بلوبانک
  'بلوبانک': 'blubank',
  'بلو بانک': 'blubank',
  'Blu Bank': 'blubank',
  'BluBank': 'blubank',

  // بانک کاسپین
  'بانک کاسپین': 'caspian',
  'کاسپین': 'caspian',
  'Caspian Bank': 'caspian',

  // بانک ایران و اروپا
  'بانک ایران و اروپا': 'iraneurope',
  'ایران و اروپا': 'iraneurope',
  'Iran Europe Bank': 'iraneurope',

  // بانک مشترک ایران و ونزوئلا
  'بانک ایران و ونزوئلا': 'iranvenezuela',
  'بانک مشترک ایران و ونزوئلا': 'iranvenezuela',
  'Iran Venezuela Bank': 'iranvenezuela',

  // مؤسسه نور
  'مؤسسه اعتباری نور': 'noor',
  'موسسه اعتباری نور': 'noor',
  'مؤسسه نور': 'noor',
  'موسسه نور': 'noor',
  'بانک نور': 'noor',
  'Noor Credit Institution': 'noor',

  // بانک استاندارد چارترد
  'Standard Chartered': 'standardchartered',
  'Standard Chartered Bank': 'standardchartered',

  // بانک تعاون اسلامی
  'بانک تعاون اسلامی': 'taavoneslami',
  'تعاون اسلامی': 'taavoneslami',
  'Taavon Eslami Bank': 'taavoneslami',
}

/**
 * نرمال‌سازی خودکار کلیدهای alias:
 * هم تعریف alias و هم نام دریافتی از API از یک تابع استفاده می‌کنند.
 */
const bankAliases: Readonly<Record<string, string>> = Object.freeze(
  Object.fromEntries(
    Object.entries(rawBankAliases).map(([alias, logoKey]) => [
      normalizeBankKey(alias),
      logoKey,
    ]),
  ),
)

/**
 * تعیین لوگو با اولویت:
 * 1. شناسه بانک
 * 2. نام فارسی
 * 3. نام انگلیسی
 */
const logoComponent = computed<Component | null>(() => {
  const candidates = [
    props.bank.id,
    props.bank.nameFa,
    props.bank.nameEn,
  ].filter(Boolean)

  for (const candidate of candidates) {
    const key = normalizeBankKey(candidate)

    // ابتدا شناسه مستقیم لوگو بررسی می‌شود.
    if (bankLogoComponents[key]) {
      return bankLogoComponents[key]
    }

    // سپس نام‌های جایگزین بررسی می‌شوند.
    const alias = bankAliases[key]

    if (alias === 'generic') {
      return null
    }

    if (alias && bankLogoComponents[alias]) {
      return bankLogoComponents[alias]
    }
  }

  return null
})

const fallbackMonogram = computed(() => {
  if (identity.value.mark !== 'generic') {
    return identity.value.monogram
  }

  const name = props.bank.nameFa
    .replace(/^بانک\s*/, '')
    .trim()

  return name.slice(0, 2) || 'ب'
})
</script>

<template>
  <span
    class="bank-logo"
    :class="[
      `bank-logo--${size}`,
      `bank-logo--${identity.mark}`,
    ]"
    :style="logoStyle"
    aria-hidden="true"
  >
    <component
      :is="logoComponent"
      v-if="logoComponent"
      class="bank-logo__asset"
      width="100%"
      height="100%"
      focusable="false"
    />

    <span
      v-else
      class="bank-logo__fallback"
    >
      {{ fallbackMonogram }}
    </span>
  </span>
</template>

<style scoped>
.bank-logo {
  display: grid;
  flex: 0 0 auto;
  overflow: hidden;
  border: 1px solid
    color-mix(in srgb, var(--bank-primary) 34%, transparent);
  border-radius: 1rem;
  background:
    radial-gradient(
      circle at 28% 18%,
      color-mix(
        in srgb,
        var(--bank-secondary) 34%,
        transparent
      ),
      transparent 48%
    ),
    color-mix(
      in srgb,
      var(--bank-primary) 12%,
      var(--surface-secondary)
    );
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, .08),
    0 8px 24px
      color-mix(in srgb, var(--bank-primary) 13%, transparent);
  color: var(--bank-primary);
  place-items: center;
}

.bank-logo--sm {
  width: 2.5rem;
  height: 2.5rem;
  border-radius: .75rem;
}

.bank-logo--md {
  width: 3rem;
  height: 3rem;
}

.bank-logo--lg {
  width: 3.75rem;
  height: 3.75rem;
  border-radius: 1.15rem;
}

.bank-logo__asset {
  display: block;
  width: 78%;
  height: 78%;
}

.bank-logo__fallback {
  color: var(--bank-primary);
  font-size: 1.05rem;
  font-weight: 800;
  line-height: 1;
}

.bank-logo--lg .bank-logo__fallback {
  font-size: 1.3rem;
}
</style>
