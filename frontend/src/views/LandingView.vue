<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowLeft, ArrowUpRight, BadgeCheck, ChartArea, ShieldCheck, Sparkles, WalletCards, Zap } from 'lucide-vue-next'
import LandingNavbar from '../components/LandingNavbar.vue'
import { mockMarketPrices } from '../mock/data'

const router = useRouter()
const marketCards = computed(() => mockMarketPrices.slice(0, 4))

function goDashboard() {
  router.push('/dashboard')
}

function goLogin() {
  router.push('/login')
}
</script>

<template>
  <div class="landing-shell">
    <LandingNavbar />

    <main class="landing-page">
      <section class="hero container">
        <div class="hero-copy">
          <div class="eyebrow">
            <Sparkles :size="14" />
            <span>OTC Desk • Institutional Liquidity</span>
          </div>
          <h1>برای معاملات بزرگ، قیمت متفاوتی لازم است.</h1>
          <p>
            یک پلتفرم OTC حرفه‌ای برای خرید و فروش حجم‌های بالا، قیمت‌گذاری اختصاصی، تسویه امن و پشتیبانی سرمایه‌گذاری‌ای که با سرعت و دقت تصمیم می‌گیرد.
          </p>
          <div class="hero-actions">
            <button class="primary-btn large" type="button" @click="goDashboard">شروع معامله</button>
            <button class="ghost-btn large" type="button" @click="goLogin">درخواست قیمت</button>
          </div>
          <div class="hero-metrics">
            <div>
              <strong>۲۵M+</strong>
              <span>حجم ماهانه</span>
            </div>
            <div>
              <strong>۰.۰۸٪</strong>
              <span>کارمزد میانگین</span>
            </div>
            <div>
              <strong>۲۴/۷</strong>
              <span>پشتیبانی</span>
            </div>
          </div>
        </div>

        <div class="hero-panel premium-visual">
          <div class="hero-panel-header">
            <span class="status-pill success">بازار فعال</span>
            <span class="tiny-label">BTC / USDT</span>
          </div>
          <div class="hero-price-row">
            <div>
              <div class="tiny-label">قیمت لحظه‌ای</div>
              <div class="price-raw">$68,420</div>
            </div>
            <div class="delta up">+۲.۸٪</div>
          </div>

          <div class="trade-panel-mini">
            <div class="mini-row">
              <span>خرید</span>
              <strong>$68,420</strong>
            </div>
            <div class="mini-row">
              <span>فروش</span>
              <strong>$68,160</strong>
            </div>
            <div class="mini-row">
              <span>اسپرد</span>
              <strong>0.15%</strong>
            </div>
            <div class="mini-row">
              <span>حجم</span>
              <strong>$18.2M</strong>
            </div>
          </div>

          <div class="mini-actions">
            <button class="mini-buy">خرید</button>
            <button class="mini-sell">فروش</button>
          </div>
        </div>
      </section>

      <section id="about" class="container section-block">
        <div class="section-head">
          <div>
            <span class="section-kicker">چرا OTC؟</span>
            <h2>مزیت‌های تخصصی معاملات بزرگ</h2>
          </div>
        </div>
        <div class="feature-grid">
          <article class="feature-card">
            <div class="feature-icon"><BadgeCheck :size="18" /></div>
            <h3>قیمت‌گذاری اختصاصی</h3>
            <p>برای حجم‌های بزرگ، قیمت‌گذاری بر اساس شرایط واقعی بازار و نقدشوندگی اختصاصی انجام می‌شود.</p>
          </article>
          <article class="feature-card">
            <div class="feature-icon"><Zap :size="18" /></div>
            <h3>تسویه سریع</h3>
            <p>تسویه به‌صورت حرفه‌ای و با زمان پاسخ کوتاه برای سفارش‌های زیرساختی و پرمقدار.</p>
          </article>
          <article class="feature-card">
            <div class="feature-icon"><ShieldCheck :size="18" /></div>
            <h3>مدیریت ریسک</h3>
            <p>کدهای مجزا، بررسی دقیق و کنترل استاندارد برای معاملات حساس و حجم بالا.</p>
          </article>
          <article class="feature-card">
            <div class="feature-icon"><WalletCards :size="18" /></div>
            <h3>نقدشوندگی بالا</h3>
            <p>دسترسی به تامین‌کننده‌های معتبر برای اجرای سفارش‌های بزرگ بدون فشار بر نرخ بازار.</p>
          </article>
        </div>
      </section>

      <section id="otc" class="container section-block process-block">
        <div class="section-head center">
          <span class="section-kicker">چگونه کار می‌کند؟</span>
          <h2>معامله در سه مرحله حرفه‌ای</h2>
        </div>
        <div class="steps-grid">
          <div class="step-card">
            <span class="step-index">01</span>
            <h3>ثبت درخواست</h3>
            <p>دارایی و حجم مورد نظر را تعیین کنید و درخواست خود را در سیستم ثبت کنید.</p>
          </div>
          <div class="step-card">
            <span class="step-index">02</span>
            <h3>دریافت قیمت</h3>
            <p>تیم ما قیمت اختصاصی و شرایط تسویه را برای شما با جزئیات اعلام می‌کند.</p>
          </div>
          <div class="step-card">
            <span class="step-index">03</span>
            <h3>تأیید و تسویه</h3>
            <p>پس از تأیید، عملیات تسویه با کنترل ریسک و پیگیری حرفه‌ای انجام می‌شود.</p>
          </div>
        </div>
      </section>

      <section id="market" class="container section-block">
        <div class="section-head split">
          <div>
            <span class="section-kicker">بازار</span>
            <h2>قیمت‌های لحظه‌ای</h2>
          </div>
          <button class="ghost-btn" type="button" @click="goDashboard">ورود به داشبورد</button>
        </div>

        <div class="market-grid">
          <article v-for="item in marketCards" :key="item.pair" class="market-card">
            <div class="market-topline">
              <div class="pair-tag">{{ item.pair }}</div>
              <span :class="['delta', item.trend === 'up' ? 'up' : 'down']">{{ item.pct }}%</span>
            </div>
            <div class="market-price">{{ Number(item.buy).toLocaleString('fa-IR') }}</div>
            <div class="market-meta">
              <span>خرید {{ Number(item.buy).toLocaleString('fa-IR') }}</span>
              <span>فروش {{ Number(item.sell).toLocaleString('fa-IR') }}</span>
            </div>
          </article>
        </div>
      </section>

      <section id="security" class="container section-block cta-banner">
        <div>
          <span class="section-kicker">امنیت و اعتماد</span>
          <h2>برای معاملات بزرگ آماده‌اید؟</h2>
          <p>درخواست خود را ثبت کنید تا تیم ما قیمت اختصاصی و مسیر تسویه را برایتان ارسال کند.</p>
        </div>
        <button class="primary-btn large" type="button" @click="goDashboard">ثبت درخواست معامله</button>
      </section>
    </main>

    <footer id="support" class="landing-footer">
      <div class="container footer-inner">
        <div>
          <div class="brand-wrap">
            <div class="brand-mark">
              <span>OT</span>
            </div>
            <div class="brand-copy small">
              <span class="brand-name">OTC</span>
              <small>Desk</small>
            </div>
          </div>
        </div>

        <div class="footer-links">
          <a href="#about">درباره ما</a>
          <a href="#market">بازار</a>
          <a href="#security">امنیت</a>
          <a href="#support">پشتیبانی</a>
        </div>
      </div>
    </footer>
  </div>
</template>
