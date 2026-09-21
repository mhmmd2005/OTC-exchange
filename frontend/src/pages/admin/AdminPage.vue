<script setup lang="ts">
import {ref} from 'vue'
import {useRouter} from 'vue-router'
import AppIcon from '@/components/ui/AppIcon.vue'
import AppButton from '@/components/ui/AppButton.vue'
import KycApplicationsPage from './KycApplicationsPage.vue'
import {useAdminAuthStore} from '@/stores/adminAuth'

const router = useRouter()
const adminAuth = useAdminAuthStore()

const activeSection = ref('kyc')

async function logout(): Promise<void> {
    await adminAuth.logout()

    await router.replace({
        name: 'admin-login',
    })
}
</script>

<template>
    <div class="admin-shell">
        <aside class="admin-sidebar">
            <div class="admin-brand">
                <div class="admin-brand__icon">
                    <AppIcon
                        name="verify"
                        :size="23"
                    />
                </div>

                <div>
                    <strong>روشا</strong>
                    <span>پنل مدیریت</span>
                </div>
            </div>

            <nav class="admin-nav">
                <button
                    type="button"
                    class="admin-nav-item"
                    :class="{
                        active:
                            activeSection === 'kyc',
                    }"
                    @click="
                        activeSection = 'kyc'
                    "
                >
                    <span
                        class="admin-nav-item__icon"
                    >
                        <AppIcon
                            name="verify"
                            :size="19"
                        />
                    </span>

                    <span
                        class="admin-nav-item__content"
                    >
                        <strong>
                            احراز هویت
                        </strong>

                        <small>
                            بررسی درخواست‌ها
                        </small>
                    </span>

                    <AppIcon
                        name="chevronLeft"
                        :size="16"
                    />
                </button>
            </nav>

            <div class="admin-sidebar__footer">
                <div class="admin-identity">
                    <div class="admin-identity__avatar">
                        <AppIcon
                            name="user"
                            :size="17"
                        />
                    </div>

                    <div>
                        <strong>
                            مدیر سیستم
                        </strong>

                        <small dir="ltr">
                            {{
                                adminAuth.user?.email
                                || '—'
                            }}
                        </small>
                    </div>
                </div>

                <button
                    type="button"
                    class="admin-logout"
                    @click="logout"
                >
                    <AppIcon
                        name="logout"
                        :size="17"
                    />

                    خروج
                </button>
            </div>
        </aside>

        <div class="admin-main">
            <header class="admin-topbar">
                <div>
                    <strong>
                        پنل مدیریت
                    </strong>

                    <span>
                        مدیریت و نظارت سیستم
                    </span>
                </div>

                <div class="admin-topbar__status">
                    <span class="status-dot"></span>
                    مدیر فعال
                </div>
            </header>

            <main class="admin-content">
                <KycApplicationsPage
                    v-if="
                        activeSection === 'kyc'
                    "
                />
            </main>
        </div>
    </div>
</template>

<style scoped>
.admin-shell {
    display: grid;
    grid-template-columns: 17rem minmax(0, 1fr);

    min-height: 100dvh;

    background: var(--color-surface);
}

.admin-sidebar {
    position: sticky;
    top: 0;

    display: flex;
    flex-direction: column;

    height: 100dvh;

    border-inline-end: 1px solid var(--color-border-soft);

    background: var(--color-surface-1);
}

.admin-brand {
    display: flex;
    align-items: center;
    gap: .8rem;

    min-height: 4.5rem;
    padding: 1rem 1.1rem;

    border-bottom: 1px solid var(--color-border-soft);
}

.admin-brand__icon {
    display: grid;

    width: 2.7rem;
    height: 2.7rem;

    border-radius: .8rem;

    background: var(--color-primary-soft);
    color: var(--color-primary);

    place-items: center;
}

.admin-brand > div:last-child {
    display: grid;
    gap: .1rem;
}

.admin-brand strong {
    color: var(--color-text-primary);
    font-size: var(--font-size-md);
}

.admin-brand span {
    color: var(--color-text-muted);
    font-size: 11px;
}

.admin-nav {
    display: grid;
    gap: .35rem;

    padding: .8rem;
}

.admin-nav-item {
    display: flex;
    align-items: center;
    gap: .7rem;

    width: 100%;
    min-height: 3.35rem;

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

.admin-nav-item.active
.admin-nav-item__icon {
    background: color-mix(
        in srgb,
        var(--color-primary) 10%,
        transparent
    );
}

.admin-nav-item__content {
    display: grid;
    flex: 1;

    min-width: 0;

    gap: .1rem;
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

.admin-sidebar__footer {
    display: grid;
    gap: .7rem;

    margin-top: auto;
    padding: .8rem;

    border-top: 1px solid var(--color-border-soft);
}

.admin-identity {
    display: flex;
    align-items: center;
    gap: .65rem;
    min-width: 0;
}

.admin-identity__avatar {
    display: grid;

    width: 2.35rem;
    height: 2.35rem;
    flex: 0 0 auto;

    border-radius: .7rem;

    background: var(--color-primary-soft);
    color: var(--color-primary);

    place-items: center;
}

.admin-identity > div:last-child {
    display: grid;
    min-width: 0;
    gap: .1rem;
}

.admin-identity strong {
    color: var(--color-text-primary);
    font-size: var(--font-size-xs);
}

.admin-identity small {
    overflow: hidden;

    color: var(--color-text-muted);
    font-size: 10px;

    text-overflow: ellipsis;
    white-space: nowrap;
}

.admin-logout {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: .45rem;

    width: 100%;
    min-height: 2.65rem;

    border: 1px solid var(--color-border-soft);
    border-radius: .7rem;

    background: transparent;
    color: var(--color-text-secondary);

    cursor: pointer;

    transition:
        background var(--transition-fast),
        color var(--transition-fast);
}

.admin-logout:hover {
    background: var(--color-danger-soft);
    color: var(--color-danger);
}

.admin-main {
    min-width: 0;
}

.admin-topbar {
    position: sticky;
    top: 0;
    z-index: 20;

    display: flex;
    align-items: center;
    justify-content: space-between;

    min-height: 4.5rem;

    padding: 0 1.5rem;

    border-bottom: 1px solid var(--color-border-soft);

    background: color-mix(
        in srgb,
        var(--color-surface) 92%,
        transparent
    );

    backdrop-filter: blur(1rem);
}

.admin-topbar > div:first-child {
    display: grid;
    gap: .1rem;
}

.admin-topbar strong {
    color: var(--color-text-primary);
}

.admin-topbar span {
    color: var(--color-text-muted);
    font-size: 11px;
}

.admin-topbar__status {
    display: flex !important;
    align-items: center;

    gap: .45rem;

    color: var(--color-success) !important;
    font-size: 12px !important;
    font-weight: 700;
}

.status-dot {
    width: .45rem;
    height: .45rem;

    border-radius: 50%;

    background: var(--color-success);
}

.admin-content {
    min-width: 0;
    padding: 1.25rem 1.5rem 2rem;
}

@media (max-width: 900px) {
    .admin-shell {
        grid-template-columns: 1fr;
    }

    .admin-sidebar {
        position: static;
        height: auto;

        border-inline-end: 0;
        border-bottom: 1px solid var(--color-border-soft);
    }

    .admin-sidebar__footer {
        display: flex;
        align-items: center;
        justify-content: space-between;
    }

    .admin-logout {
        width: auto;
        padding-inline: 1rem;
    }
}

@media (max-width: 600px) {
    .admin-topbar {
        padding-inline: 1rem;
    }

    .admin-content {
        padding-inline: .85rem;
    }
}
</style>