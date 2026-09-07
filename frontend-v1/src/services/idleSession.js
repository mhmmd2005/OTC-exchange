const IDLE_TIMEOUT = 30 * 60 * 1000
const HEARTBEAT_INTERVAL = 60 * 1000
const LAST_ACTIVITY_KEY = 'otc-last-activity'

const ACTIVITY_EVENTS = [
    'click',
    'mousemove',
    'keydown',
    'scroll',
    'touchstart',
    'pointerdown',
]

let idleTimer = null
let heartbeatTimer = null
let authStore = null
let router = null
let api = null
let isRunning = false
let activityDirty = false
let lastHeartbeatAt = 0

function getLastActivityValue() {
    const value = localStorage.getItem(
        LAST_ACTIVITY_KEY,
    )

    if (!value) {
        return null
    }

    const timestamp = Number(value)

    return Number.isFinite(timestamp)
        ? timestamp
        : null
}

function updateActivity() {
    const now = Date.now()

    localStorage.setItem(
        LAST_ACTIVITY_KEY,
        now.toString(),
    )

    activityDirty = true
}

function checkIdleTimeout() {
    const lastActivity =
        getLastActivityValue()

    if (!lastActivity) {
        return false
    }

    return (
        Date.now() - lastActivity
        >= IDLE_TIMEOUT
    )
}

function scheduleIdleTimer() {
    if (idleTimer) {
        clearTimeout(idleTimer)
        idleTimer = null
    }

    if (!isRunning) {
        return
    }

    const lastActivity =
        getLastActivityValue()

    if (!lastActivity) {
        return
    }

    const remaining =
        IDLE_TIMEOUT -
        (Date.now() - lastActivity)

    if (remaining <= 0) {
        handleIdleTimeout()
        return
    }

    idleTimer = setTimeout(
        scheduleIdleTimer,
        remaining,
    )
}

function handleActivity() {
    if (!isRunning) {
        return
    }

    updateActivity()
    scheduleIdleTimer()
}

function handleVisibilityChange() {
    if (
        document.visibilityState !== 'visible' ||
        !isRunning
    ) {
        return
    }

    if (checkIdleTimeout()) {
        handleIdleTimeout()
        return
    }

    scheduleIdleTimer()
}

function handleStorageChange(event) {
    if (
        event.key !== LAST_ACTIVITY_KEY ||
        !isRunning
    ) {
        return
    }

    const lastActivity =
        Number(event.newValue || 0)

    if (!lastActivity) {
        scheduleIdleTimer()
        return
    }

    if (
        Date.now() - lastActivity
        >= IDLE_TIMEOUT
    ) {
        handleIdleTimeout()
        return
    }

    activityDirty = true
    scheduleIdleTimer()
}

async function sendHeartbeat() {
    if (
        !isRunning ||
        !authStore ||
        !authStore.isAuthenticated ||
        !activityDirty
    ) {
        return
    }

    const now = Date.now()

    if (
        now - lastHeartbeatAt <
        HEARTBEAT_INTERVAL
    ) {
        return
    }

    if (checkIdleTimeout()) {
        await handleIdleTimeout()
        return
    }

    activityDirty = false
    lastHeartbeatAt = now

    try {
        await api.get(
            '/auth/me/',
            {
                headers: {
                    'X-Activity-Heartbeat':
                        'true',
                },
            },
        )
    } catch (error) {
        activityDirty = true

        if (
            error?.response?.status ===
            401
        ) {
            await handleIdleTimeout()
        }
    }
}

async function handleIdleTimeout() {
    if (!isRunning) {
        return
    }

    stopIdleSession()

    try {
        if (
            authStore &&
            authStore.isAuthenticated
        ) {
            await authStore.logout()
        }
    } finally {
        localStorage.removeItem(
            LAST_ACTIVITY_KEY,
        )

        if (router) {
            await router.replace('/login')
        }
    }
}

function setupActivityListeners() {
    ACTIVITY_EVENTS.forEach(
        (event) => {
            document.addEventListener(
                event,
                handleActivity,
                {
                    passive: true,
                },
            )
        },
    )

    document.addEventListener(
        'visibilitychange',
        handleVisibilityChange,
    )

    window.addEventListener(
        'storage',
        handleStorageChange,
    )
}

function removeActivityListeners() {
    ACTIVITY_EVENTS.forEach(
        (event) => {
            document.removeEventListener(
                event,
                handleActivity,
            )
        },
    )

    document.removeEventListener(
        'visibilitychange',
        handleVisibilityChange,
    )

    window.removeEventListener(
        'storage',
        handleStorageChange,
    )
}

export function startIdleSession(
    store,
    route,
    axiosInstance,
) {
    if (isRunning) {
        return
    }

    authStore = store
    router = route
    api = axiosInstance
    isRunning = true
    activityDirty = false
    lastHeartbeatAt = 0

    if (!getLastActivityValue()) {
        updateActivity()
        activityDirty = false
    }

    if (checkIdleTimeout()) {
        handleIdleTimeout()
        return
    }

    setupActivityListeners()
    scheduleIdleTimer()

    heartbeatTimer = setInterval(
        sendHeartbeat,
        1000,
    )
}

export function stopIdleSession() {
    isRunning = false
    activityDirty = false
    lastHeartbeatAt = 0

    if (idleTimer) {
        clearTimeout(idleTimer)
        idleTimer = null
    }

    if (heartbeatTimer) {
        clearInterval(
            heartbeatTimer,
        )
        heartbeatTimer = null
    }

    removeActivityListeners()
}

export function getLastActivity() {
    return getLastActivityValue()
}