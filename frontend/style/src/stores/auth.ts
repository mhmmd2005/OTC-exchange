import { defineStore } from 'pinia'
import { router } from '@/router'

export const API_BASE = (import.meta.env.VITE_API_URL as string).replace(/\/$/, '')

export const endpoints = {
  // Auth
  LOGIN:           `${API_BASE}/accounts/login/`,
  TWOFA_VERIFY:    `${API_BASE}/accounts/2fa/verify/`,
  VERIFY_EMAIL:    `${API_BASE}/accounts/verify-email/`,
  FORGOT_PASSWORD: `${API_BASE}/accounts/forgot-password/`,
  RESET_PASSWORD:  `${API_BASE}/accounts/reset-password-confirm/`,
  TOKEN_REFRESH:   `${API_BASE}/accounts/token/refresh/`,
  LOGOUT:          `${API_BASE}/accounts/logout/`,
  ME:              `${API_BASE}/accounts/me/`,

  // Profile / Settings
  PROFILE:         `${API_BASE}/accounts/profile/`,
  CHANGE_PASSWORD: `${API_BASE}/accounts/change-password/`,
  TWOFA_STATUS:        `${API_BASE}/accounts/2fa/status/`,
  TWOFA_SETUP_START:   `${API_BASE}/accounts/2fa/setup/start/`,
  TWOFA_SETUP_CONFIRM: `${API_BASE}/accounts/2fa/setup/confirm/`,
  TWOFA_DISABLE:       `${API_BASE}/accounts/2fa/disable/`,
  TWOFA_BACKUP_REGEN:  `${API_BASE}/accounts/2fa/backup-codes/regenerate/`,
  TIME_PREFS:      `${API_BASE}/accounts/time-prefs/`,
  ACTIVITY_LOGS:   `${API_BASE}/accounts/activity-logs/`,
}

function normalizeErrorMessage(data: any, fallback: string) {
  try {
    if (!data || typeof data !== 'object' || Array.isArray(data)) return fallback;

    if (typeof (data as any).detail === 'string') return (data as any).detail;
    if (Array.isArray((data as any).detail)) return (data as any).detail.join(' | ');
    if (typeof (data as any).message === 'string') return (data as any).message;
    if (typeof (data as any).error === 'string') return (data as any).error;

    const obj = data as Record<string, unknown>;
    const keys = Object.keys(obj);
    if (keys.length) {
      return keys
        .map((k) => {
          const v = obj[k];
          if (typeof v === 'string') return `${k}: ${v}`;
          if (Array.isArray(v)) return `${k}: ${(v as unknown[]).map(String).join(', ')}`;
          if (v && typeof v === 'object') return `${k}: ${JSON.stringify(v)}`;
          return `${k}: ${String(v)}`;
        })
        .join(' | ');
    }
    return fallback;
  } catch {
    return fallback;
  }
}


type StoredUser = {
  email: string
  access?: string | null
  refresh?: string | null
  token?: string | null
  profile?: any | null
}

// 2FA ticket helpers (store both simple ticket and ctx with timestamp)
type TwoFACtx = { ticket: string; ts: number }

function loadUser(): StoredUser | null {
  try { return JSON.parse(localStorage.getItem('user') || 'null') } catch { return null }
}
function saveUser(u: StoredUser | null) {
  if (!u) localStorage.removeItem('user'); else localStorage.setItem('user', JSON.stringify(u))
}

function loadTwoFATicket(): string | null {
  try {
    const raw = sessionStorage.getItem('twofa_ctx')
    if (raw) {
      const ctx = JSON.parse(raw) as TwoFACtx
      return ctx.ticket || null
    }
    return sessionStorage.getItem('twofa_ticket')
  } catch { return null }
}
function saveTwoFATicket(t: string | null) {
  try {
    if (!t) {
      sessionStorage.removeItem('twofa_ticket')
      sessionStorage.removeItem('twofa_ctx')
    } else {
      sessionStorage.setItem('twofa_ticket', t)
      sessionStorage.setItem('twofa_ctx', JSON.stringify({ ticket: t, ts: Date.now() } as TwoFACtx))
    }
  } catch {}
}

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: loadUser() as StoredUser | null,
    returnUrl: null as string | null,
    twoFATicket: loadTwoFATicket() as string | null,
  }),

  getters: {
    isAuthenticated(state): boolean {
      return !!(state.user?.access || state.user?.token)
    },
  },

  actions: {
    // --------------- Core HTTP with refresh ---------------
    async authorizedFetch(input: string, init?: RequestInit): Promise<Response> {
      const doFetch = async (token?: string | null) => {
        const headers: Record<string, string> = {
          'Content-Type': 'application/json',
          ...(init?.headers as Record<string, string> | undefined),
        }
        if (token) headers['Authorization'] = `Bearer ${token}`
        return fetch(input, { ...init, headers, credentials: 'include' })
      }

      const access = this.user?.access || this.user?.token || null
      let res = await doFetch(access)
      if (res.status !== 401) return res

      const newAccess = await this.tryRefresh()
      if (!newAccess) return res
      res = await doFetch(newAccess)
      return res
    },

    async tryRefresh(): Promise<string | null> {
      const refresh = this.user?.refresh
      if (!refresh) return null

      const res = await fetch(endpoints.TOKEN_REFRESH, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh }),
        credentials: 'include',
      })
      const data = await res.json().catch(() => ({}))
      if (!res.ok || !data.access) return null

      const updated: StoredUser = {
        ...(this.user || { email: '' }),
        access: data.access,
        token: data.access,
        refresh: data.refresh ?? this.user?.refresh ?? null,
        profile: this.user?.profile ?? null,
      }
      this.user = updated
      saveUser(updated)
      return data.access as string
    },

    // --------------- Auth flows ---------------
    async login(
      payloadOrEmail: { email: string; password: string; otp?: string; turnstile_token?: string } | string,
      passwordMaybe?: string
    ) {
      const payload =
        typeof payloadOrEmail === 'string'
          ? { email: payloadOrEmail, password: passwordMaybe as string }
          : payloadOrEmail

      const res = await fetch(endpoints.LOGIN, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: payload.email,
          password: payload.password,
          turnstile_token: payload.turnstile_token || '',
        }),
        credentials: 'include',
      })
      const data = await res.json().catch(() => ({}))
      if (!res.ok) {
        const msg = data?.detail || data?.message || data?.error || `Login failed (${res.status})`
        throw new Error(msg)
      }

      // 2FA required
      if (data?.requires_2fa && data?.ticket) {
        this.twoFATicket = data.ticket
        saveTwoFATicket(data.ticket)

        if (payload.otp) {
          return this.verify2FA({ ticket: data.ticket, code: payload.otp })
        }

        try { router.replace('/two-step') } catch {}
        return { requires_2fa: true, ticket: data.ticket }
      }

      // Normal login
      if (!data?.access) throw new Error('No access token in response')

      const updated: StoredUser = {
        email: data?.email || payload.email,
        access: data.access,
        token: data.access,
        refresh: data.refresh ?? null,
        profile: data?.profile ?? this.user?.profile ?? null,
      }
      this.user = updated
      saveUser(updated)

      const to = this.returnUrl || '/dashboard1'
      this.returnUrl = null
      try { router.replace(to) } catch {}
      return updated
    },

    // Accepts either 'code' string or full payload { ticket, code?, backup_code? }
    async verify2FA(payloadOrCode: { ticket: string; code?: string; backup_code?: string } | string) {
      const payload = typeof payloadOrCode === 'string'
        ? { ticket: this.twoFATicket || '', code: payloadOrCode }
        : payloadOrCode

      if (!payload.ticket) throw new Error('Missing 2FA ticket.')

      const res = await fetch(endpoints.TWOFA_VERIFY, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
        credentials: 'include',
      })
      const data = await res.json().catch(() => ({}))
      if (!res.ok || !data?.access) {
        const msg = data?.detail || data?.message || data?.error || `2FA verify failed (${res.status})`
        throw new Error(msg)
      }

      // Clear pending ticket
      this.twoFATicket = null
      saveTwoFATicket(null)

      const updated: StoredUser = {
        ...(this.user || { email: '' }),
        access: data.access,
        token: data.access,
        refresh: data.refresh ?? this.user?.refresh ?? null,
        profile: this.user?.profile ?? null,
      }
      this.user = updated
      saveUser(updated)

      const to = this.returnUrl || '/dashboard1'
      this.returnUrl = null
      try { router.replace(to) } catch {}
      return updated
    },

    // --------------- Profile / Settings ---------------
    async getProfile() {
      const res = await this.authorizedFetch(endpoints.ME, { method: 'GET' })
      const data = await res.json().catch(() => ({}))
      if (!res.ok) throw new Error(data?.detail || `Failed to load profile (${res.status})`)
      const updated: StoredUser = {
        ...(this.user || { email: data?.email || '' }),
        email: data?.email || this.user?.email || '',
        profile: data?.profile ?? null,
        access: this.user?.access ?? this.user?.token ?? null,
        token: this.user?.token ?? this.user?.access ?? null,
        refresh: this.user?.refresh ?? null,
      }
      this.user = updated
      saveUser(updated)
      return updated.profile
    },

    async updateProfile(payload: Record<string, any>) {
      const res = await this.authorizedFetch(endpoints.PROFILE, {
        method: 'POST',
        body: JSON.stringify(payload),
      })
      const data = await res.json().catch(() => ({}))
      if (!res.ok) throw new Error(data?.detail || `Update profile failed (${res.status})`)
      const updated: StoredUser = {
        ...(this.user || { email: '' }),
        profile: data,
        access: this.user?.access ?? this.user?.token ?? null,
        token: this.user?.token ?? this.user?.access ?? null,
        refresh: this.user?.refresh ?? null,
      }
      this.user = updated
      saveUser(updated)
      return data
    },

    async changePassword(payload: { old_password: string; new_password: string; new_password2: string }) {
      const res = await this.authorizedFetch(endpoints.CHANGE_PASSWORD, {
        method: 'PUT',
        body: JSON.stringify(payload),
      })
      const data = await res.json().catch(() => ({}))
      if (!res.ok) throw new Error(data?.detail || `Change password failed (${res.status})`)
      return data
    },

    // --------------- 2FA settings ---------------
    async get2FAStatus(): Promise<{ is_enabled: boolean; has_recovery: boolean }> {
      const res = await this.authorizedFetch(endpoints.TWOFA_STATUS, { method: 'GET' })
      const data = await res.json().catch(() => ({}))
      if (!res.ok) throw new Error(data?.detail || `Get 2FA status failed (${res.status})`)
      return data
    },
    async start2FASetup(): Promise<{ otpauth_uri: string; secret: string }> {
      const res = await this.authorizedFetch(endpoints.TWOFA_SETUP_START, { method: 'POST' })
      const data = await res.json().catch(() => ({}))
      if (!res.ok) throw new Error(data?.detail || `Start 2FA setup failed (${res.status})`)
      return data
    },
    async confirm2FASetup(payloadOrCode: { code: string } | string): Promise<{ backup_codes: string[] }> {
      const payload = typeof payloadOrCode === 'string'
        ? { code: payloadOrCode }
        : payloadOrCode

      const res = await this.authorizedFetch(endpoints.TWOFA_SETUP_CONFIRM, {
        method: 'POST',
        body: JSON.stringify(payload),
      })
      const data = await res.json().catch(() => ({}))
      if (!res.ok) {
        const msg = data?.detail || data?.message || data?.error || `Confirm 2FA setup failed (${res.status})`
        throw new Error(msg)
      }
      return data
    },
    async disable2FA(payload: { password: string; code?: string; backup_code?: string }) {
      const res = await this.authorizedFetch(endpoints.TWOFA_DISABLE, {
        method: 'POST',
        body: JSON.stringify(payload),
      })
      const data = await res.json().catch(() => ({}))
      if (!res.ok) throw new Error(data?.detail || `Disable 2FA failed (${res.status})`)
      return data
    },
async regen2FABackupCodes(
  payload: { password: string; code: string }
): Promise<{ backup_codes: string[] }> {
  const res = await this.authorizedFetch(endpoints.TWOFA_BACKUP_REGEN, {
    method: 'POST',
    body: JSON.stringify(payload),
  });

  let data: any = null;
  try {
    data = await res.json();
  } catch {
    data = null;
  }

  if (!res.ok) {
    const msg = normalizeErrorMessage(data, `Regenerate backup codes failed (${res.status})`);
    throw new Error(msg);
  }
  return data as { backup_codes: string[] };
},

// --- aliases (fixed) ---
async twoFAStatus() { return this.get2FAStatus(); },
async twoFaStatus() { return this.get2FAStatus(); },
async twoFASetupStart() { return this.start2FASetup(); },
async twoFASetupConfirm(payload: { code: string } | string) { return this.confirm2FASetup(payload); },
async twoFADisable(payload: { password: string; code?: string; backup_code?: string }) { return this.disable2FA(payload); },

async twoFABackupRegen(payload: { password: string; code: string }) {
  return this.regen2FABackupCodes(payload);
},

async twoFARegenerateBackupCodes(payload: { password: string; code: string }) {
  return this.regen2FABackupCodes(payload);
},

    // Public alias
    async verifyTwoFA(payload: { ticket: string; code?: string; backup_code?: string } | string) {
      return this.verify2FA(payload as any)
    },

    // --------------- Preferences ---------------
    async getTimePrefs(): Promise<{ timezone: string; date_format: string }> {
      const res = await this.authorizedFetch(endpoints.TIME_PREFS, { method: 'GET' })
      const data = await res.json().catch(() => ({}))
      if (!res.ok) throw new Error(data?.detail || `Get time prefs failed (${res.status})`)
      return data
    },
    async saveTimePrefs(payload: { timezone: string; date_format: string }) {
      const res = await this.authorizedFetch(endpoints.TIME_PREFS, {
        method: 'POST',
        body: JSON.stringify(payload),
      })
      const data = await res.json().catch(() => ({}))
      if (!res.ok) throw new Error(data?.detail || `Save time prefs failed (${res.status})`)
      return data
    },
    async updateTimePrefs(payload: { timezone: string; date_format: string }) { return this.saveTimePrefs(payload) },
    async updatePrefs(payload: { timezone: string; date_format: string }) { return this.saveTimePrefs(payload) },
    async savePrefs(payload: { timezone: string; date_format: string }) { return this.saveTimePrefs(payload) },
    async getPrefs() { return this.getTimePrefs() },

    // --------------- Activity Logs ---------------
    async fetchActivityLogs() {
      const res = await this.authorizedFetch(endpoints.ACTIVITY_LOGS, { method: 'GET' })
      const data = await res.json().catch(() => ({}))
      if (!res.ok) throw new Error(data?.detail || `Get activity logs failed (${res.status})`)
      return Array.isArray(data) ? data : (Array.isArray(data?.results) ? data.results : [])
    },
    async getActivityLogs() { return this.fetchActivityLogs() },
    async activityLogs() { return this.fetchActivityLogs() },
    async loadActivityLogs() { return this.fetchActivityLogs() },
    async listActivityLogs() { return this.fetchActivityLogs() },

    // --------------- Logout ---------------
    async logout() {
      try {
        await this.authorizedFetch(endpoints.LOGOUT, {
          method: 'POST',
          body: JSON.stringify({ refresh: this.user?.refresh }),
        })
      } catch {}
      this.user = null
      saveUser(null)
      this.twoFATicket = null
      saveTwoFATicket(null)
      try { router.replace('/login') } catch {}
    },

    // --------------- Forgot Password ---------
    async forgotPassword(email: string) {
  const res = await fetch(endpoints.FORGOT_PASSWORD, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email }),
    credentials: 'include',
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const msg = data?.detail || data?.message || data?.error || `Request failed (${res.status})`;
    throw new Error(msg);
  }
  return data;
},

  },
})
