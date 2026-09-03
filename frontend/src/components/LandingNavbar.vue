<script setup>
import { computed } from 'vue'
import { useAuthStore } from '../stores/auth'
import { useRouter } from 'vue-router'

const auth = useAuthStore()
const router = useRouter()
const isLoggedIn = computed(() => auth.isAuthenticated)

const navItems = [
  { label: 'بازار', href: '#market' },
  { label: 'OTC', href: '#otc' },
  { label: 'درباره ما', href: '#about' },
  { label: 'امنیت', href: '#security' },
  { label: 'پشتیبانی', href: '#support' },
]

function goLogin() {
  router.push('/login')
}

function goDashboard() {
  router.push('/dashboard')
}
</script>

<template>
  <header class="landing-header">
    <nav class="landing-nav container">
      <div class="brand-wrap" @click="goDashboard" role="button" tabindex="0" @keydown.enter="goDashboard">
        <div class="brand-mark">
          <span>OT</span>
        </div>
        <div class="brand-copy small">
          <span class="brand-name">OTC</span>
          <small>Exchange</small>
        </div>
      </div>

      <div class="nav-links">
        <a v-for="item in navItems" :key="item.label" :href="item.href">{{ item.label }}</a>
      </div>

      <div class="nav-actions">
        <button v-if="isLoggedIn" class="nav-btn primary" type="button" @click="goDashboard">داشبورد</button>
        <button v-else class="nav-btn ghost" type="button" @click="goLogin">ورود</button>
        <button class="nav-btn primary" type="button" @click="isLoggedIn ? goDashboard() : goLogin()">{{ isLoggedIn ? 'حساب من' : 'ایجاد حساب' }}</button>
      </div>
    </nav>
  </header>
</template>
