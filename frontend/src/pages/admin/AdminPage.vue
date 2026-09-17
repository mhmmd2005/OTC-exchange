<script setup lang="ts">
import { ref } from 'vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import AppCard from '@/components/ui/AppCard.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import KycApplicationsPage from './KycApplicationsPage.vue'

const activeSection = ref('kyc')
</script>

<template>
  <div class="page admin-page">
    <PageHeader
      title="پنل مدیریت"
      description="مدیریت و بررسی اطلاعات کاربران سیستم."
    />

    <div class="admin-layout">
      <aside class="admin-sidebar">
        <AppCard
          padding="none"
          class="admin-sidebar-card"
        >
          <div class="admin-sidebar__header">
            <span class="admin-sidebar__icon">
              <AppIcon
                name="verify"
                :size="20"
              />
            </span>

            <div>
              <strong>مدیریت سیستم</strong>
              <span>بخش‌های مدیریتی</span>
            </div>
          </div>

          <div class="admin-sidebar__nav">
            <button
              type="button"
              class="admin-nav-item"
              :class="{
                active: activeSection === 'kyc',
              }"
              @click="activeSection = 'kyc'"
            >
              <span class="admin-nav-item__icon">
                <AppIcon
                  name="verify"
                  :size="18"
                />
              </span>

              <span class="admin-nav-item__content">
                <strong>احراز هویت</strong>

                <small>
                  بررسی و مدیریت درخواست‌ها
                </small>
              </span>

              <AppIcon
                name="chevronLeft"
                :size="16"
                class="admin-nav-item__arrow"
              />
            </button>
          </div>
        </AppCard>
      </aside>

      <main class="admin-content">
        <KycApplicationsPage
          v-if="activeSection === 'kyc'"
        />
      </main>
    </div>
  </div>
</template>

<style scoped>
.admin-page {
  display: grid;
  gap: .7rem;

  width: calc(100% - 3rem);
  margin-left: auto;
  margin-right: 0;

  transform: translateY(-.7rem);
}

.admin-layout {
  display: grid;
  grid-template-columns: 17rem minmax(0, 1fr);
  gap: 1rem;
  align-items: start;
  margin-top: -.75rem;
}

.admin-sidebar {
  position: sticky;
  top: 1rem;
}

.admin-sidebar-card {
  overflow: hidden;
}

.admin-sidebar__header {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: 1rem;
  border-bottom: 1px solid var(--color-border-soft);
}

.admin-sidebar__icon {
  display: grid;
  width: 2.55rem;
  height: 2.55rem;
  flex: 0 0 auto;
  border-radius: .8rem;
  background: var(--color-primary-soft);
  color: var(--color-primary);
  place-items: center;
}

.admin-sidebar__header > div {
  display: grid;
  gap: .1rem;
}

.admin-sidebar__header strong {
  color: var(--color-text-primary);
  font-size: var(--font-size-sm);
}

.admin-sidebar__header span {
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
}

.admin-sidebar__nav {
  padding: .55rem;
}

.admin-nav-item {
  display: flex;
  align-items: center;
  gap: .7rem;
  width: 100%;
  min-height: 3.4rem;
  padding: .6rem .7rem;
  border: 1px solid transparent;
  border-radius: .8rem;
  background: transparent;
  color: var(--color-text-secondary);
  text-align: right;
  cursor: pointer;
  transition:
    background var(--transition-fast),
    border-color var(--transition-fast),
    color var(--transition-fast);
}

.admin-nav-item:hover {
  background: var(--color-surface-2);
  color: var(--color-text-primary);
}

.admin-nav-item.active {
  border-color: var(--color-border-soft);
  background: var(--color-primary-soft);
  color: var(--color-primary);
}

.admin-nav-item__icon {
  display: grid;
  width: 2.15rem;
  height: 2.15rem;
  flex: 0 0 auto;
  border-radius: .65rem;
  background: var(--color-surface-2);
  place-items: center;
}

.admin-nav-item.active .admin-nav-item__icon {
  background: rgba(99, 102, 241, .12);
}

.admin-nav-item__content {
  display: grid;
  flex: 1;
  min-width: 0;
  gap: .12rem;
}

.admin-nav-item__content strong {
  font-size: var(--font-size-sm);
}

.admin-nav-item__content small {
  overflow: hidden;
  color: var(--color-text-muted);
  font-size: 11px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.admin-nav-item__arrow {
  flex: 0 0 auto;
  opacity: .5;
}

.admin-content {
  min-width: 0;
}

@media (max-width: 1100px) {
  .admin-page {
    width: 100%;
    margin-left: 0;
    margin-right: 0;
    transform: none;
  }

  .admin-layout {
    grid-template-columns: 16rem minmax(0, 1fr);
    gap: .9rem;
    margin-top: -.35rem;
  }
}

@media (max-width: 900px) {
  .admin-layout {
    grid-template-columns: 1fr;
    margin-top: 0;
  }

  .admin-sidebar {
    position: static;
  }
}
</style>