import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { test } from 'node:test'
import { runInNewContext } from 'node:vm'

const bootstrapSource = await readFile(new URL('../public/theme-init.js', import.meta.url), 'utf8')

function runThemeBootstrap(theme, systemDark = false) {
  const root = { dataset: {}, style: {} }
  const metas = {
    'theme-color': { value: '', setAttribute: (_, value) => { metas['theme-color'].value = value } },
    'color-scheme': { value: '', setAttribute: (_, value) => { metas['color-scheme'].value = value } },
    'apple-mobile-web-app-status-bar-style': {
      value: '',
      setAttribute: (_, value) => { metas['apple-mobile-web-app-status-bar-style'].value = value },
    },
  }

  runInNewContext(bootstrapSource, {
    window: {
      localStorage: { getItem: () => JSON.stringify({ theme }) },
      matchMedia: () => ({ matches: systemDark }),
    },
    document: {
      documentElement: root,
      querySelector: (selector) => metas[selector.match(/name="([^"]+)"/)?.[1]] ?? null,
    },
  })

  return { root, metas }
}

test('theme bootstrap restores explicit light mode before the app starts', async () => {
  const index = await readFile(new URL('../index.html', import.meta.url), 'utf8')
  assert.ok(index.indexOf('/theme-init.js') < index.indexOf('/src/main.ts'))

  const { root, metas } = runThemeBootstrap('light')
  assert.equal(root.dataset.theme, 'light')
  assert.equal(root.style.colorScheme, 'light')
  assert.equal(metas['theme-color'].value, '#f2f6fb')
})

test('theme bootstrap resolves system preference and safely defaults invalid values', () => {
  assert.equal(runThemeBootstrap('system', false).root.dataset.theme, 'light')
  assert.equal(runThemeBootstrap('system', true).root.dataset.theme, 'dark')
  assert.equal(runThemeBootstrap('unexpected', false).root.dataset.theme, 'dark')
})
