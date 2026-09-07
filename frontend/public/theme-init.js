;(function initializeTheme() {
  var preference = 'dark'

  try {
    var stored = JSON.parse(window.localStorage.getItem('rosha.preferences.v1') || '{}')
    if (stored.theme === 'light' || stored.theme === 'dark' || stored.theme === 'system') {
      preference = stored.theme
    }
  } catch (_) {
    // The default remains dark when storage is blocked or contains invalid data.
  }

  var useDark = preference === 'dark'
    || (preference === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches)
  var theme = useDark ? 'dark' : 'light'
  var root = document.documentElement
  var themeColor = document.querySelector('meta[name="theme-color"]')
  var colorScheme = document.querySelector('meta[name="color-scheme"]')
  var statusBar = document.querySelector('meta[name="apple-mobile-web-app-status-bar-style"]')

  root.dataset.theme = theme
  root.style.colorScheme = theme
  if (themeColor) themeColor.setAttribute('content', useDark ? '#050e1a' : '#f2f6fb')
  if (colorScheme) colorScheme.setAttribute('content', theme)
  if (statusBar) statusBar.setAttribute('content', useDark ? 'black-translucent' : 'default')
})()
