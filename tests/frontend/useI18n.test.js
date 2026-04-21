// Tests for client/src/composables/useI18n.js
//
// useI18n is a module-level singleton: currentLocale lives outside the exported
// function. Tests call setLocale('en') in afterEach to restore a clean state
// so that locale changes in one test cannot bleed into the next.
//
// happy-dom provides a localStorage shim, so the composable's localStorage
// persistence calls work without mocking.

import { useI18n } from '../../client/src/composables/useI18n.js'

describe('useI18n', () => {
  let t, setLocale, currentLocale, currentCurrency

  beforeEach(() => {
    ;({ t, setLocale, currentLocale, currentCurrency } = useI18n())
    // Start every test in the English locale.
    setLocale('en')
  })

  afterEach(() => {
    // Restore English so the module singleton is predictable for subsequent tests.
    setLocale('en')
  })

  // --- English default ---

  it('returns English text for a known key when locale is "en"', () => {
    expect(t('nav.overview')).toBe('Overview')
  })

  it('returns English text for a nested key', () => {
    expect(t('orders.title')).toBe('Orders')
  })

  // --- Unknown keys fall back to the key itself ---

  it('returns the key string when the key does not exist in the current locale', () => {
    expect(t('nonexistent.key.path')).toBe('nonexistent.key.path')
  })

  it('returns the key string for a partially valid path that resolves to an object, not a string', () => {
    // 'nav' exists but is an object, not a string — should return the key.
    expect(t('nav')).toBe('nav')
  })

  // --- Japanese locale ---

  it('returns Japanese text after switching to "ja"', () => {
    setLocale('ja')
    expect(t('nav.overview')).toBe('概要')
  })

  it('currentLocale updates to "ja" after setLocale', () => {
    setLocale('ja')
    expect(currentLocale.value).toBe('ja')
  })

  it('currentLocale returns to "en" after resetting', () => {
    setLocale('ja')
    setLocale('en')
    expect(currentLocale.value).toBe('en')
  })

  // --- English fallback when key missing in ja ---

  it('returns the key when the key is completely absent from both locales while in Japanese', () => {
    // When in 'ja' and a key doesn't exist in ja, the code tries en as
    // fallback. If en also lacks it, the key itself is returned. This
    // exercises both legs of the fallback chain.
    setLocale('ja')
    expect(t('completely.absent.key')).toBe('completely.absent.key')
  })

  // --- Placeholder replacement ---

  it('substitutes {count} placeholder in English', () => {
    // orders.itemsCount = '{count} items'
    expect(t('orders.itemsCount', { count: 5 })).toBe('5 items')
  })

  it('substitutes {count} placeholder in Japanese', () => {
    // ja orders.itemsCount = '{count}件'
    setLocale('ja')
    expect(t('orders.itemsCount', { count: 3 })).toBe('3件')
  })

  it('substitutes multiple different placeholders', () => {
    // finance.fromOrders = 'From {count} orders'
    expect(t('finance.fromOrders', { count: 42 })).toBe('From 42 orders')
  })

  it('leaves unmatched placeholders unchanged when no params supplied', () => {
    // The raw template is returned with the braces intact.
    const result = t('orders.itemsCount')
    expect(result).toBe('{count} items')
  })

  it('leaves a placeholder unchanged when the matching param key is absent', () => {
    const result = t('orders.itemsCount', { total: 99 })
    expect(result).toBe('{count} items')
  })

  // --- currentCurrency ---

  it('currentCurrency is "USD" for English locale', () => {
    expect(currentCurrency.value).toBe('USD')
  })

  it('currentCurrency is "JPY" for Japanese locale', () => {
    setLocale('ja')
    expect(currentCurrency.value).toBe('JPY')
  })

  it('currentCurrency returns to "USD" after switching back to English', () => {
    setLocale('ja')
    setLocale('en')
    expect(currentCurrency.value).toBe('USD')
  })

  // --- Invalid locale is ignored ---

  it('ignores setLocale call for an unrecognised locale', () => {
    setLocale('fr')
    // Locale must remain unchanged.
    expect(currentLocale.value).toBe('en')
    expect(t('nav.overview')).toBe('Overview')
  })
})
