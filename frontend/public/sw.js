const CACHE_PREFIX = 'rosha-shell-'
const CACHE = `${CACHE_PREFIX}2026-09-01-v4`
const STATIC = ['/', '/offline.html', '/manifest.webmanifest', '/icons/rosha-mark.svg']

const PRECACHE_CONTENT_TYPES = new Map([
  ['/', ['text/html']],
  ['/offline.html', ['text/html']],
  ['/manifest.webmanifest', ['application/manifest+json', 'application/json']],
  ['/icons/rosha-mark.svg', ['image/svg+xml']],
])

const STATIC_RESPONSE_RULES = {
  script: {
    extensions: ['.js', '.mjs'],
    contentTypes: ['application/javascript', 'application/x-javascript', 'text/javascript'],
  },
  style: {
    extensions: ['.css'],
    contentTypes: ['text/css'],
  },
  font: {
    extensions: ['.woff', '.woff2', '.ttf', '.otf', '.eot'],
    contentTypes: ['font/', 'application/font-', 'application/vnd.ms-fontobject', 'application/octet-stream'],
  },
  image: {
    extensions: ['.avif', '.gif', '.ico', '.jpeg', '.jpg', '.png', '.svg', '.webp'],
    contentTypes: ['image/'],
  },
}

function isExpectedStaticResponse(request, response) {
  if (!response.ok) return false

  const rule = STATIC_RESPONSE_RULES[request.destination]
  const pathname = new URL(request.url).pathname.toLowerCase()
  const contentType = (response.headers.get('content-type') || '').toLowerCase()

  return Boolean(
    rule
    && rule.extensions.some((extension) => pathname.endsWith(extension))
    && rule.contentTypes.some((expected) => contentType.startsWith(expected)),
  )
}

async function precacheShell(cache) {
  await Promise.all(STATIC.map(async (path) => {
    const response = await fetch(path, { cache: 'reload' })
    const contentType = (response.headers.get('content-type') || '').toLowerCase()
    const expectedTypes = PRECACHE_CONTENT_TYPES.get(path) || []
    if (!response.ok || !expectedTypes.some((expected) => contentType.startsWith(expected))) {
      throw new TypeError(`Invalid precache response for ${path}`)
    }
    await cache.put(path, response)
  }))
}

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE)
      .then((cache) => precacheShell(cache))
      .then(() => self.skipWaiting()),
  )
})

self.addEventListener('activate', (event) => {
  event.waitUntil(
    Promise.all([
      caches.keys().then((keys) => Promise.all(
        keys
          .filter((key) => key.startsWith(CACHE_PREFIX) && key !== CACHE)
          .map((key) => caches.delete(key)),
      )),
      self.clients.claim(),
    ]),
  )
})

self.addEventListener('fetch', (event) => {
  const request = event.request
  const url = new URL(request.url)
  if (request.method !== 'GET' || url.origin !== self.location.origin || url.pathname.startsWith('/api/')) return

  if (request.mode === 'navigate') {
    event.respondWith(fetch(request).catch(() =>
      caches.open(CACHE).then((cache) => cache.match('/offline.html'))))
    return
  }

  const isStaticAsset = ['/assets/', '/icons/', '/fonts/'].some((prefix) => url.pathname.startsWith(prefix))
  if (isStaticAsset && ['script', 'style', 'font', 'image'].includes(request.destination)) {
    event.respondWith(
      caches.open(CACHE).then(async (cache) => {
        const cached = await cache.match(request)
        if (cached) return cached

        const response = await fetch(request)
        if (isExpectedStaticResponse(request, response)) {
          await cache.put(request, response.clone())
        }
        return response
      }),
    )
  }
})
