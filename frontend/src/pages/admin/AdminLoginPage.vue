<script setup lang="ts">
import {ref} from 'vue'
import {useRoute, useRouter} from 'vue-router'
import AppIcon from '@/components/ui/AppIcon.vue'
import AppButton from '@/components/ui/AppButton.vue'
import {ApiError} from '@/services/api'
import {useAdminAuthStore} from '@/stores/adminAuth'

const router = useRouter()
const route = useRoute()

const adminAuth = useAdminAuthStore()

const email = ref('')
const password = ref('')
const error = ref('')

async function submit(): Promise<void> {
    if (adminAuth.loading) return

    error.value = ''

    const normalizedEmail =
        email.value.trim().toLowerCase()

    if (!normalizedEmail) {
        error.value =
            'ایمیل مدیریت را وارد کنید.'
        return
    }

    if (!password.value) {
        error.value =
            'رمز عبور را وارد کنید.'
        return
    }

    try {
        await adminAuth.login(
            normalizedEmail,
            password.value,
        )

        const redirect =
            typeof route.query.redirect === 'string'
                ? route.query.redirect
                : '/admin'

        await router.replace(redirect)
    } catch (caught) {
        if (caught instanceof ApiError) {
            error.value =
                caught.message ||
                'ورود به پنل مدیریت انجام نشد.'
        } else {
            error.value =
                'ورود به پنل مدیریت انجام نشد.'
        }
    }
}
</script>

<template>
    <main class="admin-login">
        <div class="admin-login__background"></div>

        <section class="admin-login-card">
            <header class="admin-login-header">
                <div class="admin-login-logo">
                    <AppIcon
                        name="verify"
                        :size="25"
                    />
                </div>

                <div>
                    <strong>
                        پنل مدیریت روشا
                    </strong>

                    <span>
                        ورود مدیر سیستم
                    </span>
                </div>
            </header>

            <div class="admin-login-intro">
                <h1>
                    ورود به پنل مدیریت
                </h1>

                <p>
                    برای ادامه، اطلاعات حساب مدیریتی
                    خود را وارد کنید.
                </p>
            </div>

            <form
                class="admin-login-form"
                @submit.prevent="submit"
            >
                <label>
                    <span>ایمیل مدیریت</span>

                    <input
                        v-model="email"
                        type="email"
                        dir="ltr"
                        autocomplete="username"
                        placeholder="admin@example.com"
                    />
                </label>

                <label>
                    <span>رمز عبور</span>

                    <input
                        v-model="password"
                        type="password"
                        dir="ltr"
                        autocomplete="current-password"
                        placeholder="رمز عبور"
                    />
                </label>

                <div
                    v-if="error"
                    class="admin-login-error"
                    role="alert"
                >
                    <AppIcon
                        name="warning"
                        :size="18"
                    />

                    <span>{{ error }}</span>
                </div>

                <AppButton
                    type="submit"
                    variant="primary"
                    size="lg"
                    block
                    :loading="adminAuth.loading"
                    icon="login"
                >
                    ورود به پنل
                </AppButton>
            </form>

            <footer class="admin-login-footer">
                <AppIcon
                    name="lock"
                    :size="15"
                />

                <span>
                    این بخش فقط برای مدیران مجاز سیستم است.
                </span>
            </footer>
        </section>
    </main>
</template>

<style scoped>
.admin-login {
    position: relative;

    display: grid;
    min-height: 100dvh;

    padding: 1.5rem;

    background: var(--color-surface);
    place-items: center;

    overflow: hidden;
}

.admin-login__background {
    position: absolute;
    inset: 0;

    background:
        radial-gradient(
            circle at 20% 15%,
            color-mix(
                in srgb,
                var(--color-primary) 12%,
                transparent
            ),
            transparent 32%
        ),
        radial-gradient(
            circle at 85% 80%,
            color-mix(
                in srgb,
                var(--color-primary) 8%,
                transparent
            ),
            transparent 30%
        );
}

.admin-login-card {
    position: relative;
    z-index: 1;

    width: min(100%, 27rem);

    padding: 1.75rem;

    border: 1px solid var(--color-border-soft);
    border-radius: 1.25rem;

    background: var(--color-surface);

    box-shadow:
        0 1.5rem 4rem rgb(0 0 0 / 0.12),
        0 0 0 1px rgb(255 255 255 / 0.02);
}

.admin-login-header {
    display: flex;
    align-items: center;
    gap: .8rem;
    margin-bottom: 2rem;
}

.admin-login-logo {
    display: grid;

    width: 3rem;
    height: 3rem;

    border-radius: .9rem;

    background: var(--color-primary-soft);
    color: var(--color-primary);

    place-items: center;
}

.admin-login-header > div:last-child {
    display: grid;
    gap: .15rem;
}

.admin-login-header strong {
    color: var(--color-text-primary);
    font-size: var(--font-size-md);
}

.admin-login-header span {
    color: var(--color-text-muted);
    font-size: var(--font-size-xs);
}

.admin-login-intro {
    margin-bottom: 1.5rem;
}

.admin-login-intro h1 {
    margin: 0;

    color: var(--color-text-primary);
    font-size: 1.4rem;
}

.admin-login-intro p {
    margin: .4rem 0 0;

    color: var(--color-text-muted);
    font-size: var(--font-size-sm);
    line-height: 1.8;
}

.admin-login-form {
    display: grid;
    gap: 1rem;
}

.admin-login-form label {
    display: grid;
    gap: .45rem;
}

.admin-login-form label > span {
    color: var(--color-text-secondary);
    font-size: var(--font-size-sm);
    font-weight: 700;
}

.admin-login-form input {
    width: 100%;
    min-height: 3.1rem;

    padding: .75rem .9rem;

    border: 1px solid var(--color-border);
    border-radius: var(--radius-md);

    background: var(--color-surface-input);
    color: var(--color-text-primary);

    font: inherit;
}

.admin-login-form input:focus {
    outline: none;
    border-color: var(--color-border-focus);
    box-shadow: var(--shadow-focus);
}

.admin-login-error {
    display: flex;
    align-items: flex-start;
    gap: .5rem;

    padding: .75rem;

    border-radius: var(--radius-md);

    background: var(--color-danger-soft);
    color: var(--color-danger);

    font-size: var(--font-size-xs);
    line-height: 1.7;
}

.admin-login-footer {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: .45rem;

    margin-top: 1.5rem;

    color: var(--color-text-muted);
    font-size: 11px;
    text-align: center;
}
</style>