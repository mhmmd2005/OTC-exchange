<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink } from 'vue-router'
import AppIcon from '@/components/ui/AppIcon.vue'
import AppLogo from '@/components/layout/AppLogo.vue'
import { LEGAL_DOCUMENTS } from '@/constants/legal'

const props = defineProps<{ document: 'terms' | 'privacy' }>()

const content = computed(() => props.document === 'terms' ? {
  title: 'شرایط استفاده از روشا',
  intro: 'این سند چارچوب استفاده از پنل مشتریان و خدمات معامله مستقیم رمزارز روشا را توضیح می‌دهد.',
  version: LEGAL_DOCUMENTS.terms.version,
  publishedAt: LEGAL_DOCUMENTS.terms.publishedAtFa,
  sections: [
    ['۱. دامنه خدمات', 'روشا بستری برای خرید رمزارز از صرافی و فروش رمزارز به صرافی به‌صورت OTC است. این پنل بازار همتا‌به‌همتا، دفتر سفارش عمومی یا پایانه معاملات لحظه‌ای ارائه نمی‌کند.'],
    ['۲. شرایط حساب', 'اطلاعات هویتی، شماره موبایل و حساب بانکی باید متعلق به صاحب حساب کاربری و صحیح باشند. مسئولیت حفاظت از رمز عبور، کدهای یک‌بارمصرف و ابزار ورود دومرحله‌ای بر عهده کاربر است.'],
    ['۳. نرخ، کارمزد و نهایی‌شدن سفارش', 'نرخ و کارمزد پیش از تأیید نهایی نمایش داده می‌شود و فقط تا زمان درج‌شده اعتبار دارد. پس از پایان مهلت، دریافت و تأیید نرخ تازه الزامی است. سوابق سفارش و تراکنش مبنای پیگیری عملیات هستند.'],
    ['۴. واریز و برداشت', 'واریز یا برداشت فقط از مسیرها، شبکه‌ها و حساب‌های تأییدشده انجام می‌شود. انتخاب شبکه یا نشانی نادرست ممکن است به از دست رفتن دارایی منجر شود. محدودیت‌ها، کارمزد شبکه و زمان تقریبی پیش از ثبت درخواست نمایش داده می‌شوند.'],
    ['۵. کنترل‌های قانونی و امنیتی', 'روشا می‌تواند برای رعایت الزامات قانونی، مدیریت ریسک یا حفاظت از حساب، احراز هویت تکمیلی بخواهد یا عملیات مشکوک را تا پایان بررسی متوقف کند. تلاش برای دورزدن کنترل‌ها مجاز نیست.'],
    ['۶. دسترس‌پذیری و پشتیبانی', 'ممکن است برخی دارایی‌ها یا شبکه‌ها برای نگهداری موقتاً در دسترس نباشند. وضعیت عملیات در پنل اعلام می‌شود و درخواست‌های پشتیبانی از بخش پشتیبانی قابل ثبت و پیگیری‌اند.'],
    ['۷. تغییر سند', 'در صورت تغییر مهم شرایط، نسخه جدید و تاریخ انتشار اعلام می‌شود و هرجا لازم باشد پذیرش دوباره از کاربر دریافت خواهد شد.'],
  ],
} : {
  title: 'سیاست حریم خصوصی روشا',
  intro: 'در این سند توضیح می‌دهیم چه داده‌ای برای ارائه امن خدمات لازم است و چگونه با آن رفتار می‌شود.',
  version: LEGAL_DOCUMENTS.privacy.version,
  publishedAt: LEGAL_DOCUMENTS.privacy.publishedAtFa,
  sections: [
    ['۱. داده‌های مورد نیاز', 'اطلاعات ثبت‌نام و احراز هویت، حساب‌های بانکی، سوابق سفارش و تراکنش، درخواست‌های پشتیبانی و داده‌های فنی امنیتی مانند نشست‌ها و رویدادهای ورود برای ارائه خدمت پردازش می‌شوند.'],
    ['۲. هدف پردازش', 'داده‌ها برای ساخت و حفاظت حساب، انجام معامله و تسویه، پیشگیری از تقلب، رعایت تکالیف قانونی، پاسخ‌گویی پشتیبانی و بهبود پایداری خدمت استفاده می‌شوند.'],
    ['۳. نگهداری و حفاظت', 'دسترسی به داده‌ها بر اساس نیاز کاری محدود می‌شود و کنترل‌های فنی و سازمانی متناسب برای حفاظت از محرمانگی و تمامیت اطلاعات به‌کار می‌روند. رمزها و کدهای امنیتی نباید از مسیر پشتیبانی درخواست شوند.'],
    ['۴. اشتراک‌گذاری محدود', 'اطلاعات فقط در حد لازم با ارائه‌دهندگان زیرساخت، پرداخت و احراز هویت یا مراجع دارای صلاحیت قانونی به اشتراک گذاشته می‌شود. فروش داده شخصی بخشی از مدل کسب‌وکار روشا نیست.'],
    ['۵. مدت نگهداری', 'داده‌ها تا زمانی که برای ارائه خدمت، حل اختلاف، امنیت و تکالیف قانونی لازم باشند نگهداری می‌شوند و سپس مطابق رویه‌های امن حذف یا ناشناس‌سازی خواهند شد.'],
    ['۶. انتخاب‌ها و درخواست‌های شما', 'می‌توانید اطلاعات نمایه و تنظیمات ارتباطی را در پنل مدیریت کنید و برای پرسش درباره دسترسی، اصلاح یا وضعیت نگهداری داده، درخواست پشتیبانی ثبت کنید. برخی سوابق مالی به‌دلیل الزام قانونی قابل حذف فوری نیستند.'],
    ['۷. تغییر سیاست', 'نسخه و تاریخ انتشار این سیاست در همین صفحه درج می‌شود. تغییرهای مهم از مسیر مناسب به اطلاع کاربران می‌رسند.'],
  ],
})
</script>

<template>
  <div class="legal-shell">
    <a class="skip-link" href="#legal-content">پرش به متن سند</a>
    <header class="legal-header">
      <AppLogo to="/auth/register" />
      <RouterLink class="back-link" to="/auth/register"><AppIcon name="chevronRight" :size="18" /> بازگشت به ثبت‌نام</RouterLink>
    </header>
    <main id="legal-content" class="legal-content">
      <article>
        <div class="legal-title">
          <span><AppIcon name="shield" :size="18" /> سند رسمی روشا</span>
          <h1>{{ content.title }}</h1>
          <p>{{ content.intro }}</p>
          <dl><div><dt>تاریخ انتشار</dt><dd>{{ content.publishedAt }}</dd></div><div><dt>شناسه نسخه</dt><dd dir="ltr">{{ content.version }}</dd></div></dl>
        </div>
        <section v-for="section in content.sections" :key="section[0]">
          <h2>{{ section[0] }}</h2>
          <p>{{ section[1] }}</p>
        </section>
        <aside><AppIcon name="info" :size="20" /><p>برای پرسش درباره این سند، پس از ورود از بخش پشتیبانی درخواست ثبت کنید.</p></aside>
      </article>
    </main>
  </div>
</template>

<style scoped>
.legal-shell { min-height: 100dvh; background: radial-gradient(circle at 85% 0, rgba(67,139,255,.1), transparent 28rem), var(--color-bg-app); }
.legal-header { display: flex; max-width: 64rem; min-height: 5.25rem; align-items: center; justify-content: space-between; gap: var(--space-4); margin-inline: auto; padding-inline: var(--space-5); border-bottom: 1px solid var(--color-border-soft); }
.legal-header > a:first-child { display: inline-flex; }
.back-link { display: inline-flex; align-items: center; gap: var(--space-1); color: var(--color-primary); font-size: var(--font-size-sm); font-weight: 600; }
.legal-content { width: min(100% - 2rem, 54rem); margin-inline: auto; padding-block: clamp(2rem, 6vw, 4.5rem); }
article { padding: clamp(1.25rem, 4vw, 3rem); border: 1px solid var(--color-border); border-radius: var(--radius-xl); background: var(--color-surface-1); box-shadow: var(--shadow-card); }
.legal-title { padding-bottom: var(--space-7); border-bottom: 1px solid var(--color-border); }
.legal-title > span { display: inline-flex; align-items: center; gap: var(--space-2); color: var(--color-primary); font-size: var(--font-size-xs); font-weight: 700; }
h1 { margin: var(--space-3) 0 var(--space-2); font-size: clamp(1.65rem, 5vw, 2.4rem); }
.legal-title > p, section p { color: var(--color-text-secondary); line-height: 2.05; }
dl { display: flex; flex-wrap: wrap; gap: var(--space-3); margin: var(--space-5) 0 0; }
dl div { display: flex; gap: var(--space-2); padding: .55rem .8rem; border-radius: var(--radius-sm); background: var(--color-surface-2); font-size: var(--font-size-xs); }
dt { color: var(--color-text-muted); } dd { margin: 0; font-weight: 600; }
section { padding-block: var(--space-6); border-bottom: 1px solid var(--color-border-soft); }
section h2 { margin: 0 0 var(--space-2); font-size: var(--font-size-lg); }
section p { margin: 0; }
aside { display: flex; gap: var(--space-3); margin-top: var(--space-6); padding: var(--space-4); border-radius: var(--radius-md); background: var(--color-info-soft); color: var(--color-info); }
aside p { margin: 0; line-height: 1.8; }
@media (max-width: 600px) { .legal-header { min-height: 4.5rem; padding-inline: var(--space-4); }.legal-content { width: min(100% - 1rem, 54rem); padding-block: .5rem 2rem; } article { border-inline: 0; border-radius: 0 0 var(--radius-xl) var(--radius-xl); } .back-link { font-size: var(--font-size-xs); } dl { display: grid; } }
</style>
