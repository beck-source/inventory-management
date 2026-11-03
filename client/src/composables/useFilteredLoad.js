import { ref, onMounted } from 'vue'
import { useI18n } from './useI18n'

export function useFilteredLoad(loader, { immediate = true } = {}) {
  const { t } = useI18n()
  const loading = ref(false)
  const error = ref(null)
  let requestId = 0

  const reload = async () => {
    const currentRequest = ++requestId
    loading.value = true
    error.value = null
    try {
      await loader()
    } catch (err) {
      if (currentRequest !== requestId) return
      error.value = t('common.loadFailed')
      console.error('Load error:', err)
    } finally {
      if (currentRequest === requestId) loading.value = false
    }
  }

  if (immediate) onMounted(reload)

  return { loading, error, reload }
}
