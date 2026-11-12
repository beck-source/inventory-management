import { ref, watch, onScopeDispose } from 'vue'

/**
 * Shared loader for views that fetch data (optionally re-fetched when filters change).
 *
 * - `fetcher({ signal })` returns the data; pass `signal` to api calls so superseded requests abort.
 * - `onSuccess(result)` is called only for the latest request, so views can assign several refs.
 * - Previous data is never cleared: `loading` goes true on reload but `loaded` stays true,
 *   letting views show the full-page spinner only on the first load.
 * - `error` is reset at the start of every load; `reload()` is meant for a Retry button.
 */
export function useAsyncData(fetcher, { immediate = true, watchSources = null, onSuccess = null } = {}) {
  const data = ref(null)
  const loading = ref(false)
  const error = ref(null)
  const loaded = ref(false) // true once any request has succeeded

  // Counter discards out-of-order responses even if the abort did not reach the network
  let requestId = 0
  let controller = null

  const reload = async () => {
    const current = ++requestId
    if (controller) controller.abort()
    controller = new AbortController()
    loading.value = true
    error.value = null
    try {
      const result = await fetcher({ signal: controller.signal })
      if (current !== requestId) return
      data.value = result
      loaded.value = true
      if (onSuccess) onSuccess(result)
    } catch (err) {
      // Aborted requests were superseded (or the view unmounted); not a real failure
      if (current !== requestId || err?.code === 'ERR_CANCELED') return
      console.error('Failed to load data:', err)
      error.value = err
    } finally {
      if (current === requestId) loading.value = false
    }
  }

  if (watchSources) watch(watchSources, reload)
  if (immediate) reload()

  onScopeDispose(() => {
    requestId++
    if (controller) controller.abort()
  })

  return { data, loading, error, loaded, reload }
}
