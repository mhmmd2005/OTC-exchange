<script setup lang="ts">
import { RouterView } from 'vue-router'
import AppIcon from '@/components/ui/AppIcon.vue'
import AppLogo from '@/components/layout/AppLogo.vue'

function focusRouteHeading(element: Element): void {
  const heading = element.querySelector<HTMLElement>('h1')
  if (!heading) return
  heading.tabIndex = -1
  heading.focus({ preventScroll: true })
}
</script>

<template>
  <div class="auth-shell">
    <a class="skip-link" href="#main-content">پرش به فرم اصلی</a>
    <div class="auth-shell__glow auth-shell__glow--one" aria-hidden="true" />
    <div class="auth-shell__glow auth-shell__glow--two" aria-hidden="true" />

    <aside class="auth-story" aria-label="درباره خدمات روشا">
      <div class="auth-story__brand">
        <AppLogo inverse />
        <span class="secure-pill">
          <span class="secure-pill__dot" aria-hidden="true" />
          ارتباط امن
        </span>
      </div>

      <div class="auth-story__content">
        <span class="auth-story__eyebrow">خرید و فروش مستقیم، بدون پیچیدگی بازار</span>
        <p class="auth-story__headline">دارایی دیجیتال شما،<br><span>شفاف و در دسترس.</span></p>
        <p>
          پیش از هر تأیید، نرخ، کارمزد و مبلغ نهایی را می‌بینید؛ سپس مستقیم
          از روشا می‌خرید یا به روشا می‌فروشید.
        </p>

        <div class="auth-story__features">
          <div class="story-feature">
            <span class="story-feature__icon"><AppIcon name="trade" :size="21" /></span>
            <span><strong>معامله مستقیم OTC</strong><small>بدون دفتر سفارش و ابزارهای پیچیده معامله‌گری</small></span>
          </div>
          <div class="story-feature">
            <span class="story-feature__icon"><AppIcon name="info" :size="21" /></span>
            <span><strong>نرخ و کارمزد شفاف</strong><small>مبلغ پرداختی و دریافتی پیش از تأیید نهایی</small></span>
          </div>
          <div class="story-feature">
            <span class="story-feature__icon"><AppIcon name="help" :size="21" /></span>
            <span><strong>پشتیبانی همراه</strong><small>پاسخ‌گویی کارشناسان در مسیر معاملات شما</small></span>
          </div>
        </div>
      </div>

      <div class="auth-story__footer">
        <span>© ۱۴۰۵ روشا</span>
        <span class="auth-story__footer-dot" aria-hidden="true" />
        <span>خرید و فروش مستقیم دارایی دیجیتال</span>
      </div>
    </aside>

    <main id="main-content" class="auth-content">
      <header class="auth-content__header">
        <AppLogo />
        <span class="mobile-secure"><AppIcon name="lock" :size="16" /> محیط امن</span>
      </header>

      <div class="auth-content__body">
        <RouterView v-slot="{ Component, route }">
          <Transition name="auth-page" mode="out-in" @after-enter="focusRouteHeading">
            <component :is="Component" :key="route.fullPath" />
          </Transition>
        </RouterView>
      </div>

      <footer class="auth-content__footer">
        <span><AppIcon name="shield" :size="16" /> ورود شما با ارتباط رمزنگاری‌شده محافظت می‌شود.</span>
      </footer>
    </main>
  </div>
</template>

<style scoped>
.auth-shell {
  position: relative;
  isolation: isolate;
  display: grid;
  grid-template-columns: minmax(24rem, .9fr) minmax(32rem, 1.1fr);
  min-height: 100vh;
  min-height: 100dvh;
  overflow: hidden;
  background: var(--color-bg-app);
}

.auth-shell__glow {
  position: fixed;
  z-index: -1;
  border-radius: 50%;
  pointer-events: none;
  filter: blur(4px);
}

.auth-shell__glow--one {
  inset: -16rem -13rem auto auto;
  width: 34rem;
  height: 34rem;
  background: radial-gradient(circle, rgba(67, 139, 255, .13), transparent 68%);
}

.auth-shell__glow--two {
  inset: auto auto -18rem 22%;
  width: 34rem;
  height: 34rem;
  background: radial-gradient(circle, rgba(221, 183, 110, .07), transparent 67%);
}

.auth-story {
  position: relative;
  display: flex;
  flex-direction: column;
  min-height: 100dvh;
  padding: clamp(2rem, 4vw, 4rem);
  overflow: hidden;
  border-inline-end: 1px solid rgba(153, 174, 201, .12);
  background:
    linear-gradient(145deg, rgba(17, 32, 51, .96), rgba(8, 21, 34, .92)),
    var(--color-bg-sidebar);
}

.auth-story::before {
  position: absolute;
  inset: auto -9rem -12rem auto;
  width: 33rem;
  height: 33rem;
  border: 1px solid rgba(67, 139, 255, .13);
  border-radius: 50%;
  box-shadow: 0 0 0 5rem rgba(67, 139, 255, .025), 0 0 0 10rem rgba(67, 139, 255, .018);
  content: '';
  pointer-events: none;
}

.auth-story::after {
  position: absolute;
  inset: 16% auto auto -5rem;
  width: 11rem;
  height: 11rem;
  border: 1px solid rgba(221, 183, 110, .1);
  border-radius: 2.5rem;
  content: '';
  transform: rotate(22deg);
  pointer-events: none;
}

.auth-story__brand,
.auth-story__footer {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
}

.secure-pill,
.mobile-secure {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  min-height: 2.25rem;
  padding-inline: .85rem;
  border: 1px solid rgba(53, 201, 149, .2);
  border-radius: var(--radius-pill);
  background: rgba(53, 201, 149, .07);
  color: #a7ebd2;
  font-size: var(--font-size-xs);
  font-weight: 600;
}

.secure-pill__dot {
  width: .45rem;
  height: .45rem;
  border-radius: 50%;
  background: var(--color-success);
  box-shadow: 0 0 0 .25rem rgba(53, 201, 149, .1);
}

.auth-story__content {
  position: relative;
  z-index: 1;
  width: min(100%, 35rem);
  margin-block: auto;
  padding-block: clamp(3rem, 8vh, 6rem);
}

.auth-story__eyebrow {
  display: inline-block;
  margin-bottom: var(--space-5);
  color: var(--color-gold);
  font-size: var(--font-size-sm);
  font-weight: 600;
  letter-spacing: -.01em;
}

.auth-story__headline {
  margin-bottom: var(--space-5);
  font-size: clamp(2rem, 3.4vw, 3.45rem);
  font-weight: 700;
  letter-spacing: -.055em;
  line-height: 1.45;
}

.auth-story__headline span { color: #77aaff; }

.auth-story__content > p {
  max-width: 31rem;
  margin-bottom: var(--space-8);
  color: var(--color-text-secondary);
  font-size: var(--font-size-md);
  line-height: 2;
}

.auth-story__features { display: grid; gap: var(--space-4); }

.story-feature {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  padding: .9rem;
  border: 1px solid transparent;
  border-radius: var(--radius-lg);
  transition: border-color var(--transition-base), background var(--transition-base);
}

.story-feature:hover {
  border-color: rgba(153, 174, 201, .1);
  background: rgba(255, 255, 255, .025);
}

.story-feature__icon {
  display: grid;
  width: 2.8rem;
  height: 2.8rem;
  flex: 0 0 auto;
  border: 1px solid rgba(67, 139, 255, .18);
  border-radius: .9rem;
  background: rgba(67, 139, 255, .09);
  color: #7db0ff;
  place-items: center;
}

.story-feature > span:last-child { display: grid; gap: .1rem; }
.story-feature strong { font-size: var(--font-size-sm); font-weight: 600; }
.story-feature small { color: var(--color-text-muted); font-size: var(--font-size-xs); }

.auth-story__footer {
  justify-content: flex-start;
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
}

.auth-story__footer-dot { width: .25rem; height: .25rem; border-radius: 50%; background: var(--color-border-hover); }

.auth-content {
  position: relative;
  display: flex;
  flex-direction: column;
  min-width: 0;
  min-height: 100dvh;
}

.auth-content__header {
  display: none;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
  padding: calc(var(--space-4) + var(--safe-top)) var(--space-5) var(--space-3);
}

.auth-content__body {
  display: grid;
  flex: 1;
  width: 100%;
  padding: clamp(2rem, 5vw, 5rem);
  place-items: center;
}

.auth-content__footer {
  display: flex;
  justify-content: center;
  padding: 0 var(--space-5) calc(var(--space-5) + var(--safe-bottom));
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
}

.auth-content__footer span { display: inline-flex; align-items: center; gap: var(--space-2); }
.auth-content__footer svg { color: var(--color-success); }

:deep(.auth-view) {
  width: min(100%, 30rem);
  border-color: rgba(153, 174, 201, .15);
  background: rgba(13, 26, 42, .82);
  box-shadow: 0 1.5rem 5rem rgba(0, 0, 0, .2);
  backdrop-filter: blur(16px);
}

:deep(.auth-intro) { margin-bottom: var(--space-7); }

:deep(.auth-kicker) {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  margin-bottom: var(--space-3);
  color: var(--color-primary);
  font-size: var(--font-size-xs);
  font-weight: 600;
}

:deep(.auth-kicker::before) {
  width: .45rem;
  height: .45rem;
  border-radius: 50%;
  background: currentColor;
  box-shadow: 0 0 0 .25rem rgba(67, 139, 255, .1);
  content: '';
}

:deep(.auth-title) {
  margin-bottom: var(--space-2);
  font-size: clamp(1.55rem, 3vw, 1.9rem);
  font-weight: 700;
  letter-spacing: -.04em;
}

:deep(.auth-description) {
  margin: 0;
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
  line-height: 1.9;
}

:deep(.auth-description strong) { color: var(--color-text-secondary); font-weight: 600; }
:deep(.auth-form) { display: grid; gap: var(--space-5); }
:deep(.auth-form__row) { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--space-3); }

:deep(.auth-form__meta) {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  min-height: 1.5rem;
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
}

:deep(.auth-link) {
  color: var(--color-primary);
  font-weight: 600;
  transition: color var(--transition-fast);
}

:deep(.auth-link:hover) { color: var(--color-primary-hover); }

:deep(.auth-alert) {
  display: flex;
  align-items: flex-start;
  gap: var(--space-3);
  padding: .8rem .9rem;
  border: 1px solid rgba(240, 108, 117, .2);
  border-radius: var(--radius-md);
  background: var(--color-danger-soft);
  color: #f5a2a8;
  font-size: var(--font-size-xs);
  line-height: 1.7;
}

:deep(.auth-alert--success) {
  border-color: rgba(53, 201, 149, .2);
  background: var(--color-success-soft);
  color: #8ce1c2;
}

:deep(.auth-alert svg) { flex: 0 0 auto; margin-top: .1rem; }

:deep(.auth-footer) {
  margin: var(--space-6) 0 0;
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
  text-align: center;
}

:deep(.auth-security-note) {
  display: flex;
  align-items: flex-start;
  gap: var(--space-3);
  padding: var(--space-3);
  border: 1px solid var(--color-border-soft);
  border-radius: var(--radius-md);
  background: rgba(255, 255, 255, .018);
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
  line-height: 1.7;
}

:deep(.auth-security-note svg) { flex: 0 0 auto; margin-top: .1rem; color: var(--color-success); }

.auth-page-enter-active,
.auth-page-leave-active { transition: opacity var(--transition-base), transform var(--transition-base); }
.auth-page-enter-from { opacity: 0; transform: translateY(.5rem); }
.auth-page-leave-to { opacity: 0; transform: translateY(-.25rem); }

@media (max-width: 1023px) {
  .auth-shell { grid-template-columns: minmax(19rem, .78fr) minmax(29rem, 1.22fr); }
  .auth-story { padding: var(--space-8); }
  .auth-story__headline { font-size: clamp(1.8rem, 3.5vw, 2.6rem); }
  .story-feature { padding-inline: 0; }
}

@media (max-width: 767px) {
  .auth-shell { display: block; overflow: visible; }
  .auth-story { display: none; }
  .auth-content { min-height: 100dvh; }
  .auth-content__header { display: flex; }
  .auth-content__body { padding: var(--space-4) var(--space-4) var(--space-7); place-items: start center; }
  .auth-content__footer { padding-bottom: calc(var(--space-4) + var(--safe-bottom)); text-align: center; }
  :deep(.auth-view) { margin-top: var(--space-2); background: rgba(13, 26, 42, .92); }
}

@media (max-width: 420px) {
  .auth-content__header { padding-inline: var(--space-4); }
  .mobile-secure { padding-inline: .7rem; }
  :deep(.auth-form__row) { grid-template-columns: 1fr; }
}
</style>
