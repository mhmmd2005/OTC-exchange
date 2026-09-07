const MODE_STORAGE_KEY = 'otc-api-mode'

let currentMode = null

function getStoredMode() {
  if (!import.meta.env.DEV) return 'real'
  try {
    return localStorage.getItem(MODE_STORAGE_KEY) || 'real'
  } catch {
    return 'real'
  }
}

function initializeMode() {
  currentMode = getStoredMode()
}

export function getApiMode() {
  if (!import.meta.env.DEV) return 'real'
  if (!currentMode) initializeMode()
  return currentMode
}

export function setApiMode(mode) {
  if (!import.meta.env.DEV) return
  if (!['real', 'mock'].includes(mode)) {
    throw new Error(`Invalid API mode: ${mode}`)
  }
  localStorage.setItem(MODE_STORAGE_KEY, mode)
  currentMode = mode
}

export function isMockMode() {
  if (!import.meta.env.DEV) return false
  return getApiMode() === 'mock'
}

export function isRealMode() {
  return getApiMode() === 'real'
}

export function isDevelopment() {
  return import.meta.env.DEV
}

export default {
  getApiMode,
  setApiMode,
  isMockMode,
  isRealMode,
  isDevelopment,
}
