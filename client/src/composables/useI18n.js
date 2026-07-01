import { ref, computed } from 'vue'
import en from '../locales/en'
import ja from '../locales/ja'
import fr from '../locales/fr'

const translations = {
  en,
  fr,
  ja
}

// Load saved locale from localStorage, default to 'en'
const savedLocale = localStorage.getItem('app-locale') || 'en'
const currentLocale = ref(savedLocale)

// Currency is automatically set based on locale (en -> USD, ja -> JPY, fr -> EUR)
const currentCurrency = computed(() => {
  if (currentLocale.value === 'ja') return 'JPY'
  if (currentLocale.value === 'fr') return 'EUR'
  return 'USD'
})

export function useI18n() {
  const t = (key, params = {}) => {
    const keys = key.split('.')
    let value = translations[currentLocale.value]

    for (const k of keys) {
      if (value && typeof value === 'object') {
        value = value[k]
      } else {
        // If translation not found, try English as fallback
        if (currentLocale.value !== 'en') {
          let fallback = translations.en
          for (const fk of keys) {
            if (fallback && typeof fallback === 'object') {
              fallback = fallback[fk]
            } else {
              break
            }
          }
          if (fallback && typeof fallback === 'string') {
            return replacePlaceholders(fallback, params)
          }
        }
        // If still not found, return the key itself
        return key
      }
    }

    if (typeof value === 'string') {
      return replacePlaceholders(value, params)
    }

    return key
  }

  const replacePlaceholders = (text, params) => {
    return text.replace(/\{(\w+)\}/g, (match, key) => {
      return params[key] !== undefined ? params[key] : match
    })
  }

  const setLocale = (locale) => {
    if (translations[locale]) {
      currentLocale.value = locale
      localStorage.setItem('app-locale', locale)
    }
  }

  const availableLocales = computed(() => Object.keys(translations))

  const localeName = computed(() => {
    const names = {
      en: 'English',
      fr: 'Français',
      ja: '日本語'
    }
    return names[currentLocale.value] || currentLocale.value
  })

  // Translate product names
  const translateProductName = (productName) => {
    const locale = currentLocale.value
    if (translations[locale]?.productNames?.[productName]) {
      return translations[locale].productNames[productName]
    }
    return productName
  }

  // Translate customer names
  const translateCustomerName = (customerName) => {
    const locale = currentLocale.value
    if (translations[locale]?.customerNames?.[customerName]) {
      return translations[locale].customerNames[customerName]
    }
    return customerName
  }

  // Translate warehouse names
  const translateWarehouse = (warehouseName) => {
    if (currentLocale.value === 'ja') {
      const cityMap = {
        'San Francisco': 'サンフランシスコ',
        'London': 'ロンドン',
        'Tokyo': '東京'
      }
      if (cityMap[warehouseName]) return cityMap[warehouseName]
      if (warehouseName.startsWith('Warehouse ')) {
        return warehouseName.replace('Warehouse ', '倉庫')
      }
    }
    if (currentLocale.value === 'fr') {
      const cityMap = {
        'London': 'Londres'
      }
      if (cityMap[warehouseName]) return cityMap[warehouseName]
      if (warehouseName.startsWith('Warehouse ')) {
        return warehouseName.replace('Warehouse ', 'Entrepôt ')
      }
    }
    return warehouseName
  }

  const currencySymbol = computed(() => {
    if (currentCurrency.value === 'JPY') return '¥'
    if (currentCurrency.value === 'EUR') return '€'
    return '$'
  })

  // BCP 47 locale string for use with Intl/toLocaleDateString
  const dateLocale = computed(() => {
    if (currentLocale.value === 'ja') return 'ja-JP'
    if (currentLocale.value === 'fr') return 'fr-FR'
    return 'en-US'
  })

  return {
    t,
    setLocale,
    currentLocale: computed(() => currentLocale.value),
    currentCurrency,
    currencySymbol,
    dateLocale,
    availableLocales,
    localeName,
    translateProductName,
    translateCustomerName,
    translateWarehouse
  }
}
